#!/bin/bash
# Deploy Node Heartbeat API on AiKa-2
# Usage: ./deploy-heartbeat-api.sh <aika2_ip> <aika2_user>

set -e

AIKA2_IP=${1:-192.168.1.208}
AIKA2_USER=${2:-root}
SCRIPT_PATH="scripts/node_heartbeat_api.py"
SERVICE_PATH="etc/node-heartbeat-api.service"

echo "=========================================="
echo "Deploying Node Heartbeat API to AiKa-2"
echo "Target: ${AIKA2_USER}@${AIKA2_IP}"
echo "=========================================="

# Step 1: Create directories on AiKa-2
echo "[1/5] Creating directories on AiKa-2..."
ssh ${AIKA2_USER}@${AIKA2_IP} "mkdir -p /root/goaa-ai/scripts /root/goaa-ai/runtime /root/goaa-ai/logs"

# Step 2: Copy Python script
echo "[2/5] Copying Python script..."
scp ${SCRIPT_PATH} ${AIKA2_USER}@${AIKA2_IP}:/root/goaa-ai/scripts/
ssh ${AIKA2_USER}@${AIKA2_IP} "chmod +x /root/goaa-ai/scripts/node_heartbeat_api.py"

# Step 3: Copy systemd service
echo "[3/5] Copying systemd service..."
scp ${SERVICE_PATH} ${AIKA2_USER}@${AIKA2_IP}:/etc/systemd/system/node-heartbeat-api.service
ssh ${AIKA2_USER}@${AIKA2_IP} "chmod 644 /etc/systemd/system/node-heartbeat-api.service"

# Step 4: Enable and start service
echo "[4/5] Enabling and starting service..."
ssh ${AIKA2_USER}@${AIKA2_IP} "systemctl daemon-reload && systemctl enable node-heartbeat-api.service && systemctl start node-heartbeat-api.service"

# Step 5: Verify
echo "[5/5] Verifying deployment..."
echo ""
echo "=== Service Status ==="
ssh ${AIKA2_USER}@${AIKA2_IP} "systemctl status node-heartbeat-api.service"
echo ""
echo "=== Recent Logs ==="
ssh ${AIKA2_USER}@${AIKA2_IP} "journalctl -u node-heartbeat-api.service -n 20"
echo ""
echo "=== Health Check ==="
ssh ${AIKA2_USER}@${AIKA2_IP} "sleep 2 && curl -s http://localhost:5001/health | python3 -m json.tool || echo 'Service still starting...'"

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Service is now running on AiKa-2"
echo "API Endpoint: http://${AIKA2_IP}:5001"
echo ""
echo "Test heartbeat endpoint:"
echo "  curl -X POST http://${AIKA2_IP}:5001/api/v1/node/heartbeat \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"node_id\": \"aika-2\", \"cpu_usage\": 45.2, \"ram_usage\": 62.5, \"active_tasks\": 5}'"
echo ""
echo "Monitor logs:"
echo "  ssh ${AIKA2_USER}@${AIKA2_IP} 'journalctl -u node-heartbeat-api.service -f'"
echo ""
