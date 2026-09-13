# GOAA + Aika-Box — Golden Baseline v1.0 FREEZE

- **Date (UTC):** 2026-09-13
- **Mode:** READ-ONLY freeze — no deploy / no restart / no DB write / no rename / no branch change
- **Scope:** 5 個「當前已存在、已可運行」的產品面正式登記為 Golden Baseline v1.0
- **Snapshot time:** 2026-09-13 ~11:45 UTC（本檔所有指紋為該時刻實測）
- **Environment mapping:** D0 = Aika-Box / Local Development · C1 = Live / Production · C2 = Test / Staging · Worker cloud = W1…W6

> **Canonical machine-readable manifest:** **`GOLDEN-SURFACE-MANIFEST.json`**（CANONICAL = TRUE）
> **Legacy compatibility alias:** `GOLDEN-REGISTRY.json`（LEGACY_ALIAS / COMPATIBILITY_ALIAS；機器語義與 canonical 完全一致，僅為避免舊腳本與歷史引用失效而保留。**未來 Aika-Box / QwenPaw / ChatGPT / Worker 只認 `GOLDEN-SURFACE-MANIFEST.json`。**）


---

## 0. Golden 定義（凍結原則）

1. **Golden = 當前確認可用的權威基線。** 不是理想架構，是「今天真的在跑、且被信任」的那一份。
2. **允許升級**，但升級 = 新版本，不是就地破壞。
3. **任何對 Golden 內容的修改，必須先說明影響，並由 Tao 審批。**
4. **原則：只增不減、兼容優先**（additive-only, backward-compatible-first）。
5. **刪除 / rename / 破壞性 DB migration / route removal / role semantic change 必須單獨獲 Tao 批准。**
6. **暫時不用的功能優先 HIDE，不 DELETE。**

> 本輪**未**把未完成的 **AI Agent Marketplace** 假裝登記成「已存在黃金版本」。它被列在 §D Roadmap（Future Additions），狀態 = `NOT_YET_EXISTS`。

---

## 1. Golden Registry（登錄表）

| ID | 名稱 | 類別 | 當前 URL / 入口 | 能否運行 | 是否需登入 | 狀態 |
|----|------|------|------------------|----------|-----------|------|
| GOLDEN-01 | GOAA Marketing | 公開行銷面 | `https://www.goaa.ai/` | ✅ 200 | ❌ 公開 | **FROZEN** |
| GOLDEN-02 | GOAA User Portal (customer surface) | 生產客戶面 | `https://planning.goaa.ai/agent-loop/customer` | ✅（307→統一登入） | ✅ Clerk | **FROZEN** |
| GOLDEN-03 | GOAA Provider Portal（legacy 名稱 = agent） | 生產服務者面 | `https://planning.goaa.ai/agent-loop/agent` | ✅（307→統一登入） | ✅ Clerk | **FROZEN**（禁 rename） |
| GOLDEN-04 | GOAA Admin Console | 生產管理面 | `https://planning.goaa.ai/agent-loop/admin` | ✅（307→統一登入） | ✅ Clerk（admin） | **FROZEN** |
| GOLDEN-05 | Aika-Box Control Center | 本地主權入口 | `http://127.0.0.1:5188/` · `http://100.114.37.90:5188/` | ✅ 200 | ✅ session cookie | **FROZEN** |

**共享生產前端 build（GOLDEN-02/03/04 同源同一部署）：** `40c8546e152bf5fad8d7a9d0033f17cab4cbcda8`（下稱 `40c8546`）。

---

## 2. GOLDEN-01 — GOAA Marketing

| 欄位 | 值 |
|------|-----|
| 用途 | 品牌入口 / 行銷 / CTA 導流 |
| 當前 URL | `https://www.goaa.ai/`（`https://goaa.ai/` → **308** → www） |
| Legacy URL | 無（單頁站，產品路徑在此 host 全 404） |
| 源 repo / ref | **無 repo ref** — Framer 代管（`framerusercontent.com/sites/5Ni9v6rvRkAQsHrAopjr1Z/*.mjs`）；不屬 GitHub/relay 血緣 |
| Commit SHA | n/a（外部 CMS） |
| Build ID | n/a |
| 部署路徑 | Framer SaaS（不在 C1 上） |
| Service / unit | 無 |
| 前端路由 | 單頁 + 錨點；`/api/*` 無 |
| API 依賴 | 無（純靜態 + Framer runtime） |
| DB 依賴 | 無 |
| 角色 / 權限守門 | 無（公開） |
| 頁面指紋 | sha256[0:16] = `fb19c2bdc879dcac`（HTML 687,067 B，2026-09-13 實測） |
| 標題 / 描述 | `GOAA.AI Life&Asset Intelligence` / 「AI planning assistant … connect with licensed professionals」 |
| 主要 CTA | `→ planning.goaa.ai/planning`、`/agent-login`、`/client-login`、`/connect-pass?source=planning`、`cal.com/goaa.ai/30min` |
| 截圖 | `shots/GOLDEN-01-marketing-www.png`（324,221 B，sha256[0:16] `8193054c230ffe6f`） |
| 主要功能 | 品牌敘事、CTA 導流、預約（cal.com）、社群連結（FB/IG/X/Threads/LinkedIn） |
| 已知缺口（⚠️ 記錄不改） | ① 標題/描述仍是舊定位「Life & Asset Intelligence」；② 所有產品路徑在此 host = 404（只能走 planning 子域）；③ `https://help@goaa.ai` 為 malformed link（應為 `mailto:`）；④ 頁尾社群連結指向平台首頁（`facebook.com` 等）非 GOAA 帳號 |
| 回滾參考 | n/a（Framer 版本由其後台管理，不在本凍結範圍） |

---

## 3. GOLDEN-02 — GOAA User Portal（customer surface）

| 欄位 | 值 |
|------|-----|
| 用途 | 生產**客戶 / 使用者**面（AI Butler 入口、訂單、技能、授權取得） |
| 當前 URL | `https://planning.goaa.ai/agent-loop/customer` |
| 訪問現狀 | **307** → `/agent-loop/login?next=/agent-loop/customer` → `/client-login?next=/agent-loop/customer`（Clerk 統一登入） |
| Legacy URL（仍 200 / 仍可用） | `/client-login`（200, 統一登入頁）、`/client-logout`、`/client-dashboard`、`/client-dashboard/orders`、`/client-dashboard/service-orders`、`/customer-order-live`、`/connect-pass`、`/portal-preview/customer`（公開預覽） |
| 源 repo / ref | 生產前端 `40c8546e152bf5fad8d7a9d0033f17cab4cbcda8`（**local-only 分支**，GitHub 無此 ref） |
| Commit SHA | `40c8546e152bf5fad8d7a9d0033f17cab4cbcda8` |
| Build ID | `FW7iufKj5JrPAz9Kx2SkX` |
| 部署路徑 | `/opt/goaa-frontend/current` → `/opt/goaa-frontend/releases/40c8546e152bf5fad8d7a9d0033f17cab4cbcda8`（1,969 files / 28,138,994 B；22 個 releases） |
| Service / unit | `goaa-web.service`（node `server.js`，`PORT=3100`，`User=goaa-web`，`Restart=on-failure`，`NRestarts=0`） |
| 前端路由 | 本面相關：`agent-loop/customer{,/earning,/get-licensed,/skills}`、`client-dashboard{,/orders,/service-orders}`、`client-login`、`client-logout`、`customer-order-live`、`portal-preview/customer`（完整 54 pages + 2 API routes 見 §7） |
| API 依賴 | Next BFF `api/agent-loop/[...path]` → `GOAA_AGENT_LOOP_UPSTREAM` = `http://127.0.0.1:3103`；Clerk（LIVE instance）；`auth/google/callback` |
| DB 依賴 | `goaa_platform`（`users` / `user_roles` / `user_identities` / `identity_events` / `agent_applications` / `audit_log` …；migrations `0001`–`0006` 已套用） |
| 角色 / 權限守門 | Clerk session token → 3103 驗證 → `goaa_platform.user_roles` 角色守門 |
| 截圖 | `shots/GOLDEN-02-user-portal-customer-preview.png`（71,668 B，sha256[0:16] `528d2e9f17d8511b`） |
| 主要功能 | 客戶儀表板、訂單 / 服務單、技能、取得授權（get-licensed）、收益 |
| 已知缺口（⚠️ 記錄不改） | ① 未登入一律 307（正常，但無自動化驗收）；② `/portal-preview/*` 為**公開**預覽面（無守門）；③ 客戶面與 Provider 面共用同一 build，角色切換依 Clerk + DB |
| 回滾參考 | `/opt/goaa-frontend/releases/76af718b0568992c900b72d1aff5aad2516046dc`（rollback point，標記檔 `r5b2`/`r5b4`） |

---

## 4. GOLDEN-03 — GOAA Provider Portal（legacy 名稱 = agent）

> **命名紀律：** 本輪**禁止 rename**。「agent」= 現行 legacy 名稱，**語義 = 真人 Provider**。未來 canonical 名稱 = **Provider**（見 §E），但改名須單獨獲批。

| 欄位 | 值 |
|------|-----|
| 用途 | 生產**服務者（真人 Provider）**面：接單、機會、知識、AI 助理 |
| 當前 URL | `https://planning.goaa.ai/agent-loop/agent` |
| 訪問現狀 | **307** → 統一登入（`next=/agent-loop/agent`） |
| Legacy URL（仍可用） | `/agent-login`（→ client-login）、`/agent-dashboard`（200）、`/agent-dashboard/control-center`、`/agent-dashboard/skills`、`/agent-order-live`、`/portal-preview/agent`、`/agent-loop/apply` |
| 源 repo / ref | 同 GOLDEN-02（`40c8546`） |
| Commit SHA | `40c8546e152bf5fad8d7a9d0033f17cab4cbcda8` |
| Build ID | `FW7iufKj5JrPAz9Kx2SkX` |
| 部署路徑 | 同 GOLDEN-02（`/opt/goaa-frontend/current`） |
| Service / unit | `goaa-web.service` |
| 前端路由 | `agent-loop/agent{,/opportunities,/orders,/knowledge,/my-ai}`、`agent-loop/apply`、`agent-dashboard{,/control-center,/skills}`、`agent-login`、`agent-order-live`、`agent-order-demo`（**404**）、`portal-preview/agent` |
| API 依賴 | 同 GOLDEN-02（BFF → 3103；Clerk） |
| DB 依賴 | `goaa_platform`（`agent_applications` / `user_roles` / `user_identities`…）；worker/PG 側 `agents` 等表 |
| 角色 / 權限守門 | Clerk + `goaa_platform.user_roles`（provider 角色） |
| 截圖 | `shots/GOLDEN-03-provider-legacy-agent-preview.png`（65,807 B，sha256[0:16] `5dbe4dd514ceb605`） |
| 主要功能 | 機會、訂單、知識庫、My-AI、申請（apply） |
| 已知缺口（⚠️ 記錄不改） | ① 路由 / 文案仍用 legacy「agent」字樣；② `/agent-dashboard/ai-lab`、`/agent-dashboard/order-workspace`、`/agent-dashboard/service-orders`、`/agent-order-demo` 已 **404**（殘留路由）；③ 真人 Provider 與未來「AI Agent Provider」語義混用風險 → 見 §E |
| 回滾參考 | 同 GOLDEN-02 |

---

## 5. GOLDEN-04 — GOAA Admin Console

| 欄位 | 值 |
|------|-----|
| 用途 | 生產**管理面**：申請審核、內容、財務、系統、客服 |
| 當前 URL | `https://planning.goaa.ai/agent-loop/admin` |
| 訪問現狀 | **307** → 統一登入（`next=/agent-loop/admin`） |
| Legacy URL（仍可用） | `/admin-order-live`（200）、`/portal-preview/admin`（200）、`/agent-loop/admin/applications`（→ admin 首頁） |
| 源 repo / ref | 同 GOLDEN-02（`40c8546`） |
| Commit SHA | `40c8546e152bf5fad8d7a9d0033f17cab4cbcda8` |
| Build ID | `FW7iufKj5JrPAz9Kx2SkX` |
| 部署路徑 | 同 GOLDEN-02 |
| Service / unit | `goaa-web.service` |
| 前端路由 | `agent-loop/admin{,/applications,/content,/finance,/system,/support}`、`admin-order-live`、`portal-preview/admin` |
| API 依賴 | 同 GOLDEN-02（BFF → 3103；Clerk） |
| DB 依賴 | `goaa_platform`（`agent_applications` / `audit_log`（append-only）/ `user_roles`…） |
| 角色 / 權限守門 | Clerk + admin 角色 |
| 截圖 | `shots/GOLDEN-04-admin-console-preview.png`（112,332 B，sha256[0:16] `95b4ef55fcdca574`） |
| 主要功能 | 申請審核、內容管理、財務、系統、客服 |
| 已知缺口（⚠️ 記錄不改） | ① `/admin-dashboard` 已 **404**（舊入口殘留斷鏈）；② `/portal-preview/admin` 為公開預覽（無守門） |
| 回滾參考 | 同 GOLDEN-02 |

---

## 6. GOLDEN-05 — Aika-Box Control Center（`:5188`）

| 欄位 | 值 |
|------|-----|
| 用途 | Aika-Box 本地主權入口 / Worker Runtime OS 控制台 |
| 當前 URL | `http://127.0.0.1:5188/`（loopback）· `http://100.114.37.90:5188/`（Tailscale，經 socat 代理） |
| Legacy URL | 無 |
| 源 repo / ref | `/home/aika/Projects/goaa-ai-main`（monorepo）branch `codex/backend-source-capture-20260902`，HEAD `02a17ffef4544adb00b92ce630616a69846b8ee2`，子目錄 `local-console/` |
| 源檔指紋 | `local-console/main.py` sha256[0:16] = `7f62dfea43d025f6`（138,956 B） |
| Build ID | n/a；runtime 版本字串 = `5.2.C-2`（UI header 標示 `Worker Runtime OS V5.3`） |
| 部署路徑 | **實際載入** = `/home/aika/Projects/goaa-ai-main/local-console`（`override.conf` 改 `WorkingDirectory`）；`/opt/goaa/local-console` = **過期副本（未載入）** |
| Service / unit | `goaa-local-console.service`（`/opt/goaa/venv/bin/uvicorn main:app --host 127.0.0.1 --port 5188`，`Restart=always`，`MainPID=6113`，`NRestarts=0`，`EnvironmentFile=/etc/goaa/console.env`）＋ `goaa-local-console-tailscale-proxy.service`（`socat` `100.114.37.90:5188` → `127.0.0.1:5188`） |
| 前端路由 | 19 個 route decorator（GET/POST）：`/`、`/health`、`/login`(G/P)、`/logout`、`/session`、`/logs/recent`、`/node/health`、`/rag/stats`、`/settings/{agents,models,skills}`、`/tasks/{results,results/{task_id},plan,run}`、`/ai/chat`、`/rag/{chat,topk}` |
| API 依賴 | 本機 Ollama（`11434`，`ollama_available:true`）、PostgreSQL（`goaa` DB，`qwenpaw_memory_chunks` 統計）、`/opt/goaa/{run/telemetry_local,task_results,logs,workers}` |
| DB 依賴 | local-state = `local-console/local_user.db`（SQLite，12,288 B）；session = cookie（`CONSOLE_SESSION_KEY`）；stats 只讀 PG |
| 角色 / 權限守門 | session cookie + 角色枚舉 `["admin","provider","viewer"]`；現況 `authenticated:false` → 多數端點 🔒 |
| 截圖 | `shots/GOLDEN-05-aikabox-5188.png`（111,648 B，sha256[0:16] `b71b6f4cf9564250`） |
| 主要功能 | 總覽 / AI 工作區 / 任務池 / Node Health / 損益審計 / RAG 狀態 / Stepper / Models / Skills / AI Agents |
| HIDE 中（SOON，未刪） | Aika Memory、日誌歷史、系統設置、Cloud Binding |
| 已知缺口（⚠️ 記錄不改） | ① `/opt/goaa/local-console` 與 repo 目錄**雙份漂移**（unit 已 override 至 repo）；② **與 QwenPaw 無任何整合**（唯一關聯 = 只讀 PG 表 `qwenpaw_memory_chunks` 的 stats 查詢，非 QwenPaw API）；③ 4 項功能標 SOON |
| 回滾參考 | repo HEAD `02a17ffe`（工作樹可能有未提交改動，屬 D0 本地，不在 C1 回滾面） |

---

## 7. 附錄 A — 生產前端完整路由清單（`40c8546`，54 pages + 2 API routes）

```
_not-found                    admin-dashboard               admin-order-live
agent-dashboard               agent-dashboard/ai-lab (404)  agent-dashboard/control-center
agent-dashboard/order-workspace (404)                       agent-dashboard/service-orders (404)
agent-dashboard/skills        agent-login                   agent-loop
agent-loop/admin              agent-loop/admin/applications agent-loop/admin/content
agent-loop/admin/finance      agent-loop/admin/support      agent-loop/admin/system
agent-loop/agent              agent-loop/agent/knowledge    agent-loop/agent/my-ai
agent-loop/agent/opportunities                              agent-loop/agent/orders
agent-loop/apply              agent-loop/customer           agent-loop/customer/earning
agent-loop/customer/get-licensed                            agent-loop/customer/skills
agent-loop/login              agent-order-demo (404)        agent-order-live
agent-skill-engine (404)      api/agent-loop/[...path] [API] icon.png [API]
auth/google/callback          client-dashboard              client-dashboard/orders
client-dashboard/service-orders                             client-login
client-logout                 connect                       connect-pass
customer-order (404)          customer-order-live           full-flow-demo (404)
full-flow-live (404)          goaa-clerk-login              order-demo (404)
order-live (404)              planning                      portal-preview
portal-preview/admin          portal-preview/agent          portal-preview/customer
portal-preview/settings       skills
```
（標 `404` 者 = 檔案存在但當前訪問回 404，屬殘留路由，**本輪不刪**。）

**Next 層級 redirect/rewrite（`routes-manifest.json`）：** redirect `/:path+/ → /:path+`；beforeFiles rewrite `/aika-download → /aika-download.html`。

---

## 8. 附錄 B — 後端 / 依賴指紋（C1）

| 元件 | 事實 |
|------|------|
| 後端 API | `3103` = `uvicorn app.main:app`（`/opt/goaa-platform/venv`，`WorkingDirectory=/opt/goaa-platform/backend`，**`Restart=no`**） |
| migrations 已套用 | `0001_identity`、`0002_applications`、`0003_audit_append_only`、`0004_role_grant_guard`、`0005_user_identities`、`0006_golden_business_session` |
| env 檔（僅列變數名） | web：`CLERK_SECRET_KEY` `GOAA_AGENT_LOOP_UPSTREAM` `GOAA_C2_CLERK_AUTH_ENABLED` `GOAA_CLERK_INSTANCE` `NEXT_PUBLIC_CLERK_*` `NODE_OPTIONS`；api：`CLERK_AUTHORIZED_PARTIES` `CLERK_ISSUER` `CLERK_PUBLISHABLE_KEY` `CLERK_SECRET_KEY` `GOAA_C2_*` |
| Clerk | **LIVE** instance（G-4 取證） |
| Stripe | C1 = **TEST-only**（G-4 取證） |

---

## 9. §C — 凍結期間的「現狀」與「未動」聲明

- 本輪**只讀**：所有結論來自 `read / hash / status / GET / SELECT`。
- **未** deploy、**未** restart、**未** 寫 DB、**未** 改 systemd、**未** rename、**未** merge/delete 任何分支。
- **未** 修改 Framer 站台。
- Golden 內容以「今天實測指紋」為準；任何後續變動視為**新版本**，需走 §10 流程。

---

## 10. 變更審批規則（摘要，詳見 `GOLDEN-CHANGE-POLICY.md`）

1. 任何對 Golden-01…05 的修改 → **先輸出影響評估**（受影響路由 / API / DB / 角色 / 回滾點）→ **Tao 審批** → 才動手。
2. **加性優先**：新功能以新增路由 / 新增欄位 / feature flag 方式加入；預設 HIDE 而非 DELETE。
3. **單獨批准項**：刪除、rename、破壞性 DB migration、route removal、role semantic change。
4. **回滾點必須存在**：每個 Golden 面在變更前必須有可回復的 ref / release dir / snapshot。
5. 每次 Golden 變更 → 更新本 Manifest 指紋 + 記新版本號（v1.1、v1.2 …）。

---

## §D — Canonical Future Additions（**NOT YET EXISTS，本輪不登記為 Golden**）

以下為**計劃中 / 未完成**，避免被誤認為「已有黃金版本」：

| # | 能力 | 狀態 | 依賴 |
|---|------|------|------|
| D1 | **AI Butler**（客戶側 AI 助理，canonical 名稱；現況 customer 面已有雛形） | PARTIAL | 3103 + QwenPaw bridge |
| D2 | **Matters**（客戶事務 / 案件聚合） | NOT_YET_EXISTS | `goaa_platform` 新表 + UI |
| D3 | **AI Agent Marketplace**（AI Provider 供給市場） | NOT_YET_EXISTS | Provider 角色語義拆分 + 上架/計價 |
| D4 | **Get Licensed**（授權取得流程） | PARTIAL（`agent-loop/customer/get-licensed` 路由已 307 存在） | 合規 + Stripe |
| D5 | **Earning Opportunities**（收益機會） | PARTIAL（`agent-loop/customer/earning`、`agent-loop/agent/opportunities` 已存在） | 訂單結算 |
| D6 | **Aika-Box × QwenPaw Bridge** | SPIKE（Gate-1 進行中） | QwenPaw API（native approval） |

> 這些**不是** Golden v1.0 的一部分；它們是 **v1.x 的候選增項**，必須走 §10 流程。

---

## §E — Canonical Role Direction（**方向，非本輪變更**）

| 概念 | 現況（Golden v1.0） | 未來 canonical | 本輪動作 |
|------|---------------------|----------------|----------|
| 服務供給者 | legacy 名稱「**agent**」（路由 / 文案 / DB 皆用 agent） | **Provider** | **不動**（禁 rename） |
| 服務需求者 | customer / client | **Customer** | 不動 |
| 平台方 | admin | **Admin** | 不動 |
| AI 供給者（未來） | 無 | **AI Agent / AI Provider**（與真人 Provider 區分） | 不動（未存在） |

**語義風險（登記，不修）**：當前「agent」在 GOLDEN-03 = 真人 Provider，在未來 D3 = AI Agent，**一詞兩義**。任何 rename / role semantic change **必須單獨獲 Tao 批准**，且需 migration + 兼容層（舊名保留 alias）。

---

*End of GOLDEN-BASELINE-V1.md — READ-ONLY freeze artifact.*
