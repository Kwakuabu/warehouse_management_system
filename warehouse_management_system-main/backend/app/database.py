# warehouse_management_system/backend/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import Base
import os
from dotenv import load_dotenv

load_dotenv()

# Global variables for lazy initialization
engine = None
SessionLocal = None

def get_database_url():
    """Get database URL with comprehensive debugging"""
    # Print ALL environment variables for debugging
    print("=" * 50)
    print("DEBUG: ALL ENVIRONMENT VARIABLES")
    print("=" * 50)
    for key in sorted(os.environ.keys()):
        if any(keyword in key.upper() for keyword in ['DATABASE', 'MYSQL', 'DB', 'URL']):
            value = os.environ[key]
            if 'PASSWORD' in key.upper() or 'PASS' in key.upper():
                print(f"{key} = ***MASKED***")
            else:
                print(f"{key} = {value}")

    print("=" * 50)

    # Database URL from environment variable - Railway MySQL
    mysql_url = os.getenv("MYSQL_URL")
    database_url = os.getenv("DATABASE_URL")

    print(f"DEBUG: MYSQL_URL = {mysql_url}")
    print(f"DEBUG: DATABASE_URL = {database_url}")

    # Choose the URL
    DATABASE_URL = mysql_url or database_url or "sqlite:///./warehouse_db.sqlite"
    print(f"DEBUG: Chosen DATABASE_URL = {DATABASE_URL}")

    # Convert MySQL URL to use PyMySQL driver
    if DATABASE_URL.startswith("mysql://"):
        DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
        print("DEBUG: Converted mysql:// to mysql+pymysql://")

    # Handle Railway PostgreSQL URL format
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        print("DEBUG: Converted postgres:// to postgresql://")

    print(f"DEBUG: Final DATABASE_URL = {DATABASE_URL}")
    print("=" * 50)
    
    return DATABASE_URL

def initialize_database():
    """Initialize database connection lazily"""
    global engine, SessionLocal
    
    if engine is None:
        DATABASE_URL = get_database_url()
        
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
        print("DEBUG: Database initialized successfully")
    
    return engine, SessionLocal

# Dependency to get database session
def get_db():
    engine, SessionLocal = initialize_database()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create all tables
def create_tables():
    engine, SessionLocal = initialize_database()
    Base.metadata.create_all(bind=engine)

# Function to drop all tables (for development only)
def drop_tables():
    engine, SessionLocal = initialize_database()
    Base.metadata.drop_all(bind=engine)