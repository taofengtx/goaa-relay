# 11 — 唯一基線建議（A / B / C）

- 日期：2026-09-13；本報告**只給建議，未執行任何變更**。

## 1. 三個候選

| 代號 | 基線 | 位置 | 優點 | 風險 |
|---|---|---|---|---|
| **A** | `76af718`（`origin/codex/login-legal-links-20260906`）**＋ 併回 25 個 local-only commit** | GitHub ✓ ＋ 本機 | 生產線的**真實祖先**；GitHub 上可稽核；Stripe/connection 血緣最豐富（`connection_fee` 34、`settlement` 36、`idempotency` 20）；已含支付/連接 UI 與 Matters 全貌 | 併回前須先推送並掃描秘密；過程要小心 `GH013` 誤判 |
| **B** | `origin/main`（2026-08-25） | GitHub ✓ | 最「乾淨」的公開主線；Worker/RAG/Authorization Kernel 最完整 | **落後 20+ commit、缺整個 Clerk/agent-loop 面**；commerce 深度不足（`checkout_session`=0） |
| **C** | `40c8546` / `dc64591`（C1 現行生產） | **只在 C1 + 本機** | 能力**全面最強**（前端 `dispatch` 86、`clerk` 53、`skill` 56、`settlement` 41、`invoice` 31 皆為全樣本最高）；零落差 | **完全不在 GitHub**；單點損毀即不可重建；無法外部審計 |

## 2. 建議：**A（以 C 的內容為準）**

理由：
1. 生產的事實已是 C；但 C 沒有遠端備份 ⇒ **先讓 C 變成可重建**，再談擴張。
2. `76af718` 是唯一「既在 GitHub、又在生產線祖先鏈上」的節點 ⇒ 以它為基線，歷史連續、無需 rebase、無 force-push。
3. 併回後，A 的內容 = C 的內容（因為 C = 76af718 + 25），故**不會引入新設計**，符合「停止擴張 UI」。

## 3. 下一輪的**單一動作**（建議，待 Tao 核准）

> **把兩條 local-only 生產分支推上 GitHub（推送前秘密掃描 0 命中）：**
> `feat/c2-clerk-unified-login-v1`（`40c8546`，+20）與 `feat/c2-pg-agent-loop-v1`（`dc64591`，+5）。

- 這是把「唯一真實來源」從「單機」變成「可重建」的**最低風險、最高價值**一步。
- 不改任何程式、不改 C1、不部署、不動金鑰。
- 已知障礙：`GH013` push protection 曾把 `sk_test_`/`sk_live_` **樣式**誤判 ⇒ 需以切分寫法或佔位字串呈現（relay 版本既有作法：`sk_test_FIXTURE_REDACTED`）。

**替代順序**：若 Tao 不批准推送，則次佳是「在 C1 以 `git bundle` 定期備份兩條分支到 relay（不含秘密）」。

## 4. 不建議

- 不建議以 `origin/main`（B）為基線再往回併 —— 會產生大量反向合併與衝突，且丟失 9 月的整層身分/權限能力。
- 不建議恢復 `app/api/stripe/*` 三支路由 —— 在 `api.goaa.ai` 接受 Clerk 憑證之前，重開只會讓 checkout 失敗（見 08 報告）。
