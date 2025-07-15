#!/bin/bash

# Warehouse Management System Setup Script
echo "Setting up Alive Pharmaceuticals Warehouse Management System..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Database Configuration
DATABASE_URL=mysql+pymysql://root:@localhost:3306/warehouse_db

# Security
SECRET_KEY=your-secret-key-here-change-this-in-production

# Application Settings
DEBUG=True
EOF
    echo ".env file created. Please update the database credentials and secret key."
fi

# Create static directories if they don't exist
echo "Creating static directories..."
mkdir -p app/static/css app/static/js app/static/images

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Create MySQL database: CREATE DATABASE warehouse_db;"
echo "2. Update .env file with your database credentials"
echo "3. Run: ./start.sh to start the application"
echo ""
echo "The application will be available at: http://127.0.0.1:8000"