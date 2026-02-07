import asyncio
import json
import os
from utils.db import get_collection
from bson import ObjectId
from datetime import datetime

# Unified product schema for standardization
UNIFIED_SCHEMA = {
    "id": "",  # Unique product ID
    "title": "",  # Product title
    "brand": "",  # Product brand
    "category": "",  # Product category (standardized)
    "image": "",  # Primary product image URL
    "description": "",  # Product description
    "features": [],  # List of product features
    "tags": [],  # Search tags
    "vendors": {  # Vendor-specific data
        "amazon": {
            "price": 0,
            "discountprice": 0,
            "rating": 0,
            "reviews": 0,
            "availability": "",
            "link": "",
            "offers": {}
        },
        "flipkart": {
            "price": 0,
            "discountprice": 0,
            "rating": 0,
            "reviews": 0,
            "availability": "",
            "link": "",
            "offers": {}
        },
        "croma": {
            "price": 0,
            "discountprice": 0,
            "rating": 0,
            "reviews": 0,
            "availability": "",
            "link": "",
            "offers": {}
        },
        "jiomart": {
            "price": 0,
            "discountprice": 0,
            "rating": 0,
            "reviews": 0,
            "availability": "",
            "link": "",
            "offers": {}
        },
        "vijaysales": {
            "price": 0,
            "discountprice": 0,
            "rating": 0,
            "reviews": 0,
            "availability": "",
            "link": "",
            "offers": {}
        }
    },
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow()
}

# Category mapping for standardization
CATEGORY_MAPPING = {
    "mobile": "SmartPhone",
    "smartphone": "SmartPhone",
    "phone": "SmartPhone",
    "laptop": "Computer & Laptop",
    "computer": "Computer & Laptop",
    "notebook": "Computer & Laptop",
    "headphone": "Headphone",
    "earphone": "Headphone",
    "earbuds": "Headphone",
    "speaker": "Headphone",
    "gaming": "Gaming Console",
    "console": "Gaming Console",
    "camera": "Camera & Photo",
    "photography": "Camera & Photo",
    "watch": "Watches & Accessories",
    "smartwatch": "Watches & Accessories",
    "fitness": "Warable Technology",
    "tracker": "Warable Technology",
    "tv": "TV & Homes Appliances",
    "television": "TV & Homes Appliances",
    "appliance": "TV & Homes Appliances",
    "accessory": "Mobile Accessories",
    "case": "Mobile Accessories",
    "charger": "Mobile Accessories",
    "cable": "Mobile Accessories"
}

def extract_price(price_str):
    """Extract numeric price from price string"""
    if not price_str:
        return 0
    
    # Remove currency symbols and commas
    price_clean = str(price_str).replace('₹', '').replace(',', '').replace('Rs', '').strip()
    
    try:
        return float(price_clean)
    except (ValueError, TypeError):
        return 0

def standardize_category(category_str):
    """Standardize category names"""
    if not category_str:
        return "Electronics Devices"
    
    category_lower = category_str.lower().strip()
    
    for key, standard_cat in CATEGORY_MAPPING.items():
        if key in category_lower:
            return standard_cat
    
    return category_str.title()

def extract_rating(rating_str):
    """Extract numeric rating"""
    if not rating_str:
        return 0
    
    try:
        rating_clean = str(rating_str).replace('out of 5', '').replace('/5', '').strip()
        return float(rating_clean)
    except (ValueError, TypeError):
        return 0

def extract_reviews(reviews_str):
    """Extract numeric review count"""
    if not reviews_str:
        return 0
    
    try:
        # Remove common words and extract number
        reviews_clean = str(reviews_str).replace('reviews', '').replace('ratings', '').replace(',', '').strip()
        return int(reviews_clean)
    except (ValueError, TypeError):
        return 0

def generate_product_id(title, brand):
    """Generate unique product ID"""
    import hashlib
    content = f"{title}_{brand}".lower().replace(' ', '_')
    return hashlib.md5(content.encode()).hexdigest()[:12]

async def process_scraped_files():
    """Process all scraped JSON files and standardize them"""
    
    database_root = "core/database"
    processed_products = {}
    
    # Process each vendor's data
    vendors = ["amazon", "flipkart", "croma", "jiomart", "vijaysales"]
    categories = ["mobiles", "laptop", "mobileaccessories", "laptopaccessories"]
    
    for category in categories:
        category_path = os.path.join(database_root, category)
        if not os.path.exists(category_path):
            continue
            
        print(f"Processing category: {category}")
        
        for vendor in vendors:
            vendor_file = os.path.join(category_path, f"{vendor}.json")
            if not os.path.exists(vendor_file):
                continue
                
            print(f"  Processing {vendor}.json...")
            
            try:
                with open(vendor_file, 'r', encoding='utf-8') as f:
                    vendor_data = json.load(f)
                
                # Handle different data structures
                products_list = vendor_data
                if isinstance(vendor_data, dict) and 'products' in vendor_data:
                    products_list = vendor_data['products']
                
                for product_data in products_list:
                    # Extract basic info
                    title = product_data.get('Title', product_data.get('title', ''))
                    brand = product_data.get('Brand', product_data.get('brand', ''))
                    
                    if not title:
                        continue
                    
                    product_id = generate_product_id(title, brand)
                    
                    # Create or update product
                    if product_id not in processed_products:
                        processed_products[product_id] = UNIFIED_SCHEMA.copy()
                        processed_products[product_id]['id'] = product_id
                        processed_products[product_id]['title'] = title
                        processed_products[product_id]['brand'] = brand
                        processed_products[product_id]['category'] = standardize_category(category)
                        processed_products[product_id]['vendors'] = {v: UNIFIED_SCHEMA['vendors']['amazon'].copy() for v in vendors}
                    
                    # Update vendor-specific data
                    vendor_info = processed_products[product_id]['vendors'][vendor]
                    vendor_info['price'] = extract_price(product_data.get('Price', product_data.get('price', 0)))
                    vendor_info['discountprice'] = extract_price(product_data.get('Actual_Price', product_data.get('discountPrice', 0)))
                    vendor_info['rating'] = extract_rating(product_data.get('Rating', product_data.get('rating', 0)))
                    vendor_info['reviews'] = extract_reviews(product_data.get('Reviews', product_data.get('reviews', 0)))
                    vendor_info['availability'] = product_data.get('Availability', product_data.get('availability', 'In Stock'))
                    vendor_info['link'] = product_data.get('Link', product_data.get('link', ''))
                    vendor_info['offers'] = product_data.get('Offers', product_data.get('offers', {}))
                    
                    # Update common fields
                    if not processed_products[product_id]['image']:
                        processed_products[product_id]['image'] = product_data.get('Image', product_data.get('imageUrl', ''))
                    
                    if not processed_products[product_id]['description']:
                        processed_products[product_id]['description'] = product_data.get('Description', product_data.get('description', ''))
                    
                    # Extract features
                    specs = product_data.get('Specifications', product_data.get('specs', product_data.get('features', {})))
                    if specs and isinstance(specs, dict):
                        features = [f"{k}: {v}" for k, v in specs.items()]
                        processed_products[product_id]['features'] = features
                    
                    processed_products[product_id]['updated_at'] = datetime.utcnow()
                    
            except Exception as e:
                print(f"Error processing {vendor_file}: {e}")
                continue
    
    print(f"Processed {len(processed_products)} unique products")
    return list(processed_products.values())

async def sync_to_database(products):
    """Sync processed products to MongoDB"""
    try:
        collection = get_collection("ecommerce", "ecommerce_data")
        
        # Clear existing data
        await collection.delete_many({})
        print("Cleared existing products")
        
        # Insert new standardized data
        if products:
            await collection.insert_many(products)
            print(f"Inserted {len(products)} standardized products")
        
        # Create indexes for better performance
        await collection.create_index("id")
        await collection.create_index("title")
        await collection.create_index("brand")
        await collection.create_index("category")
        await collection.create_index([("title", "text"), ("brand", "text"), ("category", "text")])
        print("Created database indexes")
        
    except Exception as e:
        print(f"Database sync error: {e}")

async def main():
    """Main synchronization process"""
    print("🚀 Starting data standardization and sync...")
    
    try:
        # Process scraped files
        standardized_products = await process_scraped_files()
        
        # Save to file for backup
        with open('standardized_products.json', 'w', encoding='utf-8') as f:
            json.dump(standardized_products, f, indent=2, default=str)
        print("💾 Saved standardized products to file")
        
        # Sync to database
        await sync_to_database(standardized_products)
        
        print("✅ Data standardization and sync completed!")
        
    except Exception as e:
        print(f"❌ Sync failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())