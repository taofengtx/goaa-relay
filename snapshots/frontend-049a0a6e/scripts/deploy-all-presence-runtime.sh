#!/bin/bash
# Deploy All Presence Runtime Services
# PRESENCE-DEPLOY-20260509-001

set -e

AIKA1_IP=${1:-192.168.1.207}
AIKA2_IP=${2:-192.168.1.208}
AIKA_USER=${3:-root}

echo "=========================================="
echo "PRESENCE-DEPLOY-20260509-001"
echo "Deploying all runtime services"
echo "=========================================="
echo "AiKa-1: ${AIKA1_IP}"
echo "AiKa-2: ${AIKA2_IP}"
echo ""

# Step 1: Deploy to AiKa-2
echo "========== DEPLOY-1: Heartbeat API on AiKa-2 =========="
./deploy-heartbeat-api.sh ${AIKA2_IP} ${AIKA_USER}

# Step 2: Deploy Task Pull API to AiKa-2
echo ""
echo "========== DEPLOY-2: Task Pull API on AiKa-2 =========="
echo "Deploying Task Pull API..."
scp scripts/task_pull_api.py ${AIKA_USER}@${AIKA2_IP}:/root/goaa-ai/scripts/
ssh ${AIKA_USER}@${AIKA2_IP} "chmod +x /root/goaa-ai/scripts/task_pull_api.py"
scp etc/task-pull-api.service ${AIKA_USER}@${AIKA2_IP}:/etc/systemd/system/
ssh ${AIKA_USER}@${AIKA2_IP} "systemctl daemon-reload && systemctl enable task-pull-api.service && systemctl start task-pull-api.service"
echo "✅ Task Pull API deployed"

# Step 3: Deploy Presence Watchdog to AiKa-1
echo ""
echo "========== DEPLOY-3: Presence Watchdog on AiKa-1 =========="
echo "Deploying Presence Watchdog..."
scp scripts/presence_watchdog.py ${AIKA_USER}@${AIKA1_IP}:/root/goaa-ai/scripts/
ssh ${AIKA_USER}@${AIKA1_IP} "chmod +x /root/goaa-ai/scripts/presence_watchdog.py"
scp etc/presence-watchdog.service ${AIKA_USER}@${AIKA1_IP}:/etc/systemd/system/
ssh ${AIKA_USER}@${AIKA1_IP} "systemctl daemon-reload && systemctl enable presence-watchdog.service && systemctl start presence-watchdog.service"
echo "✅ Presence Watchdog deployed"

# Step 4: Deploy Metrics Collector to AiKa-1
echo ""
echo "========== DEPLOY-4: Metrics Collector on AiKa-1 =========="
echo "Deploying Metrics Collector..."
scp scripts/runtime_presence_metrics.py ${AIKA_USER}@${AIKA1_IP}:/root/goaa-ai/scripts/
ssh ${AIKA_USER}@${AIKA1_IP} "chmod +x /root/goaa-ai/scripts/runtime_presence_metrics.py"
scp etc/runtime-metrics.service ${AIKA_USER}@${AIKA1_IP}:/etc/systemd/system/
ssh ${AIKA_USER}@${AIKA1_IP} "systemctl daemon-reload && systemctl enable runtime-metrics.service && systemctl start runtime-metrics.service"
echo "✅ Metrics Collector deployed"

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
