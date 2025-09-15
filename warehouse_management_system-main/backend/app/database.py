# warehouse_management_system/backend/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import Base
import os
from dotenv import load_dotenv

load_dotenv()

# FORCE RAILWAY DEPLOYMENT - TIMESTAMP: 2025-09-15 7:35 PM
print("CORRECT DATABASE.PY LOADED - LAZY INITIALIZATION - TIMESTAMP 7:35 PM")
print("=" * 80)

# Database URL from environment variable - try multiple Railway variables
DATABASE_URL = (
    os.getenv("DATABASE_URL") or 
    os.getenv("MYSQL_URL") or 
    os.getenv("MYSQL_PUBLIC_URL") or 
    "sqlite:///./warehouse_db.sqlite"
)

# CRITICAL DEBUG - Print what Railway gave us
print("RAILWAY DEBUG: What DATABASE_URL did we get?")
print("=" * 80)
print(f"Raw DATABASE_URL: {repr(DATABASE_URL)}")
print(f"DATABASE_URL length: {len(DATABASE_URL) if DATABASE_URL else 'None'}")
if DATABASE_URL:
    print(f"DATABASE_URL first 50 chars: {DATABASE_URL[:50]}")
    print(f"DATABASE_URL last 50 chars: {DATABASE_URL[-50:]}")
print("=" * 80)

# Global variables for truly lazy initialization
_engine = None
_SessionLocal = None

def get_engine():
    global _engine
    if _engine is None:
        print(f"Creating engine with URL: {DATABASE_URL}")
        _engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=True
        )
    return _engine

def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal

# Dependency to get database session
def get_db():
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create all tables
def create_tables():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

# Function to drop all tables (for development only)
def drop_tables():
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)