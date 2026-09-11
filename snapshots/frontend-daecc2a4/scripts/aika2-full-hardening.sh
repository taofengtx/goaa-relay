#!/bin/bash
# AIKA2-FULL-HARDENING: 6-Step System Hardening
# Execute on AiKa-2 terminal: bash <(curl -s ...)
set -e

echo "============================================"
echo "AiKa-2 System Hardening - 6 Steps"
echo "============================================"
echo ""

# ─── Step 1: Heartbeat systemd service ───────────
echo "━━━ [Step 1/6] Heartbeat systemd auto-start ━━━"
echo ""

# Create heartbeat.py
sudo mkdir -p /opt/goaa/logs

cat > /opt/goaa/heartbeat.py << 'HEARTEOF'
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
        print(f"Heartbeat: {NODE_ID}")
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(30)
HEARTEOF

echo "[1/6] heartbeat.py created"

# Create systemd service
sudo tee /etc/systemd/system/goaa-heartbeat.service > /dev/null << 'SERVICEEOF'
[Unit]
Description=GOAA AiKa-2 Heartbeat
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/goaa/heartbeat.py
Restart=always
RestartSec=30
Environment=NODE_ID=aika-2

[Install]
WantedBy=multi-user.target
SERVICEEOF

sudo systemctl daemon-reload
sudo systemctl enable goaa-heartbeat
sudo systemctl start goaa-heartbeat
echo "[1/6] ✅ Heartbeat service enabled & started"
sudo systemctl status goaa-heartbeat --no-pager | grep Active
echo ""

# ─── Step 2: Install Ollama ─────────────────────
echo "━━━ [Step 2/6] Installing Ollama ━━━"
echo ""

if command -v ollama &> /dev/null; then
    echo "[2/6] ⏩ Ollama already installed, skipping"
else
    curl -fsSL https://ollama.ai/install.sh | sh
    echo "[2/6] ✅ Ollama installed"
fi

sudo systemctl start ollama 2>/dev/null || true
sleep 3
echo "Starting model pull in background (may take 5-10 min)..."
nohup ollama pull qwen2.5:7b > /opt/goaa/logs/ollama-pull.log 2>&1 &
echo "[2/6] ✅ Ollama model pull started (PID: $!)"

echo "Checking Ollama API..."
curl -s http://localhost:11434/api/tags | python3 -m json.tool 2>/dev/null || echo "Ollama API not ready yet (model still pulling)"
echo ""

# ─── Step 3: Docker status check ────────────────
echo "━━━ [Step 3/6] Docker Status ━━━"
echo ""

docker ps 2>/dev/null || echo "No running containers"
echo ""
docker info 2>/dev/null | grep -E 'Server Version|Containers:|Running:|Images:' || echo "Docker not fully operational yet"
echo "[3/6] ✅ Docker status checked"
echo ""

# ─── Step 4: SSH Key Exchange ───────────────────
echo "━━━ [Step 4/6] SSH Key Exchange ─━━"
echo ""

mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Generate key if not exists
if [ ! -f ~/.ssh/id_ed25519 ]; then
    ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N "" -q
    echo "[4/6] ✅ SSH key generated on AiKa-2"
else
    echo "[4/6] ⏩ SSH key already exists"
fi

echo "[4/6] AiKa-2 public key:"
cat ~/.ssh/id_ed25519.pub
echo ""
echo "To add AiKa-2 → AiKa-1: run this on AiKa-1 PowerShell:"
echo '  Add-Content -Path "C:\Users\Administrator\.ssh\authorized_keys" -Value "PASTE_KEY_HERE"'
echo ""

# ─── Step 5: Verify cluster ─────────────────────
echo "━━━ [Step 5/6] Verifying Cluster Status ━━━"
echo ""

echo "Waiting 10s for heartbeat to register..."
sleep 10

echo "Workers from DO VPS:"
curl -s http://134.199.227.108:8080/workers/status | python3 -m json.tool 2>/dev/null || echo "Cannot reach DO VPS yet"
echo "[5/6] ✅ Cluster status checked"
echo ""

# ─── Step 6: Complete ───────────────────────────
echo "━━━ [Step 6/6] Complete ━━━"
echo ""
echo "============================================"
echo "✅ AiKa-2 System Hardening Complete!"
echo "============================================"
echo ""
echo "Services running:"
systemctl status goaa-heartbeat --no-pager 2>/dev/null | head -3
echo ""
echo "Heartbeat PID: $(pgrep -f heartbeat.py || echo 'checking...')"
echo "Ollama PID: $(pgrep -f ollama || echo 'not running yet')"
echo ""
echo "To monitor heartbeat:"
echo "  tail -f /opt/goaa/logs/heartbeat.log"
echo "To monitor Ollama pull:"
echo "  tail -f /opt/goaa/logs/ollama-pull.log"
echo ""
