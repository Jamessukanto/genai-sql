#!/bin/bash

echo "Generating SSL certificates..."
mkdir -p ./backend/core/certs

# Generate self-signed certificate and private key
openssl req -x509 -newkey rsa:4096 -nodes \
    -keyout ./backend/core/certs/server.key \
    -out ./backend/core/certs/server.crt \
    -days 7 \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"


echo "SSL certificates generated successfully" 
