# app/routes/customers.py
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Customer
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Customers list page
@router.get("/", response_class=HTMLResponse)
async def customers_list(request: Request, db: Session = Depends(get_db)):
    """Display customers list page"""
    customers = db.query(Customer).all()
    return templates.TemplateResponse("customers/list.html", {
        "request": request, 
        "customers": customers
    })

# Add customer page
@router.get("/add", response_class=HTMLResponse)
async def add_customer_page(request: Request):
    """Display add customer page"""
    return templates.TemplateResponse("customers/add.html", {
        "request": request
    })

# Create customer
@router.post("/add")
async def create_customer(
    request: Request,
    name: str = Form(...),
    contact_person: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    address: str = Form(""),
    city: str = Form(""),
    credit_limit: float = Form(0.0),
    payment_terms: str = Form("Net 30"),
    db: Session = Depends(get_db)
):
    """Create a new customer"""
    # Check if customer already exists
    existing_customer = db.query(Customer).filter(Customer.name == name).first()
    if existing_customer:
        return templates.TemplateResponse("customers/add.html", {
            "request": request,
            "error": "Customer with this name already exists"
        })
    
    # Create new customer
    customer = Customer(
        name=name,
        contact_person=contact_person,
        email=email,
        phone=phone,
        address=address,
        city=city,
        credit_limit=credit_limit,
        payment_terms=payment_terms
    )
    db.add(customer)
    db.commit()
    
    return RedirectResponse(url="/customers", status_code=302)

# Customer details page
@router.get("/{customer_id}", response_class=HTMLResponse)
async def customer_detail(request: Request, customer_id: int, db: Session = Depends(get_db)):
    """Display customer details page"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return templates.TemplateResponse("customers/detail.html", {
        "request": request, 
        "customer": customer
    })

# Edit customer page
@router.get("/edit/{customer_id}", response_class=HTMLResponse)
async def edit_customer_page(request: Request, customer_id: int, db: Session = Depends(get_db)):
    """Display edit customer page"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return templates.TemplateResponse("customers/edit.html", {
        "request": request,
        "customer": customer
    })

# Update customer
@router.post("/edit/{customer_id}")
async def update_customer(
    request: Request,
    customer_id: int,
    name: str = Form(...),
    contact_person: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    address: str = Form(""),
    city: str = Form(""),
    credit_limit: float = Form(0.0),
    payment_terms: str = Form("Net 30"),
    is_active: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Update customer"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Update customer fields
    customer.name = name
    customer.contact_person = contact_person
    customer.email = email
    customer.phone = phone
    customer.address = address
    customer.city = city
    customer.credit_limit = credit_limit
    customer.payment_terms = payment_terms
    customer.is_active = is_active
    
    db.commit()
    
    return RedirectResponse(url="/customers", status_code=302)

# API: Get all customers
@router.get("/api/customers")
async def get_customers(db: Session = Depends(get_db)):
    """Get all customers for API"""
    customers = db.query(Customer).all()
    return {"customers": [{"id": c.id, "name": c.name, "city": c.city} for c in customers]}