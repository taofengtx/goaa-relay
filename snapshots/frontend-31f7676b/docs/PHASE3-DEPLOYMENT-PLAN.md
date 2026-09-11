# GOAA.AI 集群結構與 Phase 3 部署計劃

**Date:** 2026-05-10  
**Status:** Phase 2 Complete → Phase 3 Ready

---

## 當前集群結構

```
┌─────────────────────────────────────────────────────────────┐
│                    goaa.ai (Framer)                         │
│                  portal.goaa.ai (Vercel)                    │
│              api.goaa.ai (Cloudflare Tunnel)                │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│         DigitalOcean VPS (134.199.227.108) — 主雲端          │
│                                                             │
│  Model Router API :8080 (systemd)                          │
│  ├── GET  /health         ✅                                │
│  ├── POST /route          ✅ deepseek-v4-flash (default)    │
│  ├── POST /chat           ✅                                │
│  ├── POST /task/complete  ✅ → logs/tasks/                  │
│  ├── GET  /workers/status ✅ 4 workers                      │
│  ├── GET  /revenue/status ✅ real P&L                       │
│  └── GET  /tasks/history  ✅                                │
│                                                             │
│  logs/ (persistent JSONL)                                   │
│  ├── tasks/   revenue/   profit/                           │
│  └── router/  workers/   circuit-breaker/                  │
└──────────┬──────────────────────┬───────────────────────────┘
           │                      │
┌──────────▼──────────┐ ┌─────────▼──────────────────────────┐
│  AiKa-1 (Primary)   │ │  AiKa-2 (Secondary)                │
│  192.168.1.207      │ │  192.168.1.208                     │
│  Windows 11         │ │  Xubuntu 24.04                     │
│                     │ │                                    │
│  ✅ Ollama:11434     │ │  ✅ Heartbeat (systemd)             │
│  ✅ qwen2.5:7b      │ │  ⏳ Ollama (installing)             │
│  ✅ Heartbeat PID   │ │  ✅ Docker                          │
│  ✅ Docker          │ │  ✅ Python venv                     │
│  ✅ GitHub 主節點   │ │  ✅ GitHub 同步                     │
└─────────────────────┘ └────────────────────────────────────┘

Hetzner (5.78.76.21) — 只讀保留 · 3天後下線
```

---

## Phase 2 已完成 ✅

| 組件 | 狀態 |
|------|------|
| Model Router API v2.0 | ✅ DO :8080 systemd |
| DeepSeek 默認模型 (85%) | ✅ API Key 已配置 |
| Claude 硬限制 (P0/P1+risk≥4) | ✅ |
| Ollama fallback | ✅ AiKa-1 :11434 |
| 任務日誌持久化 | ✅ JSONL files |
| 真實 P&L 追蹤 | ✅ revenue/profit |
| Dashboard 5s polling | ✅ |
| Worker 心跳 aika-1 | ✅ 30s interval |
| Worker 心跳 aika-2 | ✅ systemd |
| 4 Worker 集群注冊 | ✅ |

---

## Phase 3 部署計劃

### P0：本週必須完成

**OPENCLAW-20260511-001** — OpenClaw 遷移到 DO
```
目標：把 OpenClaw + QwenPaw 從 Hetzner 遷移到 DigitalOcean
節點：AiKa-2 → DO VPS
步驟：
1. 在 DO 拉取 OpenClaw 源碼
2. 配置 docker-compose.yml
3. 啟動 OpenClaw :18789 + QwenPaw :8088
4. 更新 Cloudflare Tunnel → DO IP
5. 驗證 api.goaa.ai 指向 DO
```

**DB-20260511-001** — PostgreSQL 持久化
```
目標：Credits + 用戶數據持久化
節點：DO VPS
步驟：
1. docker run postgres:16
2. 建立 goaa 數據庫
3. 遷移 users.json → users 表
4. Credits 表（user_id, balance, transactions）
```

**SEC-20260511-001** — bcrypt 密碼加固
```
目標：替換明文密碼
節點：DO VPS (OpenClaw)
步驟：
1. pip install bcrypt
2. 修改 /api/v1/agent/login 驗證邏輯
3. 遷移現有密碼
```

### P1：下週

**CLOUDFLARE-20260512-001** — Tunnel 切換 DO
```
當前：api.goaa.ai → Hetzner 5.78.76.21
目標：api.goaa.ai → DO 134.199.227.108
方法：更新 Cloudflare Tunnel 配置
影響：Hetzner 可安全下線
```

**VOICE-20260513-001** — Voice Agent 原型
```
目標：Whisper STT + TTS 語音對話
技術：OpenAI Whisper API + browser MediaRecorder
入口：portal.goaa.ai/voice
```

### P2：月底

- Stripe Credits 充值
- AiKa-Test 自動審計
- 技能市場 v2

---

## 下一個立刻執行的任務

```
OPENCLAW-20260511-001 Step 1：
在 DO VPS 準備 OpenClaw 環境

ssh root@134.199.227.108 "
mkdir -p /opt/goaa/openclaw
cd /opt/goaa/openclaw
git clone https://github.com/taofengtx/goaa-ai-frontend.git . 2>/dev/null || git pull
"
```

---

*架構 PM：Claude | 最後更新：2026-05-10*
