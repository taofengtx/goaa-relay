#!/bin/bash
# do-deploy-phase1.sh - Fixed YAML generation
set -e

echo "=== Phase 1: GOAA Runtime Stack Deployment ==="

GOAA_DIR="/opt/goaa"
mkdir -p $GOAA_DIR/{runtime,logs,docker,configs}

echo "[1/7] Creating FastAPI main.py..."
cat > $GOAA_DIR/runtime/main.py << 'PYEOF'
from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="GOAA Cloud Worker", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok", "node": "AKC-DO-001", "time": datetime.utcnow().isoformat()}

@app.get("/api/v1/node/info")
def node_info():
    return {
        "node_id": "AKC-DO-001",
        "ip": "134.199.227.108",
        "role": "cloud_worker",
        "capabilities": ["python", "docker", "linux"],
        "status": "active"
    }

@app.post("/api/v1/task/receive")
def receive_task(task: dict):
    return {"received": True, "task_id": task.get("id"), "node": "AKC-DO-001"}
PYEOF
echo "✅ main.py created"

echo "[2/7] Creating heartbeat.py..."
cat > $GOAA_DIR/runtime/heartbeat.py << 'HBEOF'
import time, requests

NODE_ID = "AKC-DO-001"
API_URL = "https://api.goaa.ai/api/v1/geekom/heartbeat"

while True:
    try:
        requests.post(API_URL,
            json={"node_id": NODE_ID, "ip": "134.199.227.108", "status": "active"},
            timeout=10)
        print(f"Heartbeat sent: {NODE_ID}")
    except Exception as e:
        print(f"Heartbeat failed: {e}")
    time.sleep(30)
HBEOF
echo "✅ heartbeat.py created"

echo "[3/7] Creating docker-compose.yml..."
cat > $GOAA_DIR/docker/docker-compose.yml << 'COMPOSEEOF'
version: "3.9"

services:
  openclaw:
    image: python:3.11-slim
    container_name: goaa-openclaw
    working_dir: /app
    volumes:
      - /opt/goaa/runtime:/app
      - /opt/goaa/logs:/logs
    ports:
      - "18789:18789"
    environment:
      - NODE_ID=AKC-DO-001
    command: sh -c "pip install fastapi uvicorn -q && uvicorn main:app --host 0.0.0.0 --port 18789"
    restart: unless-stopped

  heartbeat:
    image: python:3.11-slim
    container_name: goaa-heartbeat
    working_dir: /app
    volumes:
      - /opt/goaa/runtime:/app
    command: sh -c "pip install requests -q && python3 heartbeat.py"
    restart: unless-stopped

networks:
  default:
    name: goaa-net
COMPOSEEOF
echo "✅ docker-compose.yml created"

echo "[4/7] Creating registration.json..."
cat > $GOAA_DIR/runtime/registration.json << 'REGEOF'
{
  "node_id": "AKC-DO-001",
  "hostname": "goaa-do-cloud",
  "ip": "134.199.227.108",
  "role": "cloud_worker",
  "provider": "DigitalOcean",
  "status": "active",
  "capabilities": ["python", "docker", "linux", "git"]
}
REGEOF
echo "✅ registration.json created"

echo "[5/7] Checking Docker..."
docker --version
echo "✅ Docker is installed"

echo "[6/7] Starting Docker Compose stack..."
cd $GOAA_DIR/docker
docker compose down 2>/dev/null || true
docker compose up -d
echo "✅ Stack started"

echo "[7/7] Verifying..."
sleep 15
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
curl -s http://127.0.0.1:18789/health || echo "Waiting for startup..."

echo "=== Phase 1 Complete ==="
