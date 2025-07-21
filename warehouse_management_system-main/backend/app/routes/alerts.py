# app/routes/alerts.py
from fastapi import APIRouter, Depends, HTTPException, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from app.database import get_db
from app.models.models import Alert, InventoryItem, Product, User
from app.utils.auth import check_user_role_from_cookie, get_current_active_user_from_cookie, check_user_roles_from_cookie
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Alerts list page - Manager and Admin only
@router.get("/", response_class=HTMLResponse)
async def alerts_list(
    request: Request, 
    current_user: User = Depends(check_user_roles_from_cookie(["staff", "manager"])),
    severity: str = Query(None),
    alert_type: str = Query(None),
    status: str = Query(None),
    db: Session = Depends(get_db)
):
    """Display alerts list page with filters - Manager and Admin only"""
    
    # Build query with filters
    query = db.query(Alert)
    
    if severity:
        query = query.filter(Alert.severity == severity)
    
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    
    if status == "acknowledged":
        query = query.filter(Alert.is_acknowledged == True)
    elif status == "unacknowledged":
        query = query.filter(Alert.is_acknowledged == False)
    
    alerts = query.order_by(Alert.created_at.desc()).all()
    
    # Get alert statistics
    total_alerts = db.query(Alert).count()
    unacknowledged_alerts = db.query(Alert).filter(Alert.is_acknowledged == False).count()
    critical_alerts = db.query(Alert).filter(
        Alert.severity == "critical",
        Alert.is_acknowledged == False
    ).count()
    high_alerts = db.query(Alert).filter(
        Alert.severity == "high",
        Alert.is_acknowledged == False
    ).count()
    
    return templates.TemplateResponse("alerts/list.html", {
        "request": request,
        "alerts": alerts,
        "total_alerts": total_alerts,
        "unacknowledged_alerts": unacknowledged_alerts,
        "critical_alerts": critical_alerts,
        "high_alerts": high_alerts,
        "stats": {
            "total_alerts": total_alerts,
            "unacknowledged_alerts": unacknowledged_alerts,
            "critical_alerts": critical_alerts,
            "high_alerts": high_alerts,
            "error_count": 0
        },
        "filters": {
            "severity": severity,
            "alert_type": alert_type,
            "status": status
        },
        "current_user": current_user,
        "pagination": {"pages": 1, "page": 1, "has_prev": False, "has_next": False}  # Simple pagination placeholder
    })

# Alert detail page
@router.get("/detail/{alert_id}", response_class=HTMLResponse)
async def alert_detail(request: Request, alert_id: int, db: Session = Depends(get_db)):
    """Display alert details"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Get related inventory item if available
    inventory_item = None
    if alert.inventory_item_id:
        inventory_item = db.query(InventoryItem).filter(InventoryItem.id == alert.inventory_item_id).first()
    
    # Get acknowledged by user if available
    acknowledged_by = None
    if alert.acknowledged_by:
        acknowledged_by = db.query(User).filter(User.id == alert.acknowledged_by).first()
    
    return templates.TemplateResponse("alerts/detail.html", {
        "request": request,
        "alert": alert,
        "inventory_item": inventory_item,
        "acknowledged_by": acknowledged_by
    })

# Acknowledge alert
@router.post("/acknowledge/{alert_id}")
async def acknowledge_alert(
    request: Request,
    alert_id: int,
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    """Acknowledge an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    try:
        alert.is_acknowledged = True
        alert.acknowledged_at = datetime.utcnow()
        # In a real system, you'd get the current user ID from the session
        alert.acknowledged_by = 1  # Default admin user
        
        db.commit()
        
        return RedirectResponse(url="/alerts", status_code=302)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error acknowledging alert: {str(e)}")

# Bulk acknowledge alerts
@router.post("/bulk-acknowledge")
async def bulk_acknowledge_alerts(
    request: Request,
    alert_ids: str = Form(...),
    db: Session = Depends(get_db)
):
    """Bulk acknowledge multiple alerts"""
    try:
        ids = [int(id.strip()) for id in alert_ids.split(",") if id.strip()]
        
        alerts = db.query(Alert).filter(Alert.id.in_(ids)).all()
        for alert in alerts:
            alert.is_acknowledged = True
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = 1  # Default admin user
        
        db.commit()
        
        return RedirectResponse(url="/alerts", status_code=302)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error bulk acknowledging alerts: {str(e)}")

# Create alert (for testing/demo purposes)
@router.post("/create")
async def create_alert(
    request: Request,
    alert_type: str = Form(...),
    message: str = Form(...),
    severity: str = Form("medium"),
    inventory_item_id: int = Form(None),
    db: Session = Depends(get_db)
):
    """Create a new alert (for testing)"""
    try:
        alert = Alert(
            alert_type=alert_type,
            message=message,
            severity=severity,
            inventory_item_id=inventory_item_id,
            is_acknowledged=False
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        return RedirectResponse(url="/alerts", status_code=302)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating alert: {str(e)}")

# API: Get alerts
@router.get("/api/list")
async def get_alerts_api(
    severity: str = Query(None),
    alert_type: str = Query(None),
    acknowledged: bool = Query(None),
    limit: int = Query(50),
    db: Session = Depends(get_db)
):
    """Get alerts for API"""
    query = db.query(Alert)
    
    if severity:
        query = query.filter(Alert.severity == severity)
    
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    
    if acknowledged is not None:
        query = query.filter(Alert.is_acknowledged == acknowledged)
    
    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    
    return {
        "alerts": [
            {
                "id": alert.id,
                "alert_type": alert.alert_type,
                "message": alert.message,
                "severity": alert.severity,
                "is_acknowledged": alert.is_acknowledged,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
                "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
            }
            for alert in alerts
        ]
    }

# API: Get alert summary
@router.get("/api/summary")
async def get_alert_summary(db: Session = Depends(get_db)):
    """Get alert summary for API"""
    try:
        total_alerts = db.query(Alert).count()
        unacknowledged_alerts = db.query(Alert).filter(Alert.is_acknowledged == False).count()
        
        # Count by severity
        critical_alerts = db.query(Alert).filter(
            Alert.severity == "critical",
            Alert.is_acknowledged == False
        ).count()
        
        high_alerts = db.query(Alert).filter(
            Alert.severity == "high",
            Alert.is_acknowledged == False
        ).count()
        
        medium_alerts = db.query(Alert).filter(
            Alert.severity == "medium",
            Alert.is_acknowledged == False
        ).count()
        
        low_alerts = db.query(Alert).filter(
            Alert.severity == "low",
            Alert.is_acknowledged == False
        ).count()
        
        # Count by type
        low_stock_alerts = db.query(Alert).filter(
            Alert.alert_type == "low_stock",
            Alert.is_acknowledged == False
        ).count()
        
        expiry_alerts = db.query(Alert).filter(
            Alert.alert_type == "expiry_warning",
            Alert.is_acknowledged == False
        ).count()
        
        temperature_alerts = db.query(Alert).filter(
            Alert.alert_type == "temperature_alert",
            Alert.is_acknowledged == False
        ).count()
        
        return {
            "total_alerts": total_alerts,
            "unacknowledged_alerts": unacknowledged_alerts,
            "by_severity": {
                "critical": critical_alerts,
                "high": high_alerts,
                "medium": medium_alerts,
                "low": low_alerts
            },
            "by_type": {
                "low_stock": low_stock_alerts,
                "expiry_warning": expiry_alerts,
                "temperature_alert": temperature_alerts
            }
        }
    except Exception as e:
        return {
            "total_alerts": 0,
            "unacknowledged_alerts": 0,
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "by_type": {"low_stock": 0, "expiry_warning": 0, "temperature_alert": 0},
            "error": str(e)
        }

# API: Acknowledge alert
@router.post("/api/acknowledge/{alert_id}")
async def api_acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """API endpoint to acknowledge an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    try:
        alert.is_acknowledged = True
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = 1  # Default admin user
        
        db.commit()
        
        return {"message": "Alert acknowledged successfully", "alert_id": alert_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error acknowledging alert: {str(e)}")

# Delete alert - Admin and Manager only
@router.post("/{alert_id}/delete")
async def delete_alert(
    alert_id: int,
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Delete an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Hard delete for alerts since they're temporary notifications
    db.delete(alert)
    db.commit()
    
    return {"success": True, "message": "Alert deleted successfully"}

# Helper function to create system alerts
def create_system_alert(
    db: Session,
    alert_type: str,
    message: str,
    severity: str = "medium",
    inventory_item_id: Optional[int] = None
) -> Alert:
    """Helper function to create system alerts"""
    alert = Alert(
        alert_type=alert_type,
        message=message,
        severity=severity,
        inventory_item_id=inventory_item_id,
        is_acknowledged=False
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

# Function to check for low stock alerts
def check_low_stock_alerts(db: Session):
    """Check for low stock items and create alerts"""
    low_stock_items = db.query(InventoryItem).join(Product).filter(
        InventoryItem.quantity_available <= Product.reorder_point,
        InventoryItem.quantity_available > 0
    ).all()
    
    for item in low_stock_items:
        # Check if alert already exists
        existing_alert = db.query(Alert).filter(
            Alert.alert_type == "low_stock",
            Alert.inventory_item_id == item.id,
            Alert.is_acknowledged == False
        ).first()
        
        if not existing_alert:
            severity = "critical" if item.quantity_available == 0 else "high"
            message = f"Low stock alert: {item.product.name} (SKU: {item.product.sku}) - Available: {item.quantity_available} {item.product.unit_of_measure}"
            create_system_alert(db, "low_stock", message, severity, item.id)

# Function to check for expiry alerts
def check_expiry_alerts(db: Session):
    """Check for items expiring soon and create alerts"""
    thirty_days_from_now = datetime.utcnow() + timedelta(days=30)
    seven_days_from_now = datetime.utcnow() + timedelta(days=7)
    
    expiring_items = db.query(InventoryItem).filter(
        InventoryItem.expiry_date.isnot(None),
        InventoryItem.expiry_date <= thirty_days_from_now,
        InventoryItem.expiry_date > datetime.utcnow(),
        InventoryItem.quantity_available > 0
    ).all()
    
    for item in expiring_items:
        # Check if alert already exists
        existing_alert = db.query(Alert).filter(
            Alert.alert_type == "expiry_warning",
            Alert.inventory_item_id == item.id,
            Alert.is_acknowledged == False
        ).first()
        
        if not existing_alert:
            days_until_expiry = (item.expiry_date - datetime.utcnow()).days
            severity = "critical" if days_until_expiry <= 7 else "high" if days_until_expiry <= 14 else "medium"
            message = f"Expiry warning: {item.product.name} (Batch: {item.batch_number}) expires in {days_until_expiry} days"
            create_system_alert(db, "expiry_warning", message, severity, item.id) 