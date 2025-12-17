# 🚛 SmartTradeX: Autonomous AI Supply Chain Enforcer

> **A Self-Healing Logistics Platform that uses Edge AI to detect failures and Autonomous Agents (LangGraph) to enforce contracts in real-time.**

![Python](https://img.shields.io/badge/Python-3.9-blue?style=for-the-badge&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![LangGraph](https://img.shields.io/badge/AI-LangGraph-orange?style=for-the-badge)
![InfluxDB](https://img.shields.io/badge/DB-InfluxDB-purple?style=for-the-badge&logo=influxdb&logoColor=white)
![Grafana](https://img.shields.io/badge/Dashboard-Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white)

---

## 📸 System Overview

![SmartTradeX Dashboard](https://github.com/Stuti-1908/SmartTradeX-Autonomous-Supply-Chain/blob/main/dashboard-screenshot.png?raw=true)

*Above: The system detects a refrigeration failure (Red Graph), triggers an AI Alert (Anomaly Score), and the Agent autonomously blocks the payment (Status: BLOCKED).*

---

## 🧠 The Problem
Traditional supply chains are **reactive**. If a container of vaccines overheats, the data is logged, but the financial loss happens anyway.

**SmartTradeX** changes this to an **active** system. It doesn't just log errors; it physically intervenes in the financial transaction logic to prevent loss using Autonomous AI Agents.

---

## 🏗️ Architecture

The system follows a distributed microservices architecture containerized with Docker.

```mermaid
graph TD
    A[IoT Simulator] -->|MQTT: Telemetry| B(Mosquitto Broker)
    B -->|Stream| C[Edge Anomaly Detector]
    B -->|Stream| D[Ingestion Service]
    
    subgraph "The Brain (AI Layer)"
    C -->|Alert: Anomaly Detected| E[LangGraph Orchestrator]
    E -->|1. Logistics Check| E
    E -->|2. Compliance RAG| E
    E -->|3. Finance Decision| B
    end
    
    subgraph "The Storage & View"
    D -->|Write| F[(InfluxDB)]
    F -->|Query| G[Grafana Dashboard]
    end

