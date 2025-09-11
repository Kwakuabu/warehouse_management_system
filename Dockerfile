FROM python:3.11.13-slim

WORKDIR /app

COPY requirements.txt .

# Force install email validator first
RUN pip install --no-cache-dir email-validator==2.1.1 dnspython==2.4.2

# Then install everything else
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]