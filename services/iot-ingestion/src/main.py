import os
import json
import logging
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("INGESTION")

# Config
MQTT_BROKER = os.getenv("MQTT_BROKER_HOST", "mosquitto")
INFLUX_URL = os.getenv("INFLUX_URL", "http://influxdb:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "my-super-secret-auth-token")
INFLUX_ORG = os.getenv("INFLUX_ORG", "smarttrade")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "logistics")

db_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = db_client.write_api(write_options=SYNCHRONOUS)

def save_telemetry(data):
    try:
        point = Point("telemetry") \
            .tag("shipment_id", data.get("shipment_id", "UNKNOWN")) \
            .field("temperature", float(data.get("temperature_celsius", 0))) \
            .field("humidity", float(data.get("humidity_percent", 0))) \
            .field("battery", float(data.get("battery_level", 0))) \
            .field("shock", float(data.get("shock_g", 0)))
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        logger.info(f"Saved Telemetry: {data.get('shipment_id')}")
    except Exception as e:
        logger.error(f"Telemetry Write Failed: {e}")

def save_alert(data):
    try:
        # FIXED: We default the type to 'ai_anomaly' if missing
        point = Point("alerts") \
            .tag("shipment_id", data.get("shipment_id", "UNKNOWN")) \
            .tag("type", data.get("alert_type", "ai_anomaly")) \
            .field("anomaly_score", float(data.get("anomaly_score", 0.0))) \
            .field("message", data.get("message", "No message"))
            
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        logger.warning(f"⚠️ Saved ALERT: {data.get('shipment_id')} (Score: {data.get('anomaly_score')})")
    except Exception as e:
        logger.error(f"Alert Write Failed: {e}")

def save_decision(data):
    try:
        # UNIVERSAL TRANSLATOR:
        # Phase 3 sends 'status', Phase 5 sends 'decision'. We grab whichever exists.
        final_status = data.get("status") or data.get("decision") or "UNKNOWN"
        
        # Phase 3 sends 'legal_ruling', Phase 5 sends 'reason'.
        final_details = data.get("legal_ruling") or data.get("reason") or "No details"

        point = Point("decisions") \
            .tag("shipment_id", data.get("shipment_id", "UNKNOWN")) \
            .field("status", final_status) \
            .field("details", final_details) # Save as Field for easy visualization
            
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        logger.info(f"👨‍⚖️ Saved Decision: {final_status}")
    except Exception as e:
        logger.error(f"Decision Write Failed: {e}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        topic = msg.topic

        if "telemetry" in topic:
            save_telemetry(payload)
        elif "alerts" in topic:
            save_alert(payload)
        # FIXED: Check for "decision" (singular) to catch both 'decisions' and 'final_decision'
        elif "decision" in topic: 
            save_decision(payload)
            
    except Exception as e:
        logger.error(f"Processing Failed: {e}")

def on_connect(client, userdata, flags, rc, properties=None):
    logger.info("Connected. Subscribing to ALL shipment topics...")
    client.subscribe("shipment/#")

if __name__ == "__main__":
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.connect(MQTT_BROKER, 1883, 60)
    client.loop_forever()