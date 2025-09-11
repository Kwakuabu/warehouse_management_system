# app/routes/products.py
from fastapi import APIRouter, Depends, Request, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.models import Product, Category, User, Vendor
from app.utils.auth import get_current_active_user_from_cookie, check_user_role_from_cookie
from typing import List, Optional
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Product list page - All authenticated users can view
@router.get("/", response_class=HTMLResponse)
async def list_products(
    request: Request,
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Display list of all products"""
    products = db.query(Product).filter(Product.is_active == True).order_by(desc(Product.created_at)).all()
    categories = db.query(Category).order_by(Category.name).all()
    
    return templates.TemplateResponse("products/list.html", {
        "request": request,
        "products": products,
        "categories": categories,
        "current_user": current_user,
        "user_role": current_user.role,
        "pagination": {"pages": 1, "page": 1, "has_prev": False, "has_next": False}  # Simple pagination placeholder
    })

# Add product page - Admin and Manager only
@router.get("/add", response_class=HTMLResponse)
async def add_product_page(
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Display add product form"""
    categories = db.query(Category).all()
    vendors = db.query(Vendor).all()
    return templates.TemplateResponse("products/add.html", {
        "request": request,
        "categories": categories,
        "vendors": vendors,
        "current_user": current_user
    })

# Add product form submission - Admin and Manager only
@router.post("/add")
async def add_product(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    sku: str = Form(...),
    category_id: int = Form(...),
    vendor_id: int = Form(None),  # Make vendor_id optional
    unit_price: float = Form(...),
    cost_price: float = Form(...),
    reorder_point: int = Form(...),
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Handle add product form submission"""
    # Check if SKU already exists
    existing_product = db.query(Product).filter(Product.sku == sku).first()
    if existing_product:
        categories = db.query(Category).all()
        vendors = db.query(Vendor).all()
        return templates.TemplateResponse("products/add.html", {
            "request": request,
            "categories": categories,
            "vendors": vendors,
            "error": "SKU already exists",
            "current_user": current_user
        })
    
    # Create new product
    product = Product(
        name=name,
        description=description,
        sku=sku,
        category_id=category_id,
        vendor_id=vendor_id,  # Include vendor_id (can be None)
        unit_price=unit_price,
        cost_price=cost_price,
        reorder_point=reorder_point
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    
    return RedirectResponse(url="/products", status_code=302)

# Product detail page - All authenticated users can view
@router.get("/{product_id}", response_class=HTMLResponse)
async def product_detail(
    request: Request,
    product_id: int,
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Display product details"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return templates.TemplateResponse("products/detail.html", {
        "request": request,
        "product": product,
        "current_user": current_user
    })

# Edit product page - Admin and Manager only
@router.get("/{product_id}/edit", response_class=HTMLResponse)
async def edit_product_page(
    request: Request,
    product_id: int,
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Display edit product form"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    categories = db.query(Category).all()
    vendors = db.query(Vendor).all()
    return templates.TemplateResponse("products/edit.html", {
        "request": request,
        "product": product,
        "categories": categories,
        "vendors": vendors,
        "current_user": current_user
    })

# Update product - Admin and Manager only
@router.post("/{product_id}/edit")
async def update_product(
    request: Request,
    product_id: int,
    name: str = Form(...),
    description: str = Form(...),
    category_id: int = Form(...),
    vendor_id: int = Form(None),  # Make vendor_id optional
    unit_price: float = Form(...),
    cost_price: float = Form(...),
    reorder_point: int = Form(...),
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Handle edit product form submission"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update product
    product.name = name
    product.description = description
    product.category_id = category_id
    product.vendor_id = vendor_id  # Include vendor_id update
    product.unit_price = unit_price
    product.cost_price = cost_price
    product.reorder_point = reorder_point
    
    db.commit()
    db.refresh(product)
    
    return RedirectResponse(url=f"/products/{product_id}", status_code=302)

# Delete product - Admin and Manager only
@router.post("/{product_id}/delete")
async def delete_product(
    product_id: int,
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Soft delete a product"""
    print(f"Delete product called for product_id: {product_id}")  # Debug log
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        print(f"Product {product_id} not found")  # Debug log
        raise HTTPException(status_code=404, detail="Product not found")
    
    print(f"Deleting product: {product.name}")  # Debug log
    
    # Soft delete
    product.is_active = False
    db.commit()
    
    print(f"Product {product_id} deleted successfully")  # Debug log
    
    # Return JSON response for AJAX calls
    return {"message": "Product deleted successfully", "product_id": product_id}

# API endpoints for AJAX calls
@router.get("/api/products")
async def get_products_api(
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """API endpoint to get all products"""
    products = db.query(Product).filter(Product.is_active == True).all()
    return {"products": [{"id": p.id, "name": p.name, "sku": p.sku} for p in products]}

@router.get("/api/products/{product_id}")
async def get_product_api(
    product_id: int,
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """API endpoint to get a specific product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product