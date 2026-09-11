#!/bin/bash
# AiKa-2 Bootstrap Script (NODE-20260509-002-L1)
# Execute on AiKa-2 (192.168.1.208)

set -e

echo "=========================================="
echo "NODE-20260509-002-L1: AiKa-2 Bootstrap"
echo "=========================================="
echo ""

# Step 1: System Update
echo "[1/6] System Update..."
sudo apt-get update -y > /tmp/apt-update.log 2>&1
sudo apt-get install -y git curl python3 python3-pip python3-venv docker.io > /tmp/apt-install.log 2>&1
echo "✅ System updated and packages installed"

# Step 2: Create GOAA directory structure
echo "[2/6] Creating /opt/goaa directory structure..."
sudo mkdir -p /opt/goaa
sudo mkdir -p /opt/goaa/logs
sudo mkdir -p /opt/goaa/data
sudo mkdir -p /opt/goaa/config

# Change ownership to current user
sudo chown -R $(whoami):$(whoami) /opt/goaa
echo "✅ Directory structure created"

# Step 3: Clone/Update Repository
echo "[3/6] Cloning GOAA AI Frontend repository..."
cd /opt/goaa
if [ -d "repo" ]; then
    cd repo && git pull origin main && cd ..
else
    git clone https://github.com/taofengtx/goaa-ai-frontend.git repo
fi
echo "✅ Repository ready"

# Step 4: Python Virtual Environment
echo "[4/6] Setting up Python virtual environment..."
cd /opt/goaa
python3 -m venv venv
source venv/bin/activate
pip install -q fastapi uvicorn httpx psutil requests flask sqlite3
echo "✅ Virtual environment ready"

# Step 5: Node Registration
echo "[5/6] Creating node registration file..."
cat > /opt/goaa/registration.json << 'REGEOF'
{
  "node_id": "COORD-002",
  "hostname": "AiKa-2",
  "ip": "192.168.1.208",
  "role": "secondary_coordinator",
  "status": "active",
  "capabilities": {
    "cpu_cores": 4,
    "memory_gb": 8,
    "docker": true,
    "gpu": false
  },
  "services": {
    "heartbeat_api": {
      "port": 5001,
      "status": "ready_for_deployment"
    },
    "task_pull_api": {
      "port": 5002,
      "status": "ready_for_deployment"
    }
  },
  "registered_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
REGEOF
echo "✅ Node registration created"

# Step 6: Verify Installation
echo "[6/6] Verifying installation..."
echo ""
echo "=== Node Registration ==="
cat /opt/goaa/registration.json
echo ""
echo "=== System Info ==="
uname -a
echo ""
echo "=== Memory Info ==="
free -h
echo ""
echo "=== Disk Info ==="
df -h /
echo ""
echo "=== Python Info ==="
/opt/goaa/venv/bin/python3 --version
echo ""
echo "=========================================="
echo "✅ NODE-20260509-002-L1 Bootstrap Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Deploy Heartbeat API: systemctl start node-heartbeat-api"
echo "  2. Deploy Task Pull API: systemctl start task-pull-api"
echo "  3. Check logs: journalctl -u node-heartbeat-api -f"
