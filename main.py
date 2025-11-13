import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Order

app = FastAPI(title="Lingerie Store API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class FilterRequest(BaseModel):
    category: Optional[str] = None
    subcategory: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    colors: Optional[List[str]] = None
    sizes: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    sort: Optional[str] = None  # 'price_asc', 'price_desc', 'rating'
    search: Optional[str] = None
    page: int = 1
    limit: int = 24


@app.get("/")
def read_root():
    return {"message": "Lingerie Store Backend Running"}


@app.get("/schema")
def get_schema():
    return {"collections": ["user", "product", "order"]}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


@app.post("/api/products/seed")
def seed_products(products: List[Product]):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    inserted_ids = []
    for prod in products:
        inserted_id = create_document("product", prod)
        inserted_ids.append(inserted_id)
    return {"inserted": len(inserted_ids), "ids": inserted_ids}


@app.post("/api/products/search")
def search_products(filters: FilterRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    query: Dict[str, Any] = {"is_active": True}

    if filters.category:
        query["category"] = filters.category
    if filters.subcategory:
        query["subcategory"] = filters.subcategory
    if filters.colors:
        query["variants.color"] = {"$in": filters.colors}
    if filters.sizes:
        query["variants.size"] = {"$in": filters.sizes}
    if filters.tags:
        query["tags"] = {"$in": filters.tags}
    if filters.search:
        query["$or"] = [
            {"title": {"$regex": filters.search, "$options": "i"}},
            {"description": {"$regex": filters.search, "$options": "i"}},
        ]

    price_filter = {}
    if filters.price_min is not None:
        price_filter["$gte"] = filters.price_min
    if filters.price_max is not None:
        price_filter["$lte"] = filters.price_max
    if price_filter:
        query["price"] = price_filter

    sort_spec = None
    if filters.sort == "price_asc":
        sort_spec = [("price", 1)]
    elif filters.sort == "price_desc":
        sort_spec = [("price", -1)]
    elif filters.sort == "rating":
        sort_spec = [("rating", -1)]

    collection = db["product"]
    skip = max(0, (filters.page - 1) * filters.limit)

    total = collection.count_documents(query)
    cursor = collection.find(query)
    if sort_spec:
        cursor = cursor.sort(sort_spec)
    items = list(cursor.skip(skip).limit(filters.limit))

    for item in items:
        item["_id"] = str(item["_id"])  # make JSON serializable

    # Build facet info for filters
    color_counts = collection.aggregate([
        {"$match": query},
        {"$unwind": "$variants"},
        {"$group": {"_id": "$variants.color", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ])
    size_counts = collection.aggregate([
        {"$match": query},
        {"$unwind": "$variants"},
        {"$group": {"_id": "$variants.size", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ])

    return {
        "total": total,
        "page": filters.page,
        "limit": filters.limit,
        "items": items,
        "facets": {
            "colors": [{"value": c["_id"], "count": c["count"]} for c in color_counts if c.get("_id")],
            "sizes": [{"value": s["_id"], "count": s["count"]} for s in size_counts if s.get("_id")],
        }
    }


@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        obj_id = ObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product id")

    doc = db["product"].find_one({"_id": obj_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    doc["_id"] = str(doc["_id"])
    return doc


@app.post("/api/orders")
def create_order(order: Order):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    order_id = create_document("order", order)
    return {"order_id": order_id}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
