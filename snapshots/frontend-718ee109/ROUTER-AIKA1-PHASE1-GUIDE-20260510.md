# ROUTER-20260510-001: AiKa-1 First Phase Deployment Guide

**Time:** 2026-05-10 08:00 UTC  
**Location:** AiKa-1 (192.168.1.207) - QwenPaw Scheduler Hub  
**Objective:** Establish local fallback & cost governance baseline

---

## 🎯 Why AiKa-1 First (Phase 1)

✅ **Strategic Reasons:**
- AiKa-1 = **QwenPaw main scheduler center**
- Router deployed on **AiKa-1**
- Docker **main environment** on AiKa-1
- GitHub **main sync node** on AiKa-1
- Network access to **internal services**
- **Cost governance** hub

❌ **Not AiKa-2 (yet):**
- AiKa-2 is secondary coordinator (backup)
- Will be edge node + fallback inference in Phase 2
- Currently focus on stability of main infrastructure

---

## 📋 Step-by-Step Execution Guide

### Step 1: Install Ollama on AiKa-1

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Expected Output:**
```
>>> Installing ollama to /usr/local/bin...
>>> Downloading ollama...
[████████████████████████] 100%
>>> Ollama installed successfully!
```

---

### Step 2: Start Ollama Service

```bash
sudo systemctl start ollama
sudo systemctl status ollama
```

**Expected Output:**
```
● ollama.service - Ollama
     Loaded: loaded (/etc/systemd/system/ollama.service; enabled)
     Active: active (running) since 2026-05-10 08:05:00 UTC
```

---

### Step 3: Pull Qwen2.5:7B Model

```bash
ollama pull qwen2.5:7b
```

**Expected Output:**
```
pulling manifest
pulling abc123...
verifying sha256 digest
writing manifest
removing any unused layers
success
```

**Time:** ~5-10 minutes (depending on network speed)

---

### Step 4: Verify Installation

```bash
curl http://localhost:11434/api/tags
```

**Expected Output:**
```json
{
  "models": [
    {
      "name": "qwen2.5:7b",
      "modified_at": "2026-05-10T08:10:00Z",
      "size": 4719816704,
      "digest": "abc123def456..."
    }
  ]
}
```

---

### Step 5: Test Router Configuration

```bash
cd ~/Projects/goaa-ai-local
python3 services/model-router/router.py
```

**Expected Output:**
```
=== GOAA Model Router Test ===

[Test 1] Regular Task (P2, Risk 1)
  Selected Model: deepseek-v4-flash (85% allocation)
  Estimated Cost: $0.0008 ✅

[Test 2] High-Risk Task (P0, Risk 4)
  Selected Model: claude-sonnet-4-6 (5% allocation)
  Estimated Cost: $0.045
  Review Required: Yes ✅

[Test 3] Cost Limit Exceeded
  Selected Model: ollama-qwen-32b (fallback)
  Cost: $0.0 (local execution) ✅

=== Routing Summary ===
DeepSeek:   85% (default)
Claude:      5% (P0/P1 high-risk)
Ollama:     10% (local fallback) + circuit breaker
```

---

## 🔧 Current Configuration

### Routing Strategy

| Model | Share | Purpose | Cost/1k tokens |
|-------|-------|---------|-----------------|
| **DeepSeek V4 Flash** | 85% | Default daily tasks | $0.00014 (in), $0.00028 (out) |
| **Claude Sonnet 4.6** | 5% | P0/P1 high-risk only | $0.003 (in), $0.015 (out) |
| **Ollama Qwen2.5:7B** | 10% | Local fallback | $0.0 (free) |

### Circuit Breaker Protection

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Hourly cost limit | $2.0/hour | Disable costly models, fallback to Ollama |
| Single call cost | $0.05/call | Mark review_required=True |
| Daily cost limit | $10.0/day | Alert email sent |

### Budget Limits

- **Daily:** $10.0 USD
- **Monthly:** $100.0 USD
- **Alert Email:** tao@goaa.ai

---

## ✅ Verification Checklist

- [ ] Ollama installed successfully
- [ ] Ollama service running (systemctl status)
- [ ] Qwen2.5:7B model downloaded
- [ ] curl http://localhost:11434/api/tags returns model list
- [ ] python3 services/model-router/router.py executes without errors
- [ ] Router selects DeepSeek for regular tasks (85%)
- [ ] Router selects Claude only for P0/P1 high-risk (5%)
- [ ] Router can fallback to Ollama when costs exceed limits

---

## 🚀 One-Command Quick Setup

If you want to automate the entire process on AiKa-1:

```bash
bash <(curl -s https://raw.githubusercontent.com/taofengtx/goaa-ai-frontend/main/AIKA1-OLLAMA-SETUP-20260510.sh)
```

Then test:

```bash
bash <(curl -s https://raw.githubusercontent.com/taofengtx/goaa-ai-frontend/main/AIKA1-ROUTER-TEST-20260510.sh)
```

---

## 📊 Current Phase Status

| Phase | Component | Status |
|-------|-----------|--------|
| **Phase 1 (Current)** | AiKa-1 Ollama + Router | ⏳ Ready for deployment |
| **Phase 2 (Next)** | AiKa-2 as edge node | ⏳ Pending Phase 1 completion |
| **Phase 3 (Future)** | Network federation | ⏳ Pending Phase 2 completion |

---

## 🎯 Success Criteria

✅ **Phase 1 Complete When:**
1. Ollama running on AiKa-1 (192.168.1.207:11434)
2. Qwen2.5:7B model available and responsive
3. Router correctly selecting models by priority/risk
4. Cost governance and circuit breaker working
5. Daily cost tracking active

---

## 📞 Next Steps

After Phase 1 completion (AiKa-1):

1. Verify router stability for 24 hours
2. Monitor cost tracking accuracy
3. Test circuit breaker threshold
4. Plan Phase 2 (AiKa-2 edge node deployment)

---

**Tao 师兄 - Please execute in order and report results:**
1. Git commit hash for router configuration
2. Ollama installation status
3. Model list output (curl /api/tags)
4. Router test output

**Commit Reference:**
- Router code: Commit `fd3ade7`
- Config updated: Pending your feedback

