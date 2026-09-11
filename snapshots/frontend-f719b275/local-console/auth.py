#!/usr/bin/env python3
"""
GOAA Local Console — auth.py (V5.3 Local Auth)
部署: /opt/goaa/local-console/auth.py

設計:
  - local_user.db (sqlite): users(username PK, password_hash, role, created_at)
  - argon2id 密碼 hash(不存明文)
  - signed cookie session(key 從環境 CONSOLE_SESSION_KEY 讀,不硬編碼)
  - 三角色:admin / provider / viewer

Secret 邊界:
  - 本模組不含任何默認密碼、不含 session key 明文
  - admin 初始密碼由 Tao 親手經 setup CLI 設定(create_user)
  - CONSOLE_SESSION_KEY 由 Tao 親手設環境變數
  - 不 log 密碼、不回傳 hash 給前端
"""

import os
import sqlite3
import time
import hmac
import hashlib
import base64
import json
import logging

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

log = logging.getLogger("local-console.auth")

DB_PATH = os.path.join(os.path.dirname(__file__), "local_user.db")
ROLES = ("admin", "provider", "viewer")
SESSION_TTL = 8 * 3600  # 8 小時

_ph = PasswordHasher()


def _session_key() -> bytes:
    """從環境讀 session 簽名 key;缺失即報錯(不給默認值)。"""
    k = os.environ.get("CONSOLE_SESSION_KEY")
    if not k:
        raise RuntimeError("CONSOLE_SESSION_KEY not set (Tao 須親手設定)")
    return k.encode("utf-8")


# ── DB ──
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at REAL NOT NULL
        )
    """)
    conn.commit()
    return conn


def create_user(username: str, password: str, role: str) -> bool:
    """建用戶(setup flow 用,Tao 親手跑)。存 argon2 hash,不存明文。"""
    if role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}")
    if not username or not password:
        raise ValueError("username/password required")
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, role, created_at) VALUES (?,?,?,?)",
            (username, _ph.hash(password), role, time.time()),
        )
        conn.commit()
        log.info("user created: username=%s role=%s", username, role)  # 不 log 密碼
        return True
    except sqlite3.IntegrityError:
        log.error("create_user failed: username=%s already exists", username)
        return False
    finally:
        conn.close()


def verify_user(username: str, password: str):
    """驗密碼。成功回 role,失敗回 None。不回傳 hash。"""
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT password_hash, role FROM users WHERE username=?", (username,)
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    pw_hash, role = row
    try:
        _ph.verify(pw_hash, password)
        return role
    except (VerifyMismatchError, InvalidHashError):
        return None


def has_any_user() -> bool:
    """是否已有用戶(供 setup flow 判斷)。"""
    conn = _connect()
    try:
        n = conn.execute("SELECT count(*) FROM users").fetchone()[0]
    finally:
        conn.close()
    return n > 0


# ── Session(signed cookie) ──
def issue_session(username: str, role: str) -> str:
    """簽發 session token:base64(payload).hmac。"""
    payload = {"u": username, "r": role, "exp": int(time.time()) + SESSION_TTL}
    raw = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    sig = hmac.new(_session_key(), raw.encode(), hashlib.sha256).hexdigest()
    return f"{raw}.{sig}"


def verify_session(token: str):
    """驗 session token。有效回 {u, r},無效/過期回 None。"""
    if not token or "." not in token:
        return None
    raw, sig = token.rsplit(".", 1)
    expect = hmac.new(_session_key(), raw.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expect):
        return None
    try:
        payload = json.loads(base64.urlsafe_b64decode(raw.encode()))
    except Exception:
        return None
    if payload.get("exp", 0) < int(time.time()):
        return None
    return {"u": payload.get("u"), "r": payload.get("r")}


# ── setup CLI(Tao 親手跑,設第一個 admin)──
if __name__ == "__main__":
    import getpass
    import sys
    print("=== GOAA Local Console — Setup ===")
    if has_any_user():
        print("已有用戶存在。如需新增,輸入新用戶資料;Ctrl-C 取消。")
    username = input("username: ").strip()
    role = input(f"role {ROLES}: ").strip()
    if role not in ROLES:
        print(f"ERROR: role 必須是 {ROLES}")
        sys.exit(1)
    pw1 = getpass.getpass("password: ")        # 不回顯
    pw2 = getpass.getpass("confirm:  ")
    if pw1 != pw2:
        print("ERROR: 兩次密碼不一致")
        sys.exit(1)
    if len(pw1) < 8:
        print("ERROR: 密碼至少 8 字元")
        sys.exit(1)
    ok = create_user(username, pw1, role)
    print("OK: user created" if ok else "FAILED: 用戶可能已存在")
