# Multi-Platform Product Scraper

This project is a unified scraping system built using Python and Selenium to extract product details (mobiles, laptops, etc.) from major Indian e-commerce websites:

- **Amazon**
- **Flipkart**
- **Croma**
- **JioMart**
- **Vijay Sales**

Each scraper gathers product **title**, **price**, **original price**, **offers**, **specifications**, and **URL**, and saves the data to structured JSON files.

---

## Project Structure

your_project/
│
├── main.py # Unified runner for all scrapers
├── amazon.py # Amazon scraper class
├── flipkart.py # Flipkart scraper class
├── croma.py # Croma scraper class
├── jiomart.py # JioMart scraper class
├── vijaysales.py # Vijay Sales scraper class
├── database/ # Folder for scraped JSON output
│ └── *.json
└── requirements.txt # Dependencies

 Example: Flipkart Only
If you want to scrape only Flipkart:

python
Copy
Edit

from flipkart import FlipkartSeleniumScraper

if __name__ == "__main__":
    flipkart_scraper = FlipkartSeleniumScraper()
    try:
        data = flipkart_scraper.scrape("IQOO mobile", pages=1)
        with open("database/mobilescrapdata.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    finally:
        flipkart_scraper.close()
Output
All scraped data is saved in JSON format under the database/ folder. Example fields:

{
  "Title": "iQOO Z9 5G (Brushed Green, 8GB RAM, 128GB Storage)",
  "Price": "₹19,999",
  "Actual_Price": "₹21,999",
  "Offers": {
    "HDFC": "10% Instant Discount..."
  },
  "Specifications": {
    "RAM": "8GB",
    "Processor": "MediaTek Dimensity..."
  },
  "Link": "https://www.amazon.in/dp/B0..."
}
