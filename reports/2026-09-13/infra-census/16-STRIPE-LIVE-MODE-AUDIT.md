# 16 — ★ Stripe / 真金流「寫入點」審計（唯讀；未付款、未改 key）

- 令文要求：建立統一環境盤點後，回答「**现在哪里会发生真钱流**」、「**不要碰任何 C1 相关 live secret**」。
- 本輪紀律：**只列鍵名、只做模式分類（LIVE/TEST/WHsec/EMPTY）；未印出任何 key、未抄錄任何值**。

## 1. 結論（三句話）

1. **C1 目前不存在任何 live 模式 Stripe 金鑰**（全 C1 `/opt` 掃描 `sk_live` / `pk_live` 命中 **0**）；現存 3 個 Stripe 鍵為 **TEST** 模式。
2. **真錢流唯一的程式路徑是**：`https://api.goaa.ai` → C1 `127.0.0.1:18789`（`openclaw`）→ `/api/v1/order/*` → `order_db.py` → C1 `goaa` DB 的 `goaa_order_*` 表。
3. 該路徑目前被**三重關閉**：金鑰為 TEST、`STRIPE_SECRET_KEY` 若為空即走 **mock 模式**、前端 `GOAA_PAID_CONNECTION` **未設＝關閉**（$39.90 顯示 coming soon）。

## 2. 金鑰位置與模式（值未讀）

| 檔案 | mode/owner | 鍵名 | 模式分類 |
|---|---|---|---|
| `/etc/goaa/secrets.env`（932 B） | `600 root:root` | `STRIPE_SECRET_KEY` | **TEST**（長度 32） |
| 同上 | | `STRIPE_PUBLISHABLE_KEY` | **TEST**（長度 32） |
| 同上 | | `STRIPE_WEBHOOK_SECRET` | `whsec_`（長度 38） |
| 同上 | | `GOAA_SECRETS_KEY`、`DEEPSEEK_API_KEY`、`SMTP_*`、`EMAIL_TO`、`PG_PASSWORD`、`GOAA_*_URL` | （非 Stripe） |

- **載入者（4 個 unit）**：`goaa-router.service`、`goaa-model-router.service`、`openclaw.service`、`openclaw.service.bak-pre-oauth-20260906`。
  ⇒ **goaa-router 與 model-router 本身不含 Stripe 程式碼**（其 `api.py` 為 dispatch/控制面），卻持有這些金鑰 ⇒ **最小權限原則未落實**。
- C2：**完全無 Stripe 鍵**。D0：`console.env` 無 Stripe 鍵（`worker_secrets.env` 由 `aika` 不可讀，未提權）。
- 全 C1 `/opt` 搜尋 `sk_live` / `pk_live` → **0**。

## 3. 程式碼（golden commerce 實作）

路徑：**C1 `/opt/goaa/runtime`**（`openclaw`, `:18789`；git `1d67bd6`，remote `git@github.com:taofengtx/goaa-ai-frontend.git`）。

| 檔 | bytes | sha16 | 職責 |
|---|---|---|---|
| `orders.py` | 103,486 | `074ad1d7cc231c7c` | `APIRouter(prefix="/api/v1/order")`；**66 個端點**：訂單/報價/付款/交付/補充/訊息/檔案/admin |
| `stripe_checkout.py` | 9,990 | `53abfba37212c768` | **Stripe REST client（httpx，零新依賴）**：Checkout Session、webhook 簽章、Connect account、account link、**Connect Transfer**、onboarding 狀態 |
| `stripe_pay.py` | 5,742 | `2465f5220b11274b` | 付款確認（`confirm_mock_payment`）、`handle_webhook`（簽章驗證） |
| `order_db.py` | — | — | 寫入 `goaa_order_payments`（L275 INSERT／L324 成功／L334 失敗）、`goaa_order_settlements`（L537 INSERT／L576 `status='paid', settled_at, payout_id`） |
| `order_state.py` | — | — | 狀態機（含 `refund_pending`／`refunded`／`settlement_ready`／`settled`） |
| `invoice_pdf.py` | 6,146 | — | 發票（`goaa_order_invoices`） |
| `demo_order_phase4.py` | 17,587 | — | Phase 4 E2E（`--stripe` = 真 Stripe **Test** 模式；`POST /webhook/stripe` 冪等重放） |

- 關鍵常數：`stripe_checkout.CONNECTION_FEE_CENTS = 3990`（**$39.90**）、`CONNECTION_FEE_LABEL = "GOAA Connection Fee (30 days)"`、`SERVICE_FEE_LABEL = "GOAA Professional Service Fee"`。
- 金鑰來源（程式自述）：`STRIPE_SECRET_KEY`（空＝mock 模式）、`STRIPE_WEBHOOK_SECRET`、`STRIPE_CONNECT_ACCOUNT`（可選固定 Test 收款帳號）。

## 4. golden E2E 對象對照表（**本輪定案**）

| 對象 | 程式碼 | 資料 | 判定 |
|---|---|---|---|
| Checkout Session | ✅ `stripe_checkout.create_checkout_session`（`orders.py:1663`，金額＝3990） | — | **在** |
| Webhook 驗簽 | ✅ `orders.py:/webhook/payment`（讀 `stripe-signature`）→ `stripe_pay.handle_webhook`（`hmac`/`hashlib`） | — | **在** |
| Payment | ✅ `order_db.py` INSERT/UPDATE | `goaa_order_payments` **41**（39 succeeded / 2 pending） | **在** |
| 冪等 | ✅ `stripe_pay`（7 命中）＋ `idempotency_key` 欄 | 有欄 | **在** |
| Settlement | ✅ `order_db.py`（含 `payout_id`、`settled_at`）＋ `/admin/settlements`、`/admin/settlements/{sid}/settle` | `goaa_order_settlements` **14** | **在** |
| Connect Account / Onboarding | ✅ `create_connect_account`、`create_account_link`、`get_connect_account`、`/agents/me/connect-account{,/link,/verify}` | `stripe_connect_account_id` 欄 | **在** |
| **Connect Transfer（撥款）** | ✅ **`stripe_checkout.create_transfer`，`orders.py:865` 實際呼叫** | `transfer_id`／`transfer_status` 欄 | **在（更正見 §6）** |
| Refund | ⚠️ 僅**狀態機＋admin 端點**（`/admin/orders/{id}/refund`、`/refunded`）；**未見任何 Stripe refund API 呼叫** | — | **半在** |
| Invoice | ✅ `invoice_pdf.py` | `goaa_order_invoices` **7** | **在** |

## 5. 真錢流「會不會發生」的判定

| 條件 | 現況 | 後果 |
|---|---|---|
| live 金鑰存在？ | **不存在**（TEST/whsec） | 不可能扣真錢 |
| `STRIPE_SECRET_KEY` 空？ | 未確認（值未讀）；但模式為 TEST | 空 ⇒ mock 模式 |
| 前端 $39.90 開關？ | `GOAA_PAID_CONNECTION` **未設＝關閉** | `/connect-pass` 顯示 notice，不叫 order API |
| 服務活著？ | `openclaw :18789` active；`/api/v1/order/orders` → **401** | 有守門 |
| 前端呼叫？ | live release 內 `https://api.goaa.ai/api/v1/order` ×9 | 合約對上 |

⇒ **現階段不會發生真錢流**；但一旦有人把 live key 寫入 `/etc/goaa/secrets.env` 並重啟 `openclaw`（**不需重建前端**），即具備收款能力 ⇒ 這是**唯一需要 Tao 明示授權的金流門檻**。

## 6. 🔴 更正（前輪）

- 前輪以 `grep 'transfers.create'` 得 0 命中，判定「轉帳未實作」——**錯誤**：此實作是**自寫 REST client**（`create_transfer`），非 Stripe SDK ⇒ 用 SDK 符號名搜尋必然漏。**已更正為「Connect Transfer 在」**。
- 教訓：查「有沒有實作」不可只查 SDK 符號，要查**意圖動詞**（create/settle/refund/payout）＋模組職責檔名。

## 7. 風險

1. Stripe 金鑰與 router/model-router **共用同一 env**；這兩個服務不需要金鑰。
2. `/etc/systemd/system/openclaw.service.bak-pre-oauth-20260906` 這個**備份檔仍在 systemd 目錄**且載入 secrets.env。
3. `refund` 只有狀態轉移、沒有向 Stripe 退款 ⇒ 若未來對客承諾退款，會出現帳實不符。
4. C1 `goaa` DB 為 **live commerce 資料庫**（45 表、含 41 筆付款）；任何「測資料」都不得在此進行。
