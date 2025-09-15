# warehouse_management_system/backend/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import Base
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./warehouse_db.sqlite")

# Debug: Print the actual DATABASE_URL Railway is providing
print("=" * 80)
print("RAILWAY DATABASE DEBUG - START")
print("=" * 80)
print(f"DATABASE_URL from Railway = '{DATABASE_URL}'")
print(f"Length of DATABASE_URL = {len(DATABASE_URL)}")
print(f"DATABASE_URL starts with: '{DATABASE_URL[:20]}...'")
print("All DATABASE/MYSQL environment variables:")
for key, value in os.environ.items():
    if 'DATABASE' in key.upper() or 'MYSQL' in key.upper():
        if 'PASSWORD' in key.upper():
            print(f"  {key} = ***HIDDEN*** (length: {len(value)})")
        else:
            print(f"  {key} = {value}")
print("=" * 80)
print("RAILWAY DATABASE DEBUG - END") 
print("=" * 80)

# Global variables for lazy initialization
_engine = None
_SessionLocal = None

def get_engine():
    global _engine
    if _engine is None:
        print("DEBUG: Creating SQLAlchemy engine...")
        # Create SQLAlchemy engine
        _engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=True  # Set to False in production
        )
        print("DEBUG: Engine created successfully")
    return _engine

def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print("DEBUG: SessionLocal created successfully")
    return _SessionLocal

# Keep these for backward compatibility
engine = None  # Will be created lazily
SessionLocal = None  # Will be created lazily

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
    print("DEBUG: About to create all tables...")
    Base.metadata.create_all(bind=engine)
    print("DEBUG: Tables created successfully")

# Function to drop all tables (for development only)
def drop_tables():
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)