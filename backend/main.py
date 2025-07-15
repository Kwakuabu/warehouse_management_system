# main.py
from fastapi import FastAPI, Depends, HTTPException, Request, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db, create_tables
from app.models.models import User
from app.routes import auth, categories, products, customers, inventory, purchase_orders, sales_order
from app.utils.auth import get_current_user
from app.utils.seed_data import seed_all_data
from typing import Optional
from contextlib import asynccontextmanager
import uvicorn
import os

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    print("Database tables created successfully!")
    
    # Seed initial data
    db = next(get_db())
    seed_all_data(db)
    
    yield
    
    # Shutdown (cleanup if needed)
    print("Application shutting down...")

# Create FastAPI instance with lifespan
app = FastAPI(
    title="Alive Pharmaceuticals Warehouse Management System",
    description="A comprehensive warehouse management system for dialysis consumables",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(categories.router, prefix="/categories", tags=["categories"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(customers.router, prefix="/customers", tags=["customers"])
app.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
app.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["purchase_orders"])
app.include_router(sales_order.router, prefix="/sales-orders", tags=["sales_orders"])

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Root endpoint - Dashboard (Protected)
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, access_token: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
    """Main dashboard page - requires authentication"""
    if not access_token:
        return RedirectResponse(url="/auth/login", status_code=302)
    
    try:
        # Extract token from "Bearer token" format
        token = access_token.replace("Bearer ", "") if access_token.startswith("Bearer ") else access_token
        # Here you would normally verify the token and get user info
        # For now, we'll just show the dashboard
        return templates.TemplateResponse("dashboard.html", {"request": request})
    except:
        return RedirectResponse(url="/auth/login", status_code=302)

# Redirect root paths to auth
@app.get("/login", response_class=HTMLResponse)
async def login_redirect():
    """Redirect to auth login"""
    return RedirectResponse(url="/auth/login")

@app.get("/register", response_class=HTMLResponse)
async def register_redirect():
    """Redirect to auth register"""
    return RedirectResponse(url="/auth/register")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Warehouse Management System is running"}

# API endpoints
@app.get("/api/users")
async def get_users(db: Session = Depends(get_db)):
    """Get all users - for testing"""
    users = db.query(User).all()
    return {"users": len(users), "message": "Users retrieved successfully"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True,
        log_level="info"
    )