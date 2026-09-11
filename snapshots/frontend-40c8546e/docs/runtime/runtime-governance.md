# GOAA.AI Runtime Governance Policy

**Task ID:** RUNTIME-GOVERNANCE-20260509-001  
**Last Updated:** 2026-05-10  
**Status:** Active

---

## 分層架構

| 層級 | 名稱 | 模式 | 說明 |
|------|------|------|------|
| L0 | Core Runtime | Persistent | OpenClaw、QwenPaw |
| L1 | Node Runtime | Persistent | Heartbeat、Presence Registry |
| L2 | Queue Runtime | Persistent | Task Queue、Core Scheduler |
| L3 | Metrics Runtime | Timer/Cron | 指標收集、健康報告 |
| L4 | UI Runtime | Request-based | 前端渲染、API 響應 |
| L5 | Experimental | 禁止 Persistent | 測試功能 |

---

## ✅ 允許 Persistent 的服務（僅限以下6個）

- `openclaw` — L0，API Gateway
- `qwenpaw` — L0，Agent Engine
- `aika-heartbeat` — L1，節點心跳
- `aika-presence` — L1，節點註冊表
- `aika-queue` — L2，任務隊列
- `aika-scheduler` — L2，核心調度

## ❌ 禁止 Persistent（必須用 Cron）

| 服務 | 改為 Cron |
|------|----------|
| docs sync | `0 * * * *`（每小時）|
| github sync | `0 * * * *`（每小時）|
| report generation | `0 22 * * *`（每日）|
| cleanup task | `0 3 * * *`（每日凌晨）|
| metrics aggregation | `*/15 * * * *`（每15分鐘）|
| experimental runtime | 完全禁止 persistent |

---

## Resource Limits 標準

```ini
# 所有 systemd 服務必須包含
CPUQuota=50%        # L0 核心服務
CPUQuota=20%        # L1/L2 服務
MemoryMax=512M      # L0 核心服務
MemoryMax=256M      # L1/L2 服務
RestartSec=10       # 崩潰後等待10秒再重啟
StartLimitBurst=3   # 5分鐘內最多重啟3次
```

---

## Health Policy

```
CPU > 90% 持續 10分鐘 → 服務標記 DEGRADED
Memory > 90% 持續 10分鐘 → 服務標記 DEGRADED
DEGRADED → 發送告警郵件至 tao@goaa.ai
DEGRADED > 30分鐘 → 自動重啟服務
```

---

## Cleanup Policy（每日 cron）

```bash
# 每日 03:00 執行
journalctl --vacuum-time=7d          # 清理7天以上日誌
find /opt/goaa/logs -mtime +7 -delete # 清理舊日誌
find /tmp -name "goaa-*" -mtime +1 -delete # 清理臨時文件
find /opt/goaa/logs -name "metrics-*" -mtime +30 -delete # 清理舊指標
```

---

## 新 Runtime 審批問卷

新增任何 Runtime 服務前必須回答：

1. **為什麼需要 persistent？** 不能用 timer？
2. **CPU 消耗預估：** 正常 / 峰值
3. **Memory 消耗預估：** 正常 / 峰值
4. **如果 crash 恢復方案：** 自動重啟 / 人工介入
5. **是否可以合併到現有服務？**

---

*維護者：Claude（架構 PM）*
