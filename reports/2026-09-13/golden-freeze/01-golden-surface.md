# 01 — GOAA 產品黃金面（5 個 surface）鎖定

- 日期：2026-09-13
- 性質：**唯讀盤點**（未改任何檔、未部署、未付款、未 push 生產）
- 依據：Tao 2026-09-13 00:58 令【Golden Freeze + GitHub Archaeology】§A
- 說明：本輪**不做重新設計**，只把「現在真正在跑的五個面」以可複驗的證據固定下來。

## 0. 五個面（鎖定）

| # | surface | 正式網址 | 目前狀態 | 承載 |
|---|---|---|---|---|
| 0 | Homepage | `https://goaa.ai` → `https://www.goaa.ai/`（308） | live 200（Framer 託管） | 品牌、入口、登入/註冊、AI 對話入口 |
| 1 | Customer | `https://planning.goaa.ai/agent-loop/customer` | 307 → 統一登入 | AI Butler：Chat / Matters / Skills Marketplace / Get Licensed / Earning Paths |
| 2 | Agent | `https://planning.goaa.ai/agent-loop/agent` | 307 → 統一登入 | AI Agent；一級菜單 5 項 |
| 3 | Admin | `https://planning.goaa.ai/agent-loop/admin` | 307 → 統一登入 | AI Admin；一級菜單 6 項 |
| 4 | Worker / Developer | 令文此段未完整送達（見 §4） | — | 以現況盤點代替 |

## 1. 三端一級菜單（以生產前端 `40c8546` 的實際路由檔為準）

生產前端（C1 `current` 指向的 release，見 07 報告）內 `app/agent-loop/` 的實際頁面檔：

- **Customer（`/agent-loop/customer`）**：`page.tsx`、`earning/`、`get-licensed/`、`skills/`
  ⇒ 對應 Chat / Matters / Skills Marketplace / Get Licensed / Earning Paths。
- **Agent（`/agent-loop/agent`）**：`page.tsx`（Overview）、`opportunities/`、`orders/`、`knowledge/`、`my-ai/`
  ⇒ 一級菜單 **恰好 5 項**：Overview / Opportunities / Service Orders / Knowledge Base / My AI ✓ 與令文一致。
- **Admin（`/agent-loop/admin`）**：`page.tsx`（Overview）、`applications/`、`content/`、`finance/`、`system/`、`support/`
  ⇒ 一級菜單 **恰好 6 項**：Overview / Applications / Content / Finance / System / Support ✓ 與令文一致。
- 另有 `app/agent-loop/apply/page.tsx`（代理商申請入口）與 `app/agent-loop/login/page.tsx`（已退役、只做轉址）。

結論：**三端菜單在生產樹內已實作且與令文逐項相符**；令文要求的「鎖定」在代碼層已成立，本輪不需任何變更。

## 2. 統一登入面（生產實況）

| 請求 | 結果 |
|---|---|
| `GET /client-login` | **200**、10,893 bytes、內含 `clerk` 相關字樣 15 處（`clerk-js` 2 處）⇒ 這就是統一登入卡 |
| `GET /goaa-clerk-login` | 307 → `/client-login` |
| `GET /agent-loop/login?next=/agent-loop/customer` | 307 → `/client-login?next=%2Fagent-loop%2Fcustomer` |
| `GET /agent-login` | 307 → `/client-login?next=%2Fagent-loop%2Fagent` |

⇒ 對外**只有一個登入入口 `/client-login`**；所有舊路徑都 307 收斂到它並保留 `next`。與 23:16 鎖定的「統一 `/client-login`」一致。

## 3. 未登入的三端守門（live）

`/agent-loop/customer`、`/agent-loop/agent`、`/agent-loop/admin` 三者皆 **307**：

```
/agent-loop/customer → /agent-loop/login?next=/agent-loop/customer
/agent-loop/agent    → /agent-loop/login?next=/agent-loop/agent
/agent-loop/admin    → /agent-loop/login?next=/agent-loop/admin
```

⇒ 三端皆 fail-closed；未登入不會看到任何面板內容。`/planning`（黃金規劃頁）為公開 200（16,147 bytes）。

## 4. surface 4（Worker / Developer）— 令文截斷，以現況補齊

令文 §A 第 4 點（Worker / Developer）**未完整送達**（在「**4 Worker / Developer**（」之後中斷）。
本輪不臆測其應有形狀，僅羅列**現況可稽核的 Worker / Developer 面**：

1. **Aika-Box 本機主控台**：`/home/aika/Projects/goaa-ai-main/local-console/`（monorepo 內、**已在 GitHub**，19 檔；uvicorn `main:app` 跑在 `127.0.0.1:5188`，另 bind tailnet `100.114.37.90:5188`；已連續執行 33 天）。
2. **Worker 控制面 API**：C1 `goaa-router`（`127.0.0.1`/`0.0.0.0:8080`）＝ dispatch 控制面，端點含 `/worker/heartbeat`、`/tasks/next/{worker_id}`、`/task/complete`、`/workers/status`、`/workers/register`、`/workers/metrics`。
3. **Worker 節點**：6 台（見 09 報告），各以 `goaa-worker-agent` 每 ~5 秒輪詢。
4. **未成形的第四端（UI）**：`app/agent-dashboard/*`、`app/portal-preview/{customer,agent,admin}` 為既有樣板；**沒有**獨立的「Worker/Developer 入口頁」在生產菜單上。

⚠️ 待 Tao 補送令文 §4 原文後再行對齊；本輪不新增任何 UI。

## 5. 結論

- 黃金面 = **1 首頁 + 3 端（customer / agent / admin）+ 1 個統一登入卡 `/client-login`**；第 5 面（Worker/Developer）待令文補齊。
- 全部皆已在生產（C1）運行，且三端菜單與令文逐項相符。
- 本報告**未觸發任何變更**。
