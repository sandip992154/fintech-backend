# Install required packages for fast scraping
pip install fake-useragent aiohttp

# Windows batch script for optimized scraping
@echo off
echo 🚀 Starting Fast Scraping System...
echo Reserving 2 CPU cores for system stability
echo.

cd /d "e:\Downloads\affiliate-marketing-backend-main\affiliate-marketing-backend-main"

echo ⚡ Method 1: Running optimized parallel scraper...
python optimized_scraper.py
echo.

echo ⚡ Method 2: Running all category scrapers...
python run_all_scrappers.py
echo.

echo 🔄 Combining scraped data...
python combine_categories.py
echo.

echo ✅ Fast scraping complete!
echo 📊 Check results in core/database/ folders
pause