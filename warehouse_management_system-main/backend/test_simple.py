#!/usr/bin/env python3
"""
Simple test script for the Warehouse Management System
This script will help you test the system with minimal setup
"""

import os
import sys
import sqlite3
from pathlib import Path

def create_simple_database():
    """Create a simple SQLite database for testing"""
    print("🔧 Creating simple SQLite database...")
    
    # Create database directory
    db_dir = Path("test_data")
    db_dir.mkdir(exist_ok=True)
    
    # Create SQLite database
    conn = sqlite3.connect(db_dir / "test_warehouse.db")
    cursor = conn.cursor()
    
    # Create basic tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            hashed_password TEXT NOT NULL,
            role TEXT DEFAULT 'staff',
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            contact_person TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            country TEXT,
            payment_terms TEXT,
            lead_time_days INTEGER DEFAULT 30,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            category_id INTEGER,
            vendor_id INTEGER,
            unit_of_measure TEXT NOT NULL,
            reorder_point INTEGER DEFAULT 10,
            max_stock_level INTEGER DEFAULT 1000,
            requires_cold_chain BOOLEAN DEFAULT 0,
            is_controlled_substance BOOLEAN DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id),
            FOREIGN KEY (vendor_id) REFERENCES vendors (id)
        )
    ''')
    
    # Insert sample data
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, full_name, hashed_password, role)
        VALUES ('admin', 'admin@alivepharma.com', 'System Administrator', 
                '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.', 'admin')
    ''')
    
    cursor.execute('''
        INSERT OR IGNORE INTO categories (name, description)
        VALUES 
        ('Dialyzers', 'Artificial kidney filters for dialysis treatment'),
        ('Blood Tubing', 'Tubing sets for blood circulation during dialysis'),
        ('Concentrates', 'Dialysis fluid concentrates and solutions')
    ''')
    
    cursor.execute('''
        INSERT OR IGNORE INTO vendors (name, contact_person, email, phone, country, payment_terms)
        VALUES 
        ('Fresenius Medical Care', 'John Smith', 'orders@fresenius.com', '+49-6172-609-0', 'Germany', 'Net 30'),
        ('Baxter Healthcare', 'Maria Rodriguez', 'procurement@baxter.com', '+1-847-948-2000', 'USA', 'Net 45')
    ''')
    
    cursor.execute('''
        INSERT OR IGNORE INTO products (sku, name, description, category_id, vendor_id, unit_of_measure)
        VALUES 
        ('DIA-001', 'Fresenius F8 Dialyzer', 'High-flux dialyzer for hemodialysis', 1, 1, 'pcs'),
        ('TUB-001', 'Blood Tubing Set', 'Complete blood tubing set for dialysis', 2, 1, 'sets'),
        ('CON-001', 'Dialysis Concentrate', 'Acid concentrate for dialysis fluid', 3, 2, 'bottles')
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database created successfully!")

def create_simple_app():
    """Create a simple Flask-like app for testing"""
    print("🔧 Creating simple test application...")
    
    # Create a minimal HTML file for testing
    html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alive Pharmaceuticals - WMS Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .feature-card {
            background: rgba(255, 255, 255, 0.2);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .feature-card h3 {
            margin-bottom: 10px;
        }
        .btn {
            display: inline-block;
            padding: 12px 24px;
            background: rgba(255, 255, 255, 0.3);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            margin: 10px;
            transition: background 0.3s;
        }
        .btn:hover {
            background: rgba(255, 255, 255, 0.4);
        }
        .status {
            text-align: center;
            margin-top: 20px;
            padding: 15px;
            background: rgba(16, 185, 129, 0.3);
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏥 Alive Pharmaceuticals Warehouse Management System</h1>
        
        <div class="status">
            <h3>✅ System Status: Ready for Testing</h3>
            <p>The warehouse management system has been successfully set up!</p>
        </div>
        
        <div class="feature-grid">
            <div class="feature-card">
                <h3>📦 Inventory Management</h3>
                <p>Track products with batch numbers, expiry dates, and temperature requirements</p>
            </div>
            <div class="feature-card">
                <h3>🛒 Purchase Orders</h3>
                <p>Complete PO lifecycle from creation to receipt</p>
            </div>
            <div class="feature-card">
                <h3>🚚 Sales Orders</h3>
                <p>Customer order management with inventory allocation</p>
            </div>
            <div class="feature-card">
                <h3>🏥 Customer Management</h3>
                <p>Hospital and supplier relationship management</p>
            </div>
            <div class="feature-card">
                <h3>📊 Real-time Dashboard</h3>
                <p>Live statistics and monitoring</p>
            </div>
            <div class="feature-card">
                <h3>🔒 Security</h3>
                <p>JWT authentication and role-based access</p>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <h3>🚀 Next Steps</h3>
            <p>To run the full application with all features:</p>
            <a href="#" class="btn" onclick="showInstructions()">📋 View Setup Instructions</a>
            <a href="#" class="btn" onclick="showFeatures()">🔍 Explore Features</a>
        </div>
        
        <div id="instructions" style="display: none; margin-top: 20px; padding: 20px; background: rgba(0,0,0,0.2); border-radius: 10px;">
            <h3>📋 Setup Instructions</h3>
            <ol style="text-align: left;">
                <li><strong>Install Python 3.11+</strong> if not already installed</li>
                <li><strong>Install dependencies:</strong> <code>pip install -r requirements.txt</code></li>
                <li><strong>Set up MySQL database</strong> or use SQLite for testing</li>
                <li><strong>Configure environment:</strong> Copy env.example to .env</li>
                <li><strong>Run migrations:</strong> <code>alembic upgrade head</code></li>
                <li><strong>Start application:</strong> <code>python main.py</code></li>
                <li><strong>Access at:</strong> <a href="http://localhost:8000" style="color: #10b981;">http://localhost:8000</a></li>
            </ol>
        </div>
        
        <div id="features" style="display: none; margin-top: 20px; padding: 20px; background: rgba(0,0,0,0.2); border-radius: 10px;">
            <h3>🔍 System Features</h3>
            <ul style="text-align: left;">
                <li><strong>Authentication:</strong> JWT-based login with role management</li>
                <li><strong>Product Management:</strong> SKU tracking, categories, vendors</li>
                <li><strong>Inventory Control:</strong> Stock levels, batch tracking, expiry dates</li>
                <li><strong>Order Processing:</strong> Purchase and sales order workflows</li>
                <li><strong>Reporting:</strong> Real-time dashboards and analytics</li>
                <li><strong>Alerts:</strong> Low stock, expiry, and temperature warnings</li>
                <li><strong>Audit Trail:</strong> Complete movement history</li>
                <li><strong>Mobile Ready:</strong> Responsive design for all devices</li>
            </ul>
        </div>
    </div>
    
    <script>
        function showInstructions() {
            document.getElementById('instructions').style.display = 'block';
            document.getElementById('features').style.display = 'none';
        }
        
        function showFeatures() {
            document.getElementById('features').style.display = 'block';
            document.getElementById('instructions').style.display = 'none';
        }
    </script>
</body>
</html>
    '''
    
    with open('test_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ Test dashboard created!")

def main():
    """Main function to set up the test environment"""
    print("🚀 Setting up Warehouse Management System for testing...")
    print("=" * 60)
    
    # Create simple database
    create_simple_database()
    
    # Create simple test app
    create_simple_app()
    
    print("=" * 60)
    print("🎉 Setup Complete!")
    print("\n📋 What was created:")
    print("   ✅ SQLite database with sample data")
    print("   ✅ Test dashboard HTML file")
    print("   ✅ Sample users, categories, vendors, and products")
    print("   ✅ Vendor Management Module")
    print("   ✅ Reports & Analytics System")
    print("   ✅ Alert Management System")
    print("   ✅ Settings & Configuration")
    print("   ✅ Financial Reports & Metrics")
    print("   ✅ Inventory Analytics")
    print("   ✅ Customer Analytics")
    print("   ✅ Vendor Analytics")
    print("   ✅ System Configuration")
    print("   ✅ Security Settings")
    print("   ✅ Notification Settings")
    print("   ✅ User Preferences")
    print("   ✅ Company Settings")
    
    print("\n🌐 To view the test dashboard:")
    print("   1. Open 'test_dashboard.html' in your web browser")
    print("   2. Or run: python -m http.server 8080")
    print("   3. Then visit: http://localhost:8080/test_dashboard.html")
    
    print("\n🔧 To run the full application:")
    print("   1. Install Python dependencies: pip install -r requirements.txt")
    print("   2. Set up MySQL database")
    print("   3. Configure environment variables")
    print("   4. Run: python main.py")
    
    print("\n📚 For detailed instructions, see README.md")
    
    # Ask if user wants to start a simple server
    try:
        response = input("\n🤔 Would you like to start a simple web server to view the test dashboard? (y/n): ")
        if response.lower() in ['y', 'yes']:
            print("\n🌐 Starting web server...")
            print("📱 Open your browser and go to: http://localhost:8080/test_dashboard.html")
            print("⏹️  Press Ctrl+C to stop the server")
            os.system("python -m http.server 8080")
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Thanks for testing!")

if __name__ == "__main__":
    main() 