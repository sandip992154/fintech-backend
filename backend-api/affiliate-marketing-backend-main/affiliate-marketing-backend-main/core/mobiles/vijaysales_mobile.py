from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
import json
import re
import uuid
import os


class VijaySalesScraper:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 15)

    def get_product_links(self, query, max_pages=3):
        links = []
        for page in range(1, max_pages + 1):
            url = f"https://www.vijaysales.com/search-listing?q={quote_plus(query)}&Page={page}"
            self.driver.get(url)
            try:
                self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.product-card__link")))
                time.sleep(2)
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                for card in soup.find_all("a", class_="product-card__link"):
                    href = card.get("href")
                    if href:
                        if not href.startswith("http"):
                            href = "https://www.vijaysales.com" + href
                        links.append(href)
            except Exception as e:
                print(f"Error getting product links on page {page}: {e}")
        return links

    def extract_rating(self):
        try:
            rating_elem = self.driver.find_element(By.XPATH, '//*[@id="reviewBtn"]/p')
            rating_text = rating_elem.text.strip()
            if rating_text:
                rating = re.search(r"\d+(\.\d+)?", rating_text)
                return rating.group(0) if rating else ""
        except Exception:
            pass
        return ""

    def extract_product_details(self, product_url, category):
        result = {
            "product_id": str(uuid.uuid4()),
            "title": "N/A",
            "brand": "N/A",
            "price": "N/A",
            "discounted_price": "N/A",
            "rating": "N/A",
            "offers": [],
            "affiliatelink": product_url,
            "category": category
        }

        try:
            self.driver.get(product_url)
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".productFullDetail__root")))
            time.sleep(2)

            psoup = BeautifulSoup(self.driver.page_source, "html.parser")

            # Title
            title_el = psoup.find("h1", class_="productFullDetail__productName")
            result["title"] = title_el.get_text(strip=True) if title_el else "N/A"
            result["brand"] = result["title"].split()[0] if result["title"] != "N/A" else "N/A"

            # Prices
            price_el = psoup.find("p", class_="product__price--price offer")
            price_wrapper = psoup.find("p", class_="product__price--mrp offer")
            price_span = price_wrapper.find("span") if price_wrapper else None

            if price_span:
                result["price"] = price_span.get_text(strip=True)
            if price_el:
                result["discounted_price"] = price_el.get_text(strip=True)

            # Rating
            result["rating"] = self.extract_rating()

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
            print(f"Error scraping product: {product_url} | {e}")

        return result

    def scrape_all_products_on_first_page(self, query, category):
        print(f"Searching for: {query}")
        product_links = self.get_product_links(query, max_pages=3)
        print(f"Found {len(product_links)} products")

        all_results = []
        for i, link in enumerate(product_links, 1):
            print(f"[{i}/{len(product_links)}] Scraping: {link}")
            details = self.extract_product_details(link, category)
            all_results.append(details)

        return all_results

    def save_to_json(self, data, filename="vijaysales.json"):
        # ✅ Build path under root/database/mobiles/
        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "mobiles"))
        os.makedirs(save_dir, exist_ok=True)  # ensures folder exists
        save_path = os.path.join(save_dir, filename)

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ Saved data to {save_path}")

    def close(self):
        self.driver.quit()


if __name__ == "__main__":
    scraper = VijaySalesScraper()
    try:
        category = "smartphone"
        brands = ["Samsung", "OnePlus","Apple"]

        all_results = []
        for brand in brands:
            print(f"\n🔍 Scraping mobiles for brand: {brand}")
            results = scraper.scrape_all_products_on_first_page(f"{brand} mobile", category)
            all_results.extend(results)

        scraper.save_to_json(all_results, "vijaysales.json")
    finally:
        scraper.close()
