from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
import random
import re
import json
import uuid
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class AmazonLaptopScraper:
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

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.wait = WebDriverWait(self.driver, 20)

    def close(self):
        self.driver.quit()

    def scrape_laptop(self, search_term="laptop", max_pages=5):
        all_data = []
        for page in range(1, max_pages + 1):
            query = quote_plus(search_term)
            url = f"https://www.amazon.in/s?k={query}&page={page}"
            self.driver.get(url)

            if "Enter the characters you see" in self.driver.page_source:
                print("🚨 Amazon CAPTCHA detected. Skipping this page.")
                time.sleep(10)
                continue

            try:
                self.wait.until(EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "div.s-main-slot div[data-component-type='s-search-result']")))
            except Exception:
                print(f"⚠ No results found or page structure changed at {url}")
                continue

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            cards = soup.select("div.s-main-slot div[data-component-type='s-search-result']")

            for card in cards:
                try:
                    link_tag = card.find("a", href=True)
                    if not link_tag:
                        continue

                    raw_href = link_tag["href"]
                    match = re.search(r"(/dp/[A-Z0-9]{10})", raw_href)
                    product_url = f"https://www.amazon.in{match.group(1)}" if match else "N/A"
                    print(f"Scraping product URL: {product_url}")
                    if product_url != "N/A" and product_url.startswith("http"):
                        self.driver.get(product_url)
                    else:
                        continue

                    self.wait.until(EC.presence_of_element_located((By.ID, "productTitle")))
                    psoup = BeautifulSoup(self.driver.page_source, "html.parser")
                    product_id = str(uuid.uuid4())

                    title_tag = psoup.find("span", id="productTitle")
                    raw_title = title_tag.get_text(strip=True).replace("|", "") if title_tag else "N/A"
                    product_name = " ".join(raw_title.split()[0:3])
                    Brand = product_name.split()[0] if product_name else "N/A"
                    Brand = Brand.capitalize()

                    # Extract discounted price (numeric only)
                    whole = psoup.find("span", class_="a-price-whole")
                    fraction = psoup.find("span", class_="a-price-fraction")
                    if whole:
                        whole_price = whole.get_text(strip=True).replace(',', '').replace('.', '')
                        if fraction:
                            fraction_price = fraction.get_text(strip=True)
                            discounted_price = f"{whole_price}{fraction_price}"
                        else:
                            discounted_price = f"{whole_price}"
                    else:
                        discounted_price = "N/A"

                    # Extract actual/original price
                    actual_price_tag = psoup.find("span", class_="a-price a-text-price")
                    price = "N/A"
                    if actual_price_tag:
                        offscreen_span = actual_price_tag.find("span", class_="a-offscreen")
                        if offscreen_span:
                            price = offscreen_span.get_text(strip=True).replace("₹", "").replace(",", "")

                    # Extract offers
                    offers = []
                    offer_section = psoup.find("div", class_="a-cardui vsx__offers-holder")
                    if offer_section:
                        for block in offer_section.find_all("div", recursive=True):
                            text = block.get_text(strip=True)
                            if text and text not in offers:
                                offers.append(text)
                    else:
                        offers = ["No offers listed"]

                    # Extract rating (numeric only)
                    rating_tag = psoup.select_one("#acrPopover > span.a-declarative > a > span")
                    rating = "N/A"
                    if rating_tag:
                        rating_text = rating_tag.get_text(strip=True)
                        rating_match = re.search(r"[\d.]+", rating_text)
                        rating = rating_match.group(0) if rating_match else "N/A"

                    # Extract model number
                    raw_specs_table = psoup.find("table", class_="a-keyvalue prodDetTable")
                    model_number = "N/A"
                    if raw_specs_table:
                        rows = raw_specs_table.find_all("tr")
                        for row in rows:
                            th = row.find("th")
                            td = row.find("td")
                            if th and td:
                                key = th.get_text(strip=True)
                                value = td.get_text(strip=True)
                                if key.lower() == "item model number":
                                    model_number = value

                    all_data.append({
                        "product_id": product_id,
                        "title": raw_title,
                        "discounted_price": discounted_price,
                        "price": price,
                        "rating": rating,
                        "model_number": model_number,
                        "brand": Brand,
                        "offers": offers,
                        "category": "laptop",
                        "affiliatelink": product_url
                    })
                    print(f"✔ Scraped: {raw_title}")
                    time.sleep(self.delay)

                except Exception as e:
                    print(f"Skipping a product due to error: {e}")
                    continue

        return all_data

    def save_to_json(self, amazon_data, filename="amazon.json"):
        try:
            json_string = json.dumps(amazon_data, indent=4, ensure_ascii=False)
            json_string = json_string.replace('\\/', '/')
            with open(filename, "w", encoding="utf-8") as f:
                f.write(json_string)
            print(f"✅ Data saved to {filename}")
        except Exception as e:
            print(f"❌ Failed to save JSON: {e}")


if __name__ == "__main__":
    import os

    scraper = AmazonLaptopScraper()
    final_data = []

    try:
        brands = ["lenovo", "asus", "dell"]   #  "hp", "apple", "acer", "samsung"
        for brand in brands:
            print(f"\n🔍 Scraping laptops for brand: {brand}")
            results = scraper.scrape_laptop(f"{brand} laptop", max_pages=2)
            final_data.extend(results)
            time.sleep(3)

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        save_path = os.path.join(project_root, "database", "laptop", "amazon.json")

        scraper.save_to_json(final_data, filename=save_path)

    finally:
        scraper.close()
