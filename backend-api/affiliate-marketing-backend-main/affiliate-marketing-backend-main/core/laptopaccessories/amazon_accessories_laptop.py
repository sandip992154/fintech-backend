import time
import random
import re
import os
import json
import uuid
import pandas as pd
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class AmazonLaptopAccessoriesScraper:
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
        options.add_experimental_option("useAutomationExtension", False)

        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 20)

    def close(self):
        self.driver.quit()

    def scroll_page(self):
        """Scrolls the Amazon search page to load all results."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def scrape_products(self, search_term="keyboard", max_pages=3):
        """Scrape product details for a given search term."""
        all_data = []
        for page in range(1, max_pages + 1):
            query = quote_plus(search_term)
            url = f"https://www.amazon.in/s?k={query}&page={page}"
            print(f"📄 Scraping {search_term} (Page {page}/{max_pages})")
            self.driver.get(url)

            # Detect captcha block
            if "Enter the characters you see below" in self.driver.page_source:
                print("⚠ Captcha detected! Skipping this page...")
                continue

            try:
                self.wait.until(EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "div.s-main-slot div.s-result-item")
                ))
                self.scroll_page()
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                cards = soup.find_all("div", {"data-component-type": "s-search-result"})
            except Exception as e:
                print(f"❌ Error loading search results: {e}")
                continue

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

                    # Retry product page load
                    for attempt in range(2):
                        try:
                            self.driver.get(product_url)
                            self.wait.until(EC.presence_of_element_located((By.ID, "productTitle")))
                            break
                        except:
                            time.sleep(3)
                    psoup = BeautifulSoup(self.driver.page_source, "html.parser")

                    product_id = str(uuid.uuid4())
                    title_tag = psoup.find("span", id="productTitle")
                    raw_title = title_tag.get_text(strip=True).replace("|", "") if title_tag else "N/A"
                    product_name = " ".join(raw_title.split()[0:3])
                    brand = product_name.split()[0] if product_name else "N/A"

                    # Price
                    whole = psoup.find("span", class_="a-price-whole")
                    fraction = psoup.find("span", class_="a-price-fraction")
                    if whole:
                        whole_price = whole.get_text(strip=True).replace(',', '').replace('.', '')
                        price = f"₹{whole_price}.{fraction.get_text(strip=True) if fraction else '00'}"
                    else:
                        price = "N/A"

                    actual_price = "N/A"
                    actual_price_tag = psoup.find("span", class_="a-price a-text-price")
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
                    if not offers:
                        offers = ["No offers listed"]

                    # Rating
                    rating_tag = psoup.select_one("#acrPopover span.a-declarative a span")
                    rating = rating_tag.get_text(strip=True) if rating_tag else "N/A"

                    # Images
                    image_urls = set()
                    for wrapper in psoup.find_all("div", class_="imgTagWrapper"):
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
                        for row in raw_specs_table.find_all("tr"):
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
                        "brand": brand,
                        "price": actual_price,
                        "discounted_Price": price,
                        "rating": rating,
                        "offers": offers,
                        "features": features,
                        "affiliatelink": product_url,
                        "image_url": image_data,
                        "category": search_term
                    })

                    time.sleep(self.delay)
                except Exception as e:
                    print(f"⚠ Skipping product due to error: {e}")
                    continue

        return all_data


if __name__ == "__main__":
    accessories = [
        "keyboard",
        "mouse"
    ]  # "laptop bag","cooling pad","laptop stand","usb hub","external hard drive"

    scraper = AmazonLaptopAccessoriesScraper()
    try:
        all_results = []
        for item in accessories:
            print(f"\n🔍 Scraping category: {item}")
            results = scraper.scrape_products(item, max_pages=3)  # increase pages to hit ~650 results
            all_results.extend(results)

        # ✅ Build save path in root/database/laptopaccessories/
        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "laptopaccessories"))
        os.makedirs(save_dir, exist_ok=True)  # ensures folder exists

        save_path = os.path.join(save_dir, "amazon.json")

        df = pd.DataFrame(all_results)
        df.to_json(save_path, orient="records", indent=2, force_ascii=False)
        print(f"✅ Scraping completed. {len(all_results)} products saved to {save_path}")
    finally:
        scraper.close()
