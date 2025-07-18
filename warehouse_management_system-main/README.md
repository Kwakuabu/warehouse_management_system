# Alive Pharmaceuticals Warehouse Management System

A comprehensive warehouse management system specifically designed for pharmaceutical companies dealing with dialysis consumables and medical supplies. This system provides end-to-end inventory management, order processing, and regulatory compliance features essential for pharmaceutical operations.

## 🏥 Features

### Core Functionality
- **Inventory Management**: Track products with batch numbers, expiry dates, and temperature requirements
- **Purchase Order Management**: Complete PO lifecycle from creation to receipt
- **Sales Order Processing**: Customer order management with inventory allocation
- **Customer & Vendor Management**: Hospital and supplier relationship management
- **Stock Movement Tracking**: Complete audit trail of all inventory movements
- **Alert System**: Low stock, expiry, and temperature alerts

### Pharmaceutical-Specific Features
- **Cold Chain Management**: Temperature-sensitive product handling
- **Expiry Date Tracking**: Critical for pharmaceutical compliance
- **Batch Traceability**: Essential for pharmaceutical regulations
- **Controlled Substances**: Special handling for regulated items
- **Temperature Monitoring**: Storage condition tracking

### User Management
- **Role-Based Access**: Admin, Manager, and Staff roles
- **JWT Authentication**: Secure token-based authentication
- **User Activity Tracking**: Audit logs for compliance

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- MySQL 8.0+
- Redis (for caching and background tasks)
- Docker & Docker Compose (for production deployment)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd warehouse_management_system-main/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your database credentials
   ```

5. **Set up database**
   ```bash
   # Create MySQL database
   mysql -u root -p
   CREATE DATABASE warehouse_db;
   CREATE USER 'wms_user'@'localhost' IDENTIFIED BY 'wms_password';
   GRANT ALL PRIVILEGES ON warehouse_db.* TO 'wms_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

6. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

7. **Start the application**
   ```bash
   python main.py
   ```

8. **Access the application**
   - Open http://localhost:8000
   - Register a new user or use default credentials

### Production Deployment with Docker

1. **Clone and navigate to backend**
   ```bash
   cd warehouse_management_system-main/backend
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with production values
   ```

3. **Start the full stack**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Open http://localhost (via Nginx)
   - Or http://localhost:8000 (direct access)

## 📁 Project Structure

```
warehouse_management_system-main/
├── backend/
│   ├── app/
│   │   ├── models/           # Database models
│   │   ├── routes/           # API routes and views
│   │   ├── templates/        # HTML templates
│   │   ├── static/           # CSS, JS, images
│   │   ├── utils/            # Utility functions
│   │   └── __init__.py
│   ├── alembic/              # Database migrations
│   ├── logs/                 # Application logs
│   ├── uploads/              # File uploads
│   ├── main.py              # Application entry point
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile           # Docker configuration
│   ├── docker-compose.yml   # Docker Compose setup
│   └── alembic.ini         # Alembic configuration
└── README.md
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```env
# Database
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/warehouse_db

# Security
SECRET_KEY=your-super-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis
REDIS_URL=redis://localhost:6379/0

# Application
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO
```

### Database Configuration

The system uses MySQL with the following key tables:
- `users` - User accounts and authentication
- `products` - Product catalog with pharmaceutical details
- `inventory_items` - Stock levels with batch tracking
- `purchase_orders` - Supplier orders
- `sales_orders` - Customer orders
- `stock_movements` - Inventory movement audit trail
- `alerts` - System alerts and notifications

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx factory-boy

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

### Test Structure
```
tests/
├── test_auth.py          # Authentication tests
├── test_models.py        # Database model tests
├── test_routes.py        # API endpoint tests
└── conftest.py          # Test configuration
```

## 📊 API Documentation

### Authentication Endpoints
- `POST /auth/token` - Get JWT token
- `POST /auth/register` - Register new user
- `GET /auth/me` - Get current user info

### Product Management
- `GET /products` - List all products
- `POST /products/add` - Add new product
- `GET /products/{id}` - Get product details

### Inventory Management
- `GET /inventory` - Inventory overview
- `POST /inventory/receive` - Receive stock
- `GET /inventory/movements` - Stock movement history

### Order Management
- `GET /purchase-orders` - List purchase orders
- `POST /purchase-orders/create` - Create purchase order
- `GET /sales-orders` - List sales orders
- `POST /sales-orders/create` - Create sales order

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: bcrypt for password security
- **Role-Based Access**: Granular permissions
- **Input Validation**: Comprehensive form validation
- **SQL Injection Protection**: SQLAlchemy ORM
- **XSS Protection**: Template escaping
- **CSRF Protection**: Built-in CSRF tokens

## 📈 Monitoring & Logging

### Logging Configuration
The system uses structured logging with different levels:
- **INFO**: General application events
- **WARNING**: Potential issues
- **ERROR**: Application errors
- **DEBUG**: Detailed debugging information

### Health Checks
- Application health: `GET /health`
- Database connectivity
- Redis connectivity
- Background task status

## 🚀 Deployment

### Production Checklist
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure secure `SECRET_KEY`
- [ ] Set up SSL certificates
- [ ] Configure database backups
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation
- [ ] Set up CI/CD pipeline

### Docker Deployment
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale services
docker-compose up -d --scale celery_worker=3
```

### Manual Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start with Gunicorn
gunicorn main:app --bind 0.0.0.0:8000 --workers 4
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Use Black for code formatting
- Use Flake8 for linting
- Add type hints where appropriate

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## 🔄 Updates & Maintenance

### Regular Maintenance Tasks
- Database backups
- Log rotation
- Security updates
- Performance monitoring
- Alert system testing

### Version Updates
- Check for dependency updates
- Test in staging environment
- Update documentation
- Deploy during maintenance window

---

**Alive Pharmaceuticals Warehouse Management System** - Streamlining pharmaceutical inventory management with compliance and efficiency. 