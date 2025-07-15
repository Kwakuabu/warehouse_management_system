# app/routes/products.py
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Product, Category, Vendor
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Products list page
@router.get("/", response_class=HTMLResponse)
async def products_list(request: Request, db: Session = Depends(get_db)):
    """Display products list page"""
    # Use left joins to handle missing categories or vendors
    products = db.query(Product).all()
    return templates.TemplateResponse("products/list.html", {
        "request": request, 
        "products": products
    })

# Add product page
@router.get("/add", response_class=HTMLResponse)
async def add_product_page(request: Request, db: Session = Depends(get_db)):
    """Display add product page"""
    categories = db.query(Category).all()
    vendors = db.query(Vendor).all()
    return templates.TemplateResponse("products/add.html", {
        "request": request,
        "categories": categories,
        "vendors": vendors
    })

# Create product
@router.post("/add")
async def create_product(
    request: Request,
    sku: str = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    category_id: int = Form(...),
    vendor_id: int = Form(...),
    unit_of_measure: str = Form(...),
    reorder_point: int = Form(10),
    max_stock_level: int = Form(1000),
    storage_temperature_min: Optional[float] = Form(None),
    storage_temperature_max: Optional[float] = Form(None),
    requires_cold_chain: bool = Form(False),
    is_controlled_substance: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Create a new product"""
    # Check if SKU already exists
    existing_product = db.query(Product).filter(Product.sku == sku).first()
    if existing_product:
        categories = db.query(Category).all()
        vendors = db.query(Vendor).all()
        return templates.TemplateResponse("products/add.html", {
            "request": request,
            "error": "SKU already exists",
            "categories": categories,
            "vendors": vendors
        })
    
    # Create new product
    product = Product(
        sku=sku,
        name=name,
        description=description,
        category_id=category_id,
        vendor_id=vendor_id,
        unit_of_measure=unit_of_measure,
        reorder_point=reorder_point,
        max_stock_level=max_stock_level,
        storage_temperature_min=storage_temperature_min,
        storage_temperature_max=storage_temperature_max,
        requires_cold_chain=requires_cold_chain,
        is_controlled_substance=is_controlled_substance
    )
    db.add(product)
    db.commit()
    
    return RedirectResponse(url="/products", status_code=302)

# Product details page
@router.get("/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: int, db: Session = Depends(get_db)):
    """Display product details page"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return templates.TemplateResponse("products/detail.html", {
        "request": request, 
        "product": product
    })

# API: Get all products
@router.get("/api/products")
async def get_products(db: Session = Depends(get_db)):
    """Get all products for API"""
    products = db.query(Product).all()
    return {"products": [{"id": p.id, "sku": p.sku, "name": p.name} for p in products]}