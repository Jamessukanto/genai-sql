#!/bin/bash

echo "Generating SSL certificates..."
mkdir -p /var/lib/postgresql/certs

# Generate self-signed certificate and private key
openssl req -x509 -newkey rsa:4096 -nodes \
    -keyout /var/lib/postgresql/certs/server.key \
    -out /var/lib/postgresql/certs/server.crt \
    -days 365 \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Set correct permissions for PostgreSQL
chown 999:999 /var/lib/postgresql/certs/server.key /var/lib/postgresql/certs/server.crt
chmod 600 /var/lib/postgresql/certs/server.key
chmod 644 /var/lib/postgresql/certs/server.crt

echo "SSL certificates generated successfully" 