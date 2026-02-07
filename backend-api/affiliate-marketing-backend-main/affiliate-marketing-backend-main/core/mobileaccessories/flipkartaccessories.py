import os
import json
import uuid
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup


# 📦 List of mobile accessories to scrape
ACCESSORIES_LIST = [
            "mobile charger",
            "phone case",
            "USB charger",
            "charging adapter"
]


class FlipkartMobileScraper:
    def __init__(self, delay=2):
        self.delay = delay
        self.start_url = "https://www.flipkart.com/search?q={}&page={}"
        chrome_options = Options()
        # chrome_options.add_argument("--headless=new")
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

    def scrape(self, max_pages=2, target_count=60):
        all_data = []

        for accessory in ACCESSORIES_LIST:
            print(f"\n🔎 Scraping Accessory: {accessory}")
            for page in range(1, max_pages + 1):
                if len(all_data) >= target_count:
                    break

                print(f"\n📄 Scraping Page {page} for {accessory}")
                self.driver.get(self.start_url.format(accessory, page))
                time.sleep(self.delay)

                soup = BeautifulSoup(self.driver.page_source, "html.parser")

                # ✅ Collect product links from multiple selectors
                link_classes = ["VJA3rP", "CGtC98", "KzDlHZ", "IRpwTa", "s1Q9rs"]
                product_links = []
                for cls in link_classes:
                    links = soup.find_all("a", class_=cls)
                    product_links.extend(
                        ["https://www.flipkart.com" + link.get("href") for link in links if link.get("href")]
                    )

                # Remove duplicates
                product_links = list(set(product_links))

                if not product_links:
                    print(f"⚠ No products found on page {page} for {accessory}, moving to next accessory.")
                    break

                for url in product_links:
                    if len(all_data) >= target_count:
                        break
                    try:
                        self.driver.get(url)
                        time.sleep(self.delay)
                        psoup = BeautifulSoup(self.driver.page_source, "html.parser")

                        title_tag = psoup.find("span", class_="VU-ZEz")
                        product_name = title_tag.get_text(strip=True) if title_tag else ""

                        actual_price_tag = psoup.find("div", class_="yRaY8j A6+E6v")
                        price = (
                            actual_price_tag.get_text(strip=True).replace("₹", "").replace(",", "")
                            if actual_price_tag else ""
                        )

                        price_tag = psoup.find("div", class_="Nx9bqj CxhGGd")
                        discounted_price = (
                            price_tag.get_text(strip=True).replace("₹", "").replace(",", "")
                            if price_tag else ""
                        )

                        rating_tag = psoup.find("div", class_="XQDdHH")
                        rating = rating_tag.get_text(strip=True) if rating_tag else ""

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
                            "category": accessory,  # ✅ Save actual accessory name
                        }

                        all_data.append(data)
                        print(f"✔ Scraped: {product_name[:50]}")

                    except Exception as e:
                        print(f"❌ Error scraping {url}: {e}")
                        continue

        self.driver.quit()

        # ✅ Ensure folder exists under root/database/mobileaccessories/
        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "mobileaccessories"))
        os.makedirs(save_dir, exist_ok=True)

        save_path = os.path.join(save_dir, "flipkart.json")

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Data saved to {save_path}")
        print(f"📦 Total products scraped: {len(all_data)}")



if __name__ == "__main__":
    scraper = FlipkartMobileScraper()
    scraper.scrape(max_pages=3, target_count=90)  # increased target so multiple accessories are scraped
