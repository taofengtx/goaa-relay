#!/usr/bin/env python3
"""
GOAA C2 — memory_context_fetch.py (V5.3 Aika Memory Context Fetch)
部署: /opt/goaa/workers/memory_context_fetch.py

對照 docs/business/GOAA_C2_DATA_PRIVACY_SPEC.md(重定位版,20 節)實作。

定位:Aika 執行任務前的本地記憶上下文補給層。
  - 純檢索補給,不經 LLM 摘要(§16)
  - internal worker,不開放 /rag/chat(§17)
  - 優先長 chunk,強過濾 ChatML 噪音(§7/§8)
  - chunk 正文僅限同信任域本地執行層內存(§3/§5/§6)
  - 不落盤/不入 log/不回前端/不出本機/不發雲端
  - best-effort cleanup(§14,非物理清零)

復用(規範 #27/#24):from embed_worker import _embed, _pg_connect
表: qwenpaw_memory_chunks  欄位: text_redacted  算子: <=>
"""

import os
import re
import gc
import time
import hashlib
import logging

from embed_worker import _embed, _pg_connect

log = logging.getLogger("c2.memory_context_fetch")

TARGET_TABLE = "qwenpaw_memory_chunks"

# §8 短句污染雙網閘
STOP_WORDS_SET = {"好", "收到", "嗯", "ok", "okay", "thanks", "thank you", "yes", "no",
                  "是", "對", "可以", "ok。", "好的"}
# §8 ChatML wrapper 噪音(角色標記)
_CHATML = re.compile(r'<\|?(im_start|im_end|system|user|assistant|endoftext)\|?>', re.I)
# §9 高密度特徵(短但有信息 → 保留):數字/下劃線/冒號/斜線/大寫縮寫
_FEATURE = re.compile(r'[0-9_:/]|[A-Z]{2,}')


def _is_noise(text: str, text_len: int, min_text_len: int) -> bool:
    """§8/§9:ChatML 噪音 + 短句 stop words 過濾;高密度短文本保留。"""
    if not text:
        return True
    if _CHATML.search(text):                 # ChatML wrapper → 噪音
        return True
    if text_len >= min_text_len:             # 夠長 → 保留
        return False
    if _FEATURE.search(text):                # 短但含高密度特徵 → 保留(模型名/端口/IP/編號)
        return False
    return text.strip().lower() in STOP_WORDS_SET


def exec_memory_context_fetch(params: dict) -> dict:
    """
    C2 主流程(spec §4)。回 context(供 Aika 注入內存)+ 審計 metadata。
    正文只進內存,函數返回前 best-effort cleanup(§14)。

    params:
      task_keywords: str   — Aika 的任務關鍵詞(用於檢索)
      top_k: int=10        — §7 撈 8-12
      max_chunks: int=6    — §11
      min_text_len: int=20 — §8
      max_context_chars: int=4000 — §11
      session_window: int=0 — §10(第一版預設關,0=不聚合)
    """
    t0 = time.time()
    enabled = os.environ.get("ENABLE_MEMORY_FETCH", "false").lower() == "true"  # §18
    keywords = params.get("task_keywords", "")
    top_k = int(params.get("top_k", 10))
    max_chunks = int(params.get("max_chunks", 6))
    min_text_len = int(params.get("min_text_len", 20))
    max_context_chars = int(params.get("max_context_chars", 4000))
    distance_threshold = params.get("distance_threshold")
    ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
    embed_model = os.environ.get("EMBED_MODEL", "nomic-embed-text")
    timeout = int(params.get("timeout", 120))

    kw_hash = hashlib.sha256(keywords.encode("utf-8")).hexdigest()[:16]  # §12 記 hash 不記原文

    # §18 disable 開關:返回空 context,Aika 退回無補給正常執行
    if not enabled:
        return {"status": "disabled", "context": "", "sources": [],
                "audit": {"task_keywords_hash": kw_hash, "execution_mode": "memory_context_fetch",
                          "selected_chunk_ids": [], "context_char_count": 0,
                          "filter_stats": {}, "duration_ms": int((time.time() - t0) * 1000)}}

    selected_chunk_ids, session_ids, msg_ids = [], [], []
    sources = []
    raw_chunks = []          # §5 正文只在此區域變數
    context_str = ""
    filter_stats = {"total_fetched": 0, "chatml_filtered": 0, "stopword_filtered": 0, "kept": 0}

    conn = None
    try:
        # 1. keywords 嵌入(復用 _embed)
        vec = _embed(keywords, ollama_url, embed_model, timeout)
        if isinstance(vec, list) and vec and isinstance(vec[0], list):
            vec = vec[0]
        vec_literal = "[" + ",".join(str(x) for x in vec) + "]"

        # 2. pgvector top-k:取 id + text_redacted(§4 正文進內存),長度降序輔助長 chunk 優先
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
        filter_stats["total_fetched"] = len(rows)

        # 3. 過濾(§8) + §7 長 chunk 優先(同距離下長的先)+ distance 門檻
        candidates = []
        for (cid, sid, mid, role, text_len, dist, text) in rows:
            if distance_threshold is not None and dist is not None and float(dist) > float(distance_threshold):
                continue
            if _CHATML.search(text or ""):
                filter_stats["chatml_filtered"] += 1
                continue
            if _is_noise(text, text_len, min_text_len):
                filter_stats["stopword_filtered"] += 1
                continue
            candidates.append((cid, sid, mid, role, text_len, dist, text))

        # §7 長 chunk 優先:在相關性(已按 distance 排序)基礎上,優先取長的
        candidates.sort(key=lambda r: (-(r[4] or 0)))   # text_len 降序

        # 4. 組裝 context(§11 保守,max_chunks + max_context_chars)
        for (cid, sid, mid, role, text_len, dist, text) in candidates[:max_chunks]:
            raw_chunks.append(text)
            selected_chunk_ids.append(str(cid))
            session_ids.append(str(sid))
            msg_ids.append(str(mid))
            sources.append({"chunk_id": str(cid), "session_id": str(sid), "msg_id": str(mid),
                            "role": role, "text_len": text_len,
                            "distance": float(dist) if dist is not None else None})
        filter_stats["kept"] = len(raw_chunks)

        context_str = "\n---\n".join(raw_chunks)[:max_context_chars]   # §11 截斷
        context_sha256 = hashlib.sha256(context_str.encode("utf-8")).hexdigest()  # §13 本地審計指紋

        # §4 context 返回供 Aika 注入內存(同信任域內部補給,非回前端)
        return {
            "status": "success",
            "context": context_str,            # 正文補給,Aika 用完即丟(§3/§6)
            "sources": sources,                # §12 metadata
            "audit": {
                "task_keywords_hash": kw_hash,  # §12 不記原文
                "selected_chunk_ids": selected_chunk_ids,
                "session_ids": session_ids,
                "msg_ids": msg_ids,
                "context_char_count": len(context_str),
                "context_sha256": context_sha256,  # §13 本地指紋,雲端無正文不可獨立驗證
                "filter_stats": filter_stats,
                "execution_mode": "memory_context_fetch",
                "duration_ms": int((time.time() - t0) * 1000),
            },
        }

    except Exception as e:
        # §15 異常脫敏:絕不 log raw exception(可能含正文)
        log.error("C2 memory_context_fetch failed", extra={
            "error_type": type(e).__name__,
            "selected_chunk_ids": selected_chunk_ids,
            "filter_stats": filter_stats,
        })
        return {
            "status": "failed",
            "context": "",
            "sources": [],
            "audit": {"task_keywords_hash": kw_hash, "execution_mode": "memory_context_fetch",
                      "selected_chunk_ids": selected_chunk_ids, "context_char_count": 0,
                      "filter_stats": filter_stats, "error_type": type(e).__name__,
                      "duration_ms": int((time.time() - t0) * 1000)},
        }
    finally:
        # §14 best-effort cleanup —— 降低正文滯留窗口(非物理清零/非保證清零)
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass
        raw_chunks = None
        context_str = None
        gc.collect()
