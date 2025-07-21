# app/routes/settings.py
from fastapi import APIRouter, Depends, HTTPException, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User
from app.utils.auth import check_user_role_from_cookie, get_current_active_user_from_cookie
from datetime import datetime
from typing import Optional, Dict, Any
import json
import shutil
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Settings dashboard - Admin only
@router.get("/", response_class=HTMLResponse)
async def settings_dashboard(
    request: Request, 
    current_user: User = Depends(check_user_role_from_cookie("admin")),
    db: Session = Depends(get_db)
):
    """Display settings dashboard - Admin only"""
    
    # Get system statistics
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    
    # Get default settings (in a real system, these would come from a settings table)
    system_settings = get_default_system_settings()
    user_preferences = get_default_user_preferences()
    company_settings = get_default_company_settings()
    
    return templates.TemplateResponse("settings/dashboard.html", {
        "request": request,
        "total_users": total_users,
        "active_users": active_users,
        "system_settings": system_settings,
        "user_preferences": user_preferences,
        "company_settings": company_settings,
        "current_user": current_user
    })

# System settings - Admin only
@router.get("/system", response_class=HTMLResponse)
async def system_settings_page(
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("admin"))
):
    """Display system settings page - Admin only"""
    settings = get_default_system_settings()
    
    return templates.TemplateResponse("settings/system.html", {
        "request": request,
        "settings": settings,
        "current_user": current_user
    })

@router.post("/system")
async def update_system_settings(
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("admin")),
    company_name: str = Form(...),
    system_email: str = Form(...),
    timezone: str = Form("UTC"),
    date_format: str = Form("YYYY-MM-DD"),
    currency: str = Form("GHS"),
    language: str = Form("en"),
    max_file_size: int = Form(10485760),
    session_timeout: int = Form(30),
    enable_notifications: bool = Form(True),
    enable_audit_log: bool = Form(True),
    db: Session = Depends(get_db)
):
    """Update system settings - Admin only"""
    try:
        # In a real system, you would save these to a settings table
        # For now, we'll just return success
        settings = {
            "company_name": company_name,
            "system_email": system_email,
            "timezone": timezone,
            "date_format": date_format,
            "currency": currency,
            "language": language,
            "max_file_size": max_file_size,
            "session_timeout": session_timeout,
            "enable_notifications": enable_notifications,
            "enable_audit_log": enable_audit_log
        }
        
        # Save settings (placeholder for actual implementation)
        save_system_settings(settings)
        
        return RedirectResponse(url="/settings/system", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating system settings: {str(e)}")

# User preferences - All authenticated users
@router.get("/preferences", response_class=HTMLResponse)
async def user_preferences_page(
    request: Request,
    current_user: User = Depends(get_current_active_user_from_cookie)
):
    """Display user preferences page - All authenticated users"""
    preferences = get_default_user_preferences()
    
    return templates.TemplateResponse("settings/preferences.html", {
        "request": request,
        "preferences": preferences,
        "current_user": current_user
    })

@router.post("/preferences")
async def update_user_preferences(
    request: Request,
    current_user: User = Depends(get_current_active_user_from_cookie),
    dashboard_layout: str = Form("grid"),
    theme: str = Form("light"),
    notifications_email: bool = Form(True),
    notifications_sms: bool = Form(False),
    notifications_push: bool = Form(True),
    language: str = Form("en"),
    timezone: str = Form("UTC"),
    date_format: str = Form("YYYY-MM-DD"),
    items_per_page: int = Form(25),
    auto_refresh: bool = Form(True),
    refresh_interval: int = Form(300),
    db: Session = Depends(get_db)
):
    """Update user preferences - All authenticated users"""
    try:
        preferences = {
            "dashboard_layout": dashboard_layout,
            "theme": theme,
            "notifications_email": notifications_email,
            "notifications_sms": notifications_sms,
            "notifications_push": notifications_push,
            "language": language,
            "timezone": timezone,
            "date_format": date_format,
            "items_per_page": items_per_page,
            "auto_refresh": auto_refresh,
            "refresh_interval": refresh_interval
        }
        
        # Save preferences (placeholder for actual implementation)
        save_user_preferences(preferences)
        
        return RedirectResponse(url="/settings/preferences", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating user preferences: {str(e)}")

# Company settings - Admin only
@router.get("/company", response_class=HTMLResponse)
async def company_settings_page(
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("admin"))
):
    """Display company settings page - Admin only"""
    settings = get_default_company_settings()
    
    return templates.TemplateResponse("settings/company.html", {
        "request": request,
        "settings": settings,
        "current_user": current_user
    })

@router.post("/company")
async def update_company_settings(
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("admin")),
    company_name: str = Form(...),
    company_address: str = Form(""),
    company_phone: str = Form(""),
    company_email: str = Form(""),
    company_website: str = Form(""),
    tax_id: str = Form(""),
    business_license: str = Form(""),
    industry: str = Form("Pharmaceutical"),
    company_size: str = Form("Medium"),
    founded_year: int = Form(2020),
    timezone: str = Form("UTC"),
    currency: str = Form("GHS"),
    fiscal_year_start: str = Form("01-01"),
    db: Session = Depends(get_db)
):
    """Update company settings - Admin only"""
    try:
        settings = {
            "company_name": company_name,
            "company_address": company_address,
            "company_phone": company_phone,
            "company_email": company_email,
            "company_website": company_website,
            "tax_id": tax_id,
            "business_license": business_license,
            "industry": industry,
            "company_size": company_size,
            "founded_year": founded_year,
            "timezone": timezone,
            "currency": currency,
            "fiscal_year_start": fiscal_year_start
        }
        
        # Save settings (placeholder for actual implementation)
        save_company_settings(settings)
        
        return RedirectResponse(url="/settings/company", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating company settings: {str(e)}")

# Security settings - Admin only
@router.get("/security", response_class=HTMLResponse)
async def security_settings_page(
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("admin"))
):
    """Display security settings page - Admin only"""
    settings = get_default_security_settings()
    
    return templates.TemplateResponse("settings/security.html", {
        "request": request,
        "settings": settings,
        "current_user": current_user
    })

@router.post("/security")
async def update_security_settings(
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("admin")),
    password_min_length: int = Form(8),
    password_require_uppercase: bool = Form(True),
    password_require_lowercase: bool = Form(True),
    password_require_numbers: bool = Form(True),
    password_require_special: bool = Form(True),
    password_expiry_days: int = Form(90),
    session_timeout_minutes: int = Form(30),
    max_login_attempts: int = Form(5),
    lockout_duration_minutes: int = Form(15),
    enable_two_factor: bool = Form(False),
    require_two_factor_admin: bool = Form(True),
    enable_ip_whitelist: bool = Form(False),
    allowed_ips: str = Form(""),
    enable_audit_log: bool = Form(True),
    audit_log_retention_days: int = Form(365),
    db: Session = Depends(get_db)
):
    """Update security settings - Admin only"""
    try:
        settings = {
            "password_min_length": password_min_length,
            "password_require_uppercase": password_require_uppercase,
            "password_require_lowercase": password_require_lowercase,
            "password_require_numbers": password_require_numbers,
            "password_require_special": password_require_special,
            "password_expiry_days": password_expiry_days,
            "session_timeout_minutes": session_timeout_minutes,
            "max_login_attempts": max_login_attempts,
            "lockout_duration_minutes": lockout_duration_minutes,
            "enable_two_factor": enable_two_factor,
            "require_two_factor_admin": require_two_factor_admin,
            "enable_ip_whitelist": enable_ip_whitelist,
            "allowed_ips": allowed_ips,
            "enable_audit_log": enable_audit_log,
            "audit_log_retention_days": audit_log_retention_days
        }
        
        # Save settings (placeholder for actual implementation)
        save_security_settings(settings)
        
        return RedirectResponse(url="/settings/security", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating security settings: {str(e)}")

# Notification settings - Manager and Admin
@router.get("/notifications", response_class=HTMLResponse)
async def notification_settings_page(
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("manager"))
):
    """Display notification settings page - Manager and Admin only"""
    settings = get_default_notification_settings()
    
    return templates.TemplateResponse("settings/notifications.html", {
        "request": request,
        "settings": settings,
        "current_user": current_user
    })

@router.post("/notifications")
async def update_notification_settings(
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    email_notifications: bool = Form(True),
    sms_notifications: bool = Form(False),
    push_notifications: bool = Form(True),
    low_stock_threshold: int = Form(10),
    expiry_warning_days: int = Form(30),
    temperature_alert_threshold: float = Form(8.0),
    daily_reports: bool = Form(True),
    weekly_reports: bool = Form(True),
    monthly_reports: bool = Form(True),
    order_confirmation_email: bool = Form(True),
    order_status_updates: bool = Form(True),
    system_alerts: bool = Form(True),
    db: Session = Depends(get_db)
):
    """Update notification settings - Manager and Admin only"""
    try:
        settings = {
            "email_notifications": email_notifications,
            "sms_notifications": sms_notifications,
            "push_notifications": push_notifications,
            "low_stock_threshold": low_stock_threshold,
            "expiry_warning_days": expiry_warning_days,
            "temperature_alert_threshold": temperature_alert_threshold,
            "daily_reports": daily_reports,
            "weekly_reports": weekly_reports,
            "monthly_reports": monthly_reports,
            "order_confirmation_email": order_confirmation_email,
            "order_status_updates": order_status_updates,
            "system_alerts": system_alerts
        }
        
        # Save settings (placeholder for actual implementation)
        save_notification_settings(settings)
        
        return RedirectResponse(url="/settings/notifications", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating notification settings: {str(e)}")

# User management - Admin only
@router.get("/users", response_class=HTMLResponse)
async def users_list_page(
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("admin")),
    db: Session = Depends(get_db)
):
    """Display user management page - Admin only"""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return templates.TemplateResponse("settings/users.html", {
        "request": request,
        "users": users,
        "current_user": current_user
    })

@router.get("/users/add", response_class=HTMLResponse)
async def add_user_form(
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("admin"))
):
    return templates.TemplateResponse("settings/users_add.html", {"request": request, "current_user": current_user})

@router.post("/users/add")
async def add_user_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    role: str = Form("staff"),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_user_role_from_cookie("admin"))
):
    # Check if username or email exists
    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse("settings/users_add.html", {"request": request, "current_user": current_user, "error": "Username already exists"})
    if db.query(User).filter(User.email == email).first():
        return templates.TemplateResponse("settings/users_add.html", {"request": request, "current_user": current_user, "error": "Email already exists"})
    from app.utils.auth import get_password_hash
    hashed_password = get_password_hash(password)
    user = User(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=hashed_password,
        role=role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return RedirectResponse(url="/settings/users", status_code=302)

@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_form(
    request: Request,
    user_id: int,
    current_user: User = Depends(check_user_role_from_cookie("admin")),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(url="/settings/users", status_code=302)
    return templates.TemplateResponse("settings/users_edit.html", {"request": request, "user": user, "current_user": current_user})

@router.post("/users/{user_id}/edit")
async def edit_user_submit(
    request: Request,
    user_id: int,
    username: str = Form(...),
    email: str = Form(...),
    full_name: str = Form(...),
    role: str = Form(...),
    is_active: Optional[bool] = Form(False),
    password: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_user_role_from_cookie("admin"))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(url="/settings/users", status_code=302)
    # Check for username/email conflicts
    if db.query(User).filter(User.username == username, User.id != user_id).first():
        return templates.TemplateResponse("settings/users_edit.html", {"request": request, "user": user, "current_user": current_user, "error": "Username already exists"})
    if db.query(User).filter(User.email == email, User.id != user_id).first():
        return templates.TemplateResponse("settings/users_edit.html", {"request": request, "user": user, "current_user": current_user, "error": "Email already exists"})
    user.username = username
    user.email = email
    user.full_name = full_name
    user.role = role
    user.is_active = is_active
    if password:
        from app.utils.auth import get_password_hash
        user.hashed_password = get_password_hash(password)
    db.commit()
    db.refresh(user)
    return RedirectResponse(url="/settings/users", status_code=302)

@router.post("/users/{user_id}/toggle")
async def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_user_role_from_cookie("admin"))
):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = not user.is_active
        db.commit()
    return RedirectResponse(url="/settings/users", status_code=302)

@router.post("/users/{user_id}/delete")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_user_role_from_cookie("admin"))
):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return RedirectResponse(url="/settings/users", status_code=302)

# API endpoints - Admin only
@router.get("/api/system-settings")
async def get_system_settings_api(
    current_user: User = Depends(check_user_role_from_cookie("admin"))
):
    """Get system settings API - Admin only"""
    return get_default_system_settings()

@router.get("/api/user-preferences")
async def get_user_preferences_api(
    current_user: User = Depends(get_current_active_user_from_cookie)
):
    """Get user preferences API - All authenticated users"""
    return get_default_user_preferences()

@router.get("/api/company-settings")
async def get_company_settings_api(
    current_user: User = Depends(check_user_role_from_cookie("admin"))
):
    """Get company settings API - Admin only"""
    return get_default_company_settings()

# Helper functions
def get_default_system_settings() -> Dict[str, Any]:
    """Get default system settings"""
    return {
        "company_name": "Alive Pharmaceuticals",
        "system_email": "admin@alivepharma.com",
        "timezone": "UTC",
        "date_format": "YYYY-MM-DD",
        "currency": "GHS",
        "language": "en",
        "max_file_size": 10485760,
        "session_timeout": 30,
        "enable_notifications": True,
        "enable_audit_log": True
    }

def get_default_user_preferences() -> Dict[str, Any]:
    """Get default user preferences"""
    return {
        "dashboard_layout": "grid",
        "theme": "light",
        "notifications_email": True,
        "notifications_sms": False,
        "notifications_push": True,
        "language": "en",
        "timezone": "UTC",
        "date_format": "YYYY-MM-DD",
        "items_per_page": 25,
        "auto_refresh": True,
        "refresh_interval": 300
    }

def get_default_company_settings() -> Dict[str, Any]:
    """Get default company settings"""
    return {
        "company_name": "Alive Pharmaceuticals",
        "company_address": "123 Healthcare Street, Accra, Ghana",
        "company_phone": "+233 20 123 4567",
        "company_email": "info@alivepharma.com",
        "company_website": "www.alivepharma.com",
        "tax_id": "GHA123456789",
        "business_license": "PHARMA-2024-001",
        "industry": "Pharmaceutical",
        "company_size": "Medium",
        "founded_year": 2020,
        "timezone": "UTC",
        "currency": "GHS",
        "fiscal_year_start": "01-01"
    }

def get_default_security_settings() -> Dict[str, Any]:
    """Get default security settings"""
    return {
        "password_min_length": 8,
        "password_require_uppercase": True,
        "password_require_lowercase": True,
        "password_require_numbers": True,
        "password_require_special": True,
        "password_expiry_days": 90,
        "session_timeout_minutes": 30,
        "max_login_attempts": 5,
        "lockout_duration_minutes": 15,
        "enable_two_factor": False,
        "require_two_factor_admin": True,
        "enable_ip_whitelist": False,
        "allowed_ips": "",
        "enable_audit_log": True,
        "audit_log_retention_days": 365
    }

def get_default_notification_settings() -> Dict[str, Any]:
    """Get default notification settings"""
    return {
        "email_notifications": True,
        "sms_notifications": False,
        "push_notifications": True,
        "low_stock_threshold": 10,
        "expiry_warning_days": 30,
        "temperature_alert_threshold": 8.0,
        "daily_reports": True,
        "weekly_reports": True,
        "monthly_reports": True,
        "order_confirmation_email": True,
        "order_status_updates": True,
        "system_alerts": True
    }

def save_system_settings(settings: Dict[str, Any]):
    """Save system settings (placeholder)"""
    # In a real system, this would save to a database table
    print(f"Saving system settings: {settings}")

def save_user_preferences(preferences: Dict[str, Any]):
    """Save user preferences (placeholder)"""
    # In a real system, this would save to a database table
    print(f"Saving user preferences: {preferences}")

def save_company_settings(settings: Dict[str, Any]):
    """Save company settings (placeholder)"""
    # In a real system, this would save to a database table
    print(f"Saving company settings: {settings}")

def save_security_settings(settings: Dict[str, Any]):
    """Save security settings (placeholder)"""
    # In a real system, this would save to a database table
    print(f"Saving security settings: {settings}")

def save_notification_settings(settings: Dict[str, Any]):
    """Save notification settings (placeholder)"""
    # In a real system, this would save to a database table
    print(f"Saving notification settings: {settings}") 

@router.get("/backup", response_class=HTMLResponse)
async def backup_page(
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("admin"))
):
    return templates.TemplateResponse("settings/backup.html", {"request": request, "current_user": current_user})

@router.get("/backup/download")
async def download_backup(
    current_user: User = Depends(check_user_role_from_cookie("admin"))
):
    # Only works for SQLite
    db_path = os.getenv("DATABASE_URL", "sqlite:///./warehouse_db.sqlite")
    if db_path.startswith("sqlite:///"):
        file_path = db_path.replace("sqlite:///", "")
        return FileResponse(file_path, filename="warehouse_db_backup.sqlite", media_type="application/octet-stream")
    else:
        raise HTTPException(status_code=400, detail="Backup only supported for SQLite in this implementation.")

@router.post("/backup")
async def restore_backup(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(check_user_role_from_cookie("admin"))
):
    db_path = os.getenv("DATABASE_URL", "sqlite:///./warehouse_db.sqlite")
    if db_path.startswith("sqlite:///"):
        file_path = db_path.replace("sqlite:///", "")
        # Save uploaded file as new database
        with open(file_path, "wb") as out_file:
            shutil.copyfileobj(file.file, out_file)
        return templates.TemplateResponse("settings/backup.html", {"request": request, "current_user": current_user, "success": "Database restored successfully. Please restart the application."})
    else:
        return templates.TemplateResponse("settings/backup.html", {"request": request, "current_user": current_user, "error": "Restore only supported for SQLite in this implementation."}) 