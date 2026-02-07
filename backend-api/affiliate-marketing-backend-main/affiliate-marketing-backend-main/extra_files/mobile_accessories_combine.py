import json
from rapidfuzz import fuzz
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
with open("../mobileaccessories/amazon_mobilesassessories.json", encoding="utf-8") as f:
    amazon_products = json.load(f)
with open("../mobileaccessories/flipkart_mobile_accessories.json", encoding="utf-8") as f:
    flipkart_products = json.load(f)
with open("../mobileaccessories/cromaassories1.json", encoding="utf-8") as f:
    croma_products = json.load(f)
with open("../mobileaccessories/jiomart_mobile_accessories.json", encoding="utf-8") as f:
    jiomart_products = json.load(f)
with open("../mobileaccessories/vijaysales_mobile_accessories.json", encoding="utf-8") as f:
    vijay_products = json.load(f)

all_vendors = {
    "Flipkart": flipkart_products,
    "Croma": croma_products,
    "JioMart": jiomart_products,
    "VijaySales": vijay_products
}

combined_data = {"products": []}

# ✅ Improved keyword extractor for accessories
def extract_model_keywords(title):
    title = title.lower()
    title = re.sub(r"[^\w\s\-+]", " ", title)
    title = re.sub(r"\s+", " ", title).strip()

    keywords = []

    accessory_types = [
        "power bank", "powerbank", "charger", "charging", "adapter",
        "earphones", "headphones", "earbuds", "buds", "neckband",
        "wired", "wireless", "bluetooth", "tws", "type-c", "usb"
    ]
    for acc in accessory_types:
        if acc in title:
            keywords.append(acc)

    words = title.split()
    if words:
        keywords.append(words[0])

    model_matches = re.findall(r"\b(?:[a-zA-Z]{2,10}-?\d{2,6}[a-zA-Z+]*|[a-zA-Z]+\d+[a-zA-Z+]*)\b", title)
    keywords.extend(model_matches)
    print(keywords)

    seen = set()
    return [k for k in keywords if not (k in seen or seen.add(k))]

# ✅ Matching logic
def match_product(base_product, vendor_products):
    base_title = base_product.get("title", "")
    base_keywords = extract_model_keywords(base_title)
    base_features = base_product.get("features", {})
    print(">>>>>>>>>>>>>>>>",base_features)

    candidates = []
    for p in vendor_products:
        vendor_title = p.get("title", "")
        title_score = fuzz.partial_ratio(base_title, vendor_title)

        keyword_boost = sum(15 for kw in base_keywords if kw.lower() in vendor_title.lower())

        if " ".join(base_title.lower().split()[:3]) in vendor_title.lower():
            keyword_boost += 10

        feature_score = 0
        for key in ["Model", "Type", "Output", "Capacity","mAh", "Connector", "Battery", "Power", "Color", "Compatibility"]:

            if key in base_features and key in p.get("features", {}):
                 if str(base_features[key]).lower() == str(p["features"][key]).lower(): 
                    feature_score += 25
                
        total_score = title_score + keyword_boost + feature_score
        candidates.append((p, total_score))

    candidates.sort(key=lambda x: x[1], reverse=True)
    if candidates and candidates[0][1] > 60:
        return candidates[0][0]
    return None

# ✅ Combine matched products
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
                "affiliatelink": a_product.get("affiliatelink", ""),
                "offers": a_product.get("offers", []),
            }
        },
        "features": a_product.get("features", {}),
        "image": a_product.get("image_url", "")
    }

    for vendor_name, vendor_products in all_vendors.items():
        matched = match_product(a_product, vendor_products)
        if matched:
            # print(f"✔ Matched: {a_product['title']} → {matched['title']}")
            product_entry["vendors"][vendor_name] = {
                "price": safe_float(matched.get("price")),
                "discountPrice": safe_float(matched.get("discounted_price")),
                "rating": safe_float(matched.get("rating")),
                "affiliateLink": matched.get("affiliatelink", ""),
                "offers": matched.get("offers", []),
            }

    combined_data["products"].append(product_entry)

# ✅ Save to file
with open("combined_products.json", "w", encoding="utf-8") as f:
    json.dump(combined_data, f, indent=2, ensure_ascii=False)

print("✅ Combined data saved to combined_products.json")
