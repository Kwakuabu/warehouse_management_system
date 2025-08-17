# app/routes/inventory.py
from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.models import InventoryItem, Product, StockMovement, User, Category
from app.utils.auth import get_current_active_user_from_cookie, check_user_role_from_cookie, check_user_roles_from_cookie
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
    """Display inventory overview - Role-based view"""
    
    if current_user.role in ["admin", "manager"]:
        # Warehouse management view for admin/manager
        return await warehouse_inventory_view(request, current_user, db)
    else:
        # Customer-facing view for staff (hospital buyers)
        return await customer_inventory_view(request, current_user, db)

async def warehouse_inventory_view(request: Request, current_user: User, db: Session):
    """Warehouse management inventory view for admin/manager users"""
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
    
    # Get categories for filter dropdown
    categories = db.query(Category).all()
    
    return templates.TemplateResponse("inventory/overview.html", {
        "request": request,
        "inventory_items": inventory_items,
        "total_value": total_value,
        "total_items": total_items,
        "in_stock_items": in_stock_items, 
        "low_stock_items": low_stock_items,
        "out_of_stock_items": out_of_stock_items,
        "categories": categories,
        "current_user": current_user,
        "user_role": current_user.role,
        "view_type": "warehouse",
        "pagination": {
            "pages": 1, 
            "page": 1, 
            "has_prev": False, 
            "has_next": False,
            "prev_num": None,
            "next_num": None,
            "iter_pages": lambda: [1]
        }  # Simple pagination placeholder
    })

async def customer_inventory_view(request: Request, current_user: User, db: Session):
    """Customer-facing inventory view for staff users (hospital buyers)"""
    # Get products with available stock (what they can order)
    available_products = db.query(Product).join(InventoryItem).filter(
        Product.is_active == True,
        InventoryItem.quantity_available > 0,
        InventoryItem.status == "available"
    ).distinct().order_by(Product.name).all()
    
    # Calculate statistics for customer view
    total_products = len(available_products)
    in_stock_products = total_products
    
    # Calculate total value of available inventory (what they can order)
    total_value = 0
    for product in available_products:
        # Get total available stock for this product
        total_stock = sum(item.quantity_available for item in product.inventory_items if item.status == "available")
        if product.unit_price:
            total_value += total_stock * float(product.unit_price)
    
    # Get categories for filter dropdown
    categories = db.query(Category).filter(
        Category.id.in_([p.category_id for p in available_products if p.category_id])
    ).all()
    
    return templates.TemplateResponse("inventory/overview.html", {
        "request": request,
        "available_products": available_products,  # Different data structure for customer view
        "total_value": total_value,
        "total_items": total_products,
        "in_stock_items": in_stock_products,
        "low_stock_items": 0,  # Not relevant for customers
        "out_of_stock_items": 0,  # Not relevant for customers
        "categories": categories,
        "current_user": current_user,
        "user_role": current_user.role,
        "view_type": "customer",
        "pagination": {
            "pages": 1, 
            "page": 1, 
            "has_prev": False, 
            "has_next": False,
            "prev_num": None,
            "next_num": None,
            "iter_pages": lambda: [1]
        }
    })

# Receive inventory page - Admin and Manager only
@router.get("/receive", response_class=HTMLResponse)
async def receive_inventory_page(
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Display receive inventory form - Admin and Manager only"""
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
    selling_price: float = Form(...),
    expiry_date: Optional[str] = Form(None),
    batch_number: str = Form(...),
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
        inventory_item.selling_price = selling_price  # Update selling price
        if parsed_expiry_date:
            inventory_item.expiry_date = parsed_expiry_date
        inventory_item.batch_number = batch_number
        inventory_item.updated_at = datetime.utcnow()
    else:
        # Create new inventory item
        inventory_item = InventoryItem(
            product_id=product_id,
            quantity_available=quantity,
            cost_price=cost_price,
            selling_price=selling_price,
            expiry_date=parsed_expiry_date,
            batch_number=batch_number
        )
        db.add(inventory_item)
    
    # Create stock movement record
    movement = StockMovement(
        product_id=product_id,
        movement_type="in",
        quantity=quantity,
        reference_number=batch_number,
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

# Receive stock API endpoint - Must come before detail route to avoid conflicts
@router.post("/{inventory_item_id}/receive")
async def receive_stock_api(
    inventory_item_id: int,
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Receive stock for existing inventory item via API"""
    try:
        data = await request.json()
        quantity = data.get("quantity", 0)
        notes = data.get("notes", "")
        
        if quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be greater than 0")
        
        inventory_item = db.query(InventoryItem).filter(InventoryItem.id == inventory_item_id).first()
        if not inventory_item:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        
        # Update inventory quantity
        inventory_item.quantity_available += quantity
        inventory_item.updated_at = datetime.utcnow()
        
        # Create stock movement record
        movement = StockMovement(
            product_id=inventory_item.product_id,
            movement_type="in",
            quantity=quantity,
            reference_number=inventory_item.batch_number,
            notes=f"Received {quantity} units via API. {notes}"
        )
        db.add(movement)
        
        db.commit()
        
        return {"message": "Stock received successfully", "new_quantity": inventory_item.quantity_available}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

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

@router.get("/export")
async def export_inventory(
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Export inventory data as CSV"""
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    # Get all inventory items
    inventory_items = db.query(InventoryItem).all()
    
    # Create CSV data
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Product Name", "SKU", "Category", "Batch Number", 
        "Quantity Available", "Cost Price", "Selling Price", 
        "Status", "Received Date", "Expiry Date"
    ])
    
    # Write data
    for item in inventory_items:
        writer.writerow([
            item.product.name,
            item.product.sku,
            item.product.category.name if item.product.category else "",
            item.batch_number,
            item.quantity_available,
            float(item.cost_price),
            float(item.selling_price),
            item.status,
            item.received_date.strftime("%Y-%m-%d") if item.received_date else "",
            item.expiry_date.strftime("%Y-%m-%d") if item.expiry_date else ""
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inventory_export.csv"}
    )