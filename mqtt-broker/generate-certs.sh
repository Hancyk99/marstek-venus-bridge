#!/bin/bash
# Generate self-signed TLS certificates for Mosquitto MQTT Broker
# For production: Use Let's Encrypt or proper CA certificates

set -e

CERT_DIR="/home/ivan/AndroidStudioProjects/marstek-venus-bridge/mqtt-broker/certs"
mkdir -p "$CERT_DIR"
cd "$CERT_DIR"

echo "Generating TLS certificates for MQTT..."

# 1. Generate CA (Certificate Authority)
openssl genrsa -out ca.key 2048
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt \
  -subj "/C=DE/ST=State/L=City/O=Marstek/CN=Marstek MQTT CA"

# 2. Generate Server Key and Certificate
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr \
  -subj "/C=DE/ST=State/L=City/O=Marstek/CN=mqtt.local"

# Sign server certificate with CA
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out server.crt -days 3650

# 3. Generate Client Key and Certificate (optional - for mutual TLS)
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr \
  -subj "/C=DE/ST=State/L=City/O=Marstek/CN=marstek-client"

# Sign client certificate with CA
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out client.crt -days 3650

# Set permissions
chmod 644 *.crt
chmod 600 *.key

echo "✓ Certificates generated in $CERT_DIR"
echo ""
echo "Files created:"
echo "  ca.crt       - CA certificate (install on clients)"
echo "  server.crt   - Server certificate"
echo "  server.key   - Server private key"
echo "  client.crt   - Client certificate (optional)"
echo "  client.key   - Client private key (optional)"
