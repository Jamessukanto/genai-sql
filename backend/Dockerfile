FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    openssl \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY tests/requirements-test.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-test.txt

COPY . .

# # Ensure init-certs.sh is runnable
# RUN mkdir -p /app/core \
#     && find /app/core -type f -name "*.sh" -exec chmod +x {} \; \
#     && ls -la /app/core/

# # Create certs directory
# RUN mkdir -p /var/lib/postgresql/certs && \
#     chown -R 999:999 /var/lib/postgresql/certs

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 
