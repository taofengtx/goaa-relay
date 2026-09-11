#!/bin/bash
set -e
LOG="/var/log/goaa-setup.log"
exec > >(tee -a $LOG) 2>&1

echo "=== goaa.ai AiKa Desktop 節點部署 $(date) ==="

# 1. 創建工作目錄
mkdir -p /opt/goaa
cd /opt/goaa

# 2. Python 虛擬環境
python3 -m venv venv
source venv/bin/activate

# 3. 安裝依賴
pip install --upgrade pip
pip install fastapi uvicorn httpx pydantic websockets python-multipart qwenpaw playwright psutil requests

# 4. Playwright 瀏覽器
python -m playwright install chromium

# 5. 安裝 Cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o /tmp/cloudflared.deb
dpkg -i /tmp/cloudflared.deb

# 6. 創建 OpenClaw systemd 服務
cat > /etc/systemd/system/openclaw.service << 'EOF'
[Unit]
Description=goaa.ai OpenClaw API Gateway
After=network.target

[Service]
Type=simple
User=goaa
WorkingDirectory=/opt/goaa
ExecStart=/opt/goaa/venv/bin/uvicorn main:app --host 0.0.0.0 --port 18789
Restart=always
RestartSec=5
Environment=HOME=/home/goaa

[Install]
WantedBy=multi-user.target
EOF

# 7. 創建 QwenPaw systemd 服務
cat > /etc/systemd/system/qwenpaw.service << 'EOF'
[Unit]
Description=goaa.ai QwenPaw Agent Engine
After=network.target

[Service]
Type=simple
User=goaa
WorkingDirectory=/opt/goaa
ExecStart=/opt/goaa/venv/bin/python -m qwenpaw app --host 127.0.0.1 --port 8088
Restart=always
RestartSec=10
Environment=HOME=/home/goaa

[Install]
WantedBy=multi-user.target
EOF

# 8. Kiosk 模式（桌面版自動登入並全屏打開 goaa.ai）
mkdir -p /home/goaa/.config/autostart
cat > /home/goaa/.config/autostart/goaa-kiosk.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=goaa.ai Kiosk
Exec=bash -c 'sleep 15 && chromium-browser --kiosk --no-sandbox --disable-infobars --noerrdialogs --disable-session-crashed-bubble https://portal.goaa.ai/agent-login'
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

chown -R goaa:goaa /home/goaa/.config

# 9. 設置自動登入
cat >> /etc/gdm3/custom.conf << 'EOF'

[daemon]
AutomaticLoginEnable=true
AutomaticLogin=goaa
EOF

# 10. 心跳腳本
cat > /opt/goaa/heartbeat.py << 'PYEOF'
import requests, time, socket, psutil

GOAA_API = "https://api.goaa.ai"
DEVICE_ID = socket.gethostname()

while True:
    try:
        requests.post(f"{GOAA_API}/api/v1/AiKa/heartbeat",
            json={
                "device_id": DEVICE_ID,
                "info": {
                    "ip": socket.gethostbyname(socket.gethostname()),
                    "cpu": psutil.cpu_percent(interval=1),
                    "memory": psutil.virtual_memory().percent,
                    "disk": psutil.disk_usage('/').percent,
                }
            }, timeout=5)
    except:
        pass
    time.sleep(30)
PYEOF

# 11. 心跳 systemd 服務
cat > /etc/systemd/system/goaa-heartbeat.service << 'EOF'
[Unit]
Description=goaa.ai AiKa Heartbeat
After=network.target

[Service]
Type=simple
User=goaa
ExecStart=/opt/goaa/venv/bin/python /opt/goaa/heartbeat.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

# 12. 啟用所有服務
systemctl daemon-reload
systemctl enable openclaw qwenpaw goaa-heartbeat

echo "=== 部署完成 $(date) ==="
echo "重啟後將自動登入並打開 goaa.ai"
