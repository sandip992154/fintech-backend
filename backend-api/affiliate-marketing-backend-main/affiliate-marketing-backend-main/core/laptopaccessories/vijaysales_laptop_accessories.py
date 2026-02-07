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
from urllib.parse import quote_plus


class VijaySalesScraper:
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

    def get_product_links(self, query, max_pages=3):
        """Fetch all product links for a given query across multiple pages"""
        links = []
        for page in range(1, max_pages + 1):
            # url = f"https://www.vijaysales.com/search-listing?q={quote_plus(query)}&Page={page}"
            url = f"https://www.vijaysales.com/search-listing?q={quote_plus(query)}&Page={page}"
            self.driver.get(url)
            try:
                self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.product-card__link")))
                time.sleep(self.delay)
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                for card in soup.find_all("a", class_="product-card__link"):
                    href = card.get("href")
                    if href:
                        if not href.startswith("http"):
                            href = "https://www.vijaysales.com" + href
                        if href not in links:
                            links.append(href)
            except Exception as e:
                print(f"⚠ Error getting product links on page {page} for {query}: {e}")
        return links

    def extract_rating(self, psoup):
        """Extract product rating if available"""
        try:
            rating_elem = psoup.find("span", class_="reviewStarText")
            if rating_elem:
                return rating_elem.get_text(strip=True)
        except Exception:
            pass
        return ""

    def extract_product_details(self, product_url, category):
        """Extract details for a single product page"""
        result = {
            "product_id": str(uuid.uuid4()),
            "title": "N/A",
            "price": "N/A",
            "discounted_price": "N/A",
            "rating": "",
            "brand": "",
            "offers": [],
            "affiliate_link": product_url,
            "category": category
        }

        try:
            self.driver.get(product_url)
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".productFullDetail__root")))
            time.sleep(self.delay)

            psoup = BeautifulSoup(self.driver.page_source, "html.parser")

            # Title
            title_el = psoup.find("h1", class_="productFullDetail__productName")
            if title_el:
                result["title"] = title_el.get_text(strip=True)
                result["brand"] = result["title"].split()[0] if result["title"] else "N/A"

            # Price & Discount
            discounted_el = psoup.find("p", class_="product__price--price offer")
            mrp_el = psoup.find("p", class_="product__price--mrp offer")
            price = mrp_el.get_text(strip=True) if mrp_el else "N/A"
            discounted_price = discounted_el.get_text(strip=True) if discounted_el else price

            result["price"] = price
            result["discounted_price"] = discounted_price

            # Rating
            result["rating"] = self.extract_rating(psoup)

            # Offers
            offers_section = psoup.find_all("div", class_="product__price--deals-card")
            unique_offers = []
            seen_texts = set()
            for section in offers_section:
                for p in section.find_all(["p", "span", "div"]):
                    text = p.get_text(strip=True)
                    if text and "view details" not in text.lower() and text not in seen_texts:
                        seen_texts.add(text)
                        unique_offers.append(text)

            result["offers"] = unique_offers if unique_offers else ["No offers found"]

        except Exception as e:
            print(f"⚠ Error scraping product: {product_url} | {e}")

        return result

    def scrape_all_products(self, queries, category, max_pages=2):
        """Scrape all products across multiple queries"""
        all_results = []
        seen_links = set()

        for query in queries:
            print(f"\n🔍 Searching for: {query}")
            product_links = self.get_product_links(query, max_pages=max_pages)
            print(f"➡ Found {len(product_links)} products for {query}")

            for i, link in enumerate(product_links, 1):
                if link in seen_links:
                    continue
                seen_links.add(link)

                print(f"[{i}/{len(product_links)}] Scraping: {link}")
                details = self.extract_product_details(link, category)
                all_results.append(details)

        return all_results

    def save_to_json(self, data, filename):
        # ✅ Ensure parent folder exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Saved {len(data)} products to {filename}")

    def close(self):
        self.driver.quit()


if __name__ == "__main__":
    scraper = VijaySalesScraper(headless=False, delay=2)
    try:
        category = "laptop accessories"

        # 🔑 Laptop accessories keywords
        accessories = [
            "keyboard",
            "mouse",
            "laptop bag"
        ]

        # Increase max_pages to fetch more products
        results = scraper.scrape_all_products(accessories, category, max_pages=2)

        # ✅ Build save path in root/database/laptopaccessories/
        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "laptopaccessories"))
        os.makedirs(save_dir, exist_ok=True)  # ensure folder exists
        save_path = os.path.join(save_dir, "vijaysales.json")

        scraper.save_to_json(results, save_path)
    finally:
        scraper.close()
