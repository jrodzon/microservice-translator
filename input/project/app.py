#!/usr/bin/env python3
"""
Simple CRUD REST API service for testing translation capabilities.
"""

from fastapi import FastAPI, HTTPException, Response, Request
from pydantic import BaseModel, ValidationError
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
import json

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

# Explicit validation functions for return codes
def validate_item_data(data: Dict[str, Any]) -> tuple[bool, str]:
    """Validate item data and return (is_valid, error_message)."""
    if not data.get("name"):
        return False, "name field is required"
    if "price" not in data:
        return False, "price field is required"
    if not data.get("category"):
        return False, "category field is required"
    return True, ""

def create_validation_error_response(message: str) -> HTTPException:
    """Create a 422 validation error response."""
    return HTTPException(
        status_code=422, 
        detail={"error": "Validation Error", "message": message}
    )

def create_not_found_error_response() -> HTTPException:
    """Create a 404 not found error response."""
    return HTTPException(
        status_code=404, 
        detail={"error": "Not Found", "message": "Item not found"}
    )

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

@app.get("/items")
async def get_all_items():
    """Get all items."""
    return items_db

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """Get a specific item by ID."""
    for item in items_db:
        if item["id"] == item_id:
            return item
    raise create_not_found_error_response()

@app.post("/items")
async def create_item(request: Request):
    """Create a new item."""
    try:
        # Parse JSON body manually to handle validation explicitly
        body = await request.json()
        
        # Explicit validation
        is_valid, error_message = validate_item_data(body)
        if not is_valid:
            raise create_validation_error_response(error_message)
        
        # Create item with explicit success response
        global next_id
        new_item = {
            "id": next_id,
            "name": body["name"],
            "description": body.get("description"),
            "price": body["price"],
            "category": body["category"]
        }
        items_db.append(new_item)
        next_id += 1
        return new_item
        
    except json.JSONDecodeError:
        raise create_validation_error_response("Invalid JSON format")
    except Exception as e:
        raise create_validation_error_response(f"Unexpected error: {str(e)}")

@app.put("/items/{item_id}")
async def update_item(item_id: int, request: Request):
    """Update an existing item."""
    try:
        # Parse JSON body manually
        body = await request.json()
    except json.JSONDecodeError:
        raise create_validation_error_response("Invalid JSON format")
    except Exception as e:
        raise create_validation_error_response(f"Unexpected error: {str(e)}")
    
    # Check if item exists
    for i, item in enumerate(items_db):
        if item["id"] == item_id:
            # Update only provided fields
            if "name" in body:
                item["name"] = body["name"]
            if "description" in body:
                item["description"] = body["description"]
            if "price" in body:
                item["price"] = body["price"]
            if "category" in body:
                item["category"] = body["category"]
            
            items_db[i] = item
            return item
    
    # Item not found - return 404
    raise create_not_found_error_response()

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """Delete an item."""
    for i, item in enumerate(items_db):
        if item["id"] == item_id:
            deleted_item = items_db.pop(i)
            response_data = {
                "message": f"Item {item_id} deleted successfully", 
                "deleted_item": deleted_item
            }
            return response_data
    
    raise create_not_found_error_response()

@app.get("/items/category/{category}")
async def get_items_by_category(category: str):
    """Get items by category."""
    filtered_items = [item for item in items_db if item["category"].lower() == category.lower()]
    return filtered_items

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
