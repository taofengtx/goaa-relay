# OpenClaw 調度器 API 規範
**版本：** v1.0.0  
**日期：** 2026-05-07  
**調度中心：** AiKa-1（192.168.1.207:18789）

---

## 一、系統概覽

```
Claude 發出指令
      ↓
AiKa-1（192.168.1.207）OpenClaw Scheduler
      ↓
 ┌────┴────┐
 ↓         ↓
雲盒節點  本地盒子節點
（免費）   （付報酬）
      ↓
結果回傳 + Credits 結算
```

---

## 二、節點註冊 API

### 2.1 節點首次註冊
```
POST /api/v1/nodes/register

請求：
{
  "node_id": "aika-local-001",       // 唯一節點ID
  "node_type": "local",              // local / cloud
  "hostname": "fq168-sm",
  "ip": "192.168.1.11",
  "capabilities": {
    "os": "Ubuntu 26.04",
    "cpu_cores": 4,
    "ram_gb": 16,
    "has_gpu": false,
    "can_ssh": true,
    "can_browser": true,
    "can_github": true,
    "can_python": true,
    "can_node": true,
    "can_docker": false,
    "can_ffmpeg": true,
    "roles": ["aika-dev", "aika-test", "aika-browser"]
  },
  "owner_user_id": "demo",           // 綁定的 goaa.ai 賬戶
  "aika_version": "1.0.4"
}

返回：
{
  "status": "registered",
  "node_token": "nt_xxx...",          // 後續請求用此 token
  "scheduler_url": "http://192.168.1.207:18789",
  "poll_interval_seconds": 30
}
```

### 2.2 節點能力更新
```
PUT /api/v1/nodes/{node_id}/capabilities

請求：更新的 capabilities 字段
返回：{"status": "updated"}
```

---

## 三、心跳 API

### 3.1 心跳上報（每 30 秒）
```
POST /api/v1/nodes/{node_id}/heartbeat

請求：
{
  "node_id": "aika-local-001",
  "timestamp": "2026-05-07T10:00:00Z",
  "status": "idle",                  // idle / busy / error
  "metrics": {
    "cpu_percent": 12.5,
    "ram_percent": 45.2,
    "disk_percent": 33.1,
    "current_task_id": null,
    "tasks_completed_today": 5,
    "online_seconds_today": 3600
  }
}

返回：
{
  "status": "ok",
  "pending_tasks": 0,                // 有任務時 > 0
  "server_time": "2026-05-07T10:00:01Z"
}
```

### 3.2 查看所有節點狀態
```
GET /api/v1/nodes

返回：
{
  "nodes": [
    {
      "node_id": "aika-local-001",
      "node_type": "local",
      "status": "idle",
      "last_seen": "2026-05-07T10:00:00Z",
      "online_days": 45,
      "capabilities": {...},
      "credits_earned_total": 2580
    }
  ],
  "total": 1,
  "online": 1,
  "idle": 1
}
```

---

## 四、任務分發 API

### 4.1 創建任務
```
POST /api/v1/tasks/dispatch

請求：
{
  "task_id": "GOAA-20260507-001",
  "title": "在 OpenClaw 加入節點心跳 API",
  "priority": "P0",
  "required_role": "aika-devops",
  "required_capabilities": ["can_ssh", "can_python"],
  "description": "...",
  "input_files": ["/opt/goaa/main.py"],
  "steps": ["1. 查看現有代碼", "2. 修改端點"],
  "acceptance": ["API 返回200", "重啟後數據保留"],
  "risk_level": "MEDIUM",
  "rollback": "cp main.py.bak main.py",
  "timeout_minutes": 120,
  "assign_to_node": null             // null=自動分配, 或指定 node_id
}

返回：
{
  "task_id": "GOAA-20260507-001",
  "status": "dispatched",
  "assigned_to": "aika-devops-01",
  "estimated_start": "2026-05-07T10:05:00Z"
}
```

### 4.2 節點主動拉取任務（輪詢）
```
GET /api/v1/tasks/pending?node_id=aika-local-001&role=aika-dev

返回：
{
  "tasks": [
    {
      "task_id": "GOAA-20260507-001",
      "title": "...",
      "steps": [...],
      "risk_level": "MEDIUM",
      "requires_approval": false
    }
  ]
}
```

### 4.3 任務狀態更新
```
PUT /api/v1/tasks/{task_id}/status

請求：
{
  "node_id": "aika-local-001",
  "status": "in_progress",           // pending/in_progress/completed/failed
  "progress_percent": 50,
  "log": "Step 2 完成，開始 Step 3"
}
```

### 4.4 任務完成上報 + 觸發報酬結算
```
POST /api/v1/tasks/{task_id}/complete

請求：
{
  "node_id": "aika-local-001",
  "node_type": "local",
  "status": "success",               // success / failed / partial
  "quality_score": 0.95,             // 0-1，由驗收標準自動評分
  "cpu_seconds": 120,
  "output_summary": "已完成所有步驟，API 測試通過",
  "output_files": ["/opt/goaa/main.py"],
  "test_results": {
    "passed": 5,
    "failed": 0,
    "coverage": "89%"
  }
}

返回：
{
  "task_id": "GOAA-20260507-001",
  "status": "completed",
  "credits_earned": 108,             // 僅 local 節點
  "credits_total": 2580,
  "next_task": null
}
```

---

## 五、報酬結算 API

### 5.1 查詢 Credits 明細
```
GET /api/v1/credits/{user_id}/history

返回：
{
  "user_id": "demo",
  "total_credits": 2580,
  "history": [
    {
      "date": "2026-05-07",
      "task_id": "GOAA-20260507-001",
      "task_type": "devops",
      "credits": 108,
      "formula": "25 × 1.5 × 1.2 × 1.2 = 108",
      "node_id": "aika-local-001"
    }
  ]
}
```

### 5.2 月費抵扣
```
POST /api/v1/credits/redeem

請求：
{
  "user_id": "demo",
  "type": "monthly_fee",
  "amount": 3990
}

返回：
{
  "status": "success",
  "credits_used": 3990,
  "credits_remaining": 0,
  "next_renewal": "2026-06-07",
  "receipt_id": "RCP-001"
}
```

---

## 六、節點安全機制

```
所有節點 API 請求必須帶：
Header: X-Node-Token: nt_xxx...

HIGH/CRITICAL 任務額外要求：
Header: X-Approval-Token: apr_xxx...  （由 Tao 師兄批准後生成）
```

### 6.1 申請審批 token
```
POST /api/v1/approval/request

請求：
{
  "task_id": "GOAA-20260507-002",
  "risk_level": "HIGH",
  "reason": "修改生產數據庫結構"
}

返回：
{
  "approval_id": "apr_xxx",
  "status": "pending",
  "notify": "tao@goaa.ai"
}
```

---

## 七、GitHub Actions 整合

任務完成後自動觸發 CI/CD：

```yaml
# .github/workflows/aika-task-complete.yml
on:
  repository_dispatch:
    types: [aika-task-complete]

jobs:
  test-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Run Tests
        run: |
          python -m pytest tests/
          npm run type-check
          npm run build
      - name: Deploy to Production
        if: success()
        run: |
          vercel --prod --yes
```

---

## 八、第一階段實施清單

以下 API 按順序在 Hetzner OpenClaw 實現：

- [ ] `POST /api/v1/nodes/register`
- [ ] `POST /api/v1/nodes/{id}/heartbeat`
- [ ] `GET /api/v1/nodes`
- [ ] `POST /api/v1/tasks/dispatch`
- [ ] `GET /api/v1/tasks/pending`
- [ ] `POST /api/v1/tasks/{id}/complete`
- [ ] `GET /api/v1/credits/{user_id}/history`
- [ ] `POST /api/v1/credits/redeem`

---

*文檔維護：Claude | AiKa-1 調度中心 IP：192.168.1.207*
