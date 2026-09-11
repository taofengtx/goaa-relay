#!/bin/bash
set -e
# AiKa Node v1.0.5 - full installer
# NEVER calls apt-get or dpkg - all system deps via Depends field
exec > >(tee -a /var/log/aika-install.log) 2>&1

VERSION="1.0.5"
GOAA_DIR="/opt/goaa"
ROUTER_API="http://134.199.227.108:8080"
LOG_FILE="/var/log/aika-install.log"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║     🦞  AiKa Box v$VERSION  安裝中                    ║"
echo "║     GOAA.AI 邊緣計算節點 — 拆箱即用                  ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"; }

USERNAME=$(ls /home | head -1 2>/dev/null || echo "tao")
log "系統: $(lsb_release -ds 2>/dev/null || echo unknown) | 用戶: $USERNAME"

# Step 1: already done in postinst
log "Step 1/8: 目錄結構已就緒 (postinst)"

# Step 2: Docker only (curl pipe, NOT apt)
log "Step 2/8: 安裝 Docker..."
if ! command -v docker &>/dev/null; then
    log "  → Docker 未安裝，通過 curl 安裝..."
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker $USERNAME 2>/dev/null || true
    log "  ✅ Docker 安裝完成"
else
    log "  ✅ Docker 已存在 ($(docker --version 2>/dev/null))"
fi
log "Step 2 完成"

# Step 3: Python venv + pip deps
log "Step 3/8: 配置 Python 環境..."
python3 -m venv $GOAA_DIR/venv
log "  ✅ venv 創建成功 ($($GOAA_DIR/venv/bin/python --version 2>/dev/null))"
$GOAA_DIR/venv/bin/pip install --upgrade pip
log "  ✅ pip 升級完成"
$GOAA_DIR/venv/bin/pip install fastapi uvicorn httpx requests psutil psycopg2-binary python-multipart pydantic
log "  ✅ Python 依賴安裝完成"
log "Step 3 完成"

# Step 4: Clone/pull GitHub runtime
log "Step 4/8: 同步 GOAA.AI 運行時代碼..."
if [ -d "$GOAA_DIR/repo/.git" ]; then
    cd $GOAA_DIR/repo && git pull origin main 2>&1 || true
else
    rm -rf $GOAA_DIR/repo
    git clone https://github.com/taofengtx/goaa-ai-frontend.git $GOAA_DIR/repo
fi
log "  ✅ repo 同步完成"
log "Step 4 完成"

# Step 5: Generate node identity
log "Step 5/8: 生成節點身份..."
HOSTNAME=$(hostname)
LOCAL_IP=$(ip route get 1 2>/dev/null | awk '{print $7}' | head -1 || echo unknown)
PRIMARY_IFACE=$(ip route get 1 2>/dev/null | awk '{print $5}' | head -1 || echo eth0)
MAC_ADDR=$(cat /sys/class/net/$PRIMARY_IFACE/address 2>/dev/null || echo 00:00:00:00:00:00)
MAC_SUFFIX=$(echo $MAC_ADDR | tr -d : | tail -c 8 | tr [:lower:] [:upper:])
NODE_ID="AKB-$MAC_SUFFIX"

cat > /tmp/gen-registration.py << 'PYEOF'
import json, os, platform, subprocess
NODE_ID = os.environ.get('NODE_ID', 'UNKNOWN')
HOSTNAME = os.environ.get('HOSTNAME', 'unknown')
LOCAL_IP = os.environ.get('LOCAL_IP', 'unknown')
MAC_ADDR = os.environ.get('MAC_ADDR', '00:00:00:00:00:00')
VERSION = os.environ.get('VERSION', '1.0.5')
ROUTER_API = os.environ.get('ROUTER_API', 'http://127.0.0.1:8080')

def get_ram_gb():
    try:
        with open('/proc/meminfo') as f:
            for line in f:
                if line.startswith('MemTotal:'):
                    return int(line.split()[1]) // (1024 * 1024)
    except: pass
    return 0

info = {
    'node_id': NODE_ID, 'hostname': HOSTNAME, 'ip': LOCAL_IP, 'mac': MAC_ADDR,
    'role': 'edge_worker', 'aika_version': VERSION, 'status': 'active',
    'registered_at': __import__('datetime').datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
    'bootstrap_method': 'deb_v1.0.5', 'github_synced': True,
    'capabilities': {
        'cpu_cores': os.cpu_count() or 0,
        'ram_gb': get_ram_gb(),
        'gpu': subprocess.run(['which','nvidia-smi'],capture_output=True).returncode == 0,
        'docker': True, 'python': True, 'ollama': False
    },
    'cloud_anchor': '134.199.227.108',
    'router_api': ROUTER_API,
    'tags': ['edge_worker', 'aika_box']
}
with open('/opt/goaa/registration.json', 'w') as f:
    json.dump(info, f, indent=2)
    f.write(chr(10))
print('Written: node_id=' + info['node_id'])
PYEOF

export NODE_ID HOSTNAME LOCAL_IP MAC_ADDR VERSION ROUTER_API
python3 /tmp/gen-registration.py
rm -f /tmp/gen-registration.py
log "  ✅ registration.json 已生成 (節點 ID: $NODE_ID)"
log "Step 5 完成"

# Step 6: Heartbeat systemd service
log "Step 6/8: 配置心跳服務..."
cat > $GOAA_DIR/heartbeat.py << 'HBEOF'
import sys, json, os, time, requests, psutil, platform, subprocess
NODE_ID = os.getenv('NODE_ID', 'unknown')
ROUTER = os.getenv('ROUTER_API', 'http://127.0.0.1:8080')
LOG_FILE = '/opt/goaa/logs/workers/heartbeat.log'
def log(m):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {m}'
    print(line)
    try:
        with open(LOG_FILE, 'a') as f: f.write(line + chr(10))
    except: pass
log(f'Heartbeat started - Node: {NODE_ID}')
while True:
    try:
        disk = '/mnt' if platform.system() == 'Windows' else '/'
        p = {
            'worker_id': NODE_ID,
            'cpu': psutil.cpu_percent(interval=2),
            'memory': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage(disk).percent,
            'docker': subprocess.run(['docker','ps'],capture_output=True,timeout=5).returncode == 0,
            'ollama': False
        }
        r = requests.post(f'{ROUTER}/worker/heartbeat', json=p, timeout=8)
        log(f'OK - CPU:{p["cpu"]}% MEM:{p["memory"]}% HTTP:{r.status_code}')
    except Exception as e:
        log(f'FAIL: {e}')
    time.sleep(30)
HBEOF
chmod +x $GOAA_DIR/heartbeat.py

cat > /etc/systemd/system/aika-heartbeat.service << SVCEOF
[Unit]
Description=AiKa Node Heartbeat v$VERSION
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=root
ExecStart=$GOAA_DIR/venv/bin/python3 $GOAA_DIR/heartbeat.py
Restart=always
RestartSec=30
Environment=NODE_ID=$NODE_ID
Environment=ROUTER_API=$ROUTER_API
CPUQuota=5%
MemoryMax=128M
[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable aika-heartbeat
systemctl start aika-heartbeat
log "  ✅ aika-heartbeat 服務已啟動 ($(systemctl is-active aika-heartbeat))"
log "Step 6 完成"

# Step 7: Desktop icon + autostart
log "Step 7/8: 配置桌面環境..."
for USER_DIR in /home/*/; do
    if [ -d "$USER_DIR" ]; then
        DESK="$USER_DIR/Desktop"
        AUTO="$USER_DIR/.config/autostart"
        mkdir -p "$DESK" "$AUTO"
        UNAME=$(basename $USER_DIR)
        cat > "$DESK/aika-workstation.desktop" << DSKEOF
[Desktop Entry]
Version=1.0
Type=Application
Name=AiKa 工作台 v$VERSION
Comment=GOAA.AI Edge Worker Node
Exec=xdg-open https://portal.goaa.ai/agent-login
Icon=$GOAA_DIR/assets/aika-icon.png
Terminal=false
DSKEOF
        chmod +x "$DESK/aika-workstation.desktop"
        log "  ✅ 桌面圖標: $DESK/aika-workstation.desktop"
        cat > "$AUTO/goaa-portal.desktop" << AUTOEOF
[Desktop Entry]
Type=Application
Name=GOAA Portal
Exec=bash -c "sleep 15 && xdg-open https://portal.goaa.ai/agent-login"
Hidden=false
X-GNOME-Autostart-enabled=true
AUTOEOF
        log "  ✅ 開機自啟: $AUTO/goaa-portal.desktop"
        chown -R $UNAME:$UNAME "$DESK" "$AUTO" 2>/dev/null || true
    fi
done
log "Step 7 完成"

# Step 8: Register to cloud
log "Step 8/8: 向 GOAA.AI 雲端註冊..."
sleep 2
PAYLOAD='{"worker_id":"'"$NODE_ID"'","cpu":0,"memory":0,"disk":0,"docker":true,"ollama":false}'
HTTP_CODE=$(curl -s -o /tmp/aika-register-resp.log -w "%{http_code}" \
    -X POST "$ROUTER_API/worker/heartbeat" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" --connect-timeout 10 2>&1)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
    log "  ✅ 雲端註冊成功 (HTTP $HTTP_CODE)"
else
    log "  ⚠️ 雲端註冊 HTTP $HTTP_CODE (心跳將重試)"
fi
log "Step 8 完成"

# Final verification
log "最終驗證..."
ERRORS=""
for item in /opt/goaa /opt/goaa/registration.json /opt/goaa/venv/bin/python /opt/goaa/repo/.git; do
    if [ -e "$item" ] || [ -d "$item" ]; then
        log "  ✅ $item"
    else
        log "  ❌ $item"
        ERRORS="$ERRORS $item"
    fi
done
if command -v docker &>/dev/null; then log "  ✅ Docker"; else log "  ❌ Docker"; fi
if systemctl is-active aika-heartbeat &>/dev/null; then log "  ✅ heartbeat"; else log "  ❌ heartbeat"; fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   ✅  AiKa Box v$VERSION 安裝完成！                   ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  節點 ID : $NODE_ID                                  ║"
echo "║  本機 IP : $LOCAL_IP                                  ║"
echo "║                                                      ║"
echo "║  💰 執行 sudo reboot 完成設置                         ║"
echo "║  重啟後自動打開 portal.goaa.ai                        ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

if [ -n "$ERRORS" ]; then
    log "⚠️  部分項目異常:$ERRORS"
else
    log "✅ 所有檢查通過！安裝成功。執行 sudo reboot 以完成設置。"
fi
