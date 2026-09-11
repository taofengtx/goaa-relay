#!/usr/bin/env python3
"""
GOAA C2 — rag_context_fetch.py (V5.3 RAG Chat)
部署: /opt/goaa/workers/rag_context_fetch.py

對照 docs/business/GOAA_C2_DATA_PRIVACY_SPEC.md 實作。
最高拍板:正文只進內存。chunk 正文僅用於組裝 prompt 餵本地 qwen2.5:3b,
不落盤、不返前端原文、不入任何 log。

復用(規範 #27,#24 已確認簽名):
  from embed_worker import _embed, _pg_connect
  _embed(text, ollama_url, model, timeout=120) → /api/embed
  _pg_connect() → 直接回 psycopg2 conn(非 context manager,需手動 close)

表: qwenpaw_memory_chunks  欄位: text_redacted  算子: <=>(cosine)
"""

import os
import gc
import json
import time
import hashlib
import logging
import urllib.request

import psycopg2  # noqa: F401  (僅型別/異常用)
from embed_worker import _embed, _pg_connect

log = logging.getLogger("c2.rag_context_fetch")

TARGET_TABLE = "qwenpaw_memory_chunks"

# §10 短句污染雙網閘
STOP_WORDS_SET = {"好", "收到", "嗯", "ok", "okay", "thanks", "thank you", "yes", "no"}
import re
_FEATURE = re.compile(r'[0-9_:/]|[A-Z]{2,}')  # 數字/下劃線/冒號/斜線/大寫縮寫 → 高密度特徵


def _is_noise(text: str, text_len: int, min_text_len: int) -> bool:
    """§10:length + stop words 雙網閘。短且命中 stop words → 噪音;含特徵 → 保留。"""
    if text_len >= min_text_len:
        return False
    norm = (text or "").strip().lower()
    if _FEATURE.search(text or ""):   # 含高密度特徵(IUL_V5_2026 / 64/071,227 / qwen2.5:3b)→ 保留
        return False
    return norm in STOP_WORDS_SET


def _ollama_chat(ollama_url: str, model: str, context: str, query: str, timeout: int):
    """§8:本地 Ollama /api/chat。正文在 context 參數內,不 log。"""
    sys_prompt = ("你是 GOAA 本地助手。只根據提供的本地記憶片段回答;"
                  "若記憶不足以回答,直接說「沒有足夠本地記憶支持回答」,不要編造。")
    user_msg = f"本地記憶片段:\n{context}\n\n問題:{query}"
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": sys_prompt},
                     {"role": "user", "content": user_msg}],
        "stream": False,
    }).encode("utf-8")
    req = urllib.request.Request(f"{ollama_url}/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
    return (data.get("message") or {}).get("content", "")


def exec_rag_context_fetch(params: dict) -> dict:
    """
    C2 主流程(spec §3)。回 answer + sources metadata + redaction flags。
    正文只進內存,函數返回前 best-effort cleanup(§5/§11)。
    """
    t0 = time.time()
    query = params.get("query_text", "")
    top_k = int(params.get("top_k", 3))
    max_chunks = int(params.get("max_chunks", 3))
    min_text_len = int(params.get("min_text_len", 20))
    max_context_chars = int(params.get("max_context_chars", 2000))
    distance_threshold = params.get("distance_threshold")  # 可選
    ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
    embed_model = os.environ.get("EMBED_MODEL", "nomic-embed-text")
    chat_model = params.get("chat_model", "qwen2.5:3b")
    timeout = int(params.get("timeout", 120))

    query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]  # §7 記 hash 不記原文
    chunk_ids = []
    sources = []
    raw_chunks = []  # §5 正文只在此區域變數
    context_str = ""

    conn = None
    try:
        # 1. query 嵌入(復用 _embed)
        vec = _embed(query, ollama_url, embed_model, timeout)
        if isinstance(vec, list) and vec and isinstance(vec[0], list):
            vec = vec[0]
        vec_literal = "[" + ",".join(str(x) for x in vec) + "]"

        # 2. pgvector top-k:取 id + text_redacted 正文(§4 正文進內存)
        conn = _pg_connect()
        cur = conn.cursor()
        cur.execute(
            f"""SELECT id, session_id, msg_id, role,
                       length(text_redacted) AS text_len,
                       round((embedding <=> %s::vector)::numeric, 4) AS cosine_distance,
                       text_redacted
                FROM {TARGET_TABLE}
                ORDER BY embedding <=> %s::vector
                LIMIT %s""",
            (vec_literal, vec_literal, top_k),
        )
        rows = cur.fetchall()
        cur.close()

        # 3. 短句污染過濾(§10) + distance 門檻 + 組 context(§9 保守)
        kept = 0
        for (cid, sid, mid, role, text_len, dist, text) in rows:
            if distance_threshold is not None and dist is not None and float(dist) > float(distance_threshold):
                continue
            if _is_noise(text, text_len, min_text_len):
                continue
            if kept >= max_chunks:
                break
            raw_chunks.append(text)   # 正文進內存
            chunk_ids.append(str(cid))
            sources.append({"chunk_id": str(cid), "session_id": str(sid), "msg_id": str(mid),
                            "role": role, "text_len": text_len, "distance": float(dist) if dist is not None else None})
            kept += 1

        context_str = "\n---\n".join(raw_chunks)[:max_context_chars]  # §9 截斷

        # 4. 餵本地 LLM(§8);若 context 空 → 安全回答不編造(§9)
        if not context_str.strip():
            answer = "沒有足夠本地記憶支持回答。"
        else:
            answer = _ollama_chat(ollama_url, chat_model, context_str, query, timeout)

        result = {
            "status": "success",
            "answer": answer,
            "sources": sources,                       # §12 只 metadata
            "model": chat_model,
            "redaction": {"raw_context_returned": False,
                          "raw_chunks_logged": False,
                          "raw_prompt_logged": False},
            # §7 審計:記 metadata 不記正文
            "audit": {"query_hash": query_hash, "chunk_ids": chunk_ids,
                      "model_name": chat_model, "answer_len": len(answer),
                      "duration_ms": int((time.time() - t0) * 1000),
                      "redaction_status": "ok"},
        }
        return result

    except Exception as e:
        # §11 異常脫敏:絕不 log raw exception(可能含 prompt/正文)
        log.error("C2 execution failed", extra={
            "error_type": type(e).__name__,
            "chunk_ids": chunk_ids,
            "model": chat_model,
        })
        return {
            "status": "failed",
            "answer": "",
            "sources": [],
            "model": chat_model,
            "redaction": {"raw_context_returned": False, "raw_chunks_logged": False, "raw_prompt_logged": False},
            "audit": {"query_hash": query_hash, "chunk_ids": chunk_ids,
                      "model_name": chat_model, "answer_len": 0,
                      "error_type": type(e).__name__,
                      "duration_ms": int((time.time() - t0) * 1000),
                      "redaction_status": "ok"},
        }
    finally:
        # §5/§11 best-effort cleanup —— 降低正文滯留窗口(非加密級擦除/非保證物理清零)
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass
        raw_chunks = None
        context_str = None
        gc.collect()
