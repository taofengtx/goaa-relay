# GOAA C2 Spec — Aika Memory Context Fetch(本地記憶上下文補給層)

> **狀態**:設計文檔(V5.3 C2,重定位版)。僅設計,不寫代碼、不部署、不重啟 Console、不碰 secret、不讀 RAG 正文。
> **重定位拍板**:C2 從「RAG Chat」正式重定位為 **Aika 執行任務前的本地記憶上下文補給層**。第一版採純檢索補給(方案甲),不經 qwen2.5:3b 摘要,不優先開放 /rag/chat。

---

## 1. Purpose

C2 為 Aika(QwenPaw 執行層)在執行任務前,提供「本地項目記憶上下文」。Aika 接到任務 → 執行前查詢相關項目脈絡(歷史決策/規範/devlog/架構)→ 注入本地執行上下文 → 對齊後執行。C2 ≠ 用戶聊天功能,≠ RAG Chat。

## 2. C2 重定位:從 RAG Chat 到 Aika Memory Context Fetch

| 維度 | 舊(RAG Chat) | 新(Memory Context Fetch) |
|---|---|---|
| 目標 | 生成一段回答 | 撈相關項目脈絡注入執行層 |
| 經 LLM | qwen2.5:3b 生成 | 不經 LLM(避免 3B 轉述失真) |
| 撈什麼 | 最相似 3 片段 | 優先長 chunk + session 脈絡 |
| 用戶 | admin/provider 問 | Aika 內部調用 |
| 入口 | /rag/chat | 內部 worker 函數 exec_memory_context_fetch |

理由:Aika 需要準確的歷史細節(模型名/端口/IP/決策),3B 摘要會丟失;原文 chunk 比摘要更接近「真實記憶」。

## 3. Internal Memory Hydration Boundary

原始 chunk 正文可以進入同一信任域內的本地執行層(Aika)內存上下文,用於執行前的臨時記憶補給。這不等於返回前端。但必須嚴守 §6 八條負約束。

## 4. Data Flow

```
Aika 接到任務(task_keywords)
→ exec_memory_context_fetch(task_keywords)
→ embedding(復用 _embed,nomic-embed-text)
→ pgvector top-k(8-12,長 chunk 優先)
→ 過濾 ChatML 噪音 + 無信息短句(§8)
→ session 聚合(§10)
→ 組裝 context(max_context_chars 內,§11)
→ 注入 Aika 本地執行內存上下文(§3)
→ Aika 對齊後執行任務
→ best-effort cleanup(§14)
```
全程不經 LLM 摘要(§16),不落盤,不回前端。

## 5. Trust Domain Definition

同信任域:aika-core-01 本機內的 worker 執行層(Aika/QwenPaw)+ 其 Python 進程內存。chunk 正文限於此域內臨時使用。

信任域外(正文絕不可達):前端瀏覽器、task_result 檔、runtime log、journal、雲端、外部 API、/logs/recent、任何落盤位置。

## 6. Eight Negative Constraints(八條負約束)

chunk 正文補給給 Aika 時,必須保證:
1. 不落盤
2. 不入 task_result
3. 不入 runtime log
4. 不入 journal
5. 不回前端
6. 不進 browser console
7. 不發送到雲端 / 外部 API
8. 不進 /logs/recent

Aika 使用後釋放引用,做 best-effort cleanup(§14)。

## 7. Retrieval Strategy(服務「執行記憶補給」非問答)

- 優先長 chunk(項目決策/規範/devlog/checklist/architecture 多在長內容)
- 強過濾 ChatML 噪音(實測 1165 chunks 中 249 條 <20 字多為角色 wrapper)
- top_k 支持 8-12(脈絡要完整,非單片段)
- 支持 max_context_chars
- 支持 session 聚合(§10)
- distance_threshold 可選

## 8. Noise Filter / STOP_WORDS_SET

```
STOP_WORDS_SET = {"好", "收到", "嗯", "ok", "okay", "thanks", "thank you", "yes", "no"}
```
- ChatML wrapper(<|im_start|> 等角色標記)→ 過濾
- 若 text_len < min_text_len 且 normalized_text 命中 STOP_WORDS_SET → 過濾
- filter_stats 記錄過濾了多少(審計用,§12)

## 9. High-density Short Text Preservation

短但高信息密度內容保留(對執行對齊有價值):
- 模型名(qwen2.5:3b)、端口(5188)、IP(100.114.37.90)
- 任務編號、配置名、案件參考號(case_ref_id)、配置參考(config_ref)
- 判定:含數字 / 下劃線 / 冒號 / 斜線 / 大寫縮寫 → 保留

## 10. Session Aggregation

避免只拿碎片:命中 chunk 所在 session 的相鄰 chunk 可一併撈入,還原對話脈絡。第一版可選同 session_id 的前後 N 條。配置項:session_window。

## 11. Context Size Limit

- top_k_default(8-12)
- max_chunks
- max_context_chars(配置項,保守值)
- 每 chunk 可截斷
- 超限時優先保留長 chunk + 高相關性

## 12. Audit Schema

task_result 只記:task_keywords_hash、query_hash、selected_chunk_ids、session_ids、msg_ids、text_len、distance、context_char_count、filter_stats、context_sha256、duration_ms、execution_mode=memory_context_fetch。

不記:原始 chunk 正文、拼接後 context、Aika 最終 prompt、原始 query 明文、任何 RAG 正文。

## 13. context_sha256 Boundary

context_sha256 是「本地被選中 context 的審計指紋」,用於本地可追溯與未來對賬。

> 誠實邊界:雲端在沒有正文的情況下不能反推正文,也不能僅憑 hash 獨立驗證正文內容。不得寫成「雲端 100% 確認正文一致」。

## 14. Best-effort Memory Cleanup

Aika 使用 context 後:clear list references、del temporary variables、optional gc.collect()。

> 誠實聲明:此為降低內存滯留窗口的工程手段。不得寫成物理清空內存 / 軍工級銷毀 / 保證清零 / 100% 防止內存殘留。

## 15. Logging / Exception Redaction

- 禁止 logger.exception(e)、logger.error(str(e))、打印含正文/context 的 traceback / request body
- 允許:記異常類型、chunk_ids、filter_stats、duration、sanitized error code

## 16. Why No LLM Summary in V1

3B 模型摘要會丟失關鍵細節(模型名/端口/IP/決策),且實測 qwen2.5:3b 拿短 chunk 即說「不足」。純檢索原文比摘要更接近「真實記憶」,更利執行對齊。LLM 摘要版留後續單獨設計。

## 17. Why No /rag/chat in V1

C2 第一版服務 Aika 內部記憶補給,非用戶問答。/rag/chat(用戶聊天)作為後續受控功能單獨設計,第一版不優先開放。

## 18. Disable / Rollback Switch

- ENABLE_MEMORY_FETCH=false 時 exec_memory_context_fetch 返回空 context(Aika 退回無記憶補給的正常執行)
- C2 失敗不得影響 Console health / systemd 自啟 / 既有 /rag/stats / Aika 主流程

## 19. Security Checklist

- [ ] raw chunk text never returned to frontend
- [ ] raw chunk text never written to task_result
- [ ] raw context never logged
- [ ] raw query not logged as plain text
- [ ] hashes recorded instead
- [ ] selected_chunk_ids / distance / text_len recorded
- [ ] internal worker only, not /rag/chat
- [ ] no LLM summary in V1
- [ ] no cloud send
- [ ] ChatML noise filtered
- [ ] stop words filter documented
- [ ] high-density short text preserved
- [ ] session aggregation documented
- [ ] best-effort cleanup (not physical zeroization)
- [ ] context_sha256 boundary honest (no cloud 100% claim)
- [ ] exception logging sanitized
- [ ] disable switch defined
- [ ] no secret touched

## 20. Open Questions Before Code

1. top_k / max_context_chars / session_window 保守值(實測後定)
2. ChatML wrapper 的精確過濾規則(正則 or 標記表)
3. STOP_WORDS_SET 是否擴充
4. context 注入 Aika 的具體機制(函數返回 vs 寫入 Aika 上下文物件)
5. filter_stats 記哪些維度

---

*GOAA C2 Spec — V5.3 設計文檔 — Aika Memory Context Fetch,純檢索補給,不經 LLM,先設計不寫碼*
