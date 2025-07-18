import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models.models import Base
from main import app

# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test database tables
Base.metadata.create_all(bind=engine)

def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    """Test client fixture"""
    with TestClient(app) as c:
        yield c

@pytest.fixture
def db_session():
    """Database session fixture"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    from app.models.models import User
    from app.utils.auth import get_password_hash
    
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("testpassword"),
        role="admin"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(client, test_user):
    """Get authenticated headers"""
    response = client.post("/auth/token", data={
        "username": "testuser",
        "password": "testpassword"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sample_category(db_session):
    """Create a sample category"""
    from app.models.models import Category
    
    category = Category(
        name="Test Category",
        description="Test category description"
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category

@pytest.fixture
def sample_vendor(db_session):
    """Create a sample vendor"""
    from app.models.models import Vendor
    
    vendor = Vendor(
        name="Test Vendor",
        contact_person="John Doe",
        email="vendor@example.com",
        phone="+1234567890",
        address="123 Test St",
        country="Test Country",
        payment_terms="Net 30",
        lead_time_days=30
    )
    db_session.add(vendor)
    db_session.commit()
    db_session.refresh(vendor)
    return vendor

@pytest.fixture
def sample_product(db_session, sample_category, sample_vendor):
    """Create a sample product"""
    from app.models.models import Product
    
    product = Product(
        sku="TEST-001",
        name="Test Product",
        description="Test product description",
        category_id=sample_category.id,
        vendor_id=sample_vendor.id,
        unit_of_measure="pcs",
        reorder_point=10,
        max_stock_level=1000,
        requires_cold_chain=False,
        is_controlled_substance=False
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product 