#!/bin/bash

# Directory for development certificates (relative to script location)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERT_DIR="$SCRIPT_DIR"

# Generate certificates if they don't exist
if [ ! -f "$CERT_DIR/server.crt" ]; then
    echo "Generating development SSL certificates..."
    
    # Generate self-signed certificate and private key
    openssl req -x509 -newkey rsa:4096 -nodes \
        -keyout "$CERT_DIR/server.key" \
        -out "$CERT_DIR/server.crt" \
        -days 365 \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

    # Set correct permissions
    chmod 600 "$CERT_DIR/server.key"
    chmod 644 "$CERT_DIR/server.crt"
    
    echo "Development SSL certificates generated in $CERT_DIR/"
else
    echo "SSL certificates already exist in $CERT_DIR/"
fi 