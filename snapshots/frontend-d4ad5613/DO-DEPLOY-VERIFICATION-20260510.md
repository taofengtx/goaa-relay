# DO-DEPLOY-VERIFICATION-20260510
## DigitalOcean Runtime Stack 部署验证指南

**时间：** 2026-05-10 06:55 UTC  
**目标：** 在 DigitalOcean (134.199.227.108) 上验证 GOAA Runtime Stack 部署  
**执行节点：** AiKa-2 (192.168.1.208)

---

## 🚀 **Phase 1：一键部署验证**

在 AiKa-2 终端执行以下命令：

```bash
# 直接从 GitHub 运行修复后的脚本
bash <(curl -s https://raw.githubusercontent.com/taofengtx/goaa-ai-frontend/main/scripts/do-deploy-phase1.sh)
```

### 预期输出：

```
=== Phase 1: GOAA Runtime Stack Deployment ===

[1/7] Creating FastAPI main.py...
✅ main.py created

[2/7] Creating heartbeat.py...
✅ heartbeat.py created

[3/7] Creating docker-compose.yml...
✅ docker-compose.yml created

[4/7] Creating registration.json...
✅ registration.json created

[5/7] Checking Docker...
Docker version 24.x.x, build xxxx
✅ Docker is installed

[6/7] Starting Docker Compose stack...
✅ Stack started

[7/7] Verifying...
NAMES               STATUS                    PORTS
goaa-openclaw      Up X seconds              0.0.0.0:18789->18789/tcp
goaa-heartbeat     Up X seconds

{"status":"ok","node":"AKC-DO-001","time":"2026-05-10T06:55:00Z"}

=== Phase 1 Complete ===
```

---

## ✅ **验证步骤**

### **Step 1：检查 OpenClaw API 健康状态**

```bash
curl http://134.199.227.108:18789/health
```

**预期返回：**

```json
{
  "status": "ok",
  "node": "AKC-DO-001",
  "time": "2026-05-10T06:55:00Z"
}
```

### **Step 2：检查节点信息**

```bash
curl http://134.199.227.108:18789/api/v1/node/info
```

**预期返回：**

```json
{
  "node_id": "AKC-DO-001",
  "ip": "134.199.227.108",
  "role": "cloud_worker",
  "capabilities": ["python", "docker", "linux"],
  "status": "active"
}
```

### **Step 3：检查 Docker 容器状态**

```bash
ssh root@134.199.227.108 "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
```

**预期返回：**

```
NAMES               STATUS                    PORTS
goaa-openclaw      Up X minutes              0.0.0.0:18789->18789/tcp
goaa-heartbeat     Up X minutes
```

### **Step 4：检查心跳日志**

```bash
ssh root@134.199.227.108 "docker logs goaa-heartbeat --tail 5"
```

**预期返回：**

```
Heartbeat sent: AKC-DO-001
Heartbeat sent: AKC-DO-001
...
```

---

## 📊 **完整验证检查清单**

- [ ] Phase 1 脚本执行完成（所有 7 步 ✅）
- [ ] Docker 容器正常运行（2 个容器 UP）
- [ ] OpenClaw API 响应 /health（HTTP 200）
- [ ] 返回正确的节点信息（node_id: AKC-DO-001）
- [ ] 心跳服务运行中（logs 显示发送记录）
- [ ] 注册文件已创建（/opt/goaa/runtime/registration.json）

---

## 🔗 **相关文件**

**GitHub Commit:**
- Phase 1 脚本: `01a72d7` - do-deploy-phase1.sh (修复版本)
- 节点注册: `c8ef98f` - node-registry.json 已更新

**脚本位置：**
https://raw.githubusercontent.com/taofengtx/goaa-ai-frontend/main/scripts/do-deploy-phase1.sh

---

## 🎯 **验证成功标准**

✅ 任务完成条件：
1. Phase 1 脚本在 DigitalOcean 上成功执行
2. 两个 Docker 容器（openclaw, heartbeat）正常运行
3. curl http://134.199.227.108:18789/health 返回 200 + JSON 数据
4. 节点已在 GitHub node-registry 中注册（AKC-DO-001）

---

**Tao 师兄 - 请在 AiKa-2 上执行上述命令，然后回报：**
1. Phase 1 脚本的完整输出
2. /health 端点的返回内容
3. docker ps 的容器列表

