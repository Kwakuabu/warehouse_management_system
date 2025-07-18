# 🧪 Testing Guide - Warehouse Management System

## 🚀 Quick Start (No Dependencies Required)

### Option 1: View Demo Dashboard (Immediate)
1. **Open the demo file**: Navigate to `backend/quick_test.html`
2. **Double-click** the file to open it in your web browser
3. **Explore the features**: Click through the demo buttons to see system capabilities

### Option 2: Install Python and Test Full System

#### Step 1: Install Python
- Download Python 3.11+ from [python.org](https://python.org)
- During installation, check "Add Python to PATH"
- Verify installation: Open command prompt and type `python --version`

#### Step 2: Install Dependencies
```bash
cd warehouse_management_system-main/backend
pip install -r requirements.txt
```

#### Step 3: Set Up Database
**Option A: Use SQLite (Simplest)**
```bash
# The system will automatically create SQLite database
python main.py
```

**Option B: Use MySQL (Production)**
1. Install MySQL 8.0+
2. Create database: `CREATE DATABASE warehouse_db;`
3. Copy `env.example` to `.env` and update database URL

#### Step 4: Run the Application
```bash
python main.py
```

#### Step 5: Access the System
- Open browser and go to: http://localhost:8000
- Register a new user or use default credentials

### Option 3: Docker Setup (Recommended for Production)

#### Prerequisites
- Install [Docker Desktop](https://docker.com/products/docker-desktop)
- Install [Docker Compose](https://docs.docker.com/compose/install/)

#### Quick Start with Docker
```bash
cd warehouse_management_system-main/backend
docker-compose up -d
```

#### Access the System
- Open browser and go to: http://localhost:8000
- The system includes MySQL, Redis, and Nginx

## 📋 What You Can Test

### 🔐 Authentication System
- User registration with role-based permissions
- JWT token-based login
- Password hashing and validation
- Session management

### 📦 Product Management
- Add new products with SKU tracking
- Categorize products (Dialyzers, Blood Tubing, etc.)
- Set vendor relationships
- Configure pharmaceutical-specific fields

### 📊 Inventory Management
- Track stock levels with batch numbers
- Monitor expiry dates
- Set reorder points and alerts
- Temperature-sensitive product handling

### 🛒 Order Processing
- Create purchase orders from vendors
- Process sales orders to hospitals
- Track order status and delivery
- Inventory allocation and reservation

### 📈 Dashboard & Reporting
- Real-time statistics
- Low stock alerts
- Expiry warnings
- Inventory value calculations

### 🏥 Customer & Vendor Management
- Hospital customer profiles
- Supplier vendor management
- Contact information and payment terms
- Credit limit tracking

## 🎯 Demo Credentials

### Default Admin User
- **Username**: admin
- **Password**: admin123
- **Role**: Administrator

### Sample Data
The system comes with sample data including:
- 3 Product Categories (Dialyzers, Blood Tubing, Concentrates)
- 2 Vendors (Fresenius Medical Care, Baxter Healthcare)
- 3 Sample Products with full specifications

## 🔍 Testing Scenarios

### 1. User Management
```
1. Register a new user with different roles
2. Test login/logout functionality
3. Verify role-based access control
4. Test password validation
```

### 2. Product Lifecycle
```
1. Add a new product with all fields
2. Assign to category and vendor
3. Set reorder points and stock levels
4. Configure cold chain requirements
```

### 3. Inventory Operations
```
1. Receive stock with batch numbers
2. Check stock levels and alerts
3. Process stock movements
4. Monitor expiry dates
```

### 4. Order Processing
```
1. Create purchase order from vendor
2. Add multiple products to order
3. Track order status changes
4. Process order receipt
```

### 5. Sales Operations
```
1. Create sales order for hospital
2. Allocate inventory to order
3. Process order fulfillment
4. Track delivery status
```

## 🐛 Troubleshooting

### Common Issues

#### Python Not Found
```bash
# Check if Python is installed
python --version

# If not found, install from python.org
# Make sure to check "Add to PATH" during installation
```

#### Database Connection Error
```bash
# For SQLite (automatic)
# No setup required

# For MySQL
# 1. Install MySQL
# 2. Create database
# 3. Update .env file with correct credentials
```

#### Port Already in Use
```bash
# Change port in main.py
uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)

# Or kill existing process
# Windows: netstat -ano | findstr :8000
# Linux/Mac: lsof -i :8000
```

#### Dependencies Installation Issues
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v

# Install one by one if needed
pip install fastapi uvicorn sqlalchemy
```

## 📱 Mobile Testing

The system is fully responsive and works on:
- Desktop browsers (Chrome, Firefox, Safari, Edge)
- Mobile browsers (iOS Safari, Android Chrome)
- Tablet browsers

## 🔒 Security Testing

### Authentication
- Test invalid login attempts
- Verify JWT token expiration
- Check role-based access
- Test password strength requirements

### Data Validation
- Test form input validation
- Verify SQL injection protection
- Check XSS prevention
- Test file upload security

## 📊 Performance Testing

### Load Testing
```bash
# Install Apache Bench (ab)
# Test with multiple concurrent users
ab -n 1000 -c 10 http://localhost:8000/

# Or use Python for testing
pip install locust
locust -f test_performance.py
```

### Database Performance
- Monitor query execution times
- Check database connection pooling
- Test with large datasets
- Verify index usage

## 🎉 Success Criteria

Your testing is successful when you can:

✅ **Register and login** with different user roles  
✅ **Add products** with all required fields  
✅ **Create purchase orders** and track status  
✅ **Process sales orders** with inventory allocation  
✅ **View real-time dashboard** with statistics  
✅ **Receive alerts** for low stock and expiry  
✅ **Search and filter** inventory items  
✅ **Export data** in various formats  
✅ **Access system** from mobile devices  

## 📞 Support

If you encounter issues:

1. **Check the logs**: Look for error messages in the console
2. **Verify setup**: Ensure all prerequisites are installed
3. **Check documentation**: Review README.md for detailed instructions
4. **Test step by step**: Follow the testing scenarios above
5. **Use demo mode**: Start with the HTML demo file

## 🚀 Next Steps

After successful testing:

1. **Customize the system** for your specific needs
2. **Add more products** and categories
3. **Configure alerts** and notifications
4. **Set up backups** and monitoring
5. **Deploy to production** using Docker
6. **Train users** on system features

---

**Happy Testing! 🎯**

The warehouse management system is designed to be robust, user-friendly, and production-ready. Take your time exploring all the features and let us know if you need any assistance! 