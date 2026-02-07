# main.py
from amazon import AmazonMobileScraper
from croma import CromaScraper
from flipkart import FlipkartSeleniumScraper
from jiomart import JioMartScraper
from vijaysales import VijaySalesScraper

import json
query="vivo mobile"
def save_data(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f" Saved: {filename}")

def run_all_scrapers():
    # Amazon
    amazon_scraper = AmazonMobileScraper()
    amazon_data = amazon_scraper.scrape_mobiles(f"{query}", max_pages=1)
    amazon_scraper.save_to_json(amazon_data, "../database/mobilescrapdata.json")
    amazon_scraper.close()
    
    # Croma
    croma_scraper = CromaScraper()
    croma_data = croma_scraper.scrape_all_products(f"{query}")
    croma_scraper.save_to_json(croma_data, "../database/mobilescrapdata.json")
    croma_scraper.close()
   

    # Flipkart
    flipkart_scraper = FlipkartSeleniumScraper()
    flipkart_data = flipkart_scraper.scrape(f"{query}")
    flipkart_scraper.save_to_json(flipkart_data, "../database/mobilescrapdata.json")
    flipkart_scraper.close()

    # JioMart
    jiomart_scraper = JioMartScraper()
    jiomart_data = jiomart_scraper.scrape_products(f"{query}", max_scrolls=5)
    jiomart_scraper.save_to_json(jiomart_data, "../database/mobilescrapdata.json")
    jiomart_scraper.close()

    # VijaySales
    vijay_scraper = VijaySalesScraper()
    vijay_data = vijay_scraper.scrape_all_products_on_first_page(f"{query}")
    vijay_scraper.save_to_json(vijay_data, "../database/mobilescrapdata.json")
    vijay_scraper.close()

if __name__ == "__main__":
    run_all_scrapers()
