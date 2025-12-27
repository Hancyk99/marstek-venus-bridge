#!/bin/bash
# Test MQTT TLS connection

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "MQTT TLS Connection Test"
echo "=================================================="
echo ""

# Check if certificates exist
if [ ! -f certs/ca.crt ]; then
    echo "❌ Error: Certificates not found!"
    echo "   Run: bash setup-tls.sh"
    exit 1
fi

# Get credentials
read -p "MQTT Username: " MQTT_USER
read -sp "MQTT Password: " MQTT_PASS
echo ""
echo ""

# Test 1: Local TLS connection (localhost)
echo "Test 1: Local TLS connection (localhost:8883)..."
timeout 5 mosquitto_sub -h localhost -p 8883 \
    --cafile certs/ca.crt \
    -u "$MQTT_USER" -P "$MQTT_PASS" \
    -t "marstek/#" -C 1 -v 2>/dev/null && echo "✓ SUCCESS" || echo "❌ FAILED"
echo ""

# Test 2: Unencrypted connection (should still work for local)
echo "Test 2: Unencrypted connection (localhost:1883)..."
timeout 5 mosquitto_sub -h localhost -p 1883 \
    -t "marstek/#" -C 1 -v 2>/dev/null && echo "✓ SUCCESS" || echo "❌ FAILED"
echo ""

# Test 3: Publish test message via TLS
echo "Test 3: Publish via TLS..."
mosquitto_pub -h localhost -p 8883 \
    --cafile certs/ca.crt \
    -u "$MQTT_USER" -P "$MQTT_PASS" \
    -t "marstek/test" \
    -m "TLS test message" && echo "✓ SUCCESS" || echo "❌ FAILED"
echo ""

echo "=================================================="
echo "Next: Test from external network"
echo "=================================================="
echo ""
echo "1. Find your public IP: curl ifconfig.me"
echo "2. Forward port 8883 in router to Raspberry Pi"
echo "3. Test from phone/laptop (not on home WiFi):"
echo ""
echo "   mosquitto_sub -h YOUR_PUBLIC_IP -p 8883 \\"
echo "     --cafile ca.crt \\"
echo "     -u $MQTT_USER -P [password] \\"
echo "     -t \"marstek/#\" -v"
echo ""
echo "⚠ Copy certs/ca.crt to your phone/laptop first!"
echo ""
