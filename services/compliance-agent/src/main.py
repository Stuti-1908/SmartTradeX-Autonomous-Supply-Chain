import os
import json
import time
import logging
import paho.mqtt.client as mqtt

# --- Configuration ---
BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "mosquitto")
INPUT_TOPIC = "shipment/alerts"
OUTPUT_TOPIC = "shipment/decisions"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("COMPLIANCE_MOCK")

# --- The "Mock" Brain ---
def analyze_contract(alert_data):
    """
    Simulates an LLM reading a contract.
    We manually code the rules from 'shipping_contract.txt' here.
    """
    shipment_id = alert_data.get("shipment_id", "UNKNOWN")
    triggers = alert_data.get("trigger_values", [0, 0, 0]) # [Temp, Humidity, Shock]
    temp = triggers[0]
    
    # Simulate "Thinking" time (Latency)
    time.sleep(1.5)
    
    logger.info(f"📄 Reading Contract for {shipment_id}...")

    # Rule Matching (Section 4.1 from our text file)
    if temp > 10.0:
        return {
            "status": "VIOLATION",
            "legal_ruling": f"VIOLATION: Temperature {temp}°C exceeds Contract Limit (8°C) as per Section 4.1. RECOMMENDATION: Reject Shipment."
        }
    elif temp < 2.0:
        return {
            "status": "VIOLATION",
            "legal_ruling": f"VIOLATION: Temperature {temp}°C is below Contract Minimum (2°C). Risk of freezing. RECOMMENDATION: Inspect Goods."
        }
    else:
        return {
            "status": "COMPLIANT",
            "legal_ruling": "COMPLIANT: Shipment conditions are within agreed terms."
        }

# --- MQTT Logic ---
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        logger.info(f"received Alert for {payload['shipment_id']}")
        
        # Ask the Mock Brain
        decision = analyze_contract(payload)
        
        logger.info(f"⚖️ LEGAL DECISION: {decision['legal_ruling']}")
        
        # Publish
        decision_payload = {
            "shipment_id": payload['shipment_id'],
            "original_alert": payload,
            "legal_ruling": decision['legal_ruling'],
            "status": decision['status']
        }
        client.publish(OUTPUT_TOPIC, json.dumps(decision_payload))
        
    except Exception as e:
        logger.error(f"Processing Error: {e}")

def on_connect(client, userdata, flags, rc, properties=None):
    logger.info("Connected (Mock Agent). Waiting for Anomalies...")
    client.subscribe(INPUT_TOPIC)

if __name__ == "__main__":
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    
    while True:
        try:
            client.connect(BROKER_HOST, 1883, 60)
            client.loop_forever()
        except Exception as e:
            logger.warning("Waiting for broker...")
            time.sleep(5)