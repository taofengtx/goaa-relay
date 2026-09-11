#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════════════
# install_consistency_cron.sh — 一次性 crontab 安裝
# ════════════════════════════════════════════════════════════════════════
#
# Purpose: 安裝規範 #47 DO ↔ git 監控 crontab
#          (每日 UTC 07:00 = PT 00:00 跑 check_do_git_consistency.sh)
#
# 簽發: 2026-05-20 PT Claude
# 規範遵守:
#   #11 only-add  : backup 現有 crontab 後 append, 不覆蓋現有條目
#   #47           : 設立規範 #47 自動化監控
#
# 使用:
#   bash install_consistency_cron.sh           # 安裝
#   bash install_consistency_cron.sh --check   # 只驗證安裝狀態
#   bash install_consistency_cron.sh --uninstall  # 移除條目
#
# 設計:
#   - 用 marker 註解 (# REGULATION_47_MONITOR) 標記條目, 方便日後管理
#   - 重跑安全 (規範 #11): 已安裝就跳過
#   - --uninstall 用 marker 精準移除, 不影響其他 crontab 條目
# ════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ─── 配置 ────────────────────────────────────────────
SCRIPT_PATH="/opt/goaa/scripts/check_do_git_consistency.sh"
MARKER="# REGULATION_47_MONITOR"
CRON_ENTRY="0 7 * * * ${SCRIPT_PATH} ${MARKER}"
BACKUP_DIR="/opt/goaa/logs"
TS=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/crontab.bak.${TS}"

# ─── flag ────────────────────────────────────────────
CHECK_ONLY=false
UNINSTALL=false
for arg in "$@"; do
    case "$arg" in
        --check) CHECK_ONLY=true ;;
        --uninstall) UNINSTALL=true ;;
        --help|-h)
            grep -E "^# (Purpose|使用|設計)" "$0" | sed 's/^# //'
            exit 0
            ;;
    esac
done

mkdir -p "$BACKUP_DIR"

# ─── Step 1: 環境驗證 ────────────────────────────────
if [[ ! -x "$SCRIPT_PATH" ]]; then
    echo "❌ FATAL: $SCRIPT_PATH not executable (chmod +x first?)" >&2
    exit 2
fi

# ─── Step 2: 取得現有 crontab ────────────────────────
CURRENT_CRON=$(crontab -l 2>/dev/null || echo "")
HAS_REGULATION_47=false
if echo "$CURRENT_CRON" | grep -qF "$MARKER"; then
    HAS_REGULATION_47=true
fi

# ─── Step 3: --check 模式 ──────────────────────────
if $CHECK_ONLY; then
    if $HAS_REGULATION_47; then
        echo "✅ 規範 #47 監控 crontab 已安裝:"
        echo "$CURRENT_CRON" | grep -F "$MARKER"
        exit 0
    else
        echo "✗ 規範 #47 監控 crontab 未安裝"
        exit 1
    fi
fi

# ─── Step 4: --uninstall 模式 ──────────────────────
if $UNINSTALL; then
    if ! $HAS_REGULATION_47; then
        echo "✓ 條目本來就不存在, 無需移除"
        exit 0
    fi
    # backup
    crontab -l > "$BACKUP_FILE" 2>/dev/null || true
    echo "✓ backup → $BACKUP_FILE"

    # 移除 marker 條目
    NEW_CRON=$(echo "$CURRENT_CRON" | grep -vF "$MARKER")
    if [[ -z "$NEW_CRON" ]]; then
        crontab -r 2>/dev/null || true
        echo "✓ crontab 清空 (僅有規範 #47 條目)"
    else
        echo "$NEW_CRON" | crontab -
        echo "✓ 規範 #47 條目已移除"
    fi
    exit 0
fi

# ─── Step 5: 安裝 (預設模式) ─────────────────────────
if $HAS_REGULATION_47; then
    echo "✓ 規範 #47 條目已安裝, 跳過 (規範 #11 防重)"
    echo "現有條目:"
    echo "$CURRENT_CRON" | grep -F "$MARKER"
    exit 0
fi

# backup 現有 crontab (規範 #11)
if [[ -n "$CURRENT_CRON" ]]; then
    echo "$CURRENT_CRON" > "$BACKUP_FILE"
    echo "✓ backup 現有 crontab → $BACKUP_FILE"
else
    echo "✓ 現有 crontab 為空, 無需 backup"
fi

# 組新 crontab (append)
NEW_CRON="${CURRENT_CRON}
${CRON_ENTRY}"

# 寫入
echo "$NEW_CRON" | crontab -

# ─── Step 6: 驗證安裝 ────────────────────────────────
INSTALLED=$(crontab -l 2>/dev/null | grep -F "$MARKER" || echo "")
if [[ -z "$INSTALLED" ]]; then
    echo "❌ FATAL: 安裝後驗證失敗, 條目未出現"
    exit 3
fi

echo "═══════════════════════════════════════════"
echo "  規範 #47 監控 crontab 安裝成功 ✅"
echo "═══════════════════════════════════════════"
echo "  條目: $INSTALLED"
echo "  下次跑: 明天 UTC 07:00 (PT 00:00)"
echo "  手動測試: bash $SCRIPT_PATH"
echo "  強制寄信測試: bash $SCRIPT_PATH --force-alert"
echo "  解除: bash $0 --uninstall"
echo "═══════════════════════════════════════════"
