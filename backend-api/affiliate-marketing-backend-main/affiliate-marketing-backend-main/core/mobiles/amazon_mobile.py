from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import pandas as pd
import time
import random
import re
import json
import uuid


class AmazonMobileScraper:
    def __init__(self, delay=1):  # Reduced delay from 3 to 1
        self.delay = delay
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.112 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.57 Safari/537.36"
        ]
        options = Options()
        options.add_argument(f"user-agent={random.choice(self.user_agents)}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Fast loading optimizations
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-logging")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")  # Skip images for faster loading
        options.add_argument("--page-load-strategy=eager")
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 5)  # Reduced wait time

    def close(self):
        self.driver.quit()

    def scrape_mobiles(self, search_term="realme mobile", max_pages=2):  # Reduced from 3 to 2 pages
        all_data = []
        for page in range(1, max_pages + 1):
            query = quote_plus(search_term)
            url = f"https://www.amazon.in/s?k={query}&page={page}"
            self.driver.get(url)
            
            try:
                self.wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@data-component-type='s-search-result']")))
            except:
                print(f"Timeout on page {page}, skipping...")
                continue
                
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            cards = soup.find_all("div", {"data-component-type": "s-search-result"})

            # Limit to first 15 products per page for faster processing
            for card in cards[:15]:
                try:
                    link_tag = card.find("a", href=True)
                    if not link_tag:
                        continue

                    raw_href = link_tag["href"]
                    match = re.search(r"(/dp/[A-Z0-9]{10})", raw_href)
                    product_url = f"https://www.amazon.in{match.group(1)}" if match else "N/A"
                    if product_url == "N/A":
                        continue

                    self.driver.get(product_url)
                    self.wait.until(EC.presence_of_element_located((By.ID, "productTitle")))
                    psoup = BeautifulSoup(self.driver.page_source, "html.parser")

                    product_id = str(uuid.uuid4())
                    title_tag = psoup.find("span", id="productTitle")
                    raw_title = title_tag.get_text(strip=True).replace("|", "") if title_tag else "N/A"
                    product_name = " ".join(raw_title.split()[0:3])
                    Brand = product_name.split()[0] if product_name else "N/A"

                    whole = psoup.find("span", class_="a-price-whole")
                    fraction = psoup.find("span", class_="a-price-fraction")
                    if whole:
                        whole_price = whole.get_text(strip=True).replace(',', '').replace('.', '')
                        if fraction:
                            fraction_price = fraction.get_text(strip=True)
                            price = f"₹{whole_price}.{fraction_price}"
                        else:
                            price = f"₹{whole_price}.00"
                    else:
                        price = "N/A"

                    actual_price_tag = psoup.find("span", class_="a-price a-text-price")
                    actual_price = "N/A"
                    if actual_price_tag:
                        offscreen_span = actual_price_tag.find("span", class_="a-offscreen")
                        if offscreen_span:
                            actual_price = offscreen_span.get_text(strip=True)

                    offers = []
                    offer_section = psoup.find("div", class_="a-cardui vsx__offers-holder")
                    if offer_section:
                        for block in offer_section.find_all("div", recursive=True):
                            title_elem = block.find("h6", class_="a-size-base a-spacing-micro offers-items-title")
                            value_elem = block.find("span", class_="a-truncate-full a-offscreen")
                            if title_elem and value_elem:
                                combined = f"{title_elem.get_text(strip=True)}: {value_elem.get_text(strip=True)}"
                                if combined not in offers:
                                    offers.append(combined)
                            else:
                                text = block.get_text(strip=True)
                                if text and text not in offers:
                                    offers.append(text)
                    else:
                        offers = ["No offers listed"]

                    rating_tag = psoup.select_one("#acrPopover > span.a-declarative > a > span")
                    rating = rating_tag.get_text(strip=True) if rating_tag else "N/A"

                    image_urls = set()
                    image_wrappers = psoup.find_all("div", class_="imgTagWrapper")
                    for wrapper in image_wrappers:
                        img_tag = wrapper.find("img")
                        if img_tag and img_tag.has_attr("src"):
                            image_urls.add(img_tag["src"])
                    thumbnail_items = psoup.find_all("li", class_="a-spacing-small item imageThumbnail a-declarative")
                    for item in thumbnail_items:
                        span = item.find("span", class_="a-button-text")
                        if span:
                            data_dynamic = span.get("data-a-dynamic-image")
                            if data_dynamic:
                                try:
                                    images_dict = json.loads(data_dynamic)
                                    sorted_imgs = sorted(images_dict.items(), key=lambda x: x[1][0], reverse=True)
                                    for img_url, _ in sorted_imgs:
                                        image_urls.add(img_url)
                                except json.JSONDecodeError:
                                    pass

                    image_urls = list(image_urls)
                    image_data = {
                        "thumbnail": image_urls[0] if image_urls else "N/A",
                        "urls": image_urls
                    }

                    raw_specs_table = psoup.find("table", class_="a-keyvalue prodDetTable")
                    raw_specs = {}
                    if raw_specs_table:
                        rows = raw_specs_table.find_all("tr")
                        for row in rows:
                            th = row.find("th")
                            td = row.find("td")
                            if th and td:
                                key = th.get_text(strip=True)
                                value = td.get_text(strip=True)
                                raw_specs[key] = value

                    features = {
                        "type": "mobile",
                        "details": {
                            "design": {
                                "dimensions": raw_specs.get("Product Dimensions", "").split(";")[0].strip() if "Product Dimensions" in raw_specs else "",
                                "weight": raw_specs.get("Item Weight", ""),
                                "form_factor": raw_specs.get("Form factor", ""),
                                "stylus_support": "Yes" if "Stylus" in raw_specs.get("Device interface - primary", "") else "",
                                "color": raw_specs.get("Colour", "").capitalize()
                            },
                            "display": {
                                "resolution": raw_specs.get("Resolution", ""),
                                "touchscreen": "Yes" if "Touchscreen" in raw_specs.get("Device interface - primary", "") else "",
                                "display_features": raw_specs.get("Other display features", "")
                            },
                            "network&connectivity": {
                                "wireless_tech": raw_specs.get("Wireless communication technologies", ""),
                                "connectivity": raw_specs.get("Connectivity technologies", ""),
                                "gps": raw_specs.get("GPS", ""),
                                "sim": "Dual SIM" if "Dual SIM" in raw_specs.get("Special features", "") else "",
                                "mobile_hotspot": "Yes" if "Mobile Hotspot" in raw_specs.get("Special features", "") else ""
                            },
                            "performance": {
                                "operating_system": raw_specs.get("OS", ""),
                                "model_number": raw_specs.get("Item model number", ""),
                                "processor": raw_specs.get("Processor", "")
                            },
                            "storage": {
                                "ram": "",
                                "rom": ""
                            },
                            "camera": {
                                "rear_camera": raw_specs.get("REAR CAMERA", ""),
                                "front_camera": raw_specs.get("FRONT CAMERA", ""),
                                "camera_features": raw_specs.get("Other camera features", "")
                            },
                            "battery": {
                                "battery_capacity": raw_specs.get("Battery Power Rating", "").replace("Milliamp Hours", "mAh"),
                                "battery_type": "Lithium Ion" if "Lithium Ion" in raw_specs.get("Batteries", "") else "",
                                "fast_charging": "Yes" if "Fast Charging" in raw_specs.get("Special features", "") else ""
                            },
                            "audio": {
                                "audio_jack": raw_specs.get("Audio Jack", "")
                            },
                            "box_contents": {
                                "in_the_box": raw_specs.get("Whats in the box", "")
                            },
                            "manufacturer": {
                                "brand": raw_specs.get("Manufacturer", "")
                            }
                        }
                    }

                    all_data.append({
                        "product_id": product_id,
                        "title": raw_title,
                        "brand": Brand,
                        "price": actual_price,
                        "discounted_price": price,
                        "rating": rating,
                        "offers": offers,
                        "features": features,
                        "affiliatelink": product_url,
                        "image_url": image_data,
                        "category": "smartphone"
                    })

                    time.sleep(self.delay)

                except Exception as e:
                    print(f"⚠ Skipping a product due to error: {e}")
                    continue

        return all_data

    def save_to_json(self, amazon_data, filename="amazon.json"):
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)  # ✅ ensure folder exists
            json_string = json.dumps(amazon_data, indent=4, ensure_ascii=False)
            json_string = json_string.replace('\\/', '/')
            with open(filename, "w", encoding="utf-8") as f:
                f.write(json_string)
            print(f"✅ Data saved to {filename}")
        except Exception as e:
            print(f"❌ Failed to save JSON: {e}")


if __name__ == "__main__":
    scraper = AmazonMobileScraper()
    brand_list = ["Samsung", "OnePlus", "Apple"]    #  "Realme", "Xiaomi", "Oppo", "Vivo", "iQOO", "Motorola"

    all_results = []
    try:
        for brand in brand_list:
            print(f"\n🔍 Scraping mobiles for brand: {brand}")
            results = scraper.scrape_mobiles(f"{brand} mobile", max_pages=3)
            all_results.extend(results)

        # ✅ Build save path under root/database/mobiles/
        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "mobiles"))
        os.makedirs(save_dir, exist_ok=True)  # ensures folder exists
        save_path = os.path.join(save_dir, "amazon.json")

        df = pd.DataFrame(all_results)
        df.to_json(save_path, orient="records", indent=2, force_ascii=False)
        print(df.head())

        print(f"✅ Scraping complete. {len(all_results)} products saved to {save_path}")
    finally:
        scraper.close()
