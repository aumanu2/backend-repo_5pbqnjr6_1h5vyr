"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: Optional[str] = Field(None, description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class ProductVariant(BaseModel):
    size: str = Field(..., description="Band/Cup size e.g., 34B")
    color: str = Field(..., description="Color name")
    sku: Optional[str] = Field(None, description="Stock keeping unit")
    stock: int = Field(0, ge=0, description="Units in stock for this variant")

class ProductImage(BaseModel):
    url: str = Field(..., description="Image URL")
    alt: Optional[str] = Field(None, description="Alt text")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in currency units")
    compare_at_price: Optional[float] = Field(None, ge=0, description="Strikethrough price if discounted")
    category: str = Field(..., description="Top-level category e.g., Bras")
    subcategory: Optional[str] = Field(None, description="Subcategory e.g., T-Shirt Bra")
    brand: Optional[str] = Field("Enamor", description="Brand name")
    rating: Optional[float] = Field(4.0, ge=0, le=5)
    rating_count: Optional[int] = Field(0, ge=0)
    tags: Optional[List[str]] = Field(default_factory=list)
    variants: List[ProductVariant] = Field(default_factory=list)
    images: List[ProductImage] = Field(default_factory=list)
    is_active: bool = Field(True)

class CartItem(BaseModel):
    product_id: str
    title: str
    price: float
    quantity: int = Field(1, ge=1)
    variant: Optional[ProductVariant] = None
    image: Optional[str] = None

class Order(BaseModel):
    items: List[CartItem]
    subtotal: float
    discount: float = 0.0
    shipping: float = 0.0
    total: float
    currency: str = "INR"
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    shipping_address: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

# Add your own schemas here:
# --------------------------------------------------

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
