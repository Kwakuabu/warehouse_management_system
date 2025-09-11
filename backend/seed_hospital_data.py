#!/usr/bin/env python3
"""
Comprehensive seed script to create hospitals, products, and assign staff users
This script populates the database with sample data for the hospital system
"""

import sqlite3
import os
from datetime import datetime

def seed_hospital_data():
    """Seed the database with hospital system data"""
    
    db_path = "warehouse_db.sqlite"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Starting Hospital System Data Seeding...")
        print("=" * 60)
        
        # 1. Create sample hospitals (customers)
        print("1. Creating sample hospitals...")
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
                INSERT OR IGNORE INTO customers 
                (name, contact_person, email, phone, address, city, credit_limit, payment_terms, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (
                hospital["name"], hospital["contact_person"], hospital["email"],
                hospital["phone"], hospital["address"], hospital["city"],
                hospital["credit_limit"], hospital["payment_terms"], datetime.now()
            ))
            print(f"   ✓ Created hospital: {hospital['name']}")
        
        # 2. Create sample products
        print("2. Creating sample products...")
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
            },
            {
                "sku": "CATH-001",
                "name": "Vascular Access Catheter",
                "description": "Temporary vascular access for dialysis",
                "category_id": 4,  # Catheters
                "vendor_id": 4,    # B. Braun
                "unit_of_measure": "pcs",
                "unit_price": 85.00,
                "cost_price": 65.00,
                "reorder_point": 15,
                "max_stock_level": 100,
                "requires_cold_chain": False,
                "is_controlled_substance": False
            },
            {
                "sku": "FILT-001",
                "name": "Ultrafilter Cartridge",
                "description": "Ultrafiltration cartridge for dialysis machines",
                "category_id": 5,  # Filters
                "vendor_id": 1,    # Fresenius
                "unit_of_measure": "pcs",
                "unit_price": 120.00,
                "cost_price": 95.00,
                "reorder_point": 10,
                "max_stock_level": 80,
                "requires_cold_chain": False,
                "is_controlled_substance": False
            }
        ]
        
        for product in products:
            cursor.execute("""
                INSERT OR IGNORE INTO products 
                (sku, name, description, category_id, vendor_id, unit_of_measure, unit_price, cost_price,
                 reorder_point, max_stock_level, requires_cold_chain, is_controlled_substance, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (
                product["sku"], product["name"], product["description"], product["category_id"],
                product["vendor_id"], product["unit_of_measure"], product["unit_price"], product["cost_price"],
                product["reorder_point"], product["max_stock_level"], product["requires_cold_chain"],
                product["is_controlled_substance"], datetime.now()
            ))
            print(f"   ✓ Created product: {product['name']} ({product['sku']})")
        
        # 3. Create sample inventory items
        print("3. Creating sample warehouse inventory...")
        inventory_items = [
            {"product_id": 1, "quantity_available": 150, "cost_price": 35.00, "batch_number": "B001-2024"},
            {"product_id": 2, "quantity_available": 100, "cost_price": 18.00, "batch_number": "B002-2024"},
            {"product_id": 3, "quantity_available": 200, "cost_price": 12.00, "batch_number": "B003-2024"},
            {"product_id": 4, "quantity_available": 75, "cost_price": 65.00, "batch_number": "B004-2024"},
            {"product_id": 5, "quantity_available": 50, "cost_price": 95.00, "batch_number": "B005-2024"}
        ]
        
        for item in inventory_items:
            cursor.execute("""
                INSERT OR IGNORE INTO inventory_items 
                (product_id, quantity_available, cost_price, batch_number, status, received_date, updated_at)
                VALUES (?, ?, ?, ?, 'available', ?, ?)
            """, (
                item["product_id"], item["quantity_available"], item["cost_price"],
                item["batch_number"], datetime.now(), datetime.now()
            ))
            print(f"   ✓ Created inventory item for product ID {item['product_id']}")
        
        # 4. Assign staff users to hospitals
        print("4. Assigning staff users to hospitals...")
        
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
                    "UPDATE users SET hospital_id = ? WHERE id = ?",
                    (hospital_id, user_id)
                )
                print(f"   ✓ Assigned {username} to hospital: {hospital_name}")
        
        # 5. Create sample hospital inventory
        print("5. Creating sample hospital inventory...")
        
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
                        INSERT OR IGNORE INTO hospital_inventory 
                        (hospital_id, product_id, current_stock, reorder_point, max_stock, last_restocked, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (hospital_id, product_id, current_stock, reorder_point, max_stock, datetime.now(), datetime.now()))
                    
                    print(f"     ✓ Added product ID {product_id}: {current_stock} units")
        
        # 6. Create sample sales orders for hospitals
        print("6. Creating sample sales orders...")
        
        if hospital_ids and product_ids:
            for i, hospital_id in enumerate(hospital_ids):
                # Create a sample order for each hospital
                order_number = f"SO-2024-{i+1:03d}"
                order_date = datetime.now()
                
                cursor.execute("""
                    INSERT OR IGNORE INTO sales_orders 
                    (order_number, customer_id, order_date, status, total_amount, created_by)
                    VALUES (?, ?, ?, 'delivered', 0, ?)
                """, (order_number, hospital_id, order_date, 1))  # created_by = 1 (admin)
                
                order_id = cursor.lastrowid
                
                # Add order items
                for j, product_id in enumerate(product_ids[:3]):  # First 3 products
                    quantity = 20 + (j * 5)  # Varying quantities
                    unit_price = 25.00 + (j * 10.00)  # Varying prices
                    total_price = quantity * unit_price
                    
                    cursor.execute("""
                        INSERT OR IGNORE INTO sales_order_items 
                        (sales_order_id, product_id, quantity_ordered, quantity_shipped, unit_price, total_price)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (order_id, product_id, quantity, quantity, unit_price, total_price))
                
                print(f"   ✓ Created order {order_number} for hospital ID {hospital_id}")
        
        # Commit all changes
        conn.commit()
        print("\n" + "=" * 60)
        print("✅ Hospital System Data Seeding Completed Successfully!")
        print(f"   - Created {len(hospitals)} hospitals")
        print(f"   - Created {len(products)} products")
        print(f"   - Created inventory items")
        print(f"   - Assigned staff users to hospitals")
        print(f"   - Created sample hospital inventory")
        print(f"   - Created sample sales orders")
        
    except Exception as e:
        print(f"\n❌ Data seeding failed: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    seed_hospital_data()
