#!/bin/bash
# build-aika-v1.0.5-fixed.sh
# 在 DO VPS 執行
# 修復：所有系統依賴移入 control Depends，postinst 零 apt 調用

set -e
VERSION="1.0.5"
PKG="aika-node"
BUILD="/tmp/aika-build-fixed"
OUTPUT="/opt/goaa/downloads"

echo "=== 構建 $PKG v$VERSION (fixed) ==="
rm -rf "$BUILD"
mkdir -p "$BUILD/DEBIAN"

# ── DEBIAN/control（依賴完整聲明）────────────────────────────
cat > "$BUILD/DEBIAN/control" << 'CTRL'
Package: aika-node
Version: 1.0.5
Architecture: amd64
Maintainer: GOAA.AI <aika@goaa.ai>
Installed-Size: 512
Depends: python3 (>= 3.10), python3-venv, python3-pip, git, curl, wget, ca-certificates, net-tools
Recommends: docker.io
Description: AiKa Edge Worker Node v1.0.5
 GOAA.AI 邊緣計算節點，拆箱即用。
 .
 安裝方式（唯一推薦）：
   sudo apt install -y ./aika-node_1.0.5.deb
   sudo reboot
CTRL

# ── DEBIAN/postinst（從 GitHub 拉取，零 apt 調用）─────────
cat > "$BUILD/DEBIAN/postinst" << 'POSTINST'
#!/bin/bash
set -e
SCRIPT_URL="https://raw.githubusercontent.com/taofengtx/goaa-ai-frontend/main/scripts/postinst-v1.0.5-fixed"
if curl -fsSL "$SCRIPT_URL" -o /tmp/aika-init.sh 2>/dev/null; then
    bash /tmp/aika-init.sh
    rm -f /tmp/aika-init.sh
else
    # 離線備用
    mkdir -p /opt/goaa/{logs,data,runtime}
    python3 -m venv /opt/goaa/venv 2>/dev/null || true
    echo "⚠️ 離線安裝，聯網後心跳服務將自動同步"
fi
POSTINST
chmod 755 "$BUILD/DEBIAN/postinst"

# ── DEBIAN/prerm ──────────────────────────────────────────────
cat > "$BUILD/DEBIAN/prerm" << 'PRERM'
#!/bin/bash
systemctl stop    aika-heartbeat 2>/dev/null || true
systemctl disable aika-heartbeat 2>/dev/null || true
PRERM
chmod 755 "$BUILD/DEBIAN/prerm"

# ── 構建 ──────────────────────────────────────────────────────
dpkg-deb --build "$BUILD" "$OUTPUT/${PKG}_${VERSION}.deb"

echo ""
echo "✅ 構建完成"
dpkg-deb --info "$OUTPUT/${PKG}_${VERSION}.deb" | grep -E "Package|Version|Depends"
ls -lh "$OUTPUT/${PKG}_${VERSION}.deb"
echo ""
echo "正確安裝方式："
echo "  wget https://api.goaa.ai/downloads/${PKG}_${VERSION}.deb"
echo "  sudo apt install -y ./${PKG}_${VERSION}.deb"
echo "  sudo reboot"
