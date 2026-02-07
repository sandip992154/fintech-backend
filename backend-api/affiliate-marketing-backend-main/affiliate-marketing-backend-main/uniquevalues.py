import json
import os

#  Path to the JSON file relative to where you're running this script
json_file_path = os.path.join("database", "laptop.json")

#  Load the JSON data
try:
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"File not found: {json_file_path}")
    exit()
except json.JSONDecodeError:
    print(f"Invalid JSON format in file: {json_file_path}")
    exit()

# Dictionary to hold sets of unique values
unique_fields = {
    "brand": set(),
    "category": set(),
    "model_name": set(),
    "screen_size": set(),
    "colour": set(),
    "hard_disk_size": set(),
    "cpu_model": set(),
    "ram_memory_installed_size": set(),
    "operating_system": set(),
    "special_feature": set(),
    "graphics_card_description": set(),
}

# Process each product in the JSON file
for product in data:
    specs = product.get("specifications", {})
    
    # Top-level fields
    brand = product.get("brand")
    category = product.get("category")
    
    if brand:
        unique_fields["brand"].add(brand.strip())
    if category:
        unique_fields["category"].add(category.strip())
    
    # Nested fields from 'specifications'
    for field in [
        "model_name", "screen_size", "colour", "hard_disk_size",
        "cpu_model", "ram_memory_installed_size", "operating_system",
        "special_feature", "graphics_card_description"
    ]:
        value = specs.get(field)
        if value:
            unique_fields[field].add(value.strip())

# Print the results
for field_name, values in unique_fields.items():
    print(f"\nUnique {field_name.replace('_', ' ').title()} options:")
    for v in sorted(values):
        print(f"  - {v}")
