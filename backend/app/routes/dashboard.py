# app/routes/dashboard.py
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from app.database import get_db
from app.models.models import (
    Product, InventoryItem, PurchaseOrder, SalesOrder, 
    Customer, Vendor, StockMovement, Alert, User
)
from app.utils.auth import get_current_active_user_from_cookie
from datetime import datetime, timedelta
from typing import Dict, Any

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request, 
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Main dashboard with role-based data - All authenticated users"""
    
    # Get current date for calculations
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    
    # Calculate real-time statistics based on user role
    if current_user.role in ["admin", "manager"]:
        # Full warehouse statistics for admin and manager
        stats = calculate_dashboard_stats(db, now, thirty_days_ago)
        recent_activities = get_recent_activities(db)
        alerts = get_active_alerts(db)
        template_data = {
            "request": request,
            "stats": stats,
            "recent_activities": recent_activities,
            "alerts": alerts,
            "now": now,
            "current_user": current_user,
            "user_role": current_user.role
        }
    else:
        # Customer-facing dashboard for staff (hospital buyers)
        stats = calculate_staff_dashboard_stats(db, now, thirty_days_ago, current_user)
        recent_activities = get_staff_recent_activities(db, current_user)
        available_products = get_available_products_for_staff(db)
        template_data = {
            "request": request,
            "stats": stats,
            "recent_activities": recent_activities,
            "available_products": available_products,
            "now": now,
            "current_user": current_user,
            "user_role": current_user.role
        }
    
    return templates.TemplateResponse("dashboard.html", template_data)

@router.get("/api/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """API endpoint for dashboard statistics"""
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    
    stats = calculate_dashboard_stats(db, now, thirty_days_ago)
    return stats

def calculate_dashboard_stats(db: Session, now: datetime, thirty_days_ago: datetime) -> Dict[str, Any]:
    """Calculate comprehensive dashboard statistics"""
    
    # Product statistics
    total_products = db.query(Product).filter(Product.is_active == True).count()
    active_products = db.query(Product).filter(
        Product.is_active == True,
        Product.id.in_(
            db.query(InventoryItem.product_id).filter(InventoryItem.quantity_available > 0)
        )
    ).count()
    
    # Inventory statistics
    inventory_items = db.query(InventoryItem).filter(InventoryItem.quantity_available > 0).all()
    total_inventory_value = sum([item.quantity_available * item.cost_price for item in inventory_items])
    
    # Low stock alerts
    low_stock_items = db.query(InventoryItem).join(Product).filter(
        InventoryItem.quantity_available <= Product.reorder_point,
        InventoryItem.quantity_available > 0
    ).count()
    
    # Expiring soon alerts
    expiring_soon = db.query(InventoryItem).filter(
        InventoryItem.expiry_date.isnot(None),
        InventoryItem.expiry_date <= now + timedelta(days=30),
        InventoryItem.expiry_date > now,
        InventoryItem.quantity_available > 0
    ).count()
    
    # Pending user approvals (admin/manager only)
    pending_users = db.query(User).filter(
        User.requires_approval == True,
        User.is_approved == False
    ).count()
    
    # Order statistics
    total_purchase_orders = db.query(PurchaseOrder).count()
    pending_purchase_orders = db.query(PurchaseOrder).filter(
        PurchaseOrder.status.in_(["pending", "confirmed", "shipped"])
    ).count()
    
    total_sales_orders = db.query(SalesOrder).count()
    pending_sales_orders = db.query(SalesOrder).filter(
        SalesOrder.status.in_(["pending", "confirmed", "shipped"])
    ).count()
    
    # Customer statistics
    total_customers = db.query(Customer).filter(Customer.is_active == True).count()
    active_customers = db.query(Customer).filter(
        Customer.is_active == True,
        Customer.id.in_(
            db.query(SalesOrder.customer_id).filter(
                SalesOrder.order_date >= thirty_days_ago
            )
        )
    ).count()
    
    # Vendor statistics
    total_vendors = db.query(Vendor).filter(Vendor.is_active == True).count()
    
    # Monthly trends
    monthly_purchase_value = db.query(func.sum(PurchaseOrder.total_amount)).filter(
        PurchaseOrder.order_date >= thirty_days_ago,
        PurchaseOrder.status.in_(["received", "shipped"])
    ).scalar() or 0
    
    monthly_sales_value = db.query(func.sum(SalesOrder.total_amount)).filter(
        SalesOrder.order_date >= thirty_days_ago,
        SalesOrder.status.in_(["delivered", "shipped"])
    ).scalar() or 0
    
    # Stock movements
    recent_movements = db.query(StockMovement).filter(
        StockMovement.created_at >= thirty_days_ago
    ).count()
    
    return {
        "total_products": total_products,
        "active_products": active_products,
        "total_inventory_value": float(total_inventory_value),
        "low_stock_alerts": low_stock_items,
        "expiring_soon": expiring_soon,
        "total_purchase_orders": total_purchase_orders,
        "pending_purchase_orders": pending_purchase_orders,
        "total_sales_orders": total_sales_orders,
        "pending_sales_orders": pending_sales_orders,
        "total_customers": total_customers,
        "active_customers": active_customers,
        "total_vendors": total_vendors,
        "monthly_purchase_value": float(monthly_purchase_value),
        "monthly_sales_value": float(monthly_sales_value),
        "recent_movements": recent_movements,
        "pending_users": pending_users,
        "last_updated": now.isoformat()
    }

def get_recent_activities(db: Session, limit: int = 10):
    """Get recent system activities"""
    activities = []
    
    # Recent stock movements
    movements = db.query(StockMovement).order_by(
        desc(StockMovement.created_at)
    ).limit(limit).all()
    
    for movement in movements:
        product = db.query(Product).filter(Product.id == movement.product_id).first()
        if product:
            activities.append({
                "type": "stock_movement",
                "message": f"{movement.movement_type.title()} {abs(movement.quantity)} units of {product.name}",
                "timestamp": movement.created_at,
                "icon": "fas fa-boxes"
            })
    
    # Recent purchase orders
    recent_purchase_orders = db.query(PurchaseOrder).order_by(
        desc(PurchaseOrder.order_date)
    ).limit(5).all()
    
    for order in recent_purchase_orders:
        vendor = db.query(Vendor).filter(Vendor.id == order.vendor_id).first()
        if vendor:
            activities.append({
                "type": "purchase_order",
                "message": f"Purchase order {order.po_number} created for {vendor.name}",
                "timestamp": order.order_date,
                "icon": "fas fa-shopping-cart"
            })
    
    # Recent sales orders
    recent_sales_orders = db.query(SalesOrder).order_by(
        desc(SalesOrder.order_date)
    ).limit(5).all()
    
    for order in recent_sales_orders:
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        if customer:
            activities.append({
                "type": "sales_order",
                "message": f"Sales order {order.order_number} created for {customer.name}",
                "timestamp": order.order_date,
                "icon": "fas fa-truck"
            })
    
    # Sort by timestamp and return top activities
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    return activities[:limit]

def get_active_alerts(db: Session, limit: int = 5):
    """Get active system alerts"""
    alerts = db.query(Alert).filter(
        Alert.is_acknowledged == False
    ).order_by(desc(Alert.created_at)).limit(limit).all()
    
    return alerts

def calculate_staff_dashboard_stats(db: Session, now: datetime, thirty_days_ago: datetime, current_user: User) -> Dict[str, Any]:
    """Calculate customer-facing dashboard statistics for staff users (hospital buyers)"""
    
    # Check if staff user has hospital assigned
    if not current_user.hospital_id:
        return {
            "total_products": 0,
            "available_products": 0,
            "products_with_stock": 0,
            "total_inventory_value": 0.0,
            "total_sales_orders": 0,
            "pending_sales_orders": 0,
            "total_inventory_items": 0,
            "recent_movements": 0,
            "last_updated": now.isoformat()
        }
    
    # Get available products (what they can order from warehouse)
    total_products = db.query(Product).filter(Product.is_active == True).count()
    available_products = db.query(Product).filter(
        Product.is_active == True,
        Product.id.in_(
            db.query(InventoryItem.product_id).filter(InventoryItem.quantity_available > 0)
        )
    ).count()
    
    # Get products with stock (what they can actually order)
    products_with_stock = db.query(Product).join(InventoryItem).filter(
        Product.is_active == True,
        InventoryItem.quantity_available > 0,
        InventoryItem.status == "available"
    ).distinct().count()
    
    # Get their hospital's sales orders only
    total_sales_orders = db.query(SalesOrder).filter(
        SalesOrder.customer_id == current_user.hospital_id
    ).count()
    pending_sales_orders = db.query(SalesOrder).filter(
        SalesOrder.customer_id == current_user.hospital_id,
        SalesOrder.status.in_(["pending", "confirmed", "shipped"])
    ).count()
    
    # Get their hospital's inventory (from HospitalInventory table)
    from app.models.models import HospitalInventory
    total_inventory_items = db.query(HospitalInventory).filter(
        HospitalInventory.hospital_id == current_user.hospital_id
    ).count()
    
    # Calculate total value of their hospital's inventory
    hospital_inventory = db.query(HospitalInventory).filter(
        HospitalInventory.hospital_id == current_user.hospital_id
    ).all()
    
    total_inventory_value = 0
    for item in hospital_inventory:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product and product.unit_price:
            total_inventory_value += item.current_stock * float(product.unit_price)
    
    # Get recent stock movements for their hospital only
    recent_movements = db.query(StockMovement).filter(
        StockMovement.created_at >= thirty_days_ago,
        StockMovement.movement_type.in_(["received", "available"])
    ).count()  # Note: StockMovement doesn't have hospital_id, so this is warehouse-wide
    
    return {
        "total_products": total_products,
        "available_products": available_products,
        "products_with_stock": products_with_stock,
        "total_inventory_value": float(total_inventory_value),
        "total_sales_orders": total_sales_orders,
        "pending_sales_orders": pending_sales_orders,
        "total_inventory_items": total_inventory_items,
        "recent_movements": recent_movements,
        "last_updated": now.isoformat()
    }

def get_staff_recent_activities(db: Session, current_user: User, limit: int = 10):
    """Get customer-facing recent activities for staff users (hospital buyers)"""
    activities = []
    
    # Check if staff user has hospital assigned
    if not current_user.hospital_id:
        return activities
    
    # Recent stock movements (what's been received/available for ordering)
    # Note: StockMovement doesn't have hospital_id, so this shows warehouse-wide movements
    movements = db.query(StockMovement).filter(
        StockMovement.movement_type.in_(["received", "available"])
    ).order_by(desc(StockMovement.created_at)).limit(limit//2).all()
    
    for movement in movements:
        product = db.query(Product).filter(Product.id == movement.product_id).first()
        if product:
            activities.append({
                "type": "stock_movement",
                "message": f"{movement.movement_type.title()} {abs(movement.quantity)} units of {product.name}",
                "timestamp": movement.created_at,
                "icon": "fas fa-boxes"
            })
    
    # Recent sales orders (their hospital's orders only)
    recent_sales_orders = db.query(SalesOrder).filter(
        SalesOrder.customer_id == current_user.hospital_id
    ).order_by(desc(SalesOrder.order_date)).limit(limit//2).all()
    
    for order in recent_sales_orders:
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        if customer:
            activities.append({
                "type": "sales_order",
                "message": f"Order {order.order_number} - {order.status.title()}",
                "timestamp": order.order_date,
                "icon": "fas fa-shopping-cart"
            })
    
    # Sort by timestamp and return top activities
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    return activities[:limit]

def get_available_products_for_staff(db: Session, limit: int = 8):
    """Get products available for ordering by staff users"""
    # Get products with available stock from warehouse
    # Staff users can see all available products in warehouse, but their orders are restricted to their hospital
    available_products = db.query(Product).join(InventoryItem).filter(
        Product.is_active == True,
        InventoryItem.quantity_available > 0,
        InventoryItem.status == "available"
    ).distinct().limit(limit).all()
    
    return available_products 