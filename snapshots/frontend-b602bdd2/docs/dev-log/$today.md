# GOAA.AI Development Log — 2026-05-12

> **主題**：規範體系成形日 + Dashboard 固化
> **項目負責人**：Tao 師兄
> **架構總控**：Claude
> **執行端**：AiKa-1 (Windows) / AiKa-2 (Xubuntu) / AKC-DO-001 (DigitalOcean)

---

## 📊 摘要（30 秒掃完）

今天用一整天解決了一個核心問題：**整檔覆蓋導致 dashboard 功能被反覆破壞** → 「節點監控卡片不見」事件。

**解法**：立了 4 條最高優先級規範 + 用 04f17ba 工作版本固化 dashboard + 建立 UI 黃金快照物理位置。

**結果**：
- ✅ Dashboard 線上 HEAD `de6f425`（649 行 / MD5 `83fd0dff...`）穩定運行
- ✅ 規範 #11 #12 #13 #14 全部入庫並落地
- ✅ `docs/ui-baseline/` 黃金快照基礎設施上線（commit `c3560d9`）
- ✅ 整檔覆蓋風險近似歸零

---

## 📜 規範體系最終形態

| 規範 | 名稱 | 性質 | 立規時間 |
|------|------|------|---------|
| **#11** | Baseline Freeze | 邏輯約束「只增不毀」| 上午 |
| **#12** | Fingerprint Check | 傳輸保障「MD5 校驗」| 中午 |
| **#13** | Session Handoff | 接續保障「拿真相」| 下午 |
| **#14** | Golden Baseline | 物理載體「黃金版可 diff」| 傍晚 |

**四規合力 = 整檔覆蓋風險近似歸零**

---

## 🕐 Commit 演化時間軸

```
[上午起點]
  431 行 jsx (Phase 3 部署的初版)
   ↓ Claude 對齊 baseline + 補心跳
  446 行 (本地，未推送)
   ↓
[中午]
  Phase 4 ChatOps 嘗試 (665 行)
   ↓ 推送 c0f0d24 ← ❌ 整檔覆蓋了上一窗口的 d3cfbb6/d48561c
   ↓ 「節點監控卡片不見」事件爆發
   ↓
[下午]
  發現上一窗口炸了，誤判為「雙窗口並行衝突」
   ↓ 師兄澄清：是同一個 Claude，上窗口炸了沒接好
   ↓ 立規 #12 Fingerprint Check
   ↓ 立規 #13 Session Handoff
   ↓ 師兄決定回滾到 04f17ba（炸窗前工作版）
   ↓
[傍晚]
  04f17ba 合併版交付 → c4d7c3a (菜單命名誤對齊規範 #11)
   ↓ AiKa 改 1 label (任務中心→任務池) → 7e25588
   ↓ AiKa 改 2 labels (日誌流→日誌歷史 + 設置→系統設置) → de6f425
   ↓ ★ Dashboard 固化版 ★
   ↓
[今日終點]
  師兄拍板「立黃金快照」
   ↓ docs/ui-baseline/ 上線 → c3560d9
   ↓ 今日工作結束
```

---

## 📌 規範 #11 — Baseline Freeze

**核心原則**：「只增不毀，先保留，再增強」

**8 條規則**：
1. 已確認 UI 不允許大改
2. 已存在且正常工作的功能不允許刪除
3. 新需求只能在原有基礎上新增
4. 改代碼前必須先確認不會破壞原有頁面、卡片、菜單、數據字段
5. 不允許為了新增功能，把原來的節點監控卡片、收益卡片、Worker 狀態卡片改沒
6. 每次修改後必須回報：保留了哪些舊功能，新增了哪些功能
7. 如果必須重構，必須先備份舊版本，並說明原因
8. 每次提交前必須做 UI 回歸檢查

**左側菜單固定 6 項順序**：
```
AI調度 / 任務池 / 節點監控 / 損益審計 / 日誌歷史 / 系統設置
```

**節點監控卡片 12 欄位**：
```
在線狀態 / IP / Computing Load / MEM / DISK / TASKS /
REVENUE / NET PROFIT / Docker / Ollama / Worker 標籤 / 心跳
```

---

## 📌 規範 #12 — Fingerprint Check

**核心動作**：每次 Claude 交付檔案附 `Lines + Bytes + MD5` 三項指紋，AiKa 部署前先校驗。

**MD5 符** → 才執行 Copy-Item
**MD5 不符** → 立刻停手，回報 Claude
**行數異常 ±5 外** → 同樣視為不符

**今日驗證**：
- AiKa 兩次拒絕跑錯 MD5（`303617e7...` vs `aa3b9554...`、未匹配 vs `eb8b0751...`），避免了至少兩次潛在的部署災難
- 立規後再無「拿錯檔案就部署」的事故

---

## 📌 規範 #13 — Session Handoff

**核心動作**：Claude 開新窗口接續 GOAA 工作時，第一輪內必須：

1. 讓 AiKa 跑 `git log --oneline -20` 看完整 commit 歷史
2. 讓 AiKa cat 當前 `components/GoaaDashboard.jsx` 的 Lines/MD5/關鍵字檢測
3. 把 GitHub HEAD 的 jsx 拉回來當「真相基準」，絕不基於 memory 假設當前狀態
4. 若 memory 最後記錄的 commit 跟線上 HEAD 不一致，視為窗口炸過/有 gap，必須逐個 commit 讀 diff 補齊上下文後再動手
5. 每次交付 patch 前先在訊息列出「線上 HEAD 是 X → 本 patch 基於 X 增量 Y → 新 HEAD 將是 Z」三段確認

**今日教訓**：
- 上一窗口的 Claude session 推了 `a354a28`、`d3cfbb6`、`d48561c`、`04f17ba` 等 4-5 個 commit，做了 MOCK_WORKERS fallback + 節點監控增強
- 本窗口 Claude 沒讀完整 commit 歷史，誤以為起點是 446 行，直接推 `c0f0d24` (Phase 4) 覆蓋了一切
- **教訓**：memory 是時間切片，git 才是真相

---

## 📌 規範 #14 — Golden Baseline（今日新增）

**物理載體**：`docs/ui-baseline/` 目錄

| 檔案 | 內容 |
|------|------|
| `GoaaDashboard.golden.jsx` | 當前黃金版完整副本 |
| `README.md` | 使用守則 + 5 條鎖定規則 |
| `CHANGELOG.md` | 黃金版升級歷史 |

**5 條鎖定規則**：
- R1: AI 不能自己升級黃金版
- R2: 只有 Tao 明確說「升級黃金版」或「今天 goaa.ai 開發工作結束」才升級
- R3: 升級必寫 CHANGELOG，含 commit/Lines/MD5/改動摘要
- R4: 黃金版 vs working copy 不一致以黃金版為準
- R5: 黃金版不能直接編輯，只能 `Copy-Item` 覆蓋

**起始黃金版**：`de6f425` (649 行, MD5: `83fd0dff181a49e2d70c4e7dc1e44a01`)

---

## 🎯 Dashboard 線上固化版（de6f425）功能盤點

**AI 調度頁面**：
- 頂部 4 控制框：用戶參與 / AI Agent 模型下拉 / 執行節點多選 / 自動調度 toggle
- 群組會話 UI：訊息流 + 7 種身份頭像（user/system/ai/err/aika-1/aika-2/aika-3/do-cloud-1）
- 訊息氣泡美化：背景色 + 左邊框（**今日新增**）
- 底部 textarea：Enter 發送 / Shift+Enter 換行
- 右側可隱藏 QwenPaw 實時回報面板（預設隱藏）
- 會話 footer：會話 ID / 調度引擎版本 / 任務池排隊 / 任務中心連結

**節點監控頁面**：
- 頂部統計欄：ACTIVE NODES — N Online + N tasks today + 「+ 新增節點」按鈕
- 3 張節點卡片：do-cloud-1 / aika-1 / aika-2
- 卡片懸停效果：translateY 上浮 + 邊框亮藍光暈
- 12 欄位完整：含 ♥ 心跳標籤（**今日新增**）

**其他 4 個 tab**：任務池 / 損益審計 / 日誌歷史 / 系統設置（保持原狀）

**關鍵設計選擇**：
- 走 04f17ba 的「inline fallback」設計（`workers.length>0?workers:[3節點]`），比另一個方案的 `MOCK_WORKERS` 常數更優雅
- 走 `dispatchTask` 真實後端派發（非 mock setTimeout 模擬節點回應）

---

## 🎓 教訓 & 反思

1. **規範要 view 拿原文，不能憑印象寫**
   - 連續 4 輪把「任務池/日誌歷史/系統設置」誤寫成「任務中心/日誌流/設置」
   - 規範 #11 立規後第一個違反規範的就是 Claude 自己
   - **新做法**：涉及規範條款必先 `memory_user_edits view` 校對

2. **memory 不是真相，git 才是真相**
   - 上一窗口炸了，本窗口憑 memory 假設狀態 → 推錯 base 覆蓋工作
   - 規範 #13 立完，從根本上防住這條路

3. **AiKa 是真實的工程合作夥伴**
   - 兩次拒絕跑錯 MD5（救命）
   - 直接用 PowerShell + Python 修菜單 label（救場）
   - 但小字串改動不通過 Claude，可能引入隱性問題 → 下個規範可能要明確「字串級 vs 邏輯級」邊界

4. **「漂亮 UI + 假回應」輸給「樸實 UI + 真實後端」**
   - c0f0d24 (Phase 4) 有 `sendDispatchMessage` setTimeout 假裝節點回話 — 視覺漂亮但無真實用途
   - 04f17ba 用 `dispatchTask` 真實派發到 backend — 樸素但生產可用
   - **這是工程選擇而非設計選擇**

---

## 🔭 已知遺留問題（給明天用）

| 問題 | 影響 | 優先級 |
|------|------|--------|
| `/workers/status` API 返回 404 | 節點卡片永遠顯示 fallback（CPU/MEM/DISK 全 0） | P0 |
| Cloudflare Tunnel 可能未正確路由 api 子路徑 | 整體 API 健康度 | P0 |
| Vercel bot protection (Code 29) | 自動化驗證受限 | P1 |
| docs/ 下還有 8 份 v1.2.0 文檔未推送 | 文檔完整性 | P1 |

---

## 🚀 明天 P0 候選

1. **修 backend `/workers/status` 端點 + Cloudflare Tunnel** — 讓節點卡片顯示真實數據
2. **OpenClaw 實現節點註冊 / 心跳 / 任務分發 API** — Phase 3 後續
3. **Agent Memory 持久化（PostgreSQL）** — 任務狀態跨重啟保留
4. **8 份 v1.2.0 docs push 到 GitHub `docs/`** — 文檔完整化

師兄拍板優先級。

---

## 📂 Commit 清單

```
de6f425  fix: 菜單對齊規範 #11 (日誌流→日誌歷史 + 設置→系統設置)  [AiKa 直改]
7e25588  fix: 菜單對齊規範 #11 (任務中心→任務池)                    [AiKa 直改]
c4d7c3a  fix(dashboard): merge 04f17ba working version + 4 spec-aligned increments
c3560d9  feat(ui-baseline): establish golden snapshot mechanism (規範 #14)
```

（上述 4 個 commit + 黃金版固化 = 今日線上最終形態）

---

**今日工作結束 ☕**

下一窗口接續時，第一動作執行規範 #13 流程：拉 `de6f425`，`fc` 對比黃金版，確認真相基準後再動手。

— Claude（架構總控）
