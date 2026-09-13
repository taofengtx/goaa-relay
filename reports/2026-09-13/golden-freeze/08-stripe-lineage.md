# 08 — Stripe / 結算 / 轉帳 / 退款 / webhook / 冪等：血緣與缺口

- 日期：2026-09-13；唯讀（未呼叫任何 Stripe API、未付款、未寫 DB）。

## 1. 🔴 生產上的決定：$39.90 連線「發版時是關閉的」

生產前端（`40c8546`）新增 `app/lib/paid-connection.ts`，檔頭原文（節錄）：

> 「At launch the golden order API (api.goaa.ai) is not changed and does not accept the business credential that Clerk sign-in produces, so a signed-in customer's purchase would fail at checkout. Until that API is updated the purchase stays closed: the entry points show "coming soon" with the 30-minute booking instead, and `/connect-pass` shows a notice instead of mounting the checkout page (so it never calls the order API).」
> 開關：`GOAA_PAID_CONNECTION`（**設為 `open` 才開；未設＝關**）；重開**不需重建**，改 env + restart 即可。

對應 commit：`049a0a6`（2026-09-11，`round C1.6: launch switch closes the $39.90 connection (coming soon + 30-min booking)`）。
配套測試：`scripts/test-paid-connection-gate.cjs`（離線、不連網、不付款）。
⇒ 這解釋了首頁殘留的 `cal.com/goaa.ai/30min` CTA（見 02 報告）。

## 2. 程式碼血緣

| 位置 | Stripe 實作 | 狀態 |
|---|---|---|
| `origin/main`（GitHub，2026-08-25） | `app/api/stripe/checkout/route.ts`、`pass-status/route.ts`、`webhook/route.ts`（3 檔） | **生產已刪**（`git diff origin/main 40c8546` 顯示三個 `D`） |
| `40c8546`（C1 生產前端） | 無 stripe API 路由；改 `paid-connection.ts` gate | 現行 |
| `dc64591`（C1 生產後端） | 無 stripe 模組 | 現行 |
| `/opt/goaa/router`（C1，`api.goaa.ai` 的服務） | **0 命中**（`api.py` 1093 行 + `db.py` 449 行；端點全是 dispatch/worker/session） | 它不是 commerce API |
| `package.json`（`origin/main` 與 `40c8546`） | **無 `stripe` 依賴** | ⇒ 舊路由應為 REST/fetch 直呼 |

## 3. 資料模型與資料（C1 `goaa` 庫；已直接查證）

| 對象 | 表 | 列數 | 關鍵欄位 |
|---|---|---|---|
| 付款 payment | `goaa_order_payments` | **41**（`succeeded` 39 / `pending` 2） | `provider`、`provider_payment_id`、`provider_payment_intent_id`、`amount_cents`、`currency`、`status`、**`idempotency_key`**、`payment_type`、`paid_at`、`metadata` |
| 結算 settlement | `goaa_order_settlements` | **14** | `payment_id`、`agent_id`、`amount_cents`、`status`、**`stripe_connect_account_id`**、`payout_id`、**`transfer_id`**、**`transfer_status`**、`settled_at`、`notes` |
| 發票 invoice | `goaa_order_invoices` | **7** | `invoice_number`、`customer_user_id`、`agent_id`、`amount_cents`、`status`、`payment_status`、`pdf_key` |
| 估價 estimate | `goaa_order_estimates` | **19** | — |
| 服務單 | `goaa_order_service_orders` | **36** | — |
| 商機 | `goaa_order_opportunities` | **10** | — |
| 代理訂閱 | `goaa_order_agent_subscriptions` | **0** | — |
| 點數 | `credits` / `credit_transactions` | 4 / **0** | — |

> `goaa_order_settlements` 出現 **Stripe Connect** 專屬欄位且已有 14 列 ⇒ 「結算/轉帳」的**資料層確實存在且曾被使用**。

## 4. 缺口清單（回答「舊 golden E2E 現在缺哪些對象」）

| 對象 | 資料層 | 程式層（本輪盤點範圍內） |
|---|---|---|
| checkout session | —（無對應表） | GitHub `origin/main` 有；**生產已刪** |
| webhook 接收/驗簽 | — | 同上（生產已刪） |
| payment 寫入端 | ✓（41 列有資料） | **未定位**（`goaa-router` 內 0 命中；生產前端亦無） |
| settlement 產出端 | ✓（14 列，含 Connect 欄位） | **未定位** |
| transfer / payout | ✓（`transfer_id`/`payout_id`/`transfer_status`） | **未定位** |
| refund | **✗ 無 refund 表** | 未定位（樣式命中多屬其他語意） |
| 冪等 idempotency | ✓（`idempotency_key` 欄） | 檔案命中：`origin/main` 11、`76af718` 4、`40c8546` **29**（僅代表字樣出現，非實作證據） |
| 訂閱 subscription | ✓ 表存在 | **0 列**（未啟用） |
| 點數 credits | ✓ 表存在 | 幾乎空（4 / 0） |

## 5. 判讀與建議

1. **重開 $39.90 的前置條件是架構級的**：`api.goaa.ai`（golden order API）必須先接受 Clerk 簽發的業務憑證 —— 這正是 `paid-connection.ts` 檔頭寫明的理由。在此之前，任何「重開付款」的嘗試都會在 checkout 失敗。
2. **付款/結算的實作端在 C1 上未被定位**（第三份可能在其他服務或已被刪的路由）。下一輪若要接真實業務，第一步應是「**定位寫入 `goaa_order_payments` / `goaa_order_settlements` 的服務**」，而不是重寫。
3. 本輪**未做任何變更**，也未呼叫任何外部支付 API。
