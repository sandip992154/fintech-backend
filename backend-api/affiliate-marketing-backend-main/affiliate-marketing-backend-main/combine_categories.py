import os, json, re, uuid, time, hashlib, threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ---------- Config ----------
CATEGORY_DIRS = {
    'laptop': './core/database/laptop',
    'mobiles': './core/database/mobiles',
    'laptop accessories': './core/database/laptopaccessories',
    'mobile accessories': './core/database/mobileaccessories'
}
VENDORS = ['amazon', 'flipkart', 'croma', 'vijaysales', 'jiomart']
FEATURE_SOURCE = {
    'laptop': 'flipkart.json',
    'mobiles': 'amazon.json',
    'laptop accessories': 'amazon.json',
    'mobile accessories': 'amazon.json'
}
FINAL_FILE = './core/database/final.json'

# ---------- Cache ----------
file_hash_cache = {}
product_cache = {}

# ---------- Helpers ----------
def clean_text(t):
    return re.sub(r"[\u200e\u200f\u202a-\u202e]", "", str(t)).strip().lower()

def file_md5(path):
    try:
        return hashlib.md5(open(path,'rb').read()).hexdigest() if os.path.exists(path) else None
    except Exception:
        return None

def load_products(path):
    if not os.path.exists(path):
        return []
    if path in product_cache:
        return product_cache[path]
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return []
    if isinstance(data, list):
        products = data
    elif isinstance(data, dict):
        products = data.get("products", [])
    else:
        products = []
    product_cache[path] = products
    return products

# ---------- Extractors ----------
_model_re = re.compile(r"\b([A-Z0-9]{4,}(?:[-/][A-Z0-9]{2,})?)\b", re.IGNORECASE)
_ram_re = re.compile(r'(\d+)\s*gb\s*ram', re.IGNORECASE)
_storage_re = re.compile(r'(\d+)\s*gb\s*(ssd|emmc|hdd|storage)?', re.IGNORECASE)

def extract_model_number(title):
    if not title: return None
    matches = _model_re.findall(title.upper())
    blocked = {"INTEL","WINDOWS","APPLE","CHROME","EMMC","SSD","RAM","DDR","CORE","GEN","OFFICE","HOME"}
    for m in matches:
        token = m.upper()
        if token in blocked: 
            continue
        if token.isdigit(): 
            continue
        if len(token) >= 4:
            return token.lower()
    return None

def extract_ram_storage(title):
    t = title or ""
    ram_m = _ram_re.search(t)
    stor_m = _storage_re.search(t)
    ram = ram_m.group(1) if ram_m else None
    storage = stor_m.group(1) if stor_m else None
    return ram, storage

def normalize_short_title(title, brand):
    t = clean_text(title or "")
    if brand:
        t = re.sub(re.escape(brand.lower()), " ", t)
    t = re.sub(r'\b(windows|home|laptop|notebook|chromebook|macbook|intel|amd|apple|core|processor|display|retina|ms office|os|graphics|iris|geforce)\b', ' ', t)
    t = re.sub(r'\b\d+(\.\d+)?\s*(gb|tb|cm|inch|inches|kg|nits)\b', ' ', t)
    t = re.sub(r'\b\d{3,4}x\d{3,4}\b', ' ', t)
    t = re.sub(r'\b[0-9]{2,}[a-z0-9]{2,}\b', ' ', t)
    t = re.sub(r'[^a-z0-9 ]+', ' ', t)
    parts = [w for w in t.split() if len(w) > 1]
    return " ".join(parts[:6])

# ---------- Core Combine ----------
def combine_category(category, dir_path):
    vendor_data = {}
    for vendor in VENDORS:
        vfile = os.path.join(dir_path, f"{vendor}.json")
        plist = load_products(vfile)
        for p in plist:
            title = p.get("title","") or ""
            brand = str(p.get("brand","") or "").strip()
            p["_brand_lower"] = clean_text(brand)
            p["_clean_title"] = clean_text(title)
            p["_model"] = extract_model_number(title)
            p["_ram"], p["_storage"] = extract_ram_storage(title)
            p["_short"] = normalize_short_title(title, brand)
        vendor_data[vendor] = plist

    constant_features, constant_images = {}, {}
    const_file = FEATURE_SOURCE.get(category)
    if const_file:
        const_path = os.path.join(dir_path, const_file)
        for p in load_products(const_path):
            key = p.get("_model") or clean_text(p.get("title",""))
            if key:
                constant_features[key] = p.get("features")
                imgs = p.get("image_url") or []
                if imgs:
                    if isinstance(imgs, dict) and "thumbnail" in imgs and "urls" in imgs:
                        constant_images[key] = imgs
                    elif isinstance(imgs, list) and len(imgs) > 0:
                        constant_images[key] = {
                            "thumbnail": imgs[0],
                            "urls": imgs
                        }

    base_vendor = VENDORS[0]
    base_list = vendor_data.get(base_vendor, [])
    common = []

    vendor_brand_map = {}
    for v in VENDORS:
        vendor_brand_map[v] = {}
        for p in vendor_data.get(v, []):
            vendor_brand_map[v].setdefault(p["_brand_lower"], []).append(p)

    for base in base_list:
        brand = base["_brand_lower"]
        if not brand:
            continue
        others_by_brand = {v: vendor_brand_map[v].get(brand, []) for v in VENDORS if v != base_vendor}

        # Stage 1: model number match
        matched_group = {base_vendor: base}
        model = base.get("_model")
        ok = False
        if model:
            ok = True
            for v, lst in others_by_brand.items():
                found = next((x for x in lst if x.get("_model") == model), None)
                if found:
                    matched_group[v] = found
                else:
                    ok = False
                    break

        # Stage 2: fallback exact short-title + RAM + storage
        if not ok:
            matched_group = {base_vendor: base}
            base_short = base.get("_short") or ""
            base_ram = base.get("_ram")
            base_storage = base.get("_storage")
            all_found = True
            for v, lst in others_by_brand.items():
                found_item = None
                for x in lst:
                    x_short = x.get("_short") or ""
                    x_ram = x.get("_ram")
                    x_storage = x.get("_storage")
                    if x_short == base_short and x_ram == base_ram and x_storage == base_storage:
                        found_item = x
                        break
                if found_item:
                    matched_group[v] = found_item
                else:
                    all_found = False
                    break
            ok = all_found

        if ok and len(matched_group) == len(VENDORS):
            # Use model number as a primary key for feature/image lookup, fall back to cleaned title
            lookup_key = base.get("_model") or clean_text(base.get("title", ""))
            
            # Fetch features and images
            features = constant_features.get(lookup_key)
            image_url = constant_images.get(lookup_key)

            vendors_info = {}
            for vname, pdata in matched_group.items():
                discount = pdata.get("discounted_price") or pdata.get("discountprice") or pdata.get("discount_price")
                vendors_info[vname] = {
                    "price": pdata.get("price"),
                    "discountprice": discount,
                    "rating": pdata.get("rating"),
                    "affiliatelink": pdata.get("affiliatelink"),
                    "offers": pdata.get("offers", [])
                }
            
            combined_product = {
                "id": str(uuid.uuid4()),
                "title": base.get("title"),
                "brand": base.get("brand"),
                "category": category,
                "vendors": vendors_info,
                "features": features,
                "image": image_url
            }
            common.append(combined_product)

    out_path = os.path.join(dir_path, '_combined.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({"products": common}, f, ensure_ascii=False, indent=2)
    print(f"✔ {category}: {len(common)} common")
    return common

def combine_final():
    allp = []
    for cat, path in CATEGORY_DIRS.items():
        allp.extend(combine_category(cat, path))
    with open(FINAL_FILE, 'w', encoding='utf-8') as f:
        json.dump({"products": allp}, f, ensure_ascii=False, indent=2)

# ---------- Watchdog ----------
class Handler(FileSystemEventHandler):
    def __init__(self):
        self.last_run = 0

    def on_modified(self, e):
        if e.is_directory or not e.src_path.endswith('.json'):
            return
        if e.src_path in product_cache:
            del product_cache[e.src_path]
        h = file_md5(e.src_path)
        if file_hash_cache.get(e.src_path) == h:
            return
        file_hash_cache[e.src_path] = h

        changed_cat = None
        for cat, path in CATEGORY_DIRS.items():
            if os.path.commonpath([os.path.abspath(e.src_path), os.path.abspath(path)]) == os.path.abspath(path):
                changed_cat = cat
                break
        if not changed_cat:
            return

        now = time.time()
        if now - self.last_run < 1.5:
            return
        self.last_run = now

        def run():
            print(f"🔁 Change detected in {changed_cat} → Recombining only that category...")
            combine_category(changed_cat, CATEGORY_DIRS[changed_cat])
            combine_final()
        threading.Thread(target=run, daemon=True).start()

# ---------- Entry ----------
if __name__ == "__main__":
    print("🔁 Running initial combine...")
    combine_final()
    print("Watching for changes...")
    obs = Observer()
    h = Handler()
    for p in CATEGORY_DIRS.values():
        if os.path.exists(p):
            obs.schedule(h, p, recursive=False)
    obs.start()
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        obs.stop()
    obs.join()