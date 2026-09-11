"""
F-lite redact 第一刀單元測試
─────────────────────────────────
所有測試樣本均為【自造假值】，絕不含任何真實密碼/真實 key。
驗證：base_redact 5 pattern + F_LITE_PATTERNS 3 類（PG/SSH/sudo）全命中。
"""
from f_lite_redact import f_lite_sanitize, sanitize_with_count


# ── 自造假樣本（FAKE，非真實）──
FAKE_CASES = [
    # base_redact 既有 5 pattern
    ("sk-FAKEFAKEFAKEFAKEFAKE1234567890",      "sk-",      "OpenAI key 形態"),
    ("AIzaFAKEFAKEFAKEFAKEFAKE1234567",         "AIza",     "Google key 形態"),
    ("ghp_FAKEFAKEFAKEFAKEFAKE1234567",         "ghp_",     "GitHub PAT 形態"),
    ("Authorization: Bearer FAKEtokenFAKEtokenFAKEtoken", "Bearer", "Bearer token"),
    ("password=FAKESECRETVALUE",                "password", "通用 key=val"),
    # F-lite 擴充 3 類
    ("postgres://goaa:FAKEPGPW123@1.2.3.4:5432/db", "postgres://", "PG 連線串"),
    ("PGPASSWORD=FAKEPGPW456 psql -h host",     "PGPASSWORD", "PGPASSWORD 賦值"),
    ("-----BEGIN OPENSSH PRIVATE KEY-----",     "BEGIN",    "SSH 私鑰區塊"),
    ("ssh-ed25519 FAKEBASE64KEYMATERIALxxxxxxxxxx user@h", "ssh-ed25519", "SSH 公鑰行"),
    ("echo FAKESUDOPW | sudo -S systemctl restart x", "sudo", "sudo-stdin 管線"),
]


def run():
    print("=== F-lite redact 第一刀 dry-run (全自造假樣本) ===\n")
    all_pass = True
    for raw, leak_marker, desc in FAKE_CASES:
        out = f_lite_sanitize(raw)
        # 判定：輸出必須含 REDACTED 標記，且不得殘留假密碼主體
        has_redact = "REDACTED" in out
        # 殘留檢查：假密碼主體（FAKE...）不應出現在輸出（key=val 類保留 key 名是預期的）
        leaked = any(tok in out for tok in ["FAKEPGPW", "FAKESUDOPW", "FAKEBASE64KEY",
                                            "FAKESECRETVALUE", "FAKEtoken",
                                            "FAKEFAKEFAKEFAKEFAKE"])
        ok = has_redact and not leaked
        all_pass = all_pass and ok
        status = "✅" if ok else "❌"
        print(f"{status} [{desc}]")
        print(f"     in : {raw}")
        print(f"     out: {out}")
        if leaked:
            print(f"     ⚠️ 殘留假密碼主體！")
        print()

    # 命中計數驗證
    pg_text = "postgres://u:FAKEPGPW@h/db and echo FAKEPW | sudo -S x"
    _, hits = sanitize_with_count(pg_text)
    print(f"F-lite pattern 命中計數 (供 audit redaction_count): {hits}")
    print()

    # 邊界：空字串/None
    assert f_lite_sanitize("") == ""
    assert f_lite_sanitize(None) is None
    print("邊界測試 (空字串/None): ✅")

    print(f"\n=== 總結: {'全過 ✅' if all_pass else '有失敗 ❌'} ===")
    return all_pass


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)
