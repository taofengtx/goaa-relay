# Round C1.9 — C2 彩排：最終版本全流程（仿 T3）

- **日期**：2026-09-11（America/Los_Angeles）／主機時間 UTC
- **對象**：C2 隔離環境（`goaa_c2test` ＋ Next BFF `13102` ＋ FastAPI `3103`，經本機 SSH 隧道）
- **範圍**：只動 C2 與中轉倉。**未改程式碼、未 build、未重啟 13102、未碰 env**；未碰 C1、`api.goaa.ai`、`goaa_c2`、支付、nginx。
- **本報告所有結論僅適用於 C2 隔離測試環境，不代表生產就緒。**

## 0. 版本錨點（開始前核對，全程未變）

| 錨點 | 期望 | 實測 | 結果 |
|---|---|---|---|
| FE `HEAD` | `40c8546e` | `40c8546e152bf5fad8d7a9d0033f17cab4cbcda8`（`feat/c2-clerk-unified-login-v1`，僅 `?? tsconfig.tsbuildinfo`） | ✅ |
| `BUILD_ID` | `28IP1GvAGURvF1PHRk8EL` | `28IP1GvAGURvF1PHRk8EL`（`/opt/goaa-test/ui-clerk-20260910/.next/BUILD_ID`，mtime `Sep 11 18:19`） | ✅ |
| `MainPID` | `2025892` | `2025892`、`ActiveState=active`、`ActiveEnterTimestamp=Fri 2026-09-11 18:22:23 UTC` | ✅ |

三項全部吻合才開始；全程未執行任何 build／重啟／env 變更。

## 1. 環境與帳號

- 拓撲：`Browser → Next 13102 (BFF) → FastAPI 127.0.0.`＋`1:3103 → goaa_c2test`；本機隧道 `ssh -L 13102:127.0.0.`＋`1:13102 do-c2`（PID `1772631` 存活）。
- 申請人：`c19apply+clerk_test@example.com`（本輪全新註冊，驗證碼 `424242`）。
- 管理員：`c2admin+clerk_test@example.com`（沿用 T3，已有 `admin`，**未再授權**）。
- 起點基線（R1 前）：`users 48`、`business_subject_links 5`、live token `0`、`applications 11`、`licenses 10`；無 `c19apply` 使用者。

## 2. 逐步結果（預期 vs 實際）

### R1 註冊（入口：正式 header）— ✅

| 項 | 預期 | 實際 |
|---|---|---|
| 入口 | `/planning` → LOGIN / REGISTER → Register Now | 一致；`Register Now` href = `/client-login` |
| 卡分支 | 走**註冊**分支（非登入） | URL hash `#/create/verify-email-address`（登入分支為 `#/factor-one`） |
| 驗證碼 | `424242` 可過 | 通過 |
| 落點 | `/planning`（C1.4 修過的 next 語義） | ✅ `/planning` |
| `client_token` | 數秒內出現 | 前綴 `60b6`、長度 32、`6,587 ms` 出現；`window.Clerk.user` = true |
| DB | 新 users 列 + subject 對應，live = 1 | users `48 → 49`、links `5 → 6`、live `1`；`user_id 587efce3-…`、`subject 0a8de149-4eea-4541-9b27-ca220d6d792c`、`linked_via clerk_issuer_subject`、issuer `lenient-phoenix-…clerk.accounts.dev`、Clerk subject `user_3JCJ22rcgCRhiFrJISmS57gpzxU`、created `20:35:06.78Z`；`business_tokens` role `customer`；`user_identities` provider `clerk` 1 列 |

### R2 申請 — ✅

| 項 | 預期 | 實際 |
|---|---|---|
| 進表單 | 客戶頁 Get Licensed → 申請表 | 一致（`/agent-loop/apply`） |
| 合成資料 | 填妥（姓名／電話／信箱／地址／執照） | 一致（`C19 Synthetic Applicant`、`+1-555-01019`、`c19apply.contact@example.com`、`100 Synthetic Avenue, Testville, CA 90000`、`SYN-LIC-C19-0001`/`CA`/`Synthetic Licensing Board`/`2027-12-31`/`Insurance`） |
| 暫存 | Save draft → `Draft` | ✅ info `Draft saved.`（稽核 `application.draft_saved` #99/#100） |
| 上傳 | `POST documents` → **201** | ✅ `POST /api/v1/agent-loop/documents` **201 Created**（`20:36:30.86Z`）；私有檔 `ce5c48e4aab1f11ab7a4a6094a76d757.png`、`38,342 B`、`c2-local-private`/`stub`/`rules-only`；稽核 #101 `document.uploaded`；DB `agent_license_documents` 對本申請**恰 1 列**（`mime_type image/png`、`size_bytes 38342`） |
| 送出 | status → `submitted` | ✅ UI `Submitted — waiting for review` / `Submitted for review.`；DB status `submitted`、`submitted_at 2026-09-11 20:37:00.847732+00`；pre_review `{recommendation: looks_complete, can_auto_approve: false, document_count: 1, expired_licenses: 0}`；稽核 #103 `application.submitted` |
| 負向：`/agent-loop/agent` | `agent_role_required` | ✅ 頁面標題 `Agent panel is locked`、內文首行 `agent_role_required`、伺服器端拒絕（未渲染面板） |
| 負向：`/agent-loop/admin` | `admin_required` | ✅ 頁面標題 `Administrator access required`、內文首行 `admin_required`（未把申請人資料送到瀏覽器） |
| 登出 | token 清空 | ✅ `client_token` null、`window.Clerk.user` false；該用戶 live → `0` |
| 臨時靜態伺服 | 用完停掉、確認埠已關 | ✅ 已停並確認（見 §5） |

### R3 核准 — ✅

| 項 | 預期 | 實際 |
|---|---|---|
| 管理員入口 | `/client-login?next=/agent-loop/admin` 登入 | ✅ 落 `/agent-loop/admin`（token 前綴 `feb1`） |
| 佇列 | 見 R2 申請、**聯絡方式遮罩** | ✅ 列 `C19 Synthetic Applicant` / `c**************t@example.com` / `submitted` / `2026/9/11 13:37:00` |
| 審查詳情遮罩 | 遮罩 | ✅ e-mail `c***…t@example.com`、地址 `10***00`；**電話 `+1-555-01019` 未遮罩**（見 §4 觀察 3） |
| 核准回應 | **200** | ✅ UI `admin.approve applied.`；後端 `POST /api/v1/agent-loop/admin/applications/cf51992d-…/approve` **200 OK**（`20:38:19.04Z`） |
| 稽核 | 有 `application.approve` | ✅ 稽核流 #98–#104 完整；**#104 `application.approve`（actor_role `admin`）**，detail `{status: approved, role_granted: true, role_revoked: false, reason_present: false}` |
| 附帶效果 | — | 申請 status `approved`、`decided_by 923f64ad-…`；`user_roles` 新增 **`agent`**（`20:38:19.042038+00`）；執照列 `4c099945-…`（`SYN-LIC-C19-0001` / `CA` / `2027-12-31`） |
| 管理員登出 | token 清空、live → 0 | ✅、且**全域 live = 0** |

### R4 經紀人入口 — ✅

| 項 | 預期 | 實際 |
|---|---|---|
| 入口 | `/planning` → LOGIN / REGISTER → AGENTS → Clerk 卡 | ✅ `AGENTS` href `/agent-login` → 307 → 卡於 `/client-login?next=%2Fagent-loop%2Fagent` |
| 登入 | 申請人登入 | ✅ 通過（`424242`） |
| 落點 | `/agent-loop/agent` | ✅ |
| 面板 | 看到經紀人面板 | ✅ 真實 **Agent panel**（`AGENT PORTAL`；側欄 `Overview` / `Opportunities` / `Service Orders` / `Knowledge Base` / `My AI` / `⇄ Back to Customer`），**未被鎖定** |
| roles | `agent,user`，無 `admin` | ✅ DB `user_roles` = `agent,user`（無 `admin`） |
| 憑證 | live token | ✅ 前綴 `e5aa`、長度 32（hex32） |

### R5 登出與憑證失效 — ✅

| 項 | 預期 | 實際 |
|---|---|---|
| 登出前記錄 | 長度 + 前 4 碼（不寫全值） | ✅ 長度 `32`、前綴 `e5aa`（hex32） |
| 登出 | token 清空 | ✅ `client_token` null、`window.Clerk.user` false |
| 撤銷後驗證 | `GET /golden/session/verify` → **401 `invalid_business_token`** | ✅ `status 401`、`{"error":{"code":"invalid_business_token","message":"business token is not usable: revoked"}}` |
| 後端佐證 | — | ✅ 日誌同源：`POST /golden/session` 200 → `GET /golden/session/verify` 200（撤銷前）→ `POST /golden/session/revoke` 200 → `GET /golden/session/verify` **401 Unauthorized** |
| 收尾 | 所有 subject live = 0 | ✅ `c19apply 0`、`c2admin 0`、`c2e2e 0`、`c2e2e2 0`、`c2e2e2b 0`、`c1round 0`；**全域 live = 0** |

（執行細節：首輪 token `e5aa` 已撤銷但值隨瀏覽器分頁被重置而消失，無法回放該值；故以第二輪登入（token 前綴 `b8fc`、同長 32）完整重跑「登入 → 記錄特徵 → 登出 → 401 驗證」。兩輪皆已撤銷，收尾 live 皆為 0。見 §4 觀察 1。）

### R6 上線狀態抽查（登入中） — ✅

| 項 | 預期 | 實際 |
|---|---|---|
| `/planning` | `data-goaa-paid` = `closed` | ✅ `documentElement[data-goaa-paid] = "closed"` |
| `/connect-pass` | 「opening soon」說明頁 | ✅ 文案 `Professional connection is opening soon …nothing has been charged…` |
| 外部請求 | 0 筆 `api.goaa.ai` | ✅ 頁面資源條目 `api.goaa.ai` = **0**；瀏覽器請求日誌 `api.goaa.ai` = **0**（全 433 筆往本機 `13102` 或 Clerk dev／`img.clerk.com`） |

## 3. 截圖（章節附圖）

| 檔 | 內容 | bytes | sha256 |
|---|---|---|---|
| `r2-submitted.jpg` | 申請送出（`submitted`） | 89,879 | `0f20054965ef70f141ba86f14dbc5f6e…` |
| `r3-queue.jpg` | 管理員佇列（聯絡方式遮罩） | 79,821 | `2b3c12fef66403251f44eca33f107c14…` |
| `r4-agent-panel.jpg` | 經紀人面板（`/agent-loop/agent`） | 84,628 | `1c9c3806238602502f3192c4007b42fd…` |

說明：截圖僅作**頁面狀態**證據；身分／換帳號／憑證失效的證據一律以 **localStorage 憑據 + 後端 session/revoke 日誌 + DB live 計數** 為準。

## 4. 誠實觀察與偏差（未自行修改任何一項）

1. **R5 首輪無法回放已撤銷 token 的值**：`browser_use` 分頁在回合之間被重置（本環境已知限制），首輪 stash 隨分頁消失，故改用第二輪完成 401 驗證。**非產品缺陷**；兩輪 token 均已在 DB 標記撤銷。
2. **核准理由未落庫**：我在審查頁輸入的理由文字未被記錄（稽核 #104 `reason_present: false`），核准本身成功且 200。屬審查頁理由欄位的綁定行為，**本輪未修改、僅報告**。
3. **審查詳情電話未遮罩**：`app/security.py` 只有 `mask_email` / `mask_license_number` / `mask_address`，**沒有 `mask_phone`**；故 e-mail／地址遮罩、電話全顯（`+1-555-01019`）。屬**既有 golden 實作行為**，非本輪引入，僅報告。
4. **上傳的 UI「成功」不等於落地**：已回查後端日誌（201）、私有檔目錄、DB 列三處一致（§R2）。
5. **中轉倉歷史中曾發生一次 `--force-with-lease`（C1.8 剝 BOM）**：依 Tao 明令**記錄即可、不改寫歷史、不回退**。另 C1.8 報告首版 commit 訊息曾帶 BOM（外觀問題），亦僅記錄。**本輪 push 不含任何 force-push。**
6. 本輪全程未重啟 `13102`、未 build、未改 env；`c19-httpserv` 為**本機暫存靜態伺服**（`SQLite-like` 測試用途），已於收尾停止。

## 5. 收尾狀態

- `c19-httpserv`：`systemctl --user stop` rc=0 → 單元 `inactive`；因 `KillMode=none` 進程存活，改以**精確 PID `1942687` kill** → 進程消失、`:8099` 監聽 **0**、`curl` 連線被拒（exit 7）。**端口已關。**
- 隧道 `1772631` 存活；`3102` MainPID 仍 `2025892`（未重啟）；`3103` 未動。
- DB：`users 49`、`business_subject_links 6`、**全域 live token 0**。
- 工作樹：FE HEAD 仍 `40c8546e`，僅 `?? tsconfig.tsbuildinfo`；**未新增任何程式碼變更**。

## 6. 秘密掃描

掃描對象：本報告與三張截圖（公開倉內容）。樣式以切分書寫，避免報告自我命中。

- 完整金鑰形態（`sk_`＋`live_` / `pk_`＋`live_` / `sk_`＋`test_` 後接長串）於報告：**0**
- `PASS`＋`WORD` 形態：**0**；私鑰標頭：**0**；`BEGIN … PRIVATE KEY`：**0**
- IPv4 字面（依切分樣式計數）：**0**；本機回環位址以切分書寫
- 開發實例主機名：**0 個完整字串**（一律寫作 `lenient-phoenix-…`）
- 良性十六進位字串（hex32+）：**5**（commit sha、私有檔名、sha256 前綴），**不作為停止條件**
- 備註：token 前 4 碼僅 4 個十六進位字元，不構成憑據；token 全值**未出現於任何檔案、日誌或報告**。
- 掃描結論：**REVIEW 級命中 0；可放行（良性）命中 5。**

## 7. 未解決問題

1. 審查頁「理由」欄位未落庫（§4 觀察 2）——待確認是既有設計或缺陷。
2. 管理員審查詳情電話未遮罩（§4 觀察 3）——既有 golden 行為，是否收緊由 Tao 決定。
3. `agent` 命名空間登出落點為 `/client-login?next=/agent-loop/customer`（既有行為，來源 `app/lib/agent-loop/signout.ts:25`）——本輪未觸及。

## 8. 結論

在**未改動任何程式碼／未 build／未重啟**的前提下，C2 隔離環境以**最終版本**（FE `40c8546e` / BUILD_ID `28IP1GvAGURvF1PHRk8EL`）完成「註冊 → 申請（含合成證件上傳 201）→ 負向檢查 → 核准（200＋稽核 `application.approve`）→ 經紀入口 → 登出與憑證失效（401）→ 上線狀態抽查（付費 closed／0 外部請求）」全流程，逐步與預期一致；收尾全域 live token 為 0，臨時伺服已關閉。**本結果為 C2 隔離環境彩排證據，非生產就緒聲明。**
