# 03 — 統一登入與三端守門（live 稽核）

- 日期：2026-09-13；方法：唯讀 GET（5 + 4 次），記錄 status / bytes / `Location`。
- 未使用任何憑證、未登入、未寫 DB。

## 1. 登入面收斂

| 請求 | status | bytes | `Location` |
|---|---|---|---|
| `GET /client-login` | **200** | 10,893 | — |
| `GET /goaa-clerk-login` | 307 | 5,925 | `/client-login` |
| `GET /agent-loop/login?next=/agent-loop/customer` | 307 | 43 | `/client-login?next=%2Fagent-loop%2Fcustomer` |
| `GET /agent-login` | 307 | 40 | `/client-login?next=%2Fagent-loop%2Fagent` |

- `/client-login` 回應內含 `clerk` 字樣 15 處（`clerk-js` 2 處、`@clerk/nextjs` 1 處）⇒ **對外唯一登入卡就是 `/client-login`**。
- 舊路徑（`/agent-loop/login`、`/agent-login`、`/goaa-clerk-login`）**全部 307 收斂**，且 `next` 被保留與 URL-encode。

## 2. 三端守門（未登入）

| 請求 | status | bytes | `Location` |
|---|---|---|---|
| `/agent-loop/customer` | 307 | 6,400 | `/agent-loop/login?next=/agent-loop/customer` |
| `/agent-loop/agent` | 307 | 6,385 | `/agent-loop/login?next=/agent-loop/agent` |
| `/agent-loop/admin` | 307 | 6,385 | `/agent-loop/login?next=/agent-loop/admin` |
| `/planning` | **200** | 16,147 | — |

⇒ 三端 fail-closed；`/planning`（黃金規劃）維持公開。

## 3. 與架構固定條款的對照（00:44:31）

- 唯一鏈路 `Browser → Next 3102(BFF) → FastAPI 3103 → goaa_c2test`：C1 上對應為 `Browser → goaa-web(3100) → goaa-platform-api(3103) → goaa_platform`。**本輪未改任何一環。**
- 統一入口 `/client-login` ✓ 與 23:16 鎖定一致。
- 無內部共享密鑰/exchange 端點、無 Next 直連 PG、無瀏覽器傳 email/userID/role：本輪唯讀未發現反例，惟**完整複驗留待下一輪**（本輪未讀 3103 全路由）。

## 4. 未解（本輪不動，僅記錄）

- 首頁 5 處 CTA 仍走 `/agent-login`（多一次 307）；建議下一輪改直連 `/client-login`。
- `3103`（後端）對「無憑證」回 `401 missing_clerk_session`，而 BFF 先擋回 `401 clerk_session_required`（文案不一致）；帶無效 token 則回 **503 + `Clerk is enabled but not configured:`**（措辭誤導，應為 401）。此為 R5b-4 §F 已知項。
