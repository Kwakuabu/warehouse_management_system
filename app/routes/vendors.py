# app/routes/vendors.py
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Vendor, User
from app.utils.auth import check_user_role_from_cookie, get_current_active_user_from_cookie
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Vendors list page - All authenticated users
@router.get("/", response_class=HTMLResponse)
async def vendors_list(
    request: Request, 
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Display vendors list page - All authenticated users"""
    vendors = db.query(Vendor).all()
    return templates.TemplateResponse("vendors/list.html", {
        "request": request, 
        "vendors": vendors,
        "current_user": current_user,
        "user_role": current_user.role,
        "pagination": {"pages": 1, "page": 1, "has_prev": False, "has_next": False}  # Simple pagination placeholder
    })

# Add vendor page - Manager and Admin only
@router.get("/add", response_class=HTMLResponse)
async def add_vendor_page(
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("manager"))
):
    """Display add vendor page - Manager and Admin only"""
    return templates.TemplateResponse("vendors/add.html", {
        "request": request,
        "current_user": current_user
    })

# Create vendor - Manager and Admin only
@router.post("/add")
async def create_vendor(
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    name: str = Form(...),
    contact_person: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    address: str = Form(""),
    country: str = Form(""),
    payment_terms: str = Form("Net 30"),
    lead_time_days: int = Form(30),
    db: Session = Depends(get_db)
):
    """Create a new vendor - Manager and Admin only"""
    # Check if vendor already exists
    existing_vendor = db.query(Vendor).filter(Vendor.name == name).first()
    if existing_vendor:
        return templates.TemplateResponse("vendors/add.html", {
            "request": request,
            "error": "Vendor with this name already exists",
            "current_user": current_user
        })
    
    # Create new vendor
    vendor = Vendor(
        name=name,
        contact_person=contact_person,
        email=email,
        phone=phone,
        address=address,
        country=country,
        payment_terms=payment_terms,
        lead_time_days=lead_time_days
    )
    db.add(vendor)
    db.commit()
    
    return RedirectResponse(url="/vendors", status_code=302)

# Vendor details page - All authenticated users
@router.get("/{vendor_id}", response_class=HTMLResponse)
async def vendor_detail(
    request: Request, 
    vendor_id: int, 
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Display vendor details page - All authenticated users"""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    return templates.TemplateResponse("vendors/detail.html", {
        "request": request, 
        "vendor": vendor,
        "current_user": current_user
    })

# Edit vendor page - Manager and Admin only
@router.get("/{vendor_id}/edit", response_class=HTMLResponse)
async def edit_vendor_page(
    request: Request, 
    vendor_id: int, 
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Display edit vendor page - Manager and Admin only"""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    return templates.TemplateResponse("vendors/edit.html", {
        "request": request,
        "vendor": vendor,
        "current_user": current_user
    })

# Update vendor - Manager and Admin only
@router.post("/{vendor_id}/edit")
async def update_vendor(
    request: Request,
    vendor_id: int,
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    name: str = Form(...),
    contact_person: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    address: str = Form(""),
    country: str = Form(""),
    payment_terms: str = Form("Net 30"),
    lead_time_days: int = Form(30),
    is_active: bool = Form(True),
    db: Session = Depends(get_db)
):
    """Update vendor - Manager and Admin only"""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    # Update vendor fields
    vendor.name = name
    vendor.contact_person = contact_person
    vendor.email = email
    vendor.phone = phone
    vendor.address = address
    vendor.country = country
    vendor.payment_terms = payment_terms
    vendor.lead_time_days = lead_time_days
    vendor.is_active = is_active
    
    db.commit()
    
    return RedirectResponse(url="/vendors", status_code=302)

# Delete vendor - Admin and Manager only
@router.post("/{vendor_id}/delete")
async def delete_vendor(
    vendor_id: int,
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Soft delete a vendor"""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    # Soft delete by setting is_active to False
    vendor.is_active = False
    db.commit()
    
    return {"success": True, "message": "Vendor deleted successfully"}

# API: Get all vendors - All authenticated users
@router.get("/api/vendors")
async def get_vendors(
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get all vendors for API - All authenticated users"""
    vendors = db.query(Vendor).all()
    return {"vendors": [{"id": v.id, "name": v.name, "country": v.country} for v in vendors]} 