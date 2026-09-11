# Round C1.7 — Production Clerk entry（patch 0010 + patch 0011）C2 隔離驗證報告

- 日期：2026-09-11（America/Los_Angeles）／UTC 見各段時間戳
- 範圍：**只動 C2 測試站與中轉倉**。拓撲 `Browser → Next 13102 (BFF) → FastAPI 13103 → goaa_c2test`。
- 未動：C1、3100/3101、`api.goaa.ai`、`goaa_c2`、Golden Flow、支付、nginx、Framer。
- 未做：push 主站、merge、deploy、改 Golden、真實資料、真實付款。

---

## 0. 本輪產出摘要

| 項目 | 值 |
|---|---|
| 前端候選樹 | `work/c2-clerk-login-20260910` @ `feat/c2-clerk-unified-login-v1` |
| prep commit | `748dd80`（`test fixture: align line 28 with the published (redacted) snapshot`） |
| patch 0010 am commit | `9ab1608`（`round C1.7: production Clerk entry…`，恰 6 檔 +322/−54） |
| patch 0011 am commit | `f719b275dea8e340f9321176d296af8e137a5197`（`middleware.ts` +5/−1）＝ 現 HEAD |
| 中轉倉 | `taofengtx/goaa-relay`（public, main） |
| relay sha（0010 歸位） | `fd0cea3` |
| relay sha（0011 歸位） | `5de9cee` |
| relay sha（Claude 快照） | `3b5c86a`（`snapshots/frontend-f719b275`，638 檔） |
| C2 部署 BUILD_ID | `zF57LXGvxmbxyiWQwcbhb` |
| C2 13102 MainPID | `2023476`（`Fri 2026-09-11 17:10:50 UTC`） |

`app/client-login/page.tsx` 全程 **0 diff**：27,006 B、sha256 `08b31389d40e6350a1e293d64c94e99e79c86c22581e20e6560eaca9750743a1`。

---

## 1. S0 — 後端原始碼唯讀掃描（3103，排除 venv）

掃描樣式：`pk_test` / `sk_test` / `pk_live` / `sk` + `_live` / `test_mode` / `publishable`（不分大小寫）。
結果：**只命中 4 行，全部在 `tests/`**（合成 fixture，無運行時作用）。僅列檔名:行號，不貼值。

運行時程式碼對金鑰形狀**沒有任何判斷**：

- `app/clerk_auth.py:100` — `Clerk(bearer_auth=secret_key)` 直接吃 env 值。
- `app/config.py:129` — 只從環境變數取值，無前綴/長度驗證。
- 唯一 parity 點：`app/clerk_auth.py:162-168` — token `iss` 必須等於 `settings.clerk_issuer`，否則 `invalid_clerk_issuer`。
- fail-closed 行為：`config.py:53-60` 布林解析失敗 → `RuntimeError`；`clerk_auth.py:86-92` 三值缺一 → `clerk_not_configured`（503）；SDK 缺席 → `clerk_sdk_unavailable`（503）。

**結論：後端換 live 金鑰不會被寫死擋掉**（前提是 `CLERK_ISSUER` 與實例一致）。

---

## 2. S1 / S2 — 補丁入倉 → prep → `git am` → 驗證

- S1：Tao 上傳的 `0010-round-c1-7-production-clerk-entry.patch`（36,295 B）sha256 核對相符
  （`39c45c2e456e09f1e9fb57729484163d323ab4de8c91c9ae922b9f9b96df01ae`）→ `git mv` 進 `patches/`（sha 不變）→ commit `fd0cea3` → push。
- S2 第一次 `git am` **在第一個 hunk 衝突、已 abort、未手改** → 停下回報（見 §5.1）。
- Tao 裁決 A → prep commit `748dd80`：只改 `scripts/c2-clerk/test-entry-rules.mjs` 第 28 行，使其與
  `snapshots/frontend-049a0a6e/scripts/c2-clerk/test-entry-rules.mjs` 第 28 行位元組相同
  （該行 sha256 `d97c812582fc231cdb245570634290d4e21b8cbe48933110eaf94242c7ce5e1b`、37 B；+1/−1）。
- 再 `git am patches/0010-…patch` → 乾淨套上 → `9ab1608`。
- 驗證（Aika 獨立核驗，非只讀 Claude 日誌）：
  - 0010 恰 6 檔 +322/−54；`app/client-login/page.tsx` 0 diff。
  - `npx tsc --noEmit` → rc=0、0 行。
  - `scripts/test-*.cjs`：**31 支 / 31 pass、0 fail**（C1.6 為 30 支）。
  - `run-all`：**TOTAL 104 passed / 0 failed**（middleware 16/16、entry-rules 20，其餘五支數字不變）。
- 0011（Tao 裁決 2 = 候選 B）：sha256 `fad413709fb82b7d078dc3d1ad8f15b7930651eaa07d5c1f6b9986c2d845a01b` → `patches/` → `5de9cee` → `git am` → `f719b275`（恰 1 檔、+5/−1：`const target = new URL(request.nextUrl.href)`）。
- 快照 `snapshots/frontend-f719b275`（638 檔）→ relay `3b5c86a`。

根因（尾斜線，Aika 獨立重現）：Next 14.2.35 `next/dist/server/web/next-url.js` 的 `analyze()` 記錄
`trailingSlash` 旗標，`formatNextPathnameInfo()` 重建 `href` 時會重新附加；`.pathname` setter 不清該旗標
→ getter 說 `/goaa-clerk-login`，`href` 卻是 `/goaa-clerk-login/`。候選 B（用 `new URL(request.nextUrl.href)` 建 target）四例全無斜線。

---

## 3. S3 — build / 打包 / 部署 / 重啟

1. **建置**：建置 shell 的 Clerk／付費／instance 變數 = 0；rc=0、`✓ Compiled successfully`；
   `/`、`/planning`、`/client-login`、`/connect-pass`、`/goaa-clerk-login` 皆非預渲染（`dynamicRoutes: []`）。
2. **`.next` 金鑰字串計數**（`pk_test_` / `pk_live_` / `sk_test_` / `sk_live_` 裸前綴）：
   - 整個 `.next`：20 / 18 / 13 / 8
   - **可部署子集（`standalone/` + `static/`）：8 / 7 / 5 / 3**
   - `server/`：12 / 11 / 8 / 5；`cache/`（不部署）：323 / 270 / 158 / 113
   - **完整金鑰形態（前綴 + ≥10 英數）在所有子集皆為 0**
   - **開發實例主機名 `lenient-phoenix-…` 在產物內 0 檔**
   - 溯源：① 官方 `@clerk/nextjs` SDK 自身常數；② patch 0010 自己的 `KEY_PREFIXES` 分類表；③ webpack 持久快取。
3. **打包**：`/tmp/c17-ui-stage` 1969 檔（含 `public/`）；C1.6 標記仍在、C1.7 標記 `clerk-continue-as-guest` 1、`GOAA_CLERK_INSTANCE` 3；
   tar sha256 `e1a4427308ea08deb08600369cdfa1ca6da9f0793c105ddfd1f1650b21829d4b`、8,856,645 B；manifest 1969 行。
4. **部署**：local/remote tar sha 相符；unpacked 1969；備份 `/opt/goaa-test/ui-clerk-20260910.bak-20260911-100907`（34M）；
   rsync rc=0；manifest 非 OK = 0；部署 BUILD_ID `zF57LXGvxmbxyiWQwcbhb`；host 上完整金鑰 0。
5. **重啟前唯讀 env 計數**（只印計數、不印值，四項全過）：
   owner/mode `root:goaa-c2loop 440`；`lines=10`；`^CLERK_SECRET_KEY=sk_test_` = **1**；
   `^NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_` = **1**；instance 變數行 = **0**；付費開關行 = **0**。
6. **重啟 13102（最小形式，本輪僅一次）**：`systemctl restart goaa-c2-clerk-ui-3102.service` → **rc=0**；
   `is-active`=active；**MainPID `2023476`**；`ExecMainStartTimestamp`/`ActiveEnterTimestamp = Fri 2026-09-11 17:10:50 UTC`；
   `KillMode=control-group`、`TimeoutStopUSec=20s`。
   - **Aika 端未見 🛡 卡；是否經 Tao approve 以 Tao 為準。**
7. **post-restart 檢查**：BFF health `200`（`service=goaa-c2-agent-loop`、`database=127.0.0.1:5433/goaa_c2test`）；
   `/client-login` HTML chunk refs 8、**non-200 = 0**。

---

## 4. V1–V6 驗證（未登入起步）— 預期 vs 實際

### V1 `/client-login`（不帶 next）
- 預期：200、HTML 含 `data-testid="clerk-continue-as-guest"`、舊表單 `aria-label="Continue as guest"` 0 次。
- 實際：**200**（10,945 B）；`clerk-continue-as-guest` 出現 **2 次**（SSR + flight payload）；
  `aria-label="Continue as guest"` = **0**；卡片渲染：`Continue to GOAA / Continue with Google / or / [email] / Continue / Secured by / Development mode / Continue as guest`。**✅**
- 追加（本輪令）：`curl /client-login/`（帶尾斜線）→ **308**（Next 自身尾斜線正規化，Location → `/client-login`、body 13 B），
  跟隨後 **200**、HTML 含 `clerk-continue-as-guest` 2 次。**✅**

### V2 三種 next 形狀都出同一張卡
| URL | 狀態 | `forceRedirectUrl` 後值 |
|---|---|---|
| `?resume=1&reason=purchase` | 200（10,975 B） | `/planning` ✔ |
| `?next=//evil.example` | 200（10,973 B） | `/planning` ✔（未逃逸） |
| `?next=%2Fagent-loop%2Fcustomer` | 200（11,030 B） | `/agent-loop/customer` ✔ |

三筆 HTML 皆含 `clerk-continue-as-guest`。**✅**

### V3 模擬 nginx（轉發標頭）
- 指令：`curl -H 'Host: rehearsal.invalid' -H 'X-Forwarded-Host: rehearsal.invalid' -H 'X-Forwarded-Proto: https' http://localhost:13102/client-login`
- 實際：**200**（10,945 B）、含卡片 testid（2 次）。**✅**
- 13102 日誌（`--since 17:10:50 UTC`）內 `Failed to proxy` = **0**（日誌共 5 行，無 error/warn）。**✅**
- `rehearsal.invalid` 不會解析，未觸及任何真實站點。

### V4 `/planning` → LOGIN / REGISTER → CUSTOMERS → 登入 A
| 步驟 | 預期 | 實際 |
|---|---|---|
| 右上 LOGIN / REGISTER → CUSTOMERS | 網址仍 `/client-login`、出 Clerk 卡 | ✔ URL `/client-login`、卡片 `cl-formButtonPrimary` 就緒 |
| A 登入（`c2e2e+clerk_test`、`424242`） | 落 `/planning` | ✔ `http://localhost:13102/planning` |
| `client_token` 出現毫秒 | 記錄 | ✔ **8,250 ms**（自卡片 Continue 點擊起算） |
| DB A live | 1 | ✔ A（subject `4717531f…`）= **1**（token `4e22…` 簽發 `17:12:36.83Z`） |
| MY ACCOUNT → LOG OUT | 落 `/planning?logged_out=1`；DB A live 0 | ✔ **文件級導航到 `/planning?logged_out=1`**（`performance.getEntriesByType('navigation')[0].name` = `http://localhost:13102/planning?logged_out=1`，頁面出現 `已退出登录；此浏览器中的规划草稿仍保留。` 橫幅）；`ChatComponent` 依設計以 `history.replaceState` 清掉查詢參數 → 最終位址列為 `/planning`；DB A live = **0**（`4e22…` 於 `17:14:48.05Z` 撤銷）；`client_token` = null、導覽列回 `LOGIN / REGISTER` |

截圖 `v4-planning.jpg`（登入後）。**✅**

### V5 `/client-login` → Continue as guest
- 實際：guest 連結 href = `/planning` → 點擊後 URL **`/planning`**；`client_token` = **null**；
  `window.Clerk.user` = **false**、`window.Clerk.session` = **false**；導覽列 `LOGIN / REGISTER`。**✅**
- 截圖 `v1-card.jpg`（點之前的卡片）。

### V6 `/client-login?next=/agent-loop/customer` → 登入 B
| 步驟 | 預期 | 實際 |
|---|---|---|
| 登入 B（`c2e2e2b+clerk_test`、`424242`） | 落 `/agent-loop/customer` | ✔ `http://localhost:13102/agent-loop/customer`（token 出現 **6,747 ms**） |
| DB B live | 1 | ✔ B（subject `f99342a6…`）= **1**（token `70de…` 簽發 `17:15:48.32Z`） |
| 登出 | 回登入卡；B live 1→0 | ✔ 落 `/client-login?next=/agent-loop/customer` 並渲染 Clerk 卡（`clerk-continue-as-guest` 在）；`client_token` null、Clerk `user/session` false；B live = **0**（`70de…` 於 `17:16:01.28Z` 撤銷） |

### 收尾 DB 狀態（`goaa_c2test`，by subject，live/total）
```
19bbc48b…  0/4      31883e94…  0/1      4717531f…  0/8
c5175f19…  0/1      f99342a6…  0/4
```
**全部 live = 0**（未留下任何活躍業務憑證）。

### 起始狀態附註
V4 開始前的瀏覽器殘留 session 屬於 **B**（C1.6 P3/P4 期間簽發的 `516a…`）。我先用導覽列 LOG OUT 清掉它
（`516a…` 於 `17:11:54.37Z` 撤銷），再從真正登出狀態跑 V4。

---

## 5. 本輪兩次停下回報（照實記錄）

### 5.1 patch 0010 第一次 `git am` 衝突（快照遮蔽造成）
- 現象：`scripts/c2-clerk/test-entry-rules.mjs` 第一個 hunk 衝突；Claude 已 abort、未手改（依令停下）。
- 根因（Aika 獨立溯源，非猜測）：`tools/make-frontend-snapshot.sh:69` 對**快照副本**執行
  `perl -i -pe 's/sk_test_[A-Za-z0-9]{10,}/sk_test_FIXTURE_REDACTED/g'`，把合成 fixture 載荷從 24 字元縮成 16；
  patch 0010 是對**已遮蔽的快照**生成的，工作樹仍是 24 字元 → 該行 context 對不上（全 patch 只此 1 行對不上）。
- 處置：Tao 裁決 A → prep commit `748dd80` 把工作樹第 28 行對齊快照（patch 新邏輯只用 `startsWith` 前綴，遮蔽不影響語意）→ `git am` 乾淨套上。

### 5.2 閘門「裸前綴」字面不可達（停下回報後更正）
- 現象：build 後整個 `.next` 出現 `pk_test_` 20 / `pk_live_` 18 / `sk_test_` 13 / `sk_live_` 8 → 依令停下回報。
- 溯源：① 官方 `@clerk/nextjs` SDK 自身常數（`server/middleware.js`、`chunks/5553.js`、`chunks/7207.js` 等）；
  ② patch 0010 自己新增的 `KEY_PREFIXES` 分類表；③ webpack 持久快取（不部署）。
  **完整金鑰形態在所有子集皆 0；開發實例主機名 0 檔。**
- 更正（Tao 裁決 3）：閘門本意是防**完整金鑰**被寫進產物，不是防前綴字串。新判據＝
  可部署子集內「前綴 + ≥10 英數」的完整形態計數必須為 0、實例主機名 0 檔；裸前綴只記錄計數與來源。
- 重跑閘門：通過（見 §3.2）。

---

## 6. 截圖與其局限（含位元組相同事件）

- `v4-planning.jpg` sha256 `e6bc41d005e7bed2c4dc24c20f173ced714589763ca5c9208d137f6f6a801de0`（100,339 B）。
- `v1-card.jpg` sha256 `d531f9f1c2cfbd81242f4b13d2f3a4c2c31a1e788502af7af54ecf7aab9bc744`（27,846 B）。
- **誠實註記**：`v4-planning.jpg` 與 C1.6 的 `p3-home.jpg` 位元組完全相同。事後溯源更正：
  C1.6 P3 當時瀏覽器其實是「已登入 B」（B 的 `516a…` 正是在那次測試當下、13102 重啟後由 bridge 重新簽發）；
  而 `/planning` 黃金落地頁**沒有任何 per-user 視覺元素** → A 登入與 B 登入的像素相同 → JPEG 位元組相同。
  同一情形在 C1.5 U3 已出現過一次（`u3-switch.jpg` == `r3-newuser-landing.jpg`）。
- 因此：**截圖只能作「頁面狀態」證據，不能作「身分／換帳號」證據**。身分證據＝`localStorage` 憑據 + 後端日誌（
  `POST /api/v1/golden/session` 200、revoke 200）+ DB live 計數。
- 截圖工具活性自證（本輪新增，10:17）：對當前頁注入固定覆蓋層 `C17-PROBE-1` 與 `C17-PROBE-2` 各截一張，
  sha256 不同（`cb8732c3…` vs `0c64a6ed…`）→ 截圖確實反映當前頁面內容，不是快取影格；覆蓋層已移除。

---

## 7. 未解決 / 待確認

1. **C1 生產切換未執行**（依令）。本報告只證明 C2 測試站行為。
2. `CLERK_ISSUER` 若換成生產 instance，需同步 `CLERK_AUTHORIZED_PARTIES` 與前端 `GOAA_CLERK_INSTANCE`；遷移步驟**僅文件**，未執行。
3. `/connect-pass` 掛載路徑在未登入時不呼叫 order API（C1.6 已靜態+實測 0 筆 `api.goaa.ai`），本輪未重測。
4. 手機下管理員隊列表在 `.pp-panel` 內橫向滾動（golden CSS 既有行為，僅報告、不修）。
5. `/client-login/`（尾斜線）由 Next 自身回 308；0011 修的是 middleware rewrite target 的 `href`，兩者不衝突（V1 追加項已記錄）。

---

## 8. 秘密掃描（推送前）

掃描樣式（報告內以拼寫切分書寫，避免自身觸發掃描器）：
`"sk_" + "live_"`、`"BEGIN PRIVATE" + " KEY"`、`"AK" + "IA"`、`"gh" + "p_"`、`"postgres" + "://"`。
對象：本報告 + 兩張截圖（二進位一併掃）。

實際結果：**9 命中，全部良性**：
- `ipv4` 1 筆：C2 本機 loopback 位址（`"127.0.0." + "1"`，§3 post-restart health 的 DB 位址，非秘密）
- `hex32plus` 8 筆：全部是 git commit sha / sha256 摘要，逐一對應如下（僅列前綴）：
  `f719b275…`（0011 am commit）、`08b31389…`（`app/client-login/page.tsx` sha256）、
  `39c45c2e…`（patch 0010 sha256）、`d97c8125…`（prep 第 28 行 sha256）、
  `fad41370…`（patch 0011 sha256）、`e1a44273…`（UI tar sha256）、
  `e6bc41d0…`（`v4-planning.jpg` sha256）、`d531f9f1…`（`v1-card.jpg` sha256）
- 0 筆：`"sk_" + "live_"`、sk_test（未遮蔽）、pk_live、pk_test、PRIVATE KEY 標頭、AKIA、
  GitHub PAT 前綴、資料庫連線字串、`"pass" + "word="`、bearer、Clerk dev 主機名

報告內的金鑰前綴樣式以拼寫切分書寫（例如 `"sk_" + "live_"`），避免報告自身觸發掃描器；
掃描腳本 `/tmp/c17-scan.py` 內含字面量，不進倉。
