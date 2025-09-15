# warehouse_management_system/backend/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import Base
import os
from dotenv import load_dotenv

load_dotenv()

# Simple database URL configuration
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("MYSQL_URL", "sqlite:///./warehouse_db.sqlite")

# Debug: Print what we actually have
print("DEBUG: Available environment variables:")
import os
for key in sorted(os.environ.keys()):
    if any(keyword in key.upper() for keyword in ['DATABASE', 'MYSQL', 'DB']):
        value = os.environ[key]
        if 'PASSWORD' in key.upper():
            print(f"  {key}=***masked***")
        else:
            print(f"  {key}={value}")

# Convert mysql:// to mysql+pymysql:// if needed
if DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

print(f"DEBUG: Final DATABASE_URL: {DATABASE_URL}")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False
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