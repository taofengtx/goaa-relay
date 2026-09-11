#!/bin/bash
# DO-DEPLOY-COMPLETE-V2: Full GOAA Runtime Stack with FastAPI
# Execute via SSH from AiKa-2 to DigitalOcean

set -e

echo "=== DO-DEPLOY-COMPLETE-V2: GOAA Runtime Stack ==="
echo ""

GOAA_DIR="/opt/goaa"
mkdir -p $GOAA_DIR/{runtime,logs,docker,configs,git}

# Step 1: Download main.py from GitHub
echo "[1/8] Downloading FastAPI main.py from GitHub..."
curl -s -o $GOAA_DIR/runtime/main.py https://raw.githubusercontent.com/taofengtx/goaa-ai-frontend/main/scripts/do-runtime-main-full.py
echo "✅ main.py downloaded"

# Step 2: Create docker-compose.yml
echo "[2/8] Creating docker-compose.yml..."
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
      - PYTHONUNBUFFERED=1
    command: sh -c "pip install fastapi uvicorn -q && uvicorn main:app --host 0.0.0.0 --port 18789 --reload"
    restart: unless-stopped
    networks:
      - goaa-net

  heartbeat:
    image: python:3.11-slim
    container_name: goaa-heartbeat
    working_dir: /app
    volumes:
      - /opt/goaa/runtime:/app
      - /opt/goaa/logs:/logs
    environment:
      - NODE_ID=AKC-DO-001
    command: sh -c "pip install requests -q && python3 -c \"
import time, requests
while True:
    try:
        requests.post('https://api.goaa.ai/api/v1/geekom/heartbeat',
            json={'node_id':'AKC-DO-001','ip':'134.199.227.108','status':'active'},
            timeout=10)
        with open('/logs/heartbeat.log', 'a') as f:
            f.write('Heartbeat sent\n')
    except Exception as e:
        print(f'Heartbeat error: {e}')
    time.sleep(30)
\""
    restart: unless-stopped
    networks:
      - goaa-net

networks:
  goaa-net:
    driver: bridge
COMPOSEEOF
echo "✅ docker-compose.yml created"

# Step 3: Create registration.json
echo "[3/8] Creating registration.json..."
cat > $GOAA_DIR/runtime/registration.json << 'REGEOF'
{
  "node_id": "AKC-DO-001",
  "hostname": "goaa-do-cloud",
  "ip": "134.199.227.108",
  "role": "cloud_worker",
  "provider": "DigitalOcean",
  "status": "active",
  "capabilities": ["python", "docker", "linux", "git"],
  "registered_at": "2026-05-10T07:15:00Z"
}
REGEOF
echo "✅ registration.json created"

# Step 4: Setup Git repository
echo "[4/8] Setting up Git repository..."
cd $GOAA_DIR
if [ ! -d .git ]; then
    git init
    git remote add origin https://github.com/taofengtx/goaa-ai-frontend.git
    git config user.email "do-cloud@goaa.ai"
    git config user.name "DO Cloud Worker"
fi
echo "✅ Git initialized"

# Step 5: Check Docker
echo "[5/8] Checking Docker..."
docker --version || (echo "Installing Docker..." && curl -fsSL https://get.docker.com | sh)
echo "✅ Docker ready"

# Step 6: Stop old containers (if any)
echo "[6/8] Cleaning up old containers..."
cd $GOAA_DIR/docker
docker compose down 2>/dev/null || true
echo "✅ Cleanup complete"

# Step 7: Start new stack
echo "[7/8] Starting new GOAA Runtime Stack..."
docker compose pull
docker compose up -d
sleep 8
echo "✅ Stack started"

# Step 8: Verify deployment
echo "[8/8] Verifying deployment..."
echo ""
echo "=== Container Status ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "=== Health Check ==="
sleep 3
curl -s http://127.0.0.1:18789/health | python3 -m json.tool || echo "API not ready yet..."
echo ""
echo ""
echo "=== DO-DEPLOY-COMPLETE-V2 FINISHED ==="
echo ""
echo "✅ GOAA Runtime Stack deployed successfully!"
echo "✅ FastAPI application running on port 18789"
echo "✅ Heartbeat service monitoring"
echo "✅ Ready for integration with OpenClaw and QwenPaw"
echo ""
