# G4 — FINAL DECISION GATE

**日期**：2026-09-13 ｜ **性質**：**只讀**最終補充核驗（Pre-Execution Decision Gate）
**前置**：Golden Freeze（relay `0d52415`）、Infrastructure Census（`d3a2644`）、G-1（`82e3639`）、G-2（`64f2c21`）、G-3（`3bc3a2c`）
**本輪只補四個未知項**：① 外部整合就緒度 ② Worker/Router 信任邊界 ③ 資料/PII 邊界 ④ Canonical 網域/路由契約

---

## §0 範圍、方法與**未做**的事

**只讀手段**：`systemctl show/cat`、`ss -ltnp`、`ufw status`、`cat` 設定檔、`information_schema`/`count(*)`、`grep` 靜態掃描、`find`／檔案 metadata、DNS 解析、**公開 HTTP GET**、`git log`／relay `status`。

**本輪明確「未做」**（依令）：
- ✗ **無攻擊測試**：未對任何端點送出寫入、未構造惡意 payload、未嘗試繞過授權、未做 fuzz／暴力／注入。
- 對公網端點只做 **GET**（等同瀏覽器訪問），且只讀狀態型端點（`/health`、`/workers/status`、`/workers/metrics`、`/tasks/queue`、`/tasks/pool/stats`、`/tasks/history`、`/cost|models/status`、`/`、`/docs`）。**未對任何 POST 端點（`/tasks/dispatch`、`/task/complete`、`/worker/heartbeat`、`/workers/register`、`/tasks/pool/add`、`/webhook/*`）發送請求**——其授權狀態全部由**代碼靜態判讀**得出，並在 §2 標註推論等級。
- ✗ 無 deploy／restart／DB write／secret rotation／branch merge-delete／Stripe charge／Framer 修改／firewall 修改。
- ✗ 未讀取任何客戶正文、訊息內容、檔案內容。所有 DB 查詢僅取 `information_schema`、欄位型別與 `count(*)`。

**秘密處理**：全篇無任何 key/token/secret 值。凡需引用憑證，只用**長度 + `sha256[0:16]` 指紋**或**前綴形狀類別**（`sk_live_*`／`pk_live_*`／`sk_test_*`／`pk_test_*`／`whsec_*` 之**類別**，非值）。公網 IPv4 一律遮罩為 `a.b.c.⟨d⟩`。

**證據等級**：`[實測]` = 直接觀測；`[靜讀]` = 代碼/設定靜態判讀（未發請求）；`[推論]` = 由兩項以上事實推得。

---

## §1 EXTERNAL INTEGRATION READINESS

### 1.1 主表

| Integration | Purpose | Account Exists? | Sandbox/Test Ready? | Production Ready? | OAuth/API/Webhook Required? | Callback URL Known? | Owner | Billing/Subscription Enabled? | Current Status | Blocker |
|---|---|---|---|---|---|---|---|---|---|---|
| **Stripe** | 連線費 + 專業服務費收款；`Connect` 付撥 | **YES**（憑證已裝） | **YES** | **NO — 僅 TEST 模式** | Webhook **必需**（`checkout.session.completed`、`transfer.*`）；API **必需** | **YES**：webhook `https://api.goaa.ai/api/v1/order/webhook/stripe`；回跳 `https://planning.goaa.ai/connect-pass`（連線費）／`.../customer-order-live`（服務費） | Tao | GOAA 自有 Stripe 帳戶收兩筆費；專業方收款走 Connect | **TEST-ONLY、程式已就緒** | ①**未裝 live key**；②**Connect onboarding 的 return/refresh 指向 Vercel 預覽站**（見 §4.3）；③webhook 在「keys 缺失」時**fail-open**（見 §1.3 W-1） |
| **Clerk** | 統一登入 / 身份來源 | **YES** | **YES**（C2 = Dev tenant） | **YES（已在產線運行）** | 前端 JS SDK + 後端驗證（issuer/JWKS）；**webhook 未設** | N/A（元件式，無外部回跳）；issuer `https://clerk.goaa.ai` | Tao | Clerk 訂閱（方案未核） | **LIVE**：`pk_live_*` + `sk_live_*`、instance=production、受控方 `planning.goaa.ai` | 無登入阻塞；但**無 Clerk webhook ⇒ 身份變更（email/刪帳）不會同步**，JIT 才寫入（見 §1.3 C-1） |
| **Google OAuth** | OpenClaw 侧身份登入之一 | **YES**（client id/secret 已裝） | YES | 待驗 | OAuth **必需** | **兩處不一致**：env 宣告 `https://planning.goaa.ai/auth/google/callback`（由 Next 頁面回應 200）；**API 路由實為** `https://api.goaa.ai/api/v1/auth/google/callback`（無 code 回 400） | Tao | 免費 | **已配置** | 需確認「Next 頁面 → API 交換」是否確實發生（見 §4.3 G-1） |
| **Pipedream** | AI butler 技能外呼（Pipedream Connect） | **NO** | NO | NO | API **必需**（`POST /skills/run`、`POST /skills/webhook/complete` 已預留契約） | **NO**（未實作） | Tao | 未開 | **NEEDS_ACCOUNT**（產品清單 `PREVIEW_ADAPTERS` 自宣告）+ 前端商城 s4 為 **placeholder（enabled=false, $9/mo）** | 開戶 + **先定「資料可外送等級」**（見矩陣 §B） |
| **WebCE** | 證照課程（夥伴/SSO） | **NO** | NO | NO | SSO + webhook（完成回呼已預留） | NO | Tao | 未開 | **NEEDS_ACCOUNT** | 開戶與夥伴審核 |
| **NIPR** | 保險證照官方查驗 | **NO** | NO | NO | API **必需**（`GET /nipr/license`） | NO | Tao | 未開 | **NEEDS_ACCOUNT** | 開戶（多為機構/付費授權） |
| **ARELLO** | 不動產證照查驗 | **NO** | NO | NO | API **必需**（`GET /arello/license`） | NO | Tao | 未開 | **NEEDS_ACCOUNT** | 開戶 |
| **Certemy**（本輪新發現） | 跨職業證照管理（候選） | **NO** | NO | NO | API（`GET /certemy/credentials`） | NO | Tao | 未開 | **NEEDS_ACCOUNT（candidate only）** | 僅候選，未決策 |
| **FirstPromoter** | 會員推薦獎勵 | **NO** | NO | NO | API（`POST /referral/track`、`/referral/reverse`） | NO | Tao | 未開 | **NEEDS_ACCOUNT**（規則：僅 20% 會員） | 開戶 |
| **Cal.com** | 專業連線的**現行實際預約路徑** | **YES** | N/A | **YES（公開頁面 200）** | 無（純連結，無 API/webhook） | N/A | Tao | Cal.com 方案（未核） | **LIVE 但未整合**：`$39.90` 連線發版時 `GOAA_PAID_CONNECTION` 未設（=closed），退回 Cal.com；產線 build 內 7 處、`www` 1 處 | 需決定它與 Stripe 連線費的**存續關係** |
| **Resend** | 交易信（替代 Zoho SMTP） | **YES**（key 已在 `openclaw.env`，長度 36） | 未驗 | **NO** | API **必需** | N/A | Tao | 未核 | **DORMANT**：產線程式**未接**（僅存在於 `staging-oauth-20260906/auth_oauth_resend.py` 一個暫存模組）；產線寄信走 `SMTP_*`（`smtp.zoho.com:587`、`aika@goaa.ai`），且 **`GOAA_C2_EMAIL_DELIVERY=disabled`** | 需 Tao 決定：以 Resend 為準則須驗證網域；否則可**撤銷該 key** |
| **External AI model providers** | 推理/嵌入 | DeepSeek **YES**；OpenAI／Anthropic／Moonshot **NO** | DeepSeek YES | DeepSeek 已用於產線 | API 必需 | N/A | Tao | DeepSeek 按量計費（未核） | **PARTIAL**：`model_router.py` 有 4 家（deepseek／openai／anthropic／moonshot）程式路徑；**只有 DeepSeek 有 key**；其餘點到即失敗。Ollama 為本機（D0/C1） | 缺 key 的 3 家＝**NEEDS_ACCOUNT**；注意 DeepSeek 已在收 `worker task payload`（矩陣 #17） |
| **External AI Agent providers** | 第三方 Agent runtime | **NO** | NO | NO | N/A | NO | — | 未開 | **不存在任何整合**：全 repo 無 `mcpServers`／MCP 設定／第三方 agent SDK；`authorization_kernel`（25 模組）**存在於 repo 但未部署**（§2） | 無阻塞（尚未規劃） |

> **產品自己的宣告**：`PREVIEW_ADAPTERS`（C2 源碼 `.../portal-preview/preview-core.ts`）對 Pipedream/WebCE/NIPR/ARELLO/Certemy/FirstPromoter **全部**標 `status: 'needs_account'`，並自帶 `serverSecretEnv` 名稱與預留端點契約、`REFERRAL_RATE = 0.2`。此清單**只存在於 C2 源碼與前端商城**（`s1–s4`），**未進入 C1 產線 build**（`needs_account` 於 C1 前端 0 命中）。

### 1.2 三個必答

**Q1：今天已經可以接 C2 的 integration？**
1. **Clerk** — C2 已有**獨立 Dev tenant**（`lenient-phoenix-9847.clerk.accounts.dev`），與 C1 產線 tenant 完全隔離 `[實測]`；10 份測試套件含 `test_clerk_auth.py`／`test_clerk_identity_jit.py`。
2. **Postgres** — `goaa_c2test` schema 指紋 `b2e18381ca5eb7cf` **與 C1 `goaa_platform` 完全一致（119 欄）** `[實測]`；`tools/migrate.py` 存在。
3. **本機 Ollama**（若照搬 URL）與 **DeepSeek/Google OAuth 程式路徑**（但 **C2 沒有任何 key**，需先注入）。
4. **nginx / 公開入口** — C2 公網 `https://143.198.224.⟨71⟩/` 回 **401 + `WWW-Authenticate: Basic realm="GOAA C2 Candidate (P5.153)"`**（public basic-auth 守門）`[實測]`；`GOAA_C2_PUBLIC_BASE_URL` **空**。
5. **✗ Stripe：不行** — C2 全部 env 檔（`clerk-api-3103.env`、`goaa-c2-backend.env`…）**無任何 Stripe 憑證** `[實測]`。付款鏈在 C2 **無法**端到端。
6. **✗ 其餘 10 家：不行** — 皆無憑證、無實作（見下）。

**Q2：必須 Tao 先開戶／升級／審核？**
**Pipedream、WebCE、NIPR、ARELLO、Certemy、FirstPromoter**（6 家 `needs_account`）＋ **Stripe LIVE 啟用**（含 Connect 平台審核）＋（若採 Resend）**Resend 網域驗證** ＋（若非 DeepSeek）**OpenAI/Anthropic/Moonshot key**。

**Q3：只能做 mock / adapter placeholder？**
**上述 6 家全部**——目前僅有：① `PREVIEW_ADAPTERS` 的型別化契約（`id/provider/purpose/kind/status/serverSecretEnv/contract/notes`）；② 前端商城條目（`s1` Compliance Monitor、`s2` Client Intake 為 first-party **enabled=true**；`s3` Form Prefill $19/mo、`s4` Pipedream Connector $9/mo 為 **enabled=false**）；③ D0 registry 內 `ocr_placeholder`、`video_gen_placeholder`（`external_api_adapter`／`comfyui_adapter`，enabled=false）。**沒有任何一個有真實 API 呼叫。**

### 1.3 本節新發現的三個具體缺陷

- **W-1（webhook fail-open）**：`goaa/runtime/orders.py` 的 `POST /webhook/stripe` 判定為
  `if 秘鑰存在 → 驗簽；else → 直接 json.loads(body)`，而 `{"fixture":true}` / `{"mock":true}` 會被**當成真實事件處理**（`_handle_checkout_completed` / `_handle_transfer`）。**今日產線有 TEST 鑰匙 ⇒ 走驗簽路徑、此分支休眠**；但一旦 env 缺失（回滾、換機、複製環境）即**由 fail-closed 變成 fail-open**，且該 URL **公網可達**。另存在 `GET /mock/checkout/{token}`（無 Stripe 時可完成訂單）。⇒ 建議改為「無簽章一律 400」，並移除 mock 端點或加 `GOAA_ENV != production` 硬閘。`[靜讀]`
- **C-1（Clerk 無 webhook）**：未發現任何 Clerk webhook 端點。身份採 **JIT 寫入**（`test_clerk_identity_jit.py` 佐證）。⇒ email 變更／帳號刪除**不會**傳播到 `goaa_platform`，而 commerce 側 72 筆舊帳號又不能當橋（`agent_ref_id` 全 NULL）⇒ G-3 §5 的 0007 映射難度**不變但更緊**。`[靜讀/推論]`
- **S-1（Stripe 目前無法扣款）**：C1 `secrets.env` 三把全為 **TEST 類別**（`sk_test_*`／`pk_test_*`／`whsec_*`）`[實測]`。⇒ **G-3 的「BEFORE STRIPE」項目在今日不構成金流風險**，但也意味「接真錢」是一道**尚未跨過的門**；`GOAA_PAID_CONNECTION` 未設（closed）與此一致。

---

## §2 WORKER / ROUTER TRUST BOUNDARY

**拓撲**：`Browser/Cloud → Router(:8080) → Worker → Task Result`

### 2.1 十二項核驗

| # | 項目 | 結論 | 證據 |
|---|---|---|---|
| 1 | Router :8080 是否公網監聽 | **YES（公網、無 IP 白名單）** | `uvicorn api:app --host 0.0.0.0 --port 8080` `[實測]`；`ufw`: `8080/tcp ALLOW IN Anywhere`（v4+v6，註解 "GOAA Model Router API"）`[實測]`；經 Cloudflare tunnel 亦有 22 條路徑對外 `[實測]` |
| 2 | Worker 註冊是否認證 | **NO** | `POST /workers/register` 無任何 token/簽章檢查，直接寫入 DB `nodes` 表 `[靜讀]`（`nodes` 現 1 列 `[實測]`） |
| 3 | Heartbeat 是否認證 | **NO** | `POST /worker/heartbeat` 只做 `worker_hb[req.worker_id] = …` + 寫 JSONL `[靜讀]` |
| 4 | Task polling 是否認證 | **NO** | `GET /tasks/next/{worker_id}` — **身份＝URL 路徑參數**；任何呼叫者可取任何 worker 的任務並把它標為 `running` `[靜讀]` |
| 5 | Task payload 是否簽章 | **NO** | 純 JSON（pydantic model），無 HMAC／無 JWS／無 nonce `[靜讀]` |
| 6 | Result upload 是否認證/簽章 | **NO** | `POST /task/complete` 無認證；`worker_id` 由呼叫者自填 `[靜讀]` |
| 7 | Replay protection | **NO** | router 全檔無 `nonce`／`replay`／`idempot`／`timestamp` 檢核 `[實測 grep]` |
| 8 | `worker_id` 是否可偽造 | **YES** | 註冊/心跳/取件/回報四處全部信任呼叫者自稱的 `worker_id`；`WORKER_REGISTRY` 為**硬編碼 dict**（aika-1/aika-2/do-cloud-1…），實際 worker 身份來自各機 systemd `Environment=WORKER_ID=…` `[實測]` |
| 9 | `task_id` 是否可重複提交 | **YES** | `/task/complete` 若 `task_id` 不存在會**自行生成**（`req.task_id or gen_task_id()`）；`/tasks/pool/add` 接受呼叫者提供的池操作 `[靜讀]` |
| 10 | Capability grant 是否真正 enforce | **NO** | `goaa_agent_skills.enabled` 僅為**展示/就緒度**欄位；執行期權威是 router/worker 內**硬編碼 7 個 `EXECUTORS`**（health_check / ollama_status / docker_status / system_status / ping_test / log_summary / chat）；全 runtime 無 `permission_scope`／`capability_grant` 檢查 `[實測 grep]` |
| 11 | Authorization kernel 是否在運行路徑 | **NO** | `services/rag/workers/authorization_kernel/` 有 **25 個模組**（`pre_action_gate.py`、`capability_grant_envelope.py`、`deny_ledger_state.py`…）`[實測]`；**C1 上 0 個檔案引用它**，未部署、未 import `[實測]` |
| 12 | D0/C1/C2/C3 Worker 之間走什麼 | **公網明文 HTTP（除 C1 自身）** | C1 worker：`ROUTER_API=http://127.0.0.1:8080`（loopback）`[實測]`；**C2 `do-cloud-2`、C3 `do-cloud-3`、D0 `aika-core-01`：`http://134.199.227.⟨108⟩:8080`（= C1 公網 IP、明文、無 TLS）** `[實測]`；Tailscale（`100.114.37.⟨90⟩`）目前只服務 local-console:5188 與 ComfyUI:8188 代理，**未用於 worker↔router** |

### 2.2 對外暴露面（Cloudflare ingress `[實測]`）

`api.goaa.ai` 對公網開放 **22 條 router 路徑** → `127.0.0.1:8080`，並有 catch-all → `127.0.0.1:18789`（OpenClaw）。其中**高風險者**：

| 路徑 | 性質 | 未認證 GET 實測 |
|---|---|---|
| `/workers/status` | **洩漏 worker 拓撲**（worker_id、IP、role、OS、任務與營收統計） | **200（2,341 B）** |
| `/workers/metrics` | 同上 | 200（182 B） |
| `/tasks/queue` `/tasks/pool/stats` `/tasks/history` `/cost/status` `/models/status` | 任務/成本/模型內部狀態 | 皆 **200** |
| `/tasks/dispatch` `/task/complete` `/worker/heartbeat` `/tasks/pool/add` `/tasks/pool/add-batch` `/tasks/next/*` `/tasks/cancel/*` | **寫入型控制面** | 未發請求（禁）；**由代碼判定為無認證** |
| `/chat` `/route` | 代呼叫 **DeepSeek（外部模型）** | 未發請求（禁）；由代碼判定為無認證 |
| `/` 、`/docs` | OpenClaw 招牌與 **110 路徑 OpenAPI** | 200（`{"service":"OpenClaw API Gateway","version":"2.0.0","node":"AKC-DO-001",…}`） |
| `/api/v1/order/*`（catch-all → 18789） | 訂單 API | `/api/v1/order/orders` → **401**（此側有 auth ✓） |
| `/api/v1/agent/*` | 專業方 API | → **401** ✓（`_authenticate_agent`，Bearer 反查 `goaa_agent_tokens`） |

### 2.3 判定

> ## **PUBLIC ROUTER ACCEPTABLE? NO.**
>
> 理由（三條即可成立）：**① 控制面無認證**（dispatch / complete / heartbeat / register / pool-add 皆可被任意網際網路使用者呼叫）；**② 傳輸無加密**（worker↔router 走公網明文 HTTP）；**③ 內部狀態外洩**（worker 拓撲、成本、模型、任務隊列）。三者疊加後，任何第三方可**冒充 worker 領取/回報任務**、**偽造節點註冊**、**代呼叫外部模型（產生費用與資料外流）**。

### 2.4 未來推薦（**只推薦，未實施**）

| 選項 | 評價 | 建議次序 |
|---|---|---|
| **B. Tailscale / private only** | 六台節點皆已有／可取得 tailnet 身份，D0 已在線；**改一個 env（`ROUTER_API`）即可**，零程式改動、可即時回滾 | **第 1 步（立即）**：`ROUTER_API → http://100.…:8080`（或 `http://goaa-router:8080`），並**移除 Cloudflare 的 `/tasks/*`、`/task/*`、`/worker/*`、`/workers/*`、`/chat`、`/route` 路徑**與 **`ufw allow 8080`** |
| **A. Public + signed token** | 保留公網時的**最低**要求：HMAC 簽章 + `worker_id` 綁定金鑰 + nonce/時間窗（防 replay）+ `task_id` 冪等 | **第 2 步**：僅在必須公網（如外部合作方 worker）時使用 |
| **D. Cloudflare Access / Tunnel** | 適合**人**的存取；對**機器對機器** worker 不適用（無法承載長輪詢/心跳且需服務憑證） | 不建議用於 worker 通道 |
| **C. mTLS** | 最強，但需憑證簽發/輪替/吊銷基建，今日無 | **第 3 步**（若 Tailscale 不可接受） |
| **E. Hybrid** | **最終建議**：worker↔router = **B（Tailscale）**；對外 dispatcher API = **A（簽章 token）**；管理員 = **D**；若需跨組織 = **C** | 組合，非單選 |

---

## §3 DATA / PII BOUNDARY

**產物**：同目錄 **`DATA-CLASSIFICATION-MATRIX.md`**（23 類資料 × 12 欄；含 evidence 等級與缺口表）。

> **命名說明（請 Tao 裁示）**：§3 明示「建立 `DATA-CLASSIFICATION-MATRIX.md`」，§5 則明示「只生成 `G4-FINAL-DECISION-GATE.md`」。本輪採**兩檔並存**（矩陣為 §3 指定產物、本檔為主報告），**未再增第三檔**。

要點摘要：
- **P0**：`goaa_platform`（identity／證照／證件檔）**完全無備份**；`goaa_order_tokens` **259 筆明文 bearer token 且 0 撤銷**，且已進入 09-06 commerce dump。
- **P1**：**全 23 類皆無 retention**；`f_lite_sanitize` **只遮 secret、不遮 PII**；worker payload/result 經**未認證公網**流動。
- **正面**：證件檔**實刪**（軟刪列 + `delete_bytes`）、RAG **實刪兩表**、`identity_events`/`agent_review_events` 由 0003 觸發器 **append-only**、C2 `private-files` 檔名為 sha256。
- **今日已發生的外送**：**worker task payload → DeepSeek**（`call_deepseek`，經 router `/chat`、`/tasks/dispatch`）。
- **外部化三問**：禁出清單 7 類（Clerk 身份／憑證／證件原文／金流識別碼／審計軌跡／客戶原文／RAG 原 chunks）；需 consent 5 類；可 metadata-only 6 類。**降級不變式**：consent 不成立 → 退回 metadata-only，而非拒絕服務（保住 C2 gate 可在無客戶資料下驗收）。

---

## §4 CANONICAL DOMAIN / ROUTE CONTRACT

**四個網域**（DNS `[實測]`）：`goaa.ai`／`www.goaa.ai`／`planning.goaa.ai`／`api.goaa.ai` → Cloudflare `104.21.54.⟨131⟩`、`172.67.138.⟨183⟩`；`clerk.goaa.ai` → `104.18.34.⟨146⟩`、`172.64.153.⟨110⟩`。

### 4.1 主表

| Function | Canonical URL（**建議**） | Current Route（實測） | Legacy Route | Redirect? | External Callback Allowed? | Owner |
|---|---|---|---|---|---|---|
| Homepage | `https://www.goaa.ai/` | 200（Framer，687,067 B） | 同 | — | 否 | Tao |
| Customer entry | `https://planning.goaa.ai/` | 200（app 根，16,075 B） | `www` 首頁 CTA（**絕對連結**至 planning ✓） | — | 否 | Tao |
| Login | `https://planning.goaa.ai/client-login` | 200（Clerk） | `/agent-login` → **307** `/client-login?next=%2Fagent-loop%2Fagent`；`/goaa-clerk-login` → **307** `/client-login`；`/agent-loop/login` → **307** `/client-login?next=…`（`next` 有保留；無 `next` 時預設 `%2Fagent-loop%2Fcustomer`） | **YES** | 否 | Tao |
| Sign-up | 同 `/client-login`（Clerk 元件內切換） | **無獨立路由**（`/signup`、`/sign-up` 皆 **404**） | — | — | 否 | Tao |
| Logout | `https://planning.goaa.ai/client-logout` | 200 | `www` 側無（404） | — | 否 | Tao |
| Customer Portal | `https://planning.goaa.ai/agent-loop/customer` | **307 → gated** | `/client-dashboard`（**200，未守門**）、`/customer-order-live`（200，Stripe 服務費回跳） | YES | 否 | Tao |
| Provider / Agent Portal | `https://planning.goaa.ai/agent-loop/agent` | **307 → gated** | `/agent-dashboard`（**200，未守門**）、`/agent-order-live`（200）、`/agent-dashboard/{service-orders,order-workspace,ai-lab}`（**404，產線硬關閉**） | YES | 否 | Tao |
| Admin Portal | `https://planning.goaa.ai/agent-loop/admin` | **307 → gated** | `/admin-dashboard` → **404（產線硬關閉，僅 VERCEL_ENV=preview/development 可見）** | YES | 否 | Tao |
| Professional application | `https://planning.goaa.ai/agent-loop/agent` | 307 → gated | `/agent-skill-engine`、`/agent-order-demo`、`/full-flow-demo` → **404（硬關閉）** | YES | 否 | Tao |
| **Stripe checkout return** | `https://planning.goaa.ai/connect-pass`（連線費）／`.../customer-order-live`（服務費） | **已正確指向 planning**（env 必填，缺失即 503） | `/full-flow-live`、`/order-live` → **404** | — | **YES（Stripe 302 回跳）** | Tao |
| **Stripe webhook** | `https://api.goaa.ai/api/v1/order/webhook/stripe` | **405（僅 POST）**、公網可達 | — | — | **YES（必需）** | Tao |
| OAuth return | `https://planning.goaa.ai/auth/google/callback` | **200（Next 頁面）**；API 側 `/api/v1/auth/google/callback` → **400（缺 code）** | — | — | **YES** | Tao |
| Pipedream callback | （未定）`https://api.goaa.ai/skills/webhook/complete` | **不存在** | — | — | 待建 | Tao |
| WebCE callback | （未定）`https://api.goaa.ai/webce/webhook` | **不存在**（契約僅預留「completion webhook」） | — | — | 待建 | Tao |
| External Agent callback | — | **不存在**（無任何外部 agent provider） | — | — | N/A | — |
| API health | `https://api.goaa.ai/health` | 200（**90 B = OpenClaw 閘道**，非 router） | router 自身 `/health` 被 catch-all 遮蔽 | — | 否 | Tao |
| **Worker router** | **建議 `http://100.…:8080`（tailnet）** | **`https://api.goaa.ai/{tasks/*,task/*,worker/*,workers/*,chat,route,cost,profit,revenue,models}*` → 公網** | — | — | **NO（應關閉）** | Tao |

### 4.2 本節新發現

- **D-1（管理端無門）**：`/admin-dashboard` 在產線**回 404**（middleware 對 `lp` 清單硬關閉，除非 `VERCEL_ENV=preview`／`development`）⇒ 今日**沒有任何可用的管理介面**；`/portal-preview`（200）與 `/portal-preview/admin`（200）**未守門**，且 `/agent-dashboard`、`/client-dashboard`、`/skills`、`/connect-pass`、`/customer-order-live` 皆為「**外殼 200、資料待 session**」。⇒ 建議把「哪些路由該 404／該 307／該 401」寫成**唯一權威表**（middleware 已是唯一決策點，宜抽出成宣告式清單）。`[實測+靜讀]`
- **D-2（重複根）**：`www.goaa.ai/` 與 `planning.goaa.ai/` 同時 200，兩者為不同產品（行銷 vs 應用）。建議明示 canonical，並讓 `goaa.ai`（apex）單向 301 至其一。`[實測]`
- **D-3（apply-onboarding 指向 Vercel）**：`GOAA_AGENT_CONSOLE_URL` 的**實際 env 值 = `https://goaa-ai-local-git-feature-agent-console-v1-tao-fengs-projects.vercel.app/agent-dashboard`**，且 `GOAA_CUSTOMER_CONSOLE_URL` 亦為 Vercel 預覽。該主機 `[實測]` 回 **302 → `https://vercel.com/sso-api?...`（Vercel SSO 牆）**。而 **Stripe Connect onboarding 的 `return_url`/`refresh_url` 正是由 `GOAA_AGENT_CONSOLE_URL` 組出**（`orders.py`）⇒ **專業方完成收款開戶後會被帶到 Vercel 登入牆**。⇒ 這是 **M4（C2 內 Stripe 端到端）與 M5（C1 晉升）的前置條件**。`[實測+靜讀]`

### 4.3 特別確認的現行遺留（**未修改**）

| 遺留 | 實測結果 | 評估 |
|---|---|---|
| `/agent-login` | 307 → `/client-login?next=%2Fagent-loop%2Fagent` | ✅ 正常，`next` 有保留（無 next 時預設 `%2Fagent-loop%2Fagent`） |
| `/client-login` | 200（Clerk；頁內含 clerk.browser.js、`pk_live_*` 指紋 `562a0cfc245df772`） | ✅ 唯一權威登入 |
| `/planning` | 200（16,147 B） | ✅ 與根 `/` 同應用 |
| `/connect-pass` | 200；`/connect` → **307** `→ /connect-pass?source=planning` | ✅ 正常 |
| Cal.com 連結 | `https://cal.com/goaa.ai/30min`：`www` 1 處、**產線 build 7 處**、公開頁 **200** | ⚠️ 未整合（無 API/webhook），但**是現行唯一「付費連線」實際路徑** |
| `help@goaa.ai` 畸形 href | `www` 內存在 **`href="https://help@goaa.ai"`**（應為 `mailto:`；www 另有 Cloudflare email-protection） | ⚠️ 確認存在，無效連結 |
| 舊 metadata | `<title>GOAA.AI Life&Asset Intelligence</title>`；description = "GOAA is an **AI planning assistant** that helps you organize your life and assets…" | ⚠️ 定位過時（未反映「持證專業連線」） |
| `data-goaa-paid` | 產線 HTML 根節點 `data-goaa-paid="closed"` | ✅ 與 `GOAA_PAID_CONNECTION` 未設一致 |
| `www` 是否載入 Clerk | clerk 命中 **0** | ✅ 行銷站不碰身份 |

---

## §5 DECISION：新事實是否改變 G-M0→G-M5 順序

> # **YES —— 有三項新事實改變計劃（不改變 M0「先做 dump」的第一動作）**

1. **（新事實 A｜最高嚴重度）產線 Task Router 是「公網、無認證、明文」的控制面。**
   G-3 的 M0 清單**完全沒有這一項**（M0 = dump／回滾指針／key／備份／`Restart`）。
   ⇒ **M0 必須新增一條**：「關閉 router 公網面（Cloudflare 路徑 + `ufw allow 8080`）並把 worker 通道改走 tailnet/私網」。且此項**需排在 M1.5（可觀測性）與任何金流工作之前**，因為一旦有真錢流（M4/M5），同一個無認證面可被用來**代呼叫外部模型**與**偽造任務結果**。
   ⇒ 另：**M0.5 的「機器可驗收凍結」必須凍結一個「已關閉的 router 面」**，否則凍結的是錯誤基線。

2. **（新事實 B）Stripe Connect onboarding 的 return/refresh URL 指向 Vercel SSO 牆。**
   `GOAA_AGENT_CONSOLE_URL`（產線 env 實際值）→ `…vercel.app/agent-dashboard` → **302 至 Vercel 登入**。
   ⇒ **M4 的進場條件被收緊**：必須**先**把該值改為 `https://planning.goaa.ai/agent-dashboard`，否則「C2 內 Stripe 端到端」走不到終點。這是 G-3 已知「Vercel 預設」的**升級版**（不只是預設，而是**產線實際值**，且直接掛在 Connect 流程上）。

3. **（新事實 C）webhook 為 fail-open，且 mock-checkout 端點存在。**
   `POST /webhook/stripe` 在「keys 缺失」時接受**無簽章**且**信任 `fixture:true`**；`GET /mock/checkout/{token}` 可在無 Stripe 時完成訂單。今日因 TEST keys 存在而休眠。
   ⇒ **M0/M5 新增 hardening 條目**：改為「無簽章一律 400」；並把 mock 端點硬閘在非 production。若不做，**回滾/換機會自動打開一個「免付款完成訂單」的門**。

**不改變順序的（確認性）事實**：C1 Stripe 為 TEST-only（使 G-3 的「BEFORE STRIPE」桶意義明確，且今日**無真實金流風險**）；Clerk 為 live 且已達產（`pk_live_*`/`sk_live_*`、instance=production）；C2 與 C1 tenant 完全隔離；6 家外部整合全部 `needs_account`（無一事實改變 M1/M2/M3 內容）。

**結論**：**G-M0 的內容擴張（A、C）、G-M4 的進場條件收緊（B）**；里程碑**序列本身（M0→M1→M1.5→M2→M3→M4→M5）不變**，M0 的**第一動作仍是 `goaa_platform` dump**（零風險、消除不可逆風險、且為其餘步驟前提）。

---

## §6 給 Tao 的六行回報（正式版）

1. **External integrations** → **BLOCKED（除 Clerk/Google 已 LIVE）**：Stripe **TEST-only**；Pipedream／WebCE／NIPR／ARELLO／Certemy／FirstPromoter 六家 **NEEDS_ACCOUNT、零實作**（僅型別化契約 + 商城 placeholder）；Cal.com **LIVE 但未整合**；Resend **有 key 未接**（產線寄信走 SMTP 且 `EMAIL_DELIVERY=disabled`）；外部 AI 模型 **只有 DeepSeek 有 key**；外部 AI Agent **不存在**。**今日可接 C2**：Clerk、Postgres、Ollama、nginx（**Stripe 與其餘全部不行**）。
2. **Worker trust boundary** → **NEEDS HARDENING（且已達「不可接受」級）**：`PUBLIC ROUTER ACCEPTABLE? NO` — 8080 對全網開放 + 22 條路徑（含 dispatch/complete/heartbeat/register/pool-add）+ 全鏈路零認證 + 零簽章 + 零 replay 防護 + 公網明文；`authorization_kernel` 25 模組存在但**未部署**；capability grant **未 enforce**。建議 **E（hybrid），先 B（tailnet）→ 再 A（簽章）**。
3. **Data/PII externalization blockers** → **P0 ×2**：identity 庫**零備份**；**259 筆明文 token、0 撤銷且已入舊 dump**。**P1**：全 23 類**無 retention**；`f_lite_sanitize` **不遮 PII**；worker payload 今日即外送 DeepSeek。禁出 7 類／需 consent 5 類／可 metadata-only 6 類。
4. **Canonical route blockers** → **D-1 管理端無門**（`/admin-dashboard` 產線 404）；**D-2 雙根並存**（www 與 planning 皆 200）；**D-3 Connect onboarding 回跳 Vercel SSO 牆**；另有 `help@goaa.ai` 畸形 href、舊 metadata、Cal.com 未整合。
5. **是否有新事實改變 G-M0→G-M5 順序** → **YES**（三項，見 §5：公網未認證 router → M0 擴張；Connect 回跳 → M4 進場收緊；webhook fail-open → M0/M5 hardening）。
6. **`INVENTORY COMPLETE`？** → **未成立**（因第 5 項為 YES）。**但本輪四項未知已全部核驗完畢、無殘留未取證項**；Tao 作出下列 8 項裁示後即可進入執行。

---

## §7 待 Tao 裁示（8 項，本輪未執行任何一項）

| # | 裁示項 | 一句話 |
|---|---|---|
| 1 | **router 公網面** | 是否核准關閉（Cloudflare 路徑 + `ufw 8080`）並把 worker 改走 tailnet？ |
| 2 | **承載順序** | 是否維持 M0 第一動作 = `goaa_platform` dump？ |
| 3 | **Connect 回跳** | 是否核准把 `GOAA_AGENT_CONSOLE_URL` 改為 `https://planning.goaa.ai/agent-dashboard`？ |
| 4 | **webhook fail-open** | 是否核准改為「無簽章一律 400」並硬閘 mock-checkout？ |
| 5 | **外部整合順序** | Pipedream 先行，或 NIPR/ARELLO 證照查驗先行？（後者直接支撐「持證」可信度） |
| 6 | **Resend 去留** | 接 Resend（需網域驗證）或撤銷該 key、續用 SMTP？ |
| 7 | **資料外送政策** | 是否採矩陣 §B 的「禁出 7／consent 5／metadata-only 6 + 降級不變式」為 v1 政策？ |
| 8 | **兩檔命名** | 認可 `DATA-CLASSIFICATION-MATRIX.md` + `G4-FINAL-DECISION-GATE.md` 兩檔並存？（§3 與 §5 字面衝突之處理） |

---

*只讀核驗，未執行任何變更。本檔與 `DATA-CLASSIFICATION-MATRIX.md` 為 G-4 全部交付。*
