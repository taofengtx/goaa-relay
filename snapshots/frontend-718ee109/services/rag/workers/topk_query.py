#!/usr/bin/env python3
"""
GOAA Worker Runtime V5.2.C-1 — exec_topk_query_verify
部署: /opt/goaa/workers/topk_query.py
角色: top-k 檢索驗證任務(被 task_runner dispatch)。

定位:驗證 query_text → embedding → pgvector top-k → task_result 鏈路。
      本階段不做真 RAG 上下文注入,不返正文。

安全鐵律:
  - 不返 text_redacted / corpus 原文 / secret / API key / password / token。
  - query_text 只回 hash(query_text_hash),不回原文。
  - PG / Ollama 連線資訊只從環境變數讀(由 Tao 親手經 worker_secrets.env 注入)。

真 RAG 檢索(回正文/正文落地策略)= C2 exec_rag_context_fetch,另案設計。
"""

import os
import hashlib

# 與 embed_worker 同目錄,共用 _embed / _pg_connect 邏輯
from embed_worker import _embed, _pg_connect


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def exec_topk_query_verify(params: dict) -> dict:
    """
    params(來自 task JSON,不含 secret):
      query_text   : 查詢文字(會被嵌入;只回 hash,不回原文)
      top_k        : 取前 K 筆(預設 5)
      target_table : 預設 qwenpaw_memory_chunks
      model        : 預設 env EMBED_MODEL 或 nomic-embed-text
    回統計 + matches(id/session_id/msg_id/role/text_len/dim/distance),不返正文。
    """
    query_text = params["query_text"]
    top_k = int(params.get("top_k", 5))
    target_table = params.get("target_table", "qwenpaw_memory_chunks")
    model = params.get("model") or os.environ.get("EMBED_MODEL", "nomic-embed-text")
    ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")

    # 1. 嵌入 query(同一個 _embed,確保同向量空間)
    qvec = _embed(query_text, ollama_url, model)
    qdim = len(qvec)

    # 2. pgvector top-k(只 SELECT 中繼欄位,不取 text_redacted)
    conn = _pg_connect()
    cur = conn.cursor()
    matches = []
    try:
        # 用參數化查詢,query 向量以參數傳入(不拼字串)
        vec_literal = "[" + ",".join(str(x) for x in qvec) + "]"
        cur.execute(
            f"""
            SELECT id, session_id, msg_id, role,
                   length(text_redacted) AS text_len,
                   vector_dims(embedding) AS dim,
                   round((embedding <=> %s::vector)::numeric, 4) AS cosine_distance
            FROM {target_table}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (vec_literal, vec_literal, top_k),
        )
        for row in cur.fetchall():
            matches.append({
                "id": row[0],
                "session_id": row[1],
                "msg_id": row[2],
                "role": row[3],
                "text_len": row[4],     # 只回長度,不回正文
                "dim": row[5],
                "distance": float(row[6]),
            })
    finally:
        cur.close()
        conn.close()

    return {
        "stats": {
            "query_text_hash": _sha256(query_text),   # 只回 hash,不回 query 原文
            "query_embedding_dim": qdim,
            "top_k": top_k,
            "rows_returned": len(matches),
            "matches": matches,
        }
    }
