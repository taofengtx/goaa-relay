# Runtime Auto Repair System

**Version:** 2.1  
**Last Updated:** 2026-05-09 11:35 UTC

## Overview

Automated detection and repair system for GOAA.AI runtime infrastructure.

---

## 1. API Auto-Detection

**Monitored Endpoints:**
- `https://api.goaa.ai/health` - OpenClaw health
- `https://api.goaa.ai/api/v1/chat/ws` - WebSocket connectivity
- `https://api.goaa.ai/downloads/` - Static file serving

**Health Criteria:**
- Response time < 2000ms
- HTTP status 200
- Valid JSON response

**Auto Repair Actions:**
- Restart OpenClaw service (if AKC-001 accessible)
- Check Cloudflare Tunnel status
- Verify DNS resolution

---

## 2. GitHub Auto-Detection

**Monitored Items:**
- Repository connectivity
- Branch integrity
- Latest commit reachability
- .gitignore compliance

**Health Criteria:**
- `git fetch` succeeds
- `git status` clean or with expected changes
- No orphaned branches

**Auto Repair Actions:**
- Re-establish SSH connection
- Garbage collect local repo
- Reset to origin/main (if safe)

---

## 3. Node Heartbeat Detection

**Monitoring:**
- AiKa-1: Windows primary (5 min interval)
- AiKa-2: Ubuntu worker (5 min interval)
- AKC-001: Cloud node (5 min interval)

**Health Criteria:**
- Responds within timeout
- Returns valid heartbeat JSON
- CPU/Memory healthy
- Disk space available

**Auto Repair Actions:**
- Automatic restart (low-risk only)
- Trigger bootstrap retry (AiKa-2)
- DNS/network troubleshooting

---

## 4. Queue Detection & Repair

**Monitored Metrics:**
- Queue depth
- Stuck tasks (running > 1 hour)
- Failed task retry count
- Worker availability

**Health Criteria:**
- Queue depth < 100
- No tasks stuck > 1 hour
- Failed retry < 3 attempts remaining
- At least 1 worker online

**Auto Repair Actions:**
- Reassign stuck tasks
- Retry failed tasks
- Rebalance queue load
- Alert if queue saturation > 80%

---

## 5. Docs Integrity Detection

**Scanned Directories:**
- `docs/runtime/` - Runtime configs
- `docs/bootstrap/` - Bootstrap docs
- `docs/logs/` - Execution logs
- `docs/security/` - Security protocols
- `docs/agents/` - Agent registry

**Health Criteria:**
- All required files present
- No corrupted markdown
- Valid JSON structures
- Links not broken (internal)

**Auto Repair Actions:**
- Regenerate missing files
- Fix markdown syntax errors
- Validate JSON structures
- Auto-commit repairs

---

## 6. Auto Low-Risk Repair

**Allowed Auto Actions:**
- ✅ Create missing .json/.md files
- ✅ Fix markdown syntax
- ✅ Update timestamps
- ✅ Rotate old logs
- ✅ Update heartbeat records
- ✅ Rebalance queue
- ✅ Restart services (non-critical)

**Forbidden Auto Actions:**
- ❌ Delete any files
- ❌ Modify credentials
- ❌ Change node configuration
- ❌ Alter bootstrap scripts
- ❌ Modify security policies

---

## 7. Tao Approval Request Mechanism

**High-Risk Actions Require Approval:**

```json
{
  "approval_request": {
    "id": "APPROVAL-20260509-001",
    "timestamp": "2026-05-09T11:35:00Z",
    "severity": "high",
    "action": "Restart OpenClaw service",
    "reason": "API health check failed 3 times",
    "node": "AKC-001 (5.78.76.21)",
    "status": "pending",
    "requested_by": "AiKa-1",
    "requested_at": "2026-05-09T11:35:00Z",
    "awaiting_approval_from": "Tao"
  }
}
```

**Approval Flow:**
1. AiKa detects high-risk problem
2. Generate approval request JSON
3. Output to console
4. Await Tao confirmation
5. Execute upon approval
6. Log result

---

## 8. Repair Execution Flow

```
Detection → Classification → Decision Tree → Action → Validation → Report
   ↓            ↓                ↓            ↓         ↓            ↓
Every 5m   Low/High Risk    Auto/Approval  Execute  Verify     GitHub Sync
```

---

## 9. Metrics & Logging

**Logged to:** `docs/logs/auto-repair.log`

```
2026-05-09T11:35:00Z | API | health | OK | -
2026-05-09T11:40:00Z | GitHub | connectivity | OK | -
2026-05-09T11:45:00Z | Node | AiKa-1 | OK | 45% CPU, 62% Memory
2026-05-09T11:50:00Z | Queue | depth | WARNING | 75 pending tasks
2026-05-09T11:50:05Z | Queue | rebalance | EXECUTED | Reassigned 5 tasks
```

---

## Status

- **System:** Ready for Phase-2 deployment
- **Last Check:** 2026-05-09 11:35 UTC
- **Uptime:** Continuous
