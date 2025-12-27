#!/usr/bin/env python3
"""
Venus A API Test Suite

Tests all available API endpoints and verifies responses.
"""

import sys
import time
import json
from typing import Dict, Optional

# Add venus-poller to path
sys.path.insert(0, '/home/ivan/AndroidStudioProjects/marstek-venus-bridge/venus-poller')

from venus_api import VenusAPIClient

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class APITester:
    """Test suite for Venus A API endpoints"""

    def __init__(self, ip: str, port: int = 30000):
        """Initialize tester with Venus A connection"""
        self.client = VenusAPIClient(ip=ip, port=port, timeout=5)
        self.original_mode = None
        self.test_results = []

    def log_test(self, name: str, passed: bool, expected: str, actual: str):
        """Log test result"""
        status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
        print(f"\n{status} {name}")
        print(f"  Expected: {expected}")
        print(f"  Actual:   {actual}")

        self.test_results.append({
            'test': name,
            'passed': passed,
            'expected': expected,
            'actual': actual
        })

    def test_battery_status(self):
        """Test Bat.GetStatus"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}Test 1: Bat.GetStatus (Battery Status){RESET}")
        print(f"{BLUE}{'='*60}{RESET}")

        result = self.client.get_battery_status()

        if result and 'soc' in result:
            expected = "Battery data with SOC, temp, capacity"
            actual = f"SOC: {result.get('soc')}%, Temp: {result.get('bat_temp')}°C, Cap: {result.get('bat_capacity')}Wh"
            self.log_test("Bat.GetStatus", True, expected, actual)
            print(f"\n  Full Response: {json.dumps(result, indent=2)}")
            return True
        else:
            self.log_test("Bat.GetStatus", False, "Valid battery data", str(result))
            return False

    def test_energy_status(self):
        """Test ES.GetStatus"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}Test 2: ES.GetStatus (Energy System Status){RESET}")
        print(f"{BLUE}{'='*60}{RESET}")

        result = self.client.get_energy_status()

        if result and 'bat_soc' in result:
            expected = "Energy data with power values"
            actual = f"Grid: {result.get('ongrid_power')}W, Battery: {result.get('bat_power')}W, SOC: {result.get('bat_soc')}%"
            self.log_test("ES.GetStatus", True, expected, actual)
            print(f"\n  Full Response: {json.dumps(result, indent=2)}")
            return True
        else:
            self.log_test("ES.GetStatus", False, "Valid energy data", str(result))
            return False

    def test_get_mode(self, expected_mode: Optional[str] = None):
        """Test ES.GetMode"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}Test: ES.GetMode (Query Current Mode){RESET}")
        print(f"{BLUE}{'='*60}{RESET}")

        result = self.client.get_mode()

        if result and 'mode' in result:
            mode = result.get('mode')

            if expected_mode:
                expected = f"Mode = {expected_mode}"
                actual = f"Mode = {mode}"
                passed = (mode == expected_mode)
                self.log_test("ES.GetMode", passed, expected, actual)
            else:
                expected = "Valid mode string"
                actual = f"Mode = {mode}"
                self.log_test("ES.GetMode", True, expected, actual)

            print(f"\n  Full Response: {json.dumps(result, indent=2)}")
            return mode
        else:
            self.log_test("ES.GetMode", False, "Valid mode data", str(result))
            return None

    def test_set_passive_mode(self):
        """Test ES.SetMode - Passive Mode"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}Test 3: ES.SetMode - Passive Mode{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")

        print(f"{YELLOW}Setting: power=50W for 60 seconds{RESET}")
        success = self.client.set_passive_mode(power=50, countdown=60)

        expected = "set_result: true"
        actual = f"set_result: {success}"
        self.log_test("ES.SetMode (Passive)", success, expected, actual)

        if success:
            time.sleep(2)  # Wait for mode change
            mode = self.test_get_mode(expected_mode="Passive")
            return mode == "Passive"

        return False

    def test_set_manual_mode(self):
        """Test ES.SetMode - Manual Mode"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}Test 4: ES.SetMode - Manual Mode{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")

        print(f"{YELLOW}Setting: power=100W, 00:00-23:59, all days{RESET}")
        success = self.client.set_manual_mode(
            power=100,
            start_time="00:00",
            end_time="23:59",
            week_set=127
        )

        expected = "set_result: true"
        actual = f"set_result: {success}"
        self.log_test("ES.SetMode (Manual)", success, expected, actual)

        if success:
            time.sleep(2)
            mode = self.test_get_mode(expected_mode="Manual")
            return mode == "Manual"

        return False

    def test_set_auto_mode(self):
        """Test ES.SetMode - Auto Mode"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}Test 5: ES.SetMode - Auto Mode{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")

        success = self.client.set_auto_mode()

        expected = "set_result: true"
        actual = f"set_result: {success}"
        self.log_test("ES.SetMode (Auto)", success, expected, actual)

        if success:
            time.sleep(2)
            mode = self.test_get_mode(expected_mode="Auto")
            return mode == "Auto"

        return False

    def test_set_ai_mode(self):
        """Test ES.SetMode - AI Mode"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}Test 6: ES.SetMode - AI Mode{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")

        success = self.client.set_ai_mode()

        expected = "set_result: true"
        actual = f"set_result: {success}"
        self.log_test("ES.SetMode (AI)", success, expected, actual)

        if success:
            time.sleep(2)
            mode = self.test_get_mode(expected_mode="AI")
            return mode == "AI"

        return False

    def restore_original_mode(self):
        """Restore original operating mode"""
        if not self.original_mode:
            print(f"\n{YELLOW}No original mode to restore{RESET}")
            return True

        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}Restoring Original Mode: {self.original_mode}{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")

        if self.original_mode == "Passive":
            success = self.client.set_passive_mode(power=0, countdown=300)
        elif self.original_mode == "Manual":
            success = self.client.set_manual_mode(power=0)
        elif self.original_mode == "Auto":
            success = self.client.set_auto_mode()
        elif self.original_mode == "AI":
            success = self.client.set_ai_mode()
        else:
            print(f"{YELLOW}Unknown mode: {self.original_mode}{RESET}")
            return False

        if success:
            print(f"{GREEN}✓ Restored to {self.original_mode} mode{RESET}")
        else:
            print(f"{RED}✗ Failed to restore mode{RESET}")

        return success

    def print_summary(self):
        """Print test summary"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}TEST SUMMARY{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed

        print(f"\nTotal Tests: {total}")
        print(f"{GREEN}Passed: {passed}{RESET}")
        print(f"{RED}Failed: {failed}{RESET}")
        print(f"Success Rate: {(passed/total*100):.1f}%")

        if failed > 0:
            print(f"\n{RED}Failed Tests:{RESET}")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test']}")

        print(f"\n{BLUE}{'='*60}{RESET}\n")

    def run_all_tests(self):
        """Run complete test suite"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}VENUS A API TEST SUITE{RESET}")
        print(f"{BLUE}IP: {self.client.ip}:{self.client.port}{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")

        # Save original mode
        print(f"\n{YELLOW}Step 0: Query original mode{RESET}")
        self.original_mode = self.test_get_mode()
        print(f"{YELLOW}Original Mode: {self.original_mode}{RESET}")

        # Read-only tests
        print(f"\n{YELLOW}=== READ-ONLY TESTS ==={RESET}")
        self.test_battery_status()
        time.sleep(1)
        self.test_energy_status()
        time.sleep(1)

        # Mode change tests
        print(f"\n{YELLOW}=== MODE CHANGE TESTS ==={RESET}")
        print(f"{YELLOW}Note: Each mode will be active for a few seconds{RESET}")

        self.test_set_passive_mode()
        time.sleep(2)

        self.test_set_manual_mode()
        time.sleep(2)

        self.test_set_auto_mode()
        time.sleep(2)

        self.test_set_ai_mode()
        time.sleep(2)

        # Restore
        self.restore_original_mode()

        # Summary
        self.print_summary()

        # Return success status
        return all(r['passed'] for r in self.test_results)


if __name__ == "__main__":
    # Load configuration
    import os
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            VENUS_IP = config['venus']['ip']
            VENUS_PORT = config['venus']['port']
    except Exception as e:
        print(f"{RED}Failed to load config.json: {e}{RESET}")
        print(f"{YELLOW}Using fallback values{RESET}")
        VENUS_IP = "192.168.1.100"
        VENUS_PORT = 30000

    print(f"\n{GREEN}Starting Venus A API Test Suite{RESET}")
    print(f"Target: {VENUS_IP}:{VENUS_PORT}\n")

    # Run tests
    tester = APITester(ip=VENUS_IP, port=VENUS_PORT)

    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Tests interrupted by user{RESET}")
        tester.restore_original_mode()
        sys.exit(130)
    except Exception as e:
        print(f"\n{RED}Test failed with error: {e}{RESET}")
        tester.restore_original_mode()
        sys.exit(1)
