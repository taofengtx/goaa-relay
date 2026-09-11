#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════════════
# check_do_git_consistency.sh — 規範 #47 DO ↔ git 一致性監控
# ════════════════════════════════════════════════════════════════════════
#
# Purpose: 每日比對 production /opt/goaa/router/{api,db}.py 跟 git infra/router/
#          + git HEAD vs origin/main 是否落後
#          不一致 → 寄信給 EMAIL_TO + log
#
# 簽發: 2026-05-20 PT Claude
# 規範遵守:
#   #11 only-add  : 純讀取 + log append, 不改 production
#   #14 v2        : 監控 git HEAD = production truth 是否仍對齊
#   #22           : SMTP 配置從 /etc/goaa/secrets.env source, 不硬編碼
#   #28 不靜默    : set -e + 任何錯誤都 log
#   #36 v2        : Runtime Truth 真實 MD5 比對
#   #47           : DO ↔ git 一致性監控的核心實作
#
# 使用:
#   bash check_do_git_consistency.sh            # 正常監控
#   bash check_do_git_consistency.sh --force-alert  # 測試用, 強制寄警報
#   bash check_do_git_consistency.sh --dry-run  # 只比對不寄信
#
# crontab:
#   0 7 * * * /opt/goaa/scripts/check_do_git_consistency.sh
#   (UTC 07:00 = PT 00:00, 每日 1 次, 規範 #47 條款 1)
#
# 回滾:
#   crontab -l | grep -v check_do_git_consistency | crontab -
#
# ════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ─── 配置 ────────────────────────────────────────────────
GOAA_ROOT="/opt/goaa"
PROD_DIR="$GOAA_ROOT/router"
GIT_SRC_DIR="$GOAA_ROOT/infra/router"
LOG_DIR="$GOAA_ROOT/logs"
LOG_FILE="$LOG_DIR/consistency_check.log"
ALERT_SCRIPT="$GOAA_ROOT/scripts/send_consistency_alert.py"
PYTHON_BIN="/opt/goaa/venv/bin/python3"
TS=$(date '+%Y-%m-%d %H:%M:%S UTC')

# ─── flags ───────────────────────────────────────────
FORCE_ALERT=false
DRY_RUN=false
for arg in "$@"; do
    case "$arg" in
        --force-alert) FORCE_ALERT=true ;;
        --dry-run) DRY_RUN=true ;;
        --help|-h)
            grep -E "^# (Purpose|使用|crontab)" "$0" | sed 's/^# //'
            exit 0
            ;;
    esac
done

# ─── log helper ─────────────────────────────────────
mkdir -p "$LOG_DIR"
log() {
    echo "[$TS] $*" | tee -a "$LOG_FILE"
}

log "═══ check_do_git_consistency START (DRY_RUN=$DRY_RUN FORCE=$FORCE_ALERT) ═══"

# ─── Step 1: 環境驗證 ────────────────────────────────────
if [[ ! -d "$GOAA_ROOT/.git" ]]; then
    log "❌ FATAL: $GOAA_ROOT/.git not found"
    exit 2
fi
if [[ ! -x "$PYTHON_BIN" ]]; then
    log "⚠️  WARN: $PYTHON_BIN not executable, alerts may fail"
fi

cd "$GOAA_ROOT"

# ─── Step 2: git fetch (純讀取, 不 pull) ─────────────
log "→ Step 2: git fetch origin main..."
if git fetch origin main 2>&1 | tee -a "$LOG_FILE"; then
    log "✓ Step 2: fetch OK"
else
    log "❌ FATAL: git fetch failed"
    exit 3
fi

# ─── Step 3: 收集 alerts ───────────────────────────
ALERTS=()

# 3.1 比對 production vs git infra/
for f in api.py db.py; do
    PROD_FILE="$PROD_DIR/$f"
    GIT_FILE="$GIT_SRC_DIR/$f"

    if [[ ! -f "$PROD_FILE" ]]; then
        ALERTS+=("MISSING_PROD|$f|production missing")
        continue
    fi
    if [[ ! -f "$GIT_FILE" ]]; then
        ALERTS+=("MISSING_GIT|$f|git infra/ missing (pull needed)")
        continue
    fi

    PROD_MD5=$(md5sum "$PROD_FILE" | awk '{print $1}')
    GIT_MD5=$(md5sum "$GIT_FILE" | awk '{print $1}')

    if [[ "$PROD_MD5" != "$GIT_MD5" ]]; then
        ALERTS+=("DIVERGE|$f|prod=$PROD_MD5 git=$GIT_MD5")
        log "⚠️  DIVERGE: $f prod=$PROD_MD5 git=$GIT_MD5"
    else
        log "✓ MATCH: $f md5=$PROD_MD5"
    fi
done

# 3.2 比對 git HEAD vs origin/main (是否未部署 commit)
CURRENT_HEAD=$(git rev-parse HEAD)
REMOTE_HEAD=$(git rev-parse origin/main)
SHORT_CURRENT=$(git rev-parse --short HEAD)
SHORT_REMOTE=$(git rev-parse --short origin/main)

if [[ "$CURRENT_HEAD" != "$REMOTE_HEAD" ]]; then
    BEHIND=$(git rev-list --count "$CURRENT_HEAD..$REMOTE_HEAD" 2>/dev/null || echo "?")
    # P1.R47.v2: 過濾 docs-only commit 避免 false positive (規範 #44 缺陷溯源)
    BEHIND_FILES=$(git diff --name-only "$CURRENT_HEAD..$REMOTE_HEAD" 2>/dev/null)
    BEHIND_PRODUCTION=false
    while IFS= read -r _f; do
        case "$_f" in
            infra/*) BEHIND_PRODUCTION=true; break ;;
        esac
    done <<< "$BEHIND_FILES"
    if $BEHIND_PRODUCTION; then
        ALERTS+=("BEHIND_PRODUCTION|HEAD|$BEHIND commits behind, infra/* affected (current=$SHORT_CURRENT remote=$SHORT_REMOTE)")
        log "⚠️  BEHIND_PRODUCTION: $BEHIND commits (infra/* changed)"
    else
        log "ℹ️  INFO: $BEHIND commits behind, but docs-only (no production impact)"
    fi
else
    log "✓ HEAD up-to-date: $SHORT_CURRENT"
fi

# ─── Step 4: force-alert 模式 (測試用) ──────────────
if $FORCE_ALERT; then
    ALERTS+=("TEST|forced|--force-alert flag set for testing SMTP")
    log "⚠️  FORCE_ALERT: 添加測試 alert"
fi

# ─── Step 5: 結果處理 ───────────────────────────────
N_ALERTS=${#ALERTS[@]}

if [[ "$N_ALERTS" -eq 0 ]]; then
    log "═══ OK: production ≡ git, HEAD up-to-date ═══"
    exit 0
fi

log "═══ FOUND $N_ALERTS ALERTS ═══"
for a in "${ALERTS[@]}"; do
    log "  - $a"
done

# ─── Step 6: 寄 SMTP 警報 (除非 --dry-run) ─────────
if $DRY_RUN; then
    log "✋ DRY_RUN: 不寄信 (alerts 已 log)"
    exit 0
fi

if [[ ! -f "$ALERT_SCRIPT" ]]; then
    log "❌ FATAL: $ALERT_SCRIPT not found, 無法寄信"
    exit 4
fi

log "→ Step 6: 呼叫 $ALERT_SCRIPT 寄信..."
if "$PYTHON_BIN" "$ALERT_SCRIPT" "${ALERTS[@]}" 2>&1 | tee -a "$LOG_FILE"; then
    log "✅ alert 寄出成功"
else
    log "❌ alert 寄出失敗 (詳見上方 STDERR)"
    exit 5
fi

log "═══ END (寄出 $N_ALERTS alerts) ═══"
exit 0
