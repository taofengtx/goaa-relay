#!/usr/bin/env python3
"""
send_consistency_alert.py — 規範 #47 DO ↔ git 警報寄信
═══════════════════════════════════════════════════════════════════════
Purpose:
  接收 check_do_git_consistency.sh 收集的 alerts 清單
  從 /etc/goaa/secrets.env source SMTP 配置 (規範 #22 不硬編碼)
  用 STARTTLS 寄信給 EMAIL_TO
  log 寄送結果到 /opt/goaa/logs/consistency_check.log

簽發: 2026-05-20 PT Claude
規範遵守:
  #22  : SMTP 配置從 secrets.env 讀, 不在程式內硬編碼密碼
  #28  : try/except 全包, 任何失敗 logger.exception
  #36 v2: alert 清單為真實數據

使用:
  python3 send_consistency_alert.py "DIVERGE|api.py|prod=X git=Y" "BEHIND|..." ...

呼叫者: check_do_git_consistency.sh (規範 #47 cron)
═══════════════════════════════════════════════════════════════════════
"""

import os
import sys
import smtplib
import socket
import logging
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formatdate
from pathlib import Path

# ─── 設定 logging ────────────────────────────────────
LOG_FILE = Path("/opt/goaa/logs/consistency_check.log")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s UTC] alert.py: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("consistency_alert")

# ─── Step 1: source secrets.env (規範 #22) ───────────
SECRETS_PATH = Path("/etc/goaa/secrets.env")


def load_secrets(path: Path) -> dict:
    """讀 KEY=VALUE 格式檔, 跳過註解 / 空行 / 縮排異常"""
    secrets = {}
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")

    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        # 跳過註解 / 空行
        if not stripped or stripped.startswith("#"):
            continue
        # 跳過縮排行 (規範 #22 嚴格頂格)
        if line[0] in (" ", "\t"):
            logger.warning(f"Line {line_no} indented (ignored): {stripped[:20]}...")
            continue
        # 跳過非 KEY=VALUE 行
        if "=" not in stripped:
            logger.warning(f"Line {line_no} no '=' (ignored)")
            continue
        key, _, value = stripped.partition("=")
        # 去引號 (常見 'value' 或 "value")
        if value and value[0] in ('"', "'") and value[-1] == value[0]:
            value = value[1:-1]
        secrets[key.strip()] = value
    return secrets


# ─── Step 2: 主邏輯 ──────────────────────────────────
def main():
    if len(sys.argv) < 2:
        logger.error("USAGE: send_consistency_alert.py 'alert1' 'alert2' ...")
        sys.exit(1)

    alerts = sys.argv[1:]
    logger.info(f"Received {len(alerts)} alerts to send")

    # ─── load secrets ────────────────────────────
    try:
        secrets = load_secrets(SECRETS_PATH)
    except Exception as e:
        logger.exception(f"FATAL: load_secrets({SECRETS_PATH}) failed: {e}")
        sys.exit(2)

    required = ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "EMAIL_TO")
    missing = [k for k in required if k not in secrets or not secrets[k]]
    if missing:
        logger.error(f"FATAL: missing secrets keys: {missing}")
        sys.exit(3)

    smtp_host = secrets["SMTP_HOST"]
    smtp_port = int(secrets["SMTP_PORT"])
    smtp_user = secrets["SMTP_USER"]
    smtp_pass = secrets["SMTP_PASS"]
    email_to = secrets["EMAIL_TO"]

    logger.info(f"SMTP config loaded: host={smtp_host} port={smtp_port} user={smtp_user[:4]}***")
    # 規範 #22: 不 log SMTP_PASS, 不 log 完整 USER

    # ─── compose email ─────────────────────────
    hostname = socket.gethostname()
    now_utc = datetime.now(timezone.utc)

    msg = EmailMessage()
    msg["Subject"] = f"[GOAA 規範 #47] DO ↔ git 偏移警報 ({len(alerts)} alerts) — {hostname}"
    msg["From"] = smtp_user
    msg["To"] = email_to
    msg["Date"] = formatdate(localtime=True)

    body_lines = [
        "GOAA Consistency Monitor 偵測到 DO production 與 GitHub HEAD 不一致.",
        "",
        f"檢查時間: {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"主機: {hostname}",
        f"Alert 數量: {len(alerts)}",
        "",
        "═══ 警報詳情 ═══",
        "",
    ]

    for i, alert in enumerate(alerts, 1):
        parts = alert.split("|", 2)
        if len(parts) == 3:
            alert_type, target, detail = parts
            body_lines.append(f"{i}. [{alert_type}] {target}")
            body_lines.append(f"   {detail}")
        else:
            body_lines.append(f"{i}. {alert}")
        body_lines.append("")

    body_lines.extend([
        "═══ 處置建議 ═══",
        "",
        "- DIVERGE 類: 走 deploy 流程 (規範 #14 v2)",
        "    ssh root@DO 'bash /opt/goaa/scripts/do-deploy-model-router-api.sh --restart'",
        "",
        "- BEHIND 類: git pull DO 同步最新 commit",
        "    ssh root@DO 'cd /opt/goaa && git pull --ff-only origin main'",
        "",
        "- MISSING_PROD: production 檔被誤刪, 從 backup 還原 + 走 deploy",
        "",
        "- MISSING_GIT: git pull 還沒跑或失敗, 手動處理",
        "",
        "═══ Log ═══",
        f"完整 log: /opt/goaa/logs/consistency_check.log",
        "",
        "—— GOAA Consistency Monitor (規範 #47)",
    ])

    msg.set_content("\n".join(body_lines))

    # ─── send email (STARTTLS) ─────────────────
    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.set_debuglevel(0)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_pass)
            logger.info("SMTP login OK")

            result = server.send_message(msg)
            logger.info(f"郵件寄出 ({len(msg.as_bytes())} bytes) → {email_to}")
            if result:
                logger.warning(f"部分收件人未接受: {result}")
            else:
                logger.info("所有收件人接受")

    except smtplib.SMTPAuthenticationError as e:
        logger.exception(f"FATAL: SMTP auth failed: {e}")
        sys.exit(4)
    except smtplib.SMTPException as e:
        logger.exception(f"FATAL: SMTP error: {e}")
        sys.exit(5)
    except (socket.timeout, socket.gaierror) as e:
        logger.exception(f"FATAL: network error: {e}")
        sys.exit(6)
    except Exception as e:
        logger.exception(f"FATAL: unexpected error: {e}")
        sys.exit(7)

    logger.info("═══ alert 寄出完成 ═══")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
