from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import ssl
import json
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

print(ssl.OPENSSL_VERSION)

# MongoDB Atlas connection string from environment
MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://shivams4127:2dtPpPPRYMxFQGoF@cluster0.mklcuw6.mongodb.net/ecommerce_db?retryWrites=true&w=majority")
DB_NAME = os.getenv("DB_NAME", "ecommerce_db")

# Initialize MongoDB async client
try:
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    ecommerce_data = db["ecommerce_data"]
    print(f"✅ Connected to MongoDB: {DB_NAME}")
except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {e}")
    raise
# Function to get a collection
def get_collection(db_name, collection_name):
    db = client[db_name]
    return db[collection_name]

#  Make this function async since it uses await
async def insert_json_to_mongo(json_path, db_name, collection_name):
    """Inserts data from a JSON file into MongoDB if the collection does not exist."""
    db = client[db_name]

    #  Await collection names since it's an async call
    existing_collections = await db.list_collection_names()
    if collection_name in existing_collections:
        print(f"Collection '{collection_name}' already exists in database '{db_name}'. Skipping insertion.")
        return

    collection = db[collection_name]

    # Load JSON data
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Determine structure
    if isinstance(data, dict) and "products" in data:
        docs_to_insert = data["products"]
    elif isinstance(data, list):
        docs_to_insert = data
    else:
        docs_to_insert = [data]

    # Add _id if not present
    for doc in docs_to_insert:
        if "_id" not in doc:
            doc["_id"] = ObjectId()

    #  Await the insertion
    result = await collection.insert_many(docs_to_insert)

    print("Inserted product IDs:")
    for _id in result.inserted_ids:
        print(_id)
