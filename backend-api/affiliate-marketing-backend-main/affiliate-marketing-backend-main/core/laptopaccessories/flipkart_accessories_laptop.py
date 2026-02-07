import os
import json
import uuid
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup


class FlipkartAccessoryScraper:
    def __init__(self, delay=2, max_pages=2):
        self.delay = delay
        self.max_pages = max_pages
        self.base_url = "https://www.flipkart.com/search?q={}&page={}"
        chrome_options = Options()
        # chrome_options.add_argument("--headless=new")  # Uncomment for headless
        self.driver = webdriver.Chrome(options=chrome_options)

    def extract_offers(self, psoup):
        offers_list = []
        offer_items = psoup.find_all("li", {"class": "kF1Ml8 col"})
        for item in offer_items:
            spans = item.find_all("span")
            if len(spans) >= 2:
                label = spans[0].get_text(strip=True)
                offer_text = spans[1].get_text(strip=True)
                full_offer = f"{label}: {offer_text}"
                offers_list.append(full_offer)
        return offers_list

    def scrape_accessory(self, accessory):
        accessory_data = []
        print(f"\n🔎 Scraping accessory: {accessory}")

        for page in range(1, self.max_pages + 1):
            print(f"   ➝ Page {page}")
            search_url = self.base_url.format(accessory.replace(" ", "+"), page)
            self.driver.get(search_url)
            time.sleep(self.delay)

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            links = soup.find_all("a", class_="VJA3rP")
            product_links = ["https://www.flipkart.com" + link.get("href") for link in links if link.get("href")]

            if not product_links:
                print(f"   ⚠️ No more products found for {accessory} on page {page}")
                break  # Stop if no products

            for url in product_links:
                try:
                    self.driver.get(url)
                    time.sleep(self.delay)
                    psoup = BeautifulSoup(self.driver.page_source, "html.parser")

                    # Title
                    title_tag = psoup.find("span", class_="VU-ZEz")
                    product_name = title_tag.get_text(strip=True) if title_tag else ""

                    # Prices
                    actual_price_tag = psoup.find("div", class_="yRaY8j A6+E6v")
                    price = actual_price_tag.get_text(strip=True).replace("₹", "").replace(",", "") if actual_price_tag else ""

                    price_tag = psoup.find("div", class_="Nx9bqj CxhGGd")
                    discounted_price = price_tag.get_text(strip=True).replace("₹", "").replace(",", "") if price_tag else ""

                    # Rating
                    rating_tag = psoup.find("div", class_="XQDdHH")
                    rating = rating_tag.get_text(strip=True) if rating_tag else ""

                    # Brand
                    brand = product_name.split()[0] if product_name else ""

                    data = {
                        "product_id": str(uuid.uuid4()),
                        "title": product_name,
                        "price": price,
                        "discounted_price": discounted_price,
                        "rating": rating,
                        "brand": brand,
                        "offers": self.extract_offers(psoup),
                        "affiliatelink": url,
                        "category": accessory
                    }

                    accessory_data.append(data)

                except Exception as e:
                    print(f"   ❌ Error scraping {url}: {e}")
                    continue

        return accessory_data

    def scrape_all(self, accessories):
        all_data = []
        for accessory in accessories:
            accessory_data = self.scrape_accessory(accessory)
            all_data.extend(accessory_data)

        self.driver.quit()

        # ✅ Build save path in root/database/laptopaccessories/
        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "laptopaccessories"))
        os.makedirs(save_dir, exist_ok=True)  # ensures folder exists

        save_path = os.path.join(save_dir, "flipkart.json")

        # Save all accessories data
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Scraping complete. {len(all_data)} products saved to {save_path}")


if __name__ == "__main__":
    accessories = [
        "keyboard",
        "mouse",
        "laptop bag"
    ]

    scraper = FlipkartAccessoryScraper(delay=2, max_pages=3)
    scraper.scrape_all(accessories)
