import os
import json
import asyncio
import aiohttp
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent

class OptimizedScraper:
    def __init__(self):
        # Reserve 2 cores for system - use remaining cores for scraping
        self.max_workers = max(1, multiprocessing.cpu_count() - 2)
        self.ua = UserAgent()
        self.session = requests.Session()
        
        # Optimize Chrome options for speed
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless=new")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--disable-logging")
        self.chrome_options.add_argument("--disable-plugins")
        self.chrome_options.add_argument("--disable-images")  # Skip images for faster loading
        self.chrome_options.add_argument("--disable-javascript")  # Disable JS when possible
        self.chrome_options.add_argument("--page-load-strategy=eager")
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
    def get_driver(self):
        """Get optimized Chrome driver"""
        options = self.chrome_options
        options.add_argument(f"--user-agent={self.ua.random}")
        return webdriver.Chrome(options=options)
    
    async def fetch_async(self, session, url):
        """Async HTTP request for faster data fetching"""
        try:
            headers = {'User-Agent': self.ua.random}
            async with session.get(url, headers=headers, timeout=10) as response:
                return await response.text()
        except Exception as e:
            print(f"Async fetch error for {url}: {e}")
            return None

class FastAmazonScraper(OptimizedScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.amazon.in"
        
    def scrape_product_batch(self, search_queries, output_file):
        """Scrape multiple products in batch with optimized driver reuse"""
        driver = self.get_driver()
        all_products = []
        
        try:
            for query in search_queries:
                products = self._scrape_search_results(driver, query, max_pages=2)
                all_products.extend(products)
                time.sleep(1)  # Reduced delay
                
        finally:
            driver.quit()
            
        # Save to file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({"products": all_products}, f, ensure_ascii=False, indent=2)
            
        return len(all_products)
    
    def _scrape_search_results(self, driver, query, max_pages=2):
        products = []
        
        for page in range(1, max_pages + 1):
            try:
                url = f"{self.base_url}/s?k={query}&page={page}"
                driver.get(url)
                
                # Wait for results with shorter timeout
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-component-type='s-search-result']"))
                )
                
                soup = BeautifulSoup(driver.page_source, "html.parser")
                product_cards = soup.find_all("div", {"data-component-type": "s-search-result"})
                
                for card in product_cards[:10]:  # Limit to first 10 products per page
                    product = self._extract_product_data(card)
                    if product:
                        products.append(product)
                        
            except Exception as e:
                print(f"Error scraping page {page} for {query}: {e}")
                
        return products
    
    def _extract_product_data(self, card):
        try:
            # Extract basic info quickly
            title_elem = card.find("h2", class_="a-size-mini") or card.find("span", class_="a-size-base-plus")
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            price_elem = card.find("span", class_="a-price-whole") or card.find("span", class_="a-offscreen")
            price = price_elem.get_text(strip=True) if price_elem else ""
            
            rating_elem = card.find("span", class_="a-icon-alt")
            rating = rating_elem.get_text(strip=True).split()[0] if rating_elem else ""
            
            link_elem = card.find("a", href=True)
            link = f"https://www.amazon.in{link_elem['href']}" if link_elem else ""
            
            if title and price:
                return {
                    "title": title,
                    "price": price,
                    "rating": rating,
                    "affiliatelink": link,
                    "brand": self._extract_brand(title),
                    "timestamp": int(time.time())
                }
        except Exception as e:
            print(f"Error extracting product: {e}")
        return None
    
    def _extract_brand(self, title):
        """Extract brand from title"""
        brands = ["apple", "samsung", "xiaomi", "realme", "oneplus", "oppo", "vivo", "redmi"]
        title_lower = title.lower()
        for brand in brands:
            if brand in title_lower:
                return brand.title()
        return ""

class FastFlipkartScraper(OptimizedScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.flipkart.com"
        
    def scrape_product_batch(self, search_queries, output_file):
        """Fast Flipkart scraping with optimized approach"""
        driver = self.get_driver()
        all_products = []
        
        try:
            for query in search_queries:
                products = self._scrape_search_results(driver, query, max_pages=2)
                all_products.extend(products)
                time.sleep(1)
                
        finally:
            driver.quit()
            
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({"products": all_products}, f, ensure_ascii=False, indent=2)
            
        return len(all_products)
    
    def _scrape_search_results(self, driver, query, max_pages=2):
        products = []
        
        for page in range(1, max_pages + 1):
            try:
                url = f"{self.base_url}/search?q={query}&page={page}"
                driver.get(url)
                
                time.sleep(2)  # Minimal wait
                soup = BeautifulSoup(driver.page_source, "html.parser")
                product_cards = soup.find_all("div", class_="_1AtVbE")[:10]  # Limit results
                
                for card in product_cards:
                    product = self._extract_product_data(card)
                    if product:
                        products.append(product)
                        
            except Exception as e:
                print(f"Error scraping Flipkart page {page}: {e}")
                
        return products
    
    def _extract_product_data(self, card):
        try:
            title_elem = card.find("div", class_="_4rR01T")
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            price_elem = card.find("div", class_="_30jeq3")
            price = price_elem.get_text(strip=True) if price_elem else ""
            
            rating_elem = card.find("div", class_="_3LWZlK")
            rating = rating_elem.get_text(strip=True) if rating_elem else ""
            
            link_elem = card.find("a", href=True)
            link = f"https://www.flipkart.com{link_elem['href']}" if link_elem else ""
            
            if title and price:
                return {
                    "title": title,
                    "price": price,
                    "rating": rating,
                    "affiliatelink": link,
                    "brand": self._extract_brand(title),
                    "timestamp": int(time.time())
                }
        except Exception as e:
            print(f"Error extracting Flipkart product: {e}")
        return None
    
    def _extract_brand(self, title):
        brands = ["apple", "samsung", "xiaomi", "realme", "oneplus", "oppo", "vivo", "redmi"]
        title_lower = title.lower()
        for brand in brands:
            if brand in title_lower:
                return brand.title()
        return ""

def run_parallel_scraping():
    """Run optimized parallel scraping with core reservation"""
    start_time = time.time()
    
    # Define scraping tasks
    scraping_tasks = [
        {
            "scraper": FastAmazonScraper(),
            "queries": ["samsung mobile", "apple iphone", "xiaomi phone"],
            "output": "./core/database/mobiles/amazon.json"
        },
        {
            "scraper": FastFlipkartScraper(),
            "queries": ["samsung mobile", "apple iphone", "xiaomi phone"],
            "output": "./core/database/mobiles/flipkart.json"
        }
    ]
    
    # Reserve 2 cores - use remaining for scraping
    max_workers = max(1, multiprocessing.cpu_count() - 2)
    print(f"🚀 Starting optimized scraping with {max_workers} workers (reserving 2 cores for system)")
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for task in scraping_tasks:
            future = executor.submit(
                task["scraper"].scrape_product_batch,
                task["queries"],
                task["output"]
            )
            futures.append(future)
        
        total_products = 0
        for future in futures:
            try:
                count = future.result(timeout=300)  # 5 minute timeout per scraper
                total_products += count
                print(f"✅ Scraper completed: {count} products")
            except Exception as e:
                print(f"❌ Scraper failed: {e}")
    
    end_time = time.time()
    print(f"🎉 Scraping completed in {end_time - start_time:.2f} seconds")
    print(f"📊 Total products scraped: {total_products}")
    
    return total_products

if __name__ == "__main__":
    try:
        run_parallel_scraping()
    except KeyboardInterrupt:
        print("⏹️ Scraping interrupted by user")
    except Exception as e:
        print(f"❌ Scraping failed: {e}")