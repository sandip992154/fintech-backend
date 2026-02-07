import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import quote_plus


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

    def extract_offers_as_key_value(self, offer_section):
        offers = {}
        current_section = None
        counter = {}

        for element in offer_section.find_all(["div", "h4", "p", "li", "span"]):
            text = element.get_text(strip=True)
            if not text:
                continue

            if text.upper().endswith("OFFERS") and "AVAILABLE" not in text.upper():
                current_section = text.title().replace(" ", "_")
                counter[current_section] = 1
            elif current_section and "Offer/s Available" not in text and "View All" not in text:
                key = f"{current_section}_{counter[current_section]}"
                if text not in offers.values():
                    offers[key] = text
                    counter[current_section] += 1

        return offers

    def extract_specifications(self, psoup):
        specs = {}
        spec_table = psoup.find("table", class_="product-specifications-table")

        if not spec_table:
            return {"Info": "No specifications found"}

        for row in spec_table.find_all("tr"):
            key_tag = row.find("th")
            value_tag = row.find("td")
            if key_tag and value_tag:
                key = key_tag.get_text(strip=True)
                value = value_tag.get_text(strip=True)
                specs[key] = value

        return specs if specs else {"Info": "No specifications available"}

    def scrape_products(self, search_query: str, max_scrolls: int = 30):
        products = []

        try:
            self.driver.get("https://www.jiomart.com/")
            search_box = self.wait.until(EC.presence_of_element_located((By.ID, "autocomplete-0-input")))
            search_box.clear()
            search_box.send_keys(search_query)
            search_box.send_keys(Keys.RETURN)

            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "ais-InfiniteHits-item")))
            time.sleep(self.delay)

            product_selector = "li.ais-InfiniteHits-item"
            last_count = 0
            for scroll_count in range(max_scrolls):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(self.delay)
                new_count = len(self.driver.find_elements(By.CSS_SELECTOR, product_selector))
                if new_count == last_count:
                    print(f" No new products after scroll #{scroll_count + 1}. Total loaded: {new_count}")
                    break
                print(f" Scrolled #{scroll_count + 1} — Loaded: {new_count} products")
                last_count = new_count

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            product_items = soup.select(product_selector)

            print(f"Found {len(product_items)} products.")

            for idx, item in enumerate(product_items, start=1):
                title_tag = item.find("div", class_="plp-card-details-name")
                price_tag = item.find("span", class_="jm-heading-xxs")
                actual_price_tag = item.find("span", class_="line-through")
                a_tag = item.find("a", href=True)

                title = title_tag.get_text(strip=True) if title_tag else "N/A"
                if "ram" not in title.lower():
                    print(f" Skipping product {idx} due to missing 'ram' in title: {title}")
                    continue

                words = title.split(" ", 3)[0:3]
                product_title = " ".join(words)
                price = price_tag.text.strip() if price_tag else "N/A"
                actual_price = actual_price_tag.get_text(strip=True) if actual_price_tag else "N/A"
                product_url = "https://www.jiomart.com" + a_tag['href'] if a_tag else None
                offers = {}
                specifications = {}

                if product_url:
                    try:
                        self.driver.get(product_url)
                        time.sleep(self.delay)
                        psoup = BeautifulSoup(self.driver.page_source, "html.parser")

                        offer_section = psoup.find("div", class_="product-offers-list jm-mb-xs")
                        offers = self.extract_offers_as_key_value(offer_section) if offer_section else {"Info": "No offers available"}

                        specifications = self.extract_specifications(psoup)

                    except Exception as e:
                        print(f" Failed to extract product page data from {product_url}: {e}")
                        offers = {"Error": "Offer parsing failed"}
                        specifications = {"Error": "Specification parsing failed"}

                products.append({
                    "Index": idx,
                    "Title": title,
                    "product_title": product_title,
                    "actual_price": actual_price,
                    "Price": price,
                    "Offers": offers,
                    "Specifications": specifications,
                    "Product URL": product_url or "N/A"
                })
                print(f"[{idx}] Scraped: {title}")

        except Exception as e:
            print(f"❗ Error: {e}")

        return products

    def save_to_json(self, jiomart_data, filename="../database/mobilescrapdata.json"):
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(jiomart_data, f, indent=4, ensure_ascii=False)
            print(f"✅ Data saved to '{filename}'")
        except Exception as e:
            print(f"❌ Failed to save JSON: {e}")

    def close(self):
        self.driver.quit()


# # Usage
# if __name__ == "__main__":
#     scraper = JioMartScraper(headless=False, delay=2)
#     try:
#         results = scraper.scrape_products("IQOO mobiles", max_scrolls=5)
#         scraper.save_to_json(results, "jiomart_redmi_first_page.json")
#     finally:
#         scraper.close()
