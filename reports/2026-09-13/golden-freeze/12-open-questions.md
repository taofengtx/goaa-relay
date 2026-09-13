# 12 — 待 Tao 決定的開放問題

- 日期：2026-09-13；本輪**到此 STOP**，以下皆未執行。

## A. 需要令文補齊

1. **令文 §A 第 4 點（Worker / Developer）原文在被截斷**（「**4 Worker / Developer**（」後中斷）。請補送，以便把第 5 個黃金面也鎖定。

## B. 需要授權（涉及變更，本輪未做）

2. **是否批准把兩條 local-only 生產分支推上 GitHub**（`feat/c2-clerk-unified-login-v1` `40c8546` / `feat/c2-pg-agent-loop-v1` `dc64591`）？推送前會做秘密掃描並處理 `GH013` 誤判。
3. **是否批准下一輪先「定位 commerce 寫入端」**（找出寫 `goaa_order_payments` / `goaa_order_settlements` 的服務）？目前該服務未在 `goaa-router`、生產前端、生產後端中出現。
4. **$39.90 連線重開**的前提是 `api.goaa.ai` 接受 Clerk 業務憑證 —— 是否排入下一階段？（現況：`GOAA_PAID_CONNECTION` 未設＝關閉。）

## C. 已知缺陷 / 待收尾（延續 R5b-4 §F 與 R6）

5. `app/lib/paid-connection.ts` 已存在但首頁仍留 1 處 `cal.com` CTA（與開關語意一致，僅待確認是否保留）。
6. 首頁 metadata（`<title>`/`og:title`/`twitter:title`）**仍為舊定位 `GOAA.AI Life&Asset Intelligence`**（3 處）；`description` 亦為舊文案。
7. 首頁 1 處疑似壞連結 `https://help@goaa.ai`（疑應為 `mailto:`）。
8. 首頁 5 處 CTA 走舊路徑 `/agent-login`（多一次 307 才到 `/client-login`）。
9. BFF 先擋 ⇒ 未帶憑證回 `401 clerk_session_required`（與後端 `missing_clerk_session` 文案不一致）；帶無效 token 回 **503 + `Clerk is enabled but not configured:`**（應為 401）。
10. `goaa-platform-api-3103.service` 為 **`Restart=no`**（開機自啟但崩潰不自癒）。
11. 首頁新 Hero 已上線，但外部若仍見舊內容 ⇒ 來源疑為搜尋引擎舊快取／Framer 舊 draft（live HTML 內舊指紋為 0）。
12. `aika-1`（`98.191.202.⟨15⟩`）憑據不可達 ⇒ 需 Tao 自行處理。`aika-core-01` 的 `ROUTER_URL` 應改 `ROUTER_API`（D0.3B 階段二）。
13. 四項**資料層空集合**：`agent_subscriptions`=0、`credit_transactions`=0、`agents`=0、`goaa_agent_skills`=2 ⇒ 這些能力尚未真正啟用。

## D. 本輪邊界聲明

- 本輪**未** merge / rebase / delete / force-push / 改 C1 / 部署 / 付款。
- 本輪**未**觸發任何 🛡 審批卡。
- 本輪**未**寫任何資料庫內容。
- 所有 `psql` 皆為 `select`；所有 HTTP 皆為唯讀 GET（公開端點）。
