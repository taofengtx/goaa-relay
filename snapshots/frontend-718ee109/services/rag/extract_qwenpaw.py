#!/usr/bin/env python3
"""Stage 0 v2: QwenPaw sessions -> redacted corpus.jsonl. 不嵌入/不上傳。"""
import json, re, sys, glob, os

PATTERNS = [
    (re.compile(r'sk-[A-Za-z0-9_\-]{20,}'),        'sk-***REDACTED***'),
    (re.compile(r'AIza[A-Za-z0-9_\-]{20,}'),       'AIza-***REDACTED***'),
    (re.compile(r'ghp_[A-Za-z0-9]{20,}'),          'ghp_***REDACTED***'),
    (re.compile(r'Bearer\s+[A-Za-z0-9._\-]{20,}'), 'Bearer ***REDACTED***'),
    (re.compile(r'(?i)(password|passwd|pwd|secret|api[_\-]?key|master[_\-]?key)(\s*[:=]\s*)\S+'), r'\1\2***REDACTED***'),
]
redaction_hits = 0

def redact(text):
    global redaction_hits
    for pat, repl in PATTERNS:
        text, n = pat.subn(repl, text)
        redaction_hits += n
    return text

def extract_text(content):
    if not isinstance(content, list):
        return ""
    return "\n".join(c.get("text", "") for c in content
                     if isinstance(c, dict) and c.get("type") == "text")

def get_msg(entry):
    # 實測結構: entry 是 list [msg_dict, []]; 兼容 dict 與 {value:[msg]}
    if isinstance(entry, list) and entry:
        return entry[0]
    if isinstance(entry, dict) and isinstance(entry.get("value"), list) and entry["value"]:
        return entry["value"][0]
    if isinstance(entry, dict) and "role" in entry:
        return entry
    return None

def main(sessions_glob, out_path):
    files = glob.glob(sessions_glob)
    if not files:
        print(f"ERROR: no session files matched {sessions_glob}", file=sys.stderr)
        sys.exit(1)
    rows = 0
    skipped_norole = 0
    skipped_empty = 0
    with open(out_path, "w", encoding="utf-8") as out:
        for fp in files:
            with open(fp, encoding="utf-8") as f:
                try:
                    j = json.load(f)
                except Exception as e:
                    print(f"WARN skip {fp}: {e}", file=sys.stderr)
                    continue
            content = (j.get("agent", {}).get("memory", {}) or {}).get("content", [])
            sid = os.path.basename(fp)
            for entry in content:
                msg = get_msg(entry)
                if not isinstance(msg, dict) or "role" not in msg:
                    skipped_norole += 1
                    continue
                text = redact(extract_text(msg.get("content", [])))
                if not text.strip():
                    skipped_empty += 1
                    continue
                out.write(json.dumps({
                    "session_id": sid,
                    "msg_id": msg.get("id", ""),
                    "role": msg.get("role", ""),
                    "ts": msg.get("timestamp", ""),
                    "text": text,
                }, ensure_ascii=False) + "\n")
                rows += 1
    print(f"OK rows={rows} skipped_norole={skipped_norole} skipped_empty={skipped_empty} redaction_hits={redaction_hits} -> {out_path}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
