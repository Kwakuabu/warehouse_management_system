#!/usr/bin/env python3
"""
Check if staff users have hospitals assigned
"""

import pymysql

def check_hospital_assignment():
    try:
        # Connect to MySQL database
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='warehouse_db'
        )
        cursor = conn.cursor()
        
        print("Checking staff user hospital assignments...")
        print("=" * 50)
        
        # Check staff users and their hospital assignments
        cursor.execute("""
            SELECT u.username, u.full_name, u.role, u.hospital_id, c.name as hospital_name 
            FROM users u 
            LEFT JOIN customers c ON u.hospital_id = c.id 
            WHERE u.role = 'staff'
        """)
        
        staff_users = cursor.fetchall()
        
        if not staff_users:
            print("No staff users found!")
        else:
            for username, full_name, role, hospital_id, hospital_name in staff_users:
                status = "✓" if hospital_id else "✗"
                hospital_info = f"-> {hospital_name}" if hospital_name else "(no hospital)"
                print(f"{status} User: {username}")
                print(f"   Full Name: {full_name}")
                print(f"   Role: {role}")
                print(f"   Hospital ID: {hospital_id}")
                print(f"   Hospital: {hospital_info}")
                print()
        
        # Also check all users to see the full picture
        print("All users:")
        print("=" * 50)
        cursor.execute("""
            SELECT u.username, u.role, u.hospital_id, c.name as hospital_name 
            FROM users u 
            LEFT JOIN customers c ON u.hospital_id = c.id
        """)
        
        all_users = cursor.fetchall()
        for username, role, hospital_id, hospital_name in all_users:
            status = "✓" if hospital_id else "✗"
            hospital_info = f"-> {hospital_name}" if hospital_name else "(no hospital)"
            print(f"{status} {username} ({role}) {hospital_info}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_hospital_assignment()
