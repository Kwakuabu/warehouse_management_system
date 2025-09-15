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
print(f"DEBUG: DATABASE_URL from Railway = '{DATABASE_URL}'")
print(f"DEBUG: All DATABASE/MYSQL env vars:")
for key, value in os.environ.items():
    if 'DATABASE' in key.upper() or 'MYSQL' in key.upper():
        if 'PASSWORD' in key.upper():
            print(f"  {key} = ***HIDDEN***")
        else:
            print(f"  {key} = {value}")
print(f"DEBUG: Using final DATABASE_URL = '{DATABASE_URL}'")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=True  # Set to False in production
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