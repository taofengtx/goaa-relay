#!/bin/bash
# AiKa Node v1.0.5 - postinst
# 安裝後自動執行：Bootstrap + 服務啟動 + GitHub 同步

set -e

GOAA_DIR="/opt/goaa"
VERSION="1.0.5"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║     AiKa Node v$VERSION 安裝完成           ║"
echo "║     GOAA.AI 邊緣計算節點                  ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# 1. 建立目錄結構
mkdir -p $GOAA_DIR/{logs,data,config,downloads}

# 2. 一鍵 Bootstrap：從 GitHub 拉取最新 Master Protocol
echo "📦 正在從 GitHub 同步最新配置..."
if command -v git &> /dev/null; then
    if [ -d "$GOAA_DIR/repo" ]; then
        cd $GOAA_DIR/repo && git pull origin main -q
    else
        git clone https://github.com/taofengtx/goaa-ai-frontend.git $GOAA_DIR/repo -q
    fi
    echo "✅ GitHub 同步完成"
else
    apt-get install -y git -q
    git clone https://github.com/taofengtx/goaa-ai-frontend.git $GOAA_DIR/repo -q
fi

# 3. 執行 Bootstrap 腳本
if [ -f "$GOAA_DIR/repo/scripts/aika2-bootstrap.sh" ]; then
    echo "🚀 正在執行節點 Bootstrap..."
    bash $GOAA_DIR/repo/scripts/aika2-bootstrap.sh
else
    echo "⚠️ Bootstrap 腳本未找到，執行基礎初始化..."
    # 基礎初始化
    apt-get update -q
    apt-get install -y python3 python3-venv python3-pip curl wget -q
    python3 -m venv $GOAA_DIR/venv
    $GOAA_DIR/venv/bin/pip install -q fastapi uvicorn httpx psutil requests
fi

# 4. 建立節點註冊文件
HOSTNAME=$(hostname)
LOCAL_IP=$(ip route get 1 | awk '{print $7}' | head -1)
NODE_ID="AKB-$(cat /sys/class/net/*/address | head -1 | tr -d ':' | tail -c 7 | tr '[:lower:]' '[:upper:]')"

cat > $GOAA_DIR/registration.json << REGEOF
{
  "node_id": "$NODE_ID",
  "hostname": "$HOSTNAME",
  "ip": "$LOCAL_IP",
  "role": "edge_worker",
  "aika_version": "$VERSION",
  "status": "active",
  "registered_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "capabilities": {
    "cpu_cores": $(nproc),
    "memory_gb": $(free -g | awk '/^Mem:/{print $2}'),
    "docker": $(command -v docker &>/dev/null && echo "true" || echo "false"),
    "gpu": false
  },
  "bootstrap_method": "auto_v1.0.5",
  "github_synced": true
}
REGEOF

echo "✅ 節點 ID：$NODE_ID"
echo "✅ 本機 IP：$LOCAL_IP"

# 5. 設置心跳服務
cat > /etc/systemd/system/aika-heartbeat.service << 'SVCEOF'
[Unit]
Description=AiKa Node Heartbeat
After=network.target

[Service]
Type=simple
ExecStart=/opt/goaa/venv/bin/python3 /opt/goaa/repo/scripts/heartbeat.py
Restart=always
RestartSec=30
Environment=GOAA_API=https://api.goaa.ai
Environment=NODE_CONFIG=/opt/goaa/registration.json

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable aika-heartbeat 2>/dev/null || true
systemctl start aika-heartbeat 2>/dev/null || true

# 6. 設置桌面圖標
DESKTOP_FILE="/home/$(ls /home | head -1)/Desktop/aika-workstation.desktop"
mkdir -p "$(dirname $DESKTOP_FILE)"
cat > "$DESKTOP_FILE" << 'DSKEOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=AiKa 工作台
Comment=GOAA.AI 邊緣計算節點
Exec=xdg-open https://portal.goaa.ai/agent-login
Icon=/opt/goaa/repo/assets/aika-icon.png
Terminal=false
StartupNotify=false
DSKEOF
chmod +x "$DESKTOP_FILE" 2>/dev/null || true

# 7. 設置開機自動打開登入頁
AUTOSTART_DIR="/home/$(ls /home | head -1)/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
cat > "$AUTOSTART_DIR/goaa-portal.desktop" << 'AUTOEOF'
[Desktop Entry]
Type=Application
Name=GOAA Portal
Exec=bash -c "sleep 10 && xdg-open https://portal.goaa.ai/agent-login"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
AUTOEOF

# 8. 設置 GitHub 每小時自動同步
(crontab -l 2>/dev/null; echo "0 * * * * cd /opt/goaa/repo && git pull origin main -q >> /opt/goaa/logs/sync.log 2>&1") | crontab -

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║     ✅ AiKa Node v$VERSION 初始化完成     ║"
echo "╠══════════════════════════════════════════╣"
echo "║  節點 ID: $NODE_ID"
echo "║  本機 IP: $LOCAL_IP"
echo "║  GitHub:  已同步 ✅"
echo "║  心跳:    已啟動 ✅"
echo "║  桌面圖標: 已建立 ✅"
echo "║"
echo "║  重啟後自動打開 portal.goaa.ai"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "請執行 'sudo reboot' 完成安裝"
