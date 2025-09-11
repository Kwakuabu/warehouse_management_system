# app/routes/auth.py
from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User
from app.models.schemas import UserCreate, User as UserSchema, Token
from app.utils.auth import (
    authenticate_user, 
    create_access_token, 
    get_password_hash,
    get_user_by_username,
    get_user_by_email,
    get_current_active_user_from_cookie,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Login page
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Display login page"""
    return templates.TemplateResponse("login.html", {"request": request})

# Register page
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Display registration page"""
    return templates.TemplateResponse("register.html", {"request": request})

# API: Login for token
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user and return access token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# API: Register new user
@router.post("/register", response_model=UserSchema)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if username already exists
    db_user = get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # Check if email already exists
    db_user = get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Validate hospital assignment for staff users
    if user.role == "staff":
        if not user.hospital_id:
            raise HTTPException(status_code=400, detail="Staff users must be assigned to a hospital")
        
        # Verify the hospital exists and is a valid hospital
        from app.models.models import Customer
        hospital = db.query(Customer).filter(
            Customer.id == user.hospital_id,
            Customer.is_active == True
        ).first()
        
        if not hospital:
            raise HTTPException(status_code=400, detail="Selected hospital not found")
        
        # Check if it's a valid hospital (not "Nathaniel Amponsah" which is ID 1)
        if user.hospital_id == 1:  # Nathaniel Amponsah is not a hospital
            raise HTTPException(status_code=400, detail="Please select a valid hospital")
    
    # Create new user (pending approval)
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        role=user.role,
        hospital_id=user.hospital_id if user.role == "staff" else None,  # Assign hospital for staff users
        requires_approval=True,
        is_approved=False,
        is_active=False  # Inactive until approved
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Form-based login (for web interface)
@router.post("/login")
async def login_form(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle form-based login"""
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Invalid username or password"}
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Redirect to dashboard with token (in a real app, you'd use secure cookies)
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

# Form-based registration (for web interface)
@router.post("/register-form")
async def register_form(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    role: str = Form("staff"),
    hospital_id: str = Form(""),
    db: Session = Depends(get_db)
):
    """Handle form-based registration"""
    # Validate passwords match
    if password != confirm_password:
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "error": "Passwords do not match"}
        )
    
    # Check if username exists
    if get_user_by_username(db, username):
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "error": "Username already exists"}
        )
    
    # Check if email exists
    if get_user_by_email(db, email):
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "error": "Email already registered"}
        )
    
    # Initialize hospital_id_int
    hospital_id_int = None
    
    # Validate hospital assignment for staff users
    if role == "staff":
        if not hospital_id or hospital_id.strip() == "":
            return templates.TemplateResponse(
                "register.html", 
                {"request": request, "error": "Staff users must be assigned to a hospital"}
            )
        
        # Convert hospital_id to integer
        try:
            hospital_id_int = int(hospital_id)
        except ValueError:
            return templates.TemplateResponse(
                "register.html", 
                {"request": request, "error": "Invalid hospital selection"}
            )
        
        # Verify the hospital exists and is a valid hospital (not a regular customer)
        from app.models.models import Customer
        hospital = db.query(Customer).filter(
            Customer.id == hospital_id_int,
            Customer.is_active == True
        ).first()
        
        if not hospital:
            return templates.TemplateResponse(
                "register.html", 
                {"request": request, "error": "Selected hospital not found"}
            )
        
        # Check if it's a valid hospital (not "Nathaniel Amponsah" which is ID 1)
        if hospital_id_int == 1:  # Nathaniel Amponsah is not a hospital
            return templates.TemplateResponse(
                "register.html", 
                {"request": request, "error": "Please select a valid hospital"}
            )
    
    # Create user (pending approval)
    hashed_password = get_password_hash(password)
    db_user = User(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=hashed_password,
        role=role,
        hospital_id=hospital_id_int,  # Will be None for non-staff users
        requires_approval=True,
        is_approved=False,
        is_active=False  # Inactive until approved
    )
    db.add(db_user)
    db.commit()
    
    # Redirect to login page with pending approval message
    return RedirectResponse(url="/login?message=Registration submitted successfully. Your account is pending admin approval.", status_code=302)

# Get current user info
@router.get("/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(get_current_active_user_from_cookie)):
    """Get current user information"""
    return current_user

# Admin approval routes
@router.get("/pending-users", response_class=HTMLResponse)
async def pending_users_page(
    request: Request,
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Display pending users for admin approval"""
    if current_user.role not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    pending_users = db.query(User).filter(
        User.requires_approval == True,
        User.is_approved == False
    ).all()
    
    return templates.TemplateResponse(
        "auth/pending_users.html", 
        {"request": request, "pending_users": pending_users, "current_user": current_user}
    )

@router.post("/approve-user/{user_id}")
async def approve_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Approve a pending user"""
    if current_user.role not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.requires_approval or user.is_approved:
        raise HTTPException(status_code=400, detail="User does not require approval")
    
    # Approve the user
    user.is_approved = True
    user.is_active = True
    user.approved_by = current_user.id
    user.approved_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": f"User {user.username} has been approved successfully"}

@router.post("/reject-user/{user_id}")
async def reject_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Reject a pending user"""
    if current_user.role not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.requires_approval or user.is_approved:
        raise HTTPException(status_code=400, detail="User does not require approval")
    
    # Delete the rejected user
    db.delete(user)
    db.commit()
    
    return {"message": f"User {user.username} has been rejected and removed"}

# Logout
@router.post("/logout")
async def logout():
    """Logout user"""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response