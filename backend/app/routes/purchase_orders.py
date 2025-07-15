# app/routes/purchase_orders.py
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import PurchaseOrder, PurchaseOrderItem, Product, Vendor, User
from datetime import datetime, timedelta
from typing import Optional, List

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Purchase orders list page
@router.get("/", response_class=HTMLResponse)
async def purchase_orders_list(request: Request, db: Session = Depends(get_db)):
    """Display purchase orders list page"""
    purchase_orders = db.query(PurchaseOrder).order_by(PurchaseOrder.order_date.desc()).all()
    return templates.TemplateResponse("purchase_orders/list.html", {
        "request": request, 
        "purchase_orders": purchase_orders
    })

# Create purchase order page
@router.get("/create", response_class=HTMLResponse)
async def create_purchase_order_page(request: Request, db: Session = Depends(get_db)):
    """Display create purchase order page"""
    vendors = db.query(Vendor).filter(Vendor.is_active == True).all()
    products = db.query(Product).filter(Product.is_active == True).all()
    
    return templates.TemplateResponse("purchase_orders/create.html", {
        "request": request,
        "vendors": vendors,
        "products": products
    })

# Process purchase order creation
@router.post("/create")
async def create_purchase_order(
    request: Request,
    vendor_id: int = Form(...),
    expected_delivery_date: str = Form(None),
    notes: str = Form(""),
    product_ids: List[int] = Form(...),
    quantities: List[int] = Form(...),
    unit_costs: List[float] = Form(...),
    db: Session = Depends(get_db)
):
    """Create a new purchase order"""
    try:
        # Generate PO number
        latest_po = db.query(PurchaseOrder).order_by(PurchaseOrder.id.desc()).first()
        po_number = f"PO-{datetime.now().year}-{(latest_po.id + 1) if latest_po else 1:04d}"
        
        # Parse expected delivery date
        exp_delivery = None
        if expected_delivery_date:
            try:
                exp_delivery = datetime.strptime(expected_delivery_date, "%Y-%m-%d")
            except ValueError:
                pass
        
        # Create purchase order
        purchase_order = PurchaseOrder(
            po_number=po_number,
            vendor_id=vendor_id,
            expected_delivery_date=exp_delivery,
            status="pending",
            notes=notes
        )
        
        db.add(purchase_order)
        db.flush()  # Get the ID
        
        # Add purchase order items
        total_amount = 0
        for i in range(len(product_ids)):
            if product_ids[i] and quantities[i] and unit_costs[i]:
                total_cost = quantities[i] * unit_costs[i]
                total_amount += total_cost
                
                po_item = PurchaseOrderItem(
                    purchase_order_id=purchase_order.id,
                    product_id=product_ids[i],
                    quantity_ordered=quantities[i],
                    unit_cost=unit_costs[i],
                    total_cost=total_cost
                )
                db.add(po_item)
        
        # Update total amount
        purchase_order.total_amount = total_amount
        db.commit()
        
        return RedirectResponse(url="/purchase-orders", status_code=302)
        
    except Exception as e:
        print(f"Error creating purchase order: {e}")
        vendors = db.query(Vendor).filter(Vendor.is_active == True).all()
        products = db.query(Product).filter(Product.is_active == True).all()
        return templates.TemplateResponse("purchase_orders/create.html", {
            "request": request,
            "vendors": vendors,
            "products": products,
            "error": f"Error creating purchase order: {str(e)}"
        })

# Purchase order details page
@router.get("/{po_id}", response_class=HTMLResponse)
async def purchase_order_detail(request: Request, po_id: int, db: Session = Depends(get_db)):
    """Display purchase order details"""
    purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    return templates.TemplateResponse("purchase_orders/detail.html", {
        "request": request,
        "purchase_order": purchase_order
    })

# Update purchase order status
@router.post("/{po_id}/update-status")
async def update_purchase_order_status(
    po_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    """Update purchase order status"""
    purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    purchase_order.status = status
    if status == "received":
        purchase_order.actual_delivery_date = datetime.utcnow()
    
    db.commit()
    return RedirectResponse(url=f"/purchase-orders/{po_id}", status_code=302)

# Generate automatic reorder suggestions
@router.get("/reorder/suggestions", response_class=HTMLResponse)
async def reorder_suggestions(request: Request, db: Session = Depends(get_db)):
    """Display reorder suggestions based on low stock"""
    # This would be implemented with inventory integration
    # For now, return empty suggestions
    suggestions = []
    
    return templates.TemplateResponse("purchase_orders/reorder.html", {
        "request": request,
        "suggestions": suggestions
    })

# API: Get purchase order summary
@router.get("/api/summary")
async def get_purchase_order_summary(db: Session = Depends(get_db)):
    """Get purchase order summary for API"""
    try:
        total_orders = db.query(PurchaseOrder).count()
        pending_orders = db.query(PurchaseOrder).filter(PurchaseOrder.status == "pending").count()
        total_value = db.query(PurchaseOrder).with_entities(
            db.func.sum(PurchaseOrder.total_amount)
        ).scalar() or 0
        
        return {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "total_value": float(total_value)
        }
    except Exception as e:
        return {
            "total_orders": 0,
            "pending_orders": 0,
            "total_value": 0,
            "error": str(e)
        }