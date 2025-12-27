# Installation Guide

Complete step-by-step installation guide for Marstek Venus Bridge.

---

## Prerequisites

### 1. Hardware Requirements

- **Raspberry Pi 3/4/5** (or any Linux server)
- **Marstek Venus A** battery system
- **Network connection** (LAN or WiFi)
- **8GB+ SD card** for Raspberry Pi

### 2. Software Requirements

- **Operating System:** Raspberry Pi OS (or any Debian-based Linux)
- **Docker:** Version 20.10+
- **Docker Compose:** Version 1.29+
- **Git:** For cloning the repository

---

## Step 1: Install Docker on Raspberry Pi

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login again to apply group changes
# Or run: newgrp docker

# Verify Docker installation
docker --version
docker-compose --version
```

---

## Step 2: Find Venus A IP Address

### Option A: Check your router
1. Log into your router's admin interface
2. Look for "Connected Devices" or "DHCP Leases"
3. Find device named "MST_VNSA_xxxx"

### Option B: Network scan
```bash
# Install nmap
sudo apt install nmap -y

# Scan your network (adjust IP range)
sudo nmap -sn 192.168.1.0/24

# Look for Marstek device
```

### Option C: Assign static IP
- **Recommended:** Assign static IP to Venus A in router settings
- Prevents IP changes after router reboot
- Example: 192.168.1.100

---

## Step 2a: Enable Venus A Open API

**IMPORTANT:** The local UDP API must be enabled before the bridge can communicate with Venus A.

### Steps:
1. Open **Marstek App** on your smartphone
2. Select your **Venus A** device
3. Go to **Settings** (⚙️ icon)
4. Find **"Open API"** or **"Local API"** section
5. **Enable** the Open API toggle
6. Note the **UDP Port** (default: 30000)
7. Save settings

### Verify:
```bash
# Test UDP communication (from Raspberry Pi)
echo '{"id":1,"method":"Marstek.GetDevice","params":{"ble_mac":"0"}}' | nc -u -w2 192.168.1.100 30000
```

You should see a JSON response with device information.

---

## Step 3: Clone Repository

```bash
# Navigate to home directory
cd ~

# Clone repository
git clone https://github.com/IvanKablar/marstek-venus-bridge.git

# Enter directory
cd marstek-venus-bridge
```

---

## Step 4: Configure

```bash
# Copy example config
cp config.example.json config.json

# Edit configuration
nano config.json
```

**Update these values:**

```json
{
  "venus": {
    "ip": "192.168.1.100",         // ← Your Venus A IP address
    "mac": "aabbccddeeff",         // ← Your Venus A MAC (without colons/hyphens)
    "port": 30000,                 // ← UDP port (default: 30000)
    "poll_interval": 60,           // ← Poll every 60 seconds
    "timeout": 10                  // ← UDP timeout in seconds
  },
  "mqtt": {
    "broker": "mosquitto",         // ← MQTT broker container name
    "port": 1883,                  // ← MQTT broker port
    "topic_prefix": "marstek/venus",
    "qos": 1,
    "retain": true
  }
}
```

**How to find your MAC address:**
1. Open Marstek App
2. Select your Venus A device
3. Go to device information/settings
4. Find MAC address (e.g., `AA:BB:CC:DD:EE:FF`)
5. **Remove colons:** `aabbccddeeff` (lowercase)

**Save:** `Ctrl+O`, `Enter`, `Ctrl+X`

---

## Step 5: Test Venus A UDP Connection

Before starting the full stack, test if Venus A is reachable via UDP:

```bash
# Ping test (basic network connectivity)
ping -c 4 192.168.1.100  # Use your Venus IP

# UDP API test (requires netcat/nc)
echo '{"id":1,"method":"Bat.GetStatus","params":{"id":0}}' | nc -u -w2 192.168.1.100 30000

# Expected response (JSON with battery data):
# {"id":1,"src":"VenusA-xxx","result":{"soc":90,"bat_temp":4.0,...}}
```

**If you don't get a response:**
1. Verify Open API is enabled in Marstek App
2. Check Venus A IP address is correct
3. Confirm UDP port 30000 is configured
4. Ensure both devices are on same network

---

## Step 6: Start Services

```bash
# Build and start services
docker-compose up -d

# Check if services are running
docker-compose ps

# Expected output:
# NAME                   STATUS
# venus-mqtt-broker      Up
# venus-poller           Up
```

---

## Step 7: Monitor Logs

```bash
# Watch all logs
docker-compose logs -f

# Watch only poller logs
docker-compose logs -f venus-poller

# Watch only MQTT broker logs
docker-compose logs -f mosquitto
```

**Expected poller output:**
```
venus-poller | Starting Venus poller...
venus-poller | Venus IP: 192.168.1.100
venus-poller | Poll interval: 60s
venus-poller | Connected to MQTT broker
venus-poller | Published to marstek/venus/aabbccddeeff/data: {...}
```

---

## Step 8: Test MQTT Subscription

In a new terminal:

```bash
# Subscribe to all Venus topics
mosquitto_sub -h localhost -p 1883 -t "marstek/venus/#" -v

# You should see data every 60 seconds:
# marstek/venus/aabbccddeeff/data {"timestamp":"...","soc":85,...}
```

---

## Step 9: Configure MQTT Client

### Option A: Same WiFi Network

When client device is on same WiFi as Raspberry Pi:

```kotlin
// Example: Android/Kotlin MQTT client
val mqttBroker = "192.168.1.50:1883"  // Your Raspberry Pi IP
val mqttTopic = "marstek/venus/+/data"

connectToMQTT(mqttBroker, mqttTopic)
```

### Option B: Remote Access (Advanced)

**⚠️ Security Warning:** Only do this if you understand the risks!

```bash
# Port forwarding in router:
# External: 8883 → Internal: 192.168.1.50:1883

# Or use VPN (recommended):
# - WireGuard
# - OpenVPN
# - Tailscale
```

---

## Troubleshooting

### Services don't start

```bash
# Check Docker status
sudo systemctl status docker

# Rebuild services
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Can't reach Venus A

```bash
# Verify IP is correct
ping YOUR_VENUS_IP

# Check if Venus A has local API
# (Venus A may only support Cloud API!)
```

### No MQTT messages

```bash
# Check poller logs for errors
docker-compose logs venus-poller

# Verify MQTT broker is running
docker-compose ps mosquitto

# Test MQTT broker directly
mosquitto_sub -h localhost -p 1883 -t "#" -v
```

### Permission denied errors

```bash
# Fix folder permissions
sudo chown -R $USER:$USER mosquitto/

# Or create folders with correct permissions
mkdir -p mosquitto/data mosquitto/log
chmod 777 mosquitto/data mosquitto/log
```

---

## Auto-Start on Boot

```bash
# Enable Docker auto-start
sudo systemctl enable docker

# Services will auto-start if restart: unless-stopped
# is set in docker-compose.yml (already configured)

# Verify auto-start
sudo reboot
# Wait 2 minutes, then check:
docker-compose ps
```

---

## Updating

```bash
# Pull latest changes
cd ~/marstek-venus-bridge
git pull

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Uninstall

```bash
# Stop and remove services
docker-compose down -v

# Remove project
cd ~
rm -rf marstek-venus-bridge

# Optional: Remove Docker
sudo apt remove docker docker-compose
```

---

## Next Steps

- [ ] Configure client app to use MQTT
- [ ] Optional: Enable TLS for remote access (port 8883)
- [ ] Optional: Set up port forwarding in router
- [ ] Optional: Add monitoring dashboard

---

## Need Help?

Create an issue on GitHub: https://github.com/YOUR_USERNAME/marstek-venus-bridge/issues
