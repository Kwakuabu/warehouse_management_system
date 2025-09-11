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
from app.utils.auth import check_user_role_from_cookie, get_current_active_user_from_cookie, check_user_roles_from_cookie
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Reports dashboard - Manager and Admin only
@router.get("/", response_class=HTMLResponse)
async def reports_dashboard(
    request: Request, 
    current_user: User = Depends(check_user_roles_from_cookie(["admin", "manager"])),
    db: Session = Depends(get_db)
):
    """Display reports dashboard with overview and quick reports - Manager and Admin only"""
    
    # Get date range (default to last 30 days)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    # Calculate comprehensive metrics for dashboard
    metrics = calculate_comprehensive_metrics(db, start_date, end_date)
    
    # Get chart data
    chart_data = get_chart_data(db, start_date, end_date)
    
    # Get recent activities for dashboard
    recent_sales = get_recent_sales(db, limit=5)
    recent_purchases = get_recent_purchases(db, limit=5)
    top_products = get_top_products(db, start_date, end_date, limit=5)
    top_customers = get_top_customers(db, start_date, end_date, limit=5)
    
    return templates.TemplateResponse("reports/dashboard.html", {
        "request": request,
        "metrics": metrics,
        "chart_data": chart_data,
        "recent_sales": recent_sales,
        "recent_purchases": recent_purchases,
        "top_products": top_products,
        "top_customers": top_customers,
        "start_date": start_date,
        "end_date": end_date,
        "current_user": current_user,
        "user_role": current_user.role
    })

# Financial reports
@router.get("/financial", response_class=HTMLResponse)
async def financial_reports(
    request: Request, 
    start_date: str = Query(None),
    end_date: str = Query(None),
    report_type: str = Query("summary"),
    current_user: User = Depends(check_user_roles_from_cookie(["staff", "manager"])),
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
    
    # For staff users, filter by their hospital
    if current_user.role == "staff" and current_user.hospital_id:
        # Generate hospital-specific financial data
        if report_type == "summary":
            financial_data = generate_hospital_financial_summary(db, start_date, end_date, current_user.hospital_id)
        elif report_type == "revenue":
            financial_data = generate_hospital_revenue_report(db, start_date, end_date, current_user.hospital_id)
        elif report_type == "expenses":
            financial_data = generate_hospital_expense_report(db, start_date, end_date, current_user.hospital_id)
        elif report_type == "profit":
            financial_data = generate_hospital_profit_report(db, start_date, end_date, current_user.hospital_id)
        else:
            financial_data = generate_hospital_financial_summary(db, start_date, end_date, current_user.hospital_id)
    else:
        # Generate full financial data for admin/manager
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
    current_user: User = Depends(check_user_roles_from_cookie(["staff", "manager"])),
    db: Session = Depends(get_db)
):
    """Display inventory reports"""
    
    # For staff users, filter by their hospital
    if current_user.role == "staff" and current_user.hospital_id:
        # Generate hospital-specific inventory data
        if report_type == "overview":
            inventory_data = generate_hospital_inventory_overview(db, current_user.hospital_id)
        elif report_type == "low_stock":
            inventory_data = generate_hospital_low_stock_report(db, current_user.hospital_id)
        elif report_type == "expiry":
            inventory_data = generate_hospital_expiry_report(db, current_user.hospital_id)
        elif report_type == "movements":
            inventory_data = generate_hospital_movement_report(db, current_user.hospital_id)
        elif report_type == "value":
            inventory_data = generate_hospital_inventory_value_report(db, current_user.hospital_id)
        else:
            inventory_data = generate_hospital_inventory_overview(db, current_user.hospital_id)
    else:
        # Generate full inventory data for admin/manager
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
    current_user: User = Depends(check_user_roles_from_cookie(["staff", "manager"])),
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
    
    # For staff users, show only their hospital's data
    if current_user.role == "staff" and current_user.hospital_id:
        customer_data = generate_hospital_customer_analytics(db, start_date, end_date, current_user.hospital_id)
    else:
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
    current_user: User = Depends(check_user_roles_from_cookie(["staff", "manager"])),
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
    
    # For staff users, show only vendors related to their hospital's orders
    if current_user.role == "staff" and current_user.hospital_id:
        vendor_data = generate_hospital_vendor_analytics(db, start_date, end_date, current_user.hospital_id)
    else:
        vendor_data = generate_vendor_analytics(db, start_date, end_date)
    
    return templates.TemplateResponse("reports/vendors.html", {
        "request": request,
        "vendor_data": vendor_data,
        "start_date": start_date,
        "end_date": end_date,
        "current_user": current_user
    })

# Sales reports
@router.get("/sales", response_class=HTMLResponse)
async def sales_report(
    request: Request,
    start_date: str = Query(None),
    end_date: str = Query(None),
    current_user: User = Depends(check_user_roles_from_cookie(["staff", "manager"])),
    db: Session = Depends(get_db)
):
    """Display sales report with summary and recent sales orders"""
    # Parse dates
    if start_date:
        start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start_date_dt = datetime.utcnow() - timedelta(days=30)
    if end_date:
        end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end_date_dt = datetime.utcnow()

    # For staff users, show only their hospital's sales data
    if current_user.role == "staff" and current_user.hospital_id:
        # Total sales and revenue in period for hospital only
        total_sales_orders = db.query(SalesOrder).filter(
            SalesOrder.customer_id == current_user.hospital_id,
            SalesOrder.order_date.between(start_date_dt, end_date_dt)
        ).count()
        total_revenue = db.query(func.sum(SalesOrder.total_amount)).filter(
            SalesOrder.customer_id == current_user.hospital_id,
            SalesOrder.order_date.between(start_date_dt, end_date_dt),
            SalesOrder.status.in_(["delivered", "shipped"])
        ).scalar() or 0

        # Recent sales orders for hospital only
        recent_sales = get_hospital_recent_sales(db, current_user.hospital_id, limit=10)
    else:
        # Total sales and revenue in period for all
        total_sales_orders = db.query(SalesOrder).filter(
            SalesOrder.order_date.between(start_date_dt, end_date_dt)
        ).count()
        total_revenue = db.query(func.sum(SalesOrder.total_amount)).filter(
            SalesOrder.order_date.between(start_date_dt, end_date_dt),
            SalesOrder.status.in_(["delivered", "shipped"])
        ).scalar() or 0

        # Recent sales orders for all
        recent_sales = get_recent_sales(db, limit=10)

    return templates.TemplateResponse("reports/sales.html", {
        "request": request,
        "total_sales_orders": total_sales_orders,
        "total_revenue": total_revenue,
        "recent_sales": recent_sales,
        "start_date": start_date_dt,
        "end_date": end_date_dt,
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

@router.get("/api/dashboard-data")
async def api_dashboard_data(
    days: int = Query(30, description="Number of days to look back"),
    db: Session = Depends(get_db)
):
    """API endpoint for dashboard chart data"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    chart_data = get_chart_data(db, start_date, end_date)
    return JSONResponse(content=chart_data)

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
def calculate_comprehensive_metrics(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Calculate comprehensive business metrics for dashboard"""
    
    # Revenue metrics
    monthly_revenue = db.query(func.sum(SalesOrder.total_amount)).filter(
        SalesOrder.order_date.between(start_date, end_date),
        SalesOrder.status.in_(["delivered", "shipped"])
    ).scalar() or 0
    
    # Previous period for comparison
    period_days = (end_date - start_date).days
    previous_start = start_date - timedelta(days=period_days)
    previous_end = start_date
    
    previous_revenue = db.query(func.sum(SalesOrder.total_amount)).filter(
        SalesOrder.order_date.between(previous_start, previous_end),
        SalesOrder.status.in_(["delivered", "shipped"])
    ).scalar() or 0
    
    # Calculate growth rate - ensure decimal values are converted to float
    revenue_growth = 0
    if previous_revenue > 0:
        revenue_growth = float(((monthly_revenue - previous_revenue) / previous_revenue) * 100)
    
    # Orders metrics
    total_orders = db.query(SalesOrder).filter(
        SalesOrder.order_date.between(start_date, end_date)
    ).count()
    
    previous_orders = db.query(SalesOrder).filter(
        SalesOrder.order_date.between(previous_start, previous_end)
    ).count()
    
    orders_growth = 0
    if previous_orders > 0:
        orders_growth = float(((total_orders - previous_orders) / previous_orders) * 100)
    
    # Inventory metrics
    total_inventory_value = db.query(func.sum(
        InventoryItem.quantity_available * InventoryItem.cost_price
    )).scalar() or 0
    
    # Profit metrics
    total_expenses = db.query(func.sum(PurchaseOrder.total_amount)).filter(
        PurchaseOrder.order_date.between(start_date, end_date),
        PurchaseOrder.status.in_(["received", "shipped"])
    ).scalar() or 0
    
    gross_profit = float(monthly_revenue - total_expenses)
    profit_margin = float((gross_profit / float(monthly_revenue)) * 100) if monthly_revenue > 0 else 0
    
    # Customer metrics
    total_customers = db.query(Customer).filter(Customer.is_active == True).count()
    active_customers = db.query(Customer).filter(
        Customer.id.in_(
            db.query(SalesOrder.customer_id).filter(
                SalesOrder.order_date.between(start_date, end_date)
            ).distinct()
        )
    ).count()
    
    previous_customers = db.query(Customer).filter(
        Customer.id.in_(
            db.query(SalesOrder.customer_id).filter(
                SalesOrder.order_date.between(previous_start, previous_end)
            ).distinct()
        )
    ).count()
    
    customer_growth = 0
    if previous_customers > 0:
        customer_growth = float(((active_customers - previous_customers) / previous_customers) * 100)
    
    # Overall growth rate - ensure all values are float before calculation
    overall_growth = (float(revenue_growth) + float(orders_growth) + float(customer_growth)) / 3
    
    return {
        "monthly_revenue": float(monthly_revenue),
        "total_orders": total_orders,
        "inventory_value": float(total_inventory_value),
        "profit_margin": round(profit_margin, 2),
        "total_customers": total_customers,
        "growth_rate": round(overall_growth, 2),
        "revenue_growth": round(revenue_growth, 2),
        "orders_growth": round(orders_growth, 2),
        "customer_growth": round(customer_growth, 2),
        "total_expenses": float(total_expenses),
        "gross_profit": gross_profit
    }

def get_chart_data(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get data for dashboard charts"""
    
    # Monthly revenue and expenses for the last 6 months
    chart_months = []
    revenue_data = []
    expenses_data = []
    
    current_date = start_date
    for i in range(6):
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
        
        chart_months.append(month_start.strftime("%b"))
        revenue_data.append(float(month_revenue))
        expenses_data.append(float(month_expenses))
        
        current_date = month_start - timedelta(days=1)
    
    # Orders status distribution
    orders_status = db.query(SalesOrder.status, func.count(SalesOrder.id)).filter(
        SalesOrder.order_date.between(start_date, end_date)
    ).group_by(SalesOrder.status).all()
    
    orders_labels = [status for status, count in orders_status]
    orders_data = [count for status, count in orders_status]
    
    # Inventory status distribution
    inventory_status = [
        ("In Stock", db.query(InventoryItem).filter(InventoryItem.quantity_available > 10).count()),
        ("Low Stock", db.query(InventoryItem).filter(
            InventoryItem.quantity_available.between(1, 10)
        ).count()),
        ("Out of Stock", db.query(InventoryItem).filter(InventoryItem.quantity_available == 0).count())
    ]
    
    inventory_labels = [status for status, count in inventory_status]
    inventory_data = [count for status, count in inventory_status]
    
    return {
        "months": chart_months,
        "revenue_data": revenue_data,
        "expenses_data": expenses_data,
        "orders_labels": orders_labels,
        "orders_data": orders_data,
        "inventory_labels": inventory_labels,
        "inventory_data": inventory_data
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
    metrics = calculate_comprehensive_metrics(db, start_date, end_date)
    
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
    # Calculate revenue metrics
    total_revenue = db.query(func.sum(SalesOrder.total_amount)).filter(
        SalesOrder.order_date.between(start_date, end_date),
        SalesOrder.status.in_(["delivered", "shipped"])
    ).scalar() or 0
    
    # Revenue by month
    monthly_revenue = []
    current_date = start_date
    while current_date <= end_date:
        month_start = current_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_rev = db.query(func.sum(SalesOrder.total_amount)).filter(
            SalesOrder.order_date.between(month_start, month_end),
            SalesOrder.status.in_(["delivered", "shipped"])
        ).scalar() or 0
        
        monthly_revenue.append({
            "month": current_date.strftime("%Y-%m"),
            "revenue": float(month_rev)
        })
        
        current_date = (current_date + timedelta(days=32)).replace(day=1)
    
    return {
        "total_revenue": float(total_revenue),
        "monthly_revenue": monthly_revenue,
        "report_type": "revenue"
    }

def generate_expense_report(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Generate detailed expense report"""
    # Calculate expense metrics
    total_expenses = db.query(func.sum(PurchaseOrder.total_amount)).filter(
        PurchaseOrder.order_date.between(start_date, end_date),
        PurchaseOrder.status.in_(["received", "shipped"])
    ).scalar() or 0
    
    # Expenses by month
    monthly_expenses = []
    current_date = start_date
    while current_date <= end_date:
        month_start = current_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_exp = db.query(func.sum(PurchaseOrder.total_amount)).filter(
            PurchaseOrder.order_date.between(month_start, month_end),
            PurchaseOrder.status.in_(["received", "shipped"])
        ).scalar() or 0
        
        monthly_expenses.append({
            "month": current_date.strftime("%Y-%m"),
            "expenses": float(month_exp)
        })
        
        current_date = (current_date + timedelta(days=32)).replace(day=1)
    
    return {
        "total_expenses": float(total_expenses),
        "monthly_expenses": monthly_expenses,
        "report_type": "expenses"
    }

def generate_profit_report(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Generate detailed profit report"""
    # Calculate profit metrics
    total_revenue = db.query(func.sum(SalesOrder.total_amount)).filter(
        SalesOrder.order_date.between(start_date, end_date),
        SalesOrder.status.in_(["delivered", "shipped"])
    ).scalar() or 0
    
    total_expenses = db.query(func.sum(PurchaseOrder.total_amount)).filter(
        PurchaseOrder.order_date.between(start_date, end_date),
        PurchaseOrder.status.in_(["received", "shipped"])
    ).scalar() or 0
    
    net_profit = float(total_revenue - total_expenses)
    profit_margin = (net_profit / float(total_revenue)) * 100 if total_revenue > 0 else 0
    
    return {
        "total_revenue": float(total_revenue),
        "total_expenses": float(total_expenses),
        "net_profit": net_profit,
        "profit_margin": round(profit_margin, 2),
        "report_type": "profit"
    }

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
    # Get low stock items
    low_stock_items = db.query(InventoryItem).join(Product).filter(
        InventoryItem.quantity_available <= Product.reorder_point,
        InventoryItem.quantity_available > 0
    ).count()
    
    # Get out of stock items
    out_of_stock_items = db.query(InventoryItem).filter(
        InventoryItem.quantity_available == 0
    ).count()
    
    # Get items below safety stock
    safety_stock_items = db.query(InventoryItem).join(Product).filter(
        InventoryItem.quantity_available < (Product.reorder_point * 0.5),
        InventoryItem.quantity_available > 0
    ).count()
    
    return {
        "low_stock_items": low_stock_items,
        "out_of_stock_items": out_of_stock_items,
        "safety_stock_items": safety_stock_items,
        "total_critical_items": low_stock_items + out_of_stock_items
    }

def generate_expiry_report(db: Session) -> Dict[str, Any]:
    """Generate expiry report"""
    # Get items expiring in 30 days
    expiring_30_days = db.query(InventoryItem).filter(
        InventoryItem.expiry_date.isnot(None),
        InventoryItem.expiry_date <= datetime.utcnow() + timedelta(days=30),
        InventoryItem.expiry_date > datetime.utcnow(),
        InventoryItem.quantity_available > 0
    ).count()
    
    # Get items expiring in 7 days
    expiring_7_days = db.query(InventoryItem).filter(
        InventoryItem.expiry_date.isnot(None),
        InventoryItem.expiry_date <= datetime.utcnow() + timedelta(days=7),
        InventoryItem.expiry_date > datetime.utcnow(),
        InventoryItem.quantity_available > 0
    ).count()
    
    # Get expired items
    expired_items = db.query(InventoryItem).filter(
        InventoryItem.expiry_date.isnot(None),
        InventoryItem.expiry_date <= datetime.utcnow(),
        InventoryItem.quantity_available > 0
    ).count()
    
    return {
        "expiring_30_days": expiring_30_days,
        "expiring_7_days": expiring_7_days,
        "expired_items": expired_items,
        "total_expiry_risk": expiring_30_days + expired_items
    }

def generate_movement_report(db: Session) -> Dict[str, Any]:
    """Generate stock movement report"""
    # Get recent stock movements
    recent_movements = db.query(StockMovement).order_by(
        StockMovement.created_at.desc()
    ).limit(10).count()
    
    # Get movements by type
    inbound_movements = db.query(StockMovement).filter(
        StockMovement.movement_type == "in"
    ).count()
    
    outbound_movements = db.query(StockMovement).filter(
        StockMovement.movement_type == "out"
    ).count()
    
    # Get average movement value
    avg_movement_value = db.query(func.avg(StockMovement.quantity * InventoryItem.cost_price)).join(
        InventoryItem, StockMovement.inventory_item_id == InventoryItem.id
    ).scalar() or 0
    
    return {
        "recent_movements": recent_movements,
        "inbound_movements": inbound_movements,
        "outbound_movements": outbound_movements,
        "total_movements": inbound_movements + outbound_movements,
        "avg_movement_value": float(avg_movement_value)
    }

def generate_inventory_value_report(db: Session) -> Dict[str, Any]:
    """Generate inventory value report"""
    # Total inventory value
    total_value = db.query(func.sum(
        InventoryItem.quantity_available * InventoryItem.cost_price
    )).scalar() or 0
    
    # Value by category
    category_values = db.query(
        Category.name,
        func.sum(InventoryItem.quantity_available * InventoryItem.cost_price).label('value')
    ).join(Product, Category.id == Product.category_id).join(
        InventoryItem, Product.id == InventoryItem.product_id
    ).group_by(Category.name).all()
    
    # Average item value
    avg_item_value = db.query(func.avg(
        InventoryItem.quantity_available * InventoryItem.cost_price
    )).scalar() or 0
    
    # High value items (>$1000)
    high_value_items = db.query(InventoryItem).filter(
        (InventoryItem.quantity_available * InventoryItem.cost_price) > 1000
    ).count()
    
    return {
        "total_value": float(total_value),
        "avg_item_value": float(avg_item_value),
        "high_value_items": high_value_items,
        "category_values": [
            {"category": cat.name, "value": float(val)} 
            for cat, val in category_values
        ]
    }

def generate_customer_analytics(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Generate customer analytics"""
    # Get customers with their order data
    customers_data = db.query(
        Customer,
        func.count(SalesOrder.id).label('total_orders'),
        func.sum(SalesOrder.total_amount).label('total_revenue')
    ).outerjoin(SalesOrder, Customer.id == SalesOrder.customer_id).filter(
        SalesOrder.order_date.between(start_date, end_date)
    ).group_by(Customer.id).order_by(
        func.sum(SalesOrder.total_amount).desc()
    ).all()
    
    # Convert to list of dictionaries
    customers = []
    for customer, orders, revenue in customers_data:
        customers.append({
            "id": customer.id,
            "name": customer.name,
            "total_orders": orders or 0,
            "total_revenue": float(revenue or 0)
        })
    
    # Calculate summary metrics
    total_customers = len(customers)
    total_revenue = sum(c['total_revenue'] for c in customers)
    avg_revenue_per_customer = total_revenue / total_customers if total_customers > 0 else 0
    
    return {
        "customers": customers,
        "total_customers": total_customers,
        "total_revenue": total_revenue,
        "avg_revenue_per_customer": round(avg_revenue_per_customer, 2)
    }

# Additional hospital-specific functions

def generate_hospital_vendor_analytics(db: Session, start_date: datetime, end_date: datetime, hospital_id: int) -> Dict[str, Any]:
    """Generate hospital-specific vendor analytics"""
    # For hospital users, show vendors related to their orders
    # This would need to be implemented based on your business logic
    # For now, return empty data
    return {
        "vendors": [],
        "total_vendors": 0,
        "total_spent": 0,
        "avg_spent_per_vendor": 0
    }

def get_hospital_recent_sales(db: Session, hospital_id: int, limit: int = 10) -> List[Dict]:
    """Get recent sales orders for a specific hospital"""
    sales = db.query(SalesOrder).filter(
        SalesOrder.customer_id == hospital_id
    ).order_by(SalesOrder.order_date.desc()).limit(limit).all()
    
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

def generate_vendor_analytics(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Generate vendor analytics"""
    # Get vendors with their purchase data
    vendors_data = db.query(
        Vendor,
        func.count(PurchaseOrder.id).label('total_orders'),
        func.sum(PurchaseOrder.total_amount).label('total_spent')
    ).outerjoin(PurchaseOrder, Vendor.id == PurchaseOrder.vendor_id).filter(
        PurchaseOrder.order_date.between(start_date, end_date)
    ).group_by(Vendor.id).order_by(
        func.sum(PurchaseOrder.total_amount).desc()
    ).all()
    
    # Convert to list of dictionaries
    vendors = []
    for vendor, orders, spent in vendors_data:
        vendors.append({
            "id": vendor.id,
            "name": vendor.name,
            "total_orders": orders or 0,
            "total_spent": float(spent or 0)
        })
    
    # Calculate summary metrics
    total_vendors = len(vendors)
    total_spent = sum(v['total_spent'] for v in vendors)
    avg_spent_per_vendor = total_spent / total_vendors if total_vendors > 0 else 0
    
    return {
        "vendors": vendors,
        "total_vendors": total_vendors,
        "total_spent": total_spent,
        "avg_spent_per_vendor": round(avg_spent_per_vendor, 2)
    }

# Hospital-specific report functions for staff users

def generate_hospital_financial_summary(db: Session, start_date: datetime, end_date: datetime, hospital_id: int) -> Dict[str, Any]:
    """Generate hospital-specific financial summary"""
    # Get hospital's sales orders
    hospital_orders = db.query(SalesOrder).filter(
        SalesOrder.customer_id == hospital_id,
        SalesOrder.order_date.between(start_date, end_date)
    ).all()
    
    total_revenue = sum(float(order.total_amount) for order in hospital_orders)
    total_orders = len(hospital_orders)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "avg_order_value": round(avg_order_value, 2),
        "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    }

def generate_hospital_revenue_report(db: Session, start_date: datetime, end_date: datetime, hospital_id: int) -> Dict[str, Any]:
    """Generate hospital-specific revenue report"""
    # Get hospital's sales orders by month
    monthly_revenue = db.query(
        func.date_format(SalesOrder.order_date, '%Y-%m').label('month'),
        func.sum(SalesOrder.total_amount).label('revenue')
    ).filter(
        SalesOrder.customer_id == hospital_id,
        SalesOrder.order_date.between(start_date, end_date)
    ).group_by(func.date_format(SalesOrder.order_date, '%Y-%m')).all()
    
    return {
        "monthly_revenue": [
            {"month": month, "revenue": float(revenue)} 
            for month, revenue in monthly_revenue
        ]
    }

def generate_hospital_expense_report(db: Session, start_date: datetime, end_date: datetime, hospital_id: int) -> Dict[str, Any]:
    """Generate hospital-specific expense report"""
    # For hospital users, expenses are their purchase orders
    hospital_orders = db.query(SalesOrder).filter(
        SalesOrder.customer_id == hospital_id,
        SalesOrder.order_date.between(start_date, end_date)
    ).all()
    
    total_expenses = sum(float(order.total_amount) for order in hospital_orders)
    
    return {
        "total_expenses": total_expenses,
        "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    }

def generate_hospital_profit_report(db: Session, start_date: datetime, end_date: datetime, hospital_id: int) -> Dict[str, Any]:
    """Generate hospital-specific profit report"""
    # For hospital users, profit is revenue minus expenses (their orders)
    hospital_orders = db.query(SalesOrder).filter(
        SalesOrder.customer_id == hospital_id,
        SalesOrder.order_date.between(start_date, end_date)
    ).all()
    
    total_revenue = sum(float(order.total_amount) for order in hospital_orders)
    # For simplicity, assume 20% profit margin
    total_profit = total_revenue * 0.2
    
    return {
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "profit_margin": 20.0,
        "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    }

def generate_hospital_inventory_overview(db: Session, hospital_id: int) -> Dict[str, Any]:
    """Generate hospital-specific inventory overview"""
    from app.models.models import HospitalInventory
    
    # Get hospital's inventory
    hospital_inventory = db.query(HospitalInventory).filter(
        HospitalInventory.hospital_id == hospital_id
    ).all()
    
    total_items = len(hospital_inventory)
    in_stock_items = sum(1 for item in hospital_inventory if item.current_stock > 0)
    low_stock_items = sum(1 for item in hospital_inventory if item.current_stock <= item.reorder_point and item.current_stock > 0)
    out_of_stock_items = sum(1 for item in hospital_inventory if item.current_stock == 0)
    
    # Calculate total value
    total_value = 0
    for item in hospital_inventory:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product and product.unit_price:
            total_value += item.current_stock * float(product.unit_price)
    
    return {
        "total_items": total_items,
        "in_stock_items": in_stock_items,
        "low_stock_items": low_stock_items,
        "out_of_stock_items": out_of_stock_items,
        "total_value": float(total_value)
    }

def generate_hospital_low_stock_report(db: Session, hospital_id: int) -> Dict[str, Any]:
    """Generate hospital-specific low stock report"""
    from app.models.models import HospitalInventory
    
    # Get hospital's low stock items
    low_stock_items = db.query(HospitalInventory).filter(
        HospitalInventory.hospital_id == hospital_id,
        HospitalInventory.current_stock <= HospitalInventory.reorder_point,
        HospitalInventory.current_stock > 0
    ).all()
    
    items_data = []
    for item in low_stock_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            items_data.append({
                "product_name": product.name,
                "current_stock": item.current_stock,
                "reorder_point": item.reorder_point,
                "max_stock": item.max_stock,
                "last_restocked": item.last_restocked
            })
    
    return {
        "low_stock_items": items_data,
        "total_low_stock_items": len(items_data)
    }

def generate_hospital_expiry_report(db: Session, hospital_id: int) -> Dict[str, Any]:
    """Generate hospital-specific expiry report"""
    # For hospital inventory, we don't track expiry dates in HospitalInventory
    # This would need to be implemented if hospitals track expiry dates
    return {
        "expiring_items": [],
        "total_expiring_items": 0,
        "note": "Expiry tracking not implemented for hospital inventory"
    }

def generate_hospital_movement_report(db: Session, hospital_id: int) -> Dict[str, Any]:
    """Generate hospital-specific movement report"""
    # For hospital inventory, movements are when they receive stock
    # This would need to be implemented if hospitals track stock movements
    return {
        "movements": [],
        "total_movements": 0,
        "note": "Movement tracking not implemented for hospital inventory"
    }

def generate_hospital_inventory_value_report(db: Session, hospital_id: int) -> Dict[str, Any]:
    """Generate hospital-specific inventory value report"""
    from app.models.models import HospitalInventory
    
    # Get hospital's inventory
    hospital_inventory = db.query(HospitalInventory).filter(
        HospitalInventory.hospital_id == hospital_id
    ).all()
    
    total_value = 0
    category_values = {}
    
    for item in hospital_inventory:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product and product.unit_price:
            item_value = item.current_stock * float(product.unit_price)
            total_value += item_value
            
            # Group by category
            if product.category:
                category_name = product.category.name
                if category_name not in category_values:
                    category_values[category_name] = 0
                category_values[category_name] += item_value
    
    return {
        "total_value": float(total_value),
        "category_values": [
            {"category": cat, "value": float(val)} 
            for cat, val in category_values.items()
        ]
    }

def generate_hospital_customer_analytics(db: Session, start_date: datetime, end_date: datetime, hospital_id: int) -> Dict[str, Any]:
    """Generate hospital-specific customer analytics"""
    # For hospital users, they are the customer, so show their own data
    hospital = db.query(Customer).filter(Customer.id == hospital_id).first()
    
    if not hospital:
        return {
            "customers": [],
            "total_customers": 0,
            "total_revenue": 0,
            "avg_revenue_per_customer": 0
        }
    
    # Get hospital's order data
    hospital_orders = db.query(SalesOrder).filter(
        SalesOrder.customer_id == hospital_id,
        SalesOrder.order_date.between(start_date, end_date)
    ).all()
    
    total_revenue = sum(float(order.total_amount) for order in hospital_orders)
    total_orders = len(hospital_orders)
    avg_revenue_per_customer = total_revenue if total_orders > 0 else 0
    
    return {
        "customers": [{
            "id": hospital.id,
            "name": hospital.name,
            "total_orders": total_orders,
            "total_revenue": total_revenue
        }],
        "total_customers": 1,
        "total_revenue": total_revenue,
        "avg_revenue_per_customer": round(avg_revenue_per_customer, 2)
    } 