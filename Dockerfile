FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements_simple.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
# Ensure email-validator is installed explicitly
RUN pip install --no-cache-dir email-validator==2.1.0

# Copy application
COPY warehouse_management_system-main/backend/ /app/

# Expose port
EXPOSE 8000

# Run app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
