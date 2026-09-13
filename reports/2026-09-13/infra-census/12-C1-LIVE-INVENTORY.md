# 12 — C1：Live / Production 盤點（唯讀）

- 命名：**C1 = Live / Production**（本輪起統一）
- 唯讀紀律：未部署、未重啟、未改設定、未寫 DB；env 只列**鍵名**，不印值；Stripe 只做**模式分類**。

## 1. 身分與網路

| 項目 | 值 |
|---|---|
| hostname | `goaa-aika-cloud-1` |
| Public IP | `134.199.227.⟨108⟩`（`eth0/20`） |
| 內網 | `10.48.0.5/16`、`10.124.0.2/20`；docker：`172.17.0.1/16`、`172.18.0.1/16`、`172.19.0.1/16` |
| Cloudflare Tunnel | `66ad1cc0-…-99237900285d`（ingress 見 17 號報告） |
| ufw | active；allow：`OpenSSH`、`80`、`443`、**`8080`（註解 "GOAA Model Router API"）**、out `587`；**`5432` 未放行** |

## 2. 服務與埠

| 埠 | 服務 | unit | ExecStart / 工作目錄 |
|---|---|---|---|
| 3100 | **前端（live）** | `goaa-web.service`（enabled+active, MainPID 3135985, `Restart=on-failure`） | `/opt/goaa-frontend/node/bin/node /opt/goaa-frontend/current/server.js`；`WorkingDirectory=/opt/goaa-frontend/current` |
| 3103 | **Agent-Loop 後端（live）** | `goaa-platform-api-3103.service`（enabled+active, MainPID 3135920, **`Restart=no`**） | `/opt/goaa-platform/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 3103`；`WorkingDirectory=/opt/goaa-platform/backend` |
| 8080 | **Worker 控制面 / goaa-router** | `goaa-router.service`（active） | `/opt/goaa/venv/bin/uvicorn api:app --host 0.0.0.0 --port 8080`；`WorkingDirectory=/opt/goaa/router` |
| 18789 | **golden order/agent API（openclaw）** | `openclaw.service`（enabled+active, MainPID 2995045） | `/opt/goaa/venv/bin/uvicorn main:app --host 0.0.0.0 --port 18789`；`WorkingDirectory=/opt/goaa/runtime` |
| 5432 | **PostgreSQL（docker）** | `docker-proxy` pid 1501/1507 | `goaa-postgres` 容器 |
| — | Worker Agent（`do-cloud-1`） | `goaa-worker-agent.service`（enabled+active, MainPID 2995004） | `/opt/goaa/venv/bin/python3 /opt/goaa/workers/agent.py`；`WORKER_ID=do-cloud-1`、`ROUTER_API=http://127.0.0.1:8080`、`POLL_SEC=5` |
| — | Cloudflare Tunnel | `cloudflared.service`（enabled+active, MainPID 2111569） | — |

- openclaw 自我健康：`GET /health` → `{"status":"ok","node":"AKC-DO-001","version":"2.0.0"}`。
- `GET /api/v1/order/orders` → **401**（活著且有守門）。

## 3. 前端 release

| 項目 | 值 |
|---|---|
| `current` → | `/opt/goaa-frontend/releases/40c8546e152bf5fad8d7a9d0033f17cab4cbcda8` |
| `BUILD_ID` | `FW7iufKj5JrPAz9Kx2SkX`（位於 `current/.next/BUILD_ID`） |
| release 數 | **22** |
| rollback 點 | `/opt/goaa-frontend/releases/76af718b0568992c900b72d1aff5aad2516046dc` |
| 部署時間 | Sep 12 08:27（目錄）/ current symlink Sep 12 08:59:58 UTC |
| 樹 | 1,969 檔 / 28,138,994 bytes（前輪 R5b-4 複核值） |

## 4. 後端樹

| 路徑 | 內容 | 指紋 |
|---|---|---|
| `/opt/goaa-platform/backend` | `app/{main,db,clerk_auth,clerk_identity,golden_session,audit,security,storage,ai_review,config}.py`、`migrations/` | 37 檔；`*.py` 排序 sha16 `dfc7af087dfb1403` |
| `/opt/goaa/router` | `api.py`（52,131 B）、多個 `.backup-*` | git `1d67bd6` |
| `/opt/goaa/runtime`（**openclaw**） | **42 個 `.py` / 85 項**；`orders.py`（103,486 B, sha16 `074ad1d7cc231c7c`）、`stripe_checkout.py`、`stripe_pay.py`、`order_db.py`、`order_state.py`、`invoice_pdf.py`、`demo_order_phase4.py`、`stageb_*`/`stagec_*`、`agent_*.py`、`auth_oauth.py` | git `1d67bd6`，remote = `git@github.com:taofengtx/goaa-ai-frontend.git` |
| `/opt/goaa/backups` | 3 項（含 `stripe-return-urls-20260904/…-orders.py.orig`） | — |

## 5. 資料庫

- 容器 `goaa-postgres`；DB：`goaa`（**45 表**，golden commerce）、`goaa_platform`、postgres/template0/template1。
- `pg_stat_activity`：`goaa` 有 2 條連線（`172.17.0.1/32` ×1、local ×1）⇒ **本輪當下無外部寫入端連入**。

## 6. env 檔（**只列鍵名，不印值**）

| 檔 | bytes | mode/owner | sha16 | 鍵數 | 含 STRIPE |
|---|---|---|---|---|---|
| `/opt/goaa-frontend/env/web.env` | 481 | 640 `root:goaa-web` | `c72e86561eac7292` | 11 | 0 |
| `/opt/goaa-platform/env/api-3103.env` | 986 | 600 `goaa-platform` | `711f5817b41fc31d` | 25 | 0 |
| `/etc/goaa/secrets.env` | 932 | 600 `root` | — | 15 | **3** |
| `/etc/goaa/openclaw.env` | 661 | 600 | — | — | 0 |
| `/etc/goaa/console.env`（D0 用同名檔） | 240 | 600 `aika` | — | 9 | 0 |

- `web.env` 鍵名：`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`、`CLERK_SECRET_KEY`、`NEXT_PUBLIC_CLERK_SIGN_IN_URL`、`NEXT_PUBLIC_CLERK_SIGN_UP_URL`、`NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL`、`NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL`、`GOAA_AGENT_LOOP_UPSTREAM`、`GOAA_C2_CLERK_AUTH_ENABLED`、`GOAA_CLERK_INSTANCE`、`HOSTNAME`、`NODE_OPTIONS`。
- `/etc/goaa/secrets.env` 鍵名：`GOAA_SECRETS_KEY`、`DEEPSEEK_API_KEY`、`SMTP_HOST`、`SMTP_PORT`、`SMTP_USER`、`SMTP_PASS`、`EMAIL_TO`、`PG_PASSWORD`、**`STRIPE_SECRET_KEY`**、**`STRIPE_PUBLISHABLE_KEY`**、**`STRIPE_WEBHOOK_SECRET`**、`GOAA_FRONTEND_URL`、`GOAA_CUSTOMER_CONSOLE_URL`、`GOAA_CONNECT_RETURN_URL`、`GOAA_SERVICE_RETURN_URL`。
- `/etc/goaa/secrets.env` 被 **4 個 unit** 載入：`goaa-router.service`、`goaa-model-router.service`、`openclaw.service`、`openclaw.service.bak-pre-oauth-20260906`（後者為備份檔，**卻仍是可載入 unit 檔**，屬衛生風險）。

## 7. 風險（唯讀觀察）

1. `8080/tcp` 對全網放行（D0.3 已由 Tao 撤銷，維持現狀）；`0.0.0.0:8080`、`0.0.0.0:18789`、`0.0.0.0:5432`（docker-proxy）皆綁全介面（5432 未在 ufw 放行）。
2. `api-3103.service` 為 `Restart=no`（前輪已記錄，未修）。
3. `/etc/systemd/system/openclaw.service.bak-pre-oauth-20260906` 是「備份 unit 檔」，內含 `EnvironmentFile=/etc/goaa/secrets.env` ⇒ 建議移出 systemd 目錄（**待 Tao 授權**）。
4. Stripe 金鑰為 **TEST 模式**（見 16 號報告），但同一 env 亦承載 golden order API ⇒ 若放入 live key，將在**不需重建**的情況下於下次重啟生效。
