#!/usr/bin/env python3
"""
Quick Mobile Data Generator
Creates sample mobile data for immediate testing while scrapers run
"""

import json
import os
import uuid
from datetime import datetime

def create_sample_mobile_data():
    """Generate sample mobile data for immediate use"""
    
    sample_mobiles = [
        {
            "id": str(uuid.uuid4()),
            "title": "Samsung Galaxy S24 Ultra 256GB",
            "brand": "Samsung",
            "category": "mobiles",
            "price": "₹1,24,999",
            "discountprice": "₹1,09,999", 
            "rating": "4.4",
            "affiliatelink": "https://www.amazon.in/dp/B0CSCDQZ5V",
            "features": ["256GB Storage", "12GB RAM", "200MP Camera", "S Pen"],
            "image": {
                "thumbnail": "https://m.media-amazon.com/images/I/71k7f1k1aVL._SX679_.jpg",
                "urls": ["https://m.media-amazon.com/images/I/71k7f1k1aVL._SX679_.jpg"]
            },
            "vendors": {
                "amazon": {
                    "price": "₹1,24,999",
                    "discountprice": "₹1,09,999",
                    "rating": "4.4",
                    "affiliatelink": "https://www.amazon.in/dp/B0CSCDQZ5V",
                    "offers": ["Bank Offer: 10% off", "Exchange up to ₹15,000"]
                },
                "flipkart": {
                    "price": "₹1,25,999",
                    "discountprice": "₹1,11,999", 
                    "rating": "4.3",
                    "affiliatelink": "https://www.flipkart.com/samsung-galaxy-s24-ultra",
                    "offers": ["Bank Offer: 5% off", "Exchange up to ₹12,000"]
                }
            }
        },
        {
            "id": str(uuid.uuid4()),
            "title": "iPhone 15 Pro Max 256GB",
            "brand": "Apple",
            "category": "mobiles",
            "price": "₹1,59,900",
            "discountprice": "₹1,49,900",
            "rating": "4.6",
            "affiliatelink": "https://www.amazon.in/dp/B0CHX8WGN8",
            "features": ["256GB Storage", "A17 Pro Chip", "48MP Camera", "Titanium Design"],
            "image": {
                "thumbnail": "https://m.media-amazon.com/images/I/81SigpJN1KL._SX679_.jpg",
                "urls": ["https://m.media-amazon.com/images/I/81SigpJN1KL._SX679_.jpg"]
            },
            "vendors": {
                "amazon": {
                    "price": "₹1,59,900",
                    "discountprice": "₹1,49,900",
                    "rating": "4.6",
                    "affiliatelink": "https://www.amazon.in/dp/B0CHX8WGN8",
                    "offers": ["No Cost EMI", "Apple Care+ available"]
                },
                "croma": {
                    "price": "₹1,59,900",
                    "discountprice": "₹1,52,900",
                    "rating": "4.5", 
                    "affiliatelink": "https://www.croma.com/iphone-15-pro-max",
                    "offers": ["Croma Exchange Bonus", "Extended Warranty"]
                }
            }
        },
        {
            "id": str(uuid.uuid4()),
            "title": "OnePlus 12 256GB",
            "brand": "OnePlus",
            "category": "mobiles",
            "price": "₹69,999",
            "discountprice": "₹64,999",
            "rating": "4.3",
            "affiliatelink": "https://www.amazon.in/dp/B0CSVJ8KNH",
            "features": ["256GB Storage", "16GB RAM", "50MP Camera", "100W Charging"],
            "image": {
                "thumbnail": "https://m.media-amazon.com/images/I/61KCOj8aGjL._SX679_.jpg",
                "urls": ["https://m.media-amazon.com/images/I/61KCOj8aGjL._SX679_.jpg"]
            },
            "vendors": {
                "amazon": {
                    "price": "₹69,999",
                    "discountprice": "₹64,999",
                    "rating": "4.3",
                    "affiliatelink": "https://www.amazon.in/dp/B0CSVJ8KNH",
                    "offers": ["Bank Offer: ₹3,000 off", "Exchange up to ₹8,000"]
                },
                "flipkart": {
                    "price": "₹70,999",
                    "discountprice": "₹65,999",
                    "rating": "4.2",
                    "affiliatelink": "https://www.flipkart.com/oneplus-12",
                    "offers": ["Super Coin Rewards", "Complete Mobile Protection"]
                }
            }
        }
    ]
    
    return sample_mobiles

def create_sample_accessories():
    """Generate sample mobile accessories data"""
    
    sample_accessories = [
        {
            "id": str(uuid.uuid4()),
            "title": "Apple AirPods Pro (2nd Generation)",
            "brand": "Apple", 
            "category": "mobile accessories",
            "price": "₹24,900",
            "discountprice": "₹22,900",
            "rating": "4.5",
            "affiliatelink": "https://www.amazon.in/dp/B0BDHWDR12",
            "features": ["Active Noise Cancellation", "Spatial Audio", "MagSafe Case"],
            "image": {
                "thumbnail": "https://m.media-amazon.com/images/I/61SUj2aKoEL._SX679_.jpg",
                "urls": ["https://m.media-amazon.com/images/I/61SUj2aKoEL._SX679_.jpg"]
            },
            "vendors": {
                "amazon": {
                    "price": "₹24,900",
                    "discountprice": "₹22,900", 
                    "rating": "4.5",
                    "affiliatelink": "https://www.amazon.in/dp/B0BDHWDR12",
                    "offers": ["EMI from ₹1,100/month", "1 Year Warranty"]
                }
            }
        }
    ]
    
    return sample_accessories

def main():
    """Generate and save sample data"""
    
    print("🏗️ CREATING SAMPLE DATA FOR IMMEDIATE USE")
    print("=" * 45)
    
    # Create mobile data
    mobiles = create_sample_mobile_data()
    mobile_file = "core/database/mobiles/sample_data.json"
    os.makedirs(os.path.dirname(mobile_file), exist_ok=True)
    
    with open(mobile_file, 'w', encoding='utf-8') as f:
        json.dump({"products": mobiles}, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Created {len(mobiles)} sample mobiles → {mobile_file}")
    
    # Create mobile accessories data  
    accessories = create_sample_accessories()
    acc_file = "core/database/mobileaccessories/sample_data.json"
    os.makedirs(os.path.dirname(acc_file), exist_ok=True)
    
    with open(acc_file, 'w', encoding='utf-8') as f:
        json.dump({"products": accessories}, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Created {len(accessories)} sample accessories → {acc_file}")
    
    # Update totals
    print("\n📊 UPDATED TOTALS:")
    print(f"📱 Mobiles: +{len(mobiles)} products")
    print(f"📱🔌 Mobile Accessories: +{len(accessories)} products")
    print(f"🎯 Total NEW products: {len(mobiles) + len(accessories)}")
    
    print("\n⚡ NEXT STEPS:")
    print("1. ✅ Sample data ready for immediate frontend testing")
    print("2. 🔄 Real scrapers running in background") 
    print("3. 🔄 Run combine_categories.py to merge all data")
    print("4. 🚀 Start backend API to serve data")

if __name__ == "__main__":
    main()