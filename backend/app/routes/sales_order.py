# app/routes/sales_orders.py
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import SalesOrder, SalesOrderItem, Product, Customer, InventoryItem, StockMovement
from datetime import datetime, timedelta
from typing import Optional, List

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Sales orders list page
@router.get("/", response_class=HTMLResponse)
async def sales_orders_list(request: Request, db: Session = Depends(get_db)):
    """Display sales orders list page"""
    sales_orders = db.query(SalesOrder).order_by(SalesOrder.order_date.desc()).all()
    return templates.TemplateResponse("sales_orders/list.html", {
        "request": request, 
        "sales_orders": sales_orders
    })

# Create sales order page
@router.get("/create", response_class=HTMLResponse)
async def create_sales_order_page(request: Request, db: Session = Depends(get_db)):
    """Display create sales order page"""
    customers = db.query(Customer).filter(Customer.is_active == True).all()
    
    # Get products with available inventory
    available_products = db.query(Product).join(InventoryItem).filter(
        Product.is_active == True,
        InventoryItem.quantity_available > 0,
        InventoryItem.status == "available"
    ).distinct().all()
    
    return templates.TemplateResponse("sales_orders/create.html", {
        "request": request,
        "customers": customers,
        "products": available_products
    })

# Process sales order creation
@router.post("/create")
async def create_sales_order(
    request: Request,
    customer_id: int = Form(...),
    delivery_date: str = Form(None),
    discount_percentage: float = Form(0.0),
    notes: str = Form(""),
    product_ids: List[int] = Form(...),
    quantities: List[int] = Form(...),
    unit_prices: List[float] = Form(...),
    db: Session = Depends(get_db)
):
    """Create a new sales order"""
    try:
        # Generate SO number
        latest_so = db.query(SalesOrder).order_by(SalesOrder.id.desc()).first()
        order_number = f"SO-{datetime.now().year}-{(latest_so.id + 1) if latest_so else 1:04d}"
        
        # Parse delivery date
        delivery_dt = None
        if delivery_date:
            try:
                delivery_dt = datetime.strptime(delivery_date, "%Y-%m-%d")
            except ValueError:
                pass
        
        # Create sales order
        sales_order = SalesOrder(
            order_number=order_number,
            customer_id=customer_id,
            delivery_date=delivery_dt,
            status="pending",
            discount_percentage=discount_percentage,
            notes=notes
        )
        
        db.add(sales_order)
        db.flush()  # Get the ID
        
        # Add sales order items and check inventory
        total_amount = 0
        for i in range(len(product_ids)):
            if product_ids[i] and quantities[i] and unit_prices[i]:
                # Check inventory availability
                available_inventory = db.query(InventoryItem).filter(
                    InventoryItem.product_id == product_ids[i],
                    InventoryItem.quantity_available >= quantities[i],
                    InventoryItem.status == "available"
                ).first()
                
                if not available_inventory:
                    raise Exception(f"Insufficient inventory for product ID {product_ids[i]}")
                
                total_price = quantities[i] * unit_prices[i]
                total_amount += total_price
                
                so_item = SalesOrderItem(
                    sales_order_id=sales_order.id,
                    product_id=product_ids[i],
                    inventory_item_id=available_inventory.id,
                    quantity_ordered=quantities[i],
                    unit_price=unit_prices[i],
                    total_price=total_price
                )
                db.add(so_item)
        
        # Apply discount and update total amount
        discount_amount = total_amount * (discount_percentage / 100)
        final_amount = total_amount - discount_amount
        sales_order.total_amount = final_amount
        
        db.commit()
        
        return RedirectResponse(url="/sales-orders", status_code=302)
        
    except Exception as e:
        print(f"Error creating sales order: {e}")
        customers = db.query(Customer).filter(Customer.is_active == True).all()
        available_products = db.query(Product).join(InventoryItem).filter(
            Product.is_active == True,
            InventoryItem.quantity_available > 0,
            InventoryItem.status == "available"
        ).distinct().all()
        
        return templates.TemplateResponse("sales_orders/create.html", {
            "request": request,
            "customers": customers,
            "products": available_products,
            "error": f"Error creating sales order: {str(e)}"
        })

# Sales order details page
@router.get("/{so_id}", response_class=HTMLResponse)
async def sales_order_detail(request: Request, so_id: int, db: Session = Depends(get_db)):
    """Display sales order details"""
    sales_order = db.query(SalesOrder).filter(SalesOrder.id == so_id).first()
    if not sales_order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    return templates.TemplateResponse("sales_orders/detail.html", {
        "request": request,
        "sales_order": sales_order
    })

# Update sales order status
@router.post("/{so_id}/update-status")
async def update_sales_order_status(
    so_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    """Update sales order status and process inventory"""
    sales_order = db.query(SalesOrder).filter(SalesOrder.id == so_id).first()
    if not sales_order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    old_status = sales_order.status
    sales_order.status = status
    
    # If order is being shipped, reduce inventory
    if status == "shipped" and old_status != "shipped":
        for item in sales_order.items:
            if item.inventory_item:
                # Reduce available quantity
                item.inventory_item.quantity_available -= item.quantity_ordered
                item.quantity_shipped = item.quantity_ordered
                
                # Create stock movement record
                stock_movement = StockMovement(
                    product_id=item.product_id,
                    inventory_item_id=item.inventory_item_id,
                    movement_type="out",
                    quantity=-item.quantity_ordered,
                    reference_type="sales_order",
                    reference_id=sales_order.id,
                    notes=f"Sold to {sales_order.customer.name} - Order: {sales_order.order_number}"
                )
                db.add(stock_movement)
    
    db.commit()
    return RedirectResponse(url=f"/sales-orders/{so_id}", status_code=302)

# Get product inventory for AJAX
@router.get("/api/product-inventory/{product_id}")
async def get_product_inventory(product_id: int, db: Session = Depends(get_db)):
    """Get available inventory for a product"""
    try:
        inventory_items = db.query(InventoryItem).filter(
            InventoryItem.product_id == product_id,
            InventoryItem.quantity_available > 0,
            InventoryItem.status == "available"
        ).all()
        
        total_available = sum([item.quantity_available for item in inventory_items])
        latest_selling_price = inventory_items[0].selling_price if inventory_items else 0
        
        return {
            "available_quantity": total_available,
            "suggested_price": float(latest_selling_price),
            "inventory_items": len(inventory_items)
        }
    except Exception as e:
        return {
            "available_quantity": 0,
            "suggested_price": 0,
            "inventory_items": 0,
            "error": str(e)
        }

# API: Get sales order summary
@router.get("/api/summary")
async def get_sales_order_summary(db: Session = Depends(get_db)):
    """Get sales order summary for API"""
    try:
        total_orders = db.query(SalesOrder).count()
        pending_orders = db.query(SalesOrder).filter(SalesOrder.status == "pending").count()
        total_revenue = db.query(SalesOrder).filter(
            SalesOrder.status.in_(["shipped", "delivered"])
        ).with_entities(db.func.sum(SalesOrder.total_amount)).scalar() or 0
        
        return {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "total_revenue": float(total_revenue)
        }
    except Exception as e:
        return {
            "total_orders": 0,
            "pending_orders": 0,
            "total_revenue": 0,
            "error": str(e)
        }