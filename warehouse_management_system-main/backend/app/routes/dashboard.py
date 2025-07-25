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
    """Main dashboard with real-time statistics - All authenticated users"""
    
    # Get current date for calculations
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    
    # Calculate real-time statistics based on user role
    if current_user.role in ["admin", "manager"]:
        # Full statistics for admin and manager
        stats = calculate_dashboard_stats(db, now, thirty_days_ago)
        recent_activities = get_recent_activities(db)
        alerts = get_active_alerts(db)
    else:
        # Limited statistics for staff
        stats = calculate_staff_dashboard_stats(db, now, thirty_days_ago)
        recent_activities = get_staff_recent_activities(db)
        alerts = []  # Staff don't see alerts
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_activities": recent_activities,
        "alerts": alerts,
        "now": now,
        "current_user": current_user,
        "user_role": current_user.role
    })

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

def calculate_staff_dashboard_stats(db: Session, now: datetime, thirty_days_ago: datetime) -> Dict[str, Any]:
    """Calculate limited dashboard statistics for staff users"""
    
    # Limited product statistics
    total_products = db.query(Product).filter(Product.is_active == True).count()
    active_products = db.query(Product).filter(
        Product.is_active == True,
        Product.id.in_(
            db.query(InventoryItem.product_id).filter(InventoryItem.quantity_available > 0)
        )
    ).count()
    
    # Basic inventory statistics
    inventory_items = db.query(InventoryItem).filter(InventoryItem.quantity_available > 0).all()
    total_inventory_value = sum([item.quantity_available * item.cost_price for item in inventory_items])
    
    # Basic order statistics (staff can see counts but not sensitive financial data)
    total_purchase_orders = db.query(PurchaseOrder).count()
    pending_purchase_orders = db.query(PurchaseOrder).filter(
        PurchaseOrder.status.in_(["pending", "confirmed", "shipped"])
    ).count()
    
    total_sales_orders = db.query(SalesOrder).count()
    pending_sales_orders = db.query(SalesOrder).filter(
        SalesOrder.status.in_(["pending", "confirmed", "shipped"])
    ).count()
    
    # Basic customer statistics
    total_customers = db.query(Customer).filter(Customer.is_active == True).count()
    
    # Basic vendor statistics
    total_vendors = db.query(Vendor).filter(Vendor.is_active == True).count()
    
    # Limited stock movements
    recent_movements = db.query(StockMovement).filter(
        StockMovement.created_at >= thirty_days_ago
    ).count()
    
    return {
        "total_products": total_products,
        "active_products": active_products,
        "total_inventory_value": float(total_inventory_value),
        "low_stock_alerts": 0,  # Staff don't see alerts
        "expiring_soon": 0,  # Staff don't see alerts
        "total_purchase_orders": total_purchase_orders,
        "pending_purchase_orders": pending_purchase_orders,
        "total_sales_orders": total_sales_orders,
        "pending_sales_orders": pending_sales_orders,
        "total_customers": total_customers,
        "active_customers": 0,  # Staff don't see customer activity
        "total_vendors": total_vendors,
        "monthly_purchase_value": 0.0,  # Staff don't see financial data
        "monthly_sales_value": 0.0,  # Staff don't see financial data
        "recent_movements": recent_movements,
        "last_updated": now.isoformat()
    }

def get_staff_recent_activities(db: Session, limit: int = 10):
    """Get limited recent activities for staff users"""
    activities = []
    
    # Recent stock movements (staff can see these)
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
    
    # Recent sales orders (staff can see these)
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