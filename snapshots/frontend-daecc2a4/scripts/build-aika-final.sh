#!/bin/bash
# build-aika-node-v1.0.5-final.sh
# 在 DO VPS (134.199.227.108) 構建最終版 aika-node_1.0.5.deb
# 執行：ssh root@134.199.227.108 "bash -s" < build-aika-node-v1.0.5-final.sh

set -e
VERSION="1.0.5"
PKG="aika-node"
BUILD="/tmp/aika-build-$VERSION"
OUTPUT="/opt/goaa/downloads"

echo "=== 構建 $PKG v$VERSION (final) ==="
rm -rf $BUILD
mkdir -p $BUILD/DEBIAN $BUILD/opt/goaa

# ── control ───────────────────────────────────────────────────
cat > $BUILD/DEBIAN/control << CTRL
Package: aika-node
Version: $VERSION
Architecture: amd64
Maintainer: GOAA.AI <aika@goaa.ai>
Installed-Size: 1024
Depends: python3, python3-venv, python3-pip, git, curl, wget, lsb-release
Description: AiKa Edge Worker Node v$VERSION
 GOAA.AI 邊緣計算節點 — 拆箱即用
 .
 安裝即自動完成：
  - 生成唯一節點 ID (基於 MAC 地址)
  - 配置 Python 運行環境
  - 安裝 Docker
  - 啟動心跳服務 (systemd)
  - GitHub 每小時自動同步
  - 桌面圖標 + 開機自動打開 portal.goaa.ai
  - 向 GOAA.AI 雲端自動注冊
CTRL

# ── postinst（從 GitHub 下載最新版本）────────────────────────
cat > $BUILD/DEBIAN/postinst << 'POSTINST'
#!/bin/bash
set -e
echo "=== AiKa Node 初始化中... ==="

# 下載最新 postinst 腳本並執行
if curl -fsSL https://raw.githubusercontent.com/taofengtx/goaa-ai-frontend/main/scripts/postinst-v1.0.5-final -o /tmp/aika-postinst.sh 2>/dev/null; then
    bash /tmp/aika-postinst.sh
    rm -f /tmp/aika-postinst.sh
else
    # 離線備用：基礎初始化
    mkdir -p /opt/goaa/{logs,data,config,runtime}
    python3 -m venv /opt/goaa/venv 2>/dev/null || true
    /opt/goaa/venv/bin/pip install -q requests psutil 2>/dev/null || true
    echo "⚠️ 離線安裝完成，部分功能需聯網後初始化"
fi
POSTINST
chmod 755 $BUILD/DEBIAN/postinst

# ── prerm（卸載時清理服務）────────────────────────────────────
cat > $BUILD/DEBIAN/prerm << 'PRERM'
#!/bin/bash
systemctl stop  aika-heartbeat 2>/dev/null || true
systemctl disable aika-heartbeat 2>/dev/null || true
PRERM
chmod 755 $BUILD/DEBIAN/prerm

# ── 構建 .deb ─────────────────────────────────────────────────
dpkg-deb --build $BUILD $OUTPUT/${PKG}_${VERSION}.deb

echo ""
echo "✅ 構建完成：$OUTPUT/${PKG}_${VERSION}.deb"
ls -lh $OUTPUT/${PKG}_${VERSION}.deb
echo "下載地址：https://api.goaa.ai/downloads/${PKG}_${VERSION}.deb"
echo "安裝命令："
echo "  wget https://api.goaa.ai/downloads/${PKG}_${VERSION}.deb"
echo "  sudo dpkg -i ${PKG}_${VERSION}.deb"
echo "  sudo reboot"
