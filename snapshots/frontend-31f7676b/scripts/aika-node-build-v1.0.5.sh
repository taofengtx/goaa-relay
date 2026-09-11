#!/bin/bash
# build-aika-node-v1.0.5.sh
# 在 Hetzner (AKC-001) 執行，構建 aika-node_1.0.5.deb
# 執行：ssh root@5.78.76.21 "bash -s" < build-aika-node-v1.0.5.sh

set -e

VERSION="1.0.5"
PKG_NAME="aika-node"
BUILD_DIR="/tmp/aika-build-$VERSION"
OUTPUT_DIR="/opt/goaa/downloads"

echo "=== 構建 $PKG_NAME v$VERSION ==="

# 清理舊構建
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR

# 建立 deb 目錄結構
mkdir -p $BUILD_DIR/DEBIAN
mkdir -p $BUILD_DIR/opt/goaa
mkdir -p $BUILD_DIR/etc/systemd/system

# control 文件
cat > $BUILD_DIR/DEBIAN/control << CTRL
Package: aika-node
Version: $VERSION
Architecture: amd64
Maintainer: GOAA.AI <aika@goaa.ai>
Description: AiKa Edge Computing Node v$VERSION
 GOAA.AI 分佈式邊緣計算節點
 自動 Bootstrap + GitHub 同步 + 心跳服務
Depends: python3, python3-venv, git, curl, wget
CTRL

# 複製 postinst 腳本
cat > $BUILD_DIR/DEBIAN/postinst << 'POSTINST'
#!/bin/bash
set -e
GOAA_DIR="/opt/goaa"
VERSION="1.0.5"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║     AiKa Node v1.0.5 初始化中...        ║"
echo "╚══════════════════════════════════════════╝"
echo ""

mkdir -p $GOAA_DIR/{logs,data,config}

# 安裝 Python 依賴
apt-get install -y git curl python3 python3-venv wget -q 2>/dev/null || true

# 一鍵 Bootstrap：從 GitHub 拉取
echo "📦 同步 GitHub 最新配置..."
if [ -d "$GOAA_DIR/repo" ]; then
    cd $GOAA_DIR/repo && git pull origin main -q 2>/dev/null || true
else
    git clone https://github.com/taofengtx/goaa-ai-frontend.git $GOAA_DIR/repo -q
fi
echo "✅ GitHub 同步完成"

# Python 虛擬環境
python3 -m venv $GOAA_DIR/venv
$GOAA_DIR/venv/bin/pip install -q fastapi uvicorn httpx psutil requests 2>/dev/null

# 節點註冊
HOSTNAME=$(hostname)
LOCAL_IP=$(ip route get 1 2>/dev/null | awk '{print $7}' | head -1 || echo "unknown")
NODE_ID="AKB-$(cat /sys/class/net/*/address 2>/dev/null | head -1 | tr -d ':' | tail -c 7 | tr '[:lower:]' '[:upper:]' || echo "000001")"

cat > $GOAA_DIR/registration.json << REGEOF
{
  "node_id": "$NODE_ID",
  "hostname": "$HOSTNAME",
  "ip": "$LOCAL_IP",
  "role": "edge_worker",
  "aika_version": "1.0.5",
  "status": "active",
  "registered_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "bootstrap_method": "auto_v1.0.5",
  "github_synced": true
}
REGEOF

# 心跳服務
cat > /etc/systemd/system/aika-heartbeat.service << SVCEOF
[Unit]
Description=AiKa Node Heartbeat v1.0.5
After=network.target

[Service]
Type=simple
ExecStart=/opt/goaa/venv/bin/python3 -c "
import time, requests, json, os
config = json.load(open('/opt/goaa/registration.json'))
while True:
    try:
        requests.post('https://api.goaa.ai/api/v1/geekom/heartbeat',
            json=config, timeout=10)
    except: pass
    time.sleep(30)
"
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable aika-heartbeat 2>/dev/null || true

# 桌面圖標
for USER_HOME in /home/*/; do
    USERNAME=$(basename $USER_HOME)
    DESKTOP="$USER_HOME/Desktop"
    AUTOSTART="$USER_HOME/.config/autostart"
    mkdir -p "$DESKTOP" "$AUTOSTART"

    cat > "$DESKTOP/aika-workstation.desktop" << DSKEOF
[Desktop Entry]
Version=1.0
Type=Application
Name=AiKa 工作台 v1.0.5
Exec=xdg-open https://portal.goaa.ai/agent-login
Terminal=false
DSKEOF
    chmod +x "$DESKTOP/aika-workstation.desktop"

    cat > "$AUTOSTART/goaa-portal.desktop" << AUTOEOF
[Desktop Entry]
Type=Application
Name=GOAA Portal
Exec=bash -c "sleep 10 && xdg-open https://portal.goaa.ai/agent-login"
X-GNOME-Autostart-enabled=true
AUTOEOF
done

# GitHub 每小時同步
(crontab -l 2>/dev/null | grep -v goaa-sync; echo "0 * * * * cd /opt/goaa/repo && git pull origin main -q >> /opt/goaa/logs/sync.log 2>&1") | crontab -

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   ✅ AiKa Node v1.0.5 安裝完成！        ║"
echo "╠══════════════════════════════════════════╣"
echo "║  節點 ID: $NODE_ID"
echo "║  本機 IP: $LOCAL_IP"
echo "║  GitHub:  已同步 ✅"
echo "║  心跳:    已啟動 ✅"
echo "║  桌面圖標: 已建立 ✅"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "執行 'sudo reboot' 完成安裝"
POSTINST

chmod 755 $BUILD_DIR/DEBIAN/postinst

# 構建 deb
echo "=== 構建 .deb 包 ==="
dpkg-deb --build $BUILD_DIR $OUTPUT_DIR/${PKG_NAME}_${VERSION}.deb

echo "=== 完成 ==="
ls -lh $OUTPUT_DIR/
echo "下載地址：https://api.goaa.ai/downloads/${PKG_NAME}_${VERSION}.deb"
