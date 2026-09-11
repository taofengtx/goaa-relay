"""
F-lite secret redaction 擴充層
─────────────────────────────────────────
定位：在現有 extract_qwenpaw.redact() 之上，疊加 F-lite 專屬 secret pattern
      （PG 連線 / SSH 私鑰 / sudo-stdin），用於 task_result / runtime log /
      前端輸出之前的二次過濾。

紀律：
  - #11 只增不毀：不改 extract_qwenpaw.py，import 複用其 redact()
  - #22 secret：pattern 只用通用形態，絕不寫入任何真實密碼值
  - C2 §6/§15：命中即遮蔽，不回顯原文
  - 不聲稱物理級清零 / 100% 不洩漏，僅 best-effort redaction

注意：本檔為 F-lite 第一刀（純函數）。掛載到 task_result/log 的整合
      屬後續刀，不在本檔範圍。
"""
import re

# 複用現有 redact（5 個 pattern：sk-/AIza/ghp_/Bearer/通用 key=val）
# import 路徑：task_runner.py 已 sys.path.insert(同目錄)，extract_qwenpaw 在上一層 rag/
try:
    from extract_qwenpaw import redact as base_redact
except ImportError:
    # 若本檔在 workers/ 子目錄被呼叫，補上層路徑
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from extract_qwenpaw import redact as base_redact


# F-lite 專屬擴充 pattern（通用形態，無真實密碼值）
F_LITE_PATTERNS = [
    # PG 連線串：postgres://user:****@host/db  → 遮 user 之後的整段
    (re.compile(r'postgres(?:ql)?://[^:\s]+:[^@\s]+@'), 'postgres://***PG_REDACTED***@'),
    # PGPASSWORD / DATABASE_URL 賦值
    (re.compile(r'(?i)(PGPASSWORD|DATABASE_URL)(\s*[:=]\s*)\S+'), r'\1\2***PG_REDACTED***'),
    # SSH 私鑰區塊起始（任意 KEY 類型）
    (re.compile(r'-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----'), '-----BEGIN ***SSH_KEY_REDACTED***-----'),
    # SSH 公鑰行（ssh-ed25519 / ssh-rsa + base64 主體）
    (re.compile(r'(ssh-(?:ed25519|rsa|dss))\s+[A-Za-z0-9+/=]{20,}'), r'\1 ***SSH_PUBKEY_REDACTED***'),
    # sudo 從 stdin 餵密碼的通用形態（不綁定任何具體密碼值/長度/格式）
    # 形態一：echo <任意> | sudo -S
    (re.compile(r'echo\s+\S+\s*\|\s*sudo\s+-S'), 'echo ***SUDO_PIPE_REDACTED*** | sudo -S'),
    # 形態二：sudo -S 後直接接（覆蓋管線外的寫法）
    (re.compile(r'(sudo\s+-S\b)'), r'\1 ***SUDO_STDIN***'),
]


def f_lite_sanitize(text):
    """
    F-lite 二次脫敏：先過 base_redact（5 pattern），再過 F_LITE_PATTERNS（PG/SSH/sudo）。
    返回脫敏後文字。命中數不在此回傳（base_redact 用全域計數；F-lite 命中見 sanitize_with_count）。
    """
    if not text:
        return text
    text = base_redact(text)
    for pat, repl in F_LITE_PATTERNS:
        text = pat.sub(repl, text)
    return text


def sanitize_with_count(text):
    """
    返回 (脫敏後文字, F_LITE_PATTERNS 命中數)。
    只計 F-lite 擴充 pattern 的命中（base_redact 自有計數）。
    供 audit 記錄 redaction_count 用（C2 §15：只記數，不記正文）。
    """
    if not text:
        return text, 0
    text = base_redact(text)
    hits = 0
    for pat, repl in F_LITE_PATTERNS:
        text, n = pat.subn(repl, text)
        hits += n
    return text, hits
