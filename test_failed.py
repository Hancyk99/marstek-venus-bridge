#!/usr/bin/env python3
"""
Retry failed API tests with longer delays
"""

import sys
import time
import json

# Add venus-poller to path
sys.path.insert(0, '/home/ivan/AndroidStudioProjects/marstek-venus-bridge/venus-poller')

from venus_api import VenusAPIClient

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

# Load configuration
config_path = '/home/ivan/AndroidStudioProjects/marstek-venus-bridge/config.json'
with open(config_path, 'r') as f:
    config = json.load(f)
    VENUS_IP = config['venus']['ip']
    VENUS_PORT = config['venus']['port']

print(f"\n{BLUE}{'='*60}{RESET}")
print(f"{BLUE}RETRY FAILED TESTS{RESET}")
print(f"{BLUE}Target: {VENUS_IP}:{VENUS_PORT}{RESET}")
print(f"{BLUE}{'='*60}{RESET}\n")

client = VenusAPIClient(ip=VENUS_IP, port=VENUS_PORT, timeout=10)

# Test 1: Bat.GetStatus with retries
print(f"{BLUE}Test 1: Bat.GetStatus (with 10s timeout and retries){RESET}")
print(f"{YELLOW}Attempt 1...{RESET}")

result = client.get_battery_status()
if not result:
    print(f"{YELLOW}Failed. Waiting 5s and retrying...{RESET}")
    time.sleep(5)

    print(f"{YELLOW}Attempt 2...{RESET}")
    result = client.get_battery_status()

if not result:
    print(f"{YELLOW}Failed. Waiting 10s and retrying...{RESET}")
    time.sleep(10)

    print(f"{YELLOW}Attempt 3...{RESET}")
    result = client.get_battery_status()

if result and 'soc' in result:
    print(f"{GREEN}✓ PASS{RESET} Bat.GetStatus")
    print(f"  SOC: {result.get('soc')}%")
    print(f"  Temp: {result.get('bat_temp')}°C")
    print(f"  Capacity: {result.get('bat_capacity')}Wh")
    print(f"  Rated: {result.get('rated_capacity')}Wh")
    print(f"\n  Full Response:")
    print(f"  {json.dumps(result, indent=2)}")
else:
    print(f"{RED}✗ FAIL{RESET} Bat.GetStatus - No valid response after 3 attempts")
    print(f"  Response: {result}")

# Wait before next test
print(f"\n{YELLOW}Waiting 10 seconds before next test...{RESET}\n")
time.sleep(10)

# Test 2: ES.GetMode after AI mode switch
print(f"{BLUE}Test 2: ES.GetMode (after AI Mode){RESET}")
print(f"{YELLOW}Step 1: Switch to AI mode...{RESET}")

ai_result = client.set_ai_mode()
if ai_result:
    print(f"{GREEN}✓{RESET} AI mode set successfully")
else:
    print(f"{RED}✗{RESET} Failed to set AI mode")

print(f"{YELLOW}Waiting 10 seconds for mode to activate...{RESET}")
time.sleep(10)

print(f"{YELLOW}Step 2: Query current mode...{RESET}")
mode_result = client.get_mode()

if not mode_result:
    print(f"{YELLOW}Failed. Waiting 5s and retrying...{RESET}")
    time.sleep(5)
    mode_result = client.get_mode()

if mode_result and 'mode' in mode_result:
    print(f"{GREEN}✓ PASS{RESET} ES.GetMode")
    print(f"  Mode: {mode_result.get('mode')}")
    print(f"  Grid Power: {mode_result.get('ongrid_power')}W")
    print(f"  SOC: {mode_result.get('bat_soc')}%")
    print(f"\n  Full Response:")
    print(f"  {json.dumps(mode_result, indent=2)}")
else:
    print(f"{RED}✗ FAIL{RESET} ES.GetMode - No valid response")
    print(f"  Response: {mode_result}")

# Restore to Manual mode
print(f"\n{YELLOW}Restoring to Manual mode...{RESET}")
time.sleep(5)
restore = client.set_manual_mode(power=0, start_time="00:00", end_time="23:59")
if restore:
    print(f"{GREEN}✓{RESET} Restored to Manual mode")
else:
    print(f"{RED}✗{RESET} Failed to restore Manual mode")

time.sleep(3)
final_mode = client.get_mode()
if final_mode:
    print(f"  Current mode: {final_mode.get('mode')}")

print(f"\n{BLUE}{'='*60}{RESET}")
print(f"{BLUE}RETRY TESTS COMPLETE{RESET}")
print(f"{BLUE}{'='*60}{RESET}\n")
