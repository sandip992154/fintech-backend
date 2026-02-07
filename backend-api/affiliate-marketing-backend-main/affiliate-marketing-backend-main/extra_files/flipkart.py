from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse, parse_qs
import uuid




class FlipkartSeleniumScraper:
    def __init__(self, delay=2):
        self.delay = delay
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/16.0 Mobile/15A372 Safari/604.1"
        ]
        options = Options()
        # options.add_argument("--headless")  
        options.add_argument(f"--user-agent={random.choice(self.user_agents)}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def close(self):
        self.driver.quit()

    def scrape_page(self, product_title, page=2):
        url = f"https://www.flipkart.com/search?q={product_title.replace(' ', '+')}&sid=tyy%2C4io&page={page}"
        self.driver.get(url)
        time.sleep(random.uniform(2, 4))
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        records = soup.select("div._75nlfW")
        return records
    def extract_product_offers_and_specs(self, url):
            
            self.driver.get(url)
            time.sleep(random.uniform(2, 4))
            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            offer_div = soup.find("div", class_="UkUFwK")
            other_offer_div = soup.find("div", class_="I+EQVr")

            # Extract raw main offer
            offer = offer_div.text.strip() if offer_div else ""

            # Extract list offers and clean them
            list_offers = [
                li.text.strip().replace("T&C", "").strip()
                for li in (other_offer_div.find_all("li", class_="kF1Ml8 col") if other_offer_div else [])
            ]

            all_offers_text = "\n".join([offer] + list_offers).strip()

            structured_offers = self.parse_offers_to_dict(all_offers_text)

            specs_ul = soup.find("div", class_="xFVion")
            specifications = "\n".join(
                li.text.strip() for li in specs_ul.find_all("li")
            ) if specs_ul else "N/A"

            return {
                "Offers": structured_offers,
                "Specifications": specifications
            }
    @staticmethod
    def parse_offers_to_dict(raw_offer: str):
        lines = raw_offer.strip().split("Bank Offer")
        offer_data = {}

        # Handle first line like "10% off" or any discount
        if lines and lines[0].strip():
            offer_data["discount"] = lines[0].strip()
            lines = lines[1:]  # remove the first discount line

        for idx, line in enumerate(lines):
            key = f"bank_offer_{idx+1}"
            offer_data[key] = line.strip().replace("T&C", "")

        return offer_data



    @staticmethod
    
    def parse_specifications(raw_spec: str):
        lines = raw_spec.strip().split('\n')
        specs = {}

        for line in lines:
            line = line.strip()
            if "RAM" in line and "ROM" in line:
                parts = line.split('|')
                for part in parts:
                    if "RAM" in part:
                        specs["ram"] = part.strip()
                    elif "ROM" in part:
                        specs["storage"] = part.strip()
            elif "Display" in line:
                specs["display"] = line
            elif "Camera" in line:
                specs["camera"] = line
            elif "Battery" in line:
                specs["battery"] = line
            elif "Operating System" in line:
                specs["os"] = line
            else:
                specs.setdefault("Other", []).append(line)

        return specs
    def extract_data(self, records):
        data = []
        for record in records:
            title_tag = record.find("div", class_="KzDlHZ")
            title = title_tag.text.strip() if title_tag else "N/A"
            product_name = title.split("(")[0].strip() if "(" in title else title
            product_name = product_name.strip()
            Brand=product_name.split()[0] if product_name else "N/A"
            print(f"Brand: {Brand}")
            product_id = str(uuid.uuid4())


            # Extract prices
            price_tag = record.find("div", class_="Nx9bqj _4b5DiR")
            price = price_tag.text.strip() if price_tag else "N/A"

            actual_price_tag = record.find("div", class_="yRaY8j ZYYwLA")
            actual_price = actual_price_tag.text.replace("MRP:", "").strip() if actual_price_tag else "N/A"
            rating_tag = record.find("div", class_="XQDdHH")
            rating = rating_tag.text.strip() if rating_tag else "N/A"
            print(rating)


            # Extract product link
            link_tag = record.find("a", class_="CGtC98")
            product_url = "N/A"
            img_url = "N/A"

            if link_tag and link_tag.has_attr("href"):
                raw_url = link_tag["href"]
                parsed_url = urlparse(raw_url)
                product_url = urljoin("https://www.flipkart.com", parsed_url.path)

                # Try to find image inside the anchor tag
                img_tag = link_tag.find("img")
                print(f"Image tag: {img_tag}")
                if img_tag:
                    img_url = img_tag.get("src") or img_tag.get("data-src") or "N/A"
                    print(f"Image URL: {img_url}")
            # Extract Offers and Specs from product detail page
            if product_url != "N/A":
                offers_specs = self.extract_product_offers_and_specs(product_url)
            else:
                offers_specs = {"Offers": "N/A", "Specifications": "N/A"}
            
            specs = offers_specs.get("Specifications", "N/A")
            if isinstance(specs, str):
                specs = self.parse_specifications(specs)  # corrected self.

            data.append({
                "product_id": product_id,
                "title": title,
                "product_name": product_name,
                "brand": Brand,
                "Price": actual_price,
                "discounted_Price": price,
                "rating": rating,
                "offers": offers_specs["Offers"],
                "specifications": specs,
                "product_link": product_url,
                "image_url": img_url,
                "category": "accessories",
            })

            time.sleep(random.uniform(1, 2))
        
        return data  

    def scrape(self, product_title, pages=2):
        all_data = []
        for page in range(1, pages + 1):
            print(f"Scraping page {page}...")
            records = self.scrape_page(product_title, page)
            if not records:
                print(f"No records found on page {page}.")
                continue
            page_data = self.extract_data(records)
            all_data.extend(page_data)
        return all_data
    @staticmethod
    def save_to_json(flipkart_data, filename="flipkart_products.json"):
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(flipkart_data, f, indent=4, ensure_ascii=False)
            print(f"✅ Data saved to {filename}")
        except Exception as e:
            print(f"❌ Failed to save JSON: {e}")


if __name__ == "__main__":
    title = "laptops"  
    flipkart_scraper = FlipkartSeleniumScraper()
    try:
        flipkart_data = flipkart_scraper.scrape(product_title=title, pages=1)
        print("✅ Flipkart Data collected successfully.")

       
        FlipkartSeleniumScraper.save_to_json(flipkart_data, "flipkart_products.json")

    finally:
        flipkart_scraper.close()
       
