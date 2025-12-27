#!/bin/bash
# Complete TLS setup for Mosquitto MQTT Broker

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "Marstek MQTT Broker - TLS Setup"
echo "=================================================="
echo ""

# 1. Generate certificates
echo "Step 1: Generating TLS certificates..."
bash generate-certs.sh
echo ""

# 2. Create password file
echo "Step 2: Creating password file..."
read -p "Enter MQTT username: " MQTT_USER
read -sp "Enter MQTT password: " MQTT_PASS
echo ""

# Create passwordfile in container format
# Note: This needs to run AFTER docker-compose up
echo "Password file will be created after starting containers."
echo "Run this command:"
echo "  docker exec -it marstek-mosquitto mosquitto_passwd -b /mosquitto/config/passwordfile $MQTT_USER $MQTT_PASS"
echo ""

# 3. Backup old config
if [ -f mosquitto.conf ]; then
    echo "Step 3: Backing up old configuration..."
    cp mosquitto.conf mosquitto.conf.backup
    echo "  Backup: mosquitto.conf.backup"
fi

# 4. Activate TLS config
echo "Step 4: Activating TLS configuration..."
cp mosquitto-tls.conf mosquitto.conf
chmod 644 mosquitto.conf
echo "  ✓ mosquitto.conf updated"
echo ""

# 5. Update docker-compose
echo "Step 5: Checking docker-compose.yml..."
if ! grep -q "8883:8883" ../../docker-compose.yml; then
    echo "  ⚠ Add TLS port mapping to docker-compose.yml:"
    echo "    ports:"
    echo "      - \"1883:1883\"   # Local (unencrypted)"
    echo "      - \"8883:8883\"   # TLS (encrypted)"
fi
echo ""

echo "=================================================="
echo "Setup complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Restart containers: docker-compose restart mosquitto"
echo "2. Create password:"
echo "   docker exec -it marstek-mosquitto mosquitto_passwd -b /mosquitto/config/passwordfile $MQTT_USER $MQTT_PASS"
echo "3. Test TLS connection:"
echo "   mosquitto_sub -h localhost -p 8883 --cafile certs/ca.crt -u $MQTT_USER -P [password] -t \"marstek/#\" -v"
echo ""
echo "Files created:"
echo "  - certs/ca.crt (install on clients)"
echo "  - certs/server.crt"
echo "  - certs/server.key"
echo "  - mosquitto.conf (TLS enabled)"
echo ""
echo "⚠ Security:"
echo "  - Port 1883: Only for Docker network (DO NOT expose)"
echo "  - Port 8883: Safe to expose via router port forwarding"
echo ""
