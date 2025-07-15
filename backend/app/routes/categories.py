# app/routes/categories.py
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Category

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Categories list page
@router.get("/", response_class=HTMLResponse)
async def categories_list(request: Request, db: Session = Depends(get_db)):
    """Display categories list page"""
    categories = db.query(Category).all()
    return templates.TemplateResponse("categories/list.html", {
        "request": request, 
        "categories": categories
    })

# Add category page
@router.get("/add", response_class=HTMLResponse)
async def add_category_page(request: Request):
    """Display add category page"""
    return templates.TemplateResponse("categories/add.html", {
        "request": request
    })

# Create category
@router.post("/add")
async def create_category(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db)
):
    """Create a new category"""
    # Check if category already exists
    existing_category = db.query(Category).filter(Category.name == name).first()
    if existing_category:
        return templates.TemplateResponse("categories/add.html", {
            "request": request,
            "error": "Category already exists"
        })
    
    # Create new category
    category = Category(name=name, description=description)
    db.add(category)
    db.commit()
    
    return RedirectResponse(url="/categories", status_code=302)

# API: Get all categories
@router.get("/api")
async def get_categories(db: Session = Depends(get_db)):
    """Get all categories for API"""
    categories = db.query(Category).all()
    return {"categories": [{"id": cat.id, "name": cat.name, "description": cat.description} for cat in categories]}