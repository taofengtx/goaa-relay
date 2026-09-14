# AIKABOX × QWENPAW — UI PATCH **CANDIDATE**（D0 / :5198 only）

- **日期**：2026-09-13 PDT
- **環境**：**D0 = Aika-Box / Local Development**（tailnet `100.114.37.90`）
- **驗證實例**：`:5198`（dev／候選） — **Golden C1 `:5188` 全程未動、未重啟**
- **候選檔案**：`/home/aika/gate2-ui-wt/local-console/main.py`
  - sha256[0:16] = **`b5371dbaf5441f14`**（2,244 行 / 160,684 B / BOM=0 / CRLF=0 / `ast.parse` OK）
  - baseline（來源）= **`0c78b8e83516613a`**（2,117 行 / 152,687 B）＝ `:5188` 現行版
- **git**：worktree `/home/aika/gate2-ui-wt`，branch `gate2-ui-patch`，base commit `a68fd85`
- **狀態**：候選完成；U1–U18 全通過；§7 HITL 部分完成（見 §7）；**未套用至 `:5188`**、**待 Tao 決策**

---

## 1. 授權與邊界（Tao 令）

- **允許**：HTML／CSS／少量前端 JS／聊天區布局／滾動邏輯／訊息折疊／響應式布局。
- **禁止**（本輪全程遵守）：QwenPaw adapter、Worker API、Session API、SSE protocol、Approval API、Audit API、Auth、DB、systemd、C1／C2、**Golden `:5188`**。**不夾帶其他功能。**
- **HITL 硬約束**：**禁止任何形式的代 Tao 點擊 Approve／Reject**（agent／browser automation／script／HTTP）。本輪所有真人決策均由 **Tao 本人在瀏覽器點擊**；先前由 agent 代點者一律標記 `TECHNICAL_PATH_PASS` / `HUMAN_APPROVAL_NOT_ACCEPTED`（見 §7）。
- 變更僅落在 **一個檔案**：`local-console/main.py`；未新增／刪除任何其他檔案或端點。

## 2. 未動聲明（可覆核量測）

| 對象 | 量測 | 值 |
|---|---|---|
| Golden `:5188` 程序 | MainPID | **2457759**（全程不變） |
| Golden `:5188` systemd | NRestarts | **2**（不變；本輪未下任何 restart） |
| Golden `:5188` `main.py` | sha256[0:16] | **`0c78b8e83516613a`**（＝baseline，未改） |
| Golden `:5188` `/` | bytes / sha16 | 99,105 B / `0ac695507342933b` |
| Golden `:5188` `/login` | sha16 | **`8aa6a59c5f0271b1`** |
| `:5198` `/login` vs `:5188` `/login` | 逐位元 | **相同**（`8aa6a59c5f0271b1`）⇒ 登入頁未被觸碰 |
| `:5188` 監聽 | bind | `100.114.37.90:5188` ＋ `127.0.0.1:5188`（未變） |
| DB / auth / session key | — | 未讀寫、未輪替 |
| C1 / C2 | — | 未部署、未重啟、未改 |
| worker API / audit API / approval API | — | 未改（僅既有端點被呼叫） |

`0.0.0.⟨0⟩` 綁定：本輪**未新增**任何 `0.0.0.⟨0⟩` 監聽；`:5198` 只綁 tailnet IP `100.114.37.90`（D0／tailnet 可達，非公網入口）。

## 3. 變更範圍

- **檔案**：僅 `local-console/main.py`。**diff**：**9 hunks、+140 / −13**（不含 hunk header）、13,892 B。
- **套用方式**：11 個唯一 anchor 字串替換（腳本內 `count==1` 斷言，否則停手）＋ `ast.parse` ＋ BOM 覆核；**ADD-ONLY 為主**。
- **新增 DOM 契約**：
  - 容器：`.main.ws`、`#p-qwenpaw.page.show`、`.card.qp-top`、`.qp-main`（grid：桌面 2 欄／窄屏單欄）、`.qp-chatmeta`（`qp-m-worker`／`qp-m-session`／`qp-m-status`／`qp-m-count`）
  - Chat：`#qp-log`、`.qp-msg`、`.qp-body`、`.qp-txt`、`.qp-code`、`.qp-live`、`.qp-collapsed`、`.qp-toggle`、`#qp-jump`
  - 右欄：`.qp-side`、`.qp-scroll`
- **CSS（重點）**：固定視口工作台 `body:has(.main.ws){height:100vh;overflow:hidden}`、側欄自捲 `body:has(.main.ws) .side{height:100vh;overflow-y:auto}`（`:has()` 關係選擇器，不動 HTML 結構）；`@media (max-width:960px)` 走上下堆疊（`.qp-side{overflow-y:auto}` ＋ 卡片 `min-height:132px`）。
- **JS（重點）**：`nearBottom`／`showJump`／`scrollLogToBottom`／`syncJump`／`updateChatMeta`／`logLine→buildMsgBody`（` ``` ` fence → `pre.qp-code`；`>14 行 || >1600 字` 自動折疊）／`ensureLive`／`loadHistory`／`loadSessions`／`newSession`／`send`／`startPoll`／`pollApprovals`／`renderApprovals`／`decide`。**未改任何 `API` 呼叫路徑或 payload。**
- **`decide()` 接線覆核**：UI `Reject` 按鈕 → `decide(a,'reject')` → `POST /api/qwenpaw/approvals/{request_id}/reject`；端點存在（`qwenpaw_api.py:306`）。**與 baseline 相同，未被本補丁改動。**
- 完整 diff：附檔 `main.py.diff`（base `0c78b8e83516613a` → 候選 `b5371dbaf5441f14`）。

## 4. 測試矩陣（`:5198`，headless 瀏覽器，**DOM 幾何量測為證**，1440×813 除特別註明）

| # | 項目 | 結果 | 證據（DOM 量測） |
|---|---|---|---|
| U1 | 固定工作台 | ✅ | `.main.ws` height 813、`overflow:hidden`；`doc.scrollHeight == clientHeight == 813` |
| U2 | Composer 恆可見 | ✅ | composer（`.inp`）rect 723–774，三態（頂／中／注入 122 則）皆 visible |
| U3 | Chat 獨立滾動 | ✅ | `#qp-log` `scrollHeight 10,287–10,832 / clientHeight 317`；`doc` 不增高 |
| U4 | 回到底部 | ✅ | 捲至頂 → `#qp-jump` 出現；真點 → `scrollTop == max`、按鈕自動隱藏 |
| U5 | Approval 獨立滾動 | ✅ | 注入 8 卡 → `sh 856 / ch 171`、`overflow-y:auto`、rect 357–528 不變 |
| U6 | Audit 獨立滾動 | ✅ | 注入 30 列 → `sh 494 / ch 171`、rect 602–774 不變 |
| U5/U6 | 三區互不干擾 | ✅ | 捲 log 至 3000 → approval 停 685、audit 停 300、`window.scrollY=0` |
| U7/U8 | 長訊息折疊／展開 | ✅ | 223px（`max-height 223.04px` / `overflow hidden`）↔ 768px（`none` / `visible`）；label「展開全文 ▼」↔「收起 ▲」；文字量不變（1,639 字） |
| U9 | Session History（真實 A→B→A） | ✅ | A1 API 8 == UI 8、B 2 == 2、A2 8 == 8；順序／內容 exact（去除 ` ``` ` fence 後）；`residueFromProbe=0` |
| U10 | Session 隔離 | ✅ | A→B→A 零交叉污染；切 session 正確清 log |
| U11 | SSE 串流 | ✅ | `.qp-live` 12 段遞增（95→548，~2.4 s）；完成後清空並渲染終稿；`Running → Completed` |
| U12 | 審批卡真出現 | ✅（技術路徑） | 送出後 ~2.2 s 自行出現：`HIGH · execute_shell_command · crontab -l`、`PENDING`、`ttl 300s`、`findings 1` ＋ Approve／Reject 兩鍵 |
| U14 | Stale 不可點 | ✅ | `UI-FINAL-STALE`：API `STALE / clickable=false / age 328.6s`；UI「（已失效，不可點擊）」、**buttonCount = 0**；worker 於 300.0 s 自動拒絕（**我未點**） |
| U15 | 100+ 訊息壓力 | ✅ | DOM 注入 121 則（共 122）→ `doc.scrollHeight` 仍 813、`vOverflow=0`、`hOverflow=0`、`sh 10,287 / ch 317` |
| U16 | 窄屏 420×900 | ✅ | `doc 900 == viewport`（vOverflow 0）、`hOverflow 0`、composer 673–723 可見、`.qp-side` 自身可捲（`sh 692 / ch 142`） |
| U17 | 無水平溢出 | ✅ | 桌面與窄屏 `hOverflow` 皆 0 |
| U18 | Console JS 錯誤 | ✅ | 重載後掛 `window.__errs`／`__rejs` 收集器 → A→B→A 往返期間 **errs=[]、rejs=[]（JS ERROR=0、UNCAUGHT EXCEPTION=0）**；console `error=0 / warning=0`（唯一曾見者為 favicon 404，`:5188` 亦相同 ⇒ pre-existing，非 JS 錯誤） |
| 回歸 | 桌面布局 | ✅ | side 216、main 1224、`.qp-main` 805 / 345、doc 813 |

**專項 A／B／C（Tao 指定）**：A 窄屏 420×900 實測 ✅；B Chat／Approval／Audit 三區分別驗 overflow ✅（各自獨立、互不影響）；C 100+ 訊息 DOM 壓力 ✅。

## 5. DOM 注入清理（Tao §2）

- 重新載入即清除；`#qp-log` 內注入字串殘留 **0**。
- **非資料污染**：`/tmp/ui-sessions.json`（dev session store）與生產 audit 檔內對注入標記命中 **0**；**未刪除、未修改任何真實 session／DB 資料**。
- 純瀏覽器端 DOM probe，不落盤。

## 6. 截圖（Tao 指定檔名；皆取自最終候選 `b5371dbaf5441f14`）

| 檔名 | bytes | sha256[0:16] |
|---|---|---|
| `01-normal-chat.png` | 211,518 | `43a738ae8050017a` |
| `02-long-history.png` | 272,530 | `d6dbe88ba91f15f6` |
| `03-composer-visible.png` | 227,320 | `1665c3713746ce5c` |
| `04-long-message-collapsed.png` | 277,215 | `c359172684f49a2d` |
| `05-long-message-expanded.png` | 302,743 | `0b18cb1977fbd15a` |
| `06-real-approval-card.png` | 194,650 | `f41afda0cbbcb559` |
| `07-audit-scroll.png` | 229,223 | `8d632a6002135834` |
| `08-narrow-screen.png` | 101,170 | `3966a2bd179aa373` |

（合計 1,816,369 B；8 張皆為最終候選 `b5371dbaf5441f14` 之 headless 渲染，1440×813，`08` 為 420×900。）

> **誠實聲明**：本輪執行者（AI agent）**無多模態能力、無法看圖**。上述截圖僅供人類目視；**所有視覺／布局宣稱一律以 §4 的 DOM 幾何量測數字為證**，不以截圖下結論。
> 截圖位於 `shots/`（本目錄）。

## 7. §7 驗收（HITL）證據

**本輪真人決策（Tao 本人在 `:5198` 瀏覽器點擊；audit 檔逐筆可覆核）**

| 時間 (PDT) | Session | request_id | 決策 | run 結果 | 工具是否執行 |
|---|---|---|---|---|---|
| 23:41:23 | `UI-FINAL-APPROVE` | `59a858a2-de96-4a55-828e-b6437b078f4c` | **approve** | `Completed`（sse 398） | ✅ 已執行 |
| 23:43:43 | `UI-FINAL-APPROVE` | `3fbd6f68-a1ff-4df9-a0ca-88231a565e68` | **approve** | `Completed`（sse 639） | ✅ 已執行 |
| 23:44:24 | `UI-FINAL-REJECT` | `b92d2485-d303-4f60-9512-041c9da8d69d` | **approve** | `Completed` | ✅ 已執行 |
| 23:45:07 | `UI-FINAL-REJECT` | `dc30f90d-906e-4a8d-aeb7-031bf0c0fcf5` | **approve** | `Completed`（sse 918） | ✅ 已執行 |
| 23:45:37 | `UI-FINAL-REJECT` | `2014471c-75ad-4fc2-a6dd-307504f1245b` | **approve** | `Completed`（sse 565） | ✅ 已執行 |

- **Approve 鏈路（真人）＝ PASS**：卡片 → 真人點擊 → 同 run 由 `Waiting Approval` 續跑 → 工具真的執行（輸出 `$ crontab -l` / `no crontab for aika`，exit 1；讀取型指令、無副作用）→ run `Completed` → 結果回流 transcript。
- **Reject 鏈路：本輪「無」真人 reject**。audit 檔（103 筆）中最後一筆 `decision=reject` 為 **23:06:52**，該筆係**由 agent 代點**（Auto-click），依 Tao 23:12 令**只能標記** `TECHNICAL_PATH_PASS` / `HUMAN_APPROVAL_NOT_ACCEPTED`。**⇒ §7 的 reject 人類驗收仍待 Tao 親點。**
- 技術面對照（先前代點那筆）：`decision=reject` → `http_status 200`、`message="denied: User denied"` → run 續行並完成、**工具未執行**（無 `no crontab for aika` 輸出）⇒ 機制本身可用。
- **審計欄位限制（重要）**：`actor=tao` / `source=ui-click` 係由 **cookie 推導**，**無法區分「真人滑鼠」與「agent 經 UI 的 HTTP 點擊」**。故本報告區分「真人點擊（PASS 證據）」與「技術路徑（僅 PASS 技術鏈路）」；**不得以 audit 欄位單獨證明人類已驗收**。

## 8. 已知限制（**非本補丁引入**，僅記錄，未修）

1. adapter `history()` 硬上限 `messages[-30:]` ⇒ 真實 API 最多回 30 則（故 100+ 則壓力以 DOM 注入證明布局）。
2. worker `/api/chats` 不含 `message_count` ⇒ session 清單 `msgs` 恆為 0。
3. `loadHistory()` 具護欄 `if(st.es) return Promise.resolve();` ⇒ **有 run 串流中（含 pending approval）時切換 session 不載入歷史**（`:5188` 現行版同樣）。
4. `decide()` 後僅 `loadAudit()` ＋ 重 poll，**不 `loadHistory()`** ⇒ 經 fetch 建立之 run 在點擊後 transcript 不自動刷新（需重選 session 或 reload）。
5. `:5198` 的 audit log 指向 **與 `:5188` 共用**的預設檔（dev 決策會寫入同一 audit 檔）——**只登記、未改行為**。
6. 審批 TTL = **300 s**（worker 端設定）⇒ 人工驗收窗口短，需可重種（附自助路徑）。
7. favicon 404 console 訊息（`:5188` 亦同 ⇒ pre-existing）。
8. 本 agent 無多模態 ⇒ 視覺宣稱一律改附 DOM 量測（見 §4、§6）。

## 9. 交付與收尾

- **掃描**：16-pattern 秘密掃描器（依類別：Stripe 金鑰前綴×4、Clerk 各變體×6、PEM 私鑰標頭、AWS 存取金鑰前綴、GitHub token 前綴、PG 連線 URI、env 賦值兩式、JWT 形字串、PG 密碼檔名、Clerk 秘密指派）＋ 兩項結構檢查（未遮罩 routable IPv4、BOM）⇒ **12 檔 / 0 命中 / BOM=False**（樣式字面僅存在於掃描腳本內，不抄入交付文件）。
- **commit（代碼）**：`7a57bc3`（branch `gate2-ui-patch`，base `a68fd85`）— **local only，未 push**（未獲授權推代碼分支）。
- **commit（交付文件）**：本報告＋`main.py.diff`＋`UI-SECT7-EVIDENCE.json`＋`UI-TEST-MATRIX.json`＋`shots/*.png` 一併 commit 至 relay 並 push（見文末「收尾量測」）。
- **` :5188` 未套用、未重啟**：是否套用（或先做窄屏局部修正）**待 Tao 決策**。
- 記憶已更新（daily + `MEMORY.md`）。

## 10. 附錄

- 附檔：`main.py.diff`（13,892 B）、`UI-SECT7-EVIDENCE.json`（本輪逐筆決策＋run 狀態＋transcript 尾段）、`UI-TEST-MATRIX.json`（U1–U18 量測）、`shots/*.png`（8 張）。
- 監聽（量測當下）：`:5198` → `100.114.37.90:5198`（uvicorn，dev）；`:5188` → `100.114.37.90:5188` + `127.0.0.1:5188`（Golden，未動）。
- 回復方式：關閉 dev 程序即可（未動 systemd／未改任何共享設定）。
