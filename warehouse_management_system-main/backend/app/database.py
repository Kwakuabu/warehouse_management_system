# warehouse_management_system/backend/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import Base
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment variable - Railway MySQL
DATABASE_URL = os.getenv("MYSQL_URL", os.getenv("DATABASE_URL", "sqlite:///./warehouse_db.sqlite"))

print(f"DEBUG: Raw DATABASE_URL: {DATABASE_URL}")

# Convert MySQL URL to use PyMySQL driver
if DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
    print("DEBUG: Converted mysql:// to mysql+pymysql://")

# Handle Railway PostgreSQL URL format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    print("DEBUG: Converted postgres:// to postgresql://")

print(f"DEBUG: Final DATABASE_URL: {DATABASE_URL}")

# Create SQLAlchemy engine with better error handling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,  # Set to False in production
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create all tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Function to drop all tables (for development only)
def drop_tables():
    Base.metadata.drop_all(bind=engine)