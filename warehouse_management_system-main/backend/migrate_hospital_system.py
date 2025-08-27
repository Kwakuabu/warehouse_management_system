#!/usr/bin/env python3
"""
Migration script to add hospital_id to users and create hospital inventory
This script should be run after updating the models to add the new fields
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Migrate the existing database to support hospital-specific data"""
    
    db_path = "warehouse_db.sqlite"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Starting database migration...")
        
        # 1. Add hospital_id column to users table
        print("1. Adding hospital_id column to users table...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN hospital_id INTEGER REFERENCES customers(id)")
            print("   ✓ Added hospital_id column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("   ✓ hospital_id column already exists")
            else:
                print(f"   ✗ Error adding hospital_id column: {e}")
        
        # 2. Create hospital_inventory table
        print("2. Creating hospital_inventory table...")
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hospital_inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hospital_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    current_stock INTEGER DEFAULT 0,
                    reorder_point INTEGER DEFAULT 5,
                    max_stock INTEGER DEFAULT 100,
                    last_restocked DATETIME,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (hospital_id) REFERENCES customers (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """)
            print("   ✓ Created hospital_inventory table")
        except sqlite3.OperationalError as e:
            print(f"   ✗ Error creating hospital_inventory table: {e}")
        
        # 3. Assign hospitals to existing staff users
        print("3. Assigning hospitals to existing staff users...")
        
        # Get all customers (hospitals)
        cursor.execute("SELECT id, name FROM customers WHERE is_active = 1")
        hospitals = cursor.fetchall()
        
        if not hospitals:
            print("   ⚠ No hospitals found in customers table")
        else:
            # Get all staff users without hospital_id
            cursor.execute("SELECT id, username, full_name FROM users WHERE role = 'staff' AND hospital_id IS NULL")
            staff_users = cursor.fetchall()
            
            if not staff_users:
                print("   ✓ No staff users need hospital assignment")
            else:
                # Assign first hospital to first staff user, second to second, etc.
                for i, (user_id, username, full_name) in enumerate(staff_users):
                    hospital_id = hospitals[i % len(hospitals)][0]
                    hospital_name = hospitals[i % len(hospitals)][1]
                    
                    cursor.execute(
                        "UPDATE users SET hospital_id = ? WHERE id = ?",
                        (hospital_id, user_id)
                    )
                    print(f"   ✓ Assigned {username} ({full_name}) to hospital: {hospital_name}")
        
        # 4. Create sample hospital inventory data
        print("4. Creating sample hospital inventory data...")
        
        # Get all products
        cursor.execute("SELECT id, name FROM products WHERE is_active = 1")
        products = cursor.fetchall()
        
        if not products:
            print("   ⚠ No products found")
        else:
            # Get all hospitals
            cursor.execute("SELECT id, name FROM customers WHERE is_active = 1")
            hospitals = cursor.fetchall()
            
            if not hospitals:
                print("   ⚠ No hospitals found")
            else:
                # Create sample inventory for each hospital
                for hospital_id, hospital_name in hospitals:
                    print(f"   Creating inventory for {hospital_name}...")
                    
                    for product_id, product_name in products:
                        # Check if inventory already exists
                        cursor.execute(
                            "SELECT id FROM hospital_inventory WHERE hospital_id = ? AND product_id = ?",
                            (hospital_id, product_id)
                        )
                        
                        if not cursor.fetchone():
                            # Create sample inventory
                            current_stock = 50  # Sample stock
                            reorder_point = 10  # Sample reorder point
                            max_stock = 100     # Sample max stock
                            
                            cursor.execute("""
                                INSERT INTO hospital_inventory 
                                (hospital_id, product_id, current_stock, reorder_point, max_stock, last_restocked)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (hospital_id, product_id, current_stock, reorder_point, max_stock, datetime.now()))
                            
                            print(f"     ✓ Added {product_name}: {current_stock} units")
                        else:
                            print(f"     ✓ {product_name} already has inventory")
        
        # Commit all changes
        conn.commit()
        print("\n✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
