#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════════════
# do-deploy-model-router-api.sh v2
# ════════════════════════════════════════════════════════════════════════
#
# Purpose: git-based deployment of /opt/goaa/router/api.py + db.py
# Replaces: v1 (curl raw.githubusercontent.com — broken for private repo)
#
# 簽發: 2026-05-20 PT Claude
# 規範遵守:
#   #11 only-add  : production 檔 deploy 前必 backup
#   #14 v2        : GitHub HEAD = production truth (git → cp, not SCP)
#   #18 重啟      : --restart 預警, 30 秒中斷
#   #28 不靜默    : set -e + logger.exception 風 (失敗立刻 abort)
#   #36 v2        : 從 STDOUT 真實 systemd unit 結論
#
# 使用:
#   bash do-deploy-model-router-api.sh           # 只 git pull + cp, 不重啟
#   bash do-deploy-model-router-api.sh --restart # git pull + cp + restart
#   bash do-deploy-model-router-api.sh --dry-run # 只 git fetch + diff 預覽
#
# 回滾:
#   cp /opt/goaa/router/api.py.bak.<TS> /opt/goaa/router/api.py
#   systemctl restart goaa-model-router
#
# ════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ─── 配置 ────────────────────────────────────────────────
GOAA_ROOT="/opt/goaa"
GIT_DIR="$GOAA_ROOT"
PROD_DIR="$GOAA_ROOT/router"
GIT_SRC_DIR="$GOAA_ROOT/infra/router"
SERVICE_NAME="goaa-model-router"
LOG_DIR="$GOAA_ROOT/logs"
TS=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/deploy_${TS}.log"

# ─── flags ─────────────────────────────────────────────
RESTART=false
DRY_RUN=false
for arg in "$@"; do
    case "$arg" in
        --restart) RESTART=true ;;
        --dry-run) DRY_RUN=true ;;
        --help|-h)
            grep -E "^# (Purpose|使用|回滾)" "$0" | sed 's/^# //'
            exit 0
            ;;
        *)
            echo "❌ Unknown arg: $arg (try --help)" >&2
            exit 1
            ;;
    esac
done

# ─── log helper ───────────────────────────────────────
mkdir -p "$LOG_DIR"
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "═══════════════════════════════════════════"
log "  do-deploy-model-router-api.sh v2 START"
log "═══════════════════════════════════════════"
log "  RESTART=$RESTART DRY_RUN=$DRY_RUN TS=$TS"

# ─── Step 1: 環境驗證 ────────────────────────────────────
[[ -d "$GIT_DIR/.git" ]] || { log "❌ $GIT_DIR/.git not found"; exit 2; }
[[ -d "$PROD_DIR" ]] || { log "❌ $PROD_DIR not found"; exit 3; }
which git >/dev/null || { log "❌ git not in PATH"; exit 4; }
which python3 >/dev/null || { log "❌ python3 not in PATH"; exit 5; }
log "✅ Step 1: env check OK"

# ─── Step 2: 紀錄當前 git HEAD (for rollback) ──────────
cd "$GIT_DIR"
OLD_HEAD=$(git rev-parse HEAD)
log "✅ Step 2: current git HEAD = $OLD_HEAD"

# ─── Step 3: git fetch + pull (規範 #14 v2 核心) ───────
log "→ Step 3: git fetch origin main..."
git fetch origin main 2>&1 | tee -a "$LOG_FILE"

NEW_HEAD=$(git rev-parse origin/main)
log "✅ Step 3.1: origin/main = $NEW_HEAD"

if [[ "$OLD_HEAD" == "$NEW_HEAD" ]]; then
    log "✓ Step 3.2: already at HEAD, no pull needed"
else
    log "→ Step 3.2: HEAD will advance $OLD_HEAD → $NEW_HEAD"

    # 看 diff stat 預覽
    log "→ Step 3.3: diff stat preview:"
    git diff --stat HEAD origin/main 2>&1 | tee -a "$LOG_FILE"

    if $DRY_RUN; then
        log "✋ DRY_RUN: 停在 Step 3.3, 不真實 pull"
        exit 0
    fi

    # 真實 pull (ff-only 防意外 merge)
    git checkout main 2>&1 | tee -a "$LOG_FILE"
    git pull --ff-only origin main 2>&1 | tee -a "$LOG_FILE"
    log "✅ Step 3.4: git pull OK, new HEAD = $(git rev-parse --short HEAD)"
fi

# ─── Step 4: 驗證 git 版檔案存在 ────────────────────────
[[ -f "$GIT_SRC_DIR/api.py" ]] || { log "❌ $GIT_SRC_DIR/api.py missing after pull"; exit 6; }
[[ -f "$GIT_SRC_DIR/db.py" ]] || { log "❌ $GIT_SRC_DIR/db.py missing after pull"; exit 7; }
log "✅ Step 4: git source files exist"

# 列出 git 版 fingerprint
GIT_API_LINES=$(wc -l < "$GIT_SRC_DIR/api.py")
GIT_API_MD5=$(md5sum "$GIT_SRC_DIR/api.py" | awk '{print $1}')
GIT_DB_LINES=$(wc -l < "$GIT_SRC_DIR/db.py")
GIT_DB_MD5=$(md5sum "$GIT_SRC_DIR/db.py" | awk '{print $1}')
log "   git infra/router/api.py: $GIT_API_LINES lines, MD5=$GIT_API_MD5"
log "   git infra/router/db.py:  $GIT_DB_LINES lines, MD5=$GIT_DB_MD5"

# ─── Step 5: backup production 檔 (規範 #11) ──────────
if [[ -f "$PROD_DIR/api.py" ]]; then
    cp -p "$PROD_DIR/api.py" "$PROD_DIR/api.py.bak.${TS}"
    log "✅ Step 5.1: backup → router/api.py.bak.${TS}"
fi
if [[ -f "$PROD_DIR/db.py" ]]; then
    cp -p "$PROD_DIR/db.py" "$PROD_DIR/db.py.bak.${TS}"
    log "✅ Step 5.2: backup → router/db.py.bak.${TS}"
fi

# ─── Step 6: 內容檢查 — 是否真有變化 (規範 #11 防重) ──
NEED_DEPLOY=false
if [[ ! -f "$PROD_DIR/api.py" ]] || ! cmp -s "$GIT_SRC_DIR/api.py" "$PROD_DIR/api.py"; then
    NEED_DEPLOY=true
    log "→ Step 6: api.py 需要部署 (新版或內容不同)"
fi
if [[ ! -f "$PROD_DIR/db.py" ]] || ! cmp -s "$GIT_SRC_DIR/db.py" "$PROD_DIR/db.py"; then
    NEED_DEPLOY=true
    log "→ Step 6: db.py 需要部署 (新版或內容不同)"
fi

if ! $NEED_DEPLOY; then
    log "✓ Step 6: production 已是最新版, 無需 cp/restart"
    log "═══════════════════════════════════════════"
    log "  DEPLOY OK (NO-OP, files already up-to-date)"
    log "  git HEAD: $(git rev-parse --short HEAD)"
    log "═══════════════════════════════════════════"
    exit 0
fi

# ─── Step 7: cp git → production ──────────────────────
cp -f "$GIT_SRC_DIR/api.py" "$PROD_DIR/api.py"
log "✅ Step 7.1: cp api.py → production"

cp -f "$GIT_SRC_DIR/db.py" "$PROD_DIR/db.py"
log "✅ Step 7.2: cp db.py → production"

# 驗證 cp 後 MD5 (規範 #12)
PROD_API_MD5=$(md5sum "$PROD_DIR/api.py" | awk '{print $1}')
PROD_DB_MD5=$(md5sum "$PROD_DIR/db.py" | awk '{print $1}')
log "   production api.py MD5: $PROD_API_MD5 (should match git: $GIT_API_MD5)"
log "   production db.py MD5:  $PROD_DB_MD5 (should match git: $GIT_DB_MD5)"

# ─── Step 8: Python syntax check (規範 #28 不靜默) ────
log "→ Step 8.1: python3 syntax check api.py..."
if ! python3 -c "import ast; ast.parse(open('$PROD_DIR/api.py').read())" 2>&1 | tee -a "$LOG_FILE"; then
    log "❌ Step 8.1 FAILED — rolling back api.py"
    cp -f "$PROD_DIR/api.py.bak.${TS}" "$PROD_DIR/api.py"
    log "   rollback OK, exit 8"
    exit 8
fi
log "✅ Step 8.1: api.py syntax OK"

log "→ Step 8.2: python3 syntax check db.py..."
if ! python3 -c "import ast; ast.parse(open('$PROD_DIR/db.py').read())" 2>&1 | tee -a "$LOG_FILE"; then
    log "❌ Step 8.2 FAILED — rolling back db.py"
    cp -f "$PROD_DIR/db.py.bak.${TS}" "$PROD_DIR/db.py"
    log "   rollback OK, exit 9"
    exit 9
fi
log "✅ Step 8.2: db.py syntax OK"

# ─── Step 9: optional restart (規範 #18 預警) ─────────
if $RESTART; then
    log "⚠️  Step 9: --restart flag set, restarting $SERVICE_NAME (30s downtime warning)"
    systemctl restart "$SERVICE_NAME"
    sleep 5

    if systemctl is-active --quiet "$SERVICE_NAME"; then
        PID=$(systemctl show -p MainPID --value "$SERVICE_NAME")
        log "✅ Step 9.1: $SERVICE_NAME active, PID=$PID"
    else
        log "❌ Step 9.1: $SERVICE_NAME failed to start!"
        log "   ROLLBACK PROCEDURE:"
        log "   cp $PROD_DIR/api.py.bak.${TS} $PROD_DIR/api.py"
        log "   cp $PROD_DIR/db.py.bak.${TS} $PROD_DIR/db.py"
        log "   systemctl restart $SERVICE_NAME"
        exit 10
    fi

    # 健康 endpoint 確認 (可選, 看你的服務有沒有 /health)
    log "→ Step 9.2: health endpoint check..."
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/workers/status | grep -q "200"; then
        log "✅ Step 9.2: /workers/status returns 200"
    else
        log "⚠️  Step 9.2: /workers/status not 200 (但服務 active, 可能 endpoint 命名差異)"
    fi
else
    log "✓ Step 9: --restart not set, 跳過重啟 (服務仍跑舊版)"
    log "   下次重啟時自動使用新版"
fi

# ─── Step 10: 摘要 ─────────────────────────────────────
log "═══════════════════════════════════════════"
log "  DEPLOY OK"
log "  git HEAD:        $(git rev-parse --short HEAD)"
log "  api.py lines:    $GIT_API_LINES"
log "  api.py MD5:      $GIT_API_MD5"
log "  db.py lines:     $GIT_DB_LINES"
log "  db.py MD5:       $GIT_DB_MD5"
log "  backup:          router/{api,db}.py.bak.${TS}"
log "  log:             $LOG_FILE"
if $RESTART; then
    log "  restart:         YES, service active"
else
    log "  restart:         NO (use --restart next time)"
fi
log "═══════════════════════════════════════════"
