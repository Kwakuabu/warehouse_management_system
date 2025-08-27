# warehouse_management_system/backend/app/models/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="staff")  # admin, manager, staff
    hospital_id = Column(Integer, ForeignKey("customers.id"), nullable=True)  # Link staff to hospital
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    hospital = relationship("Customer", foreign_keys=[hospital_id])

class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    contact_person = Column(String(100))
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)
    country = Column(String(50))
    payment_terms = Column(String(50))  # Net 30, Net 60, etc.
    lead_time_days = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    products = relationship("Product", back_populates="vendor")
    purchase_orders = relationship("PurchaseOrder", back_populates="vendor")

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # Hospital name
    contact_person = Column(String(100))
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)
    city = Column(String(50))
    credit_limit = Column(DECIMAL(12, 2), default=0.00)
    payment_terms = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sales_orders = relationship("SalesOrder", back_populates="customer")
    hospital_inventory = relationship("HospitalInventory", back_populates="hospital")
    staff_users = relationship("User", foreign_keys="User.hospital_id", back_populates="hospital")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(Text)
    
    # Relationships
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey("categories.id"))
    vendor_id = Column(Integer, ForeignKey("vendors.id"))
    unit_of_measure = Column(String(20), default="pcs")  # pcs, boxes, ml, etc.
    unit_price = Column(DECIMAL(10, 2), default=0.00)  # Added missing field
    cost_price = Column(DECIMAL(10, 2), default=0.00)  # Added missing field
    reorder_point = Column(Integer, default=10)
    max_stock_level = Column(Integer, default=1000)
    storage_temperature_min = Column(Float)  # Celsius
    storage_temperature_max = Column(Float)  # Celsius
    requires_cold_chain = Column(Boolean, default=False)
    is_controlled_substance = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship("Category", back_populates="products")
    vendor = relationship("Vendor", back_populates="products")
    inventory_items = relationship("InventoryItem", back_populates="product")
    purchase_order_items = relationship("PurchaseOrderItem", back_populates="product")
    sales_order_items = relationship("SalesOrderItem", back_populates="product")
    
    @property
    def stock_quantity(self):
        """Calculate total available stock from all inventory items"""
        if self.inventory_items:
            return sum(item.quantity_available for item in self.inventory_items if item.status == "available")
        return 0

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    batch_number = Column(String(50), nullable=False)
    manufacture_date = Column(DateTime)
    expiry_date = Column(DateTime)
    quantity_available = Column(Integer, nullable=False, default=0)
    quantity_reserved = Column(Integer, default=0)  # Reserved for orders
    cost_price = Column(DECIMAL(10, 2), nullable=False)
    selling_price = Column(DECIMAL(10, 2), nullable=False)
    location = Column(String(50))  # Warehouse location (A1, B2, etc.)
    temperature_log = Column(Text)  # JSON string for temperature readings
    status = Column(String(20), default="available")  # available, reserved, expired, damaged
    received_date = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="inventory_items")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(50), unique=True, index=True, nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow)
    expected_delivery_date = Column(DateTime)
    actual_delivery_date = Column(DateTime)
    status = Column(String(20), default="pending")  # pending, confirmed, shipped, received, cancelled
    total_amount = Column(DECIMAL(12, 2), default=0.00)
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    vendor = relationship("Vendor", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order")

class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity_ordered = Column(Integer, nullable=False)
    quantity_received = Column(Integer, default=0)
    unit_cost = Column(DECIMAL(10, 2), nullable=False)
    total_cost = Column(DECIMAL(12, 2), nullable=False)
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product", back_populates="purchase_order_items")

class SalesOrder(Base):
    __tablename__ = "sales_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow)
    delivery_date = Column(DateTime)
    status = Column(String(20), default="pending")  # pending, confirmed, shipped, delivered, cancelled
    total_amount = Column(DECIMAL(12, 2), default=0.00)
    discount_percentage = Column(Float, default=0.0)
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    customer = relationship("Customer", back_populates="sales_orders")
    items = relationship("SalesOrderItem", back_populates="sales_order")

class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"))
    quantity_ordered = Column(Integer, nullable=False)
    quantity_shipped = Column(Integer, default=0)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    total_price = Column(DECIMAL(12, 2), nullable=False)
    
    # Relationships
    sales_order = relationship("SalesOrder", back_populates="items")
    product = relationship("Product", back_populates="sales_order_items")
    inventory_item = relationship("InventoryItem")

class StockMovement(Base):
    __tablename__ = "stock_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"))
    movement_type = Column(String(20), nullable=False)  # in, out, adjustment, transfer
    quantity = Column(Integer, nullable=False)
    reference_type = Column(String(20))  # purchase_order, sales_order, adjustment
    reference_id = Column(Integer)
    reference_number = Column(String(50))  # Added missing field
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(30), nullable=False)  # low_stock, expiry_warning, temperature_alert
    product_id = Column(Integer, ForeignKey("products.id"))
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"))
    message = Column(String(500), nullable=False)
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey("users.id"))
    acknowledged_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class HospitalInventory(Base):
    __tablename__ = "hospital_inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("customers.id"), nullable=False)  # Hospital customer
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)  # Product
    current_stock = Column(Integer, default=0)  # Current hospital stock
    reorder_point = Column(Integer, default=5)  # Hospital-specific reorder point
    max_stock = Column(Integer, default=100)  # Hospital-specific max stock
    last_restocked = Column(DateTime)  # Last time hospital received stock
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    hospital = relationship("Customer", foreign_keys=[hospital_id])
    product = relationship("Product")