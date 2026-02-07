import os
import json
import uuid
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup


class FlipkartMobileScraper:
    def __init__(self, delay=1):  # Reduced delay from 2 to 1
        self.delay = delay
        self.start_url = "https://www.flipkart.com/search?q={}&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=on&as=off&page={}"
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        # Add performance optimizations
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Skip images for faster loading
        chrome_options.add_argument("--page-load-strategy=eager")
        self.driver = webdriver.Chrome(options=chrome_options)

    def extract_offers(self, psoup):
        offers_list = []
        offer_items = psoup.find_all("li", {"class": "kF1Ml8 col"})
        for item in offer_items:
            spans = item.find_all("span")
            if len(spans) >= 2:
                label = spans[0].get_text(strip=True)
                offer_text = spans[1].get_text(strip=True)
                full_offer = f"{label} - {offer_text}"
                offers_list.append(full_offer)
        return offers_list

    def scrape_brand(self, brand):
        brand_data = []
        for page in range(1, 2):  # Reduced from 3 to 2 pages
            print(f"Scraping {brand} - Page {page}")
            self.driver.get(self.start_url.format(f"{brand} mobile", page))
            time.sleep(self.delay)

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            links = soup.find_all("a", class_="CGtC98")
            product_links = ["https://www.flipkart.com" + link.get("href") for link in links if link.get("href")]

            # Limit to first 10 products per page for faster processing
            for url in product_links[:10]:
                try:
                    self.driver.get(url)
                    time.sleep(self.delay)
                    psoup = BeautifulSoup(self.driver.page_source, "html.parser")

                    title_tag = psoup.find("span", class_="VU-ZEz")
                    product_name = title_tag.get_text(strip=True) if title_tag else ""

                    title = product_name

                    # Discounted price
                    price_tag = psoup.find("div", class_="Nx9bqj CxhGGd")
                    discounted_price = (
                        f"₹{price_tag.get_text(strip=True).replace('₹', '').replace(',', '')}"
                        if price_tag else ""
                    )

                    # Original price
                    price_o = psoup.find("div", class_="yRaY8j A6+E6v")
                    price = (
                        f"₹{price_o.get_text(strip=True).replace('₹', '').replace(',', '')}"
                        if price_o else ""
                    )

                    # Rating
                    rating_tag = psoup.find("div", class_="XQDdHH")
                    rating = rating_tag.get_text(strip=True) if rating_tag else "N/A"

                    brand_name = product_name.split()[0] if product_name else brand
                    category = "smartphone"

                    data = {
                        "product_id": str(uuid.uuid4()),
                        "title": title,
                        "brand": brand_name,
                        "price": price,
                        "discounted_price": discounted_price,
                        "rating": rating,
                        "offers": self.extract_offers(psoup),
                        "affiliatelink": url,
                        "category": category
                    }

                    brand_data.append(data)
                except Exception as e:
                    print(f"Error scraping {url}: {e}")
                    continue

        return brand_data

    def scrape(self, brands):
        all_data = []
        for brand in brands:
            brand_results = self.scrape_brand(brand)
            all_data.extend(brand_results)

        self.driver.quit()

        # Save to JSON
        # ✅ Save JSON inside root/database/mobiles/
        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "mobiles"))
        os.makedirs(save_dir, exist_ok=True)  # ensures folder exists

        save_path = os.path.join(save_dir, "flipkart.json")

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Data saved to {save_path}")



if __name__ == "__main__":
    scraper = FlipkartMobileScraper()

    # ✅ Brand list
    brands = ["Samsung", "OnePlus","Apple"]

    scraper.scrape(brands)