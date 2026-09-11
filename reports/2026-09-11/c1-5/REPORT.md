# Round C1.5 (續) — Z3a/Z3b env 殘留修正 · 13102 重啟 · U3 跨帳號切換驗證

日期：2026-09-11
範圍：C2 測試主機（SSH alias `do-c2`）與本中轉倉。
**未觸碰**：C1（`planning` / `api.goaa.ai`）、`goaa_c2`、Golden Flow、支付、Framer、3100/3101、nginx。

隔離拓撲（測試環境，非生產）：

```
Browser (http://127.0.0.1:13102  →  ssh tunnel  →  C2)
  → Next 3102 BFF (goaa-c2-clerk-ui-3102.service, HOSTNAME=localhost, PORT=13102)
  → FastAPI 3103 (goaa-c2-clerk-api-3103.service)
  → PostgreSQL 5433 / goaa_c2test
```

身份提供方：Clerk **Development** 實例（`test_mode=true`），合成測試帳號（`+clerk_test` 郵箱、驗證碼 `424242`）。
本報告不含任何秘密值；所有 token 僅以「非空 / 長度」形式描述。

---

## 1. Z3a / Z3b — `CLERK_AUTHORIZED_PARTIES` 殘留埠修正

背景（C1.5 Z 段已定案根因）：白名單第二條為舊埠 `http://127.0.0.1:3102`，導致以 `127.0.0.1:13102` 存取時 `azp` 不在白名單 → Clerk token 被拒 → `invalid_clerk_session` → 401。

本輪續修兩支先前「只回報、未修改」的 env 檔。手法：**只改一行**，python `r+b` 就地寫入（不用 `sed -i`、不重寫全檔）；備份為同目錄 `.bak-<時間戳>`，**權限與 owner:group 與原檔相同**。

| 檔案 | 備份 | 改動 | 其餘行 sha256 前後 | 行數 | mode/owner | size |
|---|---|---|---|---|---|---|
| `/opt/goaa-test/env/clerk-api-3103.env` | `…bak-20260911-100202` | `CLERK_AUTHORIZED_PARTIES` → `http://localhost:13102,http://127.0.0.1:13102` | 一致（`3f77418b…9903`） | 28/28 | `root:goaa-c2loop 440` | 1171→1172 |
| `/opt/goaa-test/env/clerk-ui-3102.env` | `…bak-20260911-103145` | 同上 | 一致（`79f12dd6…ba6b6`） | 11/11 | `root:goaa-c2loop 440` | 510→511 |
| `/opt/goaa-test/env/clerk.env` | `…bak-20260911-103150` | 同上 | 一致（`61e756e8…65b1`） | 6/6 | `root:goaa-c2loop 440` | 381→382 |

備註：全域 grep 確認 `/etc/systemd/system` **無任何 unit 引用 `clerk.env`**；三個單元分別使用 `goaa-c2-backend.env` / `clerk-api-3103.env` / `clerk-ui-3102.env`。`clerk.env` 之修改為一致性清理，**目前不被任何服務讀取**。

---

## 2. R1 — 重啟 13102

- 指令（最小形式、未串接其他命令）：
  `systemctl restart goaa-c2-clerk-ui-3102.service`
- 結果：`rc=0`，未出現拒絕。
- MainPID：`2012347` → **`2015462`**；`ActiveEnterTimestamp = Fri 2026-09-11 10:32:00 UTC`。
- `KillMode=control-group`、`TimeoutStopUSec=20s`；舊進程已確實結束（`/proc/2012347` 不存在），監聽 socket 由新進程持有。

---

## 3. R2 — 重啟後驗證

| 檢查 | 結果 |
|---|---|
| `systemctl is-active` | `active` |
| BFF `/api/agent-loop/health` | **200**，`database.name = goaa_c2test` |
| `/client-login?next=/agent-loop/customer` | **200**，10,402 bytes |
| HTML 內 client chunk 引用 | 8 個，**non-200 = 0** |
| 進程 `/proc/2015462/cwd` | `/opt/goaa-test/ui-clerk-20260910` |
| 磁碟 `BUILD_ID` | `v-T0MoUeDwjoROup6Hura` |

**關鍵修復確認（重啟前 vs 後）**：

| | HTML 引用的 layout chunk | 磁碟是否存在 | chunk 回應 |
|---|---|---|---|
| 重啟前（舊進程 serve 舊 build） | `layout-e51b892a3d7dade7.js` | 不存在（磁碟為新 build） | **404** |
| 重啟後 | `layout-edecef38c3555101.js` | 存在 | **200** |

即：部署新檔但未重啟期間，舊伺服器仍引用已不在磁碟的舊 chunk（`layout-e51b892a3d7dade7.js`）→ 404 → 頁面無法 hydrate。**重啟後該狀態消除。**

---

## 4. U3 — 跨帳號切換驗證

條件：**全程同一瀏覽器分頁、不重新整理**；起點 `http://127.0.0.1:13102/client-login?next=%2Fagent-loop%2Fcustomer`（Z3a 修正後新列入白名單的來源）。

| # | 動作 | 頁面狀態 | `client_token` | Clerk signed-in | DB（total / live） |
|---|---|---|---|---|---|
| 1 | 起始 | 登入卡（未登入） | null | false | — |
| 2 | 登入 **A**（`c2e2e+clerk_test@example.com`） | 落 `/agent-loop/customer` | null → **非空**（約 2.8s 後） | true (A) | A 6 / **1** |
| 3 | A → MY ACCOUNT → LOG OUT | 落 `/client-login?next=/agent-loop/customer` | null | false | A 6 / **0** |
| 4 | **不重整**，在落地卡直接登入 **B**（`c2e2e2b+clerk_test@example.com`） | 落 `/agent-loop/customer` | **非空** | true (B) | B 2 / **1** |
| 5 | B → MY ACCOUNT → LOG OUT | 落登入卡 | null | false | B 2 / **0** |
| 6 | 再登入 A | 落 `/agent-loop/customer` | **非空** | true (A) | A 7 / **1** |
| 7 | A → LOG OUT（收尾） | 落登入卡 | null | false | A 7 / **0** |

業務主體（`business_subject_links.subject_id`）：A = `4717531f-6806-49ef-8326-6185f3ea1d3d`、B = `f99342a6-7a3a-463f-8738-a94501297727`。

### 後端日誌（`/var/log/goaa-c2-clerk-20260910/api-3103.log`，依序）

```
POST /api/v1/agent-loop/golden/session        HTTP/1.1" 200 OK     # A 登入
POST /api/v1/agent-loop/golden/session/revoke HTTP/1.1" 200 OK     # A 登出
POST /api/v1/agent-loop/golden/session        HTTP/1.1" 200 OK     # B 登入（同一分頁）
POST /api/v1/agent-loop/golden/session/revoke HTTP/1.1" 200 OK     # B 登出
POST /api/v1/agent-loop/golden/session        HTTP/1.1" 200 OK     # A 再登入
POST /api/v1/agent-loop/golden/session/revoke HTTP/1.1" 200 OK     # A 收尾登出
```

### 結論（對照 C1.5 U0 缺陷）

U0 觀察到的缺陷：**同一分頁切換使用者時，第二個使用者 `client_token` 為 null、DB 無 live token、後端無 `POST golden/session`**（登入標記未清除，bridge 不再發起）。

本次修正後（步驟 4）：**同一分頁、未重新整理之下，B 登入即取得 `client_token`，後端出現 `POST golden/session 200`，B 的業務主體出現 1 個 live token**，且反向（步驟 6，B → A）同樣成立。

---

## 5. 證據檔案

| 檔案 | 說明 | sha256 |
|---|---|---|
| `u3-switch.jpg` | B 登入後落地頁截圖（1440×813） | `8f3ec527c162174e18d1880c00e3f9946af3d572807b43fa30f3f468622f603c` |

**誠實註記**：此 JPEG 與 C1.4 R3 的落地截圖（`r3-newuser-landing.jpg`）**位元組完全相同**——黃金落地頁無 per-user 視覺元素，兩張圖在像素上不可區分。因此截圖**不構成**使用者切換的區分證據；區分證據為上表的 `client_token` 狀態、後端日誌與 DB live 計數。

---

## 6. 未解 / 待確認

1. `client_token` 並非在落地瞬間出現，本次觀測延遲約 **2.8 秒**（落在「3 秒內」的邊界）。此為既有非同步簽發機制行為，非本輪缺陷；未做進一步最佳化。
2. 落地頁無 per-user 視覺元素（見第 5 節）——非缺陷，僅為取證限制。
3. C2 上保留備份鏈：`.bak-20260911-{000731,005345,053254,060539,024044,031118,100202,103145,103150}`（未清理）。
4. `clerk.env` 不被任何 unit 讀取（僅一致性清理）。
5. 本輪**未驗證** C1 線上（`/opt/goaa/runtime`）與本中轉倉節錄的後端源碼是否一致（未連 C1）。

---

## 7. 未變更項確認

- Golden 登錄頁 `app/client-login/page.tsx`：位元組不變。
- `middleware.ts`、`clerk-entry.ts`、`golden-session*`、`api/agent-loop/**`、黃金支付、Golden Flow、Framer：未變更。
- C1 生產服務：未重啟、未修改。
- 測試帳號、DB 內容僅為 C2 `goaa_c2test` 之合成資料。
