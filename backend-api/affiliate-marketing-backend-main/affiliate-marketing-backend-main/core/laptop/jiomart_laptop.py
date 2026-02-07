import os 
import time
import json
import uuid
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


class JioMartScraper:
    def __init__(self, headless=True, delay=2):
        self.delay = delay
        self.driver = self.create_driver(headless)
        self.wait = WebDriverWait(self.driver, 20)

    def create_driver(self, headless=True):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        return webdriver.Chrome(options=options)

    def extract_specifications(self, psoup):
        text = psoup.get_text(" ", strip=True).lower()
        specs = {"ram": "", "storage": "", "display": "", "camera": "", "battery": ""}

        ram_match = re.search(r'(\d+\s?gb\s?ram)', text)
        if ram_match:
            specs["ram"] = ram_match.group(1).upper()

        storage_match = re.search(r'(\d+\s?gb\s?(internal|rom|storage)[^.,]*)', text)
        expandable_match = re.search(r'(expandable[^.,]*)', text)
        storage_parts = []
        if storage_match:
            storage_parts.append(storage_match.group(1).strip().title())
        if expandable_match:
            storage_parts.append(expandable_match.group(1).strip().title())
        specs["storage"] = ", ".join(storage_parts)

        resolution = re.search(r'screen resolution[:\-]?\s*(\d+\s?[x×]\s?\d+)', text)
        screen_size = re.search(r'screen size.*?(\d{1,2}\.\d{1,2}\s?cm\s?-\s?\d{1,2}\.\d{1,2}\s?inch)', text)
        display_parts = []
        if resolution:
            display_parts.append(f"Resolution: {resolution.group(1).upper()}")
        if screen_size:
            display_parts.append(screen_size.group(1).title())
        specs["display"] = ", ".join(display_parts)

        rear = re.search(r'rear camera[:\-]?\s*(\d+\s?mp)', text)
        front = re.search(r'front camera[:\-]?\s*(\d+\s?mp)', text)
        rear_text = rear.group(1).upper() if rear else ""
        front_text = front.group(1).upper() if front else ""
        if rear_text and front_text:
            specs["camera"] = f"Rear {rear_text} | Front {front_text}"
        elif rear_text:
            specs["camera"] = f"Rear {rear_text}"
        elif front_text:
            specs["camera"] = f"Front {front_text}"

        battery_match = re.search(r'(\d{4,5}\s?mah)', text)
        if battery_match:
            specs["battery"] = battery_match.group(1).upper()

        return specs

    def extract_offers(self, offer_section):
        offers = []
        current_section = None
        for element in offer_section.find_all(["div", "h4", "p", "li", "span"]):
            text = element.get_text(strip=True)
            if not text:
                continue
            if text.upper().endswith("OFFERS") and "AVAILABLE" not in text.upper():
                current_section = text.title().replace(" ", "_")
            elif current_section and "Offer/s Available" not in text and "View All" not in text:
                if text not in offers:
                    offers.append(text)
        return offers

    def extract_rating(self, psoup):
        try:
            rating_container = psoup.find("div", class_="feedback-service-rating-content")
            if rating_container:
                inner_div = rating_container.find("div")
                if inner_div:
                    rating_span = inner_div.find("span", class_="feedback-service-avg-rating-font feedback-service-top-text")
                    if rating_span:
                        return rating_span.get_text(strip=True)
        except Exception:
            pass
        return ""

    def extract_mobile_features(self, psoup):
        features = {
            "type": "laptop",
            "details": {
                "Storage": {"RAM": "", "ROM": ""},
                "Design": {"Dimensions": "", "Weight": "", "Form Factor": "", "Stylus Support": "", "Color": ""},
                "Display": {"Screen Size": "", "Screen Resolution": "", "Touch Screen": "", "Display Features": ""},
                "Performance": {"Processor": "", "Cores": "", "GPU": "", "Operating System": "", "model_number": ""},
                "Network & Connectivity": {"Wireless Tech": "", "Connectivity": "", "GPS": "", "SIM": "", "Mobile Hotspot": ""},
                "Camera": {"Rear Camera": "", "Front Camera": "", "Camera Features": ""},
                "Battery": {"Battery Capacity": "", "Battery Type": "", "Fast Charging": ""},
                "Audio": {"Audio Jack": ""},
                "Box Contents": {"In the Box": ""},
                "Manufacturer": {"Brand": ""}
            }
        }

        specs_section = psoup.find("div", class_="product-specifications-wrapper")
        raw_specs = {}
        if specs_section:
            for tr in specs_section.find_all("tr", class_="product-specifications-table-item"):
                th = tr.find("th", class_="product-specifications-table-item-header")
                td = tr.find("td", class_="product-specifications-table-item-data")
                if th and td:
                    raw_specs[th.get_text(strip=True).upper()] = td.get_text(strip=True)

        f = features["details"]
        f["Storage"]["RAM"] = raw_specs.get("MEMORY (RAM)", "")
        f["Storage"]["ROM"] = raw_specs.get("INTERNAL STORAGE", "")
        f["Manufacturer"]["Brand"] = raw_specs.get("BRAND", "")
        f["Display"]["Screen Resolution"] = raw_specs.get("SCREEN RESOLUTION", "")
        f["Display"]["Screen Size"] = raw_specs.get("SCREEN SIZE (DIAGONAL)", "")
        f["Battery"]["Battery Capacity"] = raw_specs.get("BATTERY CAPACITY", "")
        f["Display"]["Touch Screen"] = "Yes" if "TOUCHSCREEN" in raw_specs else ""
        f["Design"]["Color"] = raw_specs.get("COLOR", "").capitalize()
        f["Display"]["Display Features"] = raw_specs.get("DISPLAY TYPE", "")
        f["Design"]["Dimensions"] = raw_specs.get("DIMENSIONS", "")
        f["Design"]["Weight"] = raw_specs.get("NET WEIGHT", "")
        f["Performance"]["Processor"] = raw_specs.get("PROCESSOR", "")
        f["Performance"]["Cores"] = raw_specs.get("CORES", "")
        f["Performance"]["GPU"] = raw_specs.get("GPU", "")
        f["Network & Connectivity"]["SIM"] = raw_specs.get("SIM TYPE", "")
        f["Network & Connectivity"]["Connectivity"] = raw_specs.get("BLUETOOTH", "")
        f["Network & Connectivity"]["GPS"] = raw_specs.get("GPS", "")
        f["Network & Connectivity"]["Mobile Hotspot"] = raw_specs.get("WI-FI", "")
        f["Performance"]["Operating System"] = raw_specs.get("OPERATING SYSTEM", "")
        f["Performance"]["model_number"] = raw_specs.get("MODEL", "")
        f["Battery"]["Fast Charging"] = raw_specs.get("QUICK CHARGE", "")
        f["Battery"]["Battery Type"] = raw_specs.get("BATTERY TYPE", "")
        f["Camera"]["Rear Camera"] = raw_specs.get("REAR CAMERA", "")
        f["Camera"]["Front Camera"] = raw_specs.get("SELFIE CAMERA", "")
        f["Camera"]["Camera Features"] = raw_specs.get("CAMERA FEATURES", "")
        f["Audio"]["Audio Jack"] = raw_specs.get("AUDIO JACK", "")
        f["Design"]["Form Factor"] = raw_specs.get("FORM FACTOR", "")
        f["Box Contents"]["In the Box"] = raw_specs.get("IN THE BOX", "")

        return features

    def scrape_products(self, max_scrolls=80):
        products = []
        product_selector = "li.ais-InfiniteHits-item"
        brands = ["lenovo", "asus", "dell"]  # Filter brands as requested

        for page in range(1, 9):
            url = f"https://www.jiomart.com/c/electronics/computers-accessories/laptops-desktops/31996?prod_mart_master_vertical_products_popularity%5Bpage%5D={page}"
            self.driver.get(url)

            try:
                self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, product_selector)))
            except Exception as e:
                print(f"Page {page}: Timeout waiting for products - {e}")
                continue

            time.sleep(self.delay)

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            product_items = soup.select(product_selector)
            print(f"Page {page}: Found {len(product_items)} product items")  # Debug info

            for item in product_items:
                title_tag = item.find("div", class_="plp-card-details-name")
                price_tag = item.find("span", class_="jm-heading-xxs")
                actual_price_tag = item.find("span", class_="line-through")
                a_tag = item.find("a", href=True)
                title = title_tag.get_text(strip=True) if title_tag else "N/A"

                if not any(b in title.lower() for b in brands):
                    continue

                brand = title.split()[0] if title else ""
                product_url = "https://www.jiomart.com" + a_tag['href'] if a_tag else None
                if not product_url:
                    continue

                print(f"Scraping product URL: {product_url}")

                product_id = str(uuid.uuid4())
                discounted_price = price_tag.text.strip() if price_tag else "N/A"
                actual_price = actual_price_tag.get_text(strip=True) if actual_price_tag else discounted_price

                try:
                    self.driver.get(product_url)

                    # Wait until the main specs wrapper is loaded before continuing
                    self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "product-specifications-wrapper")))
                    time.sleep(self.delay)

                    psoup = BeautifulSoup(self.driver.page_source, "html.parser")
                    offer_section = psoup.find("div", class_="product-offers-list jm-mb-xs")
                    offers = self.extract_offers(offer_section) if offer_section else []
                    rating = self.extract_rating(psoup)
                    features = self.extract_mobile_features(psoup)
                    specifications = self.extract_specifications(psoup)

                    # Overwrite RAM and Storage ROM if specifications parsing found data
                    if specifications["ram"]:
                        features["details"]["Storage"]["RAM"] = specifications["ram"]
                    if specifications["storage"]:
                        features["details"]["Storage"]["ROM"] = specifications["storage"]

                    model_number = features["details"]["Performance"].get("model_number", "")

                    products.append({
                        "product_id": product_id,
                        "title": title,
                        "discounted_price": discounted_price,
                        "price": actual_price,
                        "rating": rating,
                        "model_number": model_number,
                        "brand": brand,
                        "offers": offers,
                        "affiliatelink": product_url,
                        "category": "laptop"
                    })

                except Exception as e:
                    print(f"Error loading product page: {e}", flush=True)
                    continue

        return products

    def save_to_json(self, data, filename=None):
        if not filename:
            filename = os.path.join(os.path.dirname(__file__), "..", "database", "laptop", "jiomart.json")
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def close(self):
        self.driver.quit()


if __name__ == "__main__":
    max_scrolls = 80
    scraper = JioMartScraper(headless=False)
    time.sleep(scraper.delay)

    try:
        products = scraper.scrape_products(max_scrolls=max_scrolls)
        scraper.save_to_json(products)
    except Exception as e:
        print(f"Scraping failed: {e}")
    finally:
        scraper.close()

    # print(f"\nScraping complete. Total products scraped: {len(products)}")
