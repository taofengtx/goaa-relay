# GOAA Workflow Graph Layer — V5.4 設計規範

> **版本**：v0.2 Implementation-Ready Design Spec
> **階段**：設計文檔補強階段（**不寫代碼、不部署、不重啟、不改 systemd、不碰 `/etc/goaa`、不讀 secret、不接外部 API**）
> **定位**：接續 `MODEL_SKILL_AGENT_REGISTRY.md` §142-216 已有的 Workflow Graph 骨架（📐 文檔級設計，代碼未實作），把 12 Node Types 從「只有名稱」補成可實作的 schema + interface。
> **狀態標註**：✅ 已驗證（有 repo/commit/grep 證據）/ 📐 文檔級設計（代碼未驗）/ 🆕 本 spec 新設計提案 / 🔲 待定。
> **本文件為設計規範，非 production ready，未實現。** v0.1 design baseline established → v0.2 補 schema/狀態機/adapter/review hold/capacity/visibility。

---

## 0. 定位：Workflow Graph 是產品功能，不是開發流程

| | `workflow.md`（開發流程） | **Workflow Graph Layer（本 spec）** |
|---|---|---|
| 是什麼 | GOAA 團隊**開發 GOAA 本身**的 SOP | **賣給 Provider / Client 的產品功能** |
| 對象 | 內部開發 | Provider / Client |
| 例子 | feature 分支 → CI → AiKa-Test | OCR → 提取 → RAG → 合規 → Provider 審核 → 匯出 |

> 本 spec 寫**後者**。`workflow.md` 7 步閉環是開發 SOP，**不是** Graph 節點，不混用。

---

## 1. Graph 模型

```
nodes[]            # 處理步驟（§2 schema）
edges[]            # 節點連接 + 條件分支（§3 Edge schema，默認不傳正文）
execution_target   # cloud | local | auto
review_gates[]     # 哪些 edge 需 Review Hold（§5）
logs               # 每節點審計（脫敏，過 C2 §6/§15）
```

**原則：** 每 node 有 input/output/params schema + risk + review；Graph 可審計（正文不落盤，C2 §6）；HIGH/CRITICAL node 後可掛 Review Hold（§5）。

---

## 2. Standard Node Schema（🆕 schema proposal，非實作）

> 每 Graph Node 統一 schema。**這是 schema proposal，不是 production implementation，不寫代碼。**

```json
{
  "node_id": "string",
  "node_type": "input | ocr | extraction | rag_query | llm_analysis | compliance_check | decision | provider_review | form_draft | export | audit | sync",
  "display_name": "string",
  "input_schema": {},
  "output_schema": {},
  "params_schema": {},
  "risk_level": "LOW | MEDIUM | HIGH | CRITICAL",
  "requires_review": true,
  "execution_target": "cloud | local | auto",
  "adapter": "goaa_task_runner | local_aikabox_executor | cloud_agent_executor | comfyui_adapter | external_api_adapter",
  "timeout_sec": 60,
  "retry_policy": { "max_retries": 0, "retry_backoff_sec": 0 },
  "review_gate": { "enabled": true, "gate_type": "provider_review | admin_review | compliance_review" },
  "audit_policy": { "store_inputs": false, "store_outputs": false, "store_hashes": true, "redact_raw_text": true }
}
```

### 2.1 12 Node Types — risk / review / params 方向（🆕）

| # | Node Type | risk | review | params 方向 |
|---|---|---|---|---|
| 1 | `input` | LOW | 否 | source_type / accepted_mime_types / max_file_size_mb / pii_policy |
| 2 | `ocr` | LOW | 否 | ocr_engine / language / output_layout / confidence_threshold |
| 3 | `extraction` | MEDIUM | 否 | schema_id / fields / confidence_policy / missing_field_policy |
| 4 | `rag_query` | MEDIUM | 否 | corpus_id / top_k / distance_metric / **return_policy=ids_only** |
| 5 | `llm_analysis` | MEDIUM | 否 | model_policy / prompt_template_id / memory_hydration_policy / output_schema_id |
| 6 | `compliance_check` | HIGH | 視結果 | rule_set_id / jurisdiction / severity_threshold / review_policy |
| 7 | `decision` | MEDIUM | 否 | decision_type / condition_expression / fallback_edge_id |
| 8 | `provider_review` | HIGH | **是（核心）** | reviewer_role / required_action / timeout_policy / modify_allowed |
| 9 | `form_draft` | MEDIUM | 是 | form_template_id / **draft_only** / required_review_before_export |
| 10 | `export` | HIGH | 是 | export_format / destination_policy / review_required / watermark_policy |
| 11 | `audit` | LOW | 否 | audit_level / redact_policy / store_hashes / retention_policy |
| 12 | `sync` | MEDIUM | 否 | sync_target / cloud_binding_required / retry_policy / offline_queue_policy |

> 🔲 完整 param 型別/必填待 V5.4 實作前細化；本 spec 定方向。

---

## 3. GraphRun / NodeRun / Edge Schema（🆕 proposal）

### 3.1 GraphRun
```json
{
  "graph_run_id": "string", "workflow_graph_id": "string", "skill_id": "string",
  "provider_id": "string", "client_id_hash": "string",
  "status": "PENDING | RUNNING | HELD_FOR_REVIEW | COMPLETED | FAILED | CANCELLED",
  "execution_target": "cloud | local | auto", "current_node_id": "string",
  "created_at": "timestamp", "updated_at": "timestamp", "completed_at": "timestamp|null"
}
```

### 3.2 NodeRun
```json
{
  "node_run_id": "string", "graph_run_id": "string", "node_id": "string", "node_type": "string",
  "status": "PENDING | RUNNING | HELD_FOR_REVIEW | COMPLETED | FAILED | SKIPPED",
  "risk_level": "LOW | MEDIUM | HIGH | CRITICAL", "adapter": "string",
  "execution_target": "cloud | local | auto",
  "input_ref": "hash_or_pointer", "output_ref": "hash_or_pointer", "audit_ref": "hash_or_pointer",
  "error_type": "string|null", "started_at": "timestamp|null", "completed_at": "timestamp|null"
}
```

### 3.3 Edge
```json
{
  "edge_id": "string", "from_node_id": "string", "to_node_id": "string",
  "condition": { "type": "always | expression | decision_output", "value": "string" },
  "data_policy": { "pass_raw_content": false, "pass_hashes_only": true, "requires_in_memory_hydration": false },
  "review_gate_id": "string|null"
}
```

> ⚠️ **Edge 默認不得傳遞 RAG raw text / raw prompt / secret / env**（對齊 C2 §6）。

---

## 4. Executor Adapter Layer

### 4.1 Adapter 清單（📐 Registry 提，狀態真實）

| Adapter | 後端 | candidate_status | 證據 |
|---|---|---|---|
| `goaa_task_runner` | 本地 task_runner.py（**F-lite executor**） | **status pending（見註）** | ✅ F1 盤點：`services/rag/workers/task_runner.py`，`run_task()`→`TASK_HANDLERS`（現 2 handler：embed/topk） |
| `local_aikabox_executor` | AiKa-Box 本地算力 | candidate | 📐 設計 |
| `cloud_agent_executor` | 雲端 Agent | candidate | 📐 設計 |
| `comfyui_adapter` | ComfyUI node-graph | **candidate**（API/resource/workflow 待驗） | 📐 不開放 Provider |
| `external_api_adapter` | 外部 API | **candidate**（auth/cost/IO 待驗） | 📐 |

> **`goaa_task_runner` 狀態註**：design-linked to F-lite executor；F-lite design layer 已立（F-lite v0.3 設計文檔本窗口入庫，commit `1acb515`，三端對齊），**但 task_runner 對接 Graph node 的執行能力 = implementation status pending code inspection**（現僅 2 唯讀 handler，Graph node 執行尚未實作）。**不寫 available。**

### 4.2 Adapter 派發三層把關（🆕，整合三份真實檔）
```
1. static capability check    ← node-capability-system.md（docker/gpu/ssh booleans，"能不能"）
2. role/security allowlist    ← agent-roles.md security_limits + F-lite allowlist（"准不准"）
3. dynamic health/capacity    ← §4.4 動態探針
4. cost/credit guardrail      ← §7（if applicable）
5. dispatch or queue
```

### 4.3 統一 Adapter Interface（🆕 proposal）
```json
{
  "adapter_id": "string",
  "adapter_type": "goaa_task_runner | local_aikabox_executor | cloud_agent_executor | comfyui_adapter | external_api_adapter",
  "supports_node_types": ["ocr", "llm_analysis"],
  "supports_execution_targets": ["local", "cloud", "auto"],
  "capability_requirements": {},
  "risk_ceiling": "LOW | MEDIUM | HIGH | CRITICAL",
  "requires_review": true,
  "candidate_status": "available | candidate | disabled",
  "dispatch_contract": { "input_ref": "hash_or_pointer", "output_ref": "hash_or_pointer", "timeout_sec": 60 },
  "audit_contract": { "store_raw_input": false, "store_raw_output": false, "store_hashes": true, "redaction_required": true }
}
```
> candidate adapter **不可 Provider paid callable**；external API adapter pending auth/cost/IO；ComfyUI pending API/resource/workflow；`goaa_task_runner` 是否 available 看 F-lite 真實狀態，**不自動寫 available**。

### 4.4 Dynamic Capability Probing（🆕，吸收 Gemini 建議 3，降級為設計提案）

靜態 capability 只說「有無 GPU/Docker」，不說「當前是否夠資源」。Video Agent / ComfyUI candidate 若 GPU 顯存已佔，強行 dispatch 可能 OOM。

`execution_target=auto` 或高資源節點 dispatch 前，Adapter 須跑動態探針：
```json
{
  "capacity_requirements": { "min_free_vram_mb": 2048, "max_gpu_pct": 85, "max_mem_pct": 85, "requires_gpu": true },
  "fallback_policy": "queue_until_available | route_to_cloud | route_to_other_box | fail_fast"
}
```
探針來源：B-1 `/node/health`（本機）、B-2 `/fleet/health`（Local Fleet 聚合）。

> 安全邊界：`/node/health` 已實作（B 線），`/fleet/health` 仍 B-2 設計**未完成**，不寫已完成；comfyui/external_api 仍 candidate；Video Agent candidate **非 Provider paid callable**；**不寫「8GB 一定能跑」**；不寫價格/收益/credits 結算承諾。

---

## 5. Provider Review Hold — Stateful Breakpoint（📐 Registry 概念，🆕 對齊 + Context Snapshot）

HIGH/CRITICAL node 後掛斷點，不阻塞整個 Graph。

### 5.1 Review Hold record（含 Context Snapshot，🆕 吸收 Gemini 建議 1，降級為安全設計提案）

**問題**：Graph 在 `HELD_FOR_REVIEW` 掛起時，前序節點中間結果若只在記憶體，進程退出即丟，恢復可能被迫從 input 重跑（浪費算力 + 結果可能不一致）。

```json
{
  "graph_run_id": "string", "node_id": "string", "status": "HELD_FOR_REVIEW",
  "resume_token_hash": "string", "next_node_id": "string",
  "context_snapshot_id": "string|null",
  "context_snapshot_hash": "string|null",
  "context_snapshot_policy": "none | sanitized_metadata | encrypted_local_snapshot",
  "review_actor": "string|null", "review_timestamp": "timestamp|null",
  "review_action": "approve | reject | modify | null"
}
```

**安全邊界（v0.2 只設計，不實現）：**
- snapshot **不含 secret**
- snapshot **不含 raw RAG text**，除非未來 C2 spec 明確允許「同信任域內加密本地臨時快照」
- **默認策略 = `sanitized_metadata` 或 `none`**
- 若未來用 `encrypted_local_snapshot`，須先定義：加密方式 / 本地密鑰管理 / TTL / deletion policy / audit hash / no frontend exposure
- **不寫「gc.collect() 後就安全銷毀」這種絕對說法**，只寫 best-effort cleanup
- 不把 context snapshot 寫成已實現

### 5.2 與 F-lite 對齊（真實落差）
- F-lite 用 `awaiting_approval`（Router 現有狀態）= 規範 `HELD_FOR_REVIEW` 的 **V5.3 簡化先行版**
- V5.4 正式化為 stateful breakpoint（含 next_node_id 斷點恢復 + context snapshot）
- → **F-lite 是 V5.4 Review Hold 最小實現；V5.4 是 F-lite 的完整化**

---

## 6. In-Memory Hydration Middleware（🆕 吸收 Gemini 建議 2，對齊 C2）

**`rag_query` node output 只能是：** chunk_ids / chunk_hashes / corpus_id / score·distance / metadata summary。
**Graph Edge 不傳 raw RAG text；前端不顯示；audit/task_result/logs 不寫 raw RAG text。**

`llm_analysis` 需讀 `rag_query` 對應正文時，**不經 Edge 明文傳遞**：
```
rag_query node → 回 chunk_ids/hashes only
→ edge passes ids only
→ llm_analysis 在受信任本地 executor 內請求 in-memory hydration
→ executor 呼叫 approved Memory Context Fetch function（name pending verification）
→ raw text 僅在執行記憶體存在最短必要時間（best-effort cleanup）
→ output = sanitized analysis summary
```

> 對齊 `GOAA_C2_DATA_PRIVACY_SPEC.md` §6 八不。**不寫「靜默注入後一定銷毀」、不聲稱物理級清零。** 是否用 `exec_memory_context_fetch` 以真實代碼 / C2 spec 為準；未確認則寫「approved Memory Context Fetch function, name pending verification」。

---

## 7. Cost Guardrail（📐 Registry，Video candidate）
```
max_service_credits_per_task           # credits placeholder
requires_cost_estimate_before_dispatch
execution_blocked_if_cost_unknown
```
> 憲法 §3：Credits placeholder，**不承諾收益**。針對 Video Digital Human **candidate**（API 待查證）。

---

## 8. 狀態機 — 規範 vs 現實（✅ node-task-pool.md 真實落差）

| 規範 9 態（v2.1） | Router 生產 | V5.4 處理 |
|---|---|---|
| Pending→Assigned→Running | ✅ 有 | 保留 |
| Bidding | ❌ FIFO `get_idle_worker` | **§8.1 Deferred** |
| Verifying（QS） | ❌ 無 | 🆕 接 AiKa-Test |
| Completed→Settled | ❌ 無 Settled | 🔲 Credits placeholder，暫不實 |
| Failed→Retrying（max 3） | ❌ 無 | 🆕 設計，F-lite v0.3 不實現 |
| Cancelled | ❌ 無 cancel | 🆕 補 |
| `awaiting_approval`（Router 額外） | ✅ 有 | 對齊規範 HELD_FOR_REVIEW |
| `blocked`（零利潤） | ✅ 有 | 保留 |

### 8.1 Bidding Deferred（🆕 吸收 Gemini 建議 4）
V5.4 第一階段**保留 FIFO / idle worker selection，不引入競價協議**。先集中實現：Review Hold / Adapter Interface / F-lite risk gate / Redaction / Dynamic Capacity Probe / Visibility Boundary。Bidding 保留為 future option。
> 理由：本地內網多 Box 延遲低，第一階段無需競價；競價增加複雜度；符合漸進增強，不過度工程。

---

## 9. Review Gates（🆕，接 F-lite review gates 前置）
順序對齊 Registry Sandbox Review Gate（📐 文檔級，代碼未驗）：
```
staging → git diff → test → redaction → secret pattern → unsafe command → path safety → manual review → rollback
```
**F-lite 前置貢獻**：redaction（redact()）+ secret pattern + unsafe command + path safety。

---

## 10. Visibility Matrix（🆕，五端可見性）

| Capability / Data | Command Center | AiKa-Box Console | Worker | Providers | Clients |
|---|---|---|---|---|---|
| Workflow Graph editor | Full | Limited/View | Full | Hidden/View-only skill config | Hidden |
| Graph internal nodes | Full | Limited | Full | Hidden or read-only summary | Hidden |
| Stepper progress | Full | Full | Full | Full | Full |
| Review Hold queue | Full | Full | N/A | Full for own cases | Hidden |
| Raw RAG text | Hidden | Hidden by default | Hidden by default | Hidden | Hidden |
| RAG chunk IDs / hashes | Limited | Limited | Limited | Hidden | Hidden |
| Adapter dispatch logs | Full | Limited | Limited | Hidden | Hidden |
| Audit summary | Full | Limited | Limited | Limited | Hidden / client-safe only |
| Export result | Full | Limited | N/A | Full after review | Full after delivery |

> Clients 只看 Stepper / 文件 / 結果 / 消息，**不看** raw graph / raw RAG / system logs / adapter dispatch / internal audit。Providers 看業務語言 + 自己 case 的 Review Hold，不看底層節點圖。Worker 看 graph/adapter/test。Command Center 全局治理入口。

---

## 11. 與 F-lite / V5.5 關係

```
F-lite（v0.3 設計層，commit 1acb515 入庫；executor 實作 pending）
  └─ executor = goaa_task_runner adapter（§4）
  └─ 風險引擎 + redaction = review gates 前置（§9）
  └─ awaiting_approval = Review Hold 簡化先行版（§5）
        ↓
V5.4 Workflow Graph（本 spec）
  └─ 12 Node Types schema + Adapter Layer + Review Hold + Context Snapshot + 狀態機
        ↓
V5.5（Provider Workspace + Graph-backed Skills + Marketplace）
  └─ Skill.workflow_graph_id 綁定本層 Graph
  └─ Skill Black-box（Provider 只見 input schema，節點圖內部 read_only）
```

---

## 12. 待盤/待定清單（🔲 留白，不憑印象）

- [ ] 各 Node Type 完整 param 型別/必填 — V5.4 實作前細化
- [ ] Verifying 接 AiKa-Test 真實接口（AiKa-Test 代碼未盤）
- [ ] Sandbox Review Gate 9 關代碼是否實作（Registry 文檔級，代碼未驗）
- [ ] 其餘 4 個 Executor Adapter 真實代碼起點（僅 task_runner 已盤）
- [ ] `/fleet/health`（B-2）實作狀態（B 線設計，未完成）
- [ ] Memory Context Fetch function 真實函數名（pending verification）
- [ ] Context Snapshot encrypted_local_snapshot 若採用，須補密鑰/TTL/deletion 設計
- [ ] Retrying/Cancelled/Settled 狀態 PG 持久化（接 D 線缺口）

> IP-sensitive design; see IP ledger for official filing references.

---

*v0.2 Implementation-Ready Design Spec — 設計規範，非 production ready，未實現。schema/interface 為新設計提案；candidate adapter 標 candidate 不寫 available；開發流程與產品 Graph 已分層；snapshot/hydration/probe 均為設計提案非實作。*
