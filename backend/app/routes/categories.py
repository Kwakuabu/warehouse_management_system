# app/routes/categories.py
from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.models import Category, User
from app.utils.auth import get_current_active_user_from_cookie, check_user_role_from_cookie
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Categories list page - All authenticated users can view
@router.get("/", response_class=HTMLResponse)
async def list_categories(
    request: Request,
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Display list of all categories"""
    categories = db.query(Category).order_by(Category.name).all()
    
    return templates.TemplateResponse("categories/list.html", {
        "request": request,
        "categories": categories,
        "current_user": current_user,
        "user_role": current_user.role,
        "pagination": {"pages": 1, "page": 1, "has_prev": False, "has_next": False}  # Simple pagination placeholder
    })

# Add category page - Admin and Manager only
@router.get("/add", response_class=HTMLResponse, name="add_category_page")
async def add_category_page(
    request: Request,
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Display add category form"""
    return templates.TemplateResponse("categories/add.html", {
        "request": request,
        "current_user": current_user
    })

# Add category form submission - Admin and Manager only
@router.post("/add")
async def add_category(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Handle add category form submission"""
    # Check if name already exists
    existing_category = db.query(Category).filter(Category.name == name).first()
    if existing_category:
        return templates.TemplateResponse("categories/add.html", {
            "request": request,
            "error": "Category name already exists",
            "current_user": current_user
        })
    
    # Create new category
    category = Category(
        name=name,
        description=description
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return RedirectResponse(url="/categories", status_code=302)

# Category detail page - All authenticated users can view
@router.get("/{category_id}", response_class=HTMLResponse)
async def category_detail(
    request: Request,
    category_id: int,
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Display category details"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return templates.TemplateResponse("categories/detail.html", {
        "request": request,
        "category": category,
        "current_user": current_user
    })

# Edit category page - Admin and Manager only
@router.get("/{category_id}/edit", response_class=HTMLResponse)
async def edit_category_page(
    request: Request,
    category_id: int,
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Display edit category form"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return templates.TemplateResponse("categories/edit.html", {
        "request": request,
        "category": category,
        "current_user": current_user
    })

# Update category - Admin and Manager only
@router.post("/{category_id}/edit")
async def update_category(
    request: Request,
    category_id: int,
    name: str = Form(...),
    description: str = Form(...),
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Handle edit category form submission"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if name already exists (excluding current category)
    existing_category = db.query(Category).filter(
        Category.name == name,
        Category.id != category_id
    ).first()
    if existing_category:
        return templates.TemplateResponse("categories/edit.html", {
            "request": request,
            "category": category,
            "error": "Category name already exists",
            "current_user": current_user
        })
    
    # Update category
    category.name = name
    category.description = description
    
    db.commit()
    db.refresh(category)
    
    return RedirectResponse(url=f"/categories/{category_id}", status_code=302)

# Delete category - Admin and Manager only
@router.post("/{category_id}/delete")
async def delete_category(
    category_id: int,
    current_user: User = Depends(check_user_role_from_cookie("manager")),
    db: Session = Depends(get_db)
):
    """Delete a category"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if category has products
    if category.products:
        raise HTTPException(status_code=400, detail="Cannot delete category that has products. Please remove or reassign products first.")
    
    # Hard delete the category
    db.delete(category)
    db.commit()
    
    # Return JSON response for AJAX calls
    return {"message": "Category deleted successfully", "category_id": category_id}

# API endpoints for AJAX calls
@router.get("/api/categories")
async def get_categories_api(
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """API endpoint to get all categories"""
    categories = db.query(Category).all()
    return {"categories": [{"id": c.id, "name": c.name} for c in categories]}

@router.get("/api/categories/{category_id}")
async def get_category_api(
    category_id: int,
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """API endpoint to get a specific category"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category