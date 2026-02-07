import json
from constant import *

# def load_json():
#     with open(MOBILE_DATA_FILE, 'r', encoding='utf-8') as f:
#         return json.load(f)
# def load_laptops_json():
#     with open(LAPTOP_DATA_FILE, 'r', encoding='utf-8') as f:
#         return json.load(f)
def load_all_data_json():
    with open(ALL_DATA_FILE, 'r', encoding='utf-8') as f:
        data=json.load(f) 
        return data["products"]
# def load_accessories_json():
#     with open(ACCESSORIES_DATA_FILE, 'r', encoding='utf-8') as f:
#         return json.load(f)          