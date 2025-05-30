FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    openssl \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Leverage Docker cache
COPY requirements.txt .
COPY tests/requirements-test.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-test.txt

# Copy api folder
COPY . .

# Ensure scripts directory exists and has correct permissions
RUN mkdir -p /app/scripts \
    && find /app/scripts -type f -name "*.sh" -exec chmod +x {} \; \
    && ls -la /app/scripts/

# Create certs directory with correct permissions
RUN mkdir -p /var/lib/postgresql/certs && \
    chown -R 999:999 /var/lib/postgresql/certs

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 
