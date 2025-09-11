FROM python:3.11.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Force install email validator first
RUN pip install --no-cache-dir email-validator==2.1.1 dnspython==2.4.2

# Then install everything else
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create necessary directories
RUN mkdir -p uploads logs

# Make startup script executable
RUN chmod +x start.sh

EXPOSE 8000

# Use the startup script
CMD ["./start.sh"]