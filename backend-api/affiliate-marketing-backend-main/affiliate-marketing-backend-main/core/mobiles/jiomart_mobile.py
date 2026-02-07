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

    def extract_offers(self, offer_section):
        offers = []
        for element in offer_section.find_all(["div", "h4", "p", "li", "span"]):
            text = element.get_text(strip=True)
            if text and "view all" not in text.lower():
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

    def scrape_products(self, max_scrolls=35):
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "ais-InfiniteHits-item")))

        products = []
        last_count = 0
        product_selector = "li.ais-InfiniteHits-item"

        # scroll through product list
        for _ in range(max_scrolls):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(self.delay)
            new_count = len(self.driver.find_elements(By.CSS_SELECTOR, product_selector))
            if new_count == last_count:
                break
            last_count = new_count

        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        product_items = soup.select(product_selector)

        for item in product_items:
            title_tag = item.find("div", class_="plp-card-details-name")
            price_tag = item.find("span", class_="jm-heading-xxs")
            actual_price_tag = item.find("span", class_="line-through")
            a_tag = item.find("a", href=True)

            title = title_tag.get_text(strip=True) if title_tag else "N/A"
            if not title:
                continue

            product_name = title
            brand = product_name.split()[0] if product_name else " "
            product_url = a_tag['href'] if a_tag else None
            if not product_url:
                continue

            product_id = str(uuid.uuid4())
            discounted_price = price_tag.text.strip() if price_tag else "N/A"
            actual_price = actual_price_tag.get_text(strip=True) if actual_price_tag else discounted_price

            try:
                self.driver.get(product_url)
                time.sleep(self.delay)
                psoup = BeautifulSoup(self.driver.page_source, "html.parser")
                offer_section = psoup.find("div", class_="product-offers-list jm-mb-xs")
                offers = self.extract_offers(offer_section) if offer_section else []
                rating = self.extract_rating(psoup)
            except Exception as e:
                print(f"Error loading product page: {e}")
                continue

            products.append({
                "product_id": product_id,
                "title": product_name,
                "brand": brand,
                "price": actual_price,
                "discounted_price": discounted_price,
                "rating": rating,
                "offers": offers if offers else ["No offers found"],
                "affiliatelink": product_url,
                "category": "smartphone"
            })

        return products

    def save_to_json(self, data, filename=None):
        if not filename:
            # ✅ Save under root/database/mobiles/
            save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "mobiles"))
            os.makedirs(save_dir, exist_ok=True)  # ensures folder exists
            filename = os.path.join(save_dir, "jiomart.json")

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def close(self):
        self.driver.quit()


if __name__ == "__main__":
    brand_list = ["Apple", "Samsung", "OnePlus"]
    max_scrolls = 5
    all_products = []

    for brand in brand_list:
        print(f"\nScraping brand: {brand}")
        scraper = JioMartScraper(headless=False)
        brand_url = f"https://www.jiomart.com/search/{brand}"
        scraper.driver.get(brand_url)
        time.sleep(scraper.delay)

        try:
            products = scraper.scrape_products(max_scrolls=max_scrolls)
            all_products.extend(products)
        except Exception as e:
            print(f"Failed to scrape brand '{brand}': {e}")
        finally:
            scraper.close()

    # ✅ Save JSON under root/database/mobiles/
    save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "mobiles"))
    os.makedirs(save_dir, exist_ok=True)  # ensures folder exists
    output_file = os.path.join(save_dir, "jiomart.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_products, f, indent=4, ensure_ascii=False)

    print(f"\nScraping complete. Total products scraped: {len(all_products)}")
