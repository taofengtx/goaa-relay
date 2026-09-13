# 13 — C2：Test / Staging 盤點（唯讀）

- 命名：**C2 = Test / Staging**（本輪起統一）

## 1. 身分與網路

| 項目 | 值 |
|---|---|
| hostname | `goaa-aika-cloud-2-01` |
| Public IP | `143.198.224.⟨71⟩`（`eth0/20`） |
| 內網 | `10.48.0.6/16`、`10.124.0.3/20` |
| Cloudflare Tunnel | **未安裝／未啟用**（`cloudflared.service` inactive, MainPID 0） |
| docker | **未安裝**（PG 為原生 `postgres`，pid 2039754） |

## 2. 服務與埠

| 埠 | 服務 | unit（狀態） | 說明 |
|---|---|---|---|
| 13102 | **Clerk UI（候選 3102）** | `goaa-c2-clerk-ui-3102.service`（**disabled 但 active**, MainPID 2039779, `Restart=no`） | `/opt/node/bin/node server.js`；`WorkingDirectory=/opt/goaa-test/ui-clerk-20260910`；`PORT` 來自 env（實際監聽 13102） |
| 3103 | **Clerk 後端** | `goaa-c2-clerk-api-3103.service`（**disabled 但 active**, MainPID 2040092） | `/opt/goaa-test/venv3103-clerk/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 3103`；`WorkingDirectory=/opt/goaa-test/backend-clerk-20260910` |
| 3100 | **候選前端** | `goaa-web-candidate.service`（enabled+active, MainPID 2039675） | next-server |
| 80 / 443 | **nginx** | `nginx`（pid 2039695/2039697） | 站點 `goaa-c2-candidate`（`server_name _`）；443 → `127.0.0.1:3100`，另 `$api_upstream`（`proxy_ssl_server_name on`） |
| 5433 | PostgreSQL | 原生 `postgres` | DB：`goaa_c2test`、`goaa_c2` |
| — | Worker Agent（`do-cloud-2`） | `goaa-worker-agent.service`（enabled+active, MainPID 2040085） | `WORKER_ID=do-cloud-2`、`ROUTER_API=http://134.199.227.⟨108⟩:8080`、`POLL_SEC=5` |
| — | Agent Loop | `goaa-c2-agent-loop.service`（enabled） | — |

- 實測：`https://127.0.0.1/` → **401**（有守門）；`http://127.0.0.1/` → **301**。

## 3. 目錄與樹

| 路徑 | 內容 |
|---|---|
| `/opt/goaa-test/ui-clerk-20260910` | `server.js`（4,723 B）、`.next`、`package.json`、`public`；**1,969 檔**；`BUILD_ID=28IP1GvAGURvF1PHRk8EL` |
| `/opt/goaa-test/ui-clerk-20260910.bak-*` | **9 份**備份（Sep 11，最新 17:09） |
| `/opt/goaa-test/backend-clerk-20260910` | `app/`、`migrations/`、`deploy/`、`README.md`（11,265 B）；**42 檔**；`*.py` sha16 `5e4a41a3ca9c2b2f` |
| `migrations/` | `0001_identity.sql`、`0002_applications.sql`、`0003_audit_append_only.sql`、`0004_role_grant_guard.sql`、`0005_user_identities.sql`、`0006_golden_business_session.sql`、`rollback/` |
| `/opt/goaa-test/venv`、`venv3103-clerk`（＋`*.freeze.txt`）、`wheels/` | 執行環境 |
| `/opt/goaa/{venv,web,workers}` | worker agent 於此機另有一份 |

## 4. 資料庫

| DB | 表數 | 表 |
|---|---|---|
| **`goaa_c2test`** | **15** | `agent_applications`, `agent_license_documents`, `agent_licenses`, `agent_review_events`, `business_subject_links`, `business_subjects`, `business_tokens`, `email_verifications`, `idempotency_keys`, `identity_events`, `schema_migrations`, `user_identities`, `user_roles`, `user_sessions`, `users` |
| `goaa_c2` | **10** | （同上，去掉 `business_*`、`identity_events`：`agent_applications`, `agent_license_documents`, `agent_licenses`, `agent_review_events`, `email_verifications`, `idempotency_keys`, `schema_migrations`, `user_roles`, `user_sessions`, `users`） |

- 觀察：**`goaa_c2` 已落後 `goaa_c2test`**（缺 5 張表）⇒ 若以 `goaa_c2` 為「獨立庫」目標，尚未遷移完成。

## 5. env 檔（**只列鍵名，不印值**；`/opt/goaa-test/env/` 共 13 項）

| 檔 | bytes | mode/owner | sha16 | 鍵數 |
|---|---|---|---|---|
| `clerk-api-3103.env` | 1,172 | 440 `root:goaa-c2loop` | `5a8a64cb559a7639` | 27 |
| `clerk-ui-3102.env` | 511 | 440 `root:goaa-c2loop` | `cd3581e60e7254c1` | 10 |
| `clerk.env` | 382 | 440 `root:goaa-c2loop` | `c832bc4205623204` | 5 |
| `goaa-c2-backend.env` | 747 | 440 `root:goaa-c2loop` | `84d867c9f1f28dbb` | — |
| 兩份 PostgreSQL 憑證檔、`app_role_secret` 等 | — | — | — | **內容一律未抄錄** |
| `*.bak-20260911-*`、`*.bak-c16-open` | — | — | — | 舊版殘留 |

- 鍵名（`clerk-api-3103.env`）：`GOAA_C2_ENV`、`GOAA_C2_DB_HOST/PORT/USER/PASSFILE/SSLMODE`、`GOAA_C2_MIGRATE_USER/PASSFILE`、`GOAA_C2_PSQL`、`GOAA_C2_SESSION_COOKIE/TTL/SECRET`、`GOAA_C2_PRIVATE_FILES_DIR`、`GOAA_C2_STORAGE_LABEL/SCANNER/OCR/DOWNLOAD_TTL/MAX_UPLOAD_BYTES/EMAIL_DELIVERY/PUBLIC_BASE_URL`、`GOAA_C2_DB_NAME`、`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`、`CLERK_PUBLISHABLE_KEY`、`CLERK_SECRET_KEY`、`CLERK_AUTHORIZED_PARTIES`、`CLERK_ISSUER`、`GOAA_C2_CLERK_AUTH_ENABLED`。
- **無任何 STRIPE 鍵**。

## 6. 風險（唯讀觀察）

1. 兩個核心 unit 為 **disabled 但 active** ⇒ 重開機後**不會自動起**（C2 為 staging，可接受，但需明示）。
2. `123102` 埠與 unit 名（`…3102`）**不一致**，是 D0 `-L 13102` tunnel 的對端 ⇒ 文件與指令易誤導。
3. venv、env、DB 憑證檔並存（`app_role_password`、PostgreSQL 憑證檔）⇒ staging 亦應納入秘密衛生盤點。
4. `ui-clerk-20260910.bak-*` 9 份未清理。
