# app/utils/seed_data.py
from sqlalchemy.orm import Session
from app.models.models import Category, Vendor, User
from app.utils.auth import get_password_hash

def seed_categories(db: Session):
    """Seed initial categories"""
    categories = [
        {"name": "Dialyzers", "description": "Artificial kidney filters for dialysis treatment"},
        {"name": "Blood Tubing", "description": "Tubing sets for blood circulation during dialysis"},
        {"name": "Concentrates", "description": "Dialysis fluid concentrates and solutions"},
        {"name": "Catheters", "description": "Vascular access devices for dialysis"},
        {"name": "Filters", "description": "Additional filtration devices"},
        {"name": "Accessories", "description": "Miscellaneous dialysis accessories"}
    ]
    
    for cat_data in categories:
        existing = db.query(Category).filter(Category.name == cat_data["name"]).first()
        if not existing:
            category = Category(name=cat_data["name"], description=cat_data["description"])
            db.add(category)
    
    db.commit()

def seed_vendors(db: Session):
    """Seed initial vendors"""
    vendors = [
        {
            "name": "Fresenius Medical Care",
            "contact_person": "John Smith",
            "email": "orders@fresenius.com",
            "phone": "+49-6172-609-0",
            "address": "Else-Kröner-Straße 1, 61352 Bad Homburg",
            "country": "Germany",
            "payment_terms": "Net 30",
            "lead_time_days": 21
        },
        {
            "name": "Baxter Healthcare",
            "contact_person": "Maria Rodriguez",
            "email": "procurement@baxter.com",
            "phone": "+1-847-948-2000",
            "address": "One Baxter Parkway, Deerfield, IL 60015",
            "country": "USA",
            "payment_terms": "Net 45",
            "lead_time_days": 28
        },
        {
            "name": "Nipro Corporation",
            "contact_person": "Hiroshi Tanaka",
            "email": "export@nipro.com",
            "phone": "+81-6-6372-2331",
            "address": "3-9-3 Honjo-Nishi, Kita-ku, Osaka",
            "country": "Japan",
            "payment_terms": "Net 30",
            "lead_time_days": 35
        },
        {
            "name": "B. Braun Medical",
            "contact_person": "Klaus Mueller",
            "email": "sales@bbraun.com",
            "phone": "+49-5661-71-0",
            "address": "Carl-Braun-Straße 1, 34212 Melsungen",
            "country": "Germany",
            "payment_terms": "Net 30",
            "lead_time_days": 25
        }
    ]
    
    for vendor_data in vendors:
        existing = db.query(Vendor).filter(Vendor.name == vendor_data["name"]).first()
        if not existing:
            vendor = Vendor(**vendor_data)
            db.add(vendor)
    
    db.commit()

def seed_users(db: Session):
    """Seed default users"""
    users = [
        {
            "username": "admin",
            "email": "admin@alivepharma.com",
            "full_name": "System Administrator",
            "password": "admin123",
            "role": "admin"
        },
        {
            "username": "manager",
            "email": "manager@alivepharma.com",
            "full_name": "Warehouse Manager",
            "password": "manager123",
            "role": "manager"
        },
        {
            "username": "staff",
            "email": "staff@alivepharma.com",
            "full_name": "Warehouse Staff",
            "password": "staff123",
            "role": "staff"
        }
    ]
    
    for user_data in users:
        existing = db.query(User).filter(User.username == user_data["username"]).first()
        if not existing:
            hashed_password = get_password_hash(user_data["password"])
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                hashed_password=hashed_password,
                role=user_data["role"],
                is_active=True
            )
            db.add(user)
    
    db.commit()

def seed_all_data(db: Session):
    """Seed all initial data"""
    seed_users(db)
    seed_categories(db)
    seed_vendors(db)
    print("Sample data seeded successfully!")