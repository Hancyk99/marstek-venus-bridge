"""
Venus MQTT Poller

Polls Venus A device and publishes data to MQTT broker.
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict

import paho.mqtt.client as mqtt

from venus_api import VenusAPIClient

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VenusPoller:
    """Main poller class that coordinates Venus API and MQTT publishing"""

    def __init__(self, config_path: str = "/app/config.json"):
        """Initialize poller with configuration"""
        self.config = self._load_config(config_path)
        self.venus_client = VenusAPIClient(
            ip=self.config["venus"]["ip"],
            port=self.config["venus"].get("port", 30000),
            timeout=self.config["venus"]["timeout"]
        )
        self.mqtt_client = self._setup_mqtt()
        self.running = False

    def _load_config(self, path: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {path}")
            logger.info("Using default configuration")
            return self._default_config()

    def _default_config(self) -> Dict:
        """Return default configuration"""
        return {
            "venus": {
                "ip": "192.168.1.100",
                "mac": "aabbccddeeff",
                "poll_interval": 60,
                "timeout": 10
            },
            "mqtt": {
                "broker": os.getenv("MQTT_BROKER", "localhost"),
                "port": int(os.getenv("MQTT_PORT", 1883)),
                "topic_prefix": "marstek/venus",
                "qos": 1,
                "retain": True
            }
        }

    def _setup_mqtt(self) -> mqtt.Client:
        """Setup MQTT client"""
        client = mqtt.Client()

        client.on_connect = self._on_mqtt_connect
        client.on_disconnect = self._on_mqtt_disconnect

        broker = self.config["mqtt"]["broker"]
        port = self.config["mqtt"]["port"]

        try:
            logger.info(f"Connecting to MQTT broker at {broker}:{port}")
            client.connect(broker, port, 60)
            client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise

        return client

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            logger.info("Connected to MQTT broker")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code {rc}")

    def _on_mqtt_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection. Return code: {rc}")
            logger.info("Attempting to reconnect...")

    def _publish_data(self, data: Dict):
        """Publish Venus data to MQTT"""
        if not data:
            logger.warning("No data to publish")
            return

        # Add timestamp
        data["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Publish to data topic
        mac = self.config["venus"]["mac"]
        topic_prefix = self.config["mqtt"]["topic_prefix"]
        topic = f"{topic_prefix}/{mac}/data"

        try:
            payload = json.dumps(data)
            result = self.mqtt_client.publish(
                topic,
                payload,
                qos=self.config["mqtt"]["qos"],
                retain=self.config["mqtt"]["retain"]
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published to {topic}: {payload}")
            else:
                logger.error(f"Failed to publish to {topic}, error code: {result.rc}")

        except Exception as e:
            logger.error(f"Error publishing data: {e}")

    def run(self):
        """Main polling loop"""
        logger.info("Starting Venus poller...")
        logger.info(f"Venus IP: {self.config['venus']['ip']}")
        logger.info(f"Poll interval: {self.config['venus']['poll_interval']}s")

        self.running = True

        try:
            while self.running:
                try:
                    # Fetch data from Venus
                    data = self.venus_client.get_data()

                    if data:
                        # Publish to MQTT
                        self._publish_data(data)
                    else:
                        logger.warning("Failed to fetch Venus data")

                except Exception as e:
                    logger.error(f"Error in poll cycle: {e}")

                # Wait for next poll interval
                time.sleep(self.config["venus"]["poll_interval"])

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        finally:
            self.stop()

    def stop(self):
        """Stop the poller"""
        logger.info("Stopping Venus poller...")
        self.running = False
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        logger.info("Venus poller stopped")


if __name__ == "__main__":
    poller = VenusPoller()
    poller.run()
