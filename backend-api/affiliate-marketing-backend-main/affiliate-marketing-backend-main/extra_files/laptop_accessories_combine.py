import json
import re
import uuid
from rapidfuzz import fuzz

def safe_float(value):
    if not value or value == "N/A":
        return None
    try:
        return float(re.sub(r"[^\d.]", "", str(value)))
    except ValueError:
        return None

def clean_text(text):
    return re.sub(r"[\u200e\u200f\u202a\u202b\u202c\u202d\u202e]", "", str(text)).strip()

def extract_model_keywords(title):
    title = clean_text(title).lower()
    title = re.sub(r"[^\w\s\-+]", " ", title)
    title = re.sub(r"\s+", " ", title).strip()

    keywords = []
    keywords.extend([
        word for word in [
            "mouse", "wireless", "wired", "usb", "optical", "dpi", "bluetooth", 
            "gaming", "receiver", "nano", "scroll", "plug", "play", "button", 
            "sensor", "battery", "ergonomic", "rechargeable"
        ] if word in title
    ])

    words = title.split()
    if words:
        keywords.append(words[0])

    model_matches = re.findall(r"\b(?:[a-zA-Z]{2,10}-?\d{2,6}[a-zA-Z+]*|[a-zA-Z]+\d+[a-zA-Z+]*)\b", title)
    keywords.extend(model_matches)

    seen = set()
    return [k for k in keywords if not (k in seen or seen.add(k))]

def match_product(base_product, vendor_products):
    base_title = clean_text(base_product.get("title", ""))
    base_keywords = extract_model_keywords(base_title)
    base_features = base_product.get("features", {}).get("details", {}).get("general", {})

    candidates = []
    for p in vendor_products:
        vendor_title = clean_text(p.get("title", ""))
        title_score = fuzz.partial_ratio(base_title, vendor_title)

        keyword_boost = sum(15 for kw in base_keywords if kw in vendor_title.lower())
        if " ".join(base_title.split()[:3]) in vendor_title.lower():
            keyword_boost += 10

        feature_score = 0
        vendor_features = p.get("features", {}).get("details", {}).get("general", {})
        for key in ["model_no", "connectivity", "description"]:
            if base_features.get(key) and vendor_features.get(key):
                if str(base_features[key]).lower() == str(vendor_features[key]).lower():
                    feature_score += 25

        total_score = title_score + keyword_boost + feature_score
        candidates.append((p, total_score))

    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0] if candidates and candidates[0][1] > 60 else None

# Load all vendor data
with open("../laptopaccessories/amazon_laptopaccess.json", encoding="utf-8") as f:
    amazon_products = json.load(f)

with open("../laptopaccessories/flipkart_laptop_accessories.json", encoding="utf-8") as f:
    flipkart_products = json.load(f)

with open("../laptopaccessories/cromalaptopsaccessories.json", encoding="utf-8") as f:
    croma_products = json.load(f)

with open("../laptopaccessories/jiomart_laptop_accessories.json", encoding="utf-8") as f:
    jiomart_products = json.load(f)

with open("../laptopaccessories/vijaysaleslaptopaccessories.json", encoding="utf-8") as f:
    vijay_products = json.load(f)

all_vendors = {
    "Flipkart": flipkart_products,
    "Croma": croma_products,
    "JioMart": jiomart_products,
    "VijaySales": vijay_products
}

combined_data = {"products": []}

# Combine all matches
for a_product in amazon_products:
    product_entry = {
        "id": str(uuid.uuid4()),
        "title": clean_text(a_product.get("title", "")),
        "brand": clean_text(a_product.get("brand", "N/A")),
        "category": a_product.get("category", "laptop accessories"),
        "comment": "",
        "vendors": {
            "Amazon": {
                "price": safe_float(a_product.get("price")),
                "discountprice": safe_float(a_product.get("discounted_price")),
                "rating": safe_float(a_product.get("rating")),
                "affiliatelink": a_product.get("affiliatelink", ""),
                "offers": [clean_text(o) for o in a_product.get("offers", [])],
            }
        },
        "features": a_product.get("features", {}),
        "image": a_product.get("image_url", {})
    }

    for vendor_name, vendor_products in all_vendors.items():
        matched = match_product(a_product, vendor_products)
        if matched:
            product_entry["vendors"][vendor_name] = {
                "price": safe_float(matched.get("price")),
                "discountprice": safe_float(matched.get("discounted_price")),
                "rating": safe_float(matched.get("rating")),
                "affiliatelink": matched.get("affiliatelink", ""),
                "offers": [clean_text(o) for o in matched.get("offers", [])],
            }

    combined_data["products"].append(product_entry)

# Save to JSON
with open("combined_laptop_accessories.json", "w", encoding="utf-8") as f:
    json.dump(combined_data, f, indent=2, ensure_ascii=False)

print("✅ Combined laptop accessories saved to 'combined_laptop_accessories.json'")
