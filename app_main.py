# app_main.py - TEST FILE TO SEE IF RAILWAY USES THIS
print("DEBUG: Using app_main.py - TEST FILE - UNIQUE ID: RAILWAY_TEST_002")
from fastapi import FastAPI, Depends, HTTPException, Request, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db, create_tables
from app.models.models import User
from app.routes import auth, categories, products, customers, inventory, purchase_orders, sales_order, dashboard, vendors, reports, alerts, settings
from app.utils.auth import get_current_user_from_cookie
from app.utils.seed_data import seed_all_data
from typing import Optional
from contextlib import asynccontextmanager
import uvicorn
import os
import time

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up warehouse management system...")
    create_tables()
    seed_all_data()
    yield
    # Shutdown
    print("Shutting down warehouse management system...")

# Create FastAPI app
app = FastAPI(
    title="Warehouse Management System",
    description="A comprehensive warehouse management system",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(categories.router, prefix="/categories", tags=["categories"])
app.include_router(customers.router, prefix="/customers", tags=["customers"])
app.include_router(vendors.router, prefix="/vendors", tags=["vendors"])
app.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
app.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["purchase_orders"])
app.include_router(sales_order.router, prefix="/sales-orders", tags=["sales_orders"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(settings.router, prefix="/settings", tags=["settings"])

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Warehouse Management System API", "status": "running"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse("500.html", {"request": request}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
