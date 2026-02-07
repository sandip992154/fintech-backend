from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json

class CromaSpecificationScraper:
    def __init__(self, headless=False):
        options = Options()
    
        # options.add_argument("--headless")
        options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def get_specifications(self, url):
        self.driver.get(url)
        time.sleep(3)

        try:
            view_more_btn = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[@id='specification']//button[contains(text(), 'View More')]")))
            self.driver.execute_script("arguments[0].click();", view_more_btn)
            time.sleep(2)
        except:
            print("No 'View More' button found or already expanded.")

        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        spec_block = soup.find("div", id="specification_container")
        # print(spec_block)
        raw_specs = {}

        if spec_block:
            categories = spec_block.find_all("ul", class_="cp-specification-info")
            for spec in categories:
                labels = spec.find_all("li", class_="cp-specification-spec-title")
                values = spec.find_all("li", class_="cp-specification-spec-details")

                for lbl, val in zip(labels, values):
                    key = lbl.get_text(strip=True)
                    value = val.get_text(strip=True)
                    if key:
                        raw_specs[key] = value

        return self.map_raw_to_features(raw_specs)

    def map_raw_to_features(self, raw):
        return {
            "type": "mobile",
            "details": {
                "Design": {
                    "Dimensions": raw.get("Dimensions In CM (WxDxH)", ""),
                    "Weight": raw.get("Main Unit Weight", ""),
                    "Form Factor": raw.get("Mobile Design", ""),
                    "Stylus Support": raw.get("Stylus Support", ""),
                    "Color": raw.get("Color", raw.get("Brand Color", ""))
                },
                "Display": {
                    "Resolution": raw.get("Screen Resolution", ""),
                    "Touch Screen": raw.get("Screen Type", ""),
                    "Display Features": f"Refresh Rate: {raw.get('Refresh Rate', '')} | Brightness: {raw.get('Brightness', '')}"
                },
                "Network & Connectivity": {
                    "Wireless Tech": raw.get("Cellular Technology", ""),
                    "Connectivity": f"Wi-Fi: {raw.get('Wi-Fi Supported', '')}, Bluetooth: {raw.get('Bluetooth Specifications', '')}",
                    "GPS": raw.get("Smart Sensors", ""),
                    "SIM": raw.get("SIM Type", ""),
                    "Mobile Hotspot": raw.get("Wi-Fi Features", "")
                },
                "Performance": {
                    "Operating System": f"{raw.get('OS Name & Version', '')} ({raw.get('OS Type', '')})",
                    "Model Number": raw.get("Model Number", ""),
                    "processor": f"{raw.get('Processor Name', '')} ({raw.get('Processor Brand', '')})"
                },
                "storage": {
                    "ram": raw.get("RAM", ""),
                    "rom": raw.get("Internal Storage", "")
                },
                "Camera": {
                    "Rear Camera": raw.get("Rear Camera", ""),
                    "Front Camera": raw.get("Front Camera", ""),
                    "Camera Features": raw.get("Camera Features", "")
                },
                "Battery": {
                    "Battery Capacity": raw.get("Battery Capacity", ""),
                    "Battery Type": raw.get("Battery Type", ""),
                    "Fast Charging": raw.get("Fast Charging Capability", "")
                },
                "Audio": {
                    "Audio Jack": raw.get("Audio Jack Port", "")
                },
                "Box Contents": {
                    "In the Box": raw.get("Package Includes", raw.get("Main product", ""))
                },
                "Manufacturer": {
                    "Brand": raw.get("Brand", "")
                }
            }
        }

    def close(self):
        self.driver.quit()


# Example usage
if __name__ == "__main__":
    scraper = CromaSpecificationScraper(headless=False)
    url = "https://www.croma.com/redmi-12-5g-6gb-ram-128gb-pastel-blue-/p/275650"
    
    try:
        data = scraper.get_specifications(url)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    finally:
        scraper.close()
