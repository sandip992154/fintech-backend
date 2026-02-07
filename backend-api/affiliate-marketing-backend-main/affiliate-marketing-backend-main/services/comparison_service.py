from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from utils.db import get_collection
from bson import ObjectId
from pymongo.errors import PyMongoError
import json


router = APIRouter()

DB_NAME = "ecommerce"
COLLECTION_NAME = "ecommerce_data"

def serialize_doc(doc):
    """Convert MongoDB ObjectId to string."""
    doc["_id"] = str(doc["_id"])
    return doc


@router.get("/comparison/batch")
async def get_comparison_products(
    product_ids: List[str] = Query(..., description="List of product IDs to compare")
):
    """
    Optimized endpoint to fetch multiple products in a single query for comparison.
    Returns products with all vendor pricing data.
    """
    try:
        collection = get_collection(db_name=DB_NAME, collection_name=COLLECTION_NAME)
        
        # Build query for multiple product IDs
        query_conditions = []
        for product_id in product_ids:
            if ObjectId.is_valid(product_id):
                query_conditions.append({"_id": ObjectId(product_id)})
            query_conditions.append({"id": product_id})
        
        if not query_conditions:
            raise HTTPException(status_code=400, detail="No valid product IDs provided")
        
        # Single aggregation query for all products
        pipeline = [
            {"$match": {"$or": query_conditions}},
            {
                "$addFields": {
                    "vendor_count": {"$size": {"$objectToArray": "$vendors"}},
                    "avg_price": {
                        "$avg": {
                            "$map": {
                                "input": {"$objectToArray": "$vendors"},
                                "as": "vendor",
                                "in": {
                                    "$toDouble": {
                                        "$replaceAll": {
                                            "input": {"$ifNull": ["$$vendor.v.discountprice", "$$vendor.v.price", "0"]},
                                            "find": "₹",
                                            "replacement": ""
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            {"$sort": {"vendor_count": -1, "avg_price": 1}}
        ]
        
        products_cursor = collection.aggregate(pipeline)
        products = [serialize_doc(p) async for p in products_cursor]
        
        if not products:
            raise HTTPException(status_code=404, detail="No products found for comparison")
        
        # Validate that products have vendor data
        valid_products = []
        for product in products:
            if product.get("vendors") and len(product["vendors"]) > 0:
                valid_products.append(product)
        
        return {
            "products": valid_products,
            "total": len(valid_products),
            "comparison_ready": len(valid_products) >= 2
        }
        
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/comparison/suggest")
async def suggest_comparison_products(
    category: Optional[str] = Query(default=None),
    brand: Optional[str] = Query(default=None),
    price_range: Optional[str] = Query(default=None, description="low,medium,high"),
    limit: int = Query(default=4, ge=2, le=8)
):
    """
    Suggest products for comparison based on category, brand, or price range.
    Ensures all suggested products have vendor pricing data.
    """
    try:
        collection = get_collection(db_name=DB_NAME, collection_name=COLLECTION_NAME)
        
        pipeline = []
        match_conditions = []
        
        # Category filter
        if category:
            match_conditions.append({"category": {"$regex": category, "$options": "i"}})
        
        # Brand filter
        if brand:
            match_conditions.append({"brand": {"$regex": brand, "$options": "i"}})
        
        # Ensure products have vendor data
        match_conditions.append({
            "vendors": {"$exists": True, "$ne": {}}
        })
        
        if match_conditions:
            pipeline.append({"$match": {"$and": match_conditions}})
        
        # Add price analysis
        pipeline.extend([
            {
                "$addFields": {
                    "vendor_count": {"$size": {"$objectToArray": "$vendors"}},
                    "min_price": {
                        "$min": {
                            "$map": {
                                "input": {"$objectToArray": "$vendors"},
                                "as": "vendor",
                                "in": {
                                    "$toDouble": {
                                        "$replaceAll": {
                                            "input": {"$ifNull": ["$$vendor.v.discountprice", "$$vendor.v.price", "99999"]},
                                            "find": "₹",
                                            "replacement": ""
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "avg_rating": {
                        "$avg": {
                            "$map": {
                                "input": {"$objectToArray": "$vendors"},
                                "as": "vendor",
                                "in": {"$ifNull": ["$$vendor.v.rating", 0]}
                            }
                        }
                    }
                }
            }
        ])
        
        # Price range filter
        if price_range:
            price_filters = {
                "low": {"min_price": {"$lt": 15000}},
                "medium": {"min_price": {"$gte": 15000, "$lt": 50000}},
                "high": {"min_price": {"$gte": 50000}}
            }
            if price_range in price_filters:
                pipeline.append({"$match": price_filters[price_range]})
        
        # Sort by vendor count and rating
        pipeline.extend([
            {"$match": {"vendor_count": {"$gte": 2}}},  # At least 2 vendors for comparison
            {"$sort": {"vendor_count": -1, "avg_rating": -1}},
            {"$limit": limit}
        ])
        
        products_cursor = collection.aggregate(pipeline)
        products = [serialize_doc(p) async for p in products_cursor]
        
        return {
            "suggested_products": products,
            "total": len(products),
            "criteria": {
                "category": category,
                "brand": brand,
                "price_range": price_range
            }
        }
        
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/comparison/price-analysis/{product_id}")
async def get_price_analysis(product_id: str):
    """
    Get detailed price analysis for a specific product across all vendors.
    """
    try:
        collection = get_collection(db_name=DB_NAME, collection_name=COLLECTION_NAME)
        
        # Build query
        query = {}
        if ObjectId.is_valid(product_id):
            query = {"$or": [{"_id": ObjectId(product_id)}, {"id": product_id}]}
        else:
            query = {"id": product_id}
        
        product = await collection.find_one(query)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        if not product.get("vendors"):
            raise HTTPException(status_code=400, detail="Product has no vendor pricing data")
        
        # Analyze pricing across vendors
        vendor_analysis = {}
        prices = []
        
        for vendor, data in product["vendors"].items():
            price_str = data.get("discountprice") or data.get("price", "0")
            price_num = float(price_str.replace("₹", "").replace(",", "")) if price_str and price_str != "0" else 0
            
            if price_num > 0:
                prices.append(price_num)
                vendor_analysis[vendor] = {
                    "price": price_num,
                    "formatted_price": f"₹{price_num:,.0f}",
                    "rating": data.get("rating", 0),
                    "offers": data.get("offers", []),
                    "affiliate_link": data.get("affiliatelink", "")
                }
        
        if not prices:
            raise HTTPException(status_code=400, detail="No valid pricing data found")
        
        # Calculate price statistics
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        price_diff = max_price - min_price
        savings_percent = (price_diff / max_price * 100) if max_price > 0 else 0
        
        # Find best deals
        best_price_vendor = min(vendor_analysis.items(), key=lambda x: x[1]["price"])
        best_rating_vendor = max(vendor_analysis.items(), key=lambda x: x[1]["rating"])
        
        return {
            "product_id": str(product["_id"]),
            "product_title": product.get("title", ""),
            "vendor_analysis": vendor_analysis,
            "price_statistics": {
                "min_price": f"₹{min_price:,.0f}",
                "max_price": f"₹{max_price:,.0f}",
                "avg_price": f"₹{avg_price:,.0f}",
                "price_difference": f"₹{price_diff:,.0f}",
                "max_savings_percent": round(savings_percent, 1)
            },
            "recommendations": {
                "best_price": {
                    "vendor": best_price_vendor[0],
                    "price": best_price_vendor[1]["formatted_price"],
                    "link": best_price_vendor[1]["affiliate_link"]
                },
                "best_rating": {
                    "vendor": best_rating_vendor[0],
                    "rating": best_rating_vendor[1]["rating"],
                    "link": best_rating_vendor[1]["affiliate_link"]
                }
            }
        }
        
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")