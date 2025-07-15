# app/routes/inventory.py
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.database import get_db
from app.models.models import InventoryItem, Product, StockMovement, Category
from datetime import datetime, timedelta
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Inventory overview page
@router.get("/", response_class=HTMLResponse)
async def inventory_overview(request: Request, db: Session = Depends(get_db)):
    """Display inventory overview page"""
    try:
        # Get inventory items with product details - simplified query
        inventory_items = db.query(InventoryItem).filter(
            InventoryItem.quantity_available > 0
        ).all()
        
        # Get low stock items - simplified
        low_stock_items = []
        expiring_soon = []
        
        for item in inventory_items:
            if item.product and item.quantity_available <= item.product.reorder_point:
                low_stock_items.append(item)
            
            if item.expiry_date and item.expiry_date <= datetime.utcnow() + timedelta(days=30) and item.expiry_date > datetime.utcnow():
                expiring_soon.append(item)
        
        # Calculate total inventory value
        total_value = sum([item.quantity_available * item.cost_price for item in inventory_items if item.cost_price])
        
        return templates.TemplateResponse("inventory/overview.html", {
            "request": request,
            "inventory_items": inventory_items,
            "low_stock_items": low_stock_items,
            "expiring_soon": expiring_soon,
            "total_value": total_value,
            "now": datetime.utcnow()  # Add current time for template
        })
    except Exception as e:
        print(f"Error in inventory overview: {e}")
        return templates.TemplateResponse("inventory/overview.html", {
            "request": request,
            "inventory_items": [],
            "low_stock_items": [],
            "expiring_soon": [],
            "total_value": 0,
            "now": datetime.utcnow(),
            "error": str(e)
        })

# Stock receive page
@router.get("/receive", response_class=HTMLResponse)
async def receive_stock_page(request: Request, db: Session = Depends(get_db)):
    """Display stock receiving page"""
    try:
        products = db.query(Product).filter(Product.is_active == True).all()
        return templates.TemplateResponse("inventory/receive.html", {
            "request": request,
            "products": products
        })
    except Exception as e:
        print(f"Error in receive stock page: {e}")
        return templates.TemplateResponse("inventory/receive.html", {
            "request": request,
            "products": [],
            "error": str(e)
        })

# Process stock receipt
@router.post("/receive")
async def receive_stock(
    request: Request,
    product_id: int = Form(...),
    batch_number: str = Form(...),
    quantity: int = Form(...),
    cost_price: float = Form(...),
    selling_price: float = Form(...),
    manufacture_date: str = Form(None),
    expiry_date: str = Form(None),
    location: str = Form(""),
    requires_cold_chain: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Process incoming stock"""
    try:
        # Parse dates safely
        mfg_date = None
        exp_date = None
        
        if manufacture_date:
            try:
                mfg_date = datetime.strptime(manufacture_date, "%Y-%m-%d")
            except ValueError:
                pass
        
        if expiry_date:
            try:
                exp_date = datetime.strptime(expiry_date, "%Y-%m-%d")
            except ValueError:
                pass
        
        # Create inventory item
        inventory_item = InventoryItem(
            product_id=product_id,
            batch_number=batch_number,
            manufacture_date=mfg_date,
            expiry_date=exp_date,
            quantity_available=quantity,
            cost_price=cost_price,
            selling_price=selling_price,
            location=location,
            status="available"
        )
        
        db.add(inventory_item)
        db.flush()  # Get the ID
        
        # Create stock movement record
        stock_movement = StockMovement(
            product_id=product_id,
            inventory_item_id=inventory_item.id,
            movement_type="in",
            quantity=quantity,
            reference_type="receipt",
            notes=f"Stock received - Batch: {batch_number}"
        )
        
        db.add(stock_movement)
        db.commit()
        
        return RedirectResponse(url="/inventory", status_code=302)
        
    except Exception as e:
        print(f"Error processing stock receipt: {e}")
        db.rollback()
        products = db.query(Product).filter(Product.is_active == True).all()
        return templates.TemplateResponse("inventory/receive.html", {
            "request": request,
            "products": products,
            "error": f"Error processing stock receipt: {str(e)}"
        })

# API: Get inventory summary
@router.get("/api/summary")
async def get_inventory_summary(db: Session = Depends(get_db)):
    """Get inventory summary for API"""
    try:
        total_items = db.query(func.count(InventoryItem.id)).scalar() or 0
        total_value = db.query(func.sum(InventoryItem.quantity_available * InventoryItem.cost_price)).scalar() or 0
        low_stock_count = 0  # We'll calculate this simply for now
        
        return {
            "total_items": total_items,
            "total_value": float(total_value),
            "low_stock_count": low_stock_count
        }
    except Exception as e:
        print(f"Error in inventory summary API: {e}")
        return {
            "total_items": 0,
            "total_value": 0,
            "low_stock_count": 0,
            "error": str(e)
        }