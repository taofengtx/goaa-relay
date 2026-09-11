# PHASE2-EXECUTE-NOW.ps1
# Run this in PowerShell on AiKa-1
# This script deploys the updated Model Router API v2.0 to DO VPS

Write-Host "=== Phase 2 Real Runtime Deployment ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Download updated api.py
Write-Host "[1/4] Downloading api.py v2.0..." -ForegroundColor Yellow
ssh root@134.199.227.108 "cd /opt/goaa/router && curl -s -o api.py https://raw.githubusercontent.com/taofengtx/goaa-ai-frontend/main/services/model-router/api.py && echo Downloaded: $(wc -c < api.py) bytes"
Write-Host ""

# Step 2: Restart service
Write-Host "[2/4] Restarting goaa-model-router service..." -ForegroundColor Yellow
ssh root@134.199.227.108 "fuser -k 8080/tcp 2>/dev/null; sleep 2; systemctl restart goaa-model-router; sleep 4; systemctl is-active goaa-model-router"
Write-Host ""

# Step 3: Health check
Write-Host "[3/4] Verifying health..." -ForegroundColor Yellow
$health = ssh root@134.199.227.108 "curl -s http://127.0.0.1:8080/health"
Write-Host "Health: $health"
Write-Host ""

# Step 4: Test workers endpoint
Write-Host "[4/4] Testing /workers/status..." -ForegroundColor Yellow
$workers = ssh root@134.199.227.108 "curl -s http://127.0.0.1:8080/workers/status"
Write-Host "Workers: $workers"
Write-Host ""

Write-Host "=== Phase 2 Complete! ===" -ForegroundColor Green
Write-Host "Open https://portal.goaa.ai/dashboard to verify" -ForegroundColor Cyan
