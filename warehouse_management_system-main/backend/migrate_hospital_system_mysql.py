#!/usr/bin/env python3
"""
MySQL Migration script to add hospital_id to users and create hospital inventory
This script should be run on your XAMPP MySQL database
"""

import pymysql
import os
from datetime import datetime

def migrate_mysql_database():
    """Migrate the MySQL database to support hospital-specific data"""
    
    # MySQL connection details - adjust these to match your XAMPP setup
    mysql_config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',           # XAMPP default username
        'password': '',           # XAMPP default password (empty)
        'database': 'warehouse_db', # Your database name
        'charset': 'utf8mb4'
    }
    
    try:
        print("Connecting to MySQL database...")
        conn = pymysql.connect(**mysql_config)
        cursor = conn.cursor()
        
        print("✅ Connected to MySQL database successfully!")
        print("Starting Hospital System Migration...")
        print("=" * 60)
        
        # 1. Add hospital_id column to users table
        print("1. Adding hospital_id column to users table...")
        try:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN hospital_id INT NULL,
                ADD CONSTRAINT fk_users_hospital 
                FOREIGN KEY (hospital_id) REFERENCES customers(id)
            """)
            print("   ✓ Added hospital_id column with foreign key constraint")
        except pymysql.err.OperationalError as e:
            if "Duplicate column name" in str(e):
                print("   ✓ hospital_id column already exists")
            else:
                print(f"   ✗ Error adding hospital_id column: {e}")
        
        # 2. Create hospital_inventory table
        print("2. Creating hospital_inventory table...")
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hospital_inventory (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    hospital_id INT NOT NULL,
                    product_id INT NOT NULL,
                    current_stock INT DEFAULT 0,
                    reorder_point INT DEFAULT 5,
                    max_stock INT DEFAULT 100,
                    last_restocked DATETIME NULL,
                    notes TEXT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (hospital_id) REFERENCES customers(id),
                    FOREIGN KEY (product_id) REFERENCES products(id),
                    UNIQUE KEY unique_hospital_product (hospital_id, product_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("   ✓ Created hospital_inventory table")
        except pymysql.err.OperationalError as e:
            print(f"   ✓ hospital_inventory table already exists or error: {e}")
        
        # 3. Create sample hospitals (customers) if they don't exist
        print("3. Creating sample hospitals...")
        hospitals = [
            {
                "name": "City General Hospital",
                "contact_person": "Dr. Sarah Johnson",
                "email": "procurement@citygeneral.com",
                "phone": "+1-555-0101",
                "address": "123 Medical Center Blvd, City, State 12345",
                "city": "City",
                "credit_limit": 50000.00,
                "payment_terms": "Net 30"
            },
            {
                "name": "Regional Medical Center",
                "contact_person": "Dr. Michael Chen",
                "email": "supplies@regionalmed.com",
                "phone": "+1-555-0102",
                "address": "456 Healthcare Ave, Town, State 67890",
                "city": "Town",
                "credit_limit": 75000.00,
                "payment_terms": "Net 45"
            },
            {
                "name": "Community Health Hospital",
                "contact_person": "Dr. Emily Rodriguez",
                "email": "inventory@communityhealth.com",
                "phone": "+1-555-0103",
                "address": "789 Wellness Street, Village, State 11111",
                "city": "Village",
                "credit_limit": 30000.00,
                "payment_terms": "Net 30"
            }
        ]
        
        for hospital in hospitals:
            cursor.execute("""
                INSERT IGNORE INTO customers 
                (name, contact_person, email, phone, address, city, credit_limit, payment_terms, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, %s)
            """, (
                hospital["name"], hospital["contact_person"], hospital["email"],
                hospital["phone"], hospital["address"], hospital["city"],
                hospital["credit_limit"], hospital["payment_terms"], datetime.now()
            ))
            print(f"   ✓ Created hospital: {hospital['name']}")
        
        # 4. Create sample products if they don't exist
        print("4. Creating sample products...")
        products = [
            {
                "sku": "DIAL-001",
                "name": "High-Flux Dialyzer F8",
                "description": "High-efficiency dialyzer for hemodialysis treatment",
                "category_id": 1,  # Dialyzers
                "vendor_id": 1,    # Fresenius
                "unit_of_measure": "pcs",
                "unit_price": 45.00,
                "cost_price": 35.00,
                "reorder_point": 20,
                "max_stock_level": 200,
                "requires_cold_chain": False,
                "is_controlled_substance": False
            },
            {
                "sku": "TUBE-001",
                "name": "Blood Tubing Set",
                "description": "Complete blood tubing set for dialysis machine",
                "category_id": 2,  # Blood Tubing
                "vendor_id": 2,    # Baxter
                "unit_of_measure": "pcs",
                "unit_price": 25.00,
                "cost_price": 18.00,
                "reorder_point": 30,
                "max_stock_level": 150,
                "requires_cold_chain": False,
                "is_controlled_substance": False
            },
            {
                "sku": "CONC-001",
                "name": "Dialysis Concentrate A",
                "description": "Acid concentrate for dialysis solution",
                "category_id": 3,  # Concentrates
                "vendor_id": 3,    # Nipro
                "unit_of_measure": "L",
                "unit_price": 15.00,
                "cost_price": 12.00,
                "reorder_point": 50,
                "max_stock_level": 300,
                "requires_cold_chain": True,
                "is_controlled_substance": False
            }
        ]
        
        for product in products:
            cursor.execute("""
                INSERT IGNORE INTO products 
                (sku, name, description, category_id, vendor_id, unit_of_measure, unit_price, cost_price,
                 reorder_point, max_stock_level, requires_cold_chain, is_controlled_substance, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s)
            """, (
                product["sku"], product["name"], product["description"], product["category_id"],
                product["vendor_id"], product["unit_of_measure"], product["unit_price"], product["cost_price"],
                product["reorder_point"], product["max_stock_level"], product["requires_cold_chain"],
                product["is_controlled_substance"], datetime.now()
            ))
            print(f"   ✓ Created product: {product['name']} ({product['sku']})")
        
        # 5. Assign staff users to hospitals
        print("5. Assigning staff users to hospitals...")
        
        # Get hospital IDs
        cursor.execute("SELECT id, name FROM customers WHERE is_active = 1")
        hospitals = cursor.fetchall()
        
        # Get staff users
        cursor.execute("SELECT id, username FROM users WHERE role = 'staff'")
        staff_users = cursor.fetchall()
        
        if hospitals and staff_users:
            # Assign first hospital to first staff user, second to second, etc.
            for i, (user_id, username) in enumerate(staff_users):
                hospital_id = hospitals[i % len(hospitals)][0]
                hospital_name = hospitals[i % len(hospitals)][1]
                
                cursor.execute(
                    "UPDATE users SET hospital_id = %s WHERE id = %s",
                    (hospital_id, user_id)
                )
                print(f"   ✓ Assigned {username} to hospital: {hospital_name}")
        
        # 6. Create sample hospital inventory
        print("6. Creating sample hospital inventory...")
        
        # Get all products and hospitals
        cursor.execute("SELECT id FROM products WHERE is_active = 1")
        product_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM customers WHERE is_active = 1")
        hospital_ids = [row[0] for row in cursor.fetchall()]
        
        if product_ids and hospital_ids:
            for hospital_id in hospital_ids:
                print(f"   Creating inventory for hospital ID {hospital_id}...")
                
                for product_id in product_ids:
                    # Create sample inventory with realistic values
                    current_stock = 50  # Sample stock
                    reorder_point = 10  # Sample reorder point
                    max_stock = 100     # Sample max stock
                    
                    cursor.execute("""
                        INSERT IGNORE INTO hospital_inventory 
                        (hospital_id, product_id, current_stock, reorder_point, max_stock, last_restocked, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (hospital_id, product_id, current_stock, reorder_point, max_stock, datetime.now(), datetime.now()))
                    
                    print(f"     ✓ Added product ID {product_id}: {current_stock} units")
        
        # Commit all changes
        conn.commit()
        print("\n" + "=" * 60)
        print("✅ MySQL Hospital System Migration Completed Successfully!")
        print(f"   - Added hospital_id column to users table")
        print(f"   - Created hospital_inventory table")
        print(f"   - Created {len(hospitals)} hospitals")
        print(f"   - Created {len(products)} products")
        print(f"   - Assigned staff users to hospitals")
        print(f"   - Created sample hospital inventory")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("MySQL Hospital System Migration Script")
    print("Make sure your XAMPP MySQL server is running!")
    print("You may need to adjust the database connection details below.")
    print()
    
    # Ask user to confirm database details
    print("Current MySQL connection details:")
    print("Host: localhost")
    print("Port: 3306")
    print("User: root")
    print("Password: (empty)")
    print("Database: warehouse_db")
    print()
    print("If these don't match your XAMPP setup, please edit the script first.")
    print()
    
    input("Press Enter to continue with migration...")
    migrate_mysql_database()
