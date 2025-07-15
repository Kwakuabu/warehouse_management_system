#!/bin/bash

# Warehouse Management System Startup Script
echo "Starting Alive Pharmaceuticals Warehouse Management System..."

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if database is available (optional MySQL check)
echo "Checking system requirements..."

# Start the FastAPI application
echo "Starting FastAPI server..."
echo "Access the application at: http://127.0.0.1:8000"
echo "API Documentation available at: http://127.0.0.1:8000/docs"
echo "Press Ctrl+C to stop the server"

# Run the application
python main.py