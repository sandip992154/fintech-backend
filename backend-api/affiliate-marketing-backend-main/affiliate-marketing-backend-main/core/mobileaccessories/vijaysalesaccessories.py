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


# 📦 List of mobile accessories to scrape
ACCESSORIES_LIST = [
            "mobile charger",
            "phone case",
            "USB charger",
            "charging adapter"
]


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
                page_links = []
                for card in soup.find_all("a", class_="product-card__link"):
                    href = card.get("href")
                    if href:
                        if not href.startswith("http"):
                            href = "https://www.vijaysales.com" + href
                        page_links.append(href)

                if not page_links:
                    print(f"No products found on page {page}, stopping...")
                    break

                links.extend(page_links)

                # stop once we reach ~550 products
                if len(links) >= 80:
                    print("Reached 550 products limit, stopping...")
                    break

            except Exception as e:
                print(f"Error getting product links on page {page}: {e}")
                break

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
            "price": "N/A",
            "discounted_price": "N/A",
            "rating": "",
            "brand": "",
            "offers": [],
            "affilatelink": product_url,
            "category": category
        }

        try:
            self.driver.get(product_url)
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".productFullDetail__root")))
            time.sleep(2)

            psoup = BeautifulSoup(self.driver.page_source, "html.parser")

            title_el = psoup.find("h1", class_="productFullDetail__productName")
            price_el = psoup.find("p", class_="product__price--price offer")
            price_wrapper = psoup.find("p", class_="product__price--mrp offer")
            price_span = price_wrapper.find("span") if price_wrapper else None
            price = price_span.get_text(strip=True) if price_span else "N/A"

            result["title"] = title_el.get_text(strip=True) if title_el else "N/A"
            result["price"] = price
            result["discounted_price"] = price_el.get_text(strip=True) if price_el else "N/A"
            result["brand"] = result["title"].split()[0] if title_el else "N/A"
            result["rating"] = self.extract_rating()

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

    def scrape_all_products(self, query, category):
        print(f"Searching for: {query}")
        product_links = self.get_product_links(query, max_pages=7)  # increased max_pages
        print(f"Found {len(product_links)} products")

        all_results = []
        for i, link in enumerate(product_links, 1):
            print(f"[{i}/{len(product_links)}] Scraping: {link}")
            details = self.extract_product_details(link, category)
            all_results.append(details)

        return all_results

    def save_to_json(self, data, filename):
    # ✅ Ensure folder exists under root/database/mobileaccessories/
        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "mobileaccessories"))
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved data to {save_path}")

    def close(self):
        self.driver.quit()


if __name__ == "__main__":
    scraper = VijaySalesScraper()
    try:
        all_data = []
        for accessory in ACCESSORIES_LIST:
            print(f"\n🔎 Scraping Accessory: {accessory}")
            results = scraper.scrape_all_products(accessory, accessory)
            all_data.extend(results)

        scraper.save_to_json(all_data, 'vijaysales.json')
    finally:
        scraper.close()
