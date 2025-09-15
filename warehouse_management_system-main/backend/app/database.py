# warehouse_management_system/backend/app/database.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.models import Base
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL configuration for Railway
def get_database_url():
    # Print all environment variables for debugging
    import os
    print("DEBUG: All environment variables:")
    for key, value in sorted(os.environ.items()):
        if any(keyword in key.upper() for keyword in ['DATABASE', 'MYSQL', 'DB']):
            # Mask password for security
            if 'PASSWORD' in key.upper():
                print(f"  {key}=***masked***")
            else:
                print(f"  {key}={value}")
    
    # Check if we're in Railway environment
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        print(f"DEBUG: Found DATABASE_URL")
        return database_url
    
    # Check for Railway MySQL environment variables
    mysql_host = os.getenv("MYSQLHOST") or os.getenv("MYSQL_HOST")
    mysql_port = os.getenv("MYSQLPORT", "3306") or os.getenv("MYSQL_PORT", "3306")
    mysql_database = os.getenv("MYSQLDATABASE") or os.getenv("MYSQL_DATABASE")
    mysql_user = os.getenv("MYSQLUSER", "root") or os.getenv("MYSQL_USER", "root")
    mysql_password = (os.getenv("MYSQLPASSWORD") or os.getenv("MYSQL_PASSWORD") or 
                     os.getenv("MYSQL_ROOT_PASSWORD") or os.getenv("MYSQLROOTPASSWORD"))
    
    print(f"DEBUG: MySQL vars - host:{mysql_host}, port:{mysql_port}, db:{mysql_database}, user:{mysql_user}")
    
    if all([mysql_host, mysql_database, mysql_password]):
        # Build MySQL URL for Railway
        url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8mb4"
        print(f"DEBUG: Built MySQL URL with host: {mysql_host}")
        return url
    
    print("DEBUG: No MySQL variables found, falling back to SQLite")
    # Fallback to SQLite for local development
    return "sqlite:///./warehouse_db.sqlite"

DATABASE_URL = get_database_url()
print(f"DEBUG: Final database URL: {DATABASE_URL}")

# Create SQLAlchemy engine with retry logic
def create_database_engine():
    try:
        # Try the configured database URL first
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False  # Disable echo in production
        )
        
        # Test the connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("DEBUG: Database connection successful!")
            return engine
            
    except Exception as e:
        print(f"DEBUG: Failed to connect to {DATABASE_URL}: {e}")
        
        # If MySQL fails, fallback to SQLite
        if "mysql" in DATABASE_URL.lower():
            print("DEBUG: Falling back to SQLite for development...")
            sqlite_url = "sqlite:///./warehouse_db.sqlite"
            engine = create_engine(
                sqlite_url,
                pool_pre_ping=True,
                pool_recycle=300,
                echo=False
            )
            print(f"DEBUG: Using SQLite fallback: {sqlite_url}")
            return engine
        else:
            raise

engine = create_database_engine()

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