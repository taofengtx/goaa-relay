# 05 — 漂移：C1 生產 vs GitHub（可重建性判定）

- 日期：2026-09-13；唯讀。

## 1. 落差事實

| 面向 | C1 生產 | GitHub 上 | 落差 |
|---|---|---|---|
| 前端 | release `40c8546e…`（638 tracked files、`BUILD_ID FW7iufKj5JrPAz9Kx2SkX`） | 無此 commit | **+243 A / 21 M / 5 D**（相對 `origin/main`） |
| 後端 | `dc64591b…`（585 files） | 無此 commit | 相對 `origin/main`：`app/lib` 44、`app/components` 42、`services/c2_agent_loop` 37 等 |
| 共同祖先 | `76af718` | ✓ 有 | 生產 = 祖先 + 25 個 local-only commit |

**無任何遠端 ref 包含 `40c8546` 或 `dc64591`**（`git branch -r --contains` = 空）。

## 2. 生產樹相對 `origin/main` 的獨有領域（前端 `40c8546`）

`git diff --name-status origin/main 40c8546` 前段目錄分佈：
`app/components` 53、`app/lib` 52、`services/c2_agent_loop` 23、`app/agent-loop` 18、`scripts/c2-clerk` 12、`app/portal-preview` 6、`app/agent-dashboard` 6、`app/api` 4、`app/client-dashboard` 3。

其中 **stripe 三支路由被刪**（見 08 報告）：

```
D app/api/stripe/checkout/route.ts
D app/api/stripe/pass-status/route.ts
D app/api/stripe/webhook/route.ts
```

## 3. 可重建性判定

| 問題 | 判定 |
|---|---|
| C1 現行前端能否只靠 GitHub 重建？ | **不能**（缺 20 個 commit） |
| C1 現行後端能否只靠 GitHub 重建？ | **不能**（缺 5 個 commit） |
| 能否靠 GitHub 上的 `76af718` ＋ 本機 25 個 commit 重建？ | **可以**（本機 clone 內兩條分支完整、且工作樹乾淨） |
| 若本機磁碟損毀，生產能否重建？ | **不能** —— local-only 分支無任何異地備份 |
| Aika-Box 主控台（`local-console/`）能否重建？ | **可以**（`origin/main` 等 5 個 ref 的樹摘要皆 `faa9f6ba4603ef9b`，19 檔完全一致） |

## 4. 風險

1. **單點**：唯一一份「最新 25 commit」只存在本機 clone（`/home/aika/Projects/goaa-ai-main` 與 worktrees）。C1 release 目錄是第二份（前端攤平樹 + 後端 37 檔），但後端在 C1 是部署產物、非完整 repo。
2. **可追溯性**：C1 生產 commit 沒有 commit message 進入 GitHub，外部審計看不到九月 8–13 的變更史。
3. **誤判風險**：任何以 `origin/main` 為「最新」的判斷都會落後至少 20 個 commit、且缺少整個 Clerk/agent-loop 能力面。

## 5. 建議（僅建議，未執行）

把 **`feat/c2-clerk-unified-login-v1`（20）與 `feat/c2-pg-agent-loop-v1`（5）兩條 local-only 分支推上 GitHub**（推送前先做秘密掃描；`GH013` 經驗：`sk_test_`/`sk_live_` 樣式會誤判 ⇒ 需以切分寫法或佔位字串呈現）。
這是把「唯一真實來源」變成「可重建」的**單一最高價值動作**。
