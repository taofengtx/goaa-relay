# GOAA-20260510-RUNTIME-ACTIVATE - Complete Script  
#!/bin/bash  
set -e  
  
CLOUD_IP="134.199.227.108"  
GOAA_DIR="/opt/goaa"  
  
echo "=== GOAA-20260510-RUNTIME-ACTIVATE ==="  
echo ""  
echo "[1/5] Syncing repository..."  
cd $GOAA_DIR/repo 2>/dev/null || git clone https://github.com/taofengtx/goaa-ai-frontend.git $GOAA_DIR/repo  
cd $GOAA_DIR/repo && git pull origin main  
mkdir -p $GOAA_DIR/runtime $GOAA_DIR/logs  
echo "✅ Step 1 OK"  
