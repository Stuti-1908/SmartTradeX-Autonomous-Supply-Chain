import os
import json
import logging
import time
import paho.mqtt.client as mqtt
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

# --- Configuration ---
BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "mosquitto")
INPUT_TOPIC = "shipment/alerts"        # Trigger: Anomaly
OUTPUT_TOPIC = "shipment/final_decision" # Output: Action

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SUPERVISOR")

# --- 1. The State Schema (The Shared Brain) ---
class AgentState(TypedDict):
    shipment_id: str
    anomaly_score: float
    compliance_status: Optional[str] # "VIOLATION" or "CLEARED"
    finance_action: Optional[str]    # "HOLD" or "RELEASE"
    next_step: str

# --- 2. The Agent Nodes ---

def logistics_agent(state: AgentState):
    """Verifies the sensor data severity."""
    logger.info(f"🚚 Logistics Agent: Analyzing anomaly score {state['anomaly_score']}...")
    # Logic: If score is very low, it's a confirmed hardware issue
    return {"next_step": "compliance"}

def compliance_agent(state: AgentState):
    """The Lawyer. Checks the 'Contract'."""
    logger.info(f"⚖️ Compliance Agent: Checking Contract Terms...")
    time.sleep(1) # Simulate RAG lookup
    
    # Logic: If anomaly score < -0.02, it's a Breach.
    if state['anomaly_score'] < -0.02:
        status = "VIOLATION"
        logger.info("❌ Contract Clause 4.1 Breached!")
    else:
        status = "CLEARED"
    
    return {"compliance_status": status}

def finance_agent(state: AgentState):
    """The Banker. Controls the Money."""
    status = state.get("compliance_status")
    logger.info(f"💰 Finance Agent: Reviewing Compliance Status ({status})...")
    
    if status == "VIOLATION":
        action = "HOLD_PAYMENT"
    else:
        action = "RELEASE_FUNDS"
        
    logger.info(f"💵 Decision: {action}")
    return {"finance_action": action}

def supervisor_router(state: AgentState):
    """The Traffic Cop. Routes to the next agent."""
    if state.get("compliance_status") is None:
        return "compliance"
    elif state.get("finance_action") is None:
        return "finance"
    else:
        return "end"

# --- 3. Build the Graph ---
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("logistics", logistics_agent)
workflow.add_node("compliance", compliance_agent)
workflow.add_node("finance", finance_agent)

# Add Edges (The Logic Flow)
workflow.set_entry_point("logistics")

# Logistics -> Supervisor Check
workflow.add_conditional_edges(
    "logistics",
    supervisor_router,
    {"compliance": "compliance", "finance": "finance", "end": END}
)

# Compliance -> Supervisor Check
workflow.add_conditional_edges(
    "compliance",
    supervisor_router,
    {"compliance": "compliance", "finance": "finance", "end": END}
)

# Finance -> Supervisor Check
workflow.add_conditional_edges(
    "finance",
    supervisor_router,
    {"compliance": "compliance", "finance": "finance", "end": END}
)

app = workflow.compile()

# --- MQTT Logic ---
def process_alert(payload):
    shipment_id = payload.get("shipment_id", "UNKNOWN")
    score = float(payload.get("anomaly_score", 0))
    
    logger.info(f"🚀 Starting Supervisor Workflow for {shipment_id}")
    
    # Initialize State
    initial_state = {
        "shipment_id": shipment_id,
        "anomaly_score": score,
        "compliance_status": None,
        "finance_action": None,
        "next_step": "start"
    }
    
    # Run the Graph
    final_state = app.invoke(initial_state)
    
    # Publish Final Decision
    decision = {
        "shipment_id": shipment_id,
        "decision": final_state["finance_action"],
        "reason": final_state["compliance_status"]
    }
    client.publish(OUTPUT_TOPIC, json.dumps(decision))
    logger.info(f"✅ Workflow Complete. Final Output Sent.")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        process_alert(payload)
    except Exception as e:
        logger.error(f"Graph Error: {e}")

if __name__ == "__main__":
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = lambda c, u, f, r, p: c.subscribe(INPUT_TOPIC)
    client.on_message = on_message
    
    logger.info("Connecting to Broker...")
    client.connect(BROKER_HOST, 1883, 60)
    client.loop_forever()