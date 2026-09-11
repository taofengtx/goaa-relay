# Round C1.6 — patch 0009: the $39.90 connection is closed at go-live

日期：2026-09-11
範圍：C2 測試主機（SSH alias `do-c2`）與本中轉倉。
**未觸碰**：C1、`api.goaa.ai`、`goaa_c2`、Golden Flow、支付供應商、Framer、3100/3101、nginx。

隔離拓撲（測試環境，非生產）：

```
Browser (http://localhost:13102  →  ssh tunnel  →  C2)
  → Next 3102 BFF (goaa-c2-clerk-ui-3102.service, HOSTNAME=localhost, PORT=13102)
  → FastAPI 3103 (goaa-c2-clerk-api-3103.service)
  → PostgreSQL 5433 / goaa_c2test
```

本報告不含任何秘密值；env 檔僅以 sha256／大小／mode／owner 描述。

---

## P1 — 轉交 Claude Code 套用 patch 0009 ✅

| 項目 | 預期 | 實際 |
|---|---|---|
| relay 取得 patch | Tao 上傳於 repo 根 | `9159cf1`（`0009-round-c1-6-paid-connection-gate.patch`，**本次無 `_1` 後綴**） |
| patch sha256 | `e596aef418dbd6f54245ea3628470be13291622ab168b2fdae69626c0f1bd581` | **相符**（移動前後皆同值） |
| 歸位 | `patches/0009-round-c1-6-paid-connection-gate.patch` | `git mv` → commit `8b2b56617fbf7ed1fddfc03de7cebed04d4c403b`（0 行內容變更）→ push |
| 前端工作樹 HEAD | C1.5 套完 0008 後 | `f93c5544abf742236aa61fda6bb6b63bbc60bd96` ✅ |
| `git am` | 乾淨套用 | 套用後 FE HEAD = **`049a0a6ead4353b878557767ed61ffb3ebda24b2`** |
| 變更檔案 | 僅 0009 的 8 檔 | 8 檔、**+180 / −5**，與 patch 清單一致 |
| `npx tsc --noEmit` | 0 錯誤 | **0 錯誤** |
| `scripts/test-*.cjs` | 30 檔全綠 | **30 檔 / 30 通過 / 0 失敗** |
| `scripts/c2-clerk/run-all.sh` | 99/99 | **`TOTAL: 99 passed, 0 failed, group_rc=0`** |
| 快照 | `frontend-<sha8>` | `snapshots/frontend-049a0a6e`（**637 檔**） |
| push | — | relay **`5b5707ae54c9a91324ed67074c59c81d5b22035c`**（`8b2b566..5b5707a`） |

變更的 8 檔（獨立核驗）：

```
app/components/MatterProfessionalConnect.tsx   | 11 +++-
app/components/ProfessionalConnectBar.tsx      |  2 +-
app/components/ProfessionalHandoffCard.tsx     | 16 ++++-
app/connect-pass/layout.tsx                    | 30 ++++++++++   (new)
app/layout.tsx                                 |  3 +-
app/lib/paid-connection.ts                     | 24 ++++++++     (new)
app/styles/goaa-tokens.css                     | 10 ++++
scripts/test-paid-connection-gate.cjs          | 89 ++++++++++     (new)
```

保護檔核驗：`app/client-login/page.tsx` **與 `f93c5544` 相比 0 diff**，sha256 `08b31389d40e6350a1e293d64c94e99e79c86c22581e20e6560eaca9750743a1`、**27006 bytes**（黃金登錄頁位元組不變）。`middleware.ts`、`clerk-entry.ts`、`golden-session*`、`api/agent-loop/**` 亦未變更。

---

## P2 — build → standalone（含 public/）→ 更新 13102 → 重啟 ✅

**建置**（`npx next build --no-lint`，`NODE_OPTIONS=--max-old-space-size=1024`）

| 檢查 | 預期 | 實際 |
|---|---|---|
| 建置 shell 內的 Clerk／付費變數數 | 0（不放 Clerk 變數） | **0**（`CLERK*` / `NEXT_PUBLIC_CLERK*` / `NEXT_PUBLIC_GOAA*` / `GOAA_PAID_CONNECTION` 皆無） |
| build rc | 0 | **rc=0**，`✓ Compiled successfully` |
| 預渲染檢查 | 動態 | `/`、`/planning`、`/client-login`、`/connect-pass` **皆非預渲染**（`dynamicRoutes: []`） |
| 付費閘標記在產物內 | 存在 | `data-goaa-paid` ×1、`connect-pass-closed` ×1、說明文案 ×1、`GOAA_PAID_CONNECTION` ×1 |

**打包**：staged 1969 檔；`public/`（含 `public/fonts/outfit/`）帶入；tar sha256 `864e87218da06ed39e725cdc7607341c91177febbe8157d45c032e0a127c5d0a`、**8,857,259 bytes**；產物秘密掃描：`sk_test_` 0、`sk_live_` 0、真實 Clerk 實例主機 0。

**部署**：tar sha256 遠端比對**相符**；unpacked 1969；備份 `/opt/goaa-test/ui-clerk-20260910.bak-20260911-035142`（34M）；`rsync -a --delete --exclude .next/cache` rc=0；owner `goaa-c2loop:goaa-c2loop`；**manifest `sha256sum -c` 非 OK 行 = 0**；`BUILD_ID = CTTDt_kz84kdxBeXqHcaH`；磁碟 layout chunk = `layout-f567b39096b24041.js`。
**13102 的 env 未加 `GOAA_PAID_CONNECTION`**（部署後：10 行、`GOAA_PAID_CONNECTION` 0 行、`root:goaa-c2loop 440`）—— 這正是上線狀態。

**重啟 #1**：`systemctl restart goaa-c2-clerk-ui-3102.service`（最小形式、未串接）→ **rc=0**；MainPID `2015462` → **`2016991`**；`ActiveEnterTimestamp = Fri 2026-09-11 10:52:26 UTC`。
**Aika 端是否看到 🛡 卡：未見**；是否經 Tao approve 以 Tao 為準。

---

## P3 — 驗證「關閉」狀態（瀏覽器用 `http://localhost:13102`）✅

**P3a — `/planning` HTML**

| 預期 | 實際 |
|---|---|
| `<html>` 上有 `data-goaa-paid="closed"` | `<html lang="en" data-goaa-paid="closed">` ✅（HTTP 200、16,199 B；10 個 client chunk 引用、**non-200 = 0**） |

**P3b — 首頁 `/`**

- `document.documentElement.dataset.goaaPaid` = **`"closed"`** ✅
- `.goaa-professional-connect`：**在 hydration 後的 DOM 中不存在**（條件不成立）。補充事實：
  - 伺服器端 HTML **確實含**該元素：`class="goaa-professional-connect goaa-paid-open-only"`（頂欄 `Connect Now · $39.90`）；
  - 該元素在客戶端被移除的原因是**既有的 P4.4B 行為**：`ChatComponent` 在 consultation 作用中會發 `goaa:consultation-active`，頂欄即 `return null`（與本輪 patch 無關）。
  - 該類別在**當前 `data-goaa-paid="closed"` 之下的計算樣式實測**（以同 class 元素注入後讀 `getComputedStyle`，驗畢即移除）：`display: none` ✅；`.goaa-paid-closed` → `display: block` ✅。
- 截圖：`p3-home.jpg`（100,339 B，sha256 `e6bc41d005e7bed2c4dc24c20f173ced714589763ca5c9208d137f6f6a801de0`）

**P3c — `/connect-pass?source=planning`**（未登入直接開）

| 預期 | 實際 |
|---|---|
| 標題 = "Professional connection is opening soon" | `<h1>` = **"Professional connection is opening soon"** ✅（`data-testid="connect-pass-closed"` 存在） |
| 有 Book a 30-minute assessment 連結 | **"Book a 30-minute assessment ↗" → `https://cal.com/goaa.ai/30min`** ✅ |
| 有 Back to AI Butler 連結 | **"Back to AI Butler" → `/planning`** ✅ |
| performance 資源無 api.goaa.ai | **0 筆** ✅（僅 `localhost:13102` 與 Clerk dev 主機） |
| console 無 api.goaa.ai | **無** ✅（console 僅 1 條 Clerk「development keys」警告） |
| 截圖 | `p3-connect-pass.jpg`（35,498 B，sha256 `1eed508154d4079150c93f22870d62adca1a62f5f53e1d0fabad42f7dbcc70c3`） |

**P3d — `/planning` 右欄卡片仍在**

| 預期 | 實際 |
|---|---|
| 「预约 30 分钟评估」卡片仍在 | 存在且可見 ✅（文字：`🗓预约 30 分钟评估与 GOAA 团队进一步梳理目标和下一步。预约时间 ↗预约不会自动购买 GO…`） |
| 連結 = `https://cal.com/goaa.ai/30min` | ✅ `href="https://cal.com/goaa.ai/30min"`、`target="_blank"`、`display:flex`、`offsetWidth>0` |

---

## P4 — 驗證開關能重新打開，驗完再關回去 ✅

**P4a — 加行並重啟**

| 項目 | 加行前 | 加行後 |
|---|---|---|
| `/opt/goaa-test/env/clerk-ui-3102.env` 大小 | 511 B | **537 B** |
| 行數 | 10 | **11** |
| `GOAA_PAID_CONNECTION` 命中 | 0 | **1** |
| mode / owner / inode | `440` / `root:goaa-c2loop` / `303037` | **完全相同** |
| sha256 | `cd3581e60e7254c12270eec5d2cab55f42ab70bbe183183df7df8b4edf712f67` | `d6649f0bfcafa961ff82ad01e04234ab861da99001f5610f7ed5462912791f1c` |

備份：`/opt/goaa-test/env/clerk-ui-3102.env.bak-c16-open`（511 B、`440`、`root:goaa-c2loop`、sha256 同加行前 `cd3581e6…`）。

**重啟 #2**：rc=0；MainPID `2016991` → **`2017333`**；`ActiveEnterTimestamp = Fri 2026-09-11 10:54:56 UTC`。
**Aika 端是否看到 🛡 卡：未見**；是否經 Tao approve 以 Tao 為準。

**P4b — 開啟狀態驗證**

| 檢查 | 預期 | 實際 |
|---|---|---|
| `/planning` HTML | `data-goaa-paid="open"` | `<html lang="en" data-goaa-paid="open">` ✅（16,195 B） |
| `/connect-pass?source=planning` | 原本的結帳頁 | HTTP 200（9,768 B）；**「opening soon」文案 0 次**、`connect-pass-closed` 0 次；頁面含 `39.90` / `payment` 標記 ✅ |
| 瀏覽器開同一頁 | 結帳頁、非說明頁 | `data-goaa-paid="open"`；說明頁元素不存在；內文含 `payment`、`39.90` ✅ |
| 對外請求 | 無 api.goaa.ai | **0 筆 api.goaa.ai**（network log：12 筆 `localhost:13102` + 8 筆 Clerk dev 主機）✅ |

**未按任何購買／付款按鈕**。且此頁 mount 時若無客戶憑證即 `redirect` 到 `/client-login`（程式碼事實），故本次為未登入檢視，**全程未向 `api.goaa.ai` 發出任何請求**（含讀取）。

**P4c — 還原並重啟**

| 項目 | 還原後 |
|---|---|
| 大小 / 行數 / `GOAA_PAID_CONNECTION` | 511 B / 10 行 / **0** |
| sha256 | **`cd3581e60e7254c12270eec5d2cab55f42ab70bbe183183df7df8b4edf712f67` = 加行前原值（byte-identical）** ✅ |
| mode / owner | `440` / `root:goaa-c2loop`（不變） ✅ |
| `/planning` HTML | `<html lang="en" data-goaa-paid="closed">` ✅（10/10 chunk 200） |
| `/connect-pass?source=planning` | HTTP 200（9,057 B）；說明文案 1 次、`connect-pass-closed` 1 次 → **回到說明頁** ✅ |

**重啟 #3**：rc=0；MainPID `2017333` → **`2017556`**；`ActiveEnterTimestamp = Fri 2026-09-11 10:56:41 UTC`。
**Aika 端是否看到 🛡 卡：未見**；是否經 Tao approve 以 Tao 為準。

---

## 五、未解 / 待確認 / 遺留

1. P3b 的 `.goaa-professional-connect` 在**已 hydrate 的 DOM** 中不存在（SSR 有、客戶端被既有 consultation 訊號移除），因此該條目以「條件不成立 + CSS 計算樣式實測」呈現，而非「抓到真實元素量到 none」。
2. P4b 的結帳頁僅以**未登入**狀態檢視；登入後的真實結帳畫面（會走 order-API 讀取）未演練，以免對 `api.goaa.ai` 發送任何請求。
3. C2 遺留備份：`/opt/goaa-test/ui-clerk-20260910.bak-20260911-035142`（34M）、`/opt/goaa-test/env/clerk-ui-3102.env.bak-c16-open`（未清理，依凍結條款保留）。
4. Claude Code 端偏差：`sha256sum`／`cp` 對工作目錄外路徑受其 sandbox 限制，改用 `python3 hashlib` 計算校驗值（值相符）；無其他偏差。

---

## 六、未變更項確認

- C1 / `api.goaa.ai`：本輪**零請求**（network log 0 筆）。
- `app/client-login/page.tsx`：位元組不變（27006 B、sha256 `08b31389…`）。
- `middleware.ts`、`clerk-entry.ts`、`golden-session*`、`api/agent-loop/**`、黃金支付、Golden Flow、Framer：未變更。
- 13102 env 除測試期間臨時加行（已 byte-identical 還原）外未變更。
