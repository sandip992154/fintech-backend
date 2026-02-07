from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from utils.db import get_collection  
from utils.cache import cache_response, cache_search_results, get_cached_search_results
from pymongo.errors import PyMongoError
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
import smtplib, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


router = APIRouter()

DB_NAME = "ecommerce"
COLLECTION_NAME = "ecommerce_data"
COLLECTION_NAME_1 = "contact_messages"

def serialize_doc(doc):
    """Convert MongoDB ObjectId to string."""
    doc["_id"] = str(doc["_id"])
    return doc


@router.get("/products/latest-popular")
@cache_response("latest_popular")
async def get_latest_popular(
    categories: Optional[List[str]] = Query(default=None),
    limit: int = 10
):
    try:
        collection = get_collection(db_name=DB_NAME, collection_name=COLLECTION_NAME)
        pipeline = []

        if categories:
            pipeline.append({"$match": {"category": {"$in": categories}}})

        # Compute highest rating across vendors
        pipeline.append({
            "$addFields": {
                "highest_rating": {
                    "$max": {
                        "$map": {
                            "input": {"$objectToArray": "$vendors"},
                            "as": "v",
                            "in": {"$ifNull": ["$$v.v.rating", 0]}
                        }
                    }
                }
            }
        })

        # Sort by highest_rating descending and limit
        pipeline.append({"$sort": {"highest_rating": -1}})
        pipeline.append({"$limit": limit})

        products_cursor = collection.aggregate(pipeline)
        products = [serialize_doc(p) async for p in products_cursor]
        return {"products": products}

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/products/best-selling")
@cache_response("best_selling")
async def get_best_selling(
    categories: Optional[List[str]] = Query(default=None),
    limit: int = 10
):
    try:
        collection = get_collection(db_name=DB_NAME, collection_name=COLLECTION_NAME)
        pipeline = []

        if categories:
            pipeline.append({"$match": {"category": {"$in": categories}}})

        # Compute highest rating across vendors
        pipeline.append({
            "$addFields": {
                "highest_rating": {
                    "$max": {
                        "$map": {
                            "input": {"$objectToArray": "$vendors"},
                            "as": "v",
                            "in": {"$ifNull": ["$$v.v.rating", 0]}
                        }
                    }
                }
            }
        })

        # Sort by highest_rating descending and limit
        pipeline.append({"$sort": {"highest_rating": -1}})
        pipeline.append({"$limit": limit})

        products_cursor = collection.aggregate(pipeline)
        products = [serialize_doc(p) async for p in products_cursor]
        return {"products": products}

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/products/hot-deals")
async def get_hot_deals(
    categories: Optional[List[str]] = Query(default=None),
    limit: int = 10
):
    try:
        collection = get_collection(db_name=DB_NAME, collection_name=COLLECTION_NAME)
        pipeline = []

        if categories:
            pipeline.append({"$match": {"category": {"$in": categories}}})

        # Compute lowest discount price across vendors
        pipeline.append({
            "$addFields": {
                "lowest_discountprice": {
                    "$min": {
                        "$map": {
                            "input": {"$objectToArray": "$vendors"},
                            "as": "v",
                            "in": {"$ifNull": ["$$v.v.discountprice", None]}
                        }
                    }
                }
            }
        })

        # Filter out products without discount price
        pipeline.append({"$match": {"lowest_discountprice": {"$ne": None}}})

        # Sort by lowest_discountprice ascending and limit
        pipeline.append({"$sort": {"lowest_discountprice": 1}})
        pipeline.append({"$limit": limit})

        products_cursor = collection.aggregate(pipeline)
        products = [serialize_doc(p) async for p in products_cursor]
        return {"products": products}

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/product/{product_id}")
async def get_product_detail(product_id: str):
    try:
        collection = get_collection(db_name=DB_NAME, collection_name=COLLECTION_NAME)
        from bson import ObjectId
        
        # Try to find by ObjectId first, then by string ID
        query = {}
        if ObjectId.is_valid(product_id):
            query = {"$or": [{"_id": ObjectId(product_id)}, {"id": product_id}]}
        else:
            query = {"id": product_id}
            
        product = await collection.find_one(query)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
            
        return serialize_doc(product)
        
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/products/search")
async def search_products(
    query: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    brands: Optional[List[str]] = Query(default=None),
    min_price: Optional[float] = Query(default=None),
    max_price: Optional[float] = Query(default=None),
    sort_by: Optional[str] = Query(default="-1"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100)
):
    try:
        collection = get_collection(db_name=DB_NAME, collection_name=COLLECTION_NAME)
        pipeline = []
        match_conditions = []
        
        # Text search
        if query:
            match_conditions.append({
                "$or": [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"brand": {"$regex": query, "$options": "i"}},
                    {"category": {"$regex": query, "$options": "i"}}
                ]
            })
            
        # Category filter
        if category:
            match_conditions.append({"category": {"$regex": category, "$options": "i"}})
            
        # Brand filter
        if brands:
            match_conditions.append({"brand": {"$in": brands}})
            
        # Add match stage if we have conditions
        if match_conditions:
            pipeline.append({"$match": {"$and": match_conditions}})
            
        # Add price fields for filtering and sorting
        pipeline.append({
            "$addFields": {
                "lowest_price": {
                    "$min": {
                        "$map": {
                            "input": {"$objectToArray": "$vendors"},
                            "as": "v",
                            "in": {"$ifNull": ["$$v.v.price", 999999]}
                        }
                    }
                },
                "lowest_discountprice": {
                    "$min": {
                        "$map": {
                            "input": {"$objectToArray": "$vendors"},
                            "as": "v",
                            "in": {"$ifNull": ["$$v.v.discountprice", "$$v.v.price", 999999]}
                        }
                    }
                }
            }
        })
        
        # Price range filtering
        price_conditions = []
        if min_price is not None:
            price_conditions.append({"lowest_discountprice": {"$gte": min_price}})
        if max_price is not None:
            price_conditions.append({"lowest_discountprice": {"$lte": max_price}})
            
        if price_conditions:
            pipeline.append({"$match": {"$and": price_conditions}})
            
        # Sorting
        sort_stage = {}
        if sort_by == "1":  # Price low to high
            sort_stage = {"$sort": {"lowest_discountprice": 1}}
        elif sort_by == "-1":  # Price high to low
            sort_stage = {"$sort": {"lowest_discountprice": -1}}
        else:  # Default: by relevance/rating
            pipeline.append({
                "$addFields": {
                    "highest_rating": {
                        "$max": {
                            "$map": {
                                "input": {"$objectToArray": "$vendors"},
                                "as": "v",
                                "in": {"$ifNull": ["$$v.v.rating", 0]}
                            }
                        }
                    }
                }
            })
            sort_stage = {"$sort": {"highest_rating": -1}}
            
        pipeline.append(sort_stage)
        
        # Count total for pagination
        count_pipeline = pipeline + [{"$count": "total"}]
        count_result = await collection.aggregate(count_pipeline).to_list(1)
        total = count_result[0]["total"] if count_result else 0
        
        # Pagination
        skip = (page - 1) * limit
        pipeline.extend([
            {"$skip": skip},
            {"$limit": limit}
        ])
        
        products_cursor = collection.aggregate(pipeline)
        products = [serialize_doc(p) async for p in products_cursor]
        
        return {
            "products": products,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
        
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/categories")
async def get_categories():
    try:
        collection = get_collection(db_name=DB_NAME, collection_name=COLLECTION_NAME)
        categories = await collection.distinct("category")
        return {"categories": categories}
        
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/brands")
async def get_brands(category: Optional[str] = Query(default=None)):
    try:
        collection = get_collection(db_name=DB_NAME, collection_name=COLLECTION_NAME)
        pipeline = []
        
        if category:
            pipeline.append({"$match": {"category": {"$regex": category, "$options": "i"}}})
            
        pipeline.append({"$group": {"_id": "$brand"}})
        pipeline.append({"$sort": {"_id": 1}})
        
        brands_cursor = collection.aggregate(pipeline)
        brands = [doc["_id"] async for doc in brands_cursor if doc["_id"]]
        
        return {"brands": brands}
        
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/products/compare")
async def compare_products(product_ids: List[str]):
    try:
        if len(product_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 products required for comparison")
        if len(product_ids) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 products allowed for comparison")
            
        collection = get_collection(db_name=DB_NAME, collection_name=COLLECTION_NAME)
        from bson import ObjectId
        
        # Build query for multiple product IDs
        or_conditions = []
        for pid in product_ids:
            if ObjectId.is_valid(pid):
                or_conditions.extend([
                    {"_id": ObjectId(pid)},
                    {"id": pid}
                ])
            else:
                or_conditions.append({"id": pid})
                
        products_cursor = collection.find({"$or": or_conditions})
        products = [serialize_doc(p) async for p in products_cursor]
        
        if len(products) < 2:
            raise HTTPException(status_code=404, detail="Not enough products found for comparison")
            
        return {"products": products}
        
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
# Pydantic schema
class ContactMessage(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    message: str = Field(..., min_length=1, max_length=1000)

def send_email_notification(contact):
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")
    receiver_email = os.getenv("EMAIL_RECEIVER")
    smtp_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("EMAIL_PORT", 587))

    if not all([sender_email, sender_password, receiver_email]):
        # Skip email if env variables are missing
        print("EMAIL_USER, EMAIL_PASS, or EMAIL_RECEIVER not set. Skipping email.")
        return

    subject = "New Contact Form Submission"
    body = f"""
    You have a new contact form message:

    Name: {contact.name}
    Email: {contact.email}
    Phone: {contact.phone if contact.phone else 'N/A'}
    Message: {contact.message}

    Submitted at: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
    """

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        # Use STARTTLS for port 587
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
    except Exception as e:
        # Log instead of crashing
        print(f"Failed to send email: {str(e)}")


@router.post("/contact-us")
async def submit_contact(message: ContactMessage):
    try:
        collection = get_collection(db_name=DB_NAME, collection_name=COLLECTION_NAME_1)

        # Insert into DB
        doc = message.dict()
        doc["created_at"] = datetime.utcnow()
        result = await collection.insert_one(doc)

        # Send email notification (failure won’t break API)
        send_email_notification(message)

        return {
            "success": True,
            "message": "Your message has been submitted successfully!",
            "id": str(result.inserted_id)
        }

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")