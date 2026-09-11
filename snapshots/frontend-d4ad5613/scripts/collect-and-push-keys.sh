#!/bin/bash
# collect-and-push-keys.sh
# Task: SSH-20260509-001
# 執行節點：AiKa-1 (192.168.1.207)
# 用途：收集所有協調機公鑰並推送到 Hetzner

set -e

HETZNER="root@5.78.76.21"
AIKA2_USER="goaa"
AIKA2_IP="192.168.1.208"
LOG_FILE="/var/log/goaa-key-sync.log"

echo "=== SSH 信任鏈建立 $(date) ===" | tee -a $LOG_FILE

# 1. AiKa-1 本地公鑰
if [ ! -f ~/.ssh/id_ed25519.pub ]; then
    echo "生成 AiKa-1 SSH Key..."
    ssh-keygen -t ed25519 -C "aika-1@goaa.ai" -f ~/.ssh/id_ed25519 -N ""
fi
KEY1=$(cat ~/.ssh/id_ed25519.pub)
echo "✅ AiKa-1 公鑰已讀取" | tee -a $LOG_FILE

# 2. AiKa-2 公鑰
echo "讀取 AiKa-2 公鑰..."
KEY2=$(ssh -o ConnectTimeout=10 $AIKA2_USER@$AIKA2_IP "cat ~/.ssh/id_ed25519.pub" 2>/dev/null || echo "")
if [ -z "$KEY2" ]; then
    echo "⚠️ AiKa-2 公鑰讀取失敗，跳過" | tee -a $LOG_FILE
else
    echo "✅ AiKa-2 公鑰已讀取" | tee -a $LOG_FILE
fi

# 3. 推送到 Hetzner
echo "推送公鑰到 Hetzner AKC-001..." | tee -a $LOG_FILE
ssh $HETZNER << EOF
mkdir -p /root/.ssh
chmod 700 /root/.ssh

# 備份現有 authorized_keys
cp /root/.ssh/authorized_keys /root/.ssh/authorized_keys.bak.$(date +%Y%m%d) 2>/dev/null || true

# 追加新公鑰（去重）
echo "$KEY1" >> /root/.ssh/authorized_keys
echo "$KEY2" >> /root/.ssh/authorized_keys

# 去重並排序
sort -u /root/.ssh/authorized_keys -o /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys

echo "✅ authorized_keys 已更新"
echo "當前公鑰數量: \$(wc -l < /root/.ssh/authorized_keys)"
EOF

echo "=== 完成 $(date) ===" | tee -a $LOG_FILE
