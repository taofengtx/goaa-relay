# DO-RUNTIME-ARCHITECTURE-20260510
## DigitalOcean Runtime Anchor - 完整架构与实现路线图

**时间：** 2026-05-10 07:00 UTC  
**目标：** 将 DO VPS (134.199.227.108) 转变为 GOAA 主 Runtime Anchor  
**状态：** DO Runtime Stack 验证成功 ✅

---

## 📊 **现有状态**

```
✅ Port 18789 正常运行
✅ Docker Compose 正常
✅ goaa-openclaw 容器已启动
✅ goaa-heartbeat 容器已启动
✅ Runtime Stack 真正运行中
```

---

## 🎯 **10 个核心任务**

### **Task 1: 将 nginx 替换为真正 FastAPI runtime**

**当前问题：** Port 18789 返回 nginx HTML  
**目标：** 替换为 FastAPI 应用

**实现步骤：**
1. 更新 docker-compose.yml
2. 确保 main.py 被正确挂载
3. 启动 FastAPI 应用（而不是 nginx）
4. 验证 API 响应

---

### **Task 2: 建立 `/health` 端点**

**API 规范：**

```
GET /health
Content-Type: application/json

Response 200:
{
  "status": "ok",
  "node": "AKC-DO-001",
  "timestamp": "2026-05-10T07:00:00Z",
  "uptime_seconds": 3600,
  "runtime_version": "1.0.0",
  "services": {
    "openclaw": "healthy",
    "heartbeat": "active"
  }
}
```

---

### **Task 3: 建立 `/heartbeat` 端点**

**API 规范：**

```
POST /heartbeat
Content-Type: application/json

Request:
{
  "node_id": "AKC-DO-001",
  "timestamp": "2026-05-10T07:00:00Z",
  "load": 0.45,
  "memory_usage_percent": 32.5
}

Response 200:
{
  "received": true,
  "node_id": "AKC-DO-001",
  "next_heartbeat_interval": 30
}
```

---

### **Task 4: 建立 worker registration API**

**API 规范：**

```
POST /api/v1/node/register
Content-Type: application/json

Request:
{
  "node_id": "AKC-DO-001",
  "hostname": "goaa-do-cloud",
  "role": "cloud_worker",
  "capabilities": ["python", "docker", "linux", "git"],
  "ip": "134.199.227.108"
}

Response 200:
{
  "registered": true,
  "node_id": "AKC-DO-001",
  "status": "active",
  "coordinator_ip": "192.168.1.207"
}
```

---

### **Task 5: 接入 OpenClaw Runtime**

**目标：** DO 节点能够接收和执行 OpenClaw 任务

**实现步骤：**
1. 在 FastAPI 中集成 OpenClaw client
2. 实现任务队列接收
3. 实现任务执行管理
4. 实现结果上报

---

### **Task 6: 接入 QwenPaw orchestration**

**目标：** DO 节点能够响应 QwenPaw 的编排请求

**实现步骤：**
1. 实现 QwenPaw agent 接口
2. 支持动态任务分发
3. 支持资源限制管理

---

### **Task 7: 建立真正 task pull system**

**API 规范：**

```
GET /api/v1/task/pull
Query Params:
  - node_id: AKC-DO-001
  - max_tasks: 5

Response 200:
{
  "tasks": [
    {
      "task_id": "TASK-001",
      "type": "python_execution",
      "payload": {...},
      "timeout": 300
    }
  ],
  "node_id": "AKC-DO-001"
}
```

---

### **Task 8: 接入 Cloudflare Tunnel**

**目标：** 通过 Cloudflare Tunnel 暴露内部 API

**实现步骤：**
1. 在 DO 上安装 cloudflared
2. 配置 tunnel 指向 localhost:18789
3. 验证通过 CF domain 访问

---

### **Task 9: 自动 git push runtime state**

**目标：** 容器启动时自动同步状态到 GitHub

**实现步骤：**
1. 在容器内初始化 git
2. 在启动时检出 main 分支
3. 更新 registration.json
4. 自动 commit + push

---

### **Task 10: 建立 persistent deployment architecture**

**目标：** systemd service 管理 Docker Compose stack

**实现步骤：**
1. 创建 /etc/systemd/system/goaa-runtime.service
2. 配置开机自启
3. 配置日志收集
4. 配置监控和告警

---

## 📈 **架构演进图**

```
Phase 1: nginx placeholder (现状)
  └─ Port 18789 → nginx HTML

Phase 2: FastAPI runtime (Task 1-3)
  └─ Port 18789 → /health, /heartbeat, /api/v1/node/...

Phase 3: OpenClaw integration (Task 5)
  └─ Port 18789 → Task execution, Result upload

Phase 4: QwenPaw orchestration (Task 6)
  └─ Port 18789 → Agent dispatch, Dynamic task routing

Phase 5: Task pull system (Task 7)
  └─ Port 18789 → Active task pulling, Queue management

Phase 6: Cloudflare Tunnel (Task 8)
  └─ cloudflared → api.goaa.ai/nodes/do-001/*

Phase 7: Git persistence (Task 9)
  └─ Docker init → git pull → register → git push

Phase 8: systemd persistent (Task 10)
  └─ /etc/systemd/system/goaa-runtime.service
```

---

## 🔗 **相关文件**

- Scripts: `scripts/do-deploy-phase1.sh`, `scripts/do-deploy-phase2.sh`
- Config: `docs/node-registry/node-registry.json`
- Architecture: This file

---

## 📋 **下一步**

1. ✅ 确认架构设计
2. ⏳ 更新 docker-compose.yml 
3. ⏳ 更新 main.py（FastAPI endpoints）
4. ⏳ 更新部署脚本
5. ⏳ 测试验证
6. ⏳ 推送到 GitHub

