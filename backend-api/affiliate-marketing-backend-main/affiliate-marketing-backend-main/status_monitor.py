import os
import json
import time
from datetime import datetime

def check_scraping_status():
    """Monitor scraping status and show results"""
    database_path = "./core/database"
    
    print("🔍 SCRAPING STATUS MONITOR")
    print("=" * 50)
    print(f"⏰ Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if not os.path.exists(database_path):
        print("❌ Database folder not found!")
        return
        
    categories = ["mobiles", "laptop", "laptopaccessories", "mobileaccessories"]
    vendors = ["amazon", "flipkart", "croma", "jiomart", "vijaysales"]
    
    total_products = 0
    
    for category in categories:
        category_path = os.path.join(database_path, category)
        if not os.path.exists(category_path):
            print(f"⚠️ {category}: folder not found")
            continue
            
        print(f"📂 {category.upper()}:")
        category_products = 0
        
        for vendor in vendors:
            vendor_file = os.path.join(category_path, f"{vendor}.json")
            if os.path.exists(vendor_file):
                try:
                    with open(vendor_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, dict) and "products" in data:
                        count = len(data["products"])
                    elif isinstance(data, list):
                        count = len(data)
                    else:
                        count = 0
                        
                    file_size = os.path.getsize(vendor_file) / 1024  # KB
                    mod_time = os.path.getmtime(vendor_file)
                    time_ago = time.time() - mod_time
                    
                    if time_ago < 3600:  # Less than 1 hour
                        time_str = f"{int(time_ago/60)}m ago"
                        status = "🟢"
                    elif time_ago < 86400:  # Less than 24 hours
                        time_str = f"{int(time_ago/3600)}h ago"
                        status = "🟡"
                    else:
                        time_str = f"{int(time_ago/86400)}d ago"
                        status = "🔴"
                    
                    print(f"   {status} {vendor}: {count} products ({file_size:.1f}KB) - {time_str}")
                    category_products += count
                    
                except Exception as e:
                    print(f"   ❌ {vendor}: Error reading file - {e}")
            else:
                print(f"   ⭕ {vendor}: No data file")
        
        # Check combined file
        combined_file = os.path.join(category_path, "_combined.json")
        if os.path.exists(combined_file):
            try:
                with open(combined_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                combined_count = len(data.get("products", []))
                print(f"   🔗 Combined: {combined_count} unified products")
            except:
                print(f"   ⚠️ Combined: Error reading file")
        
        print(f"   📊 Total {category}: {category_products} products")
        total_products += category_products
        print()
    
    # Check final combined file
    final_file = os.path.join(database_path, "final.json")
    if os.path.exists(final_file):
        try:
            with open(final_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            final_count = len(data.get("products", []))
            file_size = os.path.getsize(final_file) / 1024
            print(f"🎯 FINAL DATABASE: {final_count} unified products ({file_size:.1f}KB)")
        except Exception as e:
            print(f"❌ Final database error: {e}")
    else:
        print("⚠️ Final database not created yet")
    
    print(f"\n📈 TOTAL SCRAPED: {total_products} products across all vendors")
    print("=" * 50)

if __name__ == "__main__":
    check_scraping_status()