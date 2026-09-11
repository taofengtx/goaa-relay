#!/bin/bash  
# GOAA-20260510-RUNTIME-ACTIVATE  
# Execute on AiKa-2 to activate runtime and connect to DigitalOcean  
  
set -e  
echo "=== GOAA-20260510-RUNTIME-ACTIVATE ==="  
  
# Step 1: Sync repository  
echo "[Step 1] Syncing repository..."  
cd /opt/goaa/repo 2>/dev/null || git clone https://github.com/taofengtx/goaa-ai-frontend.git /opt/goaa/repo  
cd /opt/goaa/repo && git pull origin main  
mkdir -p /opt/goaa/runtime /opt/goaa/logs  
echo "✅ Step 1 OK"  
# Step 2-5 Watchdog and Registration  
  
echo "[Step 2] Deploying watchdog..."  
cat > /opt/goaa/runtime/watchdog.py <<< 'PYEOF'  
