#!/usr/bin/env python3
"""
Simple CRUD REST API service for testing translation capabilities.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager

# Database setup
DATABASE_URL = "sqlite:///./test.db"

class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price: float
    category: str

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None

# In-memory storage for simplicity
items_db = []
next_id = 1

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting CRUD service...")
    # Initialize empty database
    global items_db, next_id
    items_db = []
    next_id = 1
    yield
    # Shutdown
    print("Shutting down CRUD service...")

app = FastAPI(
    title="Test CRUD Service",
    description="A simple CRUD REST API for translation testing",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "message": "Test CRUD Service is running",
        "version": "1.0.0",
        "endpoints": {
            "items": "/items",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "crud-api"}

@app.get("/items", response_model=List[Item])
async def get_all_items():
    """Get all items."""
    return items_db

@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    """Get a specific item by ID."""
    for item in items_db:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.post("/items", response_model=Item)
async def create_item(item: Item):
    """Create a new item."""
    global next_id
    new_item = {
        "id": next_id,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "category": item.category
    }
    items_db.append(new_item)
    next_id += 1
    return new_item

@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item_update: ItemUpdate):
    """Update an existing item."""
    for i, item in enumerate(items_db):
        if item["id"] == item_id:
            # Update only provided fields
            if item_update.name is not None:
                item["name"] = item_update.name
            if item_update.description is not None:
                item["description"] = item_update.description
            if item_update.price is not None:
                item["price"] = item_update.price
            if item_update.category is not None:
                item["category"] = item_update.category
            
            items_db[i] = item
            return item
    
    raise HTTPException(status_code=404, detail="Item not found")

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """Delete an item."""
    for i, item in enumerate(items_db):
        if item["id"] == item_id:
            deleted_item = items_db.pop(i)
            return {"message": f"Item {item_id} deleted successfully", "deleted_item": deleted_item}
    
    raise HTTPException(status_code=404, detail="Item not found")

@app.get("/items/category/{category}")
async def get_items_by_category(category: str):
    """Get items by category."""
    filtered_items = [item for item in items_db if item["category"].lower() == category.lower()]
    return filtered_items

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
