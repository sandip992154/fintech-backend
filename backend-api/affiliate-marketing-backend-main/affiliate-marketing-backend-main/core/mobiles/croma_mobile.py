import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import uuid
import re


class CromaScraper:
    def __init__(self, delay=2, headless=False):
        self.delay = delay
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--log-level=3")

        try:
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 15)
        except Exception as e:
            print(f"Failed to launch browser: {e}")
            exit()

    def click_all_view_more_buttons(self):
        """Click 'View More' until it's no longer visible/clickable."""
        while True:
            try:
                view_more = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'View More')]"))
                )
                if view_more.is_displayed():
                    print(" Clicking 'View More'...")
                    self.driver.execute_script("arguments[0].click();", view_more)
                    time.sleep(self.delay)
                else:
                    break
            except Exception:
                break

    def scrape_all_products(self, search_query: str) -> list:
        all_products = []

        try:
            self.driver.get("https://www.croma.com/")
            search_box = self.wait.until(EC.presence_of_element_located((By.ID, "searchV2")))
            search_box.clear()
            search_box.send_keys(search_query)
            search_box.send_keys(Keys.RETURN)
        except Exception as e:
            print(f" Error during search: {e}")
            self.driver.quit()
            return []

        time.sleep(self.delay)
        self.click_all_view_more_buttons()

        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        product_cards = soup.find_all("li", class_="product-item")

        if not product_cards:
            print("⚠ No products found.")
            self.driver.quit()
            return []

        print(f" Found {len(product_cards)} products.")

        for idx, card in enumerate(product_cards, start=1):
            a_tag = card.find("a", href=True)
            title_tag = card.find("h3", class_="product-title")

            if not a_tag or not title_tag:
                continue

            product_url = "https://www.croma.com" + a_tag['href']
            product_title = title_tag.text.strip()
            print(f"[{idx}] Scraping: {product_title}")
            print(f"     URL: {product_url}")

            try:
                self.driver.get(product_url)
                time.sleep(self.delay)

                psoup = BeautifulSoup(self.driver.page_source, "html.parser")
                product_id = str(uuid.uuid4())

                # ✅ Title / Price / Rating
                title_tag = psoup.find("h1", class_="pd-title pd-title-normal")
                price_tag = psoup.find("span", class_="amount")
                actual_price_tag = psoup.find("span", class_="old-price")

                rating_tag = psoup.select_one("#pdpdatael span.cp-rating span")
                rating = rating_tag.get_text(strip=True) if rating_tag else "N/A"

                title = title_tag.text.strip() if title_tag else product_title
                brand = title.split()[0] if title else "N/A"
                price = actual_price_tag.get_text(strip=True) if actual_price_tag else "₹0"
                discounted_price = price_tag.text.strip() if price_tag else "₹0"

                # ✅ Robust Offers Extraction
                offers = set()
                offer_blocks = psoup.find_all(
                    "div",
                    class_=re.compile(r"(offer-container|bank-offer|bank-offers-content|product-offer-container|emi-offer)")
                )

                for block in offer_blocks:
                    # Check multiple tag types
                    for elem in block.find_all(["span", "p", "li", "div"]):
                        text = elem.get_text(" ", strip=True)
                        if text and "view details" not in text.lower():
                            offers.add(text)

                offers = list(offers) if offers else ["No offers found"]

                product_data = {
                    "product_id": product_id,
                    "title": title,
                    "brand": brand,
                    "price": price,
                    "discounted_price": discounted_price,
                    "rating": rating,
                    "offers": offers,
                    "affiliatelink": product_url,
                    "category": "smartphone"
                }

                all_products.append(product_data)

            except Exception as detail_err:
                print(f"⚠ Error scraping {product_title}: {detail_err}")

        self.driver.quit()
        return all_products

    def save_to_json(self, croma_data, filename="croma.json"):
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)  # ✅ ensure folder exists
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(croma_data, f, indent=4, ensure_ascii=False)
            print(f"✅ Data saved to {filename}")
        except Exception as e:
            print(f"❌ Failed to save JSON: {e}")

    def close(self):
        self.driver.quit()


if __name__ == "__main__":
    scraper = CromaScraper(headless=False)

    # ✅ Brand list for scraping mobiles brand-wise
    brands = ["Samsung", "OnePlus", "Apple"]

    all_results = []
    for brand in brands:
        print(f"\n🔍 Scraping mobiles for brand: {brand}")
        results = scraper.scrape_all_products(f"{brand} mobile")
        all_results.extend(results)

    # ✅ Build save path under root/database/mobiles/
    save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "mobiles"))
    os.makedirs(save_dir, exist_ok=True)  # ensures folder exists
    save_path = os.path.join(save_dir, "croma.json")

    scraper.save_to_json(all_results, save_path)
