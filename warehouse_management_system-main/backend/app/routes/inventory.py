# app/routes/inventory.py
from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.models import InventoryItem, Product, StockMovement, User
from app.utils.auth import get_current_active_user_from_cookie, check_user_role_from_cookie
from datetime import datetime
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Inventory overview page - All authenticated users can view
@router.get("/", response_class=HTMLResponse)
async def inventory_overview(
    request: Request,
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Display inventory overview"""
    # Get all inventory items
    all_inventory_items = db.query(InventoryItem).all()
    
    # Get items with available stock
    inventory_items = db.query(InventoryItem).filter(InventoryItem.quantity_available > 0).order_by(InventoryItem.received_date.desc()).all()
    
    # Calculate statistics
    total_items = len(all_inventory_items)
    in_stock_items = len([item for item in all_inventory_items if item.quantity_available > 0])
    
    # Get products to calculate low stock items
    products = db.query(Product).all()
    low_stock_items = 0
    for product in products:
        total_stock = sum(item.quantity_available for item in product.inventory_items if item.status == "available")
        if total_stock <= product.reorder_point:
            low_stock_items += 1
    
    out_of_stock_items = len([item for item in all_inventory_items if item.quantity_available == 0])
    
    # Calculate total inventory value
    total_value = sum([item.quantity_available * float(item.cost_price) for item in inventory_items if item.cost_price])
    
    return templates.TemplateResponse("inventory/overview.html", {
        "request": request,
        "inventory_items": inventory_items,
        "total_value": total_value,
        "total_items": total_items,
        "in_stock_items": in_stock_items, 
        "low_stock_items": low_stock_items,
        "out_of_stock_items": out_of_stock_items,
        "current_user": current_user,
        "user_role": current_user.role,
        "pagination": {"pages": 1, "page": 1, "has_prev": False, "has_next": False}  # Simple pagination placeholder
    })

# Receive inventory page - Admin and Manager only
@router.get("/receive", response_class=HTMLResponse)
async def receive_inventory_page(
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Display receive inventory form"""
    products = db.query(Product).filter(Product.is_active == True).all()
    return templates.TemplateResponse("inventory/receive.html", {
        "request": request,
        "products": products,
        "current_user": current_user,
        "user_role": current_user.role
    })

# Receive inventory form submission - Admin and Manager only
@router.post("/receive")
async def receive_inventory(
    request: Request,
    product_id: int = Form(...),
    quantity: int = Form(...),
    cost_price: float = Form(...),
    expiry_date: Optional[str] = Form(None),
    batch_number: Optional[str] = Form(None),
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Handle receive inventory form submission"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        products = db.query(Product).filter(Product.is_active == True).all()
        return templates.TemplateResponse("inventory/receive.html", {
            "request": request,
            "products": products,
            "error": "Product not found",
            "user_role": current_user.role
        })
    
    # Parse expiry date if provided
    parsed_expiry_date = None
    if expiry_date:
        try:
            parsed_expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d")
        except ValueError:
            products = db.query(Product).filter(Product.is_active == True).all()
            return templates.TemplateResponse("inventory/receive.html", {
                "request": request,
                "products": products,
                "error": "Invalid expiry date format",
                "user_role": current_user.role
            })
    
    # Check if inventory item already exists for this product
    inventory_item = db.query(InventoryItem).filter(InventoryItem.product_id == product_id).first()
    
    if inventory_item:
        # Update existing inventory
        inventory_item.quantity_available += quantity
        inventory_item.cost_price = cost_price  # Update cost price
        if parsed_expiry_date:
            inventory_item.expiry_date = parsed_expiry_date
        if batch_number:
            inventory_item.batch_number = batch_number
        inventory_item.updated_at = datetime.utcnow()
    else:
        # Create new inventory item
        inventory_item = InventoryItem(
            product_id=product_id,
            quantity_available=quantity,
            cost_price=cost_price,
            expiry_date=parsed_expiry_date,
            batch_number=batch_number
        )
        db.add(inventory_item)
    
    # Create stock movement record
    movement = StockMovement(
        product_id=product_id,
        movement_type="in",
        quantity=quantity,
        reference_number=batch_number or f"REC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        notes=f"Received {quantity} units of {product.name}"
    )
    db.add(movement)
    
    db.commit()
    
    return RedirectResponse(url="/inventory", status_code=302)

# Issue inventory page - Admin and Manager only
@router.get("/issue", response_class=HTMLResponse)
async def issue_inventory_page(
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Display issue inventory form"""
    inventory_items = db.query(InventoryItem).filter(InventoryItem.quantity_available > 0).all()
    return templates.TemplateResponse("inventory/issue.html", {
        "request": request,
        "inventory_items": inventory_items,
        "current_user": current_user,
        "user_role": current_user.role
    })

# Issue inventory form submission - Admin and Manager only
@router.post("/issue")
async def issue_inventory(
    request: Request,
    inventory_item_id: int = Form(...),
    quantity: int = Form(...),
    reason: str = Form(...),
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Handle issue inventory form submission"""
    inventory_item = db.query(InventoryItem).filter(InventoryItem.id == inventory_item_id).first()
    if not inventory_item:
        inventory_items = db.query(InventoryItem).filter(InventoryItem.quantity_available > 0).all()
        return templates.TemplateResponse("inventory/issue.html", {
            "request": request,
            "inventory_items": inventory_items,
            "error": "Inventory item not found",
            "user_role": current_user.role
        })
    
    if inventory_item.quantity_available < quantity:
        inventory_items = db.query(InventoryItem).filter(InventoryItem.quantity_available > 0).all()
        return templates.TemplateResponse("inventory/issue.html", {
            "request": request,
            "inventory_items": inventory_items,
            "error": f"Insufficient stock. Available: {inventory_item.quantity_available}",
            "user_role": current_user.role
        })
    
    # Update inventory
    inventory_item.quantity_available -= quantity
    inventory_item.updated_at = datetime.utcnow()
    
    # Create stock movement record
    product = db.query(Product).filter(Product.id == inventory_item.product_id).first()
    movement = StockMovement(
        product_id=inventory_item.product_id,
        movement_type="out",
        quantity=quantity,
        reference_number=f"ISS-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        notes=f"Issued {quantity} units of {product.name if product else 'Unknown Product'}. Reason: {reason}"
    )
    db.add(movement)
    
    db.commit()
    
    return RedirectResponse(url="/inventory", status_code=302)

# Inventory item detail page - All authenticated users can view
@router.get("/{inventory_item_id}", response_class=HTMLResponse)
async def inventory_item_detail(
    request: Request,
    inventory_item_id: int,
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Display inventory item details"""
    inventory_item = db.query(InventoryItem).filter(InventoryItem.id == inventory_item_id).first()
    if not inventory_item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    # Get recent movements for this item
    movements = db.query(StockMovement).filter(
        StockMovement.product_id == inventory_item.product_id
    ).order_by(desc(StockMovement.created_at)).limit(10).all()
    
    return templates.TemplateResponse("inventory/detail.html", {
        "request": request,
        "item": inventory_item,
        "stock_movements": movements,
        "current_user": current_user,
        "user_role": current_user.role
    })

# API endpoints for AJAX calls
@router.get("/api/inventory")
async def get_inventory_api(
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """API endpoint to get all inventory items"""
    inventory_items = db.query(InventoryItem).filter(InventoryItem.quantity_available > 0).all()
    return {"inventory_items": [{"id": i.id, "product_id": i.product_id, "quantity": i.quantity_available} for i in inventory_items]}

@router.get("/api/inventory/{inventory_item_id}")
async def get_inventory_item_api(
    inventory_item_id: int,
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """API endpoint to get a specific inventory item"""
    inventory_item = db.query(InventoryItem).filter(InventoryItem.id == inventory_item_id).first()
    if not inventory_item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return inventory_item