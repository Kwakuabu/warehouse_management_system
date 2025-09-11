#!/bin/bash

# Railway startup script for warehouse management system

echo "Starting warehouse management system..."

# Set default environment variables if not set
export DATABASE_URL=${DATABASE_URL:-"sqlite:///./warehouse_db.sqlite"}
export SECRET_KEY=${SECRET_KEY:-"railway-production-secret-key-change-this"}
export ENVIRONMENT=${ENVIRONMENT:-"production"}
export PORT=${PORT:-8000}

echo "Environment: $ENVIRONMENT"
echo "Database URL: $DATABASE_URL"
echo "Port: $PORT"

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port $PORT
