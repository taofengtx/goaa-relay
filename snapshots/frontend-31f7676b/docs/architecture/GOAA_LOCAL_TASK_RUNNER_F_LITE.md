# GOAA Local Task Runner — F-lite 執行層設計

> **版本**：v0.3 Design Spec（代碼級盤點完成版）
> **階段**：設計文檔補強階段（**不寫代碼、不部署、不重啟、不改 systemd、不碰 `/etc/goaa`、不讀 secret**）
> **v0.3 變更**：第 14 節 6 項代碼級落點**全部真實化**（F1+F2 盤點，6/6 代碼背書，非推測）；新增 §15 現有資產複用表 + §16 必新建清單。
> **對應 roadmap**：Dogfooding F 線「半自動執行 + Dogfooding，自舉終局，**安全閘須重設計**」
> **狀態標註**：✅ 已驗證 = 本窗口讀過真實出處；🔲 待代碼核 = 設計提案，須直讀代碼後確認，**未實現**
> **先設計、後實作、再驗證**（roadmap 安全紀律）。本文件為**設計規範，非 production ready，未實現**。

---

## 0. F-lite 是什麼 / 不是什麼

**F-lite =** 讓 AI 生成**可審計的 execution plan**，由本地 Task Runner 在 **allowlist + risk engine + approval gate + redaction gate** 內執行。

**F-lite 不是** 讓 AI 任意執行 shell。

```
❌ User task → Direct shell execution
✅ User task → Execution Plan → Risk → Scan → Approval → Dry-run/Diff → Execute → Sanitized Audit Log
```

**F 的真正價值 = 補 QwenPaw 缺的「程式化安全閘」，不是換工具。**
（依據：本週密碼反覆洩漏證明連人工審核都會漏，無閘自動執行更危險。）

> **工程誠實**：QwenPaw **未完全退場**；F-lite 逐步吸收其執行能力，secret/production/deploy 仍 Tao 親手。

---

## 1. 核心原則：限制危險權限 ≠ 限制能力

```
限制 Aika 的危險權限 ≠ 限制 Aika 的能力
```

F-lite 看起來會限制 Aika，但這不是壓制能力，而是**給 Aika 的強能力加上方向盤、剎車、安全帶和審計儀表盤**。

**我們限制的是危險權限：**
arbitrary shell / arbitrary sudo / arbitrary systemd write / arbitrary `/etc/goaa` write / arbitrary secret read / arbitrary deploy / arbitrary git push / arbitrary file deletion / arbitrary cross-node execution / arbitrary external API call

**我們不限制 Aika 的核心工程能力：**
理解任務 / 分析代碼 / 閱讀文檔 / 生成 execution plan / 生成 diff plan / 生成 patch draft / 依賴盤點 / 日誌分析 / 架構建議 / 任務拆解 / 跑 allowlist 工具 / 輸出 sanitized audit summary

**目標：把 Aika 從「聰明但危險的遠程命令執行器」升級為：**
```
可審計的本地 AI 工程執行員
有權限邊界的 AI Worker
可以進入客戶企業環境的 AI Worker Runtime
```

---

## 2. Aika Capability Levels / 分級放權模型

| Level | 名稱 | 允許 | 特點 | 首版 |
|---|---|---|---|---|
| **L1** | Advisor 只讀顧問 | 讀文檔/讀代碼/grep/find/git status/git diff/建議/風險分析/任務拆解 | 默認允許、低風險、可高度自動化、只讀不落盤 | ✅ 納入 |
| **L2** | Draft Maker 草稿生成者 | 生成 patch plan/markdown 草案/code diff 草案/測試方案/migration plan/rollback plan | 可開放、不直接落盤、輸出必須可審計、不執行系統命令 | ✅ 納入 |
| **L3** | Safe Executor 安全執行者 | 只改 `docs/`/只跑 allowlist 測試/lint/dry-run/僅 sandbox 或非生產路徑/只輸出 diff·log·audit | **需 approval**、必 dry-run first、必 diff-first、必有 rollback、不碰 secret、不碰 production | ⚠️ **少量**納入 |
| **L4** | Operator 高權限操作者 | 改 systemd/改 `/etc/goaa`/裝系統包/重啟/deploy/git push/生產 DB 寫/跨節點寫/外部付費 API | **首版默認禁止**、後續須 Tao 手批、必 Review Hold、必 audit | ❌ **不進首版自動執行** |

> **首版範圍：L1 + L2 + 少量 L3。L4 不進入首版自動執行範圍。**
> **secret / deploy / production 永遠不能全自動。**

---

## 3. 現有地基（✅ 本窗口已盤點，引用真實出處）

| 地基 | 出處 | 內容 |
|---|---|---|
| 風險引擎雛形 | `/opt/goaa/router/api.py`（Aika 盤點） | `TASK_REVENUE`(risk 1-4) / `select_model`(高風險走 Claude) / `auto_dispatcher_loop`(P0/P1+risk≥4 阻擋待審批) |
| nodes 持久化 | `api.py` L927-945（Aika 盤點） | 心跳 `UPDATE nodes SET` / 新節點 `INSERT INTO nodes` |
| 治理四級 | `docs/runtime/p3-7-ai-governance-policy.md`（11 行） | LOW 自動 / MEDIUM 建議 / HIGH 批准 / CRITICAL 封鎖 |
| 節點安全限制 | `docs/agent-roles.md` | `max_risk_level` / `requires_approval` / `blocked_actions` |
| 15 條安全硬禁令 | `docs/architecture/...5188.md`（264 行,✅讀過） | 不 shell / 不 `subprocess(shell=True)` / 不 `os.system()` / 不 printenv / 不露 secret … |
| Console/Worker 解耦 | 同上 | **Console 崩 → Worker 照跑** |
| C 線唯讀閉環 | 6/9 devlog（✅讀過） | `/ai/chat enable_tools` → DeepSeek tool_calls → PG SELECT（`_ALLOWED_TYPES` 白名單） |

→ **F-lite 不是從零造**：風險分級、審批標記、白名單**雛形已在**。要做的是「政策→可執行閘」的連接 + redaction gate + approval 持久化 + 接 5188 審批 UI。

---

## 4. 首版必守的核心原則（保留並強化 v0.1）

1. 不裸搬 `execute_shell`
2. 不允許 DeepSeek 任意 SSH 執行
3. 不公網暴露（Phase 3 永不）
4. 不做 secret / production / deploy 自動化
5. 不做真實支付或外部 Agent API 調用
6. F-lite 的價值是補 QwenPaw 缺的「程式化安全閘」
7. **Console 崩潰不得影響 Worker 執行層**
8. 所有 HIGH / CRITICAL 任務必須進入人工 Review Hold
9. 生產、secret、deploy 仍必須 Tao 親手確認

---

## 5. F-lite MVP Allowlist

**第一版只允許以下任務類型：**
- `repo_readonly_inspect`
- `docs_draft_patch`
- `docs_safe_edit_pending_approval`
- `git_diff_report`
- `test_collect_only`

**第一版禁止：**
arbitrary shell / sudo / systemd write / `/etc/goaa` write / secret read / database write / deploy / git push / production node write / external API call / LAN scan / file delete / chmod·chown / package install（除非 Tao 明確批准）

---

## 6. 執行流：Plan → Risk → Approve → Execute

```
User task
  → Execution Plan
  → Risk Classification
  → Secret / Dangerous Action Scan
  → Approval Decision
  → Dry-run / Diff-first
  → Execute
  → Sanitized Audit Log
```

**禁止：** `User task → Direct shell execution`

---

## 7. Risk Level Mapping（四級）

| 級別 | 範圍 |
|---|---|
| **LOW** | read-only、safe inspection |
| **MEDIUM** | local docs patch proposal、tests、build dry-run |
| **HIGH** | file write、cross-node operation、config change、git action |
| **CRITICAL** | secret path、`/etc/goaa`、systemd write、sudo、rm、deploy、production write |

> **未知動作默認 MEDIUM 或 HIGH，不能默認 LOW。**

---

## 8. Thinking / Output / Command Redaction

- 默認**不**向 5188 前端展示 raw reasoning / thinking。
- 若某模型或工具產生 reasoning stream，必須經過 **streaming redaction gate**。
- 命令文本、stdout、stderr、LLM output、tool output **都必須**經過 redaction。
- 命中 secret pattern 後，返回 `[SECURITY_REDACTED]` 或 `[THINKING_SECURITY_VIOLATION]`，**不回顯原文**。
- **不聲稱「物理級清零」或「100% 不洩漏」**；本節只描述工程防線與 best-effort redaction，洩漏風險無法保證歸零。

---

## 9. Approval Persistence

HIGH / CRITICAL 任務**不允許只存在記憶體**。

**pending review record（設計提案，🔲 SQLite/local_storage.db 是否已存在須先代碼盤點，不假設）：**
```
task_id
risk_level
action_type
plan_summary
proposed_files
proposed_commands_hash      # 只存 hash
resume_token_hash           # 只存 hash
status
created_at
approved_by
approved_at
rejected_reason
```

**禁止寫入：** raw secret、完整 dangerous command（含敏感路徑則不存原文）、raw resume_token。

**狀態機（設計建議，🔲 不假設 `STATUS_HELD_FOR_REVIEW` 已存在，須代碼確認）：**
`PENDING_PLAN` → `HELD_FOR_REVIEW` → `APPROVED` / `REJECTED` → `EXECUTED` / `FAILED` / `CANCELLED`

---

## 10. Master / Worker Execution Boundary

**Phase F-lite-1（首版）：**
- 單機本地 allowlist runner
- 僅 docs / read-only / diff-first
- 不碰 production、不碰 secret

**Phase F-lite-2（後續）：**
- Local Fleet worker dispatch
- Master 負責 plan / review / approval
- Worker 節點負責 sandbox build / test
- 依賴 B-2 `/fleet/health` 與 nodes registry
- **單 Worker 失敗不影響 Master**

> 🔲 當前可能尚無第二台真實 Worker Box；**不寫「所有任務必須發給 Worker 節點」**。F-lite-2 待真實 Fleet 就緒。

---

## 11. 5188 Review UI（**設計提案，非已實現**）

> ⚠️ 以下 endpoints **are proposed**；**implementation pending code inspection**；**no production deploy yet**。

- `GET /tasks/review/pending`
- `GET /tasks/review/{task_id}`
- `POST /tasks/review/{task_id}/approve`
- `POST /tasks/review/{task_id}/reject`

複用點（🔲待代碼核）：Aika 端 `TOOL_CMD_DANGEROUS_RM` 批/不批 UI 是否可複用。

---

## 12. Audit Log Schema

**只能記錄：**
```
task_id / risk_level / action_type / files_changed / command_hash
output_summary / redaction_count / approval_status / duration_ms / exit_code / created_at
```

**禁止記錄：** secret、env、raw RAG text、raw prompt、raw reasoning、full token、full DATABASE_URL、含敏感數據的 full stdout。

---

## 13. 與 V5.4 / V5.5 關聯

- F-lite 的 executor = V5.4 **Executor Adapter Layer** 的 `goaa_task_runner` 雛形
- F-lite 風險判定引擎 + redaction gate = V5.4 **Workflow Graph review gates** 的前置
- → F-lite 做好，V5.4 Graph Spec 才有安全執行後端，V5.5（Provider Workspace + Graph-backed Skills + Marketplace）才有地基

---

## 14. 代碼級落點（F1 盤點，真實出處；🔲 = 仍待查）

| # | 項目 | 真實發現（出處） | F-lite 落點 |
|---|---|---|---|
| 1 | task_runner 執行入口 | `services/rag/workers/task_runner.py`：`main()`→`run_task()`→`TASK_HANDLERS` dict dispatch（**現僅 2 handler**：`exec_embed_corpus_full`/`exec_topk_query_verify`）；錯誤截 200 字；無任意執行 | **閘插入點 = `run_task` 內 `TASK_HANDLERS.get()` 之前** |
| 2 | auto_dispatcher 審批 | `router/api.py`：P0/P1+risk≥4 → `status="awaiting_approval"`+note；**但無 approve/reject 端點，任務永久卡死** | **F-lite 核心：補端點讓 `awaiting_approval` 流轉** |
| 3 | Console 審批 UI | **❌ 確認 0 個**：`local-console/main.py` 17 端點全列（auth/health/rag/ai_chat/tasks_results/settings），**無任何 approve/reject/pending/review 端點**；task_pool 真相源在 DO Router | **須新建；Console proxy 到 DO Router（同 D.1 模式），審批狀態真相源在 Router** |
| 4 | secret 掃描 util | **✅ 已有**：`services/rag/extract_qwenpaw.py` `redact()`，5 pattern（sk-/AIza/ghp_/Bearer/通用密碼=key） | **#27 import 擴充，不重造** |
| 5 | approval 持久化 | **❌ 無 .db / SQLite**；`task_pool` 為記憶體 dict，restart 全丟 | **須新建 PG `approval_tasks` 表（schema 過 C2 §6）** |
| 6 | `_ALLOWED_TYPES` | **✅ 生產** `api.py` L762，12 種 task type（9×LOW / log_summary MEDIUM / code_review HIGH / security_scan CRITICAL） | **機制在；加 handler 即擴展白名單** |

---

## 15. 現有資產複用表（#27 整合優先，直接可用）

| 資產 | 出處 | 複用方式 |
|---|---|---|
| 風險分級 + 阻擋 | `api.py` `TASK_REVENUE` + `auto_dispatcher_loop` | risk 1-4 已映射，P0/P1+risk≥4 已阻擋 |
| 模型選擇 | `api.py` `select_model` | 高風險走 Claude，已實現 |
| secret 脫敏 | `extract_qwenpaw.py` `redact()` | import，擴充 PG/SSH/sudo pattern |
| task 白名單 | `api.py` `_ALLOWED_TYPES`（L762） | 擴展為 F-lite handler 白名單 |
| handler dispatch | `task_runner.py` `TASK_HANDLERS` | 加 handler 註冊機制 |
| RAG/secret 八不約束 | `GOAA_C2_DATA_PRIVACY_SPEC.md` §6 | audit/redaction schema 對齊 |

## 16. 必新建清單（缺口，F-lite 要補）

| 缺口 | 設計（proposed，**未實現**） | 紀律約束 |
|---|---|---|
| approve/reject 端點 | `POST /tasks/review/{id}/approve`+`/reject`（讓 `awaiting_approval` 流轉） | proposed；pending code inspection |
| approval 持久化 | PG `approval_tasks` 表 | **只存 hash**（commands_hash/resume_token_hash）；不存 raw secret / 含敏感路徑的完整危險命令；過 C2 §6 |
| 5188 審批 UI | AI Workspace 待審批列表 + HIGH/CRITICAL 彈窗 | 屬 AiKa-Box Console 端（產品 IA）；Clients 不見 |
| Console 審批端點 | `GET /tasks/pending`+`POST /task/approve`+`/reject`（proposed，**未實現**） | **Console 只 proxy 到 DO Router**（同 D.1 模式）；審批狀態真相源 = Router task_pool（須先持久化，見上）；Console 不自存審批態 |
| redaction 掛載點 | `redact()` 掛在 task_result / runtime log / 前端輸出**之前** | C2 §6 八不；命中即 `[SECURITY_REDACTED]` |
| F-lite handler 擴充 | docs/readonly/diff handler | ⚠️ **不裸搬 shell**：handler 走 allowlist 子命令，非任意 `subprocess(shell=True)` |

> ⚠️ **secret pattern 紀律**：擴充 sudo/PG/SSH pattern 時，**規則與文檔內絕不寫真實密碼值**（如已知 sudo 密碼）；只用通用形態（`sudo\s+-S`、`postgres://`、`-----BEGIN.*KEY-----`）。寫死真實密碼字串本身即洩漏。

---

*v0.3 Design Spec — 設計規範，非 production ready，未實現。§14 代碼級落點為 F1 真實盤點；§16 缺口項全標 proposed，實作待 Tao 確認。*
