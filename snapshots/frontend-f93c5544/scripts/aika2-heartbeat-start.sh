#!/bin/bash
# AIKA2-HEARTBEAT-START: Start heartbeat daemon on AiKa-2
# Execute on AiKa-2 (192.168.1.208) terminal directly
# This script installs deps and starts 30s heartbeat to DO VPS

set -e

echo "=== AiKa-2 Heartbeat Setup ==="
echo "Target: http://134.199.227.108:8080/worker/heartbeat"
echo ""

# Step 1: Install dependencies
echo "[1/4] Installing dependencies..."
pip3 install psutil requests -q
echo "✅ Dependencies installed"

# Step 2: Create heartbeat script
echo "[2/4] Creating heartbeat script..."
mkdir -p /opt/goaa/logs

cat > /opt/goaa/heartbeat.py << 'EOF'
import requests, psutil, subprocess, time

NODE_ID = "aika-2"
API = "http://134.199.227.108:8080"

while True:
    try:
        docker = subprocess.run(["docker","ps"],capture_output=True).returncode == 0
        try:
            requests.get("http://localhost:11434/api/tags",timeout=2)
            ollama = True
        except:
            ollama = False
        
        requests.post(f"{API}/worker/heartbeat", json={
            "worker_id": NODE_ID,
            "cpu": psutil.cpu_percent(interval=1),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage("/").percent,
            "docker": docker,
            "ollama": ollama
        }, timeout=5)
        print(f"Heartbeat: {NODE_ID} | CPU:{psutil.cpu_percent(interval=0)}% MEM:{psutil.virtual_memory().percent}%")
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(30)
EOF
echo "✅ heartbeat.py created"

# Step 3: Start heartbeat daemon
echo "[3/4] Starting heartbeat daemon..."
nohup python3 /opt/goaa/heartbeat.py > /opt/goaa/logs/heartbeat.log 2>&1 &
PID=$!
echo "✅ Heartbeat started (PID: $PID)"

# Step 4: Verify
echo "[4/4] Verifying..."
sleep 5
tail -3 /opt/goaa/logs/heartbeat.log
echo ""
echo "=== AiKa-2 Heartbeat Running ==="
echo "PID: $PID"
echo "Log: /opt/goaa/logs/heartbeat.log"
echo "Interval: 30 seconds"
echo ""
