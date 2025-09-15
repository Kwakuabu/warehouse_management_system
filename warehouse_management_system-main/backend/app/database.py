# warehouse_management_system/backend/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import Base
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL configuration for Railway
def get_database_url():
    # Check if we're in Railway environment
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Use provided DATABASE_URL (works for Railway MySQL)
        return database_url
    
    # Check for Railway MySQL environment variables
    mysql_host = os.getenv("MYSQL_HOST")
    mysql_port = os.getenv("MYSQL_PORT", "3306")
    mysql_database = os.getenv("MYSQL_DATABASE")
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD") or os.getenv("MYSQL_ROOT_PASSWORD")
    
    if all([mysql_host, mysql_database, mysql_password]):
        # Build MySQL URL for Railway
        return f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8mb4"
    
    # Fallback to SQLite for local development
    return "sqlite:///./warehouse_db.sqlite"

DATABASE_URL = get_database_url()
print(f"DEBUG: Using database URL: {DATABASE_URL}")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Disable echo in production
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