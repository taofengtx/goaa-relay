#!/usr/bin/env python3
"""
GOAA Worker Runtime V5.2 — embed worker
DRAFT — 部署到 AiKa-2: /opt/goaa/workers/embed_worker.py
獨立模組,不改動現有 agent.py(只在需要時 import 其 exec_*)。

安全鐵律:
  - 所有連線資訊(PG / Ollama)只從環境變數讀,零硬編碼。
  - 環境變數由 worker_secrets.env(chmod 600,師兄親手寫)經
    `set -a; . worker_secrets.env; set +a` 注入進程環境。
  - secret 永不出現在程式碼、日誌、stdout。
  - 偵測到疑似 secret 的 corpus 文本:跳過,不寫入,不輸出原文。

啟動方式(學弟可做,不碰密碼值;密碼已在進程環境):
  set -a; . /etc/goaa/worker_secrets.env; set +a
  python3 /opt/goaa/workers/embed_worker.py --corpus <path> --dry-run --limit 3
"""

import os
import sys
import json
import time
import re
import hashlib
import argparse
import logging
import urllib.request
import urllib.error

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("embed_worker")

# psycopg2 為新依賴(學弟 pip install psycopg2-binary,不碰密碼)
try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    psycopg2 = None


# ── secret 偵測(與 Stage 0 extractor 對齊) ──
_SECRET_PATTERNS = [
    re.compile(r'sk-[A-Za-z0-9_\-]{20,}'),
    re.compile(r'AIza[A-Za-z0-9_\-]{20,}'),
    re.compile(r'ghp_[A-Za-z0-9]{20,}'),
    re.compile(r'Bearer\s+[A-Za-z0-9._\-]{20,}'),
    re.compile(r'(?i)(password|passwd|pwd|secret|api[_\-]?key|master[_\-]?key)\s*[:=]\s*\S+'),
]


def _has_secret(text: str) -> bool:
    return any(p.search(text) for p in _SECRET_PATTERNS)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── 環境變數讀取(缺值即報錯,不給 fallback,不洩漏) ──
def _require_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        log.error("缺少必要環境變數: %s (請確認已 source worker_secrets.env)", name)
        sys.exit(2)
    return val


def _pg_connect():
    if psycopg2 is None:
        log.error("psycopg2 未安裝。請先: pip3 install psycopg2-binary")
        sys.exit(3)
    dsn = os.environ.get("DATABASE_URL")
    if dsn:
        return psycopg2.connect(dsn)
    return psycopg2.connect(
        host=_require_env("POSTGRES_HOST"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        dbname=_require_env("POSTGRES_DB"),
        user=_require_env("POSTGRES_USER"),
        password=_require_env("POSTGRES_PASSWORD"),   # 只從環境讀,絕不打印
    )


# ── Ollama 嵌入(endpoint / model 走環境變數) ──
def _embed(text: str, ollama_url: str, model: str, timeout: int = 120):
    # Ollama 0.23+ 標準端點 /api/embed,回傳 {"embeddings": [[...]]}
    payload = json.dumps({"model": model, "input": text}).encode("utf-8")
    req = urllib.request.Request(
        f"{ollama_url.rstrip('/')}/api/embed",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read()[:200].decode('utf-8','replace')}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"URLError: {e.reason}")
    # 新端點回 "embeddings":[[...]];舊端點回 "embedding":[...]
    embs = data.get("embeddings")
    vec = embs[0] if isinstance(embs, list) and embs else data.get("embedding")
    if not isinstance(vec, list) or len(vec) != 768:
        raise ValueError(f"embedding dim != 768 (got {len(vec) if isinstance(vec, list) else 'none'})")
    return vec


# ── 超長文本分塊(V5.2.C: 超過嵌入 context 上限時切塊) ──
MAX_CHARS = 1500      # 保守上限,約 < nomic context(中文)
OVERLAP   = 150       # 塊間重疊,避免切斷語意

def _chunk_text(text: str, max_chars: int = MAX_CHARS, overlap: int = OVERLAP):
    """超過 max_chars 才分塊;否則回單元素 list。回 [(chunk_index, chunk_text), ...]"""
    if len(text) <= max_chars:
        return [(0, text)]
    chunks = []
    start = 0
    idx = 0
    step = max_chars - overlap
    while start < len(text):
        chunks.append((idx, text[start:start + max_chars]))
        idx += 1
        start += step
    return chunks


# ── 核心 task ──
def exec_embed_corpus(params: dict) -> dict:
    """
    params: corpus_path, dry_run(預設True), limit(預設3), batch_size(預設50),
            model(預設env EMBED_MODEL或nomic-embed-text), target_table(qwenpaw_memory_chunks)
    回報純統計,無任何 text / secret 原文。
    """
    t0 = time.time()
    corpus_path = params["corpus_path"]
    dry_run = params.get("dry_run", True)
    limit = params.get("limit", 3)
    batch_size = params.get("batch_size", 50)
    model = params.get("model") or os.environ.get("EMBED_MODEL", "nomic-embed-text")
    target_table = params.get("target_table", "qwenpaw_memory_chunks")
    ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")

    stats = {"processed": 0, "skipped_secret": 0, "skipped_empty": 0, "chunked_msgs": 0,
             "failed": 0, "inserted": 0}

    rows = []
    with open(corpus_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                stats["failed"] += 1
            if limit and len(rows) >= limit:
                break

    conn = cur = None
    if not dry_run:
        conn = _pg_connect()
        cur = conn.cursor()
    pending = []

    def _flush():
        if dry_run or not pending:
            return
        execute_values(
            cur,
            f"""INSERT INTO {target_table}
                (session_id, msg_id, role, ts, text_hash, text_redacted, embedding, source)
                VALUES %s
                ON CONFLICT (session_id, msg_id) DO UPDATE
                  SET embedding=EXCLUDED.embedding, text_hash=EXCLUDED.text_hash, updated_at=now()""",
            pending,
            template="(%s,%s,%s,%s,%s,%s,%s,%s)",
        )
        conn.commit()
        stats["inserted"] += len(pending)
        pending.clear()

    try:
        for rec in rows:
            text = rec.get("text", "")
            if not text.strip():
                stats["skipped_empty"] += 1
                continue
            if _has_secret(text):
                stats["skipped_secret"] += 1   # 跳過,不寫不印原文
                continue
            parts = _chunk_text(text)
            if len(parts) > 1:
                stats["chunked_msgs"] += 1
            base_msg_id = rec.get("msg_id", "")
            for cidx, chunk in parts:
                # 分塊的 msg_id 加後綴,避免 UNIQUE(session_id,msg_id) 自我覆蓋
                this_msg_id = base_msg_id if len(parts) == 1 else f"{base_msg_id}#chunk{cidx}"
                try:
                    vec = _embed(chunk, ollama_url, model)
                except Exception as e:
                    stats["failed"] += 1
                    log.warning("embed failed (chunk skipped): %s", str(e)[:200])
                    continue
                stats["processed"] += 1
                pending.append((
                    rec.get("session_id", ""), this_msg_id,
                    rec.get("role", ""), rec.get("ts") or None,
                    _sha256(chunk), chunk, vec, "qwenpaw_corpus",
                ))
                if len(pending) >= batch_size:
                    _flush()
        _flush()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    stats["duration_s"] = round(time.time() - t0, 2)
    stats["dry_run"] = dry_run
    stats["limit"] = limit
    return {"task": "exec_embed_corpus", "ok": True, "stats": stats}


# ── CLI(學弟啟動用;密碼從進程環境讀,指令不含密碼) ──
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--dry-run", action="store_true", default=False)
    ap.add_argument("--limit", type=int, default=3)
    ap.add_argument("--batch-size", type=int, default=50)
    ap.add_argument("--model", default=None)
    ap.add_argument("--target-table", default="qwenpaw_memory_chunks")
    ap.add_argument("--check-env", action="store_true",
                    help="只檢查環境變數是否齊(回報有/無,不印值)")
    args = ap.parse_args()

    if args.check_env:
        for k in ("POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD",
                  "OLLAMA_URL", "EMBED_MODEL"):
            v = os.environ.get(k)
            # 只印「有無 + 長度」,絕不印值
            print(f"{k}: {'SET len=' + str(len(v)) if v else 'MISSING'}")
        return

    result = exec_embed_corpus({
        "corpus_path": args.corpus,
        "dry_run": args.dry_run,
        "limit": args.limit,
        "batch_size": args.batch_size,
        "model": args.model,
        "target_table": args.target_table,
    })
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
