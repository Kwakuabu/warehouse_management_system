# app/routes/purchase_orders.py
from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.models import PurchaseOrder, PurchaseOrderItem, Product, Vendor, User, InventoryItem
from app.utils.auth import get_current_active_user_from_cookie, check_user_role_from_cookie
from datetime import datetime
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Purchase orders list page - All authenticated users can view
@router.get("/", response_class=HTMLResponse)
async def list_purchase_orders(
    request: Request,
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Display list of all purchase orders"""
    purchase_orders = db.query(PurchaseOrder).order_by(desc(PurchaseOrder.order_date)).all()
    
    return templates.TemplateResponse("purchase_orders/list.html", {
        "request": request,
        "purchase_orders": purchase_orders,
        "current_user": current_user,
        "user_role": current_user.role,
        "current_datetime": datetime.utcnow(),
        "pagination": {"pages": 1, "page": 1, "has_prev": False, "has_next": False}  # Simple pagination placeholder
    })

# Create purchase order page - Admin and Manager only
@router.get("/create", response_class=HTMLResponse)
async def create_purchase_order_page(
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Display create purchase order form"""
    vendors = db.query(Vendor).filter(Vendor.is_active == True).all()
    products = db.query(Product).filter(Product.is_active == True).all()
    
    return templates.TemplateResponse("purchase_orders/create.html", {
        "request": request,
        "vendors": vendors,
        "products": products,
        "current_user": current_user,
        "user_role": current_user.role
    })

# Create purchase order form submission - Admin and Manager only
@router.post("/create")
async def create_purchase_order(
    request: Request,
    vendor_id: int = Form(...),
    expected_delivery_date: str = Form(...),
    notes: Optional[str] = Form(None),
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Handle create purchase order form submission"""
    # Generate PO number
    po_number = f"PO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # Parse expected delivery date
    try:
        parsed_delivery_date = datetime.strptime(expected_delivery_date, "%Y-%m-%d")
    except ValueError:
        vendors = db.query(Vendor).filter(Vendor.is_active == True).all()
        products = db.query(Product).filter(Product.is_active == True).all()
        return templates.TemplateResponse("purchase_orders/create.html", {
            "request": request,
            "vendors": vendors,
            "products": products,
            "error": "Invalid delivery date format",
            "user_role": current_user.role
        })
    
    # Create purchase order
    purchase_order = PurchaseOrder(
        po_number=po_number,
        vendor_id=vendor_id,
        expected_delivery_date=parsed_delivery_date,
        notes=notes,
        created_by=current_user.id
    )
    db.add(purchase_order)
    db.commit()
    db.refresh(purchase_order)
    
    return RedirectResponse(url=f"/purchase-orders/{purchase_order.id}", status_code=302)

# Purchase order detail page - All authenticated users can view
@router.get("/{purchase_order_id}", response_class=HTMLResponse)
async def purchase_order_detail(
    request: Request,
    purchase_order_id: int,
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Display purchase order details"""
    purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == purchase_order_id).first()
    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    return templates.TemplateResponse("purchase_orders/detail.html", {
        "request": request,
        "purchase_order": purchase_order,
        "current_user": current_user,
        "user_role": current_user.role
    })

# Edit purchase order page - Admin and Manager only
@router.get("/{purchase_order_id}/edit", response_class=HTMLResponse)
async def edit_purchase_order_page(
    request: Request,
    purchase_order_id: int,
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Display edit purchase order form"""
    purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == purchase_order_id).first()
    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    vendors = db.query(Vendor).filter(Vendor.is_active == True).all()
    
    return templates.TemplateResponse("purchase_orders/edit.html", {
        "request": request,
        "purchase_order": purchase_order,
        "vendors": vendors,
        "current_user": current_user,
        "user_role": current_user.role
    })

# Edit purchase order form submission - Admin and Manager only
@router.post("/{purchase_order_id}/edit")
async def edit_purchase_order(
    request: Request,
    purchase_order_id: int,
    vendor_id: int = Form(...),
    order_date: str = Form(...),
    expected_delivery_date: Optional[str] = Form(None),
    status: str = Form(...),
    total_amount: Optional[float] = Form(None),
    notes: Optional[str] = Form(None),
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Handle edit purchase order form submission"""
    purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == purchase_order_id).first()
    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    try:
        # Parse dates
        parsed_order_date = datetime.strptime(order_date, "%Y-%m-%d")
        parsed_delivery_date = None
        if expected_delivery_date:
            parsed_delivery_date = datetime.strptime(expected_delivery_date, "%Y-%m-%d")
        
        # Update purchase order
        purchase_order.vendor_id = vendor_id
        purchase_order.order_date = parsed_order_date
        purchase_order.expected_delivery_date = parsed_delivery_date
        purchase_order.status = status
        purchase_order.notes = notes
        
        if total_amount is not None:
            purchase_order.total_amount = total_amount
        
        # If status is received, set actual delivery date
        if status == "received" and not purchase_order.actual_delivery_date:
            purchase_order.actual_delivery_date = datetime.utcnow()
        
        db.commit()
        
        return RedirectResponse(url=f"/purchase-orders/{purchase_order_id}", status_code=302)
        
    except ValueError as e:
        vendors = db.query(Vendor).filter(Vendor.is_active == True).all()
        return templates.TemplateResponse("purchase_orders/edit.html", {
            "request": request,
            "purchase_order": purchase_order,
            "vendors": vendors,
            "error": f"Invalid date format: {str(e)}",
            "current_user": current_user,
            "user_role": current_user.role
        })

# Add item to purchase order - Admin and Manager only
@router.post("/{purchase_order_id}/add-item")
async def add_purchase_order_item(
    request: Request,
    purchase_order_id: int,
    product_id: int = Form(...),
    quantity_ordered: int = Form(...),
    unit_cost: float = Form(...),
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Handle add item to purchase order form submission"""
    purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == purchase_order_id).first()
    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    # Create purchase order item
    total_cost = quantity_ordered * unit_cost
    item = PurchaseOrderItem(
        purchase_order_id=purchase_order_id,
        product_id=product_id,
        quantity_ordered=quantity_ordered,
        unit_cost=unit_cost,
        total_cost=total_cost
    )
    db.add(item)
    
    # Update purchase order total
    purchase_order.total_amount += total_cost
    db.commit()
    
    return RedirectResponse(url=f"/purchase-orders/{purchase_order_id}", status_code=302)

# Update purchase order status - Admin and Manager only
@router.post("/{purchase_order_id}/update-status")
async def update_purchase_order_status(
    purchase_order_id: int,
    status: str = Form(...),
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Update purchase order status"""
    purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == purchase_order_id).first()
    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    purchase_order.status = status
    if status == "received":
        purchase_order.actual_delivery_date = datetime.utcnow()
    
    db.commit()
    
    return RedirectResponse(url=f"/purchase-orders/{purchase_order_id}", status_code=302)

# API endpoints for AJAX calls
# Reorder suggestions page - Manager and Admin only
@router.get("/reorder/suggestions", response_class=HTMLResponse)
async def reorder_suggestions_page(
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Display products that need reordering grouped by vendor"""
    
    # Get all products with their current stock levels
    products_needing_reorder = []
    all_products = db.query(Product).filter(Product.is_active == True).all()
    
    for product in all_products:
        # Calculate total available stock
        total_stock = sum(
            item.quantity_available 
            for item in product.inventory_items 
            if item.status == "available"
        )
        
        # Check if below reorder point
        if total_stock <= product.reorder_point:
            # Calculate suggested order quantity (reorder to max stock level)
            suggested_quantity = max(
                product.max_stock_level - total_stock,
                product.reorder_point * 2  # At least double the reorder point
            )
            
            products_needing_reorder.append({
                "product": product,
                "current_stock": total_stock,
                "reorder_point": product.reorder_point,
                "suggested_quantity": suggested_quantity,
                "vendor": product.vendor
            })
    
    # Group by vendor
    vendors_with_suggestions = {}
    for item in products_needing_reorder:
        vendor = item["vendor"]
        if vendor:
            vendor_key = f"{vendor.id}_{vendor.name}"
            if vendor_key not in vendors_with_suggestions:
                vendors_with_suggestions[vendor_key] = {
                    "vendor": vendor,
                    "products": []
                }
            vendors_with_suggestions[vendor_key]["products"].append(item)
        else:
            # Products without vendors go to "No Vendor" group
            if "no_vendor" not in vendors_with_suggestions:
                vendors_with_suggestions["no_vendor"] = {
                    "vendor": None,
                    "products": []
                }
            vendors_with_suggestions["no_vendor"]["products"].append(item)
    
    return templates.TemplateResponse("purchase_orders/reorder_suggestions.html", {
        "request": request,
        "vendors_with_suggestions": vendors_with_suggestions,
        "total_products_needing_reorder": len(products_needing_reorder),
        "current_user": current_user,
        "user_role": current_user.role
    })

@router.get("/api/purchase-orders")
async def get_purchase_orders_api(
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """API endpoint to get all purchase orders"""
    purchase_orders = db.query(PurchaseOrder).all()
    return {"purchase_orders": [{"id": po.id, "po_number": po.po_number, "status": po.status} for po in purchase_orders]}

@router.get("/api/purchase-orders/{purchase_order_id}")
async def get_purchase_order_api(
    purchase_order_id: int,
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """API endpoint to get a specific purchase order"""
    purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == purchase_order_id).first()
    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return purchase_order