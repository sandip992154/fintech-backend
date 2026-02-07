from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import pandas as pd
import time
import random
import re
import json
import uuid


class AmazonMobileScraper:
    def __init__(self, delay=3):
        self.delay = delay
        self.user_agents = [
            
              "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
              "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.112 Safari/537.36",
              "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.57 Safari/537.36"

            
        ]
        options = Options()
        
        options.add_argument(f"user-agent={random.choice(self.user_agents)}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def close(self):
        self.driver.quit()

    def scrape_mobiles(self, search_term="mobiles", max_pages=1):
        all_data = []
        for page in range(1, max_pages + 1):
            query = quote_plus(search_term)
            url = f"https://www.amazon.in/s?k={query}&page={page}"
            self.driver.get(url)
            self.wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@data-component-type='s-search-result']")))
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            cards = soup.find_all("div", {"data-component-type": "s-search-result"})

            for card in cards:


                try:
                    link_tag = card.find("a", href=True)
                    if not link_tag:
                        continue

                    raw_href = link_tag["href"]
                    match = re.search(r"(/dp/[A-Z0-9]{10})", raw_href)
                    product_url = f"https://www.amazon.in{match.group(1)}" if match else "N/A"
                    print(f"Scraping product URL: {product_url}")

                    self.driver.get(product_url)
                    self.wait.until(EC.presence_of_element_located((By.ID, "productTitle")))
                    psoup = BeautifulSoup(self.driver.page_source, "html.parser")

                    product_id = str(uuid.uuid4())  # Generate a unique product ID
                    title_tag = psoup.find("span", id="productTitle")
                    raw_title = title_tag.get_text(strip=True) if title_tag else "N/A"
                    print(f"Raw title found: {raw_title}")
                    product_name = " ".join(raw_title.split()[0:2])
                    print(f"Product name extracted: {product_name}")
                    Brand = product_name.split()[0] if product_name else "N/A"
                    # print(f"Brand: {Brand}")

                    # Prices
                    whole = psoup.find("span", class_="a-price-whole")
                    fraction = psoup.find("span", class_="a-price-fraction")
                    if whole:


                        whole_price = whole.get_text(strip=True).replace(',', '').replace('.', '')
                        if fraction:
                         
                         fraction_price = fraction.get_text(strip=True)
                         price = f"₹{whole_price}.{fraction_price}"
                        else:
                         
                         price = f"₹{whole_price}.00"
                    else:
                        price = "N/A"

                    actual_price_tag = psoup.find("span", class_="a-price a-text-price")
                    actual_price = actual_price_tag.find("span", class_="a-offscreen").text.strip() if actual_price_tag else "N/A"

                    # Rating
                    rating_tag = psoup.select_one("#acrPopover > span.a-declarative > a > span")
                    rating = rating_tag.get_text(strip=True) if rating_tag else "N/A"

                    # print(f"Rating tag found: {rating_tag}")
                    # print(f"Rating: {rating}")

                    # Image
                    img_tag = psoup.find("img", class_="a-dynamic-image a-stretch-horizontal")
                    # print(f"Image tag found: {img_tag}")
                    img_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else "N/A"
                    # print(f"Image URL: {img_url}")

                    # Offers (mock structure)
                    offers = {
                    "discount": "N/A",
                     "bank_offer_1": "N/A",
                    "bank_offer_2": "N/A",
                    "bank_offer_3": "N/A"
                }


                    discount_tag = psoup.find("span", class_="savingsPercentage")
                    offers["discount"] = discount_tag.get_text(strip=True) if discount_tag else "N/A"

                    # Extract bank offers more reliably
                    offer_sections = psoup.select("div.a-cardui.vsx__offers-holder")

                    if not offer_sections:
                        # Try fallback selector
                        offer_sections = psoup.select("div.a-section.a-spacing-small")

                    bank_offer_count = 0

                    for section in offer_sections:
                        # Find all possible offer texts (title + truncated description)
                        titles = section.find_all("h6", class_="a-size-base")
                        descs = section.find_all("span", class_="a-truncate-cut")

                        for title, desc in zip(titles, descs):
                            if bank_offer_count >= 3:
                                break
                            full_text = f"{title.get_text(strip=True)} - {desc.get_text(strip=True)}"
                            offers[f"bank_offer_{bank_offer_count + 1}"] = full_text
                            bank_offer_count += 1

                    # If still missing offers, try getting text from <li> or <div> blocks as fallback
                    if bank_offer_count < 3:
                        extra_offers = psoup.find_all(string=re.compile(r"(cashback|offer|bank|price)", re.I))
                        for offer_text in extra_offers:
                            clean_text = offer_text.strip()
                            if len(clean_text) > 30 and "bank_offer_" not in offers.values():
                                if bank_offer_count >= 3:
                                    break
                                offers[f"bank_offer_{bank_offer_count + 1}"] = clean_text
                                bank_offer_count += 1

                    
                 
                    specs = {
                        "ram": "N/A",
                        "storage": "N/A",
                        "display": "N/A",
                        "camera": "N/A",
                        "battery": "N/A"
                    }

                    features_ul = psoup.find("ul", class_="a-spacing-mini")
                    if features_ul:
                        items = features_ul.find_all("li")
                        print(items)
                        for li in items:
                            span = li.find("span", class_="a-list-item")
                            if not span:
                                continue
                            text = span.get_text(strip=True)
                            # Extract RAM, ROM, battery, display, and camera from text
                            ram_match = re.search(r"(\d+\s?GB)\s*RAM", text, re.IGNORECASE)
                            if ram_match and specs["ram"] == "N/A":
                                specs["ram"] = ram_match.group(1).strip().upper()

                            rom_match = re.search(r"(\d+\s?GB)\s*(ROM|storage)", text, re.IGNORECASE)
                            if rom_match and specs["storage"] == "N/A":
                                specs["storage"] = rom_match.group(1).strip().upper()

                            battery_match = re.search(r"(\d+\s?mAh)\s*battery", text, re.IGNORECASE)
                            if battery_match and specs["battery"] == "N/A":
                                specs["battery"] = battery_match.group(1).strip().upper()

                            display_match = re.search(r"(\d+(\.\d+)?\s*(inch|inches|cm|Hz)[^,]*)display", text, re.IGNORECASE)
                            if display_match and specs["display"] == "N/A":
                                specs["display"] = display_match.group(0).strip()

                            camera_match = re.search(r"(\d+\s*MP[^,]*)camera", text, re.IGNORECASE)
                            if camera_match and specs["camera"] == "N/A":
                                specs["camera"] = camera_match.group(0).strip()
                            # print(f"Processing feature........................: {text}")

                            # RAM and ROM in one line
                            match = re.search(r"(\d+\s?GB)\s*RAM[,|\s;]*(\d+\s?GB)\s*ROM", text, re.IGNORECASE)
                            # print("Match found......................:", match)
                            if match:
                                specs["ram"] = match.group(1).strip().upper()
                                specs["storage"] = match.group(2).strip().upper()

                            #RAM separately
                            elif "ram" in text.lower() and specs["ram"] == "N/A":
                                specs["ram"] = text.strip()

                            # ROM or storage separately
                            elif ("rom" in text.lower() or "storage" in text.lower()) and specs["storage"] == "N/A":
                                specs["storage"] = text.strip()

                            # Display
                            elif "display" in text.lower() or "refresh rate" in text.lower():
                                specs["display"] = text.strip()

                            # Camera
                            elif "camera" in text.lower():
                                specs["camera"] = text.strip()

                            # Battery or charging
                            elif "battery" in text.lower() or "charging" in text.lower():
                                specs["battery"] = text.strip()

                   
                    
                    

                    all_data.append({
                        "product_id": product_id,
                        "title": raw_title,
                        "product_name": product_name,
                        "brand": Brand,
                        "price": actual_price,
                        "discounted_Price": price,
                        "rating": rating,
                        "offers": offers,
                        "specifications": specs,
                        "product_link": product_url,
                        "image_url": img_url,
                        "category": "accessories"
                    })
                    print(f"✔ Scraped: {product_name}")
                    time.sleep(self.delay)

                except Exception as e:
                    print(f"⚠ Skipping a product due to error: {e}")
                    continue

                 
            self.driver.quit()
            return all_data

    def save_to_json(self, amazon_data, filename="amazon_accessories.json"):
        try:
            json_string = json.dumps(amazon_data, indent=4, ensure_ascii=False)
            json_string = json_string.replace('\\/', '/')  # Clean slashes

            with open(filename, "w", encoding="utf-8") as f:
                f.write(json_string)

            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Failed to save JSON: {e}")



if __name__ == "__main__":
    scraper = AmazonMobileScraper()
    try:
        results = scraper.scrape_mobiles("laptops", max_pages=1)
        df = pd.DataFrame(results)
        
        df.to_json("amazon mobiles.json", orient="records", indent=2 , force_ascii=False)
        print(df.head())
    finally:
        scraper.close()
