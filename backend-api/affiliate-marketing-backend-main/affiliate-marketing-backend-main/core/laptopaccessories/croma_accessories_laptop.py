import time
import os
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
            options.add_argument("--headless")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--log-level=3")

        try:
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 10)
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
                print("No more 'View More' button or it's not clickable.")
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
            return []

        time.sleep(self.delay)
        self.click_all_view_more_buttons()

        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        product_cards = soup.find_all("li", class_="product-item")

        if not product_cards:
            print(f"⚠ No products found for {search_query}.")
            return []

        print(f" Found {len(product_cards)} products for {search_query}.")

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
                title_tag = psoup.find("h1", class_="pd-title pd-title-normal")
                price_tag = psoup.find("span", class_="amount")
                actual_price_tag = psoup.find("span", class_="old-price")

                rating_tag = psoup.select_one(
                    "#pdpdatael div.cp-rating > span:nth-child(1) > span"
                )
                rating = rating_tag.get_text(strip=True) if rating_tag else "N/A"

                title = title_tag.text.strip() if title_tag else product_title
                brand = title.split()[0] if title else "N/A"
                price = price_tag.text.strip() if price_tag else "Price not found"
                actual_price = actual_price_tag.get_text(strip=True) if actual_price_tag else "Not found"

                # ✅ Updated Offers Extraction
                offers = set()
                offer_blocks = psoup.find_all("div", class_="offer-container")
                for block in offer_blocks:
                    title_elem = block.find("span", class_="bank-offer-details-carousel")
                    value_elem = block.find("span", class_="bank-offers-text-pdp-carousel")
                    if title_elem and value_elem:
                        offer_text = f"{title_elem.get_text(strip=True)} - {value_elem.get_text(strip=True)}"
                        offers.add(offer_text)
                    else:
                        text = block.get_text(" ", strip=True)  
                        if text:
                            offers.add(text)

                offers = list(offers)

                product_data = {
                    "product_id": product_id,
                    "title": title,
                    "brand": brand,
                    "price": actual_price,
                    "discounted_Price": price,
                    "rating": rating,
                    "offers": offers,
                    "affiliatelink": product_url,
                    "category": search_query
                }

                all_products.append(product_data)

            except Exception as detail_err:
                print(f"⚠ Error scraping {product_title}: {detail_err}")

        return all_products

    def save_to_json(self, croma_data, filename="croma.json"):
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(croma_data, f, indent=4, ensure_ascii=False)
            print(f"✅ Data saved to {filename}")
        except Exception as e:
            print(f" Failed to save JSON: {e}")

    def close(self):
        self.driver.quit()


if __name__ == "__main__":
    accessories = [
        "keyboard",
        "mouse",
        "laptop bag"
    ]

    scraper = CromaScraper(headless=False)
    all_results = []
    try:
        for item in accessories:
            print(f"\n🔍 Scraping category: {item}")
            results = scraper.scrape_all_products(item)
            all_results.extend(results)

        # ✅ Build save path in root/database/laptopaccessories/
        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "laptopaccessories"))
        os.makedirs(save_dir, exist_ok=True)  # ensures folder exists

        save_path = os.path.join(save_dir, "croma.json")

        scraper.save_to_json(all_results, filename=save_path)
    finally:
        scraper.close()
