import os
import json
import uuid
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


class FlipkartMobileScraper:
    def __init__(self, delay=5):
        self.delay = delay
        self.base_url = "https://www.flipkart.com/search?q={}&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=on&as=off&page={}"
        # TEST MODE: disable headless to see what browser does
        chrome_options = Options()
        # chrome_options.add_argument("--headless=new")  # ❌ Comment this for now
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

    def extract_image_url(self, psoup):
        try:
            image_urls = []
            image_div = psoup.find("div", class_="_0J1TKd")
            if image_div:
                img_tags = image_div.find_all("img", class_="_0DkuPH")
                for img in img_tags:
                    src = img.get("src")
                    if src and src not in image_urls:
                        image_urls.append(src)

            thumbnail = image_urls[0] if image_urls else ""
            return {
                "thumbnail": thumbnail,
                "urls": image_urls
            }
        except Exception:
            return {
                "thumbnail": "",
                "urls": []
            }

    def extract_mobile_features(self, psoup):
        features = {
            "type": "laptop",
            "details": {
                "storage": {"ram": "", "rom": ""},
                "design": {
                    "dimensions": "", "weight": "", "form_factor": "",
                    "stylus_support": "", "color": ""
                },
                "display": {
                    "screen_size": "", "resolution": "",
                    "touchscreen": "", "brightness": ""
                },
                "performance": {
                    "processor": "", "cores": "", "gpu": "",
                    "operating_system": "", "model_number": ""
                },
                "input": {
                    "keyboard": "",
                    "touchpad": ""
                },
                "network&connectivity": {
                    "wireless_tech": "", "connectivity": "", "gps": "",
                    "sim": "", "mobile_hotspot": "", "ethernet": ""
                },
                "camera": {
                    "rear_camera": "", "front_camera": "",
                    "camera_features": ""
                },
                "battery": {
                    "battery_capacity": "", "battery_type": "", "fast_charging": "",
                    "battery_backup": ""
                },
                "audio": {"audio_jack": "", "speaker": "", "microphone": ""},
                "box_contents": {"in_the_box": ""},
                "manufacturer": {"brand": ""}
            }
        }

        spec_section = psoup.find("div", class_="_3Fm-hO")
        if spec_section:
            rows = spec_section.find_all("tr", class_="WJdYP6 row")
            raw_specs = {}
            for row in rows:
                label_td = row.find("td", class_="+fFi1w col col-3-12")
                value_td = row.find("td", class_="Izz52n col col-9-12")
                if label_td and value_td:
                    label = label_td.get_text(strip=True).upper()
                    value_list = value_td.find_all("li", class_="HPETK2")
                    value = ', '.join(li.get_text(strip=True) for li in value_list)
                    raw_specs[label] = value

            features["details"]["storage"]["ram"] = raw_specs.get("RAM", "")
            rom = ""
            if "SSD CAPACITY" in raw_specs and raw_specs["SSD CAPACITY"]:
                rom = raw_specs["SSD CAPACITY"]
            elif "EMMC STORAGE CAPACITY" in raw_specs and raw_specs["EMMC STORAGE CAPACITY"]:
                rom = raw_specs["EMMC STORAGE CAPACITY"]
            features["details"]["storage"]["rom"] = rom

            features["details"]["manufacturer"]["brand"] = raw_specs.get("BRAND", "")
            features["details"]["display"]["resolution"] = raw_specs.get("SCREEN RESOLUTION", "")
            features["details"]["battery"]["battery_capacity"] = raw_specs.get("BATTERY CAPACITY", "")
            features["details"]["battery"]["battery_Type"] = raw_specs.get("POWER SUPPLY", "")
            features["details"]["battery"]["battery_backup"] = raw_specs.get("BATTERY BACKUP", "")
            features["details"]["display"]["touchscreen"] = raw_specs.get("TOUCHSCREEN", "")
            features["details"]["design"]["color"] = raw_specs.get("COLOR", "")
            features["details"]["display"]["brightness"] = raw_specs.get("BRIGHTNESS", "")
            features["details"]["display"]["screen_size"] = raw_specs.get("SCREEN SIZE", "")
            features["details"]["design"]["dimensions"] = raw_specs.get("DIMENSIONS", "")
            features["details"]["design"]["weight"] = raw_specs.get("WEIGHT", "")
            features["details"]["performance"]["processor"] = raw_specs.get("PROCESSOR NAME", "")
            features["details"]["network&connectivity"]["sim"] = raw_specs.get("SIM TYPE", "")
            Internet_connectivity = raw_specs.get("WIRELESS LAN", "")
            Bluetooth = raw_specs.get("BLUETOOTH", "")
            Connectivity = ""
            if Internet_connectivity or Bluetooth:
                Connectivity = f"{Internet_connectivity} x {Bluetooth}".strip("x")
            features["details"]["network&connectivity"]["connectivity"] = Connectivity
            features["details"]["network&connectivity"]["ethernet"] = raw_specs.get("ETHERNET", "")
            features["details"]["performance"]["operating_system"] = raw_specs.get("OPERATING SYSTEM", "")
            features["details"]["performance"]["model_number"] = raw_specs.get("MODEL NUMBER", "")
            features["details"]["performance"]["cores"] = raw_specs.get("NUMBER OF CORES", "")
            features["details"]["battery"]["fast_charging"] = raw_specs.get("QUICK CHARGING", "")
            features["details"]["camera"]["rear_camera"] = raw_specs.get("FLASH", "")
            features["details"]["camera"]["front_camera"] = raw_specs.get("SECONDARY CAMERA FEATURE", "")
            features["details"]["camera"]["camera_features"] = raw_specs.get("WEB CAMERA", "")
            features["details"]["audio"]["audio_jack"] = raw_specs.get("AUDIO FORMATS", "")
            features["details"]["audio"]["speaker"] = raw_specs.get("SPEAKERS", "")
            features["details"]["audio"]["microphone"] = raw_specs.get("INTERNAL MIC", "")
            features["details"]["design"]["form_factor"] = raw_specs.get("FORM FACTOR", "")
            features["details"]["box_contents"]["in_the_box"] = raw_specs.get("SALES PACKAGE", "")
            features["details"]["input"]["keyboard"] = raw_specs.get("KEYBOARD", "")
            features["details"]["input"]["touchpad"] = raw_specs.get("POINTER DEVICE", "")

        return features

    def scrape(self):
        all_data = []
        brand_list = ["lenovo", "asus", "dell"]    # , "hp", "apple", "acer", "samsung"

        for brand in brand_list:
            for page in range(1, 3):
                print(f"Scraping {brand.upper()} - Page {page}")
                self.driver.get(self.base_url.format(brand, page))
                time.sleep(self.delay)

                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                # This selector grabs all product links that go to /p/ pages
                links = soup.select('a[href*="/p/"]')
                product_links = ["https://www.flipkart.com" + link.get("href") for link in links if link.get("href")]

                print(f"🧷 Found {len(product_links)} product links on page {page}")


                for url in product_links:
                    try:
                        self.driver.get(url)
                        time.sleep(self.delay)
                        psoup = BeautifulSoup(self.driver.page_source, "html.parser")

                        title_tag = psoup.find("span", class_="VU-ZEz")
                        title = title_tag.get_text(strip=True) if title_tag else ""

                        price_tag = psoup.find("div", class_="Nx9bqj CxhGGd")
                        discounted_price = price_tag.get_text(strip=True).replace("₹", "").replace(",", "") if price_tag else ""

                        actual_price_tag = psoup.find("div", class_="yRaY8j A6+E6v")
                        price = actual_price_tag.get_text(strip=True).replace("₹", "").replace(",", "") if actual_price_tag else ""

                        rating_tag = psoup.find("div", class_="XQDdHH")
                        rating = rating_tag.get_text(strip=True) if rating_tag else ""

                        brand_extracted = title.split()[0] if title else ""
                        category = "laptop"

                        features_data = self.extract_mobile_features(psoup)
                        model_number = features_data["details"]["performance"].get("model_number", "")

                        data = {
                            "product_id": str(uuid.uuid4()),
                            "title": title,
                            "discounted_price": discounted_price,
                            "price": price,
                            "rating": rating,
                            "model_number": model_number,
                            "brand": brand_extracted,
                            "offers": self.extract_offers(psoup),
                            "image_url": self.extract_image_url(psoup),
                            "features": features_data,
                            "category": category,
                            "affiliatelink": url
                        }

                        all_data.append(data)
                        print(f"➡ Visiting: {url}")
                    except Exception as e:
                        print(f"Error scraping {url}: {e}")
                        continue

        self.driver.quit()

        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..\database\laptop"))
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, "flipkart.json")

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            print(f"📁 Data saved to {save_path}")
        except Exception as e:
            print(f"❌ Failed to save JSON: {e}")


        print("Data saved to database/laptop/flipkart.json")


if __name__ == "__main__":
    scraper = FlipkartMobileScraper()
    scraper.scrape()
