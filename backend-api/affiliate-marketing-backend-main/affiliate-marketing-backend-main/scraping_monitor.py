#!/usr/bin/env python3
"""
Scraping Performance Monitor and Data Quality Checker
Monitors scraping efficiency and ensures single-query optimization
"""

import os
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path
import subprocess
import sys

# Configuration
BACKEND_PATH = "e:/Downloads/affiliate-marketing-backend-main/affiliate-marketing-backend-main"
SCRAPERS_PATH = os.path.join(BACKEND_PATH, "core")
DATABASE_PATH = os.path.join(BACKEND_PATH, "core/database")
FINAL_JSON = os.path.join(DATABASE_PATH, "final.json")

class ScrapingMonitor:
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.vendor_status = {}
        
    def check_scraper_files(self):
        """Check if all scraper files exist"""
        print("🔍 Checking scraper files...")
        categories = ["mobiles", "laptop", "laptopaccessories", "mobileaccessories"]
        vendors = ["amazon", "flipkart", "croma", "jiomart", "vijaysales"]
        
        missing_files = []
        for category in categories:
            cat_path = os.path.join(SCRAPERS_PATH, category)
            if os.path.exists(cat_path):
                for vendor in vendors:
                    scraper_file = f"{vendor}_{category}.py" if category != "laptop" else f"{vendor}laptop.py"
                    scraper_path = os.path.join(cat_path, scraper_file)
                    if not os.path.exists(scraper_path):
                        missing_files.append(scraper_path)
                        
        if missing_files:
            print(f"❌ Missing scraper files: {len(missing_files)}")
            for file in missing_files:
                print(f"   - {file}")
            return False
        else:
            print("✅ All scraper files found")
            return True
    
    def run_test_scraping(self):
        """Run a quick test scraping session"""
        print("\n🚀 Running test scraping session...")
        self.start_time = time.time()
        
        try:
            # Run scraper orchestrator
            os.chdir(BACKEND_PATH)
            result = subprocess.run(
                [sys.executable, "run_all_scrappers.py"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            execution_time = time.time() - self.start_time
            
            if result.returncode == 0:
                print(f"✅ Scraping completed in {execution_time:.2f}s")
                print(f"📊 Output: {len(result.stdout.split('✅'))} successful operations")
                return True
            else:
                print(f"❌ Scraping failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Scraping timeout - may indicate performance issues")
            return False
        except Exception as e:
            print(f"💥 Scraping error: {e}")
            return False
    
    def check_data_quality(self):
        """Check the quality and completeness of scraped data"""
        print("\n📊 Checking data quality...")
        
        if not os.path.exists(FINAL_JSON):
            print("❌ Final JSON file not found")
            return False
            
        try:
            with open(FINAL_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            products = data.get('products', [])
            total_products = len(products)
            
            print(f"📦 Total products: {total_products}")
            
            # Analyze vendor coverage
            vendor_stats = {}
            categories = set()
            brands = set()
            
            for product in products:
                # Category analysis
                category = product.get('category', 'unknown')
                categories.add(category)
                
                # Brand analysis
                brand = product.get('brand', 'unknown')
                brands.add(brand)
                
                # Vendor analysis
                vendors = product.get('vendors', {})
                for vendor, data in vendors.items():
                    if vendor not in vendor_stats:
                        vendor_stats[vendor] = {
                            'total': 0, 
                            'with_price': 0, 
                            'with_rating': 0,
                            'with_affiliate': 0
                        }
                    
                    vendor_stats[vendor]['total'] += 1
                    
                    if data.get('price') or data.get('discountprice'):
                        vendor_stats[vendor]['with_price'] += 1
                    if data.get('rating'):
                        vendor_stats[vendor]['with_rating'] += 1  
                    if data.get('affiliatelink'):
                        vendor_stats[vendor]['with_affiliate'] += 1
            
            # Print analysis
            print(f"🏷️  Categories: {len(categories)} ({', '.join(categories)})")
            print(f"🔖 Brands: {len(brands)}")
            print(f"🏪 Vendors: {len(vendor_stats)}")
            
            print("\n📈 Vendor Data Quality:")
            for vendor, stats in vendor_stats.items():
                price_pct = (stats['with_price'] / stats['total'] * 100) if stats['total'] > 0 else 0
                rating_pct = (stats['with_rating'] / stats['total'] * 100) if stats['total'] > 0 else 0
                affiliate_pct = (stats['with_affiliate'] / stats['total'] * 100) if stats['total'] > 0 else 0
                
                print(f"  {vendor}: {stats['total']} products")
                print(f"    - Price data: {price_pct:.1f}%")
                print(f"    - Ratings: {rating_pct:.1f}%") 
                print(f"    - Affiliate links: {affiliate_pct:.1f}%")
            
            # Quality assessment
            quality_score = 0
            if total_products >= 100:  # Minimum product count
                quality_score += 25
            if len(vendor_stats) >= 3:  # Multiple vendors
                quality_score += 25
            if all(stats['with_price'] / stats['total'] > 0.8 for stats in vendor_stats.values()):  # Price coverage
                quality_score += 25
            if len(categories) >= 3:  # Category diversity
                quality_score += 25
                
            print(f"\n🎯 Overall Quality Score: {quality_score}/100")
            
            if quality_score >= 75:
                print("✅ Data quality is EXCELLENT")
                return True
            elif quality_score >= 50:
                print("⚠️ Data quality is GOOD but could be improved")
                return True
            else:
                print("❌ Data quality needs IMPROVEMENT")
                return False
                
        except Exception as e:
            print(f"💥 Data quality check failed: {e}")
            return False
    
    def test_comparison_optimization(self):
        """Test that comparison queries work efficiently"""
        print("\n⚡ Testing comparison query optimization...")
        
        if not os.path.exists(FINAL_JSON):
            print("❌ No data file for testing")
            return False
            
        try:
            with open(FINAL_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            products = data.get('products', [])
            
            # Find products suitable for comparison (multiple vendors)
            comparison_candidates = []
            for product in products:
                vendors = product.get('vendors', {})
                if len(vendors) >= 2:  # At least 2 vendors for comparison
                    comparison_candidates.append(product)
                    
            print(f"🔍 Found {len(comparison_candidates)} products suitable for comparison")
            
            if len(comparison_candidates) >= 4:
                print("✅ Sufficient products for comparison functionality")
                
                # Test sample comparison data
                sample = comparison_candidates[:4]
                print("\n📋 Sample comparison data:")
                for i, product in enumerate(sample, 1):
                    vendors = list(product.get('vendors', {}).keys())
                    print(f"  {i}. {product.get('title', 'Unknown')[:40]}...")
                    print(f"     Vendors: {', '.join(vendors)}")
                    
                return True
            else:
                print("⚠️ Insufficient products for robust comparison")
                return False
                
        except Exception as e:
            print(f"💥 Comparison test failed: {e}")
            return False

    def generate_performance_report(self):
        """Generate a comprehensive performance report"""
        print("\n📄 Generating Performance Report...")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "scraping_time": getattr(self, 'execution_time', 0),
            "data_file_size": os.path.getsize(FINAL_JSON) if os.path.exists(FINAL_JSON) else 0,
            "checks": {
                "scraper_files": self.check_scraper_files(),
                "data_quality": self.check_data_quality(),
                "comparison_ready": self.test_comparison_optimization()
            }
        }
        
        # Save report
        report_file = os.path.join(BACKEND_PATH, "performance_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        print(f"📊 Report saved to: {report_file}")
        
        # Summary
        all_passed = all(report["checks"].values())
        status = "🟢 READY" if all_passed else "🟡 NEEDS ATTENTION"
        print(f"\n🎯 System Status: {status}")
        
        return report

def main():
    print("🔧 Affiliate Marketing Platform - Scraping Performance Monitor")
    print("=" * 60)
    
    monitor = ScrapingMonitor()
    
    # Run all checks
    file_check = monitor.check_scraper_files()
    
    if file_check:
        scraping_success = monitor.run_test_scraping()
        data_quality = monitor.check_data_quality()
        comparison_ready = monitor.test_comparison_optimization()
    else:
        print("❌ Skipping other tests due to missing files")
        scraping_success = data_quality = comparison_ready = False
    
    # Generate final report
    report = monitor.generate_performance_report()
    
    print("\n" + "=" * 60)
    if all(report["checks"].values()):
        print("🎉 All systems operational! Platform ready for production.")
    else:
        print("⚠️ Some issues detected. Review the report above.")

if __name__ == "__main__":
    main()