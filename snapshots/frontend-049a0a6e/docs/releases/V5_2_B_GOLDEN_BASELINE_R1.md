# GOAA Worker Runtime V5.2.B Golden Baseline R1

**完成時間**: 2026-06-02 PT
**節點**: aika-core-01 / AiKa-Box Pro Alpha
**狀態**: 乾淨、可驗證、零 secret 洩漏的最小閉環,正式封存。

---

## 1. Golden Baseline 名稱

GOAA Worker Runtime V5.2.B Golden Baseline R1

## 2. 核心閉環

```
QwenPaw corpus (corpus_all.jsonl, 1080 lines)
  → aika-core-01 / AiKa-Box Pro Alpha
  → embed_worker.py
  → Ollama nomic-embed-text
  → 768 維 embedding
  → DO PostgreSQL pgvector
  → public.qwenpaw_memory_chunks
  → limit=3 real insert
  → top-k similarity query passed
```

## 3. 核心文件

| 文件 | 路徑 | 備註 |
|---|---|---|
| Worker | `/opt/goaa/workers/embed_worker.py` | 嵌入 + 寫入 task |
| Corpus | `/opt/goaa/workers/corpus_all.jsonl` | 1080 行,內容不外洩 |
| Secrets | `/etc/goaa/worker_secrets.env` | **僅記錄存在與權限要求,不記錄內容**;chmod 600,Tao 親手建立 |
| Table | `public.qwenpaw_memory_chunks` | DO PostgreSQL,vector(768) |

## 4. 指紋

```
embed_worker.py
  SHA256: 53e1a49806bd04f74c3c2e728dbce10c799b2a82be73d0ae2a92c90063b53a1e
  MD5   : 96c38a6c8ce62b035e4f1be2d271b8a3   (120s timeout 版)

corpus_all.jsonl
  SHA256: 151bbb7599bf89b8738ec8d2cf9dd6f985e115bab86a03a2748d2cce8a494bd7
  size  : 564K / 1080 lines
```

## 5. Runtime 環境

```
host           : aika-core-01
role           : AiKa-Box Pro Alpha
Ollama         : 0.24.0
model          : nomic-embed-text
embedding dim  : 768
Python         : 3.14.4
psycopg2       : OK (/opt/goaa/venv)
worker service : goaa-worker-agent.service active
```

## 6. 資料庫狀態

```
PostgreSQL : postgres:16-alpine (container goaa-postgres, 5935b1d86140)
pgvector   : 0.8.0 (已存在,無需安裝/編譯/CREATE EXTENSION)
table      : public.qwenpaw_memory_chunks
DB user    : goaa_rag (專用 RAG 帳號,非生產主用戶 goaa)
test rows  : 3
top-k      : passed
```

表結構:`id, session_id, msg_id, role, ts, text_hash, text_redacted, embedding vector(768), metadata jsonb, source, created_at, updated_at`,`UNIQUE(session_id, msg_id)`,3 索引(session_id / text_hash / metadata)。

## 7. 已驗證測試

- ✅ check-env passed(7 變數全 SET,只輸出 LEN)
- ✅ dry-run limit=3 passed(processed=3, failed=0, 0.82s)
- ✅ real insert limit=3 passed(inserted=3, 1.04s)
- ✅ count=3 passed(0 → 3)
- ✅ vector_dims=768 passed(3 筆全 768)
- ✅ top-k similarity query passed(id=1 自身 distance=0.0000,另兩筆 0.4314 / 0.4964 遞增)

## 8. 安全規則(本 baseline 鐵律)

- secrets 僅由 Tao 親手處理
- 不 cat secrets.env
- 不 printenv
- 只允許 SET / LEN 輸出,不輸出 value
- QwenPaw / Aika 不得接觸 secret
- 使用專用 DB 用戶 `goaa_rag`,不改生產主用戶 `goaa` 密碼
- corpus 正文不上傳雲對話

## 9. Golden 後禁止事項

- ❌ 不手動跑全量 1080 import
- ❌ 不在聊天中暴露 corpus 正文
- ❌ 不在無新指紋的情況下改 embed_worker.py
- ❌ 不讓 Aika 接觸 worker_secrets.env
- ❌ 不在 Worker Runtime task 框架外跑全量 import

## 10. 下一階段

**V5.2.C / First Real Worker Runtime Task**

```
task name   : exec_embed_corpus_full
worker_id   : aika-core-01
full corpus : 1080
task_id     : required
credits     : placeholder required
devlog      : required
```

全量 1080 不手動跑,作為 Worker Runtime OS V5.2 第一個正式任務執行。

## 11. Git

```
tag    : v5.2b-golden-r1
commit : docs(release): add V5.2.B golden baseline R1
```

---

*GOAA Project — V5.2.B Golden Baseline R1 — 2026-06-02 PT*
*閉環驗證:corpus → embed → pgvector → top-k,全程零 secret 洩漏。*
