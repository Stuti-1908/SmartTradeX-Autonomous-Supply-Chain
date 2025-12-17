import json
import logging
import os
import numpy as np
import paho.mqtt.client as mqtt
from sklearn.ensemble import IsolationForest
from collections import deque
import time

# --- Configuration ---
BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "mosquitto")
INPUT_TOPIC = "shipment/telemetry"
ALERT_TOPIC = "shipment/alerts"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ANOMALY_AI")

# --- The Brain (State) ---
# We keep the last 50 readings to retrain/refine our model
history_buffer = deque(maxlen=50)
model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
is_trained = False

def train_model():
    """Retrains the model on current history buffer"""
    global is_trained, model
    if len(history_buffer) < 20:
        return # Not enough data yet
    
    # We use Temp, Humidity, and Shock as features
    X = np.array(history_buffer)
    model.fit(X)
    is_trained = True
    logger.info(f"Model Retrained on {len(history_buffer)} data points.")

def process_data(data):
    """
    1. Extract features
    2. Add to buffer
    3. Predict anomaly
    """
    try:
        # Extract features (Temp, Humidity, Shock)
        # Use .get() to avoid crashing if a field is missing
        features = [
            float(data.get("temperature_celsius", 0)),
            float(data.get("humidity_percent", 0)),
            float(data.get("shock_g", 0))
        ]
        
        # Add to history for future training
        history_buffer.append(features)
        
        # Train initially if needed
        if not is_trained and len(history_buffer) >= 20:
            train_model()

        # If model is live, PREDICT
        if is_trained:
            # Reshape for single sample
            X_new = np.array([features])
            prediction = model.predict(X_new) # 1 = Normal, -1 = Anomaly
            score = model.decision_function(X_new)[0] # Lower score = more anomalous

            if prediction[0] == -1:
                logger.warning(f"🚨 ANOMALY DETECTED! Score: {score:.4f} | Data: {features}")
                
                # Publish Alert
                alert_payload = {
                    "shipment_id": data.get("shipment_id", "UNKNOWN"),
                    "timestamp": data.get("timestamp", ""),
                    "anomaly_score": float(score),
                    "trigger_values": features,
                    "message": "Abnormal sensor pattern detected (AI Model)"
                }
                client.publish(ALERT_TOPIC, json.dumps(alert_payload))
            else:
                logger.info(f"Normal Pattern (Score: {score:.2f})")

    except Exception as e:
        logger.error(f"Processing Error: {e}")

# --- MQTT Boilerplate ---
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        process_data(payload)
    except Exception as e:
        logger.error(f"Message Error: {e}")

def on_connect(client, userdata, flags, rc, properties=None):
    logger.info("Connected. Listening for Telemetry...")
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