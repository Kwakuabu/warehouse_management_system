# app/routes/reports.py
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, extract
from app.database import get_db
from app.models.models import (
    Product, InventoryItem, PurchaseOrder, SalesOrder, 
    Customer, Vendor, StockMovement, Category, User
)
from app.utils.auth import check_user_role_from_cookie, get_current_active_user_from_cookie
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Reports dashboard - Manager and Admin only
@router.get("/", response_class=HTMLResponse)
async def reports_dashboard(
    request: Request, 
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Display reports dashboard with overview and quick reports - Manager and Admin only"""
    
    # Get date range (default to last 30 days)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    # Calculate key metrics
    metrics = calculate_key_metrics(db, start_date, end_date)
    
    # Get recent activities for dashboard
    recent_sales = get_recent_sales(db, limit=5)
    recent_purchases = get_recent_purchases(db, limit=5)
    top_products = get_top_products(db, start_date, end_date, limit=5)
    top_customers = get_top_customers(db, start_date, end_date, limit=5)
    
    return templates.TemplateResponse("reports/dashboard.html", {
        "request": request,
        "metrics": metrics,
        "recent_sales": recent_sales,
        "recent_purchases": recent_purchases,
        "top_products": top_products,
        "top_customers": top_customers,
        "start_date": start_date,
        "end_date": end_date,
        "current_user": current_user
    })

# Financial reports
@router.get("/financial", response_class=HTMLResponse)
async def financial_reports(
    request: Request, 
    start_date: str = Query(None),
    end_date: str = Query(None),
    report_type: str = Query("summary"),
    db: Session = Depends(get_db)
):
    """Display financial reports"""
    
    # Parse dates
    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start_date = datetime.utcnow() - timedelta(days=30)
    
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end_date = datetime.utcnow()
    
    # Generate financial data based on report type
    if report_type == "summary":
        financial_data = generate_financial_summary(db, start_date, end_date)
    elif report_type == "revenue":
        financial_data = generate_revenue_report(db, start_date, end_date)
    elif report_type == "expenses":
        financial_data = generate_expense_report(db, start_date, end_date)
    elif report_type == "profit":
        financial_data = generate_profit_report(db, start_date, end_date)
    else:
        financial_data = generate_financial_summary(db, start_date, end_date)
    
    return templates.TemplateResponse("reports/financial.html", {
        "request": request,
        "financial_data": financial_data,
        "start_date": start_date,
        "end_date": end_date,
        "report_type": report_type,
        "current_user": current_user
    })

# Inventory reports
@router.get("/inventory", response_class=HTMLResponse)
async def inventory_reports(
    request: Request,
    report_type: str = Query("overview"),
    category_id: int = Query(None),
    db: Session = Depends(get_db)
):
    """Display inventory reports"""
    
    if report_type == "overview":
        inventory_data = generate_inventory_overview(db)
    elif report_type == "low_stock":
        inventory_data = generate_low_stock_report(db)
    elif report_type == "expiry":
        inventory_data = generate_expiry_report(db)
    elif report_type == "movements":
        inventory_data = generate_movement_report(db)
    elif report_type == "value":
        inventory_data = generate_inventory_value_report(db)
    else:
        inventory_data = generate_inventory_overview(db)
    
    # Get categories for filter
    categories = db.query(Category).all()
    
    return templates.TemplateResponse("reports/inventory.html", {
        "request": request,
        "inventory_data": inventory_data,
        "categories": categories,
        "report_type": report_type,
        "selected_category": category_id,
        "current_user": current_user
    })

# Customer analytics
@router.get("/customers", response_class=HTMLResponse)
async def customer_analytics(
    request: Request,
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db)
):
    """Display customer analytics"""
    
    # Parse dates
    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start_date = datetime.utcnow() - timedelta(days=90)
    
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end_date = datetime.utcnow()
    
    customer_data = generate_customer_analytics(db, start_date, end_date)
    
    return templates.TemplateResponse("reports/customers.html", {
        "request": request,
        "customer_data": customer_data,
        "start_date": start_date,
        "end_date": end_date,
        "current_user": current_user
    })

# Vendor analytics
@router.get("/vendors", response_class=HTMLResponse)
async def vendor_analytics(
    request: Request,
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db)
):
    """Display vendor analytics"""
    
    # Parse dates
    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start_date = datetime.utcnow() - timedelta(days=90)
    
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end_date = datetime.utcnow()
    
    vendor_data = generate_vendor_analytics(db, start_date, end_date)
    
    return templates.TemplateResponse("reports/vendors.html", {
        "request": request,
        "vendor_data": vendor_data,
        "start_date": start_date,
        "end_date": end_date,
        "current_user": current_user
    })

# API endpoints for data
@router.get("/api/financial-summary")
async def api_financial_summary(
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db)
):
    """API endpoint for financial summary"""
    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start_date = datetime.utcnow() - timedelta(days=30)
    
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end_date = datetime.utcnow()
    
    data = generate_financial_summary(db, start_date, end_date)
    return JSONResponse(content=data)

@router.get("/api/inventory-summary")
async def api_inventory_summary(db: Session = Depends(get_db)):
    """API endpoint for inventory summary"""
    data = generate_inventory_overview(db)
    return JSONResponse(content=data)

@router.get("/api/customer-analytics")
async def api_customer_analytics(
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db)
):
    """API endpoint for customer analytics"""
    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start_date = datetime.utcnow() - timedelta(days=90)
    
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end_date = datetime.utcnow()
    
    data = generate_customer_analytics(db, start_date, end_date)
    return JSONResponse(content=data)

# Helper functions
def calculate_key_metrics(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Calculate key business metrics"""
    
    # Revenue
    total_revenue = db.query(func.sum(SalesOrder.total_amount)).filter(
        SalesOrder.order_date.between(start_date, end_date),
        SalesOrder.status.in_(["delivered", "shipped"])
    ).scalar() or 0
    
    # Expenses
    total_expenses = db.query(func.sum(PurchaseOrder.total_amount)).filter(
        PurchaseOrder.order_date.between(start_date, end_date),
        PurchaseOrder.status.in_(["received", "shipped"])
    ).scalar() or 0
    
    # Profit
    gross_profit = float(total_revenue - total_expenses)
    profit_margin = (gross_profit / float(total_revenue)) * 100 if total_revenue > 0 else 0
    
    # Orders
    total_sales_orders = db.query(SalesOrder).filter(
        SalesOrder.order_date.between(start_date, end_date)
    ).count()
    
    total_purchase_orders = db.query(PurchaseOrder).filter(
        PurchaseOrder.order_date.between(start_date, end_date)
    ).count()
    
    # Inventory
    total_inventory_value = db.query(func.sum(
        InventoryItem.quantity_available * InventoryItem.cost_price
    )).scalar() or 0
    
    # Customers
    active_customers = db.query(Customer).filter(
        Customer.id.in_(
            db.query(SalesOrder.customer_id).filter(
                SalesOrder.order_date.between(start_date, end_date)
            ).distinct()
        )
    ).count()
    
    return {
        "total_revenue": float(total_revenue),
        "total_expenses": float(total_expenses),
        "gross_profit": gross_profit,
        "profit_margin": round(profit_margin, 2),
        "total_sales_orders": total_sales_orders,
        "total_purchase_orders": total_purchase_orders,
        "total_inventory_value": float(total_inventory_value),
        "active_customers": active_customers
    }

def get_recent_sales(db: Session, limit: int = 5) -> List[Dict]:
    """Get recent sales orders"""
    sales = db.query(SalesOrder).order_by(SalesOrder.order_date.desc()).limit(limit).all()
    return [
        {
            "id": sale.id,
            "order_number": sale.order_number,
            "customer_name": sale.customer.name if sale.customer else "Unknown",
            "total_amount": float(sale.total_amount),
            "status": sale.status,
            "order_date": sale.order_date
        }
        for sale in sales
    ]

def get_recent_purchases(db: Session, limit: int = 5) -> List[Dict]:
    """Get recent purchase orders"""
    purchases = db.query(PurchaseOrder).order_by(PurchaseOrder.order_date.desc()).limit(limit).all()
    return [
        {
            "id": purchase.id,
            "po_number": purchase.po_number,
            "vendor_name": purchase.vendor.name if purchase.vendor else "Unknown",
            "total_amount": float(purchase.total_amount),
            "status": purchase.status,
            "order_date": purchase.order_date
        }
        for purchase in purchases
    ]

def get_top_products(db: Session, start_date: datetime, end_date: datetime, limit: int = 5) -> List[Dict]:
    """Get top selling products"""
    # This is a simplified version - in a real system you'd aggregate from sales order items
    products = db.query(Product).limit(limit).all()
    return [
        {
            "id": product.id,
            "name": product.name,
            "sku": product.sku,
            "total_sales": 0,  # Would be calculated from sales data
            "revenue": 0  # Would be calculated from sales data
        }
        for product in products
    ]

def get_top_customers(db: Session, start_date: datetime, end_date: datetime, limit: int = 5) -> List[Dict]:
    """Get top customers by revenue"""
    customers = db.query(Customer).limit(limit).all()
    return [
        {
            "id": customer.id,
            "name": customer.name,
            "total_orders": 0,  # Would be calculated from sales data
            "total_revenue": 0  # Would be calculated from sales data
        }
        for customer in customers
    ]

def generate_financial_summary(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Generate financial summary report"""
    metrics = calculate_key_metrics(db, start_date, end_date)
    
    # Monthly trends
    monthly_data = []
    current_date = start_date
    while current_date <= end_date:
        month_start = current_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_revenue = db.query(func.sum(SalesOrder.total_amount)).filter(
            SalesOrder.order_date.between(month_start, month_end),
            SalesOrder.status.in_(["delivered", "shipped"])
        ).scalar() or 0
        
        month_expenses = db.query(func.sum(PurchaseOrder.total_amount)).filter(
            PurchaseOrder.order_date.between(month_start, month_end),
            PurchaseOrder.status.in_(["received", "shipped"])
        ).scalar() or 0
        
        monthly_data.append({
            "month": current_date.strftime("%Y-%m"),
            "revenue": float(month_revenue),
            "expenses": float(month_expenses),
            "profit": float(month_revenue - month_expenses)
        })
        
        current_date = (current_date + timedelta(days=32)).replace(day=1)
    
    return {
        "metrics": metrics,
        "monthly_data": monthly_data,
        "period": {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d")
        }
    }

def generate_revenue_report(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Generate detailed revenue report"""
    # Implementation would include detailed revenue breakdown
    return {"message": "Revenue report data"}

def generate_expense_report(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Generate detailed expense report"""
    # Implementation would include detailed expense breakdown
    return {"message": "Expense report data"}

def generate_profit_report(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Generate detailed profit report"""
    # Implementation would include detailed profit analysis
    return {"message": "Profit report data"}

def generate_inventory_overview(db: Session) -> Dict[str, Any]:
    """Generate inventory overview report"""
    total_items = db.query(InventoryItem).count()
    total_value = db.query(func.sum(
        InventoryItem.quantity_available * InventoryItem.cost_price
    )).scalar() or 0
    
    low_stock_items = db.query(InventoryItem).join(Product).filter(
        InventoryItem.quantity_available <= Product.reorder_point,
        InventoryItem.quantity_available > 0
    ).count()
    
    expiring_soon = db.query(InventoryItem).filter(
        InventoryItem.expiry_date.isnot(None),
        InventoryItem.expiry_date <= datetime.utcnow() + timedelta(days=30),
        InventoryItem.expiry_date > datetime.utcnow(),
        InventoryItem.quantity_available > 0
    ).count()
    
    return {
        "total_items": total_items,
        "total_value": float(total_value),
        "low_stock_items": low_stock_items,
        "expiring_soon": expiring_soon
    }

def generate_low_stock_report(db: Session) -> Dict[str, Any]:
    """Generate low stock report"""
    # Implementation would include detailed low stock analysis
    return {"message": "Low stock report data"}

def generate_expiry_report(db: Session) -> Dict[str, Any]:
    """Generate expiry report"""
    # Implementation would include detailed expiry analysis
    return {"message": "Expiry report data"}

def generate_movement_report(db: Session) -> Dict[str, Any]:
    """Generate stock movement report"""
    # Implementation would include detailed movement analysis
    return {"message": "Movement report data"}

def generate_inventory_value_report(db: Session) -> Dict[str, Any]:
    """Generate inventory value report"""
    # Implementation would include detailed value analysis
    return {"message": "Inventory value report data"}

def generate_customer_analytics(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Generate customer analytics"""
    # Implementation would include detailed customer analysis
    return {"message": "Customer analytics data"}

def generate_vendor_analytics(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Generate vendor analytics"""
    # Implementation would include detailed vendor analysis
    return {"message": "Vendor analytics data"} 