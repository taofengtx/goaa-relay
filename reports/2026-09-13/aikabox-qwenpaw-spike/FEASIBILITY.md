# Aika-Box × QwenPaw 可行性评估（2HR SPIKE｜只讀）

**日期**：2026-09-13 ｜ **性質**：**只讀評估，不開發、不部署、不改生產**
**範圍**：D0（Aika-Box / `aika-core-01`）本機 QwenPaw 服務 + Aika-Box :5188 AI Workspace
**問題**：是否值得用 1–2 天做最小版 Aika-Box Bridge，取代「Tao 複製指令 → QwenPAW 執行 → Tao 審批 → Tao 複製結果」的人工迴路。

**本輪未做**：未修改 QwenPaw／Aika-Box／5188；未寫 adapter；未改 UI；未 restart；未 deploy；未改 firewall；未改 Worker／GOAA／C1／C2；未呼叫任何寫入型生產接口；未自動 approve。僅 `read / inspect / status / config / schema / endpoint discovery / local safe GET`。

**秘密處理**：全篇無 secret 值。僅列 env **變數名**、路徑、埠、端點名、schema 形狀、認證**型別**。公網/Tailnet IP 遮罩為 `a.b.c.⟨d⟩`。

---

## 0. 執行摘要（先看這個）

| 問題 | 答案 |
|---|---|
| QwenPaw API READY? | **YES**（官方 FastAPI 服務，全套 REST + SSE，非逆向） |
| 我們要看的文件在哪 | 本機**沒有** `website/public/docs/`（pip 安裝包）；`/docs`、`/openapi.json` 皆 **404（已關閉）** ⇒ **權威來源 = 套件原始碼**（`site-packages/qwenpaw/app/`） |
| Approval Bridge | **A. NATIVE API** |
| Expected MVP Hours | **15** |
| Worst Case Hours | **24** |
| GO / CONDITIONAL GO / NO-GO | **CONDITIONAL GO**（條件見 §8） |

**一句話**：QwenPaw 本身就內建了我們要的**全部六個能力**（送訊息、收結果、持續 session、捕捉審批、approve/reject、續跑原任務），**不需要 browser automation、不需要逆向、不需繞過安全守衛**；唯一要寫的是「橋接與狀態正規化」的薄層。

---

## 1. QwenPaw Integration Capability Matrix

服務基礎：`qwenpaw app --host 100.114.37.⟨90⟩ --port 8088`（v1.1.5.post1）。所有端點掛在 **`/api`**（`app.include_router(api_router, prefix="/api")`），另有 agent-scoped 掛載 `/api/agents/{agentId}/…`。

### A. Send Message

| 項目 | 結果 | 證據 |
|---|---|---|
| 正式 API / SDK / local endpoint | **YES（正式 REST API）** | `POST /api/console/chat`（`app/routers/console.py`），FastAPI `@router.post`，回 `StreamingResponse(text/event-stream)` |
| 能否向指定 session/thread 發訊 | **YES** | body `session_id`（另可 `X-Agent-Id` header 或 `/api/agents/{agentId}/console/chat` 指定 workspace/agent）；內部以 `session_id` → `get_or_create_chat()` 取得 `chat_id` |
| 純文本 | **YES** | `input:[{content:["text"]}]`；亦接受 `AgentRequest`（agentscope schema）；支援多模態 content_parts |
| 結構化任務 | **YES（部分）** | 同為文字/內容型 payload；`meta`/`channel_meta` 可帶結構化欄位；**沒有** task-schema（如「任務物件 + 參數」）這類一等公民——結構化要靠 prompt 或平台既有 `/tasks/*`（那是 5188 側） |
| 送訊後是否阻塞 | **NO** | 回應為 SSE 串流；**背景續跑**（docstring: “Run continues in background after disconnect”） |
| 重連／續看 | **YES** | 同端點 `POST`，body `{"reconnect": true}` → 附加到進行中的 streaming；內部 `tracker.attach(chat.id)` |

### B. Receive Response

| 項目 | 結果 | 證據 |
|---|---|---|
| 取得方式 | **SSE（primary）**；另有 **polling**（REST GET） | SSE：`POST /api/console/chat`；Polling：`GET /api/chats`、`GET /api/chats/{chat_id}`、`GET /api/console/push-messages` |
| WebSocket | **NOT AVAILABLE（一般用途）** | 全 app 僅 **Twilio 語音頻道**用 WebSocket（`app/channels/voice/conversation_relay.py`）；無通用 WS API |
| Webhook | **NOT AVAILABLE** | 無出站 webhook 機制；搭 `app/cron` 可能但非 API 事件 |
| 持續取得執行狀態 | **YES** | `GET /api/chats` → 每筆含 `status`（僅 `idle` / `running`）；`app/runner/task_tracker.py::get_status` |
| 取得最終結果 | **YES** | `GET /api/chats/{chat_id}` → `{messages:[…], status}`（實測 66 筆 message，含 `role`/`content`/`status`/`error`/`usage`/`metadata`）；SSE 串流本身亦回放全程（run 內 `buffer` 保留所有事件，重連不丟） |
| 區分 running | **YES** | chat.status = `running`；SSE event `status=in_progress` |
| 區分 completed | **YES** | SSE 終端事件 `object="response" && status=RunStatus.Completed`（`channels/console/channel.py:384`）；事件列舉 `created/in_progress/completed/canceled/failed/rejected/unknown/queued` |
| 區分 failed | **YES（需解析）** | SSE `{"error": …}` 事件（`task_tracker._producer` 的 except 分支）＋ message 層 `error` 欄位／`status=failed` |
| 區分 waiting approval | **YES（關鍵！）** | `GET /api/console/push-messages` → `pending_approvals[]`；另 SSE 會送 `tool_guard_approval` 訊息（`_emit_waiting_for_approval_blocking`） |

### C. Session / Thread

| 項目 | 結果 | 證據 |
|---|---|---|
| thread/session id | **YES** | `chat_id`（UUID）＋ `session_id`（渠道會話鍵）＋ `root_session_id`（用於子會話/子代理審批路由） |
| 回復歷史會話 | **YES** | `GET /api/chats`（列表）／`GET /api/chats/{chat_id}`（完整歷史）；持久化於 `~/.qwenpaw/workspaces/<agentId>/chats.json` 與 `sessions/`、`dialog/YYYY-MM-DD.jsonl` |
| 並行多專案/任務 | **YES** | `task_tracker._runs` 支援多個 `run_key` 並行；每個 chat 各自 SSE 佇列；**狀態為 in-memory**（見風險 R2） |
| 指定 workspace/project | **YES（以 agent 為單位）** | 路徑式 `/api/agents/{agentId}/…`、或 `X-Agent-Id` header；每個 agent 一個獨立 workspace 目錄、skills、memory、sessions。**注意：這是「agent 隔離」，不是「同 agent 內多 project 隔離」** |

### D. Approval（核心）

| 項目 | 結果 | 證據 |
|---|---|---|
| programmatic approval event | **YES** | `app/routers/approval.py`（`POST /approve`、`POST /deny`、`GET /list`）；`app/approvals/service.py`（`PendingApproval` + `asyncio.Future`） |
| approval id | **YES** | `request_id`（UUID） |
| action / requested command | **YES** | `tool_name` + `tool_params`（= 該 tool call 的 `input`，即「要執行的命令/參數」） |
| risk level | **YES** | `severity`（`low/medium/high/…`）；附 `findings_count`、`findings_summary` |
| created_at | **YES** | epoch 秒（`p.created_at`）＋ `timeout_seconds` |
| status | **PARTIAL** | 只列 **pending**；`status` 欄位存在於記憶體記錄（`pending/resolved/cancelled`）但**無 REST 查詢已完成歷史**（G1 見 §5） |
| approve（程式化） | **YES** | `POST /api/approval/approve` body `{request_id, session_id, user_id?, reason?}` → `svc.resolve_request(req, APPROVED)` |
| reject（程式化） | **YES** | `POST /api/approval/deny`（同上，`reason` 可填）→ `ApprovalDecision.DENIED` |
| 審批後續跑同一任務 | **YES（自動）** | Worker 在**同一個 run 內阻塞等待** `asyncio.Future`（`_acting_with_approval` → `_wait_for_approval_with_heartbeat`）；Future 一 resolve，該 run 立即續行。**無需另開 run、無需「resume」API** |
| 是否必須人工在原 UI 點 | **NO** | 官方 console UI 也是打這同一組 API；`/approval approve`（chat command）與 `/daemon approve` 只是**別名入口**，底層同一 `ApprovalService` |
| `/approval approve` 是否只是 chat/UI command | **是 chat command，但底層有正式 API** | `app/runner/control_commands/approval_handler.py`（command） vs `app/routers/approval.py`（API）→ **API 才是底層** |
| 逾時 | **有** | `TOOL_GUARD_APPROVAL_TIMEOUT_SECONDS`（預設 **300 s**，可用 env `QWENPAW_TOOL_GUARD_APPROVAL_TIMEOUT_SECONDS` 覆寫）；逾時 → 自動拒絕；`/stop` → `cancel_all_pending_by_root_session` |
| 安全守衛 | **不繞過** | 審批是 **tool_guard** 的一部分（`security.tool_guard`）；API 只做同一決策的 resolve。守衛條件（agent `approval_level`：AUTO / SMART / STRICT、guarded_tools、denied_tools、rules）完全不變 |

### E. Task Status

| 項目 | 結果 |
|---|---|
| task/run id | **YES**：`chat_id` 即 run key；approval 另有 `request_id` |
| 查狀態 | **YES**：`GET /api/chats`（`idle`/`running`）＋ SSE event status |
| 取消 | **YES**：`POST /api/console/chat/stop`（參數 `chat_id`）→ `task_tracker.request_stop()`；並連帶取消該 root session 所有 pending approval |
| resume | **YES（自動）**：審批 resolve 即續跑；此外「重連串流」＝ `reconnect:true`（不是重啟任務） |
| 逾時機制 | **YES**：approval 300 s 自動拒絕；`tracker.wait_all_done(timeout=)`；SSE 有 heartbeat keep-alive |

### F. Authentication

| 方式 | 現況 | 備註 |
|---|---|---|
| API key | **無此機制** | 無 API-key header 概念 |
| Session cookie | **無** | 非 cookie 式 |
| OAuth | **無** | — |
| Local token（Bearer） | **存在但未啟用** | `app/auth.py`：`Authorization: Bearer <token>` 或 `?token=`；token 由 `POST /api/auth/login`（單一使用者）／`/register` 產生，HMAC 簽章 + 可撤銷（`jti`） |
| Socket credential | **無** | — |
| 目前實際狀態 | **認證關閉** | `GET /api/auth/status` → `{"enabled": false, "has_users": false}`（實測）；`QWENPAW_AUTH_ENABLED` **未設**於服務環境 ⇒ `AuthMiddleware._should_skip_auth()` 直接放行 |
| 白名單 | `security.allow_no_auth_hosts = ["127.0.0.1","::1"]` | ⚠️ 但服務**沒綁 loopback**（只綁 tailnet `100.114.37.⟨90⟩`）⇒ 此白名單目前**形同無效**；若啟用認證，橋接端必須帶 token |
| 網路邊界 | **僅 Tailscale** | 監聽 `100.114.37.⟨90⟩:8088`（**非** `0.0.0.0`、**非** `127.0.0.1`）⇒ 對公網不可達，僅 tailnet 可達 |

**判斷：是否適合由 Aika-Box 安全調用？**
**適合，但附兩個硬條件**：
1. 橋接端**必須留在本機/tailnet**（不可轉發到公網）；QwenPaw 目前無認證，等於「能連到 tailnet 的人＝能以 agent 身分執行工具」。
2. 建議（非本輪）啟用 `QWENPAW_AUTH_ENABLED` + 建單一使用者 token，並把服務綁到 `127.0.0.1`（或保留 tailnet + token）；否則橋接會把這個「無認證且能跑 shell」的能力**再包一層**。

---

## 2. 當前 QwenPaw 本地能力（D0 只讀盤點）

| 項目 | 實測值 |
|---|---|
| Service | `qwenpaw.service`（systemd，`enabled`，active since 2026-08-10；`/etc/systemd/system/qwenpaw.service`，787 B），MainPID **7366** |
| Process | `/home/aika/qwenpaw/venv/bin/python …/qwenpaw app --host 100.114.37.⟨90⟩ --port 8088`（Memory 19G，Tasks 211，CPU 8h11m） |
| 子行程 | 2× `playwright/driver/node`（browser 工具用） |
| Listening port | **`100.114.37.⟨90⟩:8088`**（唯一；無 127.0.0.1:8088）；同機另有 `127.0.0.1:5188` + `100.114.37.⟨90⟩:5188`（= GOAA Local Runtime Console） |
| Local API endpoints | 前綴 **`/api`**：`chats`(5)、`console`(4)、`approval`(**3**)、`agents`(6)、`agent`(19)、`agent-scoped`（`/api/agents/{agentId}/…` 掛載 chats/config/cron/mcp/skills/tools/workspace/console/plugins/plan）、`agent-stats`、`config`(28)、`auth`(7)、`messages`(1)、`skills`/`skills-stream`、`tools`、`workspace`、`envs`、`mcp`、`providers`、`local-models`、`plugins`、`backups`、`plan`、`token-usage`、`crons` |
| Config path | `/home/aika/.qwenpaw/config.json`（18,517 B；`security` 節：`tool_guard`/`file_guard`/`skill_scanner`/`allow_no_auth_hosts`）；`settings.json`（22 B） |
| Logs | `/home/aika/.qwenpaw/qwenpaw.log`（6.38 MB，活躍）；`/home/aika/qwenpaw/logs/`；`/home/aika/qwenpaw/qwenpaw-8088.log`；debug 端點 `GET /api/console/debug/backend-logs` |
| Workspace / session storage | `/home/aika/.qwenpaw/workspaces/<agentId>/`：`chats.json`（chat_id→session_id 註冊表）、`sessions/`、`dialog/YYYY-MM-DD.jsonl`、`memory/`、`skills/`、`file_store/`、`tool_result(s)/`、`media/`、`embedding_cache/`。現有 agent：`default`、`QwenPaw_QA_Agent_0.2` |
| Approval storage | **純記憶體**：`ApprovalService._pending: dict[request_id → PendingApproval(asyncio.Future)]`；GC：`_GC_PENDING_MAX_AGE_SECONDS=1800`、`_GC_MAX_PENDING=200`、completed `_GC_MAX_AGE_SECONDS=3600`／`_GC_MAX_COMPLETED=500`。**無 DB、無檔案** |
| Task/run storage | **純記憶體**：`task_tracker._runs: dict[run_key → _RunState(task, queues, buffer)]`（含 SSE buffer，供重連回放）；無持久化 |
| Documented API | 本機**無** `website/public/docs/`（pip 安裝包不含 site）；**`/docs`、`/redoc`、`/openapi.json` 皆 404**（FastAPI docs 已關；`_app.py` 在 production 模式不掛 docs）⇒ **以原始碼為權威** |
| WebSocket / SSE | **SSE 有**：`/api/console/chat`（串流）、`/api/skills/...stream`、`/api/backups/stream`。**WS 僅 Twilio 語音**（非通用） |
| MCP / agent protocol | **MCP = client only**（`app/mcp/{manager,stateful_client,watcher}.py`，`MCPClientManager`）：QwenPaw 是 **MCP 客戶端**（吃外部 MCP server），**不暴露** MCP server ⇒ **不能**用 MCP 反向驅動 QwenPaw。另有 `acp`（`app/…`＋config `acp` 節）＝ACP **客戶端**（QwenPaw 可委託外部 agent），同屬「QwenPaw 主動向外」 |
| 其他 | `console_push_store.py`（進程內 push 佇列，`sticky` 旗標、`take`/`get_recent`，供 `push-messages`）；`channels/` 支援 20+ 渠道（dingtalk/feishu/discord/telegram/…） |

**安全設定現況（只列名/值）**：`tool_guard.enabled = true`；`guarded_tools = null`（＝預設集）；`denied_tools = []`；`custom_rules = []`；`disabled_rules = []`；`shell_evasion_checks` 全 `false`（8 項）；`file_guard.enabled = true`，`sensitive_files` 0 筆；`skill_scanner.mode = "warn"`。

---

## 3. 是否已有可複用接口

| 通道 | 判定 | 依據 |
|---|---|---|
| **A. HTTP API** | **READY** | 正式 FastAPI，`/api/console/chat` + `/api/chats*` + `/api/console/push-messages` + `/api/approval/{list,approve,deny}` 一次到位；實測可用 |
| **B. WebSocket** | **NOT AVAILABLE** | 僅 Twilio 語音頻道私有 WS；無通用 WS |
| **C. SSE** | **READY** | `text/event-stream`，run 內 buffer 支援 `reconnect:true` 回放；實測端點存在且回 200 串流 |
| **D. MCP** | **NOT AVAILABLE（此方向）** | QwenPaw 只是 MCP **client**；不提供 server。*（反向可用：把橋接做成 MCP server 給 QwenPaw 呼叫——但那不是本需求方向）* |
| **E. local CLI** | **PARTIAL** | `qwenpaw` CLI 有 `chats`/`channels`/`agents`/`cron`/`daemon`/…（`cli/` 25 模組）；但**沒有**「送訊息並取得結果」的穩定子命令（`channels send` 為出站推播）。CLI = 運維用，**不建議**當橋接骨幹 |
| **F. internal RPC** | **PARTIAL（不建議）** | Python in-process import（`get_approval_service()` 等）**可行但**需與服務同進程／同 venv；跨進程會拿到**不同 singleton** ⇒ 不可用。**NOT RECOMMENDED** |
| **G. browser automation only** | **NOT NEEDED** | 不需要用瀏覽器控制 QwenPaw |

> 因為 **A/C 都是 READY**，**不需要 browser automation** ⇒
> ### **MVP RISK（接口層）= LOW**（非 HIGH）
> 但見 §5 的三項「設計風險」（認證邊界、in-memory run、300 s 逾時）。

---

## 4. Approval Bridge 可行性

### **APPROVAL BRIDGE = A. NATIVE API**

理由：`app/routers/approval.py` 是**官方一等公民路由**（`_app.py:628 app.include_router(approval_router, prefix="/api")`），不是內部私有函式、不是 UI 專用。它直接 resolve `ApprovalService` 中 agent 正阻塞等待的 `asyncio.Future`。

### 六問逐答

| # | 問題 | 答案 | 做法／證據 |
|---|---|---|---|
| 1 | Aika-Box 能否**監聽** approval request | **YES** | 輪詢 `GET /api/console/push-messages`（回**全部** pending，含跨 session）或 `GET /api/approval/list?session_id=<root>`。事件形狀：`{request_id, session_id, root_session_id, agent_id, tool_name, severity, findings_count, findings_summary, tool_params, created_at, timeout_seconds}`。若要即時，可同時讀 SSE 串流中的 `tool_guard_approval` 訊息 |
| 2 | 能否取得**唯一 ID** | **YES** | `request_id`（UUID v4）；配對鍵 = `request_id`，並需帶上 `root_session_id`（API 會驗 `pending.root_session_id == body.session_id`，不符回 **403**；不存在回 **404**） |
| 3 | Tao 能否在 **Aika-Box** 點 Approve / Reject | **YES** | 橋接在 :5188 現有 console 新增一頁/一區塊（或既有 UI 內嵌），把 `tool_name` + `tool_params` + `severity` + `findings_summary` 呈現給 Tao；兩個按鈕 → 呼叫下游 API |
| 4 | Aika-Box 能否把結果**傳回** QwenPaw | **YES** | `POST /api/approval/approve` 或 `POST /api/approval/deny`，body `{request_id, session_id(=root_session_id), user_id, reason}` → `{success, message, tool_name, request_id}` |
| 5 | QwenPaw 能否**續跑原任務** | **YES（自動）** | 原 run 在 `_wait_for_approval_with_heartbeat` 阻塞等 Future（附 heartbeat keep-alive）；resolve 後**同一 run 續行**並繼續把事件推入 SSE buffer。**「resume」是免費的** |
| 6 | 是否**繞過**現有安全守衛 | **NO（不繞過）** | 審批是 tool_guard 的**組成部分**；API 只 resolve 決策，不改變守衛規則。橋接的權限**等同**官方 console UI（同一組 API、同一 session 驗證）。**唯一新增風險**是「把無認證的 QwenPaw API 再暴露一層」→ 由 §5 的存取控制設計處理 |

**必要安全設計（非繞過，是收斂）**：
1. 橋接服務**只綁 `127.0.0.1`**（或沿用 5188 現有登入 + 角色）；**不新增任何公網/Tailscale 對外 listener**。
2. 橋接**不得**把 QwenPaw API 原樣透傳（不能出現「任意 URL 代理」）；只允許**白名單化**的 5 個呼叫。
3. 橋接**禁止**提供 auto-approve：approve 必須是「Tao 在 UI 的明確點擊」→ 一次 `request_id` 一次決策，且寫本地審計（誰、何時、哪個 `request_id`、approve/deny）。
4. 逾時一致性：QwenPaw 300 s 後自動拒絕；橋接 UI 必須顯示剩餘時間（`created_at` + `timeout_seconds`），避免 Tao 在已逾時後誤以為已批准。
5. 雙重審批防護：第二次 approve 同 `request_id` 應回 404/成功但無效——橋接需冪等處理。

---

## 5. 最小 MVP 架構（只設計，不開發）

```
Aika-Box :5188  (既有 GOAA Local Runtime Console, FastAPI, 已有 admin/provider/viewer 登入)
   └─ AI Workspace 頁（新增 1 頁）
        │  (1) 提交任務
        ▼
   qwenpaw_adapter  (新模組, 唯一新增的「理解 QwenPaw」的地方)
        │  (2) POST /api/console/chat  (SSE)                ── 送訊息／啟動 run
        │  (3) GET  /api/chats                              ── run status (idle|running)
        │  (4) GET  /api/console/push-messages              ── approval inbox (ALL pending)
        │  (5) GET  /api/chats/{chat_id}                    ── 最終結果／歷史
        ▼
   QwenPaw 100.114.37.⟨90⟩:8088
        └─ Run(chat_id) ──▶ tool_guard ──▶ [APPROVAL] ──▶ 續跑 ──▶ 結果
                                ▲
   approval inbox (橋接側)      │  (6) POST /api/approval/approve | /deny
        └─ Tao 在 5188 點擊 ────┘      body {request_id, session_id=root_session_id}
```

### 最小模組（**只允許**這 6 個）

| # | 模組 | 職責 | 對外 | 實作要點 |
|---|---|---|---|---|
| 1 | `qwenpaw_adapter` | 唯一封裝 QwenPaw HTTP/SSE 的地方 | Python 模組 | base URL 設定化（`127.0.0.1`/tailnet + port 8088）；5 個白名單呼叫；逾時、重試、SSE 解析 |
| 2 | `conversation/session bridge` | 我方 project ↔ `chat_id` 映射；建立/重用 chat | 表/檔 | 存 `{project_id → chat_id, session_id, root_session_id}`（SQLite 或 5188 既有 DB）；`POST /api/chats` 或讓 `console/chat` 自動 `get_or_create` |
| 3 | `run status` | 正規化狀態 | `GET /run/{id}` | `running` ← chats.status；`completed|failed` ← SSE 終端事件／message `status`+`error`；`waiting_approval` ← pending 清單命中 `root_session_id` |
| 4 | `approval inbox` | 背景輪詢 + 暫存 | `GET /approvals` | 1–2 s 輪詢 `push-messages`（或長輪詢）；本地快取 + 去重（`request_id`）；TTL 對齊 300 s |
| 5 | `approve/reject` | 轉發決策 | `POST /approvals/{request_id}/{approve|deny}` | 帶 `session_id = root_session_id`；403/404 轉為友善錯誤；寫本地審計 |
| 6 | `result return` | 取回並呈現 | `GET /result/{id}` | `GET /api/chats/{chat_id}` → 取最後 assistant message；呈現全文（可摺疊） |

### **明確不做**（依令）
Agent Factory／Marketplace／Worker 重構／Skill 重構／漂亮 UI／多租戶／計費／完整權限系統／GOAA 整合。

### 三項設計風險（非接口風險）
- **R1 認證邊界**：QwenPaw 目前**無認證**且能執行工具 ⇒ 橋接是唯一入口，必須自己守住（見 §4 安全設計 1–4）。
- **R2 run 狀態 in-memory**：QwenPaw 重啟／`_runs` GC ⇒ 進行中 run 消失、pending approval 消失（`ApprovalService` 亦為記憶體）。橋接必須把「失聯」呈現為 `unknown/lost`，**不可**假裝仍 running。
- **R3 300 s 審批逾時**：Tao 必須在 5 分鐘內回應，否則自動拒絕。MVP 應顯示倒數；若要更長，需改 QwenPaw env（**本輪禁止**，屬後續獨立變更）。

---

## 6. Required Code Changes（若 GO）

| # | 位置 | 變更 | 檔案數（估） | 是否觸碰生產 |
|---|---|---|---|---|
| C1 | Aika-Box :5188 app（`local-console`） | 新增 `qwenpaw_adapter.py`（新檔） | 1 | 否（D0 本地） |
| C2 | 同上 | 新增 `approval_bridge.py`（inbox 輪詢 + approve/deny + 審計） | 1 | 否 |
| C3 | 同上 | `main.py` 註冊 5–6 個新路由（`/qwenpaw/task`、`/qwenpaw/run/{id}`、`/qwenpaw/approvals`、`/qwenpaw/approvals/{id}/approve|deny`、`/qwenpaw/result/{id}`） | 1（改） | 否 |
| C4 | 同上 | 前端：1 頁（提交 + 狀態 + **審批收件匣** + 結果），沿用現有登入/角色 | 1–2（改） | 否 |
| C5 | 本地映射表 | 新增 SQLite 表或 JSON：`project_id ↔ chat_id/root_session_id`＋審計日誌 | 1 | 否 |
| C6 | 設定 | QwenPaw base URL／埠（env 或 config；**不含任何 secret**） | 0–1 | 否 |
| — | **QwenPaw 本體** | **零變更**（必要時僅 env 調逾時，獨立授權） | 0 | 否 |
| — | **C1 / C2 / GOAA / Worker / firewall** | **零變更** | 0 | 否 |

> 全部落在 **D0 Aika-Box**，**不觸碰任何生產**。這是最小衝擊路徑。

---

## 7. Dependency / Risk List

| ID | 類型 | 風險 | 等級 | 緩解 |
|---|---|---|---|---|
| D1 | 依賴 | 只有**一個** QwenPaw base URL（tailnet）；服務若停 → 橋接全停 | Med | 健康檢查 `GET /api/version`；UI 明示離線 |
| D2 | 依賴 | 依賴 **SSE 串流語意**（終端事件、error 事件）作為完成判定 | Med | 以 `GET /api/chats/{id}` 的 message `status`/`error` 作**權威**，SSE 只作即時性 |
| R1 | 安全 | QwenPaw API **無認證**（`auth/status` enabled=false）＋ agent 可執行工具 ⇒ 橋接成為唯一門 | **High** | 橋接只綁 loopback／沿用 5188 登入；白名單 5 呼叫；禁透傳 |
| R2 | 穩定 | run/approval 狀態 **in-memory**，重啟即失 | **High** | 橋接以 `unknown/lost` 呈現；重連時以 `chats.json`＋歷史重建視圖 |
| R3 | 產品 | 審批 **300 s** 逾時自動拒絕 | Med | UI 倒數；逾時後禁止再送決策；必要時另案調 env |
| R4 | 一致性 | `root_session_id` 驗證：錯值回 **403**、舊值回 **404** | Low | 由 inbox 取得 `root_session_id` 後原樣回送；不要自行推導 |
| R5 | 併發 | 同一 `request_id` 重複決策 | Low | 橋接冪等（第一次成功即鎖） |
| R6 | 協定 | SSE 需長連線；代理/緩衝可能截斷 | Low | `Cache-Control:no-cache` 已由服務提供；橋接可退為 polling-only（架構已支援） |
| R7 | 範圍 | 「MVP UI」時間不可控（容易膨脹成「漂亮 UI」） | Med | 硬性限 1 頁、無樣式工程、沿用現成元件 |
| R8 | 治理 | QwenPaw `/docs` 關閉、本機無官方文件 ⇒ 升級 QwenPaw 版本可能改變 API | Med | 以源碼為權威；pin 版本 1.1.5.post1；adapter 集中一檔（唯一影響面） |
| R9 | 平台 | Aika-Box :5188 是**既有** app（v5.2.C-2，role 模型 admin/provider/viewer）⇒ 變更需遵守其既有規範 | Low | 沿用既有 auth/角色；不動現有 18 個端點 |

---

## 8. Hour Estimate（人時，不含規劃/等待）

| 階段 | Best | **Expected** | Worst |
|---|---|---|---|
| Spike only（手工驗證 6 個呼叫：送訊息、收 SSE、讀 pending、approve、見續跑、取結果） | 1 | **2** | 4 |
| MVP backend（adapter + session bridge + run status + result） | 3 | **5** | 8 |
| Approval bridge（inbox 輪詢 + approve/deny + 映射 + 冪等 + 逾時/GC + 審計） | 1.5 | **3** | 5 |
| MVP UI（1 頁：提交 / 狀態 / **審批收件匣** / 結果） | 2 | **3** | 6 |
| Testing（單元 + 整合 + 失敗模式：重啟、逾時、重連、雙重審批、併發） | 1.5 | **2** | 5 |
| **Total** | **9** | **15** | **28** |

> 以 **Expected = 15 h（≈ 2 個工作天內的 1.5 天）** 計。**若 MVP 必須含獨立門戶頁（非嵌入既有 console）或需樣式工程 → +4~6 h ⇒ 落入 NO-GO 區間**。

---

## 9. GO / CONDITIONAL GO / NO-GO

### 逐條對照

**GO 條件**
| 條件 | 結果 |
|---|---|
| Send Message 可程序化 | ✅ `POST /api/console/chat` |
| Response 可程序化獲取 | ✅ SSE + `GET /api/chats/{id}` |
| Session 可持續 | ✅ `chat_id`/`session_id` + `chats.json` |
| Approval 可程序化捕獲 | ✅ `GET /api/console/push-messages`（或 `/api/approval/list`） |
| Approve/Reject 可程序化 | ✅ `POST /api/approval/{approve,deny}` |
| Resume 可程序化 | ✅ 自動（Future resolve → 同 run 續行） |
| 不繞過安全守衛 | ✅ 同一 tool_guard 決策路徑 |
| Expected total ≤ 16 h | ✅ **15 h** |

**NO-GO 條件**
| 條件 | 結果 |
|---|---|
| Approval 只能原 UI 手工操作 | ❌ 不成立（有原生 API） |
| 只能依賴不穩定 browser automation | ❌ 不成立（完全不需要） |
| 需逆脆弱私有接口 | ❌ 不成立（公開路由） |
| 需重寫 QwenPaw | ❌ 不成立（零變更） |
| 需改大量 Aika-Box 基礎設施 | ❌ 不成立（+1 模組組 +1 頁） |
| Expected > 16 h | ❌ 15 h |

### **判定：CONDITIONAL GO**

技術條件全部滿足（8/8），因此不是 NO-GO。判為 **CONDITIONAL**（而非無條件 GO）的唯一原因是**範圍條件**：

**放行條件（必須全部成立）**
1. **UI 硬限一頁**，嵌入既有 :5188 console（沿用其 admin 登入與角色），**不做**獨立門戶、不做樣式工程。
2. **橋接只綁 loopback**（或僅經既有 console 認證可達），**不新增任何對外 listener**；QwenPaw 維持 tailnet-only。
3. 橋接**只白名單 5 個呼叫**，禁止任意代理；**禁止 auto-approve**；審批須留下本地審計。
4. 接受 **300 s 審批逾時**（不在本 MVP 內調整 QwenPaw 設定）。
5. 接受 **run/approval 狀態 in-memory**：橋接必須能顯示 `lost/unknown`，不假裝 running。
6. 第一件事是 **2 h Spike 手工驗證 6 個呼叫**；若任一呼叫不如預期，**立即回退到人工流程**（成本僅 2 h）。

**若上述任一不成立 → 降為 NO-GO**（尤其第 1 條；它是 15 h → 21 h+ 的主要變數）。

### If GO：第一天做什麼（Day 1，8 h）

| 時段 | 動作 | 產出 |
|---|---|---|
| 0:00–2:00 | **Spike**：手動跑完 6 個呼叫（含 `reconnect:true`、逾時後再 approve 的失敗行為） | Spike 記錄 + 決策（繼續／回退） |
| 2:00–4:00 | `qwenpaw_adapter`：5 個白名單呼叫 + SSE 解析 + 錯誤映射 | 可 import 的模組 |
| 4:00–6:00 | session bridge + run status 正規化（`running/completed/failed/waiting_approval/lost`） | `GET /qwenpaw/run/{id}` |
| 6:00–8:00 | approval inbox 輪詢 + `approve/deny` 轉發 + 冪等 + 審計日誌 | `GET/POST /qwenpaw/approvals…` |

**Day 1 結束的驗收**：能用 `curl` 完整走一次「送任務 → 卡在審批 → inbox 看到 → approve → 任務續跑 → 取到結果」。**UI 留到 Day 2**（或更省：Day 1 的 curl 流程先給 Tao 用）。

### If NO-GO：為什麼繼續手工複製更划算

若 Tao 選擇不做（或上述條件不成立），**繼續手工複製並非落後**，理由：
1. **人工流程的唯一成本是 Tao 的複製貼上時間**，但其**收益是零新增攻擊面**——今日 QwenPaw API **無認證且能執行工具**，任何橋接都會把這個能力包成新入口；維持手工＝維持「能連 tailnet 就等於能跑工具」的邊界不變。
2. **Run/approval 狀態全在記憶體**（R2）：服務一重啟，橋接上的「進行中任務」全部失真；手工流程天然免疫。
3. **300 s 審批窗**（R3）對「非同步工作流」價值有限：若 Tao 無法在 5 分鐘內到 Aika-Box 點按鈕，橋接的體驗反而比手機上直接開 QwenPaw 差。
4. **QwenPaw 已有自己的 console UI**（同一台、tailnet 可達、`/api/console/chat` 就是它的後端），且**聊天指令 `/approval approve` 已可直接用**；在 Tao 大多數時間已在該 UI 的前提下，橋接解決的是「少一次複製」，而**不解決**任何新能力。
5. 15 h 的投入換來的邊際收益＝**每次任務省數十秒**；若 Tao 每日任務數 < ~10 次，回本期以月計。**先量測一週的「複製次數 × 每次秒數」再決定**是更划算的順序。

---

## 附錄 A｜本輪實測清單（可重現，全部只讀）

| 動作 | 指令／端點 | 結果 |
|---|---|---|
| 版本 | `qwenpaw --version` | `1.1.5.post1` |
| 服務 | `systemctl status qwenpaw` | active，`/etc/systemd/system/qwenpaw.service` |
| 埠 | `ss -ltnp` | `100.114.37.⟨90⟩:8088` |
| 認證狀態 | `GET /api/auth/status` | `{"enabled": false, "has_users": false}` |
| 版本 API | `GET /api/version` | `{"version":"1.1.5.post1"}` |
| docs | `/docs`, `/redoc`, `/openapi.json` | **404** |
| chats | `GET /api/chats` | 陣列，含 `id/session_id/status/created_at/updated_at/pinned` |
| 歷史 | `GET /api/chats/{chat_id}` | `{messages:[…], status}`（結構：`role`,`content`,`status`,`error`,`usage`,`metadata`,`object`,`type`,`sequence_number`） |
| 審批 inbox | `GET /api/console/push-messages?session_id=…` | `{messages:[…], pending_approvals:[…]}` |
| agents | `GET /api/agents` | 含 `default` 等 |
| 5188 | `GET 127.0.0.1:5188/openapi.json` | `GOAA Local Runtime Console` v5.2.C-2，18 paths |
| 5188 登入狀態 | `GET 127.0.0.1:5188/session` | `authenticated:false, roles:[admin,provider,viewer]` |
| 既有 QwenPaw 客戶端 | `grep -rln "api/console/chat\|/api/approval/approve"`（D0 home） | **僅命中 qwenpaw 套件本身** ⇒ **不存在任何既有橋接** |

**未執行**：任何 POST 到 QwenPaw（包括 `/api/console/chat`、`/api/approval/*`）——本輪**不啟動任務、不審批**，所有寫入型結論均來自原始碼靜讀。

## 附錄 B｜關鍵端點速查（供實作參考，非本次呼叫）

| 用途 | 方法 路徑 | 關鍵參數 |
|---|---|---|
| 送訊息／啟動 run | `POST /api/console/chat` | `{channel, user_id, session_id, input:[{content:[…]}], reconnect}` → `text/event-stream` |
| 停止 run | `POST /api/console/chat/stop` | `chat_id` |
| run 列表＋狀態 | `GET /api/chats` | `user_id?`, `channel?` |
| 歷史／結果 | `GET /api/chats/{chat_id}` | — |
| 審批收件匣 | `GET /api/console/push-messages` | `session_id?`（回全部 pending） |
| 審批列表 | `GET /api/approval/list` | `session_id?`（= root_session_id，含子會話） |
| 批准 | `POST /api/approval/approve` | `{request_id, session_id(=root), user_id?, reason?}` |
| 拒絕 | `POST /api/approval/deny` | 同上（`reason` 建議填） |
| 指定 agent/workspace | `/api/agents/{agentId}/…` 或 header `X-Agent-Id` | 子會話審批路由：header `X-Root-Session-Id` |
| 健康 | `GET /api/version` | — |

---

*只讀評估。未修改 QwenPaw／Aika-Box／5188；未開發；未部署；未觸碰 C1/C2/GOAA/Worker/firewall。*
