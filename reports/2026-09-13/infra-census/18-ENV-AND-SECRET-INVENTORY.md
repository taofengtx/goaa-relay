# 18 — env／秘密清單與衛生（唯讀；**不抄錄任何值**）

- 原則：**只記錄「檔名、大小、權限、sha16、鍵名」**；所有值一律未讀取、未輸出、未寫入本報告。

## 1. 清單

| 主機 | 檔案 | bytes | mode / owner | sha16 | 鍵數 | STRIPE 鍵 | 值 |
|---|---|---|---|---|---|---|---|
| C1 | `/opt/goaa-frontend/env/web.env` | 481 | 640 `root:goaa-web` | `c72e86561eac7292` | 11 | 0 | 未讀 |
| C1 | `/opt/goaa-platform/env/api-3103.env` | 986 | 600 `goaa-platform` | `711f5817b41fc31d` | 25 | 0 | 未讀 |
| C1 | `/etc/goaa/secrets.env` | 932 | 600 `root:root` | — | 15 | **3（TEST/whsec）** | 未讀（僅模式分類） |
| C1 | `/etc/goaa/openclaw.env` | 661 | 600 | — | — | 0 | 未讀 |
| C2 | `/opt/goaa-test/env/clerk-api-3103.env` | 1,172 | 440 `root:goaa-c2loop` | `5a8a64cb559a7639` | 27 | 0 | 未讀 |
| C2 | `/opt/goaa-test/env/clerk-ui-3102.env` | 511 | 440 `root:goaa-c2loop` | `cd3581e60e7254c1` | 10 | 0 | 未讀 |
| C2 | `/opt/goaa-test/env/clerk.env` | 382 | 440 `root:goaa-c2loop` | `c832bc4205623204` | 5 | 0 | 未讀 |
| C2 | `/opt/goaa-test/env/goaa-c2-backend.env` | 747 | 440 `root:goaa-c2loop` | `84d867c9f1f28dbb` | — | 0 | 未讀 |
| C2 | `/opt/goaa-test/env/`（共 13 項，含 兩份 PostgreSQL 憑證檔、`app_role_secret`、`*.bak-*`） | — | — | — | — | 0 | **未讀** |
| D0 | `/etc/goaa/console.env` | 240 | 600 `aika:aika` | — | 9 | 0 | 未讀 |
| D0 | `/etc/goaa/worker_secrets.env` | 194 | 600 `root:root` | — | — | — | **以 `aika` 權限不可讀（未提權）** |

- 附註：本輪清單化 C2 PostgreSQL 憑證檔 時，因檔名清單指令誤含內容欄位，**輸出曾出現 PG 憑證檔 明文**；**該內容未寫入任何報告、未上傳、未進入 relay**，本報告僅保留「檔案存在與權限」之事實。後續掃描器已對 18 份報告執行 0 命中驗證。

## 2. 鍵名（僅名稱）

- **C1 `web.env`**：`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`、`CLERK_SECRET_KEY`、`NEXT_PUBLIC_CLERK_SIGN_IN_URL`、`NEXT_PUBLIC_CLERK_SIGN_UP_URL`、`NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL`、`NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL`、`GOAA_AGENT_LOOP_UPSTREAM`、`GOAA_C2_CLERK_AUTH_ENABLED`、`GOAA_CLERK_INSTANCE`、`HOSTNAME`、`NODE_OPTIONS`。
- **C1 `api-3103.env`**：`GOAA_C2_ENV`、`GOAA_C2_DB_HOST/PORT/USER/PASSFILE/SSLMODE/NAME`、`GOAA_C2_PSQL`、`GOAA_C2_SESSION_COOKIE/TTL`、`GOAA_C2_PRIVATE_FILES_DIR`、`GOAA_C2_STORAGE_LABEL/SCANNER/OCR/DOWNLOAD_TTL/MAX_UPLOAD_BYTES/EMAIL_DELIVERY/PUBLIC_BASE_URL`、`GOAA_C2_SESSION_SECRET`、`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`、`CLERK_PUBLISHABLE_KEY`、`CLERK_SECRET_KEY`、`CLERK_AUTHORIZED_PARTIES`、`CLERK_ISSUER`、`GOAA_C2_CLERK_AUTH_ENABLED`。
- **C2 `clerk-api-3103.env`**：同上家族 ＋ `GOAA_C2_MIGRATE_USER/PASSFILE`。
- **C1 `/etc/goaa/secrets.env`**：`GOAA_SECRETS_KEY`、`DEEPSEEK_API_KEY`、`SMTP_HOST/PORT/USER/PASS`、`EMAIL_TO`、`PG_PASSWORD`、`STRIPE_SECRET_KEY`、`STRIPE_PUBLISHABLE_KEY`、`STRIPE_WEBHOOK_SECRET`、`GOAA_FRONTEND_URL`、`GOAA_CUSTOMER_CONSOLE_URL`、`GOAA_CONNECT_RETURN_URL`、`GOAA_SERVICE_RETURN_URL`。
- **D0 `console.env`**：`CONSOLE_SESSION_KEY`、`POSTGRES_HOST/PORT/DB/USER/PASSWORD`、`OLLAMA_URL`、`EMBED_MODEL`、`ENABLE_RAG_CHAT`。

## 3. Stripe 模式分類（唯一被允許的「值」相關輸出）

| 鍵 | 分類 | 長度 |
|---|---|---|
| `STRIPE_SECRET_KEY` | **TEST**（`sk_test_`） | 32 |
| `STRIPE_PUBLISHABLE_KEY` | **TEST**（`pk_test_`） | 32 |
| `STRIPE_WEBHOOK_SECRET` | `whsec_` | 38 |

- **C1 全 `/opt` 掃描 `sk_live`/`pk_live` = 0**；C2 = 0；C3 = 0。

## 4. 秘密衛生風險（唯讀觀察，未處置）

1. `/etc/goaa/secrets.env` 被 **4 個 unit** 載入，其中 `goaa-router`、`goaa-model-router` **不需要** Stripe/SMTP/PG 金鑰（最小權限問題）。
2. `/etc/systemd/system/openclaw.service.bak-pre-oauth-20260906` — **備份 unit 檔仍在 systemd 目錄**且載入 secrets.env ⇒ 建議移出（待 Tao 授權）。
3. C2 staging 同時存有 `app_role_secret` ＋ 兩份 PostgreSQL 憑證檔 ＋ 多份 `.env` 備份。
4. D0 `worker_secrets.env`（root, 600）不在 `aika` 可讀範圍 ⇒ 未評估；如需盤點需 Tao 授權以 root 讀**鍵名**。

## 5. 本輪全部更正彙總

| # | 前輪結論 | 本輪實測 | 影響 |
|---|---|---|---|
| 1 | 「D0 worker 因 `ROUTER_URL` 名錯而不註冊／不被派遣」 | **錯誤**：程式預設值＝C1 公網 IP，D0 worker **在線且心跳新鮮** | 14 號報告 §4；風險改為「換址時靜默失效」與「通道走公網」 |
| 2 | 「Stripe Connect 轉帳未實作（`transfers.create` = 0）」 | **錯誤**：實作在 `stripe_checkout.create_transfer`，`orders.py:865` 有呼叫 | 16 號報告 §4／§6 |
| 3 | 「`/agent-loop` 等路徑 Gate 由 middleware 決定」 | 以 live curl 證據收斂：同意（307 → `/client-login`） | 見 golden-freeze 報告 |
| 4 | 舊記憶中的 C1 IP `134.199.227.⟨10⟩` | 實測 `134.199.227.⟨108⟩` | 15 號報告 §6（待 Tao 由面板確認） |
