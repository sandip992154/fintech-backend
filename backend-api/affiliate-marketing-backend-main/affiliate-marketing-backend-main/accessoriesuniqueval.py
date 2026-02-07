from fastapi import APIRouter
import json
import os

app = APIRouter()

# Path to the accessories.json file
DATA_PATH = os.path.join(os.path.dirname(__file__), "database/accessories.json")

@app.get("/accessories")
def get_dynamic_filters():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Initialize filter sets
    accessory_types = set()
    connectivity_options = set()
    feature_keywords = set()
    compatibility_keywords = set()

    # Define keyword patterns
    type_keywords = ["mouse", "keyboard", "hard drive", "docking", "stand", "webcam"]
    connectivity_keywords = ["usb", "bluetooth", "2.4ghz", "wired", "wireless"]
    feature_keywords_list = ["ergonomic", "gaming", "portable", "adjustable", "silent", "ambidextrous", "performance"]
    compatibility_list = ["windows", "mac", "universal"]

    # Parse products
    for item in data:
        title = item.get("title", "").lower()

        for keyword in type_keywords:
            if keyword in title:
                accessory_types.add(keyword.title())

        for conn in connectivity_keywords:
            if conn in title:
                if conn == "2.4ghz":
                    connectivity_options.add("Wireless (2.4GHz)")
                else:
                    connectivity_options.add(conn.title())

        for feat in feature_keywords_list:
            if feat in title:
                feature_keywords.add(feat.title())

        for comp in compatibility_list:
            if comp in title:
                compatibility_keywords.add(comp.title() + " Compatible")

    return {
        "Laptop Accessories": {
            "accessoryType": sorted(list(accessory_types)),
            "connectivity": sorted(list(connectivity_options)),
            "compatibility": sorted(list(compatibility_keywords)),
            "features": sorted(list(feature_keywords)),
            "material": []  # No material info in file
        }
    }
