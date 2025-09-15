# app/routes/customers.py
from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.models import Customer, User
from app.utils.auth import get_current_active_user_from_cookie, check_user_role_from_cookie
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Customers list page - All authenticated users can view
@router.get("/", response_class=HTMLResponse)
async def list_customers(
    request: Request,
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Display list of all customers"""
    customers = db.query(Customer).filter(Customer.is_active == True).order_by(desc(Customer.created_at)).all()
    
    return templates.TemplateResponse("customers/list.html", {
        "request": request,
        "customers": customers,
        "current_user": current_user,
        "user_role": current_user.role,
        "pagination": {"pages": 1, "page": 1, "has_prev": False, "has_next": False}  # Simple pagination placeholder
    })

# Add customer page - Admin and Manager only
@router.get("/add", response_class=HTMLResponse)
async def add_customer_page(
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Display add customer form"""
    return templates.TemplateResponse("customers/add.html", {
        "request": request,
        "current_user": current_user
    })

# Add customer form submission - Admin and Manager only
@router.post("/add")
async def add_customer(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    contact_person: str = Form(...),
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Handle add customer form submission"""
    # Check if email already exists
    existing_customer = db.query(Customer).filter(Customer.email == email).first()
    if existing_customer:
        return templates.TemplateResponse("customers/add.html", {
            "request": request,
            "error": "Email already exists",
            "current_user": current_user
        })
    
    # Create new customer
    customer = Customer(
        name=name,
        email=email,
        phone=phone,
        address=address,
        contact_person=contact_person
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    return RedirectResponse(url="/customers", status_code=302)

# Customer detail page - All authenticated users can view
@router.get("/{customer_id}", response_class=HTMLResponse)
async def customer_detail(
    request: Request,
    customer_id: int,
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Display customer details"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return templates.TemplateResponse("customers/detail.html", {
        "request": request,
        "customer": customer,
        "current_user": current_user
    })

# Edit customer page - Admin and Manager only
@router.get("/{customer_id}/edit", response_class=HTMLResponse)
async def edit_customer_page(
    request: Request,
    customer_id: int,
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Display edit customer form"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return templates.TemplateResponse("customers/edit.html", {
        "request": request,
        "customer": customer,
        "current_user": current_user
    })

# Update customer - Admin and Manager only
@router.post("/{customer_id}/edit")
async def update_customer(
    request: Request,
    customer_id: int,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    contact_person: str = Form(...),
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Handle edit customer form submission"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Check if email already exists (excluding current customer)
    existing_customer = db.query(Customer).filter(
        Customer.email == email,
        Customer.id != customer_id
    ).first()
    if existing_customer:
        return templates.TemplateResponse("customers/edit.html", {
            "request": request,
            "customer": customer,
            "error": "Email already exists",
            "current_user": current_user
        })
    
    # Update customer
    customer.name = name
    customer.email = email
    customer.phone = phone
    customer.address = address
    customer.contact_person = contact_person
    
    db.commit()
    db.refresh(customer)
    
    return RedirectResponse(url=f"/customers/{customer_id}", status_code=302)

# Delete customer - Admin and Manager only
@router.post("/{customer_id}/delete")
async def delete_customer(
    customer_id: int,
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Soft delete a customer"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Soft delete
    customer.is_active = False
    db.commit()
    
    return RedirectResponse(url="/customers/", status_code=302)

# API endpoints for AJAX calls
@router.get("/api/customers")
async def get_customers_api(
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """API endpoint to get all customers"""
    customers = db.query(Customer).filter(Customer.is_active == True).all()
    return {"customers": [{"id": c.id, "name": c.name, "email": c.email} for c in customers]}

@router.get("/api/customers/{customer_id}")
async def get_customer_api(
    customer_id: int,
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """API endpoint to get a specific customer"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer