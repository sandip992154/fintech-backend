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
    def __init__(self, delay=3):
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

        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def close(self):
        self.driver.quit()

    def scrape_keyword(self, search_term="mobiles", max_pages=3, target_count=None, existing_links=None):
        """Scrape a single keyword"""
        all_data = []
        query = quote_plus(search_term)

        for page in range(1, max_pages + 1):
            url = f"https://www.amazon.in/s?k={query}&page={page}"
            print(f"\n🔎 Scraping '{search_term}' page {page} -> {url}")
            self.driver.get(url)

            try:
                self.wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@data-component-type='s-search-result']")))
            except:
                print(f"⚠ No results found on page {page}, stopping.")
                break

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            cards = soup.find_all("div", {"data-component-type": "s-search-result"})

            if not cards:
                print(f"⚠ No products on page {page}, stopping this keyword.")
                break

            for card in cards:
                try:
                    link_tag = card.find("a", href=True)
                    if not link_tag:
                        continue

                    raw_href = link_tag["href"]
                    match = re.search(r"(/dp/[A-Z0-9]{10})", raw_href)
                    product_url = f"https://www.amazon.in{match.group(1)}" if match else "N/A"
                    if product_url == "N/A":
                        continue

                    # Deduplication
                    if existing_links and product_url in existing_links:
                        continue

                    print(f"➡ Scraping product: {product_url}")
                    self.driver.get(product_url)
                    self.wait.until(EC.presence_of_element_located((By.ID, "productTitle")))
                    psoup = BeautifulSoup(self.driver.page_source, "html.parser")

                    product_id = str(uuid.uuid4())
                    title_tag = psoup.find("span", id="productTitle")
                    raw_title = title_tag.get_text(strip=True).replace("|", "") if title_tag else "N/A"
                    product_name = " ".join(raw_title.split()[0:3])
                    Brand = product_name.split()[0] if product_name else "N/A"

                    # Price
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

                    # Offers
                    offers = []
                    offer_section = psoup.find("div", class_="a-cardui vsx__offers-holder")
                    if offer_section:
                        for block in offer_section.find_all("div", recursive=True):
                            text = block.get_text(strip=True)
                            if text and text not in offers:
                                offers.append(text)
                    else:
                        offers = ["No offers listed"]

                    # Rating
                    rating_tag = psoup.select_one("#acrPopover > span.a-declarative > a > span")
                    rating = rating_tag.get_text(strip=True) if rating_tag else "N/A"

                    # Images
                    image_urls = set()
                    image_wrappers = psoup.find_all("div", class_="imgTagWrapper")
                    for wrapper in image_wrappers:
                        img_tag = wrapper.find("img")
                        if img_tag and img_tag.has_attr("src"):
                            image_urls.add(img_tag["src"])
                    image_urls = list(image_urls)
                    image_data = {
                        "thumbnail": image_urls[0] if image_urls else "N/A",
                        "urls": image_urls
                    }

                    # Specs
                    raw_specs = {}
                    raw_specs_table = psoup.find("table", class_="a-keyvalue prodDetTable")
                    if raw_specs_table:
                        rows = raw_specs_table.find_all("tr")
                        for row in rows:
                            th = row.find("th")
                            td = row.find("td")
                            if th and td:
                                raw_specs[th.get_text(strip=True)] = td.get_text(strip=True)

                    features = {
                        "type": "generic",
                        "details": {
                            "general": {
                                "model_no": raw_specs.get("Item model number", ""),
                                "description": raw_specs.get("Special features", ""),
                                "connectivity": raw_specs.get("Other display features", "")
                            }
                        }
                    }

                    all_data.append({
                        "product_id": product_id,
                        "title": raw_title,
                        "brand": Brand,
                        "price": actual_price,
                        "discounted_Price": price,
                        "rating": rating,
                        "offers": offers,
                        "features": features,
                        "affiliatelink": product_url,
                        "image_url": image_data,
                        "category": "mobile accessories"
                    })
                    print(f"✔ Scraped: {raw_title}")
                    time.sleep(self.delay)

                    # Stop if we already hit target
                    if target_count and len(all_data) >= target_count:
                        return all_data

                except Exception as e:
                    print(f"⚠ Skipping product due to error: {e}")
                    continue

        return all_data

    def scrape_multiple_keywords(self, keywords, max_pages=2, target_count=50):
        """Scrape multiple search keywords until we reach target_count"""
        all_data = []
        seen_links = set()

        for keyword in keywords:
            if len(all_data) >= target_count:
                break
            results = self.scrape_keyword(keyword, max_pages=max_pages, target_count=target_count - len(all_data), existing_links=seen_links)
            for r in results:
                seen_links.add(r["affiliatelink"])
            all_data.extend(results)
            print(f"✅ Collected {len(all_data)} items so far...")

        return all_data

    def save_to_json(self, amazon_data, filename="amazon.json"):
        try:
            # ✅ Ensure folder exists under root/database/mobileaccessories/
            save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "mobileaccessories"))
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, filename)

            json_string = json.dumps(amazon_data, indent=4, ensure_ascii=False)
            json_string = json_string.replace('\\/', '/')
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(json_string)

            print(f"✅ Data saved to {save_path}")
        except Exception as e:
            print(f"❌ Failed to save JSON: {e}")


if __name__ == "__main__":
    scraper = AmazonMobileScraper()
    try:
        # Multiple search terms to go beyond 100 results
        keywords = [
            "mobile charger",
            "phone case",
            "USB charger",
            "charging adapter"
        ]  # ,"Memory card","mobile charging cable","wireless charger","power bank","headphones","earphones","mobile screen protector"

        results = scraper.scrape_multiple_keywords(keywords, max_pages=2, target_count=50)

        # ✅ Save DataFrame JSON under same folder
        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "mobileaccessories"))
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, "amazon.json")

        df = pd.DataFrame(results)
        df.to_json(save_path, orient="records", indent=2, force_ascii=False)
        print(df.head())
        print(f"✅ Scraping complete. Total products saved to {save_path}")
    finally:
        scraper.close()
