#!/usr/bin/env python3
"""
Minimal test script to debug the dashboard issue
"""
import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.database import get_db, create_tables
from app.models.models import User
from app.utils.auth import get_current_active_user_from_cookie
from app.utils.seed_data import seed_all_data

# Create FastAPI app
app = FastAPI(title="Minimal Test")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Initialize database
@app.on_event("startup")
async def startup_event():
    create_tables()
    print("Database tables created!")
    
    # Seed data
    db = next(get_db())
    seed_all_data(db)
    print("Data seeded!")

# Test route without authentication
@app.get("/test")
async def test_route():
    return {"message": "Test route works!"}

# Test dashboard route with authentication
@app.get("/dashboard-test", response_class=HTMLResponse)
async def dashboard_test(
    request: Request, 
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Test dashboard route"""
    print(f"Dashboard test accessed by: {current_user.username}")
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": {
            "total_products": 0,
            "low_stock_alerts": 0,
            "expiring_soon": 0,
            "total_inventory_value": 0,
            "pending_purchase_orders": 0,
            "active_customers": 0,
            "total_vendors": 0,
            "recent_movements": 0
        },
        "recent_activities": [],
        "alerts": [],
        "now": "2024-01-01",
        "current_user": current_user,
        "user_role": current_user.role
    })

# Simple login route
@app.get("/login-test", response_class=HTMLResponse)
async def login_test(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001) 