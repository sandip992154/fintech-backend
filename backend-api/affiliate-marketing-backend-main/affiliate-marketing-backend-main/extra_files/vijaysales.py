from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
import json
import re


class VijaySalesScraper:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 15)

    def get_product_links(self, query):
        url = f"https://www.vijaysales.com/search-listing?q={quote_plus(query)}&Page=1"
        self.driver.get(url)
        try:
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.product-card__link")))
            time.sleep(2)
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            links = []

            for card in soup.find_all("a", class_="product-card__link"):
                href = card.get("href")
                if href:
                    if not href.startswith("http"):
                        href = "https://www.vijaysales.com" + href
                    links.append(href)
            return links
        except Exception as e:
            print(f"Error getting product links: {e}")
            return []

    def extract_product_details(self, product_url):
        result = {
            "Title": "N/A",
            "Product_title": "N/A",
            "Price": "N/A",
            "actual_price": "N/A",
            "Offers": {"bankk_offer": {}},
            "Specifications": {"Key Features": []},
            "URL": product_url
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
            print("price", price)

            result["Title"] = title_el.get_text(strip=True) if title_el else "N/A"
            result["Product_title"] = " ".join(result["Title"].split()[:3]) if title_el else "N/A"
            result["actual_price"] = price if price else "N/A"
            result["Price"] = price_el.get_text(strip=True) if price_el else "N/A"

            
            offers_section = psoup.find_all("div", class_="product__price--deals-card")
            offers_by_bank = {}
            for section in offers_section:
                for p in section.find_all(["p", "span", "div"]):
                    text = p.get_text(strip=True)
                    if text and "view details" not in text.lower():
                        matched = re.search(r"(HDFC|YES|IDFC|AU|AXIS|ICICI|KOTAK|SBI|BOB|RBL|Federal|IndusInd|Bank of India|PNB|Canara|Union Bank)", text, re.IGNORECASE)
                        if matched:
                            bank = matched.group(1).upper()
                            offers_by_bank.setdefault(bank, []).append(text)

            result["Offers"] = {"bankk_offer": offers_by_bank} if offers_by_bank else {"Info": "No structured offers found"}

            
            key_features = []
            feature_section = psoup.find("div", class_="product__keyfeatures")
            print(feature_section)
            if feature_section:
                for li in feature_section.find_all("li"):
                    text = li.get_text(strip=True)
                    if text:
                        key_features.append(text)
            result["Specifications"]["Key Features"] = key_features if key_features else ["Not available"]

            print(f"Scraped: {result['Title']}")

        except Exception as e:
            print(f"Error scraping product: {product_url} | {e}")

        return result

    def scrape_all_products_on_first_page(self, query):
        print(f" Searching for: {query}")
        product_links = self.get_product_links(query)
        print(f"Found {len(product_links)} products")

        all_results = []
        for i, link in enumerate(product_links, 1):
            print(f"[{i}/{len(product_links)}] Scraping: {link}")
            details = self.extract_product_details(link)
            all_results.append(details)

        return all_results

    def save_to_json(self, vijay_data, filename="../database/mobilescrapdata.json"):
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(vijay_data, f, indent=4, ensure_ascii=False)
            print(f" Saved {len(vijay_data)} products to {filename}")
        except Exception as e:
            print(f"Failed to save JSON: {e}")

    def close(self):
        self.driver.quit()



# if __name__ == "__main__":
#     scraper = VijaySalesScraper()
#     try:
#         results = scraper.scrape_all_products_on_first_page("IQOO mobiles")
#         scraper.save_to_json(results, "vijaysales_redmi_first_page.json")
#     finally:
#         scraper.close()
