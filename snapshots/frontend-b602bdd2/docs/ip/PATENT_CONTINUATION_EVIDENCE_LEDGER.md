# GOAA Patent Continuation Evidence Ledger

> **狀態**:長期技術證據文檔。為 GOAA provisional patent specification 一年後轉正式 non-provisional 申請,準備技術證據鏈。
> **原則**:技術語言,非商業話術。**不寫死任何未核驗的 USPTO 專利號。** 不寫 secret。

---

## 0. 目的

GOAA V4.2 → V5.2 的演進,**不是普通 SaaS 功能堆疊**,而是一個分布式 AI Runtime OS,從雲端調度、邊緣 worker、任務框架、本地 RAG、pgvector、Local Console、Model/Skill/Agent Registry 逐步形成的技術系統。本文件記錄技術改進證據,供未來正式專利 claim 支撐。

## 0.1 Provisional Application 已提交(USPTO 真實記錄)

> 依據 USPTO Electronic Acknowledgement Receipt(2026-05-21 已歸檔於 `docs/ip/`)。以下為收據真實信息,**非傳聞、非編造**。注意:此為 **provisional application(臨時申請)已提交**,**尚未授權**(Patent # 為空),不得表述為「已獲專利」。

| 項目 | 值 |
|---|---|
| Application # | **64/071,227** |
| Confirmation # | 1251 |
| Patent Center # | 76509658 |
| Receipt Date | 2026-05-21 02:30:54 PM ET |
| Application Type | Utility — Provisional Application under 35 USC 111(b) |
| Title of Invention | **Distributed AI Runtime Operating System with Physical Execution Capability** |
| First Named Inventor | Tao Feng |
| Filing Date | (待 Filing Receipt 正式核發) |

提交文件(各帶 USPTO SHA-512,見收據第 2 頁):
- generatedADS76509658.pdf(Application Data Sheet,5 頁)
- GOAA_Provisional_Patent_Draft_101_Technical_Rewrite_v4_Filing_Draft.pdf(Specification,11 頁)
- GOAA_AI_Utility_Provisional_Drawings_FIGS_1-5_PORTRAIT_US_LETTER.pdf(Drawings,5 頁)

> **後續**:provisional 自 receipt date 起 12 個月內,須提交 non-provisional 以主張優先權。本證據鏈即為該 non-provisional 申請準備技術支撐。發明名稱中的 "Distributed AI Runtime Operating System with Physical Execution Capability" 與本文件第 1-2 節的技術演進/計算系統改進**直接對應**。

## 1. 技術架構演進時間線

| 版本 | 技術里程碑(technical improvement) |
|---|---|
| **V4.2** | 雲端 Router / Worker 通信基礎(cloud router–worker communication) |
| **V4.5** | aika-core-01 加入 Worker Network,成為 AiKa-Box Pro Alpha(edge node joins worker network) |
| **V5.0** | 真實 LLM 接通(live LLM integration) |
| **V5.1** | LLM dispatch_task → worker 執行 → LLM 回報閉環(LLM-driven task dispatch loop) |
| **V5.2.B** | QwenPaw corpus → Ollama embedding → pgvector → top-k 閉環(vectorized memory retrieval pipeline) |
| **V5.2.C** | Local Task Runner + Local Runtime Console(local-state task execution + console) |
| **V5.3** | Model / Skill / Agent Registry(resource abstraction layer) |
| **V5.4** | External Agent Adapter(cloud agent integration) |
| **V5.5** | Provider Workspace Agent Invocation(hybrid agent orchestration) |

## 2. 計算系統改進證據(技術語言)

避免「商業流程自動化」表述。以下為系統性技術改進:

1. **邊緣計算節點本地執行**(edge worker local execution)
2. **本地 runtime console 與 worker daemon 解耦**(decoupled console / daemon — console failure does not affect task execution)
3. **task_result / runtime log / ledger 形成可審計執行軌跡**(auditable execution trace)
4. **本地 RAG 檢索不返正文的安全隔離機制**(retrieval returns metadata + distance only, no source text)
5. **Model / Skill / Agent 三註冊表形成可調度計算資源抽象層**(schedulable resource abstraction)
6. **Cloud / Local Agent Router 形成混合雲邊協同**(hybrid cloud-edge routing)
7. **worker_secrets.env 與前端 console 物理隔離**(secret store physically isolated from frontend)
8. **allowlist task runner 阻斷任意 shell 執行**(allowlist execution, no arbitrary shell)
9. **pgvector memory store 與本地 Ollama embedding 形成本地記憶能力**(local memory capability via local embedding + vector store)

## 3. 可實現性證據(每個 milestone 應記錄)

每個里程碑記錄以下欄位作為 reduction-to-practice 證據:

```
file path / version / SHA256 / MD5 / systemd service / port /
input-output schema / task_result 示例 / log path / test result /
是否觸碰 secret / 是否返回正文 / 是否有 rollback 方案
```

### 已記錄的可實現性證據(V5.2.B / V5.2.C-1)

| 項目 | 證據 |
|---|---|
| embed_worker.py(分塊版) | NormMD5 `04633802e635ee26b9b3a8a4581faf7d`;路徑 `/opt/goaa/workers/embed_worker.py` |
| task_runner.py | NormMD5 `ec9fd0e0d123171ce7a7e3f5c4130147`;路徑 `/opt/goaa/workers/task_runner.py` |
| topk_query.py | NormMD5 `4850e348751c667b84e408f392c1777b` |
| corpus_all.jsonl | SHA256 `151bbb7599bf89b8738ec8d2cf9dd6f985e115bab86a03a2748d2cce8a494bd7`(1080 lines) |
| 嵌入維度 | 768(nomic-embed-text) |
| 入庫記錄 | full corpus 1080 → 分塊後 1165 chunks 入庫;dim768 全綠;13 sessions |
| top-k 測試 | passed(query → embedding → pgvector top-k → metadata 排序正確) |
| 是否觸碰 secret | 否(secret 由 Tao 親手經 worker_secrets.env 注入,只 SET/LEN 驗證) |
| 是否返回正文 | 否(檢索只返 metadata + distance) |
| rollback | corpus 源頭保留,可 TRUNCATE 重灌;每版有指紋可回溯 |

## 4. Golden Baseline 證據

納入證據鏈的 V5.2.B Golden Baseline R1:

- **Release doc**:`docs/releases/V5_2_B_GOLDEN_BASELINE_R1.md`(git tag `v5.2b-golden-r1`)
- **embed_worker.py 指紋**:見上表
- **corpus_all.jsonl 指紋**:見上表
- **qwenpaw_memory_chunks schema**:id / session_id / msg_id / role / ts / text_hash / text_redacted / embedding vector(768) / metadata jsonb / source / created_at / updated_at;UNIQUE(session_id, msg_id);3 索引
- **pgvector**:0.8.0
- **top-k similarity query**:passed
- **full corpus 入庫**:1080 → 1165 chunks
- **exec_embed_corpus_full**:作為 task framework 的正式化路徑(Worker Runtime task)

## 5. Patent-safe Wording(用語規範)

**避免**(商業話術):幫保險人員賺錢、自動處理商業訂單、分潤、代理人佣金、客戶營銷自動化

**改用**(技術語言):
- distributed runtime execution
- edge worker orchestration
- local-state task execution
- vectorized memory retrieval
- tool invocation ledger
- local/cloud agent routing
- secure local runtime boundary
- model/skill/agent resource abstraction

## 6. 後續維護

- 每個新版本 / .deb 發布,在本 ledger 補一行可實現性證據(含指紋、路徑、測試結果、是否觸碰 secret/正文、rollback)
- 對應 future claim support,但**不在本文件斷言具體 claim**(claim 由專利律師起草)
- **永不寫死未核驗 USPTO 號**;需引用時只寫 "GOAA provisional patent specification"

---

*GOAA Patent Continuation Evidence Ledger — 技術證據,非商業話術,無專利號*
