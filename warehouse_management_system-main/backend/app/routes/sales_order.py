# app/routes/sales_orders.py
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import SalesOrder, SalesOrderItem, Product, Customer, InventoryItem, StockMovement, User
from app.utils.auth import check_user_role_from_cookie, get_current_active_user_from_cookie, check_user_roles_from_cookie
from datetime import datetime, timedelta
from typing import Optional, List

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Hospital My Orders page - Staff users see only their hospital's orders
@router.get("/my-orders", response_class=HTMLResponse)
async def hospital_my_orders(
    request: Request, 
    current_user: User = Depends(check_user_roles_from_cookie(["staff"])),
    db: Session = Depends(get_db)
):
    """Display hospital's own orders - Staff users only see their hospital's orders"""
    
    if not current_user.hospital_id:
        # If staff user has no hospital assigned, show empty orders
        return templates.TemplateResponse("sales_orders/my_orders.html", {
            "request": request, 
            "sales_orders": [],
            "current_user": current_user,
            "user_role": current_user.role,
            "current_datetime": datetime.utcnow(),
            "view_type": "hospital",
            "total_orders": 0,
            "pending_orders": 0,
            "shipped_orders": 0,
            "delivered_orders": 0,
            "total_spent": 0,
            "recent_orders": 0,
            "pagination": {"pages": 1, "page": 1, "has_prev": False, "has_next": False}
        })
    
    # Get orders for the staff user's specific hospital
    hospital_orders = db.query(SalesOrder).filter(
        SalesOrder.customer_id == current_user.hospital_id
    ).order_by(SalesOrder.order_date.desc()).all()
    
    # Calculate hospital-specific metrics
    total_orders = len(hospital_orders)
    pending_orders = len([o for o in hospital_orders if o.status in ["pending", "confirmed"]])
    shipped_orders = len([o for o in hospital_orders if o.status == "shipped"])
    delivered_orders = len([o for o in hospital_orders if o.status == "delivered"])
    
    # Calculate total spent by hospital
    total_spent = sum(float(order.total_amount) for order in hospital_orders)
    
    # Get recent orders (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_orders = len([o for o in hospital_orders if o.order_date >= thirty_days_ago])
    
    return templates.TemplateResponse("sales_orders/my_orders.html", {
        "request": request, 
        "sales_orders": hospital_orders,
        "current_user": current_user,
        "user_role": current_user.role,
        "current_datetime": datetime.utcnow(),
        "view_type": "hospital",  # Indicates this is hospital view
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "shipped_orders": shipped_orders,
        "delivered_orders": delivered_orders,
        "total_spent": total_spent,
        "recent_orders": recent_orders,
        "pagination": {"pages": 1, "page": 1, "has_prev": False, "has_next": False}
    })

# Sales orders list page - All authenticated users
@router.get("/", response_class=HTMLResponse)
async def sales_orders_list(
    request: Request, 
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Display sales orders list page - All authenticated users"""
    sales_orders = db.query(SalesOrder).order_by(SalesOrder.order_date.desc()).all()
    return templates.TemplateResponse("sales_orders/list.html", {
        "request": request, 
        "sales_orders": sales_orders,
        "current_user": current_user,
        "user_role": current_user.role,
        "current_datetime": datetime.utcnow(),
        "pagination": {"pages": 1, "page": 1, "has_prev": False, "has_next": False}  # Simple pagination placeholder
    })

# Create sales order page - Staff, Manager and Admin can create orders
@router.get("/create", response_class=HTMLResponse)
async def create_sales_order_page(
    request: Request, 
    current_user: User = Depends(check_user_roles_from_cookie(["staff", "manager"])),
    db: Session = Depends(get_db)
):
    """Display create sales order page - Staff (hospital buyers) and Manager/Admin can create orders"""
    
    # For staff users, only show their hospital; for managers, show all customers
    if current_user.role == "staff" and current_user.hospital_id:
        customers = db.query(Customer).filter(
            Customer.id == current_user.hospital_id,
            Customer.is_active == True
        ).all()
    else:
        customers = db.query(Customer).filter(Customer.is_active == True).all()
    
    # Get all active products (not just those with inventory)
    # This allows creating orders even for products that might be backordered
    available_products = db.query(Product).filter(Product.is_active == True).all()
    
    return templates.TemplateResponse("sales_orders/create.html", {
        "request": request,
        "customers": customers,
        "products": available_products,
        "current_user": current_user,
        "user_role": current_user.role,
        "auto_customer_id": current_user.hospital_id if current_user.role == "staff" else None
    })

# Process sales order creation - Staff, Manager and Admin can create orders
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
    current_user: User = Depends(check_user_roles_from_cookie(["staff", "manager"])),
    db: Session = Depends(get_db)
):
    """Create a new sales order - Staff (hospital buyers) and Manager/Admin can create orders"""
    try:
        # For staff users, ensure they can only create orders for their hospital
        if current_user.role == "staff" and current_user.hospital_id:
            if customer_id != current_user.hospital_id:
                raise HTTPException(status_code=403, detail="Staff users can only create orders for their assigned hospital")
        elif current_user.role == "staff" and not current_user.hospital_id:
            raise HTTPException(status_code=403, detail="Staff user must be assigned to a hospital to create orders")
        
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
            notes=notes,
            created_by=current_user.id
        )
        
        db.add(sales_order)
        db.flush()  # Get the ID
        
        # Add sales order items and check inventory
        total_amount = 0
        for i in range(len(product_ids)):
            if product_ids[i] and quantities[i] and unit_prices[i]:
                # Check inventory availability (optional - allow backorders)
                available_inventory = db.query(InventoryItem).filter(
                    InventoryItem.product_id == product_ids[i],
                    InventoryItem.quantity_available >= quantities[i],
                    InventoryItem.status == "available"
                ).order_by(InventoryItem.received_date.asc()).first()  # FIFO - oldest first
                
                # Allow creating orders even without sufficient inventory (backorder)
                inventory_item_id = available_inventory.id if available_inventory else None
                
                total_price = quantities[i] * unit_prices[i]
                total_amount += total_price
                
                so_item = SalesOrderItem(
                    sales_order_id=sales_order.id,
                    product_id=product_ids[i],
                    inventory_item_id=inventory_item_id,  # Can be None for backorders
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
        # Use same product filtering as GET route
        available_products = db.query(Product).filter(Product.is_active == True).all()
        
        return templates.TemplateResponse("sales_orders/create.html", {
            "request": request,
            "customers": customers,
            "products": available_products,
            "current_user": current_user,
            "user_role": current_user.role,
            "error": f"Error creating sales order: {str(e)}"
        })

# Sales order details page
@router.get("/{so_id}", response_class=HTMLResponse)
async def sales_order_detail(
    request: Request, 
    so_id: int, 
    current_user: User = Depends(check_user_roles_from_cookie(["staff", "manager", "admin"])),
    db: Session = Depends(get_db)
):
    """Display sales order details"""
    sales_order = db.query(SalesOrder).filter(SalesOrder.id == so_id).first()
    if not sales_order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    # Pre-load inventory items for each order item to avoid N+1 queries
    for item in sales_order.items:
        if item.inventory_item_id:
            item.inventory_item = db.query(InventoryItem).filter(InventoryItem.id == item.inventory_item_id).first()
    
    # Calculate subtotal for template (convert to float to avoid decimal arithmetic issues)
    subtotal = float(sales_order.total_amount) / (1 - float(sales_order.discount_percentage)/100) if sales_order.discount_percentage > 0 else float(sales_order.total_amount)
    discount_amount = (subtotal * float(sales_order.discount_percentage)/100) if sales_order.discount_percentage > 0 else 0
    
    return templates.TemplateResponse("sales_orders/detail.html", {
        "request": request,
        "sales_order": sales_order,
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "current_user": current_user,
        "user_role": current_user.role
    })

# Edit sales order page - Staff, Manager and Admin can edit their orders
@router.get("/{so_id}/edit", response_class=HTMLResponse)
async def edit_sales_order_page(
    request: Request,
    so_id: int,
    current_user: User = Depends(check_user_roles_from_cookie(["staff", "manager"])),
    db: Session = Depends(get_db)
):
    """Display edit sales order page - Staff (hospital buyers) and Manager/Admin can edit orders"""
    sales_order = db.query(SalesOrder).filter(SalesOrder.id == so_id).first()
    if not sales_order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    # Only allow editing pending orders
    if sales_order.status not in ["pending", "confirmed"]:
        raise HTTPException(status_code=400, detail="Cannot edit orders that are already shipped or delivered")
    
    customers = db.query(Customer).filter(Customer.is_active == True).all()
    available_products = db.query(Product).filter(Product.is_active == True).all()
    
    return templates.TemplateResponse("sales_orders/edit.html", {
        "request": request,
        "sales_order": sales_order,
        "customers": customers,
        "products": available_products,
        "current_user": current_user,
        "user_role": current_user.role
    })

# Process sales order edit - Staff, Manager and Admin can edit their orders
@router.post("/{so_id}/edit")
async def edit_sales_order(
    request: Request,
    so_id: int,
    customer_id: int = Form(...),
    delivery_date: str = Form(None),
    discount_percentage: float = Form(0.0),
    notes: str = Form(""),
    product_ids: List[int] = Form(...),
    quantities: List[int] = Form(...),
    unit_prices: List[float] = Form(...),
    current_user: User = Depends(check_user_roles_from_cookie(["staff", "manager"])),
    db: Session = Depends(get_db)
):
    """Edit an existing sales order - Staff (hospital buyers) and Manager/Admin can edit orders"""
    try:
        sales_order = db.query(SalesOrder).filter(SalesOrder.id == so_id).first()
        if not sales_order:
            raise HTTPException(status_code=404, detail="Sales order not found")
        
        # Only allow editing pending orders
        if sales_order.status not in ["pending", "confirmed"]:
            raise HTTPException(status_code=400, detail="Cannot edit orders that are already shipped or delivered")
        
        # Update sales order details
        sales_order.customer_id = customer_id
        sales_order.delivery_date = datetime.strptime(delivery_date, "%Y-%m-%d") if delivery_date else None
        sales_order.discount_percentage = discount_percentage
        sales_order.notes = notes
        
        # Remove existing items
        db.query(SalesOrderItem).filter(SalesOrderItem.sales_order_id == so_id).delete()
        
        # Add new items
        total_amount = 0
        for i in range(len(product_ids)):
            if product_ids[i] and quantities[i] and unit_prices[i]:
                total_price = quantities[i] * unit_prices[i]
                total_amount += total_price
                
                so_item = SalesOrderItem(
                    sales_order_id=sales_order.id,
                    product_id=product_ids[i],
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
        
        return RedirectResponse(url=f"/sales-orders/{so_id}", status_code=302)
        
    except Exception as e:
        print(f"Error editing sales order: {e}")
        customers = db.query(Customer).filter(Customer.is_active == True).all()
        available_products = db.query(Product).filter(Product.is_active == True).all()
        
        return templates.TemplateResponse("sales_orders/edit.html", {
            "request": request,
            "sales_order": sales_order,
            "customers": customers,
            "products": available_products,
            "current_user": current_user,
            "user_role": current_user.role,
            "error": f"Error editing sales order: {str(e)}"
        })

# Update sales order status - Only Admin and Manager can update status
@router.post("/{so_id}/update-status")
async def update_sales_order_status(
    so_id: int,
    status: str = Form(...),
    current_user: User = Depends(check_user_roles_from_cookie(["admin", "manager"])),  # Only admin/manager can update status
    db: Session = Depends(get_db)
):
    """Update sales order status and process inventory - Only Admin and Manager can process orders"""
    sales_order = db.query(SalesOrder).filter(SalesOrder.id == so_id).first()
    if not sales_order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    old_status = sales_order.status
    sales_order.status = status
    
    # If order is being shipped, reduce inventory
    if status == "shipped" and old_status != "shipped":
        for item in sales_order.items:
            if item.inventory_item_id:
                # Get the inventory item
                inventory_item = db.query(InventoryItem).filter(InventoryItem.id == item.inventory_item_id).first()
                if inventory_item and inventory_item.quantity_available >= item.quantity_ordered:
                    # Reduce available quantity
                    inventory_item.quantity_available -= item.quantity_ordered
                    item.quantity_shipped = item.quantity_ordered
                    
                    # Create stock movement record
                    stock_movement = StockMovement(
                        product_id=item.product_id,
                        inventory_item_id=item.inventory_item_id,
                        movement_type="out",
                        quantity=-item.quantity_ordered,
                        reference_type="sales_order",
                        reference_id=sales_order.id,
                        reference_number=sales_order.order_number,
                        notes=f"Sold to {sales_order.customer.name} - Order: {sales_order.order_number}",
                        created_by=current_user.id
                    )
                    db.add(stock_movement)
                else:
                    # Handle insufficient stock or missing inventory item
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Insufficient stock for product {item.product.name if item.product else 'Unknown'}"
                    )
    
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

# Partial shipment route - Only Admin and Manager can handle partial shipments
@router.post("/{so_id}/partial-shipment")
async def partial_shipment(
    so_id: int,
    item_id: int = Form(...),
    quantity_shipped: int = Form(...),
    current_user: User = Depends(check_user_roles_from_cookie(["admin", "manager"])),  # Admin and Manager only
    db: Session = Depends(get_db)
):
    """Handle partial shipment of a specific item - Only Admin and Manager can process shipments"""
    sales_order = db.query(SalesOrder).filter(SalesOrder.id == so_id).first()
    if not sales_order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    # Find the specific item
    order_item = db.query(SalesOrderItem).filter(
        SalesOrderItem.id == item_id,
        SalesOrderItem.sales_order_id == so_id
    ).first()
    
    if not order_item:
        raise HTTPException(status_code=404, detail="Order item not found")
    
    if quantity_shipped > order_item.quantity_ordered - order_item.quantity_shipped:
        raise HTTPException(status_code=400, detail="Quantity exceeds remaining order amount")
    
    if order_item.inventory_item_id:
        inventory_item = db.query(InventoryItem).filter(InventoryItem.id == order_item.inventory_item_id).first()
        if inventory_item and inventory_item.quantity_available >= quantity_shipped:
            # Reduce available quantity
            inventory_item.quantity_available -= quantity_shipped
            order_item.quantity_shipped += quantity_shipped
            
            # Create stock movement record
            stock_movement = StockMovement(
                product_id=order_item.product_id,
                inventory_item_id=order_item.inventory_item_id,
                movement_type="out",
                quantity=-quantity_shipped,
                reference_type="sales_order",
                reference_id=sales_order.id,
                reference_number=sales_order.order_number,
                notes=f"Partial shipment: {quantity_shipped} units sold to {sales_order.customer.name} - Order: {sales_order.order_number}",
                created_by=current_user.id
            )
            db.add(stock_movement)
            
            # Update order status if all items are shipped
            all_shipped = all(item.quantity_shipped >= item.quantity_ordered for item in sales_order.items)
            if all_shipped:
                sales_order.status = "shipped"
            
            db.commit()
            return RedirectResponse(url=f"/sales-orders/{so_id}", status_code=302)
        else:
            raise HTTPException(status_code=400, detail="Insufficient stock for partial shipment")
    else:
        raise HTTPException(status_code=400, detail="No inventory item linked to this order item")