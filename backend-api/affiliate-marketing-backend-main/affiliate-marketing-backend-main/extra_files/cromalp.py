import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import uuid


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

                title_tag = psoup.find("h1", class_="pd-title pd-title-normal")
                price_tag = psoup.find("span", class_="amount")
                actual_price_tag = psoup.find("span", class_="old-price")
                spec_list = psoup.find("div", class_="cp-keyfeature pd-eligibility-wrap")

                title = title_tag.text.strip() if title_tag else product_title
                short_title = " ".join(title.split()[:3])
                price = price_tag.text.strip() if price_tag else "Price not found"
                actual_price = actual_price_tag.get_text(strip=True) if actual_price_tag else "Not found"
                specifications = {
                    "ram": "N/A",
                    "storage": "N/A",
                    "display": "N/A",
                    "camera": "N/A",
                    "battery": "N/A"
                }
                                
                if spec_list:
                    for li in spec_list.find_all("li"):
                        feature = li.get_text(strip=True)

                        for line in feature.strip().split("\n"):
                            if "Display" in line:
                                specifications["display"] = line.split(":", 1)[1].strip()
                            elif "Memory" in line:
                                parts = line.split(":", 1)[1].strip().split(",")
                                for part in parts:
                                    if "RAM" in part:
                                        specifications["ram"] = part.strip()
                                    elif "ROM" in part or "Storage" in part:
                                        specifications["storage"] = part.strip()
                            elif "Camera" in line:
                                specifications["camera"] = line.split(":", 1)[1].strip()
                            elif "Battery" in line:
                                specifications["battery"] = line.split(":", 1)[1].strip()
                print(f"Specifications found: {specifications}")

                specs = {
                    "ram": specifications.get("ram", "N/A"),
                    "storage": specifications.get("storage", "N/A"),
                    "display": specifications.get("display", "N/A"),
                    "camera": specifications.get("camera", "N/A"),
                    "battery": specifications.get("battery", "N/A")
                }
                print(f"Specifications found: {specs}")
                img_element = self.driver.find_element(By.ID, "0prod_img")
                print("img_element found:", img_element)
                img_url = img_element.get_attribute("src")
                print(f"Image URL..........: {img_url}")
                rating_elem = self.driver.find_element(By.CSS_SELECTOR, "#pdpdatael > div.cp-section.banner-spacing.show-pdp-icon > div.container > div > div > div > div.col-md-6.right-alignElement > div > ul > li > div.cp-rating > span:nth-child(1) > span")
                rating = rating_elem.text.strip()
                print("Rating:", rating)
                offers = {
                    "discount": "N/A",
                    "bank_offer_1": "N/A",
                    "bank_offer_2": "N/A",
                    "bank_offer_3": "N/A"
                }

                # Try to extract discount if available
                discount_tag = psoup.find("span", class_="savingsPercentage")
                if discount_tag:
                    offers["discount"] = discount_tag.get_text(strip=True)

                # Extract bank offers in readable format
                offer_section = psoup.find("div", class_="offer-section-pdp")
                if offer_section:
                    offer_blocks = offer_section.find_all("div", recursive=True)
                    count = 1
                    for block in offer_blocks:
                        if count > 3:
                            break
                        title_elem = block.find("span", class_="bank-name-text")
                        value_elem = block.find("span", class_="bank-offers-text-pdp-carousel")
                        
                        if title_elem and value_elem:
                            offer_text = f"{title_elem.get_text(strip=True)} - {value_elem.get_text(strip=True)}"
                            offers[f"bank_offer_{count}"] = offer_text
                            count += 1
                        else:
                            text = block.get_text(strip=True)
                            if text and count <= 3:
                                offers[f"bank_offer_{count}"] = text
                                count += 1
                print(f"Offers found...............: {offers}")
                
                
                  

                product_data = {
                    "product_id": str(uuid.uuid4()), 
                    "title": title,
                    "product_name": short_title,
                    "brand": short_title.split()[0] if title else "N/A",
                    "rating":rating,
                    "actual_Price": actual_price,
                    "discounted_Price": price,
                    "offers": offers,
                    "Specifications": specifications,
                    "product_url": product_url,
                    "image_url": img_url,
                    "category": "laptops"
                }

                all_products.append(product_data)

            except Exception as detail_err:
                print(f"⚠ Error scraping {product_title}: {detail_err}")

        self.driver.quit()
        return all_products


    def save_to_json(self,croma_data, filename="laptopscrapdatacroma.json"):
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(croma_data, f, indent=4, ensure_ascii=False)
            print(f" Data saved to {filename}")
        except Exception as e:
            print(f" Failed to save JSON: {e}")
    def close(self):
        self.driver.quit()


if __name__ == "__main__":
    scraper = CromaScraper(headless=False)  
    results = scraper.scrape_all_products("laptops")
    scraper.save_to_json(results)