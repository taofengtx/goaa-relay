# Round C1.8 — AGENTS 走 Clerk 卡、登入後進 `/agent-loop/agent`（patch 0012）C2 隔離驗證報告

- 日期：2026-09-11（UTC）
- 範圍：**只動 C2 與中轉倉**；不碰 C1、`api.goaa.ai`、`goaa_c2`、支付、nginx；本輪只重啟 `goaa-c2-clerk-ui-3102.service` **一次**
- 拓撲：`Browser → Next 13102 BFF → FastAPI 3103 → goaa_c2test`
- 基線：前端 `f719b275dea8e340f9321176d296af8e137a5197`（C1.7b）；後端 `dc64591b…`（未動）
- 產物：`patches/0012-round-c1-8-agents-clerk-entry.patch`、`snapshots/frontend-40c8546e/`（638 檔）

## 0. 本輪產出摘要

| 項 | 結果 |
|---|---|
| P0 唯讀預檢（離線臨時 worktree） | 全綠，原樹 HEAD 不變 |
| S2 正式套用 | 恰 4 檔 +76/−48；FE HEAD → `40c8546e152bf5fad8d7a9d0033f17cab4cbcda8` |
| 靜態驗證 | tsc 0；31 支 cjs 全綠；run-all **104 passed / 0 failed** |
| 兩個受保護頁 | `client-login` 與 `agent-login` **0 diff**（位元組不變） |
| S3 建置 | rc=0；可部署子集內完整金鑰形態 **0**；dev 實例主機名 **0 檔** |
| S3 部署 | 1969 檔；tar sha 相符；主機端 manifest 非 OK **0** |
| S3 重啟（一次） | rc=0；MainPID `2023476` → `2025892`；`2026-09-11 18:22:23 UTC` |
| V（HTTP + 瀏覽器） | 全部符合預期；AGENTS 入口 → Clerk 卡 → 落 `/agent-loop/agent` |
| 收尾 DB | `goaa_c2test` 所有 subject 的 live token **全為 0** |

## 1. S1 — patch 0012 入倉（前情）

- 來源：Tao 於聊天上傳；sha256 `1af0851c13058637f417fe5fdf5ca8c967dbca6fb99f5d6645358cc62b3a1609`（16,353 B）相符。
- `git apply --stat`：恰 **4 檔、+76/−48** — `app/lib/clerk-entry.ts`(28/14)、`middleware.ts`(8/7)、`scripts/c2-clerk/test-entry-rules.mjs`(19/11)、`scripts/c2-clerk/test-middleware.mjs`(21/16)。
- 入倉 commit `025dc96`（relay `main`），已 push。
- 語意：`/agent-login` 由「黃金產品路徑、不可動」改列為**與 Clerk 同管時退役的舊入口**；`AGENT_PORTAL_NEXT = "/agent-loop/agent"` 為登入落點。

## 2. P0 — 唯讀預檢（先驗證、後套用）

在臨時 worktree `/tmp/c18-preflight`（`node_modules` 以符號連結指回原樹）先跑，**全綠才進 S2**：

| 步驟 | 預期 | 實際 |
|---|---|---|
| 0 | 原 FE HEAD = `f719b275` | `f719b275dea8e340f9321176d296af8e137a5197` ✓ |
| 1 | `git apply --check` 乾淨 | `APPLY_CHECK: CLEAN` ✓ |
| 2 | `git am` 不衝突 | `AM_RC=0` ✓ |
| 3 | 恰 4 檔 +76/−48 | 28/14、8/7、19/11、21/16 ✓ |
| 4 | 受保護頁 0 diff | 空（0 diff）✓ |
| 5 | `npx tsc --noEmit` | `TSC_RC=0`，0 行 ✓ |
| 6 | 31 支 `scripts/test-*.cjs` | `PASS=31 FAIL=0` ✓ |
| 7 | `bash scripts/c2-clerk/run-all.sh` | `TOTAL: 104 passed, 0 failed, group_rc=0`（entry-rules 20、middleware 16、bff 14、signout 7、candidate-shape 8、golden-routes 16、golden-session 23）✓ |
| 8 | 移除臨時 worktree；原樹 HEAD 仍 `f719b275` | remove rc=0；HEAD `f719b275` ✓ |

## 3. S2 — 正式套用（原工作樹）

以受限 `--allowedTools` 白名單的 Claude Code 執行（**未**用 `--dangerously-skip-permissions`），Aika 僅啟動/等待/回傳日誌；`claude exit rc=0`。隨後 Aika 逐項獨立核驗：

| 項 | 預期 | 實際 |
|---|---|---|
| 新 commit | 4 檔 +76/−48 | `40c8546e152bf5fad8d7a9d0033f17cab4cbcda8`（parent `f719b275`）✓ |
| `git show --numstat` | 4 行 | `clerk-entry.ts` 28/14、`middleware.ts` 8/7、`test-entry-rules.mjs` 19/11、`test-middleware.mjs` 21/16 ✓ |
| `git diff f719b275 HEAD` | 只 4 檔 | `4 files changed, 76 insertions(+), 48 deletions(-)` ✓ |
| `client-login` 硬閘 | 0 diff、27006 B、`08b31389…43a1` | 0 diff；27006 B；`08b31389d40e6350a1e293d64c94e99e79c86c22581e20e6560eaca9750743a1` ✓ |
| `agent-login` 硬閘 | 0 diff（舊頁不改） | 0 diff；5346 B；`52558d504250da006d0f98cbfd1f18d8310f223282a17758252abb41515c2556` ✓ |
| 工作樹 | 僅未追蹤建置產物 | `?? tsconfig.tsbuildinfo` ✓ |
| `tsc` / 31 cjs / run-all | 0 / 31 全綠 / 104 | 0；`PASS=31 FAIL=0`；`TOTAL 104 passed, 0 failed` ✓ |
| 快照 | `frontend-40c8546e` | 638 檔（`find -type f` 實測 638）✓ |
| relay | push | `025dc96..fe4c2b7`；`main = fe4c2b7bef9de9da309e5d03b336f9b50940cca9` ✓ |

## 4. S3 — build / 打包 / 部署 / 重啟

### 4.1 建置
- 建置 shell 內 Clerk／付費／instance 變數計數 **0**（值從未輸出）；`.next` 先清空重建。
- `next build --no-lint` **rc=0**、`✓ Compiled successfully`；5 個路由皆非預渲染（`/`、`/planning`、`/client-login`、`/connect-pass`、`/goaa-clerk-login`：prerendered? no）。
- 閘門 B（**完整金鑰形態** = 前綴 + ≥10 英數）：`pk_test_` / `pk_live_` / `sk_test_` / `sk_live_` 四者 **0 / 0 / 0 / 0**。
- 可部署子集（`standalone/` + `static/`，1962 檔）：完整形態 **0 / 0 / 0 / 0**；`server/`（214 檔）亦 **0 / 0 / 0 / 0**。
- 裸前綴僅記錄計數（不作停止條件）：整個 `.next` `pk_test_` 20、`pk_live_` 18、`sk_test_` 13、`sk_live_` 8；其中可部署子集為 8 / 7 / 5 / 3，其餘落在 webpack 持久化快取（7 檔內 323 / 270 / 158 / 113）。**未出現任何完整金鑰。**
- Clerk 開發實例主機名在產物內 **0 檔**。
- C1.6／C1.7 回歸標記仍在：`data-goaa-paid` 1、`connect-pass-closed` 1、opening-soon 文案 1、`GOAA_PAID_CONNECTION` 1、`GOAA_CLERK_INSTANCE` 5、`clerk-continue-as-guest` 1、cal.com 預約 7 檔。

### 4.2 打包
- 1969 檔；manifest 1969 行；`tar sha256 = 34b59b63c877e75cdace985c4931841d3147e3b5abfdf2fd0a58317953b90c7c`；8,857,386 B。
- `BUILD_ID = 28IP1GvAGURvF1PHRk8EL`；layout chunk `layout-f567b39096b24041.js`（root layout 未被本輪改動，與 C1.7 相同）。

### 4.3 部署
- TS = `20260911-112127`；本機/遠端 tar sha 相符；解包 1969 檔。
- 備份 `/opt/goaa-test/ui-clerk-20260910.bak-20260911-112127`（34M）；`rsync -a --delete` rc=0；owner `goaa-c2loop:goaa-c2loop`。
- 主機端重跑 manifest：非 OK 行 **0**；磁碟 `BUILD_ID` 同上；可部署產物完整金鑰 **0**。

### 4.4 重啟（本輪唯一一次）
- 重啟前唯讀 env 檢查（只印計數）：10 行、`root:goaa-c2loop 440`、`CLERK_SECRET_KEY`（測試前綴）1 行、`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`（測試前綴）1 行、`GOAA_CLERK_INSTANCE` 0、`GOAA_PAID_CONNECTION` 0。
- `systemctl restart goaa-c2-clerk-ui-3102.service` → **rc=0**。
- **審批卡在 Tao 的對話中出現並經 Tao 核准**（本輪 Aika 直接提交最小形式的重啟指令、未包腳本、未改用 kill）。
- MainPID `2023476` → **`2025892`**；`ActiveEnterTimestamp = Fri 2026-09-11 18:22:23 UTC`；`KillMode=control-group`、`TimeoutStopUSec=20s`。

### 4.5 重啟後唯讀核驗
- unit **active**；BFF health（`/api/agent-loop/health`）**200**：`service=goaa-c2-agent-loop`、`environment=c2-dev`、`database = 127.0.0.` `1:5433/goaa_c2test`、`server_version 16.15`、`reachable=true`、`production_ready=false`、`production_resources_used=false`。
- `/client-login` **200**、10945 B、chunk ref 10、**非 200 = 0**。
- 本機隧道 `ssh -f -N -T -L 13102:127.0.0.` `1:13102 do-c2`（PID `1772631`）存活。

## 5. V — 驗證

### V1 `/agent-login`（舊經紀人入口）
| 請求 | 預期 | 實際 |
|---|---|---|
| `GET /agent-login` | 307 → `/client-login?next=%2Fagent-loop%2Fagent` | **307**，`Location: /client-login?next=%2Fagent-loop%2Fagent`（40 B）✓ |
| `GET /agent-login?foo=bar` | 同上 | **307**，同上 ✓ |
| `GET -L /agent-login` | 200、卡片在 | **200**、11012 B、`clerk-continue-as-guest` ×2、`Continue as guest` ×2、舊 `aria-label="Continue as guest"` **0** ✓ |

### V2 `next` 形狀 → 卡片落點
| `next` | 實際 |
|---|---|
| `%2Fagent-loop%2Fagent` | 200、11012 B、卡 ×2、卡內 `forceRedirectUrl = /agent-loop/agent` ✓ |
| `%2Fagent-loop%2Fcustomer` | 200、11030 B、卡 ×2、`forceRedirectUrl = /agent-loop/customer` ✓ |
| `//evil.example` | 200、10973 B、卡 ×2、收斂為 `forceRedirectUrl = /planning` ✓ |
| `%2Fplanning` | 200、10962 B、卡 ×2、`forceRedirectUrl = /planning` ✓ |

### V3 尾斜線與黃金頁
- `/agent-login/` → **308** → `/agent-login`（12 B）→ 續 307 → 卡片；為 Next 自身尾斜線正規化。
- `/planning`（黃金落地頁）→ **200**、16199 B、卡片標記 **0**（未被任何卡替換）✓

### V4 瀏覽器端到端：導覽列 AGENTS → 卡片 → 登入 A → 落 `/agent-loop/agent`
- `/planning` 起始：`localhost:13102`、`window.Clerk.user/session` 皆 false、`client_token` null。
- 導覽列「LOGIN / REGISTER▾」→ 選單 **AGENTS**（href 仍為 `/agent-login`，**舊頁未改**）→ 點擊後 URL = `http://localhost:13102/client-login?next=%2Fagent-loop%2Fagent`，Clerk 卡掛載（"Continue to GOAA" / "Continue with Google" / Email address / "Continue as guest"）。
- 帳號 **A = `c2e2e+clerk_test@example.com`**（驗證碼 `424242`）→ 落 **`/agent-loop/agent`**；`client_token` 出現（32 hex，本報告只寫前綴 `c57287b3…`）；`window.Clerk.user/session` 皆 true。
- **A 具經紀人權限**（`user_roles`：role `agent`，2026-09-11 09:10:01 UTC 授予）→ 渲染**真實 Agent panel**（導覽：Overview / Opportunities / Service Orders / Knowledge Base / My AI / ⇄ Back to Customer）。
- 登出（MY ACCOUNT▾ → LOG OUT）→ `client_token` null、Clerk user/session false、卡片回來；落點 `/client-login?next=/agent-loop/customer`（見 §8 觀察）。

### V5 `Continue as guest`
- `/client-login` → "Continue as guest"（`/planning`）→ 落 **`/planning`**、`client_token` null、Clerk user/session false、導覽列回「LOGIN / REGISTER▾」✓

### V6 直接走 `/agent-login` 入口（帳號 B）
- 帳號 **B = `c2e2e2b+clerk_test@example.com`**（`424242`）→ 落 **`/agent-loop/agent`**；`client_token` 出現（前綴 `0a467be4…`）。
- **B 無經紀人執照** → 落點頁顯示黃金頁自身的伺服器端授權閘：`agent_role_required`、「Agent panel is locked」，並提供 "Back to user dashboard"(`/agent-loop/customer`) 與 "Sign in with another account"(`/agent-loop/login`)。**兩者都落在 `/agent-loop/agent`**：有權限者見到面板，無執照者見到鎖定頁（fail-closed，非本輪改動的閘）。
- 由 `/agent-loop/customer` 登出 → 回 `/client-login?next=/agent-loop/customer`、`client_token` null、Clerk false。

### 5.1 追加 curl（Tao 令，不需重啟）
| 請求 | 預期 | 實際 |
|---|---|---|
| `GET /agent-loop/login?next=%2Fagent-loop%2Fagent` | 307，next=`/agent-loop/agent` | **307**，`/client-login?next=%2Fagent-loop%2Fagent` ✓ |
| `GET /agent-loop/login` | 307，next=`/agent-loop/customer` | **307**，`/client-login?next=%2Fagent-loop%2Fcustomer` ✓ |
| `GET /agent-login?resume=1&reason=order&order=abc` | 307，next=`/agent-loop/agent` | **307**，`/client-login?next=%2Fagent-loop%2Fagent` ✓ |
| 跟隨兩個落點 | 卡片在 | 各 **200**、11012 B / 11030 B、卡 ×2、`forceRedirectUrl` 分別為 `/agent-loop/agent`、`/agent-loop/customer` ✓ |
| `GET -L /agent-login` | 卡片在 | **200**、11012 B、卡 ×2 ✓ |

### 5.2 身份與會話映射（本輪新簽發的 token）

| 帳號 | subject id | token 前綴 | 簽發（UTC） | 撤銷（UTC） | DB live |
|---|---|---|---|---|---|
| A `c2e2e…` | `4717531f-6806-49ef-8326-6185f3ea1d3d` | `c572` | 18:23:16.589846 | 18:23:42.217027 | 1 → 0 |
| B `c2e2e2b…` | `f99342a6-7a3a-463f-8738-a94501297727` | `0a46` | 18:24:20.118770 | 18:24:57.081734 | 1 → 0 |
| A（第二次） | `4717531f-…` | `af22` | 18:26:20.242806 | 18:26:36.648909 | 1 → 0 |

- 機制不變（C1.7 已驗）：`business_tokens.user_id` 存 **subject id**；瀏覽器憑據 = `localStorage.client_token` + `Authorization: Bearer`；**撤銷是唯一槓桿**（無 TTL）。本輪無任何跨帳號殘留：A 登出後 B 登入、B 登出後 A 再登入，每輪 live 皆正確為 0/1。
- 收尾（三個 token 全部撤銷後）：`c2e2e` 0/10、`c2e2e2b` 0/5、`c1round` 0/4、`c2admin` 0/1、`c2e2e2` 0/1 —— **所有 subject live 全為 0**。

## 6. 截圖

| 檔 | 位元組 | sha256（前 16） | 內容 |
|---|---|---|---|
| `v1-agent-card.jpg` | 27858 | `f9f637aea0d6dcc3` | `/agent-login` 307 後落地的 Clerk 卡（Continue to GOAA / Google / Email / Continue as guest） |
| `v6-agent-portal.jpg` | 84212 | `4c500ca8d296a831` | A 登入後落點 `/agent-loop/agent`：真實 Agent panel（含 Licence 區塊） |
| `v6-agent-locked.jpg` | 33846 | `9b2fe2873c5a616a` | B 登入後落點 `/agent-loop/agent`：`agent_role_required` 鎖定頁 |

**局限說明**：截圖只作「頁面狀態」證據。本輪的身份/換帳號證據採用 **localStorage 憑據 + 後端 session/revoke 記錄 + DB live 計數**（§5.2），不以截圖位元組推論身份。

## 7. 觀察（既有行為，非本輪引入）

1. **經紀人入口登出後回 `/client-login?next=/agent-loop/customer`**。來源為 `app/lib/agent-loop/signout.ts:25` 的常數 `CLERK_SIGN_OUT_REDIRECT = '/client-login?next=/agent-loop/customer'`（agent-loop 命名空間共用），由 `GoldenSessionBridge` 的 `signOut(redirectUrl)` 執行。**patch 0012 未觸及此檔**（0012 僅 4 檔），亦不在本輪範圍內 → 記錄為既有行為：`/agent-loop/agent` 的 LOG OUT 會回到「客戶」登入卡而非「經紀人」卡。是否要在後續輪次改成對稱落點，待 Tao 決定。
2. 導覽列 AGENTS 連結的 `href` 仍是 `/agent-login`（舊頁面原始檔 0 diff），**流量由 middleware 收口**，頁面原始碼未被改寫。
3. 落點頁的權限判定完全由伺服器端（DB `user_roles` / 執照）決定，每請求重檢；本輪未繞過、未放寬。
4. 本輪無任何 C1／`api.goaa.ai`／`goaa_c2`／支付／nginx 寫入；`/connect-pass` 未觸發（未操作付費相關頁面）。

## 8. 未解決 / 待確認

- §7.1 的登出落點不對稱（客戶卡 vs 經紀人卡）——**只報告，未修改**。
- `REPORT` 內所有主機位址僅以迴圈位址形式出現；Clerk 開發實例主機名以省略寫法 `lenient-phoenix-…` 表示。
- 測試帳號 B 無經紀人執照屬**刻意的測試資料狀態**，非缺陷。

## 9. 秘密掃描（推送前）

對 `reports/2026-09-11/c1-8/` 全部 **4 檔**（`REPORT.md` + 三張 jpg）以腳本掃描，**實測**：

| 樣式 | 命中 | 判讀 |
|---|---|---|
| 完整金鑰形態（`"sk"+"_test_"` / `"sk"+"_live_"` / `"pk"+"_test_"` / `"pk"+"_live_"` 後接 ≥8 英數） | **0** | — |
| 私鑰標頭 / AWS AKIA / GitHub PAT / 連線字串 / `"pass"+"word="` 鍵值 / `"Bearer "` 長憑據 | **0** | — |
| Clerk 開發實例主機名 | **0** | 報告只寫省略形 `lenient-phoenix-…` |
| 迴圈位址樣式 | **0** | 報告一律用切分寫法（`127.0.0.` + `1`） |
| 32 位以上十六進位字串 | **9** | 全部良性：commit sha（`f719b275…`×2、`40c8546e…`×2、`fe4c2b7b…`）與 sha256 摘要（`1af0851c…`、`08b31389…`、`52558d50…`、`34b59b63…`） |

**總命中 = 9，全部為良性字面；完整金鑰、憑據、私鑰、密碼樣式 = 0。** 三張 jpg 二進位內容零命中。

報告內所有掃描樣式均以**切分寫法**書寫（例：迴圈位址寫成 `127.0.0.` + `1`、金鑰前綴寫成 `"sk" + "_test_"`），避免報告自我命中使計數膨脹。

## 附錄：環境（無秘密）

- unit：`goaa-c2-clerk-ui-3102.service`（`EnvironmentFile=/opt/goaa-test/env/clerk-ui-3102.env`，10 行、`PORT=13102`、`HOSTNAME=localhost`、`GOAA_AGENT_LOOP_UPSTREAM` 指向本機 3103；無 `GOAA_PAID_CONNECTION`、無 `GOAA_CLERK_INSTANCE`）
- 部署目錄：`/opt/goaa-test/ui-clerk-20260910`（1969 檔、`BUILD_ID 28IP1GvAGURvF1PHRk8EL`）
- 備份鏈（最新）：`.bak-20260911-112127`（34M）
- 後端：3103（未改動）、`goaa_c2test` migrations `0001..0006`
- 本輪新增：新增 repo 內檔案僅 `patches/0012…`、`snapshots/frontend-40c8546e/`、本報告目錄；**未改動** C1、3100/3101、`goaa_c2`、Golden Flow、支付、nginx。
