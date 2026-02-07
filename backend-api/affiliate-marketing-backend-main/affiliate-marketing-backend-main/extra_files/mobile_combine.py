import json
from rapidfuzz import process, fuzz
import uuid
import re

def safe_float(value):
    if not value or value == "N/A":
        return None
    try:
        return float(re.sub(r"[^\d.]", "", str(value)))
    except ValueError:
        return None

# Load JSON files
with open("amazon_mobiles1.json", encoding="utf-8") as f:
    amazon_products = json.load(f)
with open("flipkart_mobile.json", encoding="utf-8") as f:
    flipkart_products = json.load(f)
with open("cromamobiles1.json", encoding="utf-8") as f:
    croma_products = json.load(f)
with open("jiomart_mobile.json", encoding="utf-8") as f:
    jiomart_products = json.load(f)
with open("vijaysales_mobile.json", encoding="utf-8") as f:
    vijay_products = json.load(f)

all_vendors = {
    "Flipkart": flipkart_products,
    "Croma": croma_products,
    "JioMart": jiomart_products,
    "VijaySales": vijay_products
}

combined_data = {"products": []}

# Extract model/variant from title
def extract_model_keywords(title):
    return re.findall(r"[A-Za-z]+\s?\d{1,3}[A-Za-z]*", title)

def match_product(base_product, vendor_products):
    base_title = base_product.get("title", "")
    base_keywords = extract_model_keywords(base_title)
    base_features = base_product.get("features", {})

    candidates = []
    for p in vendor_products:
        vendor_title = p.get("title", "")
        title_score = fuzz.partial_ratio(base_title, vendor_title)

        # Boost score if any model keyword exists in vendor title
        keyword_boost = 0
        for kw in base_keywords:
            if kw.lower() in vendor_title.lower():
                keyword_boost += 15

        feature_score = 0
        for key in ["RAM", "ROM", "Model", "Storage"]:
            if key in base_features and key in p.get("features", {}):
                if base_features[key] == p["features"][key]:
                    feature_score += 25

        total_score = title_score + keyword_boost + feature_score
        candidates.append((p, total_score))

    candidates.sort(key=lambda x: x[1], reverse=True)
    if candidates and candidates[0][1] > 60:  # You can increase or decrease threshold
        return candidates[0][0]
    return None

for a_product in amazon_products:
    product_entry = {
        "id": str(uuid.uuid4()),
        "title": a_product["title"],
        "brand": a_product.get("brand", "N/A"),
        "category": a_product.get("category"),
        "comment": "",
        "vendors": {
            "Amazon": {
                "price": safe_float(a_product.get("price")),
                "discountPrice": safe_float(a_product.get("discounted_price")),
                "rating": safe_float(a_product.get("rating")),
                "affiliateLink": a_product.get("affiliatelink", ""),
                "offers": a_product.get("offers", []),
                
            }
        },
        "features": a_product.get("features", {}),
        "image": a_product.get("image_url", "")
    }

    for vendor_name, vendor_products in all_vendors.items():
        matched = match_product(a_product, vendor_products)
        if matched:
            product_entry["vendors"][vendor_name] = {
                "price": safe_float(matched.get("price")),
                "discountPrice": safe_float(matched.get("discounted_price")),
                "rating": safe_float(matched.get("rating")),
                "affiliateLink": matched.get("affiliatelink", ""),
                "offers": matched.get("offers", [])
                
            }

    combined_data["products"].append(product_entry)

with open("combined_products.json", "w", encoding="utf-8") as f:
    json.dump(combined_data, f, indent=2, ensure_ascii=False)
