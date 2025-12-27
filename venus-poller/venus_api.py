"""
Venus A UDP API Client

Handles communication with the local Venus A device via UDP JSON-RPC protocol.
Based on Marstek Device Open API (Rev 1.0)
"""

import socket
import json
import logging
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class VenusAPIClient:
    """Client for communicating with Venus A via UDP JSON-RPC"""

    def __init__(self, ip: str, port: int = 30000, timeout: int = 10):
        """
        Initialize Venus API client

        Args:
            ip: Venus A IP address
            port: UDP port (default: 30000)
            timeout: Request timeout in seconds
        """
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.request_id = 0

    def _send_request(self, method: str, params: Dict = None, max_retries: int = 2, retry_delay: float = 3.0) -> Optional[Dict]:
        """
        Send UDP JSON-RPC request to Venus A with retry logic

        Args:
            method: API method name (e.g., "Bat.GetStatus")
            params: Method parameters (default: {"id": 0})
            max_retries: Maximum number of retry attempts (default: 2)
            retry_delay: Delay in seconds between retries (default: 3.0)

        Returns:
            Response dictionary or None on error
        """
        if params is None:
            params = {"id": 0}

        last_error = None

        for attempt in range(max_retries + 1):
            # Wait before retry (but not on first attempt)
            if attempt > 0:
                logger.info(f"Retry {attempt}/{max_retries} for {method} after {retry_delay}s")
                time.sleep(retry_delay)

            self.request_id += 1
            request = {
                "id": self.request_id,
                "method": method,
                "params": params
            }

            sock = None
            try:
                # Create UDP socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(self.timeout)

                # Send request
                message = json.dumps(request).encode('utf-8')
                sock.sendto(message, (self.ip, self.port))
                logger.debug(f"Sent to {self.ip}:{self.port}: {request}")

                # Receive response
                data, addr = sock.recvfrom(4096)
                response = json.loads(data.decode('utf-8'))
                logger.debug(f"Received from {addr}: {response}")

                # Check for errors
                if "error" in response:
                    error = response['error']
                    logger.error(f"API error: {error}")
                    # Don't retry on permanent errors (method not found, invalid params, feature not supported)
                    return None

                # Success
                if attempt > 0:
                    logger.info(f"Request succeeded on attempt {attempt + 1}")
                return response.get("result")

            except socket.timeout:
                last_error = f"Timeout waiting for response from {self.ip}:{self.port}"
                logger.warning(last_error)
                # Continue to retry
                continue

            except Exception as e:
                last_error = f"Error communicating with Venus A: {e}"
                logger.warning(last_error)
                # Continue to retry
                continue

            finally:
                if sock:
                    try:
                        sock.close()
                    except:
                        pass

        # All retries exhausted
        logger.error(f"Request failed after {max_retries + 1} attempts: {last_error}")
        return None

    def get_battery_status(self) -> Optional[Dict]:
        """
        Get battery status (Bat.GetStatus)

        Returns:
            {
                "soc": 98,
                "charg_flag": true,
                "dischrg_flag": true,
                "bat_temp": 25.0,
                "bat_capacity": 2508.0,
                "rated_capacity": 2560.0
            }
        """
        return self._send_request("Bat.GetStatus")

    def get_energy_status(self) -> Optional[Dict]:
        """
        Get energy system status (ES.GetStatus)

        Returns:
            {
                "bat_soc": 98,
                "bat_cap": 2560,
                "pv_power": 0,
                "ongrid_power": 100,
                "offgrid_power": 0,
                "bat_power": 0,
                "total_pv_energy": 0,
                "total_grid_output_energy": 844,
                "total_grid_input_energy": 1607,
                "total_load_energy": 0
            }
        """
        return self._send_request("ES.GetStatus")

    def get_data(self) -> Optional[Dict]:
        """
        Fetch comprehensive data from Venus A

        Combines battery and energy system data into single dictionary.

        Returns:
            Dictionary with Venus data or None on error
        """
        bat_data = self.get_battery_status()
        es_data = self.get_energy_status()

        if not bat_data and not es_data:
            logger.error("Failed to fetch any data from Venus A")
            return None

        # Combine data
        result = {}

        if bat_data:
            result.update({
                "soc": bat_data.get("soc"),
                "battery_temp": bat_data.get("bat_temp"),
                "battery_capacity": bat_data.get("bat_capacity"),
                "rated_capacity": bat_data.get("rated_capacity"),
                "charging_allowed": bat_data.get("charg_flag"),
                "discharging_allowed": bat_data.get("dischrg_flag")
            })

        if es_data:
            result.update({
                "pv_power": es_data.get("pv_power"),
                "grid_power": es_data.get("ongrid_power"),
                "offgrid_power": es_data.get("offgrid_power"),
                "battery_power": es_data.get("bat_power"),
                "total_pv_energy": es_data.get("total_pv_energy"),
                "total_grid_output": es_data.get("total_grid_output_energy"),
                "total_grid_input": es_data.get("total_grid_input_energy"),
                "total_load_energy": es_data.get("total_load_energy")
            })

        return result

    def set_manual_mode(self, power: int, start_time: str = "00:00",
                        end_time: str = "23:59", week_set: int = 127,
                        enable: int = 1) -> bool:
        """
        Set manual mode with power and schedule

        Args:
            power: Power in Watts (positive = charge, negative = discharge)
            start_time: Start time "HH:MM" (default: "00:00")
            end_time: End time "HH:MM" (default: "23:59")
            week_set: Week bitmask (127 = all days, default)
            enable: 1 = ON, 0 = OFF

        Returns:
            True if successful, False otherwise
        """
        params = {
            "id": 0,
            "config": {
                "mode": "Manual",
                "manual_cfg": {
                    "time_num": 0,
                    "start_time": start_time,
                    "end_time": end_time,
                    "week_set": week_set,
                    "power": power,
                    "enable": enable
                }
            }
        }

        result = self._send_request("ES.SetMode", params)
        if result and result.get("set_result"):
            logger.info(f"Manual mode set: power={power}W, {start_time}-{end_time}")
            return True
        return False

    def set_passive_mode(self, power: int, countdown: int = 300) -> bool:
        """
        Set passive mode for immediate power control

        Args:
            power: Power in Watts (positive = charge, negative = discharge)
            countdown: Duration in seconds (default: 300s = 5min)

        Returns:
            True if successful, False otherwise
        """
        params = {
            "id": 0,
            "config": {
                "mode": "Passive",
                "passive_cfg": {
                    "power": power,
                    "cd_time": countdown
                }
            }
        }

        result = self._send_request("ES.SetMode", params)
        if result and result.get("set_result"):
            logger.info(f"Passive mode set: power={power}W for {countdown}s")
            return True
        return False

    def set_auto_mode(self) -> bool:
        """
        Enable auto mode

        Returns:
            True if successful, False otherwise
        """
        params = {
            "id": 0,
            "config": {
                "mode": "Auto",
                "auto_cfg": {
                    "enable": 1
                }
            }
        }

        result = self._send_request("ES.SetMode", params)
        if result and result.get("set_result"):
            logger.info("Auto mode enabled")
            return True
        return False

    def set_ai_mode(self) -> bool:
        """
        Enable AI mode

        Returns:
            True if successful, False otherwise
        """
        params = {
            "id": 0,
            "config": {
                "mode": "AI",
                "ai_cfg": {
                    "enable": 1
                }
            }
        }

        result = self._send_request("ES.SetMode", params)
        if result and result.get("set_result"):
            logger.info("AI mode enabled")
            return True
        return False

    def get_mode(self) -> Optional[Dict]:
        """
        Get current operating mode

        Returns:
            {
                "mode": "Passive",
                "ongrid_power": 100,
                "offgrid_power": 0,
                "bat_soc": 98
            }
        """
        return self._send_request("ES.GetMode")
