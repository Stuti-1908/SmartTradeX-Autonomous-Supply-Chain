import time
import json
import logging
import os
import random
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel
import paho.mqtt.client as mqtt
from faker import Faker

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("IOT_SIM")

# Configuration
BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "mosquitto")
BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", 1883))
TOPIC = "shipment/telemetry"

# --- 1. Define the Data Schema (Restored) ---
class SensorReading(BaseModel):
    shipment_id: str
    timestamp: str
    location: dict  # {lat, lon}
    temperature_celsius: float
    humidity_percent: float
    shock_g: float
    battery_level: float

# --- 2. The Smart Container Class (Restored) ---
class SmartContainer:
    def __init__(self, shipment_id):
        self.shipment_id = shipment_id
        # Simulating a route from Mumbai to Dubai
        self.latitude = 19.0760 
        self.longitude = 72.8777
        self.battery = 100.0
        
    def generate_telemetry(self) -> SensorReading:
        # Simulate slight movement
        self.latitude += random.uniform(0.01, 0.05)
        self.longitude -= random.uniform(0.01, 0.05)
        
        # Simulate battery drain
        self.battery -= 0.05
        
        # Simulate Environment
        temp = random.uniform(-2, 5)
        if random.random() < 0.05: # 5% chance of anomaly
            temp = random.uniform(10, 15)

        return SensorReading(
            shipment_id=self.shipment_id,
            timestamp=datetime.utcnow().isoformat(),
            location={"lat": round(self.latitude, 4), "lon": round(self.longitude, 4)},
            temperature_celsius=round(temp, 2),
            humidity_percent=round(random.uniform(30, 60), 2),
            shock_g=round(random.uniform(0, 2), 2),
            battery_level=round(self.battery, 2)
        )

# --- 3. The Network Execution Loop ---
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info(f"Connected to MQTT Broker at {BROKER_HOST}:{BROKER_PORT}")
    else:
        logger.error(f"Failed to connect, return code {rc}")

if __name__ == "__main__":
    # --- MQTT Setup (Updated for v2 API to remove warnings) ---
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    
    # Retry logic
    while True:
        try:
            client.connect(BROKER_HOST, BROKER_PORT, 60)
            client.loop_start() 
            break
        except Exception as e:
            logger.warning(f"Waiting for Broker... ({e})")
            time.sleep(5)

    # --- Simulation Loop ---
    containers = [SmartContainer(f"SHP-{str(uuid4())[:8].upper()}") for _ in range(3)]
    
    logging.info(f"Initialized simulation for {len(containers)} containers.")
    
    try:
        while True:
            for container in containers:
                data = container.generate_telemetry()
                payload = json.dumps(data.dict())
                
                client.publish(TOPIC, payload)
                logger.info(f"Published: {data.shipment_id} | Temp: {data.temperature_celsius}C")
            
            time.sleep(2)
    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()
        logger.info("Simulation stopped.")