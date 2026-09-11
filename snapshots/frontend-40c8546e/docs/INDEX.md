# GOAA.AI 開發文檔總索引 (Master INDEX)

**版本**: V1.0
**最後更新**: 2026-05-16
**狀態**: 戰略憲法 V1.0 完整整合版

## 📌 文件角色標籤 (規範 SUPREME 治理)

```text
本文角色: Master 文檔總索引
本文類型: Navigation Index
是否允許直接執行: 否
是否允許修改 Production: 否
是否需要 Tao 拍板: 否 (索引可自動更新)
最高參考來源: 本檔即索引
```

---

## 🏛️ Canonical Files (正式版本聲明)

**以下檔案為 GOAA.AI 戰略基線正式版本, 不可走偏**:

| 檔案 | 角色 | 路徑 |
|---|---|---|
| `MEMORY.md` | 當前狀態源 | `docs/MEMORY.md` |
| `AGENTS.md` | 命名規範源 | `docs/AGENTS.md` |
| `GOAA_BUSINESS_MODEL_V1.md` | 戰略憲法主檔 (最高戰略源) | `docs/business/` |
| `RUNTIME_OS_STRATEGIC_BLUEPRINT_V1.md` | Runtime OS 架構基線 | `docs/architecture/` |
| `FUTURE_DDL_SKILL_MARKETPLACE.md` | V4.2+ DDL 儲備 | `docs/architecture/` |
| `V4_1_Worker_PLAN.md` | Worker V5.0 第一階段執行計劃 | `docs/roadmap/` |
| `V4_2_PLUS_SKILL_MARKETPLACE.md` | Phase 5 Roadmap | `docs/roadmap/` |
| `INDEX.md` | Master 索引 | `docs/` |

### 🚫 不得作為架構基線

帶以下後綴的檔案**不得作為架構基線**, 應歸檔到 `docs/archive/`:
- `*(1).md`, `*(2).md` (重複下載)
- `*copy*.md`, `*duplicate*.md`
- `*backup_*.md`, `*.backup.md`
- `*_v1.md`, `*_v2.md` (舊版迭代, 除非明確標示為 canonical)
- `draft_*.md` (草案版本)

### 衝突解決規則
1. **GOAA_BUSINESS_MODEL_V1.md** = 最高戰略源 (商業 / 角色 / 5 原則)
2. **MEMORY.md** = 當前狀態源 (版本 / 系統架構)
3. **AGENTS.md** = 命名規範源 (DB / API / UI 命名)
4. 三者衝突時, 以本順序為準
5. 任何修改必須 Tao 拍板 (規範 #14 R2)

---

## 🎯 快速導航

### 如果你是新加入的 AI / Worker
1. 先讀 **`MEMORY.md`** (1 頁版戰略憲法摘要 + 系統狀態)
2. 再讀 **`AGENTS.md`** (命名規範強制 + 你的角色)
3. 動工前讀 **規範體系** (見下方 #4)
4. 開發新功能讀 **`docs/business/GOAA_BUSINESS_MODEL_V1.md`** (戰略憲法主檔)

### 如果你要設計新功能
1. **戰略對齊**: `docs/business/GOAA_BUSINESS_MODEL_V1.md` 第 12 章 (5 原則)
2. **架構對齊**: `docs/architecture/RUNTIME_OS_STRATEGIC_BLUEPRINT_V1.md` (雲腦+本地手腳)
3. **路線圖對齊**: `docs/roadmap/V4_1_Worker_PLAN.md` (V4.x 階段)
4. **資料庫對齊**: `docs/architecture/FUTURE_DDL_SKILL_MARKETPLACE.md`

### 如果你要動 Production
1. 規範 #13 接續校驗 (git log + MD5 確認)
2. 規範 #14 R2 (Tao 拍板)
3. 規範 #15 (24h Cooldown)
4. 規範 #19 v2 (收工郵件真實寄出)
5. 規範 #24 (不憑想像)
6. 規範 #31 (AiKa STDOUT 透傳)

---

## 📚 文檔層級結構

```
docs/
├─ MEMORY.md                                    ← 系統長期記憶 + 戰略憲法摘要
├─ AGENTS.md                                    ← 命名規範 + AI 工作者分工
├─ INDEX.md                                     ← 本檔, 總索引
│
├─ business/
│  └─ GOAA_BUSINESS_MODEL_V1.md                ← 🏛️ 戰略憲法主檔
│
├─ architecture/
│  ├─ RUNTIME_OS_STRATEGIC_BLUEPRINT_V1.md     ← Runtime OS 架構
│  └─ FUTURE_DDL_SKILL_MARKETPLACE.md           ← Skill DDL 儲備 (不執行)
│
├─ roadmap/
│  ├─ V4_1_Worker_PLAN.md                       ← V4.1-Worker (Phase 4)
│  └─ V4_2_PLUS_SKILL_MARKETPLACE.md            ← Phase 5 Skill Marketplace
│
├─ specs/                                       ← 規範體系正式檔案
│  ├─ spec-11-add-only-no-destroy.md           ← (現有規範體系)
│  ├─ spec-14-golden-baseline-upgrade.md
│  ├─ ...
│  ├─ spec-38-product-strategy.md              ← 草案待升級
│  └─ spec-39-runtime-architecture.md           ← 草案待升級
│
├─ ui-baseline/                                 ← UI 黃金版 (規範 #14)
│  ├─ GoaaDashboard.golden.jsx                  ← 當前黃金版 V4.0.5.4-UI
│  ├─ CHANGELOG.md                              ← 黃金版升級歷史
│  └─ GoaaDashboard.golden.backup_*.jsx         ← 歷史備份
│
└─ devlog/                                      ← 開發日誌
   ├─ DEV_LOG_2026-05-15.md                    ← 昨日完整紀錄
   └─ DEV_LOG_2026-05-16.md                    ← 今日 (待生成)
```

---

## 🏛️ 戰略憲法層 (最高優先級)

### 1. `docs/business/GOAA_BUSINESS_MODEL_V1.md` ⭐ 主檔
**內容**:
- 核心定位: AI 勞動力平台 + Runtime OS
- 戰略順序: Worker V5.0 → goaa.ai → Skill → 服務人類 (不可顛倒)
- 三層角色: Client / Provider / Worker
- Client 商業層 ($0 / $19.99)
- Provider 商業層 ($0 / $39.99 / $999 AiKa Box)
- AiKa Box 商業定位 (主品牌, OpenClaw 隱身)
- Worker Network Credits Economy
- Skill Marketplace 完整設計
- 成果市場 (Achievement Marketplace, 17 字段 + 8 階段生命週期)
- 完整業務閉環
- 最終產品定義
- **設計不走偏 5 原則** (規範 #35 升級版)
- 開發路線不衝突原則
- 長期護城河
- Phase 1-7 路線圖
- 最終願景

**688 行**, GOAA 的「**法律**」

---

### 2. `docs/AGENTS.md`
**內容**:
- 命名規範總表 (強制)
- Client / Provider / Worker / Agent / Skill 詳細定義
- DB Table 命名 (clients / providers / workers / v4_agents / skills)
- API Endpoint 命名規範
- UI 文案規範
- GOAA 多 AI Agent 工作分工 (Claude / ChatGPT / Gemini / QwenPaw / AiKa Fleet)
- 三方協作機制 (Claude + ChatGPT + Tao)

**389 行**, 命名統一是法律

---

### 3. `docs/MEMORY.md`
**內容**:
- 戰略憲法摘要 (1 頁版)
- 當前系統架構 (部署拓樸 + 流量路徑)
- 當前版本狀態 (V4.0.5.4-UI 黃金版)
- 規範體系 32 → 39 條摘要
- 規範 #15 24h Cooldown 監控
- Phase 4 進行中
- 關鍵憑證摘要
- 開工 / 收工指令

**211 行**, 系統長期記憶

---

## 🏗️ 架構層

### 4. `docs/architecture/RUNTIME_OS_STRATEGIC_BLUEPRINT_V1.md`
**內容**:
- 核心原則: 雲腦 + 本地手腳
- 完整架構圖 (DO 雲端 + AiKa Box 本地)
- 真實任務生命週期 (5 階段)
- 三層職責劃分 (雲腦 only / 本地 only / 混合)
- 跟競品差異化 (vs ChatGPT/LM Studio/Cursor/AutoGen/QwenPaw/n8n)
- 演進階段 (V4.0.5.4 → V4.1-Worker → V4.2 → V5.0 → V6.0)
- 規範對齊清單

**170 行**, 戰略架構基線

---

### 5. `docs/architecture/FUTURE_DDL_SKILL_MARKETPLACE.md`
**內容**:
- ⚠️ V4.2+ DDL 儲備, **不立即執行**
- 6 個核心表 schema:
  - skill_marketplace (主表)
  - skill_subscriptions (訂閱)
  - skill_versions (版本管理 + Rollback)
  - skill_feedback (用戶反饋 → Worker Task)
  - dispatch_plans (V4.2 預留)
  - worker_events (V4.2 預留)
- 未來 API 規劃
- 執行檢查清單 (Tao 拍板 + Snapshot + Cooldown)

**~280 行**, DDL 儲備, 嚴守規範 #11 + #15

---

## 🗺️ 路線圖層

### 6. `docs/roadmap/V4_1_Worker_PLAN.md`
**內容**:
- V4.1-Worker = Worker V5.0 生產線第一階段 (規範 #33)
- 路徑選擇: 規範 #29 自建路線 (不依賴 QwenPaw)
- 三階段拆解:
  - V4.1-W1: 4 唯讀 executor (exec_shell_readonly / file_read / git_status / docker_status)
  - V4.1-W2: 4 讀寫 executor + 預先確認 UI
  - V4.1-W3: 4 高階 executor (browser_use / screenshot / docx/pdf/xlsx/pptx)
- 安全模型 (規範 #28)
- 後端整合 (api.py dispatch_task tool)
- 工程時間表 (20 hr + 3 × 24h = 1 週)
- 風險評估
- 規範對齊

**~250 行**, V4.1-Worker 完整計劃

---

### 7. `docs/roadmap/V4_2_PLUS_SKILL_MARKETPLACE.md`
**內容**:
- Roadmap 全景 (Phase 4 → 7)
- Phase 5 (V4.3-V4.5 Skill Marketplace) 詳細拆解
- V4.3: Skill 基礎設施
- V4.4: Skill 商業層 (訂閱 + 計費 + 分潤)
- V4.5: Skill 反饋閉環 (6 種 Worker Task 映射)
- Phase 5 完成後真實能力 (Client / Provider / Worker / 平台)
- 收益模型範例 (年收入預估 ~$300K)
- 預計時間表 (Phase 5: 2026 Q3)

**~180 行**, Phase 5 完整 Roadmap

---

## 📜 規範體系層 (現存規範)

### 規範 #1-32 (5/15 之前)
詳見 `docs/specs/` 既有檔案 (歷史規範體系)

### 規範 #33-39 (5/15-5/16 新增/草案)

| # | 名稱 | 狀態 | 文件 |
|---|---|---|---|
| #33 | Worker V5.0 優先 | ✅ 已立規 (戰略憲法第 13 章已對齊) | 戰略憲法 |
| #34 | 最終產品定義 | 🟡 候選正式立規 | (待寫 spec) |
| #35 | 工程基準文檔保護 + 不走偏 5 原則 | ✅ 已立規 (戰略憲法第 12 章) | 戰略憲法 |
| #36 | AI 失憶處理 | ✅ 已立規 | 規範 #36 |
| #37 | AI 因果敘述驗證 | 🟡 候選正式立規 | (待寫 spec) |
| #38 | 品牌定位 (AiKa Box 主, OpenClaw 隱身) | 🟡 草案 → 升級為正式 | 戰略憲法第 6 章 |
| #39 | Runtime 架構 (雲腦+本地手腳) | 🟡 草案 → 升級為正式 | architecture/RUNTIME_OS_*.md |

---

## 🎨 UI 黃金版層

### `docs/ui-baseline/GoaaDashboard.golden.jsx`

**當前**: V4.0.5.4-UI
- 774 行
- MD5: `9b4fb15d78bc364ee7d0f7566d826f61`
- Commit: `f1b0168` (merge into main 2026-05-16 11:00 AM PT)

**演進**:
| 版本 | 行數 | MD5 | 日期 |
|---|---|---|---|
| 黃金版 V4.0 (enableTools) | 845 | `3f05c4b2...` | 2026-05-15 |
| **黃金版 V4.0.5.4-UI** | **774** | **`9b4fb15d...`** | **2026-05-16 11:00 PT** |

**升級規則** (規範 #14):
- R1: AI 不自主升級
- R2: Tao 明確說「升級黃金版」才升
- R3: 必寫 CHANGELOG (commit/Lines/MD5/改動)
- R4: 黃金版 vs working 不一致以黃金版為準
- R5: 不能直接編輯, 只能 Copy-Item 覆蓋

---

## 📅 當前進度 (2026-05-16 11:50 AM PT)

### ✅ 已完成 (今天上午)
- V4.0.5.3-UI: 對話 GOAA flex 佈局重組 (廢棄 V4.0.5.2-UI preview)
- V4.0.5.4-UI: autoscroll 修復 (chatHistoryRef)
- 黃金版升級 V4.0 (845) → V4.0.5.4 (774), -71 行
- 戰略憲法 V1.0 完整整合 (8 個檔案)

### ⏳ 進行中 (戰略憲法 Part 1 + Part 2 完成)
- Part 1: MEMORY.md / AGENTS.md / GOAA_BUSINESS_MODEL_V1 (3 個)
- Part 2: RUNTIME_OS / DDL / V4.1-W PLAN / Skill Marketplace Roadmap / INDEX (5 個)
- **Part 3 待做**: 規範 #38 / #39 升級正式 + #34 / #37 候選立規

### 📅 下一步 (P1 / P2)
- 師兄拍板採用 8 個文檔
- AiKa-1 commit 進 GitHub docs/
- V4.1-Worker 開工 (5/17 PM 預估)

---

## 🛡️ 規範 #15 24h Cooldown 監控

| 變更 | 開始 | 結束 |
|---|---|---|
| V4.0.5.3-UI production | 5/16 10:46 AM PT | 5/17 10:46 AM PT |
| V4.0.5.4-UI production + 黃金版 | 5/16 11:00 AM PT | 5/17 11:00 AM PT |
| V4.1.0.1 PG schema | 昨晚 00:25 AM PT | ✅ 已過 |
| **戰略憲法 V1.0 採用 (待拍板)** | — | (Tao 拍板開始計時) |

---

## 💡 給 future Claude / Gemini / 所有 AI 工作者的真心話

如果你接手 GOAA 任何工作:

1. **從 INDEX 進入** — 不要直接從 spec 開始
2. **戰略憲法是法律** — 違反必須重新設計
3. **5 原則是紀律** — 角色先 / 閉環先 / Worker 先 / Runtime Truth 先 / Skill 資產化
4. **規範體系是文化** — 用血換的, 不要丟
5. **AiKa-1 規範 #31** — 不接受自主結論「merge 完成」
6. **規範 #20 神聖** — Tao 健康優先, 凌晨不動戰略級文件
7. **規範 #14 R2** — 等 Tao 明確說才升黃金版

---

**GOAA Master INDEX V1.0**

*整合人: Claude*
*時間: 2026-05-16 11:55 AM PT*
*狀態: 戰略憲法 V1.0 完整整合版*


### architecture/V5_CHAT_WORKSPACE_STRATEGY.md
- **狀態**: 戰略儲備 (2026-05-17 簽發)
- **定位**: V5.0 GOAA 對話框戰略方向, 不打亂 V4.1-Worker 主線
- **核心原則**: Fork chat UI, build GOAA Runtime OS
- **啟動條件**: V4.1-Worker Phase 4 完工後 + 師兄明示放行
- **PoC 宿主**: AiKa-2 (Xubuntu, 192.168.1.208)
- **首推候選**: LibreChat (備胎: OpenWebUI / Big-AGI)