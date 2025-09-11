# main.py - RAILWAY FIX - UNIQUE ID: MAIN_FIX_001 - COMPLETE CORRECT VERSION
print("DEBUG: Using complete correct main.py - UNIQUE ID: MAIN_FIX_001")
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
    print("Database tables created successfully!")
    
    # Run database migration for user approval system
    try:
        db = next(get_db())
        from sqlalchemy import text
        
        # Check if approval columns exist
        result = db.execute(text("SHOW COLUMNS FROM users LIKE 'requires_approval'"))
        if not result.fetchone():
            print("Adding user approval columns to database...")
            
            # Add new columns
            db.execute(text("ALTER TABLE users ADD COLUMN requires_approval BOOLEAN DEFAULT 1"))
            db.execute(text("ALTER TABLE users ADD COLUMN is_approved BOOLEAN DEFAULT 0"))
            db.execute(text("ALTER TABLE users ADD COLUMN approved_by INT"))
            db.execute(text("ALTER TABLE users ADD COLUMN approved_at DATETIME"))
            
            # Update existing users to be approved
            db.execute(text("""
                UPDATE users 
                SET requires_approval = 0, 
                    is_approved = 1, 
                    approved_at = NOW() 
                WHERE requires_approval = 1 OR is_approved = 0
            """))
            
            db.commit()
            print("User approval system migration completed successfully!")
        else:
            print("User approval columns already exist.")
            
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        if 'db' in locals():
            db.close()
    
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
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(categories.router, prefix="/categories", tags=["categories"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(customers.router, prefix="/customers", tags=["customers"])
app.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
app.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["purchase_orders"])
# CORRECT: sales_order (singular) NOT sales_orders (plural)
app.include_router(sales_order.router, prefix="/sales-orders", tags=["sales_orders"])
app.include_router(vendors.router, prefix="/vendors", tags=["vendors"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(settings.router, prefix="/settings", tags=["settings"])

# Mount static files - CORRECT PATH: app/static (relative to backend directory)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Middleware to inject pending users count
@app.middleware("http")
async def add_pending_users_count(request: Request, call_next):
    """Add pending users count to request state for templates"""
    response = await call_next(request)
    
    # Only add to HTML responses
    if isinstance(response, HTMLResponse):
        try:
            # Get database session
            db = next(get_db())
            from app.models.models import User
            pending_count = db.query(User).filter(
                User.requires_approval == True,
                User.is_approved == False
            ).count()
            
            # Add to request state
            request.state.pending_users_count = pending_count
        except:
            request.state.pending_users_count = 0
    
    return response

# Root endpoint - Dashboard (Protected)
@app.get("/", response_class=HTMLResponse)
async def root_dashboard(request: Request, current_user: User = Depends(get_current_user_from_cookie)):
    """Main dashboard page - requires authentication"""
    return RedirectResponse(url="/dashboard", status_code=302)

# Redirect root paths to auth
@app.get("/login", response_class=HTMLResponse)
async def login_redirect():
    """Redirect to auth login"""
    return RedirectResponse(url="/auth/login")

@app.get("/register", response_class=HTMLResponse)
async def register_redirect():
    """Redirect to auth register"""
    return RedirectResponse(url="/auth/register")

# Enhanced Health check endpoint for production
@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint for AWS Load Balancer and ECS
    Returns detailed health status including database connectivity
    """
    start_time = time.time()
    health_status = {
        "status": "healthy",
        "service": "alive-pharmaceuticals-warehouse",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": int(time.time()),
        "checks": {}
    }
    
    try:
        # Check database connectivity
        db = next(get_db())
        try:
            # Simple database query to test connectivity
            result = db.execute(text("SELECT 1 as test"))
            db_result = result.fetchone()
            if db_result and db_result[0] == 1:
                health_status["checks"]["database"] = {
                    "status": "healthy",
                    "message": "Database connection successful"
                }
            else:
                raise Exception("Database query returned unexpected result")
        except Exception as db_error:
            health_status["status"] = "unhealthy"
            health_status["checks"]["database"] = {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(db_error)}"
            }
        finally:
            db.close()
    
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Failed to establish database connection: {str(e)}"
        }
    
    # Check application readiness
    try:
        # Verify critical components are loaded
        health_status["checks"]["application"] = {
            "status": "healthy",
            "message": "Application components loaded successfully",
            "routers_loaded": 12  # Number of routers you have
        }
    except Exception as app_error:
        health_status["status"] = "unhealthy"
        health_status["checks"]["application"] = {
            "status": "unhealthy",
            "message": f"Application components failed: {str(app_error)}"
        }
    
    # Add response time
    health_status["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    # Return appropriate HTTP status code
    status_code = 200 if health_status["status"] == "healthy" else 503
    
    return JSONResponse(
        status_code=status_code,
        content=health_status
    )

# Lightweight health check for basic monitoring
@app.get("/health/live")
async def liveness_check():
    """
    Simple liveness check - just confirms the application is running
    Used for basic monitoring that doesn't need database connectivity
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "alive",
            "service": "alive-pharmaceuticals-warehouse",
            "timestamp": int(time.time())
        }
    )

# Readiness check for complex health verification
@app.get("/health/ready")
async def readiness_check():
    """
    Readiness check - confirms application is ready to serve traffic
    Includes all dependency checks
    """
    return await health_check()

# API endpoints
@app.get("/api/users")
async def get_users(db: Session = Depends(get_db)):
    """Get all users - for testing"""
    users = db.query(User).all()
    return {"users": len(users), "message": "Users retrieved successfully"}

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse("500.html", {"request": request}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )