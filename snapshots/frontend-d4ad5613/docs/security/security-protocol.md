# GOAA.AI Security Protocol

**Last Updated:** 2026-05-09  
**Status:** Active  
**Trigger:** Hetzner AKC-001 brute-force attack (212.220.15.227)

---

## 1. 多協調機 SSH 信任協議

### 授權公鑰清單

所有以下節點的公鑰必須存在於 AKC-001 的 `/root/.ssh/authorized_keys`：

| 節點 | IP | 公鑰位置 |
|------|-----|---------|
| AiKa-1 (COORD-001) | 192.168.1.207 | `~/.ssh/id_ed25519.pub` |
| AiKa-2 (COORD-002) | 192.168.1.208 | `~/.ssh/id_ed25519.pub` |

### 公鑰分發腳本（在 AiKa-1 執行）

```bash
#!/bin/bash
# collect-and-push-keys.sh
# 執行節點：AiKa-1 (192.168.1.207)

HETZNER="root@5.78.76.21"
AIKA2="goaa@192.168.1.208"

echo "=== 收集公鑰 ==="

# AiKa-1 本地公鑰
KEY1=$(cat ~/.ssh/id_ed25519.pub)
echo "AiKa-1 公鑰已讀取"

# AiKa-2 公鑰
KEY2=$(ssh $AIKA2 "cat ~/.ssh/id_ed25519.pub")
echo "AiKa-2 公鑰已讀取"

echo "=== 推送到 Hetzner ==="
ssh $HETZNER "
mkdir -p /root/.ssh
echo '$KEY1' >> /root/.ssh/authorized_keys
echo '$KEY2' >> /root/.ssh/authorized_keys
sort -u /root/.ssh/authorized_keys -o /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys
echo '✅ authorized_keys 已更新'
cat /root/.ssh/authorized_keys | wc -l
echo '行數（每行一個公鑰）'
"
```

---

## 2. Fail2Ban 配置標準

```ini
# /etc/fail2ban/jail.local
[sshd]
enabled = true
port = ssh
maxretry = 3
bantime = 86400
findtime = 600
```

**已封禁 IP 記錄：**
- `212.220.15.227` — 2026-05-09 大規模暴力破解

---

## 3. 主機遭攻擊自動切換流程

```
AiKa-1 (192.168.1.207) 被封鎖或無法連接
    ↓ 心跳超時 > 60 秒
AiKa-2 (192.168.1.208) 自動檢測
    ↓
從 GitHub 拉取最新 node-registry.json
    ↓
AiKa-2 接管調度角色
    ↓
通過備用 SSH Key 連接 AKC-001
    ↓
發送告警郵件至 tao@goaa.ai
    ↓
等待 AiKa-1 恢復確認
```

### 切換觸發腳本（AiKa-2 上的 watchdog）

```bash
#!/bin/bash
# failover-watchdog.sh — 運行於 AiKa-2

PRIMARY="192.168.1.207"
CHECK_INTERVAL=30
FAIL_THRESHOLD=3
fail_count=0

while true; do
    if ! ping -c 1 -W 3 $PRIMARY > /dev/null 2>&1; then
        fail_count=$((fail_count + 1))
        echo "$(date): AiKa-1 無響應 ($fail_count/$FAIL_THRESHOLD)"
        
        if [ $fail_count -ge $FAIL_THRESHOLD ]; then
            echo "$(date): 觸發 Failover！AiKa-2 接管調度"
            cd /opt/goaa/repo && git pull origin main
            # 啟動備用調度服務
            systemctl start openclaw-backup 2>/dev/null || true
            # 發送告警
            curl -X POST https://api.goaa.ai/api/v1/notify/email \
                -H "Content-Type: application/json" \
                -d '{"subject":"⚠️ AiKa-1 Failover 觸發","content":"AiKa-2 已接管調度","to":"tao@goaa.ai"}'
            fail_count=0
        fi
    else
        fail_count=0
    fi
    sleep $CHECK_INTERVAL
done
```

---

## 4. 每日安全檢查清單

```bash
# 在 AKC-001 執行
fail2ban-client status sshd          # 查看封禁狀態
journalctl -u sshd --since "1 hour ago" | grep "Failed"  # 失敗嘗試
netstat -tuln | grep :22             # SSH 端口狀態
```

---

*維護者：Claude（工程）| 最後事件：2026-05-09 Hetzner 暴力破解攻擊*
