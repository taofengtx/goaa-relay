# Phase 2 Real Runtime 执行指南
## GOAA-20260510-REAL — Real Worker OS v0.2

**GitHub Commit:** `ab2e14f`
**Dashboard 已推送 ✅**
**api.py v2.0 (15.4KB) 已推送 ✅**

---

## 第一步：在 DO VPS 更新 Model Router API

在 **AiKa-1 PowerShell** 执行：

```powershell
ssh root@134.199.227.108 "cd /opt/goaa/router && curl -s -o api.py https://raw.githubusercontent.com/taofengtx/goaa-ai-frontend/main/services/model-router/api.py && wc -c api.py"
```

預期輸出：`15382 /opt/goaa/router/api.py`

### 重啟服務

```powershell
ssh root@134.199.227.108 "fuser -k 8080/tcp 2>/dev/null; sleep 2; systemctl restart goaa-model-router; sleep 4; systemctl is-active goaa-model-router"
```

預期輸出：`active`

### 驗證健康檢查

```powershell
ssh root@134.199.227.108 "curl -s http://127.0.0.1:8080/health"
```

預期輸出：
```json
{"status":"ok","service":"goaa-model-router","version":"2.0.0","time":"...","ollama_available":false,"claude_available":true,"claude_hourly_cost":0,"claude_daily_cost":0}
```

### 驗證 Worker 端點（新功能）

```powershell
ssh root@134.199.227.108 "curl -s http://127.0.0.1:8080/workers/status"
```

預期輸出：
```json
{"workers":[],"total_workers":0}
```

---

## 第二步：提交測試任務

```powershell
ssh root@134.199.227.108 @'
curl -s -X POST http://127.0.0.1:8080/route `
  -H "Content-Type: application/json" `
  -d '{"prompt":"check DO runtime status","priority":2,"risk_level":1}'
'@
```

預期輸出：
```json
{"selected_model":"deepseek-v4-flash","estimated_cost_usd":0.00028, ...}
```

### 測試 DeepSeek 真實 Chat

```powershell
ssh root@134.199.227.108 @'
curl -s -X POST http://127.0.0.1:8080/chat `
  -H "Content-Type: application/json" `
  -d '{"prompt":"What is Docker?","priority":2,"risk_level":1}'
'@
```

---

## 第三步：驗證 Dashboard

打開瀏覽器訪問：**https://portal.goaa.ai/dashboard**

確認：
- ✅ Worker 列表顯示正常
- ✅ Task History 可讀
- ✅ 5秒自動刷新
- ✅ Real Logs 顯示
- ✅ Cost / Revenue / Profit 面板

---

## 架構總結

```
AiKa-1 (Windows)
├── Ollama Qwen2.5:7b → localhost:11434
└── SSH → DO VPS

DO VPS (134.199.227.108)
├── Port 18789 → goaa-openclaw (FastAPI Runtime)
├── Port 8080  → goaa-model-router (systemd 持久化)
│   ├── GET  /health
│   ├── POST /route
│   ├── POST /chat
│   ├── POST /task/complete
│   ├── POST /worker/heartbeat
│   ├── GET  /workers/status
│   ├── GET  /workers/metrics
│   ├── GET  /cost/status
│   ├── GET  /revenue/status
│   ├── GET  /profit/status
│   ├── GET  /tasks/history
│   └── GET  /models/status
├── Docker Compose → goaa-openclaw + goaa-heartbeat
└── systemd → goaa-model-router (自動重啟)

Vercel (Cloud)
└── portal.goaa.ai/dashboard → GoaaDashboard.jsx
```
