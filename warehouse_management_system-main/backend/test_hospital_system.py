#!/usr/bin/env python3
"""
Test script to verify the hospital system is working correctly
"""

import sqlite3
import os

def test_hospital_system():
    """Test the hospital system functionality"""
    
    db_path = "warehouse_db.sqlite"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Testing Hospital System...")
        print("=" * 50)
        
        # 1. Check if hospital_id column exists in users table
        print("1. Checking users table structure...")
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'hospital_id' in columns:
            print("   ✓ hospital_id column exists in users table")
        else:
            print("   ✗ hospital_id column missing from users table")
            return
        
        # 2. Check if hospital_inventory table exists
        print("2. Checking hospital_inventory table...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hospital_inventory'")
        if cursor.fetchone():
            print("   ✓ hospital_inventory table exists")
        else:
            print("   ✗ hospital_inventory table missing")
            return
        
        # 3. Check users and their hospital assignments
        print("3. Checking user hospital assignments...")
        cursor.execute("""
            SELECT u.id, u.username, u.role, u.hospital_id, c.name as hospital_name
            FROM users u
            LEFT JOIN customers c ON u.hospital_id = c.id
            ORDER BY u.id
        """)
        users = cursor.fetchall()
        
        if not users:
            print("   ⚠ No users found in database")
        else:
            for user_id, username, role, hospital_id, hospital_name in users:
                status = "✓" if hospital_id else "✗"
                hospital_info = f"-> {hospital_name}" if hospital_name else "(no hospital)"
                print(f"   {status} User {username} ({role}) {hospital_info}")
        
        # 4. Check customers (hospitals)
        print("4. Checking customers (hospitals)...")
        cursor.execute("SELECT id, name, is_active FROM customers ORDER BY id")
        customers = cursor.fetchall()
        
        if not customers:
            print("   ⚠ No customers found in database")
        else:
            for customer_id, name, is_active in customers:
                status = "✓" if is_active else "⚠"
                print(f"   {status} Customer {customer_id}: {name} (active: {is_active})")
        
        # 5. Check products
        print("5. Checking products...")
        cursor.execute("SELECT id, name, is_active FROM products ORDER BY id")
        products = cursor.fetchall()
        
        if not products:
            print("   ⚠ No products found in database")
        else:
            for product_id, name, is_active in products:
                status = "✓" if is_active else "⚠"
                print(f"   {status} Product {product_id}: {name} (active: {is_active})")
        
        # 6. Check hospital inventory
        print("6. Checking hospital inventory...")
        cursor.execute("""
            SELECT hi.hospital_id, c.name as hospital_name, hi.product_id, p.name as product_name, 
                   hi.current_stock, hi.reorder_point
            FROM hospital_inventory hi
            JOIN customers c ON hi.hospital_id = c.id
            JOIN products p ON hi.product_id = p.id
            ORDER BY hi.hospital_id, hi.product_id
        """)
        inventory = cursor.fetchall()
        
        if not inventory:
            print("   ⚠ No hospital inventory found")
        else:
            for hospital_id, hospital_name, product_id, product_name, stock, reorder in inventory:
                print(f"   ✓ {hospital_name}: {product_name} - Stock: {stock}, Reorder: {reorder}")
        
        print("\n" + "=" * 50)
        print("Hospital System Test Complete!")
        
    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_hospital_system()
