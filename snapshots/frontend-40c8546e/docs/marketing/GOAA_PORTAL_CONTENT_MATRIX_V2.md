# GOAA.AI Portal Content Matrix V2.0

> **戰略重構藍圖文檔 — 2026-05-17 簽發**
> 一句話原則: **從 Chatbot / 寵物小龍蝦, 升級為 Physical AI Runtime OS**
> 核心戰略: **中文保留品牌靈魂, 英文升級為矽谷硬核工具鏈語言**
> 本文檔為 **goaa.ai V2.0 改版藍圖, 不直接修改 production**

---

## 0. Strategic Refactor Summary

### 0.1 重構目的 (Why V2.0)

本次重構回應的真實問題:

| 維度 | V1.x 現狀 (Radison Template 殘留) | V2.0 戰略升級 |
|---|---|---|
| **產品定位** | Chatbot / AI 寵物小龍蝦 | Physical AI Runtime OS / 數位勞動力經濟體 |
| **核心 metaphor** | 「養 AI 龍蝦」(消費品玩具感) | 「通電、連網、部署實體 AI 勞動力」(基礎設施感) |
| **目標對象** | 個人用戶 (單層) | Client + Provider + Worker 三層生態 |
| **盈利模式** | 訂閱費 (模糊) | Provider Pro $39.99/mo + Skill Marketplace + Credits 結算 |
| **品牌語氣 (中)** | 雙語混雜, 部分英文殘留 | 中文版完整保留靈魂 (「能做事, 能賺錢」/「AI 數字生活小龍蝦」) |
| **品牌語氣 (英)** | 直翻中文 metaphor (失去溢價感) | 矽谷硬核重寫 (Distributed AI Labor / Edge Compute / Provider-grade OS) |
| **國際化** | 主語言混亂, 無 toggle | EN | 中 manual toggle, 不做 OS auto-detect |

### 0.2 異構市場雙軌防護網 (規範 #29)

V2.0 採用**中英雙軌制**, 不是簡單翻譯:

- **中文版** = 本土化情感共鳴 + 傳播靈魂 (面向北美華人 / 中國背景 / complex global lives 用戶)
- **英文版** = 矽谷硬核 + 高溢價 SaaS / AI Infrastructure 語言 (面向國際資本 / 極客用戶 / Provider 群體)

兩個版本**意譯互通, 文案各自獨立**, 不互為直翻。

### 0.3 本文檔角色聲明

| 項 | 說明 |
|---|---|
| **本文檔類型** | 戰略內容矩陣 + Framer V2.0 改版藍圖 |
| **執行範圍** | GitHub 文檔合流, 不修改 Framer production |
| **不允許** | Publish goaa.ai / 改 Framer / 改 V4.1-Worker 主線 / 編造 AiKa Box 硬體 Spec / 把 Credits 描述為收益保證 |
| **允許** | 創建 / 更新本 Markdown 文檔 |
| **後續執行** | 由 Tao 師兄人工 review + 拍板, 進入 Framer V2.0 draft page 階段化重構 |

### 0.4 規範對齊清單

| 規範 | 對應 |
|---|---|
| #11 (只增不毀) | 不刪除現有中文品牌內容, 純新增 V2.0 矩陣 |
| #15 (24h cooldown) | 本文檔 push 後計時, Framer 動作獨立 cooldown |
| #27 (Integration First) | 重用 Framer 平台, 不自建 CMS |
| #29 (敢創新) | 中英雙軌防護網, 不強行統一 |
| #30 (漸進式智能) | 文檔先行 → Framer draft page → 人工 review → Publish |
| #36 (失憶防護) | AiKa Box 真實能力基於 aika-download / geekom_comparison HTML 吸收, 不憑想像 |
| SUPREME 1.4 | Runtime Truth — 不承諾未交付的硬體 Spec, 不誇大未上線的 Skill |

---

## 1. Global Navigation / Header

### 1.1 中文版 Header

**Logo**: GOAA (現有 logo 保留)

**導航項** (左到右):

| 中文項 | Anchor / Link | 對應 Section |
|---|---|---|
| 首頁 | `/` 或 `#hero` | Hero (Section 2) |
| 生態 | `#ecosystem` | Three-Tier Ecosystem (Section 3) |
| 技能市場 | `#marketplace` | Skill Marketplace (Section 5) |
| Provider Pro | `#provider` | Provider Layer (Section 3.2) |
| Worker Network | `#worker` | Worker Layer (Section 3.3) |
| 聯繫我們 | `#contact` | Trust / Contact (Section 6) |

**右上角控件區**:
- **EN | 中 Toggle**: 兩個分頁, 預設「中」, 手動切換
- **主 CTA 按鈕**: 「部署我的 AI 勞動力」(紫色 / Cyber-Noir 風格)

### 1.2 English version Header

**Logo**: GOAA (same)

**Navigation items** (left to right):

| English | Anchor / Link | Corresponding Section |
|---|---|---|
| Home | `/` or `#hero` | Hero (Section 2) |
| Ecosystem | `#ecosystem` | Three-Tier Ecosystem (Section 3) |
| Skill Marketplace | `#marketplace` | Skill Marketplace (Section 5) |
| Provider Pro | `#provider` | Provider Layer (Section 3.2) |
| Worker Network | `#worker` | Worker Layer (Section 3.3) |
| Contact | `#contact` | Trust / Contact (Section 6) |

**Top-right controls**:
- **EN | 中 Toggle**: Two tabs, default to user's last choice or `EN`, manual switch
- **Primary CTA**: "Deploy AI Labor" (Cyber-Noir purple)

### 1.3 語言切換規則

| 規則 | 說明 |
|---|---|
| 預設語言 | 第一次訪問: 預設**中文**; 後續訪問: 讀取 localStorage 保留上次選擇 |
| 切換方式 | 純手動點擊 EN | 中 toggle, **不做 OS auto-detect** |
| URL 區分 | 建議: `/` (中文) / `/en` (英文), 或 query param `?lang=en` |
| 內容同步 | 中英版 sections 數量必須一致 (語意對應, 不要其中一版多出區塊) |

### 1.4 Header 視覺風格

- 風格延續 Cyber-Noir 黑色基調 (對齊 Dashboard 黃金版 V4.0.5.4-UI)
- 固定 (sticky) 頂部, 滾動透明度漸變
- Logo 高度 32-40px
- 導航項 hover 效果 (顏色變紫色 + 底線淡入)
- EN | 中 Toggle 樣式: 兩個 pill 按鈕, 選中態紫色背景

---

## 2. Hero Section — Physical AI Runtime OS

### 2.1 戰略定位

**從**: 「聊天 / 對話式 AI 工具」**升級為**: 「軟硬一體化的數位勞動力中樞」

第一屏的視覺與文案必須瞬間傳遞:

1. **這不是 Chatbot** — 不是又一個 ChatGPT 包裝
2. **這是 OS** — 像 Windows / iOS 一樣的「運行平台」
3. **它真的會幹活** — 不只生成文字, 是執行真實工作流
4. **它連接實體硬體** — AiKa Box 不是雲端虛擬機, 是擺在你家的盒子
5. **它創造收益** — 不止省時間, 還能賺錢

### 2.2 主視覺設計

**核心元素**:
- 中央: **AiKa Box 龍蝦盒子硬件 render placeholder** (真實渲染圖位置, 等實機照片)
- 視覺效果: **electric-blue breathing light** (寶藍色呼吸燈, `animate-pulse` 樣式)
- 背景: Cyber-Noir 黑色 + 微星點 + 漸層光
- 旁邊: 流動的 task 列表 (puls 動畫, 顯示 "OCR 解析中..." "報稅自動填寫中..." 等真實任務)

**Metaphor**: Local node / Edge runtime / Physical labor (不是 "AI 助理")

⚠️ **Spec 隔離條款**: 本文檔**不規定** AiKa Box 的 CPU / RAM / 端口等硬體 spec, 等實際硬體開發完成後由師兄拍板補充。當前 placeholder 文案應寫 "邊緣工作站" 等 metaphor, 不寫 "搭載 i5-12450H / 16GB DDR4" 等假 spec。

### 2.3 中文 Hero 文案

#### 主標題 (兩行)

```
GOAA Runtime OS
讓 AI 真正下場幹活的實體數位勞動力系統
```

#### 副標題 (3 句, 換行排版)

```
停止無意義的字元拼湊。
通電、連網, 部署真正的實體數位勞動力。
7×24 小時為你全自動閉環幹活, 捍衛隱私, 創造複利。
```

#### 品牌靈魂句 (微小字, 但醒目)

```
能做事, 能賺錢。
你的 AI 數字生活小龍蝦。
```

> 品牌靈魂句的位置: 主副標題之下, CTA 之上, 字體比副標題小但顏色更亮 (紫色或金色 accent)。
> **戰略意圖**: 中文用戶看到「小龍蝦」會心一笑 (本土情感), 同時上面的「Runtime OS / 實體數位勞動力」確立硬核基調。雙軌並存。

#### 雙 CTA (並排)

```
[ 開始部署 AI 勞動力 → ]   主 CTA, 紫色實心
[ 查看 Worker Network ]    次 CTA, 紫色描邊
```

### 2.4 English Hero Copy

#### Main headline (two lines)

```
GOAA Runtime OS
Deploy Physical AI Labor, Not Just Chatbots.
```

#### Subheadline (3 lines)

```
Stop generating pure text.
Power on, connect, and deploy native physical AI labor that automates real-world workflows 24/7.
Sandboxed, privacy-first, and designed for compound productivity.
```

#### Brand soul tagline (subtle but accented)

```
Make it work. Make it earn.
Your edge-deployed AI labor unit.
```

> **戰略意圖**: 英文版**避免直翻「小龍蝦」**。"edge-deployed AI labor unit" 是矽谷硬核工具鏈語言, 保留「個人化 AI 勞動單元」的靈魂, 但用 infrastructure 語言重寫。
> "Make it work. Make it earn." 對應「能做事, 能賺錢」, 短促有力, 雙押韻 (work / earn), 符合英文 hook 美感。

#### Dual CTA

```
[ Deploy AI Labor → ]      Primary CTA, purple solid
[ Explore Worker Network ] Secondary CTA, purple outline
```

### 2.5 Hero 區塊文案邊界 (規範 #28 + SUPREME 1.4)

**不允許出現的措辭**:

| ❌ 禁止 | 原因 |
|---|---|
| 「保證收益 $X/月」 | Credits 收益不是金融保證 (Risk Register 條款 5) |
| 「合法替代律師/會計師」 | 合規邊界 (Risk Register 條款 6) |
| 「完美零錯誤」 | AI 沙箱有失敗率, 過度承諾傷品牌 |
| 「Search the world's largest AI workforce」 | 當前 Worker Network 規模真實是 3 節點 (Phase 3 上線), 不誇大 |
| 「AiKa Box 內建 X 核 Y GB」 | 硬體 spec 未定案前禁止寫死 |

**允許的措辭**:

| ✅ 鼓勵 | 原因 |
|---|---|
| 「為你 7×24 自動執行真實工作流」 | Runtime Truth (Worker 真實會跑) |
| 「本地優先, 數據不離開你的盒子」 | AiKa Box 真實能力 (吸收自 geekom_comparison) |
| 「閒置算力可接入網絡, 換取 Credits」 | 真實設計 (geekom_comparison 明列) |
| 「Credits 可抵扣月費或兌換 Skill」 | 真實設計 (memory: $39.9 = 3,990 Credits 抵月費) |

---

## 3. Three-Tier Ecosystem Matrix (Revised — 對齊戰略憲法 V1.0)

### 3.0 三層生態戰略架構圖

GOAA 不是單一產品, 而是**三層互鎖的勞動力經濟體**, 三層各有獨立商業模型 + 共享 Credits 結算層:

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Layer / 用戶端                     │
│   Free $0  →  Plus $19.99/mo (觸發: 需要真人服務時)           │
│              ↓ 任務派發                                        │
├─────────────────────────────────────────────────────────────┤
│                  Provider Layer / 專業服務者端                │
│   Free $0  →  Pro $39.99/mo (觸發: 希望獲取客戶訂單時)         │
│            +  AiKa Box $999 硬件 或 $99/mo                    │
│              ↓ Skill / Workflow 編排                          │
├─────────────────────────────────────────────────────────────┤
│              Worker Network Layer / 勞動力網絡端              │
│   三條賺錢通道:                                                │
│   ① 任務執行 (OCR / 自動化) → Credits                          │
│   ② 閒置算力市場 (本地 AiKa Box) → Credits                     │
│   ③ Skill 開發推 Marketplace → 50/50 分潤 (新)                │
│              ↓ Credits 結算回流                                │
├─────────────────────────────────────────────────────────────┤
│           Credits Economy / 積分經濟結算層 (底層)              │
│   $0.01 / Credit · QS < 0.6 無 payout · 抵月費可兌 Skill       │
└─────────────────────────────────────────────────────────────┘
```

**核心商業邏輯**:
- Client 出錢 (按需訂閱 / Credits 消費) → 觸發點是「**需要真人**」, 不是預付牆
- Provider 出腦 (專業判斷) → 升級點是「**想接平台訂單**」, 免費試水後付費接單
- Worker 出力 (算力 + 開發) → **三條賺錢通道**, 不只執行也能生產資產

---

### 3.1 Client Layer / 用戶端 (兩階梯訂閱)

#### 3.1.1 中文版卡片

**Header**:
```
👤 Client Layer
你的 AI 生活管家 — 從免費對話到真人撮合
```

**定位文案**:
```
讓普通家庭和個人, 用 AI 處理生活、財務、保險、房貸、稅務和文件壓力。
你提出問題, GOAA 結構化拆解。當需要真人服務時, $19.99/月解鎖 Provider 撮合。
```

**兩階梯訂閱**:

##### 階梯 1: Free ($0) — 對話與分析

```
免費獲得:
✓ 與 AI 對話 / 提問 / 諮詢
✓ 上傳資料 / 獲取結構化分析
✓ 獲取下一步任務建議
✓ AI 自動理解需求, 結構化拆解

三大真實場景:

【場景 1: IRS 稅務信件】
你: 「我收到一封 IRS 的信, 我看不懂。」
GOAA: OCR 解析 → 總結重點 → 風險提示 → 推薦下一步動作

【場景 2: 房貸壓力】
你: 「我想買房, 但不知道預算。」
GOAA: 分析收入 → 估算貸款能力 → 推薦方案 → 提示需要持牌 Provider

【場景 3: 退休保險】
你: 「我 45 歲, 想規劃退休。」
GOAA: 分析需求 → 估算資金缺口 → 推薦 IUL / Term 方案 → 提示需要 Provider
```

⚠️ **邊界**: Free 階段 AI 只做結構化分析, **不撮合真人 Provider**。Provider 撮合需要升級 Plus。

##### 階梯 2: Plus ($19.99 / 月) — 真人服務連接

```
觸發條件: 當 AI 拆解後, 你需要「真人專業服務」接手時, 出現 Plus 升級牆。

升級獲得:
✓ AI + 真人 Provider 協作模式
✓ 看到匹配領域的 Provider 列表 (含執照 / 評分 / 案例)
✓ AI 自動整理你的資料 / 表格 / 文件 → 直送選定 Provider
✓ AI 工作流輔助 (持續跟進 Provider 進度)
✓ 優先匹配 (Pro 等級 Provider 優先派發)
✓ 多輪任務協作 (跨 session 記憶, 不重複填表)
✓ 完整歷史任務記錄 (可審計)

何時值 $19.99/月:
單次撮合一個會計師 / 律師 / 房貸顧問 → 省下你自己找 + 比較 + 篩選的 4-8 小時
任務完成後可暫停訂閱, 下次需要再續訂 (規範 #11 不強制鎖定)
```

⚠️ **邊界**: GOAA 提供 AI 撮合與資料整理, **不替代專業者本身**。所有法律、稅務、保險、投資的最終決策由持牌 Provider 負責。

#### 雙 CTA

```
[ 開始免費對話 → ]            主 CTA, 紫色實心
[ 了解 Plus 升級觸發 ]        次 CTA, 紫色描邊
```

---

#### 3.1.2 English version card

**Header**:
```
👤 Client Layer
AI Life Operations — From Free Chat to Provider Match
```

**Positioning**:
```
AI-powered life, finance, compliance, and document automation for everyday clients.
You bring the problem. GOAA structures it. When you need a real human, $19.99/mo unlocks provider matching.
```

##### Tier 1: Free ($0) — Conversation & Analysis

```
Get for free:
✓ AI conversation, Q&A, consultation
✓ Upload documents, receive structured analysis
✓ Next-step task recommendations
✓ AI auto-understanding and structured decomposition of your needs

Three real-world scenarios:

【Scenario 1: IRS Letter】
You: "I got a letter from the IRS. I don't understand it."
GOAA: OCR parsing → key risks → response options → next steps

【Scenario 2: Mortgage Stress】
You: "I want to buy a house but don't know my budget."
GOAA: Income analysis → loan capacity estimate → option matrix → "you'll need a licensed provider"

【Scenario 3: Retirement Planning】
You: "I'm 45 and want to plan retirement."
GOAA: Needs analysis → funding gap estimate → IUL / Term comparison → "you'll need a provider"
```

⚠️ **Boundary**: In Free tier, AI only performs structured analysis. **No provider matching** without Plus upgrade.

##### Tier 2: Plus ($19.99 / month) — Real Provider Connection

```
Trigger: When AI decomposition concludes you need a real licensed provider, 
a Plus upgrade prompt appears. No upfront paywall.

Plus unlocks:
✓ AI + licensed Provider collaboration mode
✓ Provider list display (license, ratings, case history)
✓ AI auto-assembles your data / forms / docs → delivered to chosen Provider
✓ Workflow assistance (continuous follow-up tracking)
✓ Priority matching (Pro-tier Providers prioritized)
✓ Multi-round cross-session memory (no repeated form-filling)
✓ Full auditable task history

When $19.99/mo pays off:
One match for an accountant / attorney / mortgage broker saves you 
4-8 hours of finding, comparing, vetting. Cancel after task done, re-subscribe when needed.
```

⚠️ **Boundary**: GOAA provides AI matching and data prep — **not professional replacement**. 
Final legal/tax/insurance/investment decisions rest with the licensed Provider.

#### Dual CTA

```
[ Start Free Chat → ]              Primary CTA, purple solid
[ Learn Plus Trigger ]             Secondary CTA, purple outline
```

---

### 3.2 Provider Layer / 專業服務者端 (三階梯, 含硬件)

#### 3.2.1 中文版卡片

**Header**:
```
👔 Provider Layer
免費試水 → Pro 接單 → AiKa Box 全副武裝
```

**定位文案**:
```
為保險、房產、稅務、會計、貸款、移民等專業服務者提供
免費 AI 工具 → Pro 接平台訂單 → AiKa Box 邊緣工作站 三階成長路徑。
你接案, AI 幹活, Worker Network 跑底層任務。
```

##### 階梯 1: Free ($0) — AI 工具試水

```
免費獲得:
✓ AI 測試 / 上傳文檔
✓ AI 自動分析客戶資料
✓ AI 自動填表 (TurboTax / TaxAct / Excel 等)
✓ 基礎 CRM (客戶名單 / 聯絡記錄)
✓ Provider Profile 上架 (但不接平台訂單)

定位: 讓 Provider「先試試 AI 能不能省事」, 不收錢, 不鎖功能。
```

##### 階梯 2: Pro ($39.99 / 月) — 接平台訂單

```
觸發條件: 當 Provider 希望「獲取客戶訂單」時, 升級 Pro。

Pro 解鎖:
✓ AI 自動接單 (Client Plus 撮合進來的訂單直送)
✓ Client Leads (按專業領域 + 地理 + 評分匹配)
✓ AI 自動整理客戶資料 / 表格 / 總結 / 報價 / 跟進
✓ AI CRM 完整版 (提醒 / 工作流管理 / 自動 follow-up)
✓ 8 大 Provider 賣點全部啟用 (詳見舊版 3.2 章節)

為什麼 Provider 願意付 $39.99/月:
單客戶獲取成本: 傳統 $80-300 → Pro 約 $5-15 (含 Credits)
處理時間: 傳統 25-45 min/案 → Pro 約 3-8 min/案
回本門檻: 月接 1-2 個額外案件即可 cover 訂閱費
Credits 抵扣: 3,990 Credits = $39.9, 完全可由本月接案產生的 Credits 自動抵扣
```

##### 階梯 3: AiKa Box ($999 一次性硬件 或 $99 / 月)

```
觸發條件: 當 Provider 想「把 AI 真正部署到辦公室」時。

AiKa Box 是什麼:
- 本地 AI Worker Appliance (本地 AI 工作盒子)
- 不是普通電腦, 不是聊天機器人
- 放在 Provider 辦公室裡的實體 AI 邊緣工作站

核心能力:
✓ 本地 .exe 自動化 (TurboTax / TaxAct / Excel 直接控)
✓ 局域網文件直接讀寫 (辦公室共享文件夾)
✓ 網頁自動化無反爬 (本地 IP 過政府 / 銀行)
✓ 離線 AI 推理 (數據不離開辦公室, 合規)
✓ Docker / Git / Browser Automation
✓ 本地模型 / GPU 推理 / OCR / 多任務處理
✓ 閒置時自動接入 Worker Network 賺 Credits ($50-150/mo 額外收入)

兩種購買:
- 一次性硬件 $999 (擁有所有權, 長期最划算)
- 月付 $99/月 (低門檻試水, 隨時退訂)

回本計算 (基於 RTX 4060 + 100 任務/月):
- 每月 Credits 節省: $45
- 閒置算力收入: $80
- 扣除電費後淨收益: $125/月
- 回本月數: 6-12 個月 (依使用密度)
```

⚠️ **品牌哲學** (戰略憲法第 6 章):
> **AiKa Box 是主品牌, OpenClaw 是技術層隱身**
> 對外: 「本地 AI Worker 自動執行任務」
> 內部: 「GOAA Runtime OS with OpenClaw Gateway」
> 普通用戶不會為「OpenClaw」買單, 但會為「**本地 AI 自動幹活**」買單。

⚠️ **邊界**: $39.99 / $99 / $999 為當前定價, 未來可能調整。Pro 不保證 Leads 數量, AiKa Box 性能依工作負載而異。

#### 三 CTA

```
[ 免費試 AI 工具 → ]              主 CTA (Free)
[ 升級 Pro 接訂單 ]               次 CTA (Pro)
[ 了解 AiKa Box 邊緣工作站 ]      三 CTA (AiKa Box)
```

---

#### 3.2.2 English version card

**Header**:
```
👔 Provider Layer
Free Trial → Pro Inbound → AiKa Box Full Deployment
```

**Positioning**:
```
For insurance, real estate, tax, accounting, mortgage, and immigration professionals:
Free AI tools → Pro inbound leads → AiKa Box edge appliance. A three-tier growth path.
You close deals. AI handles paperwork. Worker Network runs the backend.
```

##### Tier 1: Free ($0) — Test the AI

```
Free access:
✓ AI testing and document upload
✓ AI auto-analysis of client materials
✓ AI auto-fill (TurboTax / TaxAct / Excel etc.)
✓ Basic CRM (contact list, call logs)
✓ Provider profile listing (NOT eligible for platform-routed leads)

Purpose: Let Providers try AI without commitment. No fee. No locked features.
```

##### Tier 2: Pro ($39.99 / month) — Receive Platform Leads

```
Trigger: When the Provider wants inbound client leads, they upgrade to Pro.

Pro unlocks:
✓ AI auto-routing of Client Plus matches directly to your inbox
✓ Client Leads scored by domain expertise + geography + ratings
✓ AI auto-prep of client data / forms / quotes / follow-ups
✓ Full CRM (reminders, workflow management, auto-follow-up)
✓ Eight Provider value props fully activated

Why Providers pay $39.99/mo:
Acquisition cost: traditional $80-300 → Pro ~$5-15 (incl. Credits)
Processing time: traditional 25-45 min/case → Pro ~3-8 min/case
Break-even: 1-2 additional cases per month covers the subscription
Credits offset: 3,990 Credits = $39.9, fully offsettable by Credits earned from cases
```

##### Tier 3: AiKa Box ($999 one-time or $99 / month)

```
Trigger: When the Provider wants to deploy AI physically in their office.

What AiKa Box is:
- A local AI Worker Appliance
- Not a PC, not a chatbot device
- A physical edge AI workstation installed in the Provider's office

Core capabilities:
✓ Local .exe automation (direct control of TurboTax / TaxAct / Excel)
✓ LAN file direct read/write (office shared folders)
✓ Anti-bot web automation (local IP passes gov / bank sites)
✓ Offline AI inference (data never leaves the office, compliance-ready)
✓ Docker / Git / Browser Automation
✓ Local model / GPU inference / OCR / multi-task processing
✓ Idle-time auto-connection to Worker Network ($50-150/mo extra)

Two purchase options:
- One-time hardware $999 (full ownership, best long-term)
- Monthly $99/mo (low entry, cancel anytime)

ROI (based on RTX 4060 + 100 tasks/month):
- Monthly Credits savings: $45
- Idle compute revenue: $80
- Net of electricity: $125/month
- Payback period: 6-12 months
```

⚠️ **Brand Philosophy** (Charter Ch. 6):
> **AiKa Box is the primary brand. OpenClaw is the runtime layer, hidden.**
> External: "Local AI Worker that automates real tasks."
> Internal: "GOAA Runtime OS with OpenClaw Gateway."
> Regular users won't pay for "OpenClaw" but will pay for "**local AI that actually works**."

⚠️ **Boundary**: $39.99 / $99 / $999 are current prices, subject to adjustment. 
Pro does not guarantee lead volume. AiKa Box performance varies by workload.

#### Triple CTA

```
[ Try AI Free → ]                  Primary CTA (Free)
[ Upgrade to Pro for Leads ]       Secondary CTA (Pro)
[ Explore AiKa Box Appliance ]     Tertiary CTA (AiKa Box)
```

---

### 3.3 Worker Network Layer / 勞動力網絡端 (三條賺錢通道)

#### 3.3.1 中文版卡片

**Header**:
```
⚡ Worker Network
不只是執行者, 也是生產者 — 三條賺錢通道全開
```

**定位文案**:
```
讓閒置設備、AiKa Box、Docker Worker、瀏覽器自動化節點
加入 GOAA Worker Network, 通過任務執行 + 算力出售 + Skill 生產三條通道獲得 Credits 收益。
你的電腦不睡覺, 你的 RTX 顯卡不浪費, 你的開發能力也能變現。
```

##### 通道 1: 任務執行 (基礎收益)

```
做什麼:
- 文檔 OCR 任務 (Client 端稅單 / 保單)
- 瀏覽器自動化 (Playwright / Selenium)
- Docker 沙箱執行 (隔離安全)
- AI 視頻處理 / 本地 GPU 推理
- 本地模型推理 (Ollama qwen2.5:7b)

怎麼結算:
- 任務完成 → Quality Score 評估 → Credits 立即入帳
- 真實數字 (從 AiKa-Box Runtime Truth):
  - OCR + 自動報稅: 全程 3 分鐘, 結算 16 Credits ($0.16)
  - 純雲端模式同樣任務: 25 分鐘, 80 Credits ($0.80)

⚠️ Runtime Truth 邊界:
- QS < 0.6 → 無 payout, 任務退回 redo
- Security = 0 → 強制歸零 + 安全警報
- 只有本地 AiKa Box 賺 Credits, 雲端 VPS 節點不賺 (戰略憲法 7.3)
```

##### 通道 2: 閒置算力市場 (被動收益)

```
做什麼:
- 非工作時間 (晚上 / 週末) 自動接入 Worker Network 跑批
- 本地 GPU (RTX 系列) 提供 AI 推理算力
- 本地 CPU + RAM 跑 Docker 沙箱任務

收益範例 (戰略憲法 + AiKa-Box HTML 真實素材):
- 基於 RTX 4060 + 100 任務/月
- 每月閒置算力收入: $80
- 加上 Credits 節省: $45
- 扣除電費後淨收益: $125/月

⚠️ 邊界:
- 收益依設備性能 + 任務量 + 電費 + 區域算力價格而異
- $125/月是測算值, 非保證
- 完全不影響工作時間使用 (Worker 工作時自動暫停閒置任務)
```

##### 通道 3: Skill 開發推 Marketplace (高溢價收益, NEW)

```
做什麼 (Worker = 生產者, 不只是執行者):

Worker 可開發以下類型 Skill, 推到 Skill Marketplace:
- Consumer Skill (Client 端): 家庭信件管理 / IRS 信件分析 / 房貸壓力測試
- Professional Skill (Provider 端): AI 視頻自動生成 / 保險方案精算 / Lead Follow-up

收益模式 (戰略憲法 8.3, 50/50 分潤):

【真實範例 A: Consumer Skill — 家庭信件管理】
- 月費: $2.99/月
- 訂閱: 1,000 人
- 本月總收入: $2,990
- GOAA 平台分潤: $1,495
- Worker 分潤 (你): $1,495
- Runtime 成本: $210
- 你的淨利潤估算: ~$2,780/月

【真實範例 B: Professional Skill — Provider 視頻生成】
- 月費: $9.99/月
- 訂閱: 300 個 Provider
- 本月總收入: $2,997
- GOAA 平台分潤: $1,498.50
- Worker 分潤 (你): $1,498.50
- Runtime 成本: $520
- 你的淨利潤估算: ~$2,477/月

8 階段完整生命週期 (戰略憲法 9.3):
1. 需求來源 → 2. 生成開發任務 → 3. Worker 開發 Skill → 4. 測試與驗收
→ 5. 封裝與版本化 → 6. 上傳到技能市場 → 7. 訂閱與計費 → 8. 反饋與升級

6 種反饋自動映射 Worker Task (戰略憲法 9.4):
- Bug → patch_task (P1)
- 體驗不好 → ux_improvement_task (P2)
- 速度慢 → optimization_task (P2)
- 想增功能 → feature_task (P3)
- 輸出錯誤 → prompt_fix_task (P1)
- 成本太高 → cost_optimization_task (P2)
- 安全問題 → security_fix_task (P0 緊急)
- 計費爭議 → billing_review_task (P1)

⚠️ 邊界:
- Skill 訂閱數依市場接受度而異, $2,780 / $2,477 為範例計算非保證
- 50/50 分潤為戰略憲法默認比例, 不隨意修改
- Skill 必須過測試與安全審查才能上架 (8 階段第 4 步)
- Rollback 機制保護: 訂閱者不滿可隨時取消, Worker 需快速響應反饋
```

##### Worker 節點類型

```
┌──────────────────────────────────────────────────────────┐
│ AiKa-Box (本地龍蝦盒子) — 命名: AKB-xxx                   │
│ 安裝在家 / 辦公室, Provider 主用, 局域網內最強, 反爬最強     │
│ ✅ 三條通道全開 (執行 / 算力 / Skill 開發)                 │
├──────────────────────────────────────────────────────────┤
│ AiKa-Cloud (雲端節點) — 命名: AKC-xxx                     │
│ 跑在 DigitalOcean / Hetzner, 公網可用, 即開即用            │
│ ⚠️ 戰略憲法 7.3: 雲端 VPS 不賺 Credits, 僅執行平台任務     │
├──────────────────────────────────────────────────────────┤
│ Worker 閒置設備 (用戶自接入)                              │
│ Mac mini / 舊筆電 / 工作站 GPU, Docker 跑 Worker Agent     │
│ ✅ 通道 1+2 可用, 通道 3 需 AiKa-Box 部署 (戰略憲法配套)   │
└──────────────────────────────────────────────────────────┘
```

##### Worker Network 真實規模 (Runtime Truth, 規範 SUPREME 1.4)

```
當前 Live 節點: 5 (aika-1 / aika-2 / do-cloud-1 / do-cloud-2 / do-cloud-3)
任務池累計: Phase 3 已啟動 (2026-05-13 首日 7 SUCCESS)
首日結算範例: $0.75 (技術驗證階段, 非運營階段)

V4.1-Worker 主線完工後 (預估 2-3 週): 10-50 節點規模
V4.3+ Skill Marketplace 上線後 (Phase 5): 100+ 節點 + 真實 Skill 訂閱
V5.0 上線後 (2026 Q3): 全球分散式 Worker Network 雛形
```

#### 三 CTA

```
[ 接入 Worker Network → ]         主 CTA (3 通道全開)
[ 了解 Skill 開發分潤 ]            次 CTA (通道 3)
[ 查看節點儀表板 ]                 三 CTA (Runtime Truth)
```

---

#### 3.3.2 English version card

**Header**:
```
⚡ Worker Network
Not Just Executors — Producers Too. Three Earning Channels.
```

**Positioning**:
```
Join GOAA Worker Network with your idle machines, AiKa Boxes, Docker workers, 
or browser automation nodes. Earn Credits through task execution + idle compute + 
Skill production. Your machine doesn't sleep. Your RTX doesn't idle. Your code earns.
```

##### Channel 1: Task Execution (Base Income)

```
What you do:
- Document OCR tasks (Client tax forms, policies)
- Browser automation (Playwright / Selenium)
- Docker sandbox execution (isolated security)
- AI video processing / local GPU inference
- Local model inference (Ollama qwen2.5:7b)

Settlement:
- Task done → Quality Score evaluated → Credits credited instantly
- Real numbers (from AiKa-Box Runtime Truth):
  - OCR + auto-tax-filing: 3 min total, 16 Credits ($0.16)
  - Pure-cloud equivalent: 25 min, 80 Credits ($0.80)

⚠️ Runtime Truth boundary:
- QS < 0.6 → no payout, task returned for redo
- Security = 0 → forced zero + security alert
- Only AiKa-Box (local) earns Credits. Cloud VPS nodes do not (Charter 7.3).
```

##### Channel 2: Idle Compute Market (Passive Income)

```
What you do:
- Auto-join Worker Network during off-hours (nights / weekends)
- Local GPU (RTX series) provides AI inference capacity
- Local CPU + RAM runs Docker sandboxed tasks

Sample earnings:
- Based on RTX 4060 + 100 tasks/month
- Monthly idle compute income: $80
- Plus Credits savings: $45
- Net of electricity: $125/month

⚠️ Boundary:
- Earnings vary by hardware / task volume / electricity / regional compute prices
- $125/mo is illustrative, not guaranteed
- Zero impact on work-hour usage (idle tasks auto-pause when you're working)
```

##### Channel 3: Skill Development → Marketplace (High-Margin Income, NEW)

```
What you do (Worker = producer, not just executor):

Develop Skills and publish them to the Skill Marketplace:
- Consumer Skills (Client side): household mail management / IRS triage / mortgage stress test
- Professional Skills (Provider side): AI video generation / insurance modeling / lead follow-up

Revenue model (Charter 8.3, 50/50 split):

【Real Example A: Consumer Skill — Household Mail Management】
- Price: $2.99/month
- Subscribers: 1,000
- Monthly revenue: $2,990
- GOAA platform share: $1,495
- Worker share (yours): $1,495
- Runtime cost: $210
- Your estimated net: ~$2,780/month

【Real Example B: Professional Skill — Provider Video Generation】
- Price: $9.99/month
- Subscribers: 300 Providers
- Monthly revenue: $2,997
- GOAA platform share: $1,498.50
- Worker share (yours): $1,498.50
- Runtime cost: $520
- Your estimated net: ~$2,477/month

8-stage lifecycle (Charter 9.3):
1. Demand sourcing → 2. Generate dev tasks → 3. Worker develops Skill → 4. Testing & QA
→ 5. Packaging & versioning → 6. Marketplace upload → 7. Subscription & billing → 8. Feedback & upgrade

6 feedback → Worker Task mappings (Charter 9.4):
- Bug → patch_task (P1)
- UX issue → ux_improvement_task (P2)
- Slow → optimization_task (P2)
- Feature request → feature_task (P3)
- Wrong output → prompt_fix_task (P1)
- Too expensive → cost_optimization_task (P2)
- Security → security_fix_task (P0 urgent)
- Billing dispute → billing_review_task (P1)

⚠️ Boundary:
- Subscriber counts vary by market reception. $2,780 / $2,477 are illustrative, not guaranteed.
- 50/50 split is the Charter default — not arbitrarily changed.
- Skills must pass testing and security review before marketplace listing (lifecycle step 4).
- Rollback protection: subscribers can cancel anytime; Workers must respond fast to feedback.
```

##### Worker node types

```
┌──────────────────────────────────────────────────────────┐
│ AiKa-Box (Edge Hardware Appliance) — Naming: AKB-xxx     │
│ Installed at home / office. Provider's primary tool.      │
│ ✅ All three channels (execution / idle / Skill dev)     │
├──────────────────────────────────────────────────────────┤
│ AiKa-Cloud (Cloud Node) — Naming: AKC-xxx                │
│ Runs on DigitalOcean / Hetzner. Public, instant-on.       │
│ ⚠️ Charter 7.3: Cloud VPS does NOT earn Credits.         │
│    Used for platform-routed tasks only.                   │
├──────────────────────────────────────────────────────────┤
│ Worker Idle Hardware (User-connected)                     │
│ Mac mini / old laptops / workstation GPUs running Docker  │
│ ✅ Channels 1+2 available. Channel 3 needs AiKa-Box.     │
└──────────────────────────────────────────────────────────┘
```

##### Worker Network Reality (Runtime Truth, SUPREME 1.4)

```
Current Live nodes: 5 (aika-1 / aika-2 / do-cloud-1/2/3)
Task pool: Phase 3 launched 2026-05-13 (7 SUCCESS day-one)
Day-one earnings example: $0.75 (validation phase, pre-revenue)

Post-V4.1 (2-3 weeks): 10-50 node scale
Post-V4.3+ Skill Marketplace (Phase 5): 100+ nodes + real Skill subscriptions
Post-V5.0 (2026 Q3): global distributed Worker Network embryo
```

#### Triple CTA

```
[ Connect Worker Node → ]          Primary CTA (all 3 channels)
[ Learn Skill Revenue Share ]      Secondary CTA (channel 3)
[ View Node Dashboard ]            Tertiary CTA (Runtime Truth)
```

---

### 3.4 三層生態互動敘事 (修正版, 給設計師的視覺指引)

Framer 實作時, 三張卡片**並排展示**, 但在卡片下方加一條**動態互動敘事帶**, 體現完整 Credits 流動:

**中文敘事 — 案例: IRS 信件 + Skill 訂閱閉環**:
```
👤 Client (Free): "我收到 IRS 的 CP2000 信件, 看不懂"
       ↓ AI 拆解 → 風險高 → 推薦 Plus 升級
👤 Client (Plus $19.99) → 看到 Provider 列表 → 選會計師 Jane
       ↓ AI 自動整理稅務資料 → 直送 Jane
👔 Provider Pro ($39.99): Jane 收到完整資料包 → 5 分鐘審核
       ↓ Jane 用 AiKa Box ($99/月) → 本地 OCR + 填表
⚡ AiKa Box (Worker): 跑「IRS 信件分析 Skill」($2.99/月訂閱)
       ↓ 任務完成 → Credits 結算
💰 結算分配 (假設這次任務消耗 8 Credits = $0.08):
   Client 付: $19.99 (Plus 月費)
   Provider 收: 平台分潤 $X / Worker 分潤 $Y
   Worker (Skill 開發者) 收: $2.99 訂閱 × 50% = $1.495
   AiKa Box (執行 Worker) 收: 任務執行 Credits
   平台收: Plus + Pro + Skill 50% + Runtime 成本回收
```

**English narrative — Case: IRS Letter + Skill Subscription Loop**:
```
👤 Client (Free): "I got an IRS CP2000 notice. Don't understand it."
       ↓ AI decomposition → high risk → Plus upgrade prompt
👤 Client (Plus $19.99) → sees Provider list → picks CPA Jane
       ↓ AI auto-prep tax docs → delivered to Jane
👔 Provider Pro ($39.99): Jane receives full data package → 5-min review
       ↓ Jane uses AiKa Box ($99/mo) → local OCR + form-fill
⚡ AiKa Box (Worker): runs "IRS Letter Analysis Skill" ($2.99/mo subscription)
       ↓ Task completed → Credits settlement
💰 Settlement (assume task consumes 8 Credits = $0.08):
   Client pays: $19.99 (Plus subscription)
   Provider earns: platform share $X / Worker share $Y
   Worker (Skill developer) earns: $2.99 × 50% = $1.495
   AiKa Box (execution Worker) earns: task execution Credits
   Platform earns: Plus + Pro + 50% of Skill + Runtime cost recovery
```

**視覺風格** (對齊 Dashboard 黃金版 V4.0.5.4-UI 的 Cyber-Noir 風格):
- Glassmorphism Card 半透明黑底, 紫色 accent
- 三張卡片之間有**流動光線連線** (electric-blue 呼吸燈, 動畫)
- 底部敘事帶**順序高亮** (每秒推進一格, 形成完整閉環)
- Credits 結算數字**滾動動畫** ($0.08 / $1.495 等真實數字)
- 鼠標 hover 在「Plus / Pro / AiKa Box」標籤時, 對應 CTA 強光提示

---


---

## 3.4 Three-Tier Boundary Doctrine（三端產品邊界鐵律）

> **同步補充**：本 Section 為三端邊界在 marketing matrix 中的鏡像聲明
> **完整版規範**：見 `docs/AGENTS.md` Three-Tier Product Boundary Doctrine（九節完整）
> **商業模式對齊**：見 `docs/business/GOAA_BUSINESS_MODEL_V1.md` 十二章

### 3.4.1 三端邊界（一句話 / One-Sentence Doctrine）

**中文**：
> Worker 負責生產能力，Provider 負責交付服務，Client 負責提出需求與查看結果。

**English**：
> Worker produces capability. Provider delivers service. Client requests outcome.

此句為 GOAA.AI 三端邊界的最終定義，所有 marketing 文案、UI 設計、產品描述必須對齊。

---

### 3.4.2 三端邊界表（中英雙語）

| 端 / Tier | 中文定位 | English Definition | Skill 範圍 |
|:---|:---|:---|:---|
| **Worker** | 內部生產線，成熟後開放給開發者 | Internal production line; opens to developers when mature | Worker / Developer Skill（後期）|
| **Provider** | 接單 + 跟單 + 調用專業 Skill + 審核交付，**不開發 Skill** | Order intake + follow-up + professional Skill invocation + audit & deliver. **Does not develop Skills.** | Provider Skill（專業）|
| **Client** | 提需求 + 看進度 + 與 Provider 互動 + 使用生活化 Skill | Request + track + interact with Provider + use lifestyle Skills | Client Skill（生活化）|

**三端通過 GOAA Runtime OS 連接，但界面、權限、語言、功能必須完全分層。**

**Connected by GOAA Runtime OS — but UI, permission, language, and feature scope must be fully layered.**

---

### 3.4.3 三端嚴禁混淆原則（Hard Boundary Rules）

```
❌ 普通 Client 不需要管理 Worker
❌ Provider 不需要開發 Skill
❌ Worker 平台當前階段不對外承諾開發者收益
❌ 三個平台不混在一個複雜後台裡
```

```
❌ Clients never manage Workers.
❌ Providers never develop Skills.
❌ Worker platform makes no developer-revenue promises in the current phase.
❌ The three tiers must never collapse into one back office.
```

---

### 3.4.4 官網主推順序（Current Commercial Phase）

```
1. Provider AI 工作台                    ← 主推（現金流，Provider Pro $39.99/月）
2. AiKa Box / 本地 Worker Runtime        ← 配套硬體（$1299）
3. Client 訂單進度與互動                  ← 需求方入口
4. Skill Marketplace Preview              ← 未來價值
5. Worker Developer Platform (Future)    ← 不過早承諾
```

---


## 4. AiKa Box Hardware Section

### 4.0 戰略定位 (核心宣言)

> **AiKa Box 不是普通電腦, 不是聊天機器人, 不是單純模型盒子。**
> **它是放在你家、辦公室、服務網點裡的實體 AI 邊緣工作站。**
> **通電、連網, 它就開始幫你幹活。**

這一段 Hero 文案直接寫在 Section 4 第一屏, 視覺上佔據整頁 60% 高度, 配 AiKa Box 渲染圖。

---

### 4.1 為什麼需要獨立 Section

AiKa Box 在 V2.0 文檔有**雙重身份**:

| 身份 | 出現位置 | 角色 |
|---|---|---|
| **Provider 商業階梯 Tier 3** | Section 3.2 | Provider 升級購買的硬件 ($999 / $99) |
| **Worker Network 節點類型** | Section 3.3 | AKB-xxx 三通道全開的 Worker 節點 |
| **獨立硬件產品** | Section 4 ← 本節 | 直接面向 Provider 與商業用戶的旗艦 SKU |

Section 4 是 AiKa Box 的**正面戰場展示**, 不只是 Provider Tier 3 的補充, 而是**獨立硬件產品線**, 對標 Mac mini / Geekom / Intel NUC 等迷你工作站, 但定位為**「AI 自動幹活的盒子」**。

---

### 4.2 中文版完整文案

#### Hero 段 (主視覺 + 主標題)

**主視覺**: AiKa Box 實體渲染圖 (placeholder, 等實機照片)
- 視覺效果: **electric-blue breathing light** (寶藍色呼吸燈, 沿盒子邊緣 `animate-pulse`)
- 旁邊浮動 task list (puls 動畫): "本地 OCR 解析中..." / "TurboTax 自動填表中..." / "瀏覽器接管自動化..."
- 背景: Cyber-Noir 黑色 + 微星點 + 漸層紫光

**主標題 (兩行)**:
```
AiKa Box
本地 AI Worker Appliance — 把 AI 真正部署到你的辦公室
```

**副標題**:
```
這不是又一台迷你電腦。
這是一台會自己工作的盒子, 為 Provider 與商業用戶設計。
通電、連網, 它就開始幹活。
```

#### 8 大核心能力 (對齊 geekom_comparison HTML 真實素材)

| 能力 | 真實描述 |
|---|---|
| **本地 .exe 自動化** | 直接控制 TurboTax / TaxAct / Excel 等報稅辦公軟件, 無需上傳文件 |
| **局域網文件直讀寫** | 訪問辦公室所有電腦的共享文件夾, 即時處理客戶文件 |
| **網頁自動化無反爬** | 本地 IP 訪問政府網站、銀行系統, 成功率 97% (vs 純雲端 61%) |
| **離線 AI 推理** | 本地運行 AI 模型, 數據不離開辦公室, 合規安全 |
| **閒置算力出售** | 非工作時間自動接入 Worker Network, 每月額外收入 $50-150 |
| **視頻本地剪輯發布** | 直接訪問本地視頻素材, 處理速度快 10 倍, 零上傳等待 |
| **Docker / Git 全套** | 完整開發環境, 支援 Browser Automation / OCR / docx/pdf/xlsx |
| **GOAA Runtime OS** | Worker V5.0 生產線就跑在 AiKa Box 上 (戰略憲法 Ch. 11) |

#### 智能檢測機制 (來自 geekom_comparison HTML)

```
登入 portal.goaa.ai 時, 系統自動判斷:

  本地盒子在線 → 啟用全部技能 (97% 可用率)
  ⚪ 無本地盒子 → 雲端模式 (61% 可用率)
```

這是 GOAA Runtime OS 的**雲端決策 + 本地執行**架構真實落地 (戰略憲法第 11 章, 規範 #39)。

#### 真實對比 (來自 geekom_comparison HTML 數據)

| 指標 | AiKa Box 本地 | AiKa Cloud 純雲端 |
|---|---|---|
| 技能可用率 | **97%** | 61% |
| Credits 消耗 | **節省 60%** | 基準 |
| 回本月數 | **6-12 個月** | N/A |
| 反爬通過率 | **97% (本地 IP)** | 61% (雲端 IP 被識別) |
| 數據合規 | ✅ 不離開辦公室 | ⚠️ 文件上傳雲端 |

#### 真實工作流範例 (自動報稅, 來自 geekom_comparison HTML)

**有 AiKa Box (全自動)**:
```
1. 客戶文件已在辦公室電腦共享文件夾
2. AiKa Box 直接讀取文件, 無需上傳
3. 自動打開 TurboTax, AI 填入所有數據
4. 自動提交, 發送確認郵件給客戶

✅ 全程 3 分鐘, 消耗 16 Credits ($0.16)
```

**純雲端 (半手動)**:
```
1. 手動掃描客戶文件並上傳到雲端
2. AI 分析文件 (等待上傳, 消耗存儲 Credits)
3. AI 生成報稅建議, 但無法直接操作軟件
4. 手動打開 TurboTax, 參照建議填入數據

⚠️ 全程 25 分鐘, 消耗 80 Credits ($0.80)
```

**結論**: 同樣一單報稅, AiKa Box 快 8 倍 + 省 80% Credits。

#### 回本計算 (基於 RTX 4060 + 100 任務/月)

| 項目 | 金額 |
|---|---|
| 每月 Credits 節省 (vs 純雲端) | **$45** |
| 閒置算力市場收入 | **$80** |
| 扣除電費後淨收益 | **$125 / 月** |
| 一次性硬件回本 ($999 ÷ $125) | **~8 個月** |
| 月付模式回本 (vs 雲端費用) | **立刻 (從第 1 個月開始現金流為正)** |

#### 兩種購買選項

```
┌────────────────────────────────────────────┐
│ 一次性硬件                                  │
│ $999 (擁有所有權)                          │
│                                            │
│ ✓ 長期最划算                                │
│ ✓ 8 個月回本                                │
│ ✓ 設備是你的, 隨時可斷網獨立運作            │
│ ✓ 閒置算力收入全歸你                        │
├────────────────────────────────────────────┤
│ 月付方案                                    │
│ $99 / 月                                   │
│                                            │
│ ✓ 低門檻試水, 隨時退訂                      │
│ ✓ 第 1 個月即現金流為正                     │
│ ✓ 硬件出問題平台負責更換                    │
│ ✓ 適合短期項目 / 季節性業務                 │
└────────────────────────────────────────────┘
```

#### 中文 CTA

```
[ 立即購買 AiKa Box → ]            主 CTA (一次性)
[ 月付方案試 30 天 ]               次 CTA (月付)
[ 查看真實對比數據 ]               三 CTA (數據驅動)
```

---

### 4.3 English version copy

#### Hero (visual + headline)

**Main visual**: AiKa Box render placeholder
- Visual: electric-blue breathing light along the chassis edge (`animate-pulse`)
- Floating task list (pulse animation): "Local OCR in progress..." / "TurboTax auto-filling..." / "Browser takeover automation..."
- Background: Cyber-Noir black + starfield + purple gradient

**Headline (two lines)**:
```
AiKa Box
Edge AI Worker Appliance — Deploy AI Physically Into Your Office
```

**Subheadline**:
```
Not another mini PC.
A box that works on its own — engineered for Providers and business users.
Power it on. Connect it. Let it work.
```

#### Eight core capabilities

| Capability | Description |
|---|---|
| **Local .exe Automation** | Direct control of TurboTax / TaxAct / Excel — no file upload needed |
| **LAN File Direct Access** | Reads shared folders across the office, processes client docs in real time |
| **Anti-Bot Web Automation** | Local IP accesses gov / bank sites at 97% success (vs 61% pure cloud) |
| **Offline AI Inference** | Local model execution. Data never leaves your office. Compliance-ready. |
| **Idle Compute Monetization** | Off-hours auto-join Worker Network. $50-150/mo extra income. |
| **Local Video Editing** | Direct local asset access. 10× faster than upload-based workflows. |
| **Docker / Git Full Stack** | Complete dev environment. Browser Automation / OCR / docx/pdf/xlsx ready. |
| **GOAA Runtime OS** | Worker V5.0 production line runs natively on AiKa Box (Charter Ch. 11). |

#### Smart detection mechanism

```
On portal.goaa.ai login, the system auto-detects:

  Local box online → all skills unlocked (97% availability)
  ⚪ No local box → cloud mode (61% availability)
```

This is GOAA Runtime OS's **"Decision in Cloud, Execution at Edge"** architecture in action 
(Charter Ch. 11 / Spec #39).

#### Real-world comparison

| Metric | AiKa Box (Local) | AiKa Cloud (Pure Cloud) |
|---|---|---|
| Skill availability | **97%** | 61% |
| Credits consumption | **60% savings** | baseline |
| Payback period | **6-12 months** | N/A |
| Anti-bot success rate | **97% (local IP)** | 61% (cloud IP detected) |
| Data compliance | ✅ Never leaves office | ⚠️ Cloud upload required |

#### Real workflow example (auto tax filing)

**With AiKa Box (fully automated)**:
```
1. Client docs already in office LAN shared folder
2. AiKa Box reads files directly — no upload
3. Auto-opens TurboTax, AI fills in all data
4. Auto-submits, sends confirmation email to client

✅ Total: 3 minutes, 16 Credits ($0.16)
```

**Pure cloud (semi-manual)**:
```
1. Manually scan client docs, upload to cloud
2. AI analyzes (waits for upload, consumes storage Credits)
3. AI suggests filing approach but cannot operate software
4. Manually open TurboTax, transcribe based on AI suggestions

⚠️ Total: 25 minutes, 80 Credits ($0.80)
```

**Conclusion**: Same tax filing — AiKa Box is 8× faster and saves 80% Credits.

#### ROI breakdown (RTX 4060 + 100 tasks/month)

| Item | Amount |
|---|---|
| Monthly Credits savings (vs cloud) | **$45** |
| Idle compute market revenue | **$80** |
| Net of electricity | **$125 / month** |
| One-time hardware payback ($999 ÷ $125) | **~8 months** |
| Monthly plan payback (vs cloud spend) | **Immediate (cash-flow positive from month 1)** |

#### Two purchase options

```
┌────────────────────────────────────────────┐
│ One-Time Hardware                           │
│ $999 (Full ownership)                       │
│                                            │
│ ✓ Best long-term value                      │
│ ✓ 8-month payback                           │
│ ✓ It's yours — works offline indefinitely  │
│ ✓ All idle compute income is yours          │
├────────────────────────────────────────────┤
│ Monthly Plan                                │
│ $99 / month                                 │
│                                            │
│ ✓ Low-commitment trial, cancel anytime      │
│ ✓ Cash-flow positive from month 1           │
│ ✓ Hardware replacement covered              │
│ ✓ Best for short-term / seasonal work       │
└────────────────────────────────────────────┘
```

#### English CTA

```
[ Buy AiKa Box → ]                 Primary CTA (one-time)
[ Try Monthly for 30 Days ]        Secondary CTA (monthly)
[ See Real Comparison Data ]       Tertiary CTA (data-driven)
```

---

### 4.4 視覺實作指引 (給 Framer 設計師)

#### Section 4 排版骨架

```
┌─────────────────────────────────────────────────────┐
│ [Hero: AiKa Box 主視覺 + 主副標題]                   │
│ (60% 高度, 中央展示, electric-blue breathing light)  │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│ [智能檢測機制 - 動態狀態指示器]                       │
│ (本地盒子 ON / 雲端 OFF, 真實 toggle 動畫)          │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│ [8 大核心能力 - 4×2 Grid Glassmorphism Cards]        │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│ [真實對比表 - AiKa Box vs Cloud, 大字數據強調]       │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│ [真實工作流範例 - 兩個 Step-by-Step 流程並排對比]    │
│ (3 min / 16 Credits  vs  25 min / 80 Credits)        │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│ [回本計算表 - 大字 $125/mo · 8 個月回本]             │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│ [兩種購買選項 - 並排卡片]                            │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│ [三 CTA 並排]                                        │
└─────────────────────────────────────────────────────┘
```

#### 視覺風格規則

- 全部對齊 Dashboard 黃金版 V4.0.5.4-UI 的 Cyber-Noir 黑色基調
- 主色: `#0a0a0a` (黑底) + `#7c3aed` (紫色 accent) + electric-blue `#60a5fa` (呼吸燈)
- 字體: DM Serif Display (主標) + DM Sans (內文) + DM Mono / JetBrains Mono (數據)
- 數據強調用 mono 字體 + 大字號 (28-48px), 對比柔色背景

#### ⚠️ Hardware Spec 隔離條款 (規範 SUPREME 1.4 + 規範 #36)

**禁止寫入文案的內容** (Hardware Spec 未定案):
- ❌ 「搭載 i5-12450H / 16GB DDR4 / 512GB NVMe」
- ❌ 「RTX 4060 內置」(RTX 4060 是 ROI 範例假設, 不是 AiKa Box 標配)
- ❌ 「2.5GbE 雙網口」/ 「Wi-Fi 6E」等任何具體型號
- ❌ 「散熱噪音 < 30dB」/ 「TDP 65W」等性能保證

**允許寫入的內容**:
- ✅ 「邊緣 AI 工作站」(Edge AI Workstation)
- ✅ 「本地推理 + Browser Automation + Docker」(能力描述)
- ✅ 抽象 metaphor (electric-blue breathing light 等)
- ✅ ROI 範例 (基於 RTX 4060 假設) — 必須註明「基於假設, 實際依機型而異」

實際硬件 spec 等師兄拍板出貨時補充, Framer V2.0 改版時**保留 placeholder 不寫死**。

---

## 5. Skill Marketplace / Asset Long Corridor

### 5.0 戰略定位

> **這是 GOAA.AI 長期最重要的商業層。**
> **未來真正值錢的不是聊天, 而是「可執行技能」。**
> (戰略憲法第 8 章原文)

Skill Marketplace 是 GOAA 從**訂閱費經濟** (Plus + Pro + AiKa Box) 進化到**資產經濟** (Skill 訂閱分潤) 的關鍵躍遷。

---

### 5.1 中文版完整文案

#### Section 5 Hero 段

**主標題**:
```
Skill Marketplace
能力即資產 — 訂閱、啟停、按需調用、Credits 結算
```

**副標題**:
```
每一個高頻任務、專業流程、文檔處理、生活管理、風險控制與資產配置方案,
都可以沉澱為可複用、可銷售、可訂閱、可分潤、可升級、可回滾、可持續產生收益的 Skill。
```

#### 6 張 Skill Card 展示 (資產長廊)

##### Skill Card 1: 家庭信件自動化管理

```
🏠 Household Mail Auto-Management
適用角色: Client
狀態: Beta (V4.3 開發中)

中文價值描述:
你的 IRS / DMV / 銀行 / 保險信件全部 AI 自動 OCR + 風險分類 + 提醒。
每月一個摘要, 重要的不漏, 廢紙不打擾。

English value:
All your IRS / DMV / bank / insurance mail auto-OCR'd, risk-tagged, alerted.
Monthly digest — never miss what matters, never get spammed.

訂閱: $2.99 / 月  ·  試用 7 天
分潤: 50/50 (平台 / Worker)
Toggle: 一鍵啟用 / 隨時停用
```

##### Skill Card 2: IRS Letter OCR & Risk Alert

```
📧 IRS Letter OCR & Risk Triage
適用角色: Client + Provider (兩端通用)
狀態: Internal (戰略憲法 4.1 場景 1 真實案例)

中文價值描述:
專門針對 IRS 寄來的 CP2000 / CP12 / Notice / Audit Letter 等複雜信件,
本地 OCR 解析 → 風險等級 (高/中/低) → 截止日期 → 回應草稿選項。

English value:
Specifically tuned for CP2000 / CP12 / Notice / Audit letters from the IRS.
Local OCR parsing → risk tier → deadline → response draft options.

訂閱:
  Client: $4.99 / 月
  Provider Pro 用戶: 包含在 $39.99/月 (免費啟用)
分潤: 50/50 (平台 / Worker)
Toggle: 一鍵啟用 / 隨時停用
```

##### Skill Card 3: AI 營銷視頻自動生成

```
🎬 AI Marketing Video Auto-Generation
適用角色: Provider (Real Estate / Insurance / 任何需要視頻營銷的)
狀態: Coming Soon (V4.3-V4.5)

中文價值描述:
給一份房產資訊或保險方案, AiKa Box 本地自動生成 30 秒短視頻,
含旁白 / 字幕 / 背景音樂, 可直接發 Instagram / Tiktok / 微信。

English value:
Input property listing or insurance proposal. AiKa Box locally generates 30-sec videos
with voiceover, captions, background music — ready for Instagram / TikTok / WeChat.

訂閱: $9.99 / 月 (Provider 端 Professional Skill, 戰略憲法 8.2 範例)
分潤: 50/50 (平台 / Worker)
真實收益範例 (戰略憲法 8.3):
  - 300 訂閱 × $9.99 = $2,997 / 月
  - 平台收 $1,498.50, Worker 收 $1,498.50
  - Runtime 成本 $520, Worker 淨利 ~$2,477 / 月
Toggle: 一鍵啟用 / 隨時停用
```

##### Skill Card 4: Mortgage Stress Test

```
🏦 Mortgage Stress Test Skill
適用角色: Client + Provider (兩端通用)
狀態: Beta (戰略憲法 4.1 場景 2)

中文價值描述:
輸入家庭收入 / 現有債務 / 儲蓄 / 信用分數,
模擬多種利率 (30Y 固定 / 7/1 ARM / Jumbo) + DTI + 失業 3 月現金流 stress test.

English value:
Input income / debt / savings / credit score.
Simulates multiple rate scenarios (30Y fixed / 7/1 ARM / Jumbo) + DTI + 3-month job-loss stress test.

訂閱:
  Client: $5.99 / 月 (按需訂閱, 房貸決策期使用)
  Provider Pro 用戶: 包含在 $39.99/月
分潤: 50/50 (平台 / Worker)
Toggle: 一鍵啟用 / 隨時停用
```

##### Skill Card 5: IUL / Term Insurance Planning

```
🛡️ IUL / Term Insurance Planning Skill
適用角色: Provider (持牌保險經紀)
狀態: Coming Soon (V4.4)

中文價值描述:
跨領域拆解 45 歲家庭需求 — 教育金 (529) + 退休 (401k/IRA/Roth) + 保險 (IUL/Term).
AI 跑多情境模擬, 投影 20 年現金流, 比較 IUL vs Term 稅務 + 成本 + 保額.

English value:
Cross-domain decomposition for mid-life households — education (529) + retirement (401k/IRA/Roth) + insurance.
AI multi-scenario modeling, 20-year cash-flow projection, IUL vs Term tax/cost/coverage comparison.

訂閱: $19.99 / 月 (Provider 高溢價 Skill)
分潤: 50/50 (平台 / Worker)
Toggle: 一鍵啟用 / 隨時停用

⚠️ 戰略憲法邊界: 本 Skill 提供分析框架, 不構成保險或投資建議.
        所有實際投保決策必須由持牌保險經紀人 (Provider) 最終確認.
```

##### Skill Card 6: Provider Lead Follow-up

```
📞 Provider Lead Follow-up Automation
適用角色: Provider (CRM 自動化)
狀態: Internal (Provider Pro 配套, V4.4 上線)

中文價值描述:
Client 進線 → AI 自動發 welcome / 排程 follow-up / 文件到期提醒 /
客戶生日問候 / 政策變更通知 — Provider 只需專注真正需要決策的對話.

English value:
Client inbound → AI sends welcome / schedules follow-ups / docs expiry alerts /
client birthday greetings / policy change notifications. Provider focuses only on real decision moments.

訂閱: 包含在 Provider Pro $39.99/月 (Pro 用戶免費啟用)
分潤: Pro 訂閱費已含, 不額外計費
Toggle: 一鍵啟用 / 隨時停用
```

---

### 5.2 Skill Marketplace 統一卡片字段 (戰略憲法 9.2 + DDL 對齊)

每張 Skill Card 在 Framer 上的展示字段, 對應 `skill_marketplace` 表 schema:

```
┌────────────────────────────────────────────────┐
│ [Skill Icon]  [Skill Name]                      │
│              [English Name]                     │
│                                                 │
│ [Category]  [Target User]  [Status]             │
│                                                 │
│ 中文價值描述 (one-liner)                        │
│ English value (one-liner)                       │
│                                                 │
│ ────────────────────────────────                │
│ 訂閱: $X / 月  ·  試用 N 天                     │
│ 分潤: 50/50 (平台 / Worker)                     │
│ ────────────────────────────────                │
│                                                 │
│ [Toggle: 啟用 / 停用]                           │
│ [評分: ⭐⭐⭐⭐⭐ 4.8]                          │
│ [訂閱數: 1,000+]                                │
│                                                 │
│ [Subscribe →]  [View Details]                   │
└────────────────────────────────────────────────┘
```

#### 對應 DDL 欄位 (skill_marketplace 表, FUTURE_DDL_SKILL_MARKETPLACE.md)

| Framer 顯示 | DDL 欄位 |
|---|---|
| Skill Name | `name VARCHAR(100)` |
| Category | `category VARCHAR(50)` (Client/Provider/Office/Real Estate/Insurance) |
| Target User | `target_user VARCHAR(30)` (Client/Provider/Both) |
| Status | `status VARCHAR(20)` (draft/testing/review/published/paused/archived) |
| Subscription Price | `price_monthly DECIMAL(10,2)` |
| Trial | `trial_days INTEGER` |
| Platform Share | `platform_share DECIMAL(5,2) DEFAULT 50.00` |
| Worker Share | `worker_share DECIMAL(5,2) DEFAULT 50.00` |
| Rating | `rating FLOAT` |
| Subscriber Count | `active_subscribers INTEGER` |

---

### 5.3 SaaS 商業直覺 (戰略憲法 9.5 一鍵啟停)

Skill Marketplace 必須傳遞**滑動訂閱、即時啟停、按需調用、Credits 結算**的商業直覺:

#### 中文使用體驗
- **發現 Skill** → 看評分 / 試用 / 詳情
- **訂閱** → 滑動藍色 toggle, 立即生效, 1 秒可用
- **使用** → AI 自動調用, 後台跑 Worker, Credits 即時結算
- **停用** → 滑動關閉, 立即停止, 不再扣費
- **重新啟用** → 隨時 reactivate, 數據自動恢復

#### English experience
- **Discover** → Browse ratings / trial / details
- **Subscribe** → Slide blue toggle, instant activation, usable in 1 sec
- **Use** → AI auto-invokes, Worker runs in background, Credits settled real-time
- **Pause** → Slide off, immediate suspension, no further charges
- **Reactivate** → Anytime, data auto-restored

---

### 5.4 8 階段完整生命週期 (戰略憲法 9.3 對應)

Section 5 底部加一條**敘事帶**, 展示 Skill 從生產到收益的完整閉環:

```
1️⃣ 需求來源          (Client 高頻 / Provider 痛點 / 用戶反饋)
       ↓
2️⃣ 生成開發任務      (skill_design_task / workflow_build_task)
       ↓
3️⃣ Worker 開發 Skill  (邏輯 / Prompt / Workflow / UI / Billing)
       ↓
4️⃣ 測試與驗收        (功能 / 安全 / 成本 / 失敗回滾)
       ↓
5️⃣ 封裝與版本化      (Package + Version + Runtime Config + UI)
       ↓
6️⃣ 上傳到技能市場    (Client / Provider / AiKa Box 三端分發)
       ↓
7️⃣ 訂閱與計費        (月費 + Runtime 調用 + Worker 收益累計)
       ↓
8️⃣ 反饋與升級        (評分 / Bug / 新需求 → 自動生成 6 種 Worker Task)
       ↓
       回到 Worker Network — 形成閉環
```

**English 8-stage lifecycle**:
```
1️⃣ Demand sourcing    (Client high-freq / Provider pain / user feedback)
       ↓
2️⃣ Dev task generation (skill_design_task / workflow_build_task)
       ↓
3️⃣ Worker builds Skill (logic / prompts / workflow / UI / billing)
       ↓
4️⃣ Testing & QA       (function / security / cost / rollback)
       ↓
5️⃣ Packaging & versioning (Package + Version + Runtime Config + UI)
       ↓
6️⃣ Marketplace upload (Client / Provider / AiKa Box distribution)
       ↓
7️⃣ Subscription & billing (monthly + Runtime invocation + Worker accrual)
       ↓
8️⃣ Feedback & upgrade (ratings / bugs / requests → 6 Worker Task types)
       ↓
       Back to Worker Network — closed loop
```

---

### 5.5 視覺實作指引 (給 Framer 設計師)

#### Section 5 排版骨架

```
┌─────────────────────────────────────────────────────┐
│ [Hero: Skill Marketplace 主標題 + 副標題]            │
│ (一行 + 兩行副標, 中央展示)                         │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│ [6 張 Skill Card - 資產長廊 Horizontal Scroll]       │
│ (3 列 × 2 行 桌面 / 1 列 × 6 行 手機)                │
│ 每張卡片 Glassmorphism 半透明 + Toggle 動畫          │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│ [SaaS 體驗演示 - 訂閱滑動 / 啟停動畫]                │
│ (大圖展示 toggle 過程)                               │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│ [8 階段生命週期敘事帶 - 動態高亮推進]                │
│ (每秒推進一格, 從 1️⃣ 到 8️⃣ 形成閉環)               │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│ [CTA: Marketplace 主入口]                            │
└─────────────────────────────────────────────────────┘
```

#### 滑動藍色 Toggle 設計 (戰略憲法 9.5)

```css
/* Glassmorphism toggle */
.skill-toggle {
  background: linear-gradient(90deg, #1e1e1e, #0a0a0a);
  border: 1px solid #2a2a2a;
}

.skill-toggle.active {
  background: linear-gradient(90deg, #60a5fa, #7c3aed); /* electric-blue → purple */
  box-shadow: 0 0 12px rgba(96, 165, 250, 0.5);
}

.toggle-thumb {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
```

#### CTA

```
[ 探索 Skill Marketplace → ]      主 CTA
[ 了解 Worker 如何開發 Skill ]    次 CTA (連 Section 3.3 通道 3)
```

---

### 5.6 ⚠️ Skill Marketplace 邊界聲明 (規範 SUPREME 1.4 + #28)

#### 不允許出現的措辭

| ❌ 禁止 | 原因 |
|---|---|
| 「Marketplace 已上線」 | V4.3 才開始建設, 當前狀態是規劃 (Roadmap Phase 5) |
| 「保證 Worker 月入 $X」 | 訂閱數依市場接受度, 範例非保證 |
| 「6 張 Skill 全部可購買」 | Skill Cards 1/3/5 是 V4.3-V4.5 Coming Soon, 不是當前可購 |
| 「50/50 分潤永不變」 | 戰略憲法默認比例, 但可能未來調整 |
| 「Skill 不會失敗」 | 規範 #28 + 戰略憲法 9.4 反饋類型明確包含 bug / wrong_output |

#### 允許的措辭

| ✅ 鼓勵 | 原因 |
|---|---|
| 「V4.3-V4.5 Skill Marketplace 上線計劃」 | Runtime Truth, 真實 Roadmap |
| 「真實收益範例 (基於假設訂閱數)」 | 數字真實, 邊界明確 |
| 「50/50 分潤是當前默認」 | 不過度承諾 |
| 「Skill 開發 8 階段含測試 + Rollback」 | 規範 #28 完整生命週期 |

---

## 5.2 Skill Marketplace Layering（Skill Marketplace 分層）

Skill Marketplace **必須按使用者三層分流**，不可混合展示。

### 5.2.1 三層分流表

| 層 / Layer | 對象 / Audience | 範例 / Examples | 上架階段 |
|:---|:---|:---|:---:|
| **Client Skill** | 普通用戶 / Everyday users | 家庭信件管理、IRS 信件提醒、帳單整理、房貸壓力測試、家庭文件分類、生活待辦總結 | Phase 5+ |
| **Provider Skill** | 專業服務者 / Professionals | Insurance Needs Analysis、IUL/Term 草稿、客戶 intake、AI follow-up、IRS Letter Triage、表格草稿 | Phase 3-4 |
| **Worker / Developer Skill** | 開發者 / Developers（後期）| 新 Skill 開發、Runtime 插件、Browser automation、OCR pipeline、行業 workflow | 律師意見書後 |

### 5.2.2 三層原則對照

| 層 | 中文原則 | English Principle |
|:---|:---|:---|
| Client Skill | 簡單 / 生活化 / 一鍵啟用 / 不涉及專業最終判斷 | Simple / lifestyle / one-tap activate / no professional final judgement |
| Provider Skill | 專業 / 可審計 / Provider 最終審核 / 服務訂單 / 提升交付效率 | Professional / auditable / human-in-the-loop / order-bound / efficiency-driven |
| Worker-Dev Skill | 開發者使用 / 權限治理 / 版本管理 / 測試審核 / 後期開放 | Developer-grade / governed / versioned / tested / phased rollout |

### 5.2.3 當前階段嚴禁事項

**Phase 1 ~ Phase 4 嚴禁**：Worker / Developer Skill 暴露給 Client 或普通 Provider。

**Through Phase 4: Worker / Developer Skills must not be visible to Clients or general Providers.**

---

## 5.3 Worker Developer Skill Roadmap（Worker 開發者 Skill 路線）

### 5.3.1 當前階段（Phase 1 ~ Phase 4）

Worker / Developer Skill **不對外開放**。

**Worker / Developer Skills are not publicly listed during Phase 1 through Phase 4.**

**當前用途**：GOAA 內部使用，由 5 個 AiKa 節點（aika-1/2 + do-cloud-1/2/3）並行開發專業 Skill，封裝後上架到 Provider Skill 層。

---

### 5.3.2 開放前置條件（Hard Prerequisites）

以下條件**全部達成**才可開放 Worker / Developer Skill 對外：

```
☐ Worker Runtime 成熟（沙箱 / Snapshot / Rollback）
☐ 任務審計（tool_invocations 完整鏈路 + Runtime Truth）
☐ Credits 結算機制（QS × Difficulty × Stability 公式穩定）
☐ 權限治理（Worker / Developer 分級）
☐ Skill 版本管理（語意化版號 + Changelog + 回滾）
☐ 律師意見書（SEC + FinCEN + 州 Money Transmitter）
☐ KYC / AML 流程
☐ Terms of Service 完整版
☐ 50+ 內部驗證成功的 Skill 庫
☐ 50/50 分潤經濟模型驗證可持續
```

**All ten conditions must be met before Worker / Developer Skills open to the public.**

---

### 5.3.3 商業承諾邊界（嚴禁）

當前 marketing 階段嚴禁以下文案：

- ❌ 「成為 GOAA Worker 開發者，月入 XXX」
- ❌ 「Skill 開發者收益分成 50/50」（前置條件未滿足前不對外宣傳）
- ❌ 「Worker Network 招募」針對個人開發者

**Marketing must not promise developer earnings before all ten prerequisites are met.**

---

### 5.3.4 未來開放時的承諾框架（僅參考，前置條件達成後啟用）

| 維度 | 框架 |
|:---|:---|
| 分潤模型 | 50/50（Platform / Worker-Developer）|
| 結算單位 | Credits（按 QS × Difficulty × Stability）|
| 准入機制 | KYC + 技術測試 + Skill 試點審核 |
| 版本治理 | 強制語意化版號 + 24h cooldown publish + Rollback |
| 違規處置 | Credits 清零 + 帳號凍結 + 法律追究 |

---

**Section 簽發**：2026-05-19 Tao 師兄
**規範同步**：`docs/AGENTS.md` Three-Tier Product Boundary Doctrine（完整版）
**商業同步**：`docs/business/GOAA_BUSINESS_MODEL_V1.md` 十二章

## 6. Trust / Privacy / Compliance Section

### 6.0 戰略定位

GOAA 處理用戶最敏感的場景: 稅務 / 保險 / 房貸 / 退休 / 法律 / 移民。

這些場景對應**三大信任維度**:

| 維度 | 用戶擔心什麼 | GOAA 答案 |
|---|---|---|
| **隱私** | 我的稅單會不會被洩露? | 本地優先 + AiKa Box 數據不離開辦公室 |
| **合規** | AI 會不會給我錯誤的法律建議? | 不替代持牌專業者, AI 只做結構化分析 |
| **可審計** | 出問題我能不能查? | 每個任務全鏈路 replay, 24h 觀察期 |

Section 6 必須在主頁 **Footer 之前**, 給用戶留下「**這家公司認真守規矩**」的最終印象。

---

### 6.1 中文版完整文案

#### Hero 段

**主標題**:
```
信任不靠承諾, 靠架構
Trust Built Into the Architecture
```

**副標題**:
```
GOAA Runtime OS 從第一行代碼就為隱私、合規、可審計而設計.
不是事後補救, 而是天生帶有的工程紀律.
```

#### 三大信任維度 (Glassmorphism Card Grid)

##### 信任維度 1: 隱私 (Privacy-First Architecture)

**Header**: `🔒 隱私不是賣點, 是底線`

```
本地優先架構 (Local-First):
✓ AiKa Box 部署在 Provider 辦公室或用戶家中
✓ OCR / 文件分析 / AI 推理全部在本地完成
✓ 敏感資料 (稅單 / 保單 / 文檔) 數據不離開你的盒子
✓ 雲端只負責任務調度與結算, 不存原始文件

戰略憲法第 11 章原文:
「雲端決策, 本地執行」(Decision in Cloud, Execution at Edge)
這是 GOAA Runtime OS 的最高架構原則, 不可違反.

對比競品:
- ChatGPT: 你上傳的稅單存在 OpenAI 雲端
- 其他雲 SaaS: 文件必須先上傳才能分析
- GOAA AiKa Box: 文件在你本機 OCR, 雲端只看任務元數據
```

##### 信任維度 2: 合規 (Compliance-Aware Workflows)

**Header**: `⚖️ 不替代專業者, 不越權承諾`

```
GOAA 三大合規邊界 (戰略憲法強制):

1. AI 不替代律師 / 會計師 / 保險經紀 / 投資顧問
   - AI 只做結構化分析與資料整理
   - 最終決策由持牌 Provider 負責

2. 涉及專業判斷的場景由持牌 Provider 承接
   - 稅務回應 → CPA / 稅務律師
   - 房貸申請 → 持牌貸款顧問
   - 保險方案 → 持牌保險經紀
   - 法律事務 → 律師

3. AI 輸出明確標示「分析建議」, 不是「專業意見」
   - 每個 AI 回應底部都有合規邊界聲明
   - 高風險場景自動觸發「請諮詢持牌專業者」提示

規範對齊:
- 戰略憲法第 9 章 (Skill Marketplace 邊界)
- 規範 #28 (Silent Failure 不准 — 必須誠實標示限制)
```

##### 信任維度 3: 可審計 (Auditable Task Logs)

**Header**: `📋 每個任務都可回放, 出問題能查`

```
Runtime Truth 完整審計鏈 (戰略憲法第 8 章):

每個任務記錄:
✓ task_id (UUID, 全鏈路追蹤)
✓ worker_id (誰執行)
✓ dispatch_plan_id (誰規劃)
✓ runtime_cost (跑了多少資源)
✓ api_cost (用了哪些 AI 模型 + 多少 token)
✓ revenue (Worker 賺了多少)
✓ profit (淨利潤)
✓ credits (結算憑證)
✓ duration (耗時)
✓ skill_id (調用了哪個 Skill)

爭議時可做什麼:
- 完整 replay: 從派發到結算重現整個過程
- Quality Score 評估: QS < 0.6 → 任務退回 redo, Worker 不獲 payout
- Security 強制歸零: 違規任務 → Credits 強制歸零 + 安全警報
- 24h 觀察期 (規範 #15): 任何 production 變更後 24 小時內可緊急回滾

Worker 升級審計 (戰略憲法 9.4 反饋閉環):
- 用戶反饋自動映射 8 種 Worker Task (patch / ux / optimization / feature / prompt_fix / cost / security / billing)
- 每個 patch 必須註明 rollback_from_version (DDL 字段)
- Skill 版本帶 artifact_hash + runtime_config_hash 防篡改
```

#### 免責聲明 (合規必須, 戰略憲法強制)

```
⚠️ 重要聲明:

GOAA 提供 AI 輔助分析與流程自動化, 不構成法律、稅務、投資、
保險或財務建議. 涉及專業判斷的場景, 應由持牌專業人士最終確認.

GOAA 不對因依賴 AI 分析結果而產生的任何損失承擔責任. 用戶應自行
判斷 AI 輸出的適用性, 並在重大決策前諮詢相應領域的持牌 Provider.

Credits 收益是任務完成的結算憑證, 不是金融投資回報. 實際每月
Credits 收益依任務量 / 設備性能 / 電費 / 區域算力價格而異.

AiKa Box 硬件規格、Skill Marketplace 訂閱價格、Provider Pro
月費為當前定價, 未來可能因運營成本或市場調整而變動.

最後更新: 2026-05-17
```

#### 中文 CTA

```
[ 了解 GOAA 隱私架構 → ]          主 CTA
[ 查看合規邊界全文 ]               次 CTA
[ 申請任務審計回放 ]               三 CTA (進階用戶)
```

---

### 6.2 English version copy

#### Hero

**Headline**:
```
Trust Built Into the Architecture
Not Promised, Engineered.
```

**Subheadline**:
```
GOAA Runtime OS is engineered for privacy, compliance, and auditability from the first line of code.
Not retrofitted — built in by design.
```

#### Three Trust Dimensions

##### Dimension 1: Privacy-First Architecture

**Header**: `🔒 Privacy Is the Floor, Not the Feature`

```
Local-first architecture:
✓ AiKa Box deployed in Provider's office or user's home
✓ OCR / document analysis / AI inference all run locally
✓ Sensitive data (tax forms / policies / documents) never leave your box
✓ Cloud handles only task dispatch and settlement — never raw files

Charter Ch. 11 mandate:
"Decision in Cloud, Execution at Edge."
GOAA Runtime OS's highest architectural principle. Inviolable.

Competitive contrast:
- ChatGPT: Your tax forms live on OpenAI's servers
- Other cloud SaaS: Files must upload before analysis
- GOAA AiKa Box: Files OCR'd on your machine — cloud sees only task metadata
```

##### Dimension 2: Compliance-Aware Workflows

**Header**: `⚖️ No Professional Replacement. No Overreach.`

```
Three GOAA compliance boundaries (Charter-enforced):

1. AI does NOT replace lawyers / CPAs / insurance brokers / investment advisors
   - AI performs structured analysis and data prep only
   - Final decisions rest with the licensed Provider

2. Professional-judgment scenarios route to licensed Providers
   - Tax responses → CPAs / tax attorneys
   - Mortgage applications → licensed loan officers
   - Insurance plans → licensed insurance brokers
   - Legal matters → attorneys

3. AI outputs explicitly labeled "analysis" — never "professional opinion"
   - Every AI response footer carries a compliance disclaimer
   - High-risk scenarios auto-trigger "consult a licensed provider" prompt

Spec alignment:
- Charter Ch. 9 (Skill Marketplace boundaries)
- Spec #28 (No Silent Failure — must honestly disclose limits)
```

##### Dimension 3: Auditable Task Logs

**Header**: `📋 Every Task Is Replayable. Disputes Are Investigable.`

```
Runtime Truth full audit chain (Charter Ch. 8):

Each task records:
✓ task_id (UUID, end-to-end tracking)
✓ worker_id (who executed)
✓ dispatch_plan_id (who planned)
✓ runtime_cost (resources consumed)
✓ api_cost (AI models + token spend)
✓ revenue (Worker earnings)
✓ profit (net)
✓ credits (settlement receipt)
✓ duration (elapsed time)
✓ skill_id (invoked Skill)

In dispute, you can:
- Full replay: reconstruct the task from dispatch to settlement
- Quality Score check: QS < 0.6 → task returned for redo, no Worker payout
- Security zero-out: violation → Credits forced to zero + security alert
- 24h cooldown (Spec #15): any production change can be rolled back within 24h

Skill upgrade audit (Charter 9.4 feedback loop):
- User feedback auto-maps to 8 Worker Task types
- Every patch records rollback_from_version (DDL field)
- Skill versions carry artifact_hash + runtime_config_hash for tamper-detection
```

#### Disclaimer (compliance-required)

```
⚠️ IMPORTANT NOTICE:

GOAA provides AI-assisted analysis and workflow automation. It does not provide legal,
tax, investment, insurance, or financial advice. Professional scenarios should be reviewed
by licensed providers.

GOAA bears no liability for losses arising from reliance on AI analysis output. Users should
independently evaluate the applicability of AI outputs and consult licensed Providers in the
relevant domain before any material decision.

Credits earnings are task-completion receipts, not investment returns. Actual monthly Credits
earnings vary by task volume, hardware performance, electricity costs, and regional compute
pricing.

AiKa Box hardware specifications, Skill Marketplace subscription prices, and Provider Pro
monthly fees are current pricing — subject to future adjustment based on operating costs or
market conditions.

Last updated: 2026-05-17
```

#### English CTA

```
[ Learn GOAA Privacy Architecture → ]   Primary CTA
[ View Full Compliance Boundaries ]     Secondary CTA
[ Request Task Audit Replay ]           Tertiary CTA (advanced users)
```

---

### 6.3 視覺實作指引 (給 Framer 設計師)

#### Section 6 排版骨架

```
┌─────────────────────────────────────────────────────┐
│ [Hero: 信任不靠承諾, 靠架構 + 副標]                  │
└─────────────────────────────────────────────────────┘
┌──────────────┬──────────────┬──────────────────────┐
│ 🔒 隱私       │ ⚖️ 合規      │ 📋 可審計            │
│ Privacy      │ Compliance   │ Audit                │
│              │              │                      │
│ Local-First  │ No Overreach │ Replayable           │
│              │              │                      │
│ [Glassmorph] │ [Glassmorph] │ [Glassmorph]         │
└──────────────┴──────────────┴──────────────────────┘
┌─────────────────────────────────────────────────────┐
│ [⚠️ 免責聲明全文 - 灰色小字, 但清晰可讀]              │
│ (背景半透明灰, 邊框細線分隔)                         │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│ [三 CTA 並排]                                        │
└─────────────────────────────────────────────────────┘
```

#### 視覺風格規則

- 三張信任卡片**並排**, 桌面 3 列, 平板 2 列, 手機 1 列堆疊
- 每張卡片配對應 emoji 大圖標 (🔒 / ⚖️ / 📋)
- Glassmorphism 半透明黑底 + 紫色細邊框
- 免責聲明區塊獨立分隔, 字體稍小 (12-13px) 但行距寬鬆 (1.6), 灰色不刺眼
- 切勿用紅色警告色, 用低調的灰白組合, 傳遞「**穩重而誠實**」氣質

---

### 6.4 ⚠️ Trust Section 邊界聲明 (規範 #28 + SUPREME 1.4)

#### 不允許的措辭

| ❌ 禁止 | 原因 |
|---|---|
| 「100% 隱私保證」 | 任何系統都有漏洞風險, 過度承諾傷信任 |
| 「永遠不會洩露」 | 規範 #28 不准 silent failure, 必須誠實邊界 |
| 「GOAA AI 比律師更準確」 | 合規紅線, 不可比較持牌專業者 |
| 「Worker 永遠誠實」 | Worker Quality Score < 0.6 機制就是承認失敗存在 |

#### 允許的措辭

| ✅ 鼓勵 | 原因 |
|---|---|
| 「本地優先架構, 數據不離開你的盒子」 | 真實架構描述 |
| 「不替代持牌 Provider」 | 規範 + 合規邊界明確 |
| 「每個任務可審計可回放」 | Runtime Truth 真實機制 |
| 「QS < 0.6 任務退回 redo」 | 質量機制誠實展示 |

---

## 7. Footer Matrix

### 7.0 戰略定位

Footer 是用戶離開前**最後一眼**, 必須:
1. 重申品牌核心宣言 (一句話定義)
2. 提供完整導航 (六大欄目)
3. 顯示真實聯絡資訊 (GEER IT INC 母公司)
4. 對齊 Cyber-Noir 黑色風格

師兄拍板: Footer slogan 改為 **"GOAA — AI Agent for your life"** ← 來自今天上午 Phase A 拍板。

---

### 7.1 中文版 Footer

#### 主結構

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  [GOAA Logo]                                                 │
│                                                              │
│  GOAA — AI Agent for your life                              │
│  GOAA Runtime OS · 讓 AI 真正下場幹活                       │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  Platform           Provider Pro      Worker Network         │
│  ─ 首頁              ─ Pro 訂閱        ─ 加入網絡            │
│  ─ 生態              ─ AiKa Box        ─ Skill 開發          │
│  ─ Skill Marketplace ─ Leads 撮合      ─ 算力市場            │
│  ─ Provider Pro      ─ CRM 工作流      ─ Credits 結算        │
│                                                              │
│  Skill Marketplace  Privacy           Contact                │
│  ─ 家庭信件管理      ─ 隱私架構        ─ help@goaa.ai        │
│  ─ IRS 信件分析      ─ 合規邊界        ─ EN | 中 toggle      │
│  ─ AI 視頻生成       ─ 任務審計        ─ Provider 申請       │
│  ─ 完整 Skill 列表   ─ 免責聲明        ─ Worker 申請        │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  GEER IT INC                                                 │
│  © 2026 GOAA. All rights reserved.                          │
│                                                              │
│  [LinkedIn] [X] [Instagram] [Facebook] [Threads]            │
│                                                              │
│  Powered by GOAA Runtime OS                                  │
└──────────────────────────────────────────────────────────────┘
```

#### Footer 核心欄目 (六大)

| 欄目 | 子項 |
|---|---|
| **Platform** | 首頁 / 生態 / Skill Marketplace / Provider Pro |
| **Provider Pro** | Pro 訂閱 / AiKa Box / Leads 撮合 / CRM 工作流 |
| **Worker Network** | 加入網絡 / Skill 開發 / 算力市場 / Credits 結算 |
| **Skill Marketplace** | 家庭信件管理 / IRS 信件分析 / AI 視頻生成 / 完整 Skill 列表 |
| **Privacy** | 隱私架構 / 合規邊界 / 任務審計 / 免責聲明 |
| **Contact** | help@goaa.ai / EN \| 中 toggle / Provider 申請 / Worker 申請 |

#### Contact 區塊 (Phase A 拍板「保留真實但隱藏」)

```
真實資料 (Framer 中保存, 但 production 暫時隱藏):
- Email: help@goaa.ai
- Phone: (858) 519-8064
- Address: 9663 Garvey Ave ste 127, South El Monte, CA 91733
- 創辦人: Tao Feng

當前 production 顯示策略 (Phase A 師兄拍板):
- 只顯示 help@goaa.ai (郵箱)
- 隱藏電話與地址 (避免 spam / 騷擾)
- V5.0 完整收 lead 機制後再開放
```

#### 品牌口號層次

```
主口號 (大字, 顯眼):
  GOAA — AI Agent for your life

副口號 (中字, 補充戰略定位):
  GOAA Runtime OS · 讓 AI 真正下場幹活

技術口號 (小字, Footer 最底):
  Powered by GOAA Runtime OS
```

---

### 7.2 English Footer

#### Main structure

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  [GOAA Logo]                                                 │
│                                                              │
│  GOAA — AI Agent for your life                              │
│  GOAA Runtime OS · Physical AI labor for real-world tasks   │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  Platform              Provider Pro       Worker Network     │
│  ─ Home                ─ Pro Subscription ─ Join Network     │
│  ─ Ecosystem           ─ AiKa Box         ─ Skill Dev        │
│  ─ Skill Marketplace   ─ Lead Matching    ─ Compute Market   │
│  ─ Provider Pro        ─ CRM Workflows    ─ Credits Settle   │
│                                                              │
│  Skill Marketplace     Privacy            Contact            │
│  ─ Household Mail Mgmt ─ Privacy Arch     ─ help@goaa.ai     │
│  ─ IRS Letter Triage   ─ Compliance       ─ EN | 中 toggle   │
│  ─ AI Video Gen        ─ Audit Logs       ─ Apply Provider   │
│  ─ Full Skill List     ─ Disclaimer       ─ Apply Worker     │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  GEER IT INC                                                 │
│  © 2026 GOAA. All rights reserved.                          │
│                                                              │
│  [LinkedIn] [X] [Instagram] [Facebook] [Threads]            │
│                                                              │
│  Powered by GOAA Runtime OS                                  │
└──────────────────────────────────────────────────────────────┘
```

#### Six column structure

| Column | Items |
|---|---|
| **Platform** | Home / Ecosystem / Skill Marketplace / Provider Pro |
| **Provider Pro** | Pro Subscription / AiKa Box / Lead Matching / CRM Workflows |
| **Worker Network** | Join Network / Skill Dev / Compute Market / Credits Settlement |
| **Skill Marketplace** | Household Mail Mgmt / IRS Letter Triage / AI Video Gen / Full Skill List |
| **Privacy** | Privacy Arch / Compliance / Audit Logs / Disclaimer |
| **Contact** | help@goaa.ai / EN \| 中 toggle / Apply Provider / Apply Worker |

#### Tagline hierarchy

```
Primary tagline (large, prominent):
  GOAA — AI Agent for your life

Secondary tagline (medium, strategic positioning):
  GOAA Runtime OS · Physical AI labor for real-world tasks

Technical tagline (small, bottom of footer):
  Powered by GOAA Runtime OS
```

---

### 7.3 視覺實作指引 (給 Framer 設計師)

#### Footer 排版骨架

```
┌─────────────────────────────────────────────────────┐
│ [Top Row: GOAA Logo + 主口號 (右側留白)]             │
│                                                     │
│ GOAA — AI Agent for your life                       │
│ GOAA Runtime OS · 讓 AI 真正下場幹活                │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│ [六大欄目 - 3×2 grid 桌面 / 1×6 stack 手機]          │
│ [每欄 1 個標題 + 4 個子項]                          │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│ [底部: 公司資訊 + 版權 + 社交 icons]                 │
│ GEER IT INC · © 2026 GOAA · [Social Icons]          │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│ [極小字: Powered by GOAA Runtime OS]                │
└─────────────────────────────────────────────────────┘
```

#### 風格規則

- **顏色**: Cyber-Noir 黑底 + 紫色 accent + 灰白文字
- **字體**: DM Serif Display (主口號) + DM Sans (欄目) + DM Mono (技術口號)
- **欄目間距**: 32px 桌面, 16px 手機
- **社交 icon**: 純白色, hover 變紫色
- **連結**: 默認灰白, hover 變紫色 + 底線淡入
- **Logo**: 32-40px 高, 黑底白 logo (對齊 Dashboard 黃金版)

#### EN | 中 Toggle 位置

```
Footer 右上角 (Contact 區塊內) 重複放一個 EN | 中 Toggle, 
與 Header 同步狀態 (用戶切過後 Footer 也跟著切換).

實作: localStorage 共享, 兩個 toggle 都監聽同一個 lang state.
```

---

### 7.4 ⚠️ Footer 邊界聲明 (規範 #28 + #36)

#### 不允許的內容

| ❌ 禁止 | 原因 |
|---|---|
| 偽造的 Slack / Discord / Telegram 群組 | 真實社群未建立, 不假裝有 |
| 「GOAA 全球辦公室」 (假地址) | 規範 #28 不准 silent failure |
| 「24/7 客服熱線」 (沒有真實客服) | 過度承諾傷信任 |
| 「Fortune 500 客戶」 (沒有真實客戶) | Runtime Truth 違反 |

#### 允許的內容

| ✅ 鼓勵 | 原因 |
|---|---|
| help@goaa.ai (真實 Email, SMTP 通過驗證) | 規範 #19 v2 SMTP 真實寄出 |
| GEER IT INC (真實母公司) | 公司資訊真實 |
| 9663 Garvey Ave (真實地址, Phase A 暫時隱藏) | 真實但暫不公開 |
| (858) 519-8064 (真實電話, Phase A 暫時隱藏) | 真實但暫不公開 |
| 「Powered by GOAA Runtime OS」 | 真實技術棧 |

---

## 8. Framer Implementation Notes

### 8.0 戰略定位

本章節為**給 Framer 設計師 / 開發者的執行手冊**, 不直接出現在 production 網頁上。

目的: 將前面 Section 0-7 的戰略文案 → 轉化為 Framer 可執行的 6 輪重構流程, 配合規範 #15 24h cooldown + 規範 #11 只增不毀 + 規範 #26 jsx 預檢護欄。

---

### 8.1 6 輪重構流程 (Framer V2.0 改版)

#### Round 1: Phase A 緊急清理 (1-2 小時, 已在 2026-05-17 完成大部分)

**目標**: 清除 Radison template 殘留 4 大殘留 + 隱藏 Contact 真實資料

**操作清單**:
1. ❌ 刪除 Testimonials section (Radison 客戶證言殘留)
2. ❌ 刪除 Services section ("Tailored solutions" 殘留)
3. ❌ 刪除 Benefits section ("Discover key benefits" 殘留)
4. ❌ 刪除 Pricing section (Essential / Advanced / Comprehensive 殘留)
5. ✅ 隱藏 Contact 區塊真實電話 + 地址 (Phase A 拍板)
6. ✅ Footer slogan 改為 "GOAA — AI Agent for your life"

**師兄手動操作, Claude 提供逐步指引**:
- 在 Framer 編輯器右側 layers panel 找到對應 section
- 右鍵 → Delete
- 保存後 Preview 確認佈局不破

**驗收標準**:
- production https://goaa.ai 訪問後不見任何 Radison 字樣
- Footer slogan 顯示 "GOAA — AI Agent for your life"
- Contact 區塊只顯示 help@goaa.ai

#### Round 2: 中文核心 Section 0-2 落地 (2-3 小時)

**目標**: 將 Hero / Header / Strategic Refactor Summary 的中文版本落地到 Framer

**操作清單**:
1. **Header 重寫**: 6 個導航項 (首頁/生態/Skill Marketplace/Provider Pro/Worker Network/聯繫我們) + EN | 中 toggle + 主 CTA「部署我的 AI 勞動力」
2. **Hero 重寫**:
   - 主標題: 「GOAA Runtime OS / 讓 AI 真正下場幹活的實體數位勞動力系統」
   - 副標題 3 行
   - 品牌靈魂句: 「能做事, 能賺錢. / 你的 AI 數字生活小龍蝦.」
   - 雙 CTA: 「開始部署 AI 勞動力 →」 + 「查看 Worker Network」
3. **Section 0 內容**: 戰略重構摘要表 + 邊界聲明 (允許 / 禁止措辭)

**規範 #26 jsx 預檢**:
- 預覽桌面 + 平板 + 手機三種斷點
- 確認 EN | 中 toggle 切換無亂碼
- 確認 CTA 點擊有 hover 效果

**驗收標準**:
- Hero 第一屏視覺打動 (Cyber-Noir 黑底 + electric-blue 呼吸燈)
- 主標題誇張可信, 不是 Chatbot 感
- 邊界聲明嚴守 — 不出現「保證收益」「100% 完美」等禁忌

#### Round 3: 英文核心 Section 0-2 落地 (1-2 小時)

**目標**: 英文版**不直翻**, 升級為矽谷硬核工具鏈語言

**操作清單**:
1. **Header English**: Home / Ecosystem / Skill Marketplace / Provider Pro / Worker Network / Contact
2. **Hero English**:
   - Headline: "GOAA Runtime OS / Deploy Physical AI Labor, Not Just Chatbots."
   - Subheadline: "Stop generating pure text. Power on, connect, deploy native physical AI labor..."
   - Brand soul tagline: "Make it work. Make it earn. / Your edge-deployed AI labor unit."
   - Dual CTA: "Deploy AI Labor →" + "Explore Worker Network"

**規範 #29 異構雙軌**:
- 英文版不重複中文「小龍蝦」metaphor
- 英文版用 infrastructure language: "Physical AI labor", "edge-deployed", "Make it earn"
- 押韻設計: work / earn (雙押韻)

**驗收標準**:
- 英文版讀起來像 Anthropic / Vercel / Linear 的 landing page (矽谷硬核風)
- 不像 Google Translate 直翻
- "Make it work. Make it earn." 朗讀通順, 短促有力

#### Round 4: Section 3-5 業務層落地 (4-5 小時, 最重)

**目標**: Three-Tier Ecosystem + AiKa Box + Skill Marketplace 三大商業層落地

**操作清單**:
1. **Section 3 三層生態 Card Grid**:
   - Client / Provider / Worker 三張 Glassmorphism Card 並排
   - 每張卡片含: header + 定位 + 階梯訂閱 + 真實案例 + CTA
   - 底部敘事帶 (動態高亮 1→4 完整閉環)
2. **Section 4 AiKa Box Hardware**:
   - Hero 大圖 (placeholder, 等實機照片)
   - 8 大核心能力 (Grid 4×2)
   - 智能檢測機制動畫 (本地盒子 ON / 雲端 OFF)
   - 真實對比表 (97% vs 61% 等大字數據)
   - 真實工作流範例 (3 min / 16 Credits  vs  25 min / 80 Credits)
   - 回本計算大字 ($125/mo · 8 個月回本)
   - 兩種購買選項並排卡片
   - 三 CTA 並排
3. **Section 5 Skill Marketplace**:
   - 6 張 Skill Card (3×2 Grid)
   - SaaS 體驗演示 (toggle 滑動 / 啟停動畫)
   - 8 階段生命週期敘事帶
   - CTA Marketplace 主入口

**規範 #36 v2 真實狀態鎖**:
- 所有數字 ($19.99 / $39.99 / $999 / $99 / $2.99 / $9.99 / 50/50 / $2,780 / $2,477) 必須與戰略憲法 V1.0 完全對齊
- AiKa Box 硬件 spec 嚴禁寫死 (CPU/RAM/GPU 等待師兄拍板出貨時補充)
- Skill Marketplace 6 張卡片狀態標籤 (Beta / Internal / Coming Soon) 嚴守, 不誇大已上線

**驗收標準**:
- 三層生態 Card Grid 視覺震撼 (Glassmorphism 半透明 + 流動光線連線)
- AiKa Box 真實對比表大數據 (97% vs 61%) 一眼震撼
- Skill Marketplace 6 張卡片 toggle 滑動絲滑 (electric-blue → purple 漸層)

#### Round 5: Tao Review + 24h Cooldown (規範 #15)

**目標**: 師兄真實審查 + 24h 觀察期, 不直接 Publish

**操作清單**:
1. Round 1-4 全部完成後, Framer 編輯器**保存 draft**, **不 Publish**
2. Claude 生成 Round 4 完成報告 (含截圖 / 邊界對齊清單)
3. 師兄審查全部 5 個 Section, 給出修正意見 (如有)
4. 師兄修正完成後, 啟動 **規範 #15 24h cooldown 計時器**
5. 24h 期間: 任何窗口 / Claude / AiKa-1 / AiKa-2 不准動 Framer
6. 24h 觀察期內若發現重大問題 → 修正 → cooldown 重置

**規範 #15 配套**:
- Cooldown 起算後立刻在 Memory 加註 "Framer V2.0 cooldown: 5/X HH:MM PT → 5/Y HH:MM PT"
- HANDOFF.md 同步更新
- AiKa-1 / AiKa-2 不准在這 24h 期間動 Framer

**驗收標準**:
- 師兄對 5 個 Section 全部認可 (中文版 + 英文版)
- 24h cooldown 無重大發現 / 用戶投訴
- Memory + HANDOFF.md 同步更新

#### Round 6: Publish + 24h 觀察期 (規範 #15 再啟動)

**目標**: 正式 Publish production goaa.ai V2.0, 再啟 24h 觀察期

**操作清單**:
1. 師兄在 Framer 編輯器點擊 "Publish"
2. 等待 Framer CDN 部署完成 (約 2-5 分鐘)
3. 訪問 production https://goaa.ai 真實驗證
4. AiKa-1 / AiKa-2 / DO 三方 curl 驗證 (確認全球 CDN 同步)
5. 啟動**新的 24h 觀察期** (Round 5 是 draft cooldown, Round 6 是 production cooldown)

**規範 #15 嚴守**:
- Production 變更後 24h 內不准做 Phase B 修改
- 24h 內若發現重大問題 → 緊急回滾到 V1.x (Framer 有 version history)
- 24h 後若無問題 → V2.0 鎖定為新 production baseline

**驗收標準**:
- production goaa.ai 全球可訪問
- 三方驗證一致
- 24h 觀察期無 crash / error / 用戶投訴
- 沒有 production hot-fix (除緊急回滾)

---

### 8.2 Framer 技術實作清單

#### CMS 動態內容 (建議)

```
不要把所有 6 張 Skill Card 寫死在 page 上.
改用 Framer CMS 動態渲染:

1. 建立 CMS Collection "Skills"
2. 字段: name / english_name / category / target_user / status / 
        price_monthly / trial_days / platform_share / worker_share / 
        rating / active_subscribers / icon / description_cn / description_en
3. 6 張卡片動態從 CMS 拉取
4. 未來上 / 下架 Skill 只需在 CMS 編輯, 不需動 page

優勢:
- Skill 上下架不需重新 publish
- 多語言切換自動 (description_cn / description_en)
- 未來上 100 個 Skill 也是同一個 page
```

#### Lottie / Video 動畫

```
Section 4 AiKa Box Hero 區塊建議用 Lottie 動畫:
- electric-blue breathing light (沿盒子邊緣 animate-pulse)
- 旁邊浮動 task list (pulse 動畫)
- 背景 Cyber-Noir 黑色 + 微星點 + 漸層紫光

如無 Lottie, 用 CSS animation:
@keyframes breathing {
  0%, 100% { opacity: 0.6; box-shadow: 0 0 20px #60a5fa; }
  50% { opacity: 1; box-shadow: 0 0 40px #60a5fa; }
}

.aika-box-hero {
  animation: breathing 3s ease-in-out infinite;
}
```

#### EN | 中 Toggle 實作

```javascript
// localStorage 共享 lang state (Header + Footer 兩個 toggle 同步)

const setLanguage = (lang) => {
  localStorage.setItem('goaa_lang', lang);
  document.documentElement.lang = lang === 'en' ? 'en' : 'zh-Hant';
  // 觸發所有 lang-toggle 監聽器更新
  window.dispatchEvent(new CustomEvent('langChange', { detail: lang }));
};

const getLanguage = () => {
  return localStorage.getItem('goaa_lang') || 'zh-Hant';
};

// Header / Footer Toggle 元件
const LangToggle = () => {
  const [lang, setLang] = useState(getLanguage());
  
  useEffect(() => {
    const handler = (e) => setLang(e.detail);
    window.addEventListener('langChange', handler);
    return () => window.removeEventListener('langChange', handler);
  }, []);
  
  return (
    <div className="lang-toggle">
      <button 
        className={lang === 'en' ? 'active' : ''} 
        onClick={() => setLanguage('en')}>
        EN
      </button>
      <button 
        className={lang === 'zh-Hant' ? 'active' : ''} 
        onClick={() => setLanguage('zh-Hant')}>
        中
      </button>
    </div>
  );
};
```

#### CDN / 性能優化

```
1. 圖片用 WebP + 多分辨率 (srcset)
2. 字體預載入 (DM Serif Display, DM Sans, DM Mono)
3. Above-the-fold critical CSS inline
4. Section 4-7 lazy load (用 Intersection Observer)
5. Framer 內建 CDN 已優化, 額外加: Cloudflare Tunnel proxy
6. Lighthouse 目標: Performance 90+, Accessibility 95+, SEO 95+
```

---

### 8.3 規範 #11 護欄: 不破壞已有 Dashboard

#### Critical Path 隔離

```
Framer V2.0 改版**只影響 portal.goaa.ai 首頁 (Hero / Header / Footer)**, 
不影響:
- Dashboard 黃金版 (V4.0.5.4-UI, 774 行 / 9b4fb15d)
- portal.goaa.ai/dashboard (登入後的調度中心)
- AiKa Box 真實設備
- Worker Network 真實節點

Framer V2.0 改版**不能**:
- 動 components/GoaaDashboard.jsx
- 動 services/model-router/api.py
- 動 services/worker-agent/agent.py
- 觸發 Dashboard 黃金版重新 build
```

#### 規範 #11 Backup 護欄

```
Framer 編輯器內建 version history (有 30 天回滾)
但為了規範 #11 雙重保護:

Round 1-6 每一輪開始前, Claude 提醒師兄:
1. 在 Framer 編輯器右上角點擊 "Save" 確保 draft 保存
2. 拍照截屏當前狀態 (備份視覺)
3. 記錄當前 version ID (Framer 有版本號)

Round 6 Publish 前:
- 顯式拍照 / 截屏完整頁面 (Desktop / Tablet / Mobile)
- 記錄當前 production version
- 24h 觀察期內若需回滾, 用 Framer 版本歷史 1-click 回滾
```

---

## 9. Risk Register

### 9.0 戰略定位

本章節為**風險登記簿**, 列出 V2.0 改版可能踩的雷, 並提供緩解策略。

規範 #28 強制: 不准 silent failure, 必須誠實列風險。

---

### 9.1 風險 1: 中文「小龍蝦」metaphor 國際化失敗 (P1)

**風險描述**:
中文用戶看到「能做事, 能賺錢 / 你的 AI 數字生活小龍蝦」會心一笑, 但英文直翻 "Your AI digital lobster" 完全失去意義, 反而引發困惑或 ridicule。

**緩解策略**:
- ✅ 規範 #29 異構雙軌: 中文保留小龍蝦, 英文升級為 "Your edge-deployed AI labor unit"
- ✅ 英文版品牌靈魂句: "Make it work. Make it earn." (押韻 + 強而有力)
- ✅ 中文版主要面向北美華人 / 中國背景 / complex global lives 用戶
- ✅ 英文版主要面向國際資本 / 極客用戶 / Provider 群體

**剩餘風險**: 中等. 若有人翻譯中文版發現 metaphor 差異, 可能質疑「為什麼中文這麼可愛, 英文這麼工業?」  
**回應**: 戰略選擇, 不解釋. 兩個版本各自獨立, 服務不同用戶群。

---

### 9.2 風險 2: 過度承諾 Provider Pro 收益 (P0)

**風險描述**:
Provider Pro 文案寫「月接 1-2 個額外案件即可 cover 訂閱費」, 用戶實際訂閱後若 0 案件, 可能投訴 / 退款 / 公開負評。

**緩解策略**:
- ✅ Section 3.2.1 / 3.2.2 明確邊界聲明: 「Pro 不保證 Leads 數量, 實際成單依 Provider 自身專業判斷」
- ✅ Provider Pro Free 階段提供, 不強制付費
- ✅ 30 天試用期 (Try 30 Days Free)
- ✅ 取消政策明確 (隨時可取消)

**剩餘風險**: 中等. 若市場接受度不如預期, Provider Pro 可能不可持續。  
**回應**: V4.3 上線後密切監控 Pro 訂閱數據, 若低於預期觸發 Skill Marketplace 加速。

---

### 9.3 風險 3: Credits 被誤認為金融投資產品 (P0)

**風險描述**:
Credits 公式「$0.01 / Credit · 可抵月費 · 50/50 分潤」可能被監管 / 用戶誤認為 cryptocurrency / token / 證券, 引發 SEC / FinCEN / 州監管調查。

**緩解策略**:
- ✅ Section 6 免責聲明明確: 「Credits 是任務完成的結算憑證, 不是金融投資回報」
- ✅ Section 3.3 Worker Network 邊界: 「Credits 收益依任務量 / 設備性能 / 電費而異, $125/月為基於假設的測算值, 非保證」
- ✅ Credits 不可提現 (memory: $39.9 = 3,990 Credits 抵月費, 不可換現金)
- ✅ Credits 只能在 GOAA 生態內使用 (抵月費 / 換 Skill / 內部結算)
- ✅ 不發行 cryptocurrency / 不上交易所 / 不接受第三方買賣

**剩餘風險**: 低. 但需專業法律意見書 (V4.3 Skill Marketplace 上線前必須完成)。

---

### 9.4 風險 4: IUL / Term Insurance / 稅務內容合規違規 (P0)

**風險描述**:
Skill Card 5 (IUL/Term Insurance Planning) + Section 3.1 Client 案例 3 (45 歲家庭資產配置) 涉及保險 + 投資 + 稅務內容。若被持牌專業者投訴「未持牌即提供保險 / 投資建議」, 可能違反州保險法 / SEC / IRS Circular 230。

**緩解策略**:
- ✅ Section 6 三大合規邊界明確: AI 不替代律師 / CPA / 保險經紀 / 投資顧問
- ✅ Skill Card 5 邊界聲明: 「本 Skill 提供分析框架, 不構成保險或投資建議. 所有實際投保決策必須由持牌保險經紀人 (Provider) 最終確認」
- ✅ Client 案例 3 結尾: 「→ 推薦保險 Provider (持牌)」, 不直接 AI 給投保建議
- ✅ Provider 篩選機制: GOAA 平台只 onboard 真實持牌 Provider (持牌證件審核)
- ✅ 用戶協議 (Terms of Service) 明確免責條款 (V4.3 上線前完成)

**剩餘風險**: 中等. 但律師意見書 + 持牌 Provider 真實審核可大幅降低。

---

### 9.5 風險 5: AiKa Box 硬件 spec 與實際出貨不一致 (P1)

**風險描述**:
V2.0 文案寫了 "RTX 4060 + 100 任務/月 → $125/月" 等 ROI 計算, 用戶可能誤認為 AiKa Box 自帶 RTX 4060。實際出貨硬件規格未定案 (可能是 i5 + 集成顯卡, 也可能是 i7 + RTX 4060)。

**緩解策略**:
- ✅ Section 2.2 Hero + Section 4.4 視覺實作指引: **Spec 隔離條款**, 不寫具體硬件型號
- ✅ ROI 範例明確標註「基於 RTX 4060 + 100 任務/月假設」, 不是 AiKa Box 自帶
- ✅ AiKa Box CTA 改為 "加入 Waitlist", 不是 "立即購買" (除非師兄明確批准預售)
- ✅ 實機照片用 placeholder, 等出貨後補真實照片
- ✅ Spec 由師兄拍板, 出貨前 V2.0 文案保持 spec 隔離

**剩餘風險**: 低. 但出貨後若 spec 變更, V2.0 文案需要對應更新。

---

### 9.6 風險 6: Skill Marketplace 超前承諾 (P0)

**風險描述**:
6 張 Skill Card 中 3 張 (Card 1 家庭信件 / Card 3 AI 視頻 / Card 5 IUL/Term) 標為 Beta / Coming Soon。用戶若以為「現在就能訂閱」, 訂閱後發現未上線, 可能投訴。

**緩解策略**:
- ✅ Section 5.6 邊界聲明明確列禁忌: 「不允許 Marketplace 已上線」
- ✅ 6 張 Skill Card 狀態標籤強制顯示 (Beta / Internal / Coming Soon)
- ✅ Coming Soon 卡片的 Toggle disabled, 點擊觸發 "Notify Me" Waitlist 彈窗
- ✅ Available 卡片才能訂閱 (V4.3 上線後逐步開放)
- ✅ V4.3 Roadmap 明確時程: 2026 Q3 預計 Card 2 IRS Letter + Card 4 Mortgage Stress + Card 6 Provider Lead 上線

**剩餘風險**: 低. 但需在 Framer 實作層強制執行 disabled toggle 邏輯。

---

### 9.7 風險 7: Framer Publish 誤觸 production (P1)

**風險描述**:
Round 5 (Tao Review) 期間師兄編輯 draft, 若不小心點擊 "Publish" 按鈕, 未經審查的 V2.0 直接上 production goaa.ai, 可能展示不完整 / 有錯誤的版本。

**緩解策略**:
- ✅ Framer 編輯器 Publish 按鈕需二次確認 (內建機制)
- ✅ Round 5 明確流程: 師兄保存 draft, 不點 Publish
- ✅ Round 6 才是 Publish 階段, 規範 #15 24h cooldown 嚴守
- ✅ 若誤觸 Publish, Framer version history 1-click 回滾到 V1.x

**剩餘風險**: 極低. Framer 機制 + 規範 #15 雙重保護。

---

### 9.8 風險 8: 電話 / 地址被爬蟲抓取 (P1)

**風險描述**:
Contact 區塊真實電話 (858) 519-8064 + 地址 (9663 Garvey Ave) 若直接公開, 可能被爬蟲抓取, 引發 spam call / spam mail / 騷擾。

**緩解策略**:
- ✅ Phase A 拍板「保留真實但 production 隱藏」, 電話 + 地址不公開
- ✅ Production 只顯示 help@goaa.ai (郵箱, 已配 Zoho 反 spam)
- ✅ 真實電話 + 地址保留在 Framer CMS 內 (內部使用)
- ✅ V5.0 完整收 lead 機制後再開放 (用 Cloudflare Turnstile 反爬蟲)

**剩餘風險**: 極低. 當前 Phase A 策略已最大化保護。

---

### 9.9 風險登記簿總覽

| # | 風險 | 優先級 | 狀態 |
|---|---|---|---|
| 1 | 中文 metaphor 國際化失敗 | P1 | ✅ 規範 #29 異構雙軌已緩解 |
| 2 | 過度承諾 Provider Pro 收益 | P0 | ✅ 邊界聲明 + 30 天試用已緩解 |
| 3 | Credits 被誤認為投資 | P0 | ⏳ 需律師意見書 (V4.3 前) |
| 4 | IUL/稅務內容合規違規 | P0 | ⏳ 需律師意見書 + Provider 真實審核 |
| 5 | AiKa Box spec 不一致 | P1 | ✅ Spec 隔離條款已緩解 |
| 6 | Skill Marketplace 超前承諾 | P0 | ✅ Disabled toggle + Coming Soon 標籤已緩解 |
| 7 | Framer 誤 Publish | P1 | ✅ 規範 #15 + Framer 機制已緩解 |
| 8 | 電話地址被爬蟲 | P1 | ✅ Phase A 隱藏策略已緩解 |

**結論**: 8 個風險中, 5 個已完全緩解, 2 個 (Credits 合規 / 保險合規) 需律師意見書, 1 個 (AiKa Box spec) 等出貨後更新。

V2.0 文案藍圖**可以推送 GitHub**, 但**不可立刻 Publish Framer production**, 須等律師意見書完成 + 師兄拍板。

---

## 10. Final Execution Checklist

### 10.0 戰略定位

本章節為**最終執行檢查清單**, 確認 V2.0 文案藍圖**從 GitHub 推送到 Framer Publish** 的每一個步驟都對齊規範 + 戰略憲法。

---

### 10.1 GitHub 推送前檢查 (本文件本身)

#### 規範 #11 (只增不毀)
- ✅ 本文件為新增, 不刪除任何既有 docs/marketing 內容
- ✅ Section 0-10 完整自包含, 不依賴外部文檔
- ✅ 不修改 components/GoaaDashboard.jsx (Dashboard 黃金版隔離)
- ✅ 不修改 V4_1_Worker_PLAN.md 主線
- ✅ 不修改 INDEX.md / MEMORY.md / AGENTS.md (除非師兄明確要求)

#### 規範 #12 (Fingerprint Check)
- ⏳ 推送前 AiKa-1 必須驗證: Lines + Bytes + MD5
- ⏳ 預期: ~2360 行 / ~95 KB / MD5 待生成

#### 規範 #13 v2 (Session Handoff)
- ⏳ 推送後 HANDOFF.md 更新, 加入 V2.0 文檔位置 + commit hash

#### 規範 #14 R2 (Golden Baseline)
- ✅ 本文件**不**升級 Dashboard 黃金版 (V4.0.5.4-UI 不變)
- ✅ 本文件是 marketing 文檔, 不是 UI 文檔

#### 規範 #15 (24h Cooldown)
- ⏳ 推送後 24h cooldown 計時器起算
- ⏳ Memory 加註 cooldown 釋放時間

#### 規範 #21 (指令長度限制)
- ✅ AiKa-1 寫入指令拆分為 5 個子批次 (每個 < 10000 字符)
- ✅ 整合用 Python 腳本 (從 Downloads 抓 5 個檔案合併)

#### 規範 #26 (jsx 部署預檢)
- ✅ 本文件為 markdown, 不是 jsx, 無需 React 預檢
- ✅ 本文件不影響 Vercel build

#### 規範 #28 (No Silent Failure)
- ✅ 全文 8 個風險明確列出 (Section 9)
- ✅ 邊界聲明全文清晰 (Section 6 免責聲明)
- ✅ 不過度承諾, 不假裝萬全

#### 規範 #36 v2 (Memory First, Real State Verification)
- ✅ 所有商業數字 ($19.99 / $39.99 / $999 / $99 / $2.99 / $9.99 / 50/50) 來自戰略憲法 V1.0 真實提取
- ✅ AiKa Box 8 大能力來自 geekom_comparison HTML 真實素材
- ✅ Worker Network 規模 (5 Live 節點 / 7 SUCCESS / $0.75 day-one) 來自 memory 真實狀態
- ✅ 不憑想像捏造數字

---

### 10.2 AiKa-1 寫入步驟 (規範 #21 拆分)

#### Step 0: 環境準備 (1 分鐘)

```powershell
cd C:\Users\Administrator\Projects\goaa-ai-local
git status
git pull origin main
git log --oneline -5

# 確認 HEAD = 363ac4a (動作 A 推完後的 HEAD)
# 確認 working tree clean
```

#### Step 1: 創建目錄 (10 秒)

```powershell
New-Item -ItemType Directory -Path "docs\marketing" -Force | Out-Null
```

#### Step 2: 從師兄 Downloads 抓檔案 (1 分鐘)

```powershell
# 師兄會從 Claude 對話下載 5 個 batch 檔案
# (或 1 個合併後的完整檔案, 取決於 Claude 給的方式)
$src = "C:\Users\Administrator\Downloads\GOAA_PORTAL_CONTENT_MATRIX_V2.md"
$dst = "docs\marketing\GOAA_PORTAL_CONTENT_MATRIX_V2.md"

# 規範 #12 fingerprint 校驗
$srcHash = Get-FileHash $src -Algorithm MD5
$srcLines = (Get-Content $src).Count
$srcSize = (Get-Item $src).Length

Write-Host "Source file:"
Write-Host "  Path: $src"
Write-Host "  Lines: $srcLines"
Write-Host "  Bytes: $srcSize"
Write-Host "  MD5: $($srcHash.Hash.ToLower())"
Write-Host ""
Write-Host "預期: 約 2360 行 / ~95 KB / MD5 從 Claude 提供"
```

#### Step 3: 對齊 Claude 給的 fingerprint (規範 #12, 30 秒)

```powershell
# Claude 會給:
# Lines: 2362
# Bytes: 95XXX
# MD5: XXXXXXXXX

# 師兄手動對比, 若不符合則 STOP, 不寫入

if ($srcHash.Hash.ToLower() -eq "EXPECTED_MD5_FROM_CLAUDE") {
    Write-Host "✅ MD5 對齊"
} else {
    Write-Host "❌ MD5 不對齊, 停手回報 Claude"
    return
}
```

#### Step 4: 寫入 docs/marketing/ (10 秒)

```powershell
Copy-Item $src $dst -Force

# 寫入後再校驗一次
$dstHash = Get-FileHash $dst -Algorithm MD5
$dstLines = (Get-Content $dst).Count

Write-Host "Written to: $dst"
Write-Host "  Lines: $dstLines"
Write-Host "  MD5: $($dstHash.Hash.ToLower())"

if ($dstHash.Hash -eq $srcHash.Hash) {
    Write-Host "✅ Copy 完整, MD5 一致"
} else {
    Write-Host "❌ Copy 損壞, 重試"
    return
}
```

#### Step 5: git add + commit + push (1 分鐘)

```powershell
git add docs/marketing/GOAA_PORTAL_CONTENT_MATRIX_V2.md
git status

# 預期: 1 new file, ~2360 insertions

git commit -m "docs: construct goaa.ai V2.0 marketing copy matrix blueprint"
git push origin main

# 推完看新 HEAD
git log --oneline -3
```

#### Step 6: GitHub 真實驗證 (30 秒)

```powershell
# 等 GitHub 30 秒同步
Start-Sleep -Seconds 30

# 用 curl 確認 GitHub raw 可訪問
$rawUrl = "https://raw.githubusercontent.com/taofengtx/goaa-ai-frontend/main/docs/marketing/GOAA_PORTAL_CONTENT_MATRIX_V2.md"
$response = Invoke-WebRequest -Uri $rawUrl -UseBasicParsing

Write-Host "GitHub raw status: $($response.StatusCode)"
Write-Host "Content length: $($response.Content.Length) bytes"

if ($response.StatusCode -eq 200) {
    Write-Host "✅ GitHub 真實可訪問"
} else {
    Write-Host "❌ GitHub 同步問題, 等多 30 秒重試"
}
```

#### Step 7: 規範閉環回報 (30 秒)

```powershell
$newHead = (git rev-parse --short HEAD)
$now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Write-Host ""
Write-Host "================================================"
Write-Host "V2.0 Marketing Matrix Push 真實閉環"
Write-Host "================================================"
Write-Host "新 HEAD: $newHead"
Write-Host "Push 時間: $now PT"
Write-Host "規範 #15 24h Cooldown 解除: $((Get-Date).AddHours(24).ToString('yyyy-MM-dd HH:mm:ss')) PT"
Write-Host ""
Write-Host "GitHub URL:"
Write-Host "  https://github.com/taofengtx/goaa-ai-frontend/blob/main/docs/marketing/GOAA_PORTAL_CONTENT_MATRIX_V2.md"
Write-Host ""
Write-Host "下一步:"
Write-Host "  1. Memory 條目更新 (Claude 處理)"
Write-Host "  2. HANDOFF.md 更新 V2.0 文檔位置 (Claude 處理)"
Write-Host "  3. 規範 #19 v2 SMTP 收工郵件 (Claude 處理)"
Write-Host "  4. 24h cooldown 內不動 V2.0 文件"
```

---

### 10.3 Claude 端後續動作

#### 動作 1: 更新 Memory 條目 (規範 #36 v2)

```
新增 Memory 條目: "GOAA V2.0 Marketing Matrix 文檔已 push (2026-05-19 HH:MM PT):
路徑 docs/marketing/GOAA_PORTAL_CONTENT_MATRIX_V2.md, 
commit XXXXXXX, ~2360 行 / ~95 KB.
規範 #15 24h cooldown 起算, 5/20 HH:MM PT 解除.
下一步: Framer V2.0 6 輪重構, V4.3 Skill Marketplace 上線前需律師意見書 (Credits + IUL 合規)."
```

#### 動作 2: 更新 HANDOFF.md (規範 #13 v2)

```
HANDOFF.md 文末加入:

## 最新里程碑 (2026-05-19)
- V2.0 Marketing Matrix 文檔 push: commit XXXXXXX
- 文檔路徑: docs/marketing/GOAA_PORTAL_CONTENT_MATRIX_V2.md
- 規模: ~2360 行 / ~95 KB
- 規範 #15 cooldown: 5/19 HH:MM PT → 5/20 HH:MM PT

## 待辦 P0 (V2.0 後續)
1. 律師意見書 (Credits 合規 + IUL/稅務合規) — V4.3 前完成
2. Framer V2.0 6 輪重構 (Round 1-6)
3. AiKa Box 硬件 spec 待師兄拍板
4. Skill Marketplace 6 張卡片 disabled toggle 實作
```

#### 動作 3: 規範 #19 v2 SMTP 收工郵件

```
郵件主題: "GOAA Dev Log 2026-05-19 — V2.0 Marketing Matrix push + Action A 閉環"

郵件內容:
1. 戰績摘要:
   - 動作 A (HANDOFF.md fix) commit 363ac4a push 5/19 01:07 PT
   - Memory 條目 14 升級 (V4.0.5.4-UI 黃金版 fingerprint)
   - V2.0 Marketing Matrix push commit XXXXXXX (~2360 行)

2. 系統狀態:
   - Worker 5 Live 節點正常
   - PG 持久化正常
   - Cloudflare Tunnel 正常

3. 明日 P0:
   - 律師意見書啟動 (Credits + 保險合規)
   - Framer Round 2 (中文 Hero + Header 落地)

4. 規範變更:
   - 規範 #15 兩個 cooldown 並行 (5/20 01:07 PT 動作 A + 5/20 HH:MM PT V2.0)
```

---

### 10.4 ⚠️ 後續注意事項 (規範 #28 誠實聲明)

#### V2.0 文檔 push 後**不可立刻**做的事

| ❌ 禁止 | 原因 |
|---|---|
| 立刻 Publish Framer V2.0 | 需律師意見書 + Round 1-6 完整流程 |
| 修改 Dashboard 黃金版 | 規範 #11 + #14 R2 雙重保護 |
| 改 V4.1-Worker 主線 | 主線不動搖 (戰略憲法第 2 章) |
| 公開承諾 AiKa Box 硬件 spec | Spec 未定案, 規範 #36 + SUPREME 1.4 |
| 預售 Skill Marketplace | 未上線, 規範 #28 不准虛假承諾 |

#### V2.0 文檔 push 後**可以**做的事

| ✅ 允許 | 操作 |
|---|---|
| 開始律師意見書工作 | 找 GEER IT INC 顧問律師 / 外聘 SEC + insurance 律師 |
| Framer Round 1-2 啟動 | Phase A 緊急清理 + 中文核心落地 |
| 拍真實 AiKa Box 照片 | 出貨後拍照, 取代 placeholder |
| Skill Marketplace 開發 | V4.3 Roadmap 啟動 |
| Worker Network 擴充 | V4.1-Worker 主線繼續 |

---

### 10.5 規範閉環檢查表 (Push 前 / Push 後)

#### Push 前檢查

- [ ] 規範 #11: 不破壞既有
- [ ] 規範 #12: Fingerprint 對齊 (Lines + Bytes + MD5)
- [ ] 規範 #21: 指令拆分 < 10000 字符
- [ ] 規範 #28: 邊界聲明完整
- [ ] 規範 #36 v2: 真實數字 / 真實素材

#### Push 後檢查

- [ ] 新 HEAD 真實確認 (git rev-parse)
- [ ] GitHub raw URL 真實可訪問 (curl 200)
- [ ] Memory 條目更新 (Claude)
- [ ] HANDOFF.md 更新 V2.0 位置 (Claude)
- [ ] 規範 #15 cooldown 計時起算
- [ ] 規範 #19 v2 SMTP 收工郵件真實寄出

---

**簽發**: 2026-05-19 (PT)  
**狀態**: 戰略文檔藍圖, Framer V2.0 改版前必讀  
**下次審視**: V4.3 Skill Marketplace 上線前

# GOAA — AI Agent for your life. Built for trust. Engineered to earn.

---

# 📜 PROVIDER-FIRST STRATEGY UPDATE (2026-05-19)

> **SUPREME DIRECTIVE 修訂 — 由 ChatGPT + Gemini + Tao 三方討論後**, 在原 V2.0 Marketing Matrix (Section 0-10) 基礎上, 新增 Section 11-21, 鎖定 **「前 6 個月聚焦 Provider Pro」** 商業基線。
>
> 本次修訂遵守規範 #11 (只增不毀): Section 0-10 完整保留, 不修改任何既有商業數字、Hero 文案、AiKa Box 邊界、Skill Marketplace 卡片狀態。
>
> 本次修訂**不直接修改 Framer production**, 不 Publish goaa.ai, 不影響 GoaaDashboard.jsx, 不動 V4.1-Worker / Worker V5.0 主線。
>
> **修訂簽發**: 2026-05-19 (PT) · **觸發**: SUPREME DIRECTIVE Provider-First Revision

---

## 11. Integrated Review Notes — ChatGPT + Gemini + Tao

### 11.1 修訂背景

V2.0 Marketing Matrix 原版 (Section 0-10) 已完整描繪 GOAA 長期願景:
- AI Runtime OS
- AI Worker Economy
- Three-Tier Ecosystem (Client / Provider / Worker)
- Skill Marketplace 50/50 分潤
- AiKa Box 邊緣硬件

但 Tao 師兄與 ChatGPT + Gemini 三方審查後, 對**短期落地路徑**達成新共識:

> **GOAA.AI 長期是 AI Runtime OS, 但前 6 個月必須聚焦 Provider AI 工作台.**
>
> 也就是: 先做能收錢的華人專業服務者 AI 自動化工作台, 再逐步擴展成 Client + Provider + Worker + Skill Marketplace 的 AI 勞動力平台.

### 11.2 Provider-First Revision (English)

```
Provider-First Revision:

Although the long-term Portal V2.0 narrative remains AI Runtime OS / AI Worker Economy,
the first commercial version of goaa.ai should prioritize Provider AI Workstation messaging.

The homepage should not over-rotate into a broad consumer platform.
It should first explain how GOAA helps service professionals automate client intake,
document workflows, follow-ups, draft generation, and local task execution.

Client Plus, public Skill Marketplace, Worker Developer Platform, and Worker payout economy
remain roadmap layers — not Phase 1 deliverables.

Reviewers: ChatGPT + Gemini + Tao
Effective: 2026-05-19 (PT)
```

### 11.3 Provider-First 修訂 (中文)

```
Provider-First 修訂:

GOAA.AI 的長期願景仍然是 AI Runtime OS 與 AI Worker Economy,
但第一個商業落地版本應優先聚焦 Provider AI 工作台.

官網首頁不應過度強調全民 Client 平台,
而應先說清楚 GOAA 如何幫專業服務者自動整理客戶資料、處理文件、
生成 follow-up、草稿與本地任務執行.

Client Plus、公開 Skill Marketplace、Worker 開發者平台與 Worker Credits 提現
均屬後續階段, 不是 Phase 1 交付內容.

審查者: ChatGPT + Gemini + Tao 三方
生效日: 2026-05-19 (PT)
```

### 11.4 與原 V2.0 Section 0-10 的關係

| 原 V2.0 內容 | Provider-First Revision 處理 |
|---|---|
| Section 2 Hero "Physical AI Runtime OS" | **保留** (長期願景), 但 Framer 首屏文案調整為 Provider 優先 |
| Section 3 Three-Tier Ecosystem (Client / Provider / Worker) | **保留**, 但短期 Framer 文案排序: Provider 第一, Client 第二, Worker 第三 |
| Section 4 AiKa Box | **保留**, 但短期定位為「Provider 辦公室本地 Worker Runtime」 |
| Section 5 Skill Marketplace 6 張卡片 | **保留**, 但短期只主推 Provider Skill (Card 2 IRS / Card 4 Mortgage / Card 6 Provider Lead) |
| Section 6 Trust / Privacy / Compliance | **保留**, Provider-First 階段更需要嚴守邊界 |
| Section 7 Footer "GOAA — AI Agent for your life" | **保留**, 通用品牌口號 |
| Section 8 Framer 6 輪重構 | **更新** — Round 2 中文 Hero 優先用 Provider 文案 |
| Section 9 Risk Register | **保留**, 增補 Provider-First 風險條目 |

### 11.5 文檔變更類型聲明

- ✅ **新增** (規範 #11 只增不毀): Section 11-21 全部為新增
- ✅ **保留** (Section 0-10): 完整保留, 0 修改
- ✅ **不修改 production**: Framer / GoaaDashboard / api.py / db.py / Worker Agent 0 變更
- ✅ **不 Publish**: 文檔層改動, 不觸發 production 部署
- ✅ **不開新 cooldown**: docs 文檔修改不在規範 #15 適用範圍 (規範 #15 適用基礎設施移除)

---

## 12. Provider-First Commercial Strategy

### 12.1 戰略核心定位

GOAA.AI 的長期願景是:

```
AI Runtime OS
AI Worker Economy
Skill Marketplace
Client + Provider + Worker 三層生態
```

但**短期不能直接做完整平台**.

前 6 個月唯一商業主線是:

```
Provider AI 工作台
```

### 12.2 目標客群 (前 6 個月唯一聚焦)

**主目標**: 北美華人專業服務者 (Solo Provider / 小型 Provider 團隊)

具體職業:
- 保險經紀 (Insurance Broker) — PFA / Term / IUL / Whole Life
- 房產經紀 (Real Estate Agent) — Buyer Agent / Listing Agent
- 稅務專業 (Tax Professional) — CPA / EA / Tax Preparer
- 會計 (Accountant) — Bookkeeper / Small Business CPA
- 移民顧問 (Immigration Consultant) — Family / Work / Investment
- 貸款顧問 (Loan Officer) — Mortgage / Refinance
- 其他自僱型專業服務者

### 12.3 短期核心產品

**不是**全民 AI 平台, **而是**:

```
幫 Provider 自動整理文件、分析客戶資料、生成 follow-up、表格草稿
與專業服務工作流的 AI 自動化工作台.
```

### 12.4 為什麼 Provider 先行 (戰略邏輯)

#### 對比 Client Plus vs Provider Pro

| 維度 | Client Plus $19.99/月 | Provider Pro $39.99/月 |
|---|---|---|
| **付費意願** | 普通用戶初期猶豫 (個人開支考量) | 強烈 (Provider 收入來自成交, 效率即金錢) |
| **價值感知** | 「我為什麼要付 AI?」 | 「多接 1 個客戶就回本」 |
| **使用頻率** | 偶發 (一年幾次 IRS / 房貸) | 高頻 (每天接客戶) |
| **流失率** | 較高 (任務完成就取消) | 較低 (持續工具依賴) |
| **支撐單客 LTV** | 低 (~$50-100/年) | 高 (~$480/年, 5 年留存 $2,000+) |

#### Provider 付費邏輯 (具體場景)

GOAA 幫 Provider:
- 多接 1 個客戶 (Lead 撮合 + 客戶 intake 自動化)
- 少花 5 小時整理資料 (文件 OCR + 結構化提取)
- 更快跟進客戶 (Auto follow-up + CRM 工作流)
- 自動生成表格草稿 (TurboTax / TaxAct / Excel)
- 提高成交效率 (AI 預先準備方案草稿, Provider 審核即可發送)
- 減少重複文書工作 (Skill 標準化高頻流程)

**$39.99/月 ROI 計算**:
- 假設 Provider 平均單客成交價 = $500-2000
- 多接 1 個客戶 = +$500-2000
- 訂閱費 $39.99/月 = $479.88/年
- **單客回本: 1 個客戶即過**

### 12.5 GOAA 的市場差異化定位

市面上已有方向:
- 通用 AI Agent (ChatGPT / Claude Desktop / Perplexity)
- RPA 自動化 (UiPath / Automation Anywhere)
- 多模型對話 UI (LibreChat / OpenWebUI)
- 本地 AI 硬體 (Apple Intelligence / Nvidia DIGITS)
- 去中心化算力 (io.net / Akash)
- Agent workflow 平台 (n8n / Zapier AI)

GOAA **不正面競爭通用 AI Agent 或企業 RPA**.

GOAA 的差異化:

```
華人 / 北美專業服務市場 (Underserved)
+
Client / Provider / Worker 三層角色 (Unique Stack)
+
本地 AiKa Box 實體執行 (Compliance + Anti-bot)
+
雲端 Runtime OS 調度 (Cross-device Orchestration)
+
Worker Credits 成本結算 (Internal Economy)
+
Skill / 成果市場 (Asset Layer)
+
保險、房產、稅務、移民、會計等高頻專業服務場景 (Vertical Depth)
```

GOAA 的第一戰場**不是** Horizontal AI, **而是**:

```
Vertical AI Labor OS for Service Providers
中文: 面向專業服務者的垂直 AI 勞動力操作系統
```

### 12.6 短期產品定位修正 (對外敘事)

#### 官網 V2.0 首頁第一版

**不應**: 一上來只打「全球 Physical AI Runtime OS」這種過於宏大的敘事

**而應**: 第一版定位調整為

```
GOAA.AI 是給華人專業服務者的 AI 自動化工作台.
```

#### 中文短版文案

```
GOAA.AI 幫保險、房產、稅務、移民、會計等專業服務者,
用 AI 自動整理文件、分析客戶資料、生成跟進內容與表格草稿,
並通過本地 Worker / AiKa Box 執行真實任務.
```

#### 英文短版文案

```
GOAA helps service professionals automate client intake, document workflows,
follow-ups, and local task execution through AI Workers and local runtime nodes.
```

#### 長期願景保留 (Footer / About / Roadmap)

```
AI Runtime OS · AI Worker Economy · Skill Marketplace
```

長期願景**保留**, 但**首頁首屏和前 6 個月銷售話術**必須先聚焦 Provider.

---

## 13. Product Boundary: Worker / Provider / Client

### 13.0 三端最終邊界 (一句話定義)

```
Worker 是內部生產線, 成熟後開放給開發者生產 Skill.
Provider 是專業服務工作台, 負責接單、跟單、調用專業 Skill、審核並交付結果.
Client 是需求方平台, 負責提出需求、查看訂單進度、與 Provider 互動, 並使用生活化 Skill.
```

更短的一句:

```
Worker 負責生產能力, Provider 負責交付服務, Client 負責提出需求與查看結果.
```

---

### 13.1 Worker 當前定位

#### 當前階段 (Phase 1, 內部生產線)

```
Worker = 內部生產線
```

Worker 負責:
- 內部任務調度
- Worker V5.0 開發
- Runtime 測試
- 技能開發
- 工具鏈驗證
- 成果市場的早期生產
- GOAA 自身系統迭代

**Worker 現階段不面向普通 Client 開放**.  
**Worker 現階段也不是 Provider 日常使用的複雜開發工具**.

#### 未來階段 (Phase 5+, 開發者平台)

當以下能力成熟後, Worker 可逐步開放給外部開發者:

- Worker Runtime
- 任務審計
- Credits 結算
- 權限治理
- Skill 版本管理
- Skill 測試與審核
- 安全沙箱
- 回滾機制

未來定位:

```
Worker = 開發者生產平台
```

但這是**後期路線**, **不是當前商業 MVP**.

#### 戰略順序鐵律

當前正確順序:

```
內部 Worker V5.0 生產線先跑通
↓
Provider AI 自動化工作台先產生現金流
↓
Worker 成熟後再開放給開發者生產 Skill
```

---

### 13.2 Provider AI 自動化工作台定位

#### Provider 工作台 ≠ 開發者平台

Provider **不需要理解**複雜的:
- Worker Runtime
- Executor
- Credits 底層
- Skill 開發流程
- 版本管理
- 調度引擎
- Runtime 日誌

Provider 工作台**必須做到**:

```
簡單
直接
易用
能接單
能跟進
能調用技能
能處理文件
能生成草稿
能創造現金流
```

#### Provider 工作台對話框 (獨立於 Worker 開發環境)

Provider 工作台有**自己獨立的對話框**.

這個對話框的核心**不是**開發 Skill, **而是**:

```
上接 Client 訂單
下接 Skill Marketplace
中間由 AI 幫 Provider 完成專業服務流程
```

#### Provider 工作台主要功能

- 接收 Client 訂單
- 查看訂單狀態
- 與 Client 溝通
- 跟進訂單回覆
- 上傳 / 接收客戶文件
- 調用 Skill Marketplace 的付費專業 Skill
- 處理文件
- 整理客戶資料
- 生成 follow-up
- 生成方案草稿
- 生成表格草稿
- 由 Provider 最終審核後交付給 Client

**Provider 不直接開發複雜 Skill**.

#### Provider 典型使用流程

```
我收到一個客戶訂單
↓
AI 幫我整理資料
↓
我選擇一個專業 Skill
↓
系統處理文件 / 生成草稿
↓
我審核
↓
我回覆客戶
↓
訂單繼續推進
```

**一句話**:

```
Provider 工作台 = 接單 + 跟單 + 調用專業 Skill + 審核並交付客戶結果
```

---

### 13.3 Client 平台定位

#### Client 與 Provider 的關係

```
Client = 需求方 / 買方
Provider = 專業服務供給方 / 賣方
```

Client 平台**本質是買賣雙方的交換場景**, 不是複雜開發平台.

#### Client 主要需要

- 提出需求
- 上傳資料
- 查看 AI 初步分析
- 選擇是否連接 Provider
- 查看訂單進度
- 與 Provider 互動
- 查看 Provider 回覆
- 查看任務當前狀態
- 使用生活化 Skill
- 管理自己的文件與家庭事務

#### Client 端核心可見性

Client 應該能**清楚看到**:

```
我的訂單現在到哪一步了?
Provider 有沒有回覆?
我還需要補什麼資料?
AI 幫我整理出了什麼?
哪些任務已經完成?
哪些任務正在處理中?
```

#### Client 使用 Skill 的範圍

Client 可使用 Skill Marketplace, 但主要使用**生活化 Skill**, 不是專業開發 Skill.

**Client 可用 Skill 示例**:
- 家庭信件管理
- IRS / DMV / 銀行信件提醒
- 帳單整理
- 家庭文件分類
- 房貸壓力測試 (基礎版)
- 保險資料整理
- 家庭待辦提醒
- 生活文件摘要

#### Client 不需要看到的內容

Client **不需要**看到:
- Worker 調度
- Credits 成本細節
- Skill 開發流程
- Runtime 日誌
- 版本管理
- 技術 executor

**一句話**:

```
Client 平台 = 提需求 + 看進度 + 與 Provider 互動 + 使用生活化 Skill
```

---

### 13.4 三端關係對官網 V2.0 文案的影響

Portal V2.0 官網**不應**把三個平台混在一起.

首頁應讓訪客**快速理解**:

```
Client : 我有需求, 想找人幫我解決.
Provider : 我接訂單, 用 AI 和 Skill 提高服務效率.
Worker  : 內部生產線, 未來開放給開發者生產 Skill.
```

#### 當前商業階段官網主推順序 (鐵律)

```
1. Provider AI 工作台 (第一主推)
   ↓
2. AiKa Box / 本地 Worker Runtime (Provider 配套)
   ↓
3. Client 訂單進度與互動 (第二主推)
   ↓
4. Skill Marketplace Preview (展示未來)
   ↓
5. Worker Developer Platform (未來開放, 不強調)
```

#### 三端錯位禁忌

- ❌ **不要讓普通 Client 誤以為自己要管理 Worker**
- ❌ **不要讓 Provider 誤以為自己要開發 Skill**
- ❌ **不要讓 Worker 平台過早對外承諾開發者收益**

---

## 14. Skill Marketplace 分層

為避免 Client / Provider / Worker 混用, Skill Marketplace 必須**三層分類**:

---

### 14.1 Client Skill (生活化, 低複雜度, 低風險)

**面向**: 普通用戶

**例如**:
- 家庭信件管理
- 帳單提醒
- 文件分類
- 房貸壓力測試 (基礎版)
- 家庭保險資料整理
- 生活待辦總結
- DMV 文件提醒
- 醫療帳單分類

**Client Skill 原則**:

```
簡單
生活化
可一鍵啟用
不涉及專業最終判斷
價位: $0 / $2.99 / $4.99 / $9.99 月
```

---

### 14.2 Provider Skill (專業, 可審計, Provider 審核, 服務訂單)

**面向**: 專業服務者

**例如**:
- Insurance Needs Analysis (保險需求分析)
- IUL / Term 方案草稿
- 房產客戶跟進 (Real Estate Follow-up)
- 稅務文件整理 (Tax Document Triage)
- IRS Letter 初步分析
- 客戶 intake package
- AI follow-up 文案生成
- 表格草稿生成 (TurboTax / TaxAct 自動填表)
- Mortgage Stress Test (Provider 版)
- Lead 跟進自動化

**Provider Skill 原則**:

```
專業
可審計
Provider 最終審核 (AI 不替代專業判斷)
服務訂單導向
提升交付效率
價位: $4.99 / $9.99 / $19.99 月 (或 Pro 訂閱包含)
```

---

### 14.3 Worker / Developer Skill (後期, 面向開發者與 Worker 生產者)

**面向**: 後期開發者與 Worker 生產者

**例如**:
- 新 Skill 開發 (Skill Development Kit)
- Runtime 插件
- Browser automation workflow 模板
- OCR pipeline 模板
- 數據處理模板
- 行業自動化 workflow 模板

**Worker / Developer Skill 原則**:

```
開發者使用
需要權限治理
需要版本管理
需要測試與審核
後期開放 (Phase 5+)
價位: 開發者訂閱 / 分潤模式 (50/50 或更高)
```

#### Phase 1-2 階段鐵律

**當前階段 (Phase 1-2) 不要把 Worker / Developer Skill 暴露給 Client 或普通 Provider**.

理由:
- Client 看到會混淆 (「我要學開發?」)
- Provider 看到會覺得太複雜 (「我又不是程式員」)
- Worker 平台未成熟, 過早暴露會傷品牌

---

## 15. 前 6 個月鐵律

**前 6 個月只聚焦**:

```
Provider Pro + Worker Runtime
```

### 15.1 ❌ 不做清單

| 項目 | 為何不做 |
|---|---|
| 大規模 Client 市場 | Provider 未成熟前, Client 接不住訂單會傷品牌 |
| 公開 Skill Marketplace | Skill 池未足夠, 公開後 UI 空殼會丟用戶 |
| Worker 法幣 payout | SEC / FinCEN / 州監管未確認, 合規高風險 |
| 硬體量產 | 庫存風險高, 先用 Mini PC + GOAA Runtime |
| 自研聊天 UI | 浪費工程資源, 用 LibreChat / OpenWebUI |
| 複雜 drag-and-drop workflow editor | Provider 不需要, AI 對話即工作流 |
| 全行業同時鋪開 | 資源分散, 集中保險 / 房產 / 稅務先打透 |

### 15.2 ✅ 只做清單

| 項目 | 為何先做 |
|---|---|
| Provider 工作台 | 直接創造現金流 |
| 文件處理 (OCR + 結構化) | Provider 高頻痛點, AI 直接解決 |
| 客戶資料整理 (Client Intake) | Provider 接單第一步, 重複度高 |
| follow-up 文案 | Provider 提升成交率核心動作 |
| 表格草稿生成 | TurboTax / TaxAct / Excel 自動化, Provider 省時 |
| 本地 Worker PoC | AiKa Box 軟件版 (Mini PC + Runtime image) |
| Provider Pro $39.99/月收費測試 | 真實付費意願驗證 |

---

## 16. 第一個垂直場景建議

當前 Provider 客群覆蓋多個行業, 但**前 6 個月 MVP 必須選 1-2 個場景死磕**, 不全行業同時鋪開.

### 16.1 Priority A: 保險經紀場景 (Insurance Broker MVP)

**推薦作為第一個 MVP**.

#### 為什麼選保險經紀

| 維度 | 評估 |
|---|---|
| Tao 師兄熟悉度 | ✅ 熟悉 PFA / IUL / Term / Whole Life 場景 |
| 客單價 | ✅ 高 ($500-5000 commission per case) |
| follow-up 需求 | ✅ 多 (Underwriting / Renewal / Annual Review) |
| 文件處理量 | ✅ 多 (Application / Medical Records / Policy Docs) |
| 方案草稿價值 | ✅ 高 (Needs Analysis 直接影響成交) |
| 付費意願 | ✅ 強 (Provider 願為效率與成交率付費) |

#### 第一個產品 (Insurance MVP)

```
Insurance Client Intake + Needs Analysis Assistant
```

#### Insurance MVP 核心功能

- 收集客戶基本資料: 年齡、收入、家庭狀況、預算、目標
- 結構化整理客戶保險需求
- 生成初步保險方案草稿 (Term / IUL / Whole Life 對比)
- 生成 follow-up 話術 (Email / SMS / WeChat 三種格式)
- Provider 審核 + 個性化修改後發給客戶
- 保留完整 task_id / audit trail (Runtime Truth)
- 自動跟進 Underwriting 進度提醒
- Annual Review 自動提醒 + 預生成 Review 報告

#### Insurance MVP 對應 Skill

- Skill: "Insurance Needs Analysis Assistant" ($9.99/月 或 Pro 訂閱包含)
- 觸發場景: Provider 接到新客戶 → AI 結構化需求 → 生成草稿 → Provider 審核 → 發送
- ROI: 預估 Provider 單客 intake 時間從 45 分鐘 → 8 分鐘 (省 80%)

---

### 16.2 Priority B: IRS / 稅務信件場景 (Tax / IRS MVP)

**可作為第二個 MVP** (Insurance MVP 驗證後啟動).

#### 優點

| 優勢 | 細節 |
|---|---|
| 痛點強 | 用戶看到 IRS 信件第一反應是恐慌 |
| 文件明確 | CP2000 / CP12 / Audit Letter 等格式標準化 |
| OCR 價值高 | 信件多為 PDF, OCR + 風險分類自動化空間大 |
| 觸發真人 Provider | 高風險信件自動推薦 CPA / 稅務律師 |

#### 風險 (合規敏感)

| 風險 | 處理 |
|---|---|
| 合規更敏感 | 必須嚴格 disclaimer: AI 只做 OCR + 風險分類, 不做最終稅務建議 |
| 需要更嚴格邊界 | Provider Pro (持牌 CPA) 才能調用「IRS 回應草稿」Skill |
| 不得讓 AI 做最終稅務建議 | 戰略憲法第 6 章合規邊界鐵律 |

#### Tax / IRS MVP 對應 Skill

- Skill: "IRS Letter OCR & Risk Triage" ($4.99/月 Client, Pro 訂閱包含)
- Provider Skill: "IRS Response Draft Assistant" (Provider Pro 持牌 CPA 限定)
- 觸發場景: Client 上傳 IRS 信件 → AI OCR + 風險分類 → 高風險推薦持牌 Provider → Provider 審核草稿 → 發送

---

### 16.3 MVP 啟動順序鐵律

```
Phase 1: Insurance MVP (保險) 先打透
   ↓ (3-4 個月驗證)
Phase 2: Tax / IRS MVP (稅務) 加入
   ↓ (6 個月後)
Phase 3: Real Estate MVP (房產) 加入
   ↓
Phase 4: Mortgage MVP (貸款) 加入
   ↓
Phase 5: Immigration / Accounting / 其他垂直擴展
```

**不全行業同時鋪開**.

---

## 17. 三條破局原則

### 17.1 原則 1: 軟體先行, 硬體貼牌

#### ❌ 不要

- 一開始找工廠開模
- 壓硬體庫存
- 立刻賣 $999 硬體

#### ✅ 要

Phase 2 / Phase 3 的 AiKa Box 採用:

```
成熟 Mini PC
+
Linux / Xubuntu / Windows 11 Pro
+
GOAA Worker Agent Runtime (軟體)
+
遠程維護
```

#### 可選硬體 (不開模)

- 客戶現有舊電腦 (Provider 辦公室現存 PC)
- Mini PC (Beelink / Geekom / Lenovo Tiny 類設備)
- 內部測試機

#### 對外品牌統一

對外稱:

```
AiKa Box Runtime
```

**不一開始就重硬體**.

#### 真正賣點 (軟體 + 服務, 不是硬體本身)

- GOAA Runtime OS
- Worker Agent
- 本地文件處理 (OCR / Excel / TurboTax automation)
- Browser Automation (本地 IP 反爬 97%)
- Provider workflow hooks
- 遠程管理與維護
- 安全沙箱 (Docker / Snapshot)

---

### 17.2 原則 2: 以對話框包裝自動化腳本

#### ❌ 不要

- 急著寫複雜 workflow editor
- 自研聊天 UI (浪費 4-6 週工程資源)
- 重新發明對話氣泡輪子

#### ✅ 要

**前台**: 用成熟多模型 Chat UI

```
LibreChat (首選, MIT, plugin 系統成熟)
OpenWebUI (備胎, Ollama 生態強)
Big-AGI (備胎 2, UI 漂亮)
```

**GOAA 自建** (Runtime 護城河):

```
Task Router (規範 #27 Integration First 例外)
Worker dispatch
worker_events 事件流
Credits 成本結算
Runtime Truth 真相層
Provider workflow hooks
Skill / Achievement Marketplace hook
GOAA audit / replay / rollback
```

#### 典型流程 (對話框 = 入口, 後端 = 自動化)

```
Provider 在對話框說:
「幫我整理這個客戶 PDF, 生成保險需求分析草稿.」
        ↓
GOAA Chat Workspace (LibreChat fork) 接收
        ↓
Task Router 解析意圖
        ↓
Worker 執行: OCR / 摘要 / 模板填充
        ↓
返回草稿到對話框
        ↓
Provider 審核 + 修改
        ↓
Provider 點擊「發送給客戶」
```

#### 一句話原則

```
用對話框的皮, 包自動化腳本的骨.
```

---

### 17.3 原則 3: 前期 Credits 不提現

#### Credits 前期只做

```
任務成本計量
月費抵扣
使用量審計
內部結算
Quality Score 評估
Runtime 成本追蹤
```

#### Credits 前期禁止

```
❌ 法幣提現
❌ 固定收益承諾
❌ 投資回報宣傳
❌ Worker payout marketing
```

#### 為什麼禁止

避免:
- 非法集資 (SEC / 州監管)
- 收益承諾陷阱 (FTC unfair practices)
- 金融監管 (FinCEN / 各州 Money Transmitter License)
- 用戶誤解 (Credits ≠ cryptocurrency ≠ 證券)

#### Credits 真實定位

```
Credits 是任務完成的內部結算憑證,
不是金融投資回報, 不是數位資產, 不上交易所.
```

長期 (Phase 5+) 若考慮 Credits payout, 必須:
1. 律師意見書確認 (SEC + 州金融法 + FinCEN)
2. KYC / AML 流程完整
3. 用戶協議明確 (Terms of Service)
4. 不對外行銷 "投資回報"

---

## 18. 盈利點排序

### 18.1 第一收入點: Provider Pro (Phase 1, 最先賣)

```
$39.99/月
```

#### 核心能力 (Provider 立刻見效)

- Client intake automation (客戶 intake 自動化)
- 文件 OCR (PDF / 圖片 / 掃描件)
- 客戶資料摘要 (AI 結構化提取)
- follow-up 文案生成 (Email / SMS / WeChat)
- 表格草稿生成 (TurboTax / TaxAct / Excel)
- AI CRM (客戶分類 / 提醒 / 工作流)
- Provider 審核工作流 (AI 草稿 → Provider 修改 → 發送)

#### 真實成本 vs 訂閱費

- Runtime 成本: ~$8-15/Provider/月
- LLM API 成本: ~$5-10/Provider/月
- 總成本: ~$13-25/Provider/月
- **毛利率: ~37-67%** (健康)

---

### 18.2 第二收入點: Setup / Onboarding Fee (Phase 1, 一次性)

```
$199 - $999 一次性 setup fee
```

#### 服務內容

- 導入 Provider Profile (照片 / 證照 / 介紹)
- 建立表格模板 (TurboTax / Excel / Word)
- 建立 follow-up 模板 (Email / SMS / WeChat 三套)
- 配置文件處理流程 (Client 上傳 → OCR → 結構化)
- 配置 AI CRM (客戶分類 / 提醒規則)
- 配置本地 Worker (AiKa Box Mini PC 部署 + 遠程連線測試)
- 1 對 1 培訓 (2 小時 Zoom call)

#### 為何收 setup fee

- Provider 看到「立即上手」價值, 願付一次性
- 篩選真實意願 Provider (避免免費試用流失)
- 降低 Provider Pro 訂閱流失率 (沉沒成本心理)

---

### 18.3 第三收入點: AiKa Box Runtime 管理費 (Phase 2)

**先不賣硬體本體**.

先賣:

```
$49 - $99/月 software runtime
```

#### 部署方式 (硬體貼牌)

- 客戶自有 mini PC (Provider 辦公室現存)
- 客戶舊電腦 (省成本)
- GOAA 預裝 mini PC (帶 image 出貨, 不開模)
- 遠程維護 (SSH / Tailscale / TeamViewer)

#### Runtime 訂閱包含

- GOAA Runtime OS (Worker Agent + Task Router 本地版)
- 自動更新 (Skill / 模板 / 安全 patch)
- 24/7 監控 (心跳 + 健康度)
- 遠程故障診斷
- Skill 同步 (Marketplace 訂閱的 Skill 自動部署到本地)

---

### 18.4 第四收入點: Provider Skill Library (Phase 2 後期)

等高頻流程被驗證後, 再做**小訂閱** (Skill Marketplace 早期版本).

#### 候選 Skill (按驗證優先級)

```
IRS Letter Skill (Tax 場景)
Insurance Needs Analysis Skill (Insurance 場景)
Real Estate Follow-up Skill (房產場景)
Mortgage Stress Test Skill (貸款場景)
Client Intake Assistant (跨行業通用)
Annual Review Report (Insurance / Tax 通用)
```

#### 價格測試 (按 Skill 複雜度)

```
$2.99 / 月 (Light Skill, 單一功能)
$4.99 / 月 (Standard Skill, 多步流程)
$9.99 / 月 (Professional Skill, 行業專業)
$19.99 / 月 (Premium Skill, 跨行業套件)
```

#### Skill Marketplace 分潤 (戰略憲法 8.3)

```
50/50 (Platform / Worker-Developer)
```

但 Phase 2 階段, 前 5-10 個 Skill 由 GOAA 內部 Worker 開發 (Worker = 內部生產線), 等成熟後再開放外部開發者.

---

### 18.5 第五收入點: Client Plus (Phase 3, 後置)

```
$19.99/月
```

#### 為何後置

**Client 需要足夠 Provider 接得住**.

如果 Phase 1-2 階段 Client Plus 上線, 但 Provider 池不足 (例如 < 50 個活躍 Provider), Client 上傳需求後**無人接單**, 會嚴重傷品牌.

正確順序:
1. Phase 1: Provider Pro $39.99/月 上線, 累積 50-100 Provider
2. Phase 2: Setup Fee + Skill Library 增加 Provider 黏性
3. Phase 3: Client Plus $19.99/月 上線, Provider 池足夠接得住

---

### 18.6 第六收入點: Worker Credits / 成果市場 (Phase 5+, 長期閉環)

**長期閉環, 前期只做成本與抵扣, 不做 payout**.

#### Phase 1-4 Credits 範圍

- 任務成本計量 (Runtime + LLM)
- 月費抵扣 ($39.99 = 3,990 Credits)
- 使用量審計 (Skill 調用次數)
- Quality Score 評估
- 內部結算

#### Phase 5+ Credits 擴展 (需律師意見書)

- 外部開發者 Skill 分潤 (50/50)
- Worker Developer 平台開放
- 成果市場 (Achievement Marketplace)
- **可能**的 Credits payout (合規確認後)

**前期絕對不做 payout**, 避免 SEC / 州金融監管風險.

---

## 19. 五步打穿路線圖

### 19.1 Phase 1: 完成 Worker V5.0 生產線 (現在 - 最近 1-2 週)

#### 目標

```
GOAA 自己能穩定派任務、執行任務、回報任務.
```

#### 必做

- db.py 物理審查 (V4.1-W0)
- tool_invocations 雙寫
- exec_shell_inventory
- file_read
- git_status
- docker_status
- dispatch_task async
- worker_events 事件流
- Runtime Truth (真實狀態鎖)

#### 驗收標準

```
同一個任務, QwenPaw 能做, GOAA Worker 也能做.
```

---

### 19.2 Phase 2: 官網 V2.0 文檔隔離儲備 (本任務 + 已完成)

#### 已交付

- `docs/marketing/GOAA_PORTAL_CONTENT_MATRIX_V2.md` Section 0-10 已 push (commit 28c574f, 2026-05-19 01:32 PT)
- 加入 Provider-First Strategy 與三端產品邊界 (本次修訂 Section 11-21)

#### 官網對外要先突出

```
Provider AI 工作台 (第一主推)
本地 Worker / AiKa Box (Provider 配套)
文件與客戶流程自動化 (Provider 核心痛點)
```

**不是**一開始只講宏大的全球 AI 勞動力帝國.

---

### 19.3 Phase 3: Provider AI 工作台 MVP (下週 - 接下來幾週)

#### 入口部署

```
Fork LibreChat (首選, MIT, plugin 系統成熟)
部署在 AiKa-2 (192.168.1.208, Xubuntu, 11GB RAM)
```

#### 第一批功能 (Insurance MVP 優先)

- PDF 上傳 (拖拉到對話框)
- OCR (本地 Tesseract / Cloud Vision)
- 客戶資料摘要 (AI 結構化提取)
- follow-up 文案 (Email / SMS / WeChat)
- 保險 / 房產 / 稅務方案草稿
- 任務進度顯示 (Worker dispatch status)
- Provider 審核後輸出 (一鍵發送)

#### 第一批用戶 (內測, 人工 onboarding)

- PFA 保險團隊 (Tao 師兄熟悉的)
- 房產經紀朋友 (1-2 個試水)
- 稅務 / 會計朋友 (1-2 個試水)

#### 第一個收費

```
$39.99/月 Provider Pro
+
$199 setup fee (內測階段試點)
```

可先**人工 onboarding**, 不必完全自助化.

---

### 19.4 Phase 4: AiKa Box Software Kit (MVP 驗證後)

#### 時間

Provider Pro 內測驗證 (5-10 個付費 Provider 留存) 之後啟動.

#### 不做 (規範 #11 + 17.1)

- ❌ 不先開模
- ❌ 不先量產
- ❌ 不壓硬體庫存

#### 要做

```
Mini PC (Beelink / Geekom / Lenovo Tiny)
+
GOAA Runtime image (預裝 Worker Agent + Skill)
+
Provider 辦公室部署
+
遠程維護
```

#### 收費

```
$49 - $99/月 Runtime 管理費
```

#### 測試項目

- 本地文件夾 OCR (Office 共享文件夾)
- 本地瀏覽器 automation (政府 / 銀行網站)
- 本地 IP 通過率 (vs 雲端 IP)
- 桌面軟體控制 (TurboTax / TaxAct / Excel)
- 局域網文件處理 (跨辦公室電腦)

---

### 19.5 Phase 5: 高頻流程資產化 (Skill Marketplace 早期)

#### 觸發條件

當 **10 個 Provider 都在反覆做同一件事**, 就封裝 Skill.

#### Skill 候選 (按 Provider 反饋優先級排序)

- IRS Letter Summary Skill
- Insurance Needs Analysis Skill
- Real Estate Follow-up Skill
- Mortgage Stress Test Skill
- Client Intake Skill
- Annual Review Skill
- DMV / 移民文件 Skill (跨行業通用)

#### 先做 (內部驗證階段)

```
Provider Skill Library
(GOAA 內部 Worker 開發, 不開放外部)
```

#### 再做 (公開 Marketplace 階段, Phase 5 後期)

```
公開 Skill Marketplace (滑動啟停)
月費訂閱 ($2.99 - $19.99)
50/50 分潤 (Platform / Worker-Developer)
成果市場 (Achievement Marketplace)
Worker Credits (內部結算)
```

#### 觸發外部開發者開放條件

- 50+ 個 Skill 內部驗證成功
- Worker 平台技術成熟 (Runtime / Audit / Rollback)
- 律師意見書完成 (合規邊界明確)
- 外部開發者經濟模型驗證 (50/50 分潤可持續)

---

## 20. 合規與風險控制

### 20.1 鐵律 1: 不承諾收益

所有 Credits、Worker、AiKa Box 收益**必須標明**:

```
示例估算, 非收益保證.
```

#### 違反案例 (禁止)

- ❌ "Worker 每月穩定收入 $125"
- ❌ "Provider Pro 保證多接 5 個客戶"
- ❌ "AiKa Box 8 個月回本"
- ❌ "Skill 訂閱者增長保證 1000+/月"

#### 合規措辭 (鼓勵)

- ✅ "示例: RTX 4060 + 100 任務/月, 估算 $125/月 (基於假設, 非保證)"
- ✅ "Provider Pro 不保證 Lead 數量, 實際成單依 Provider 自身專業判斷"
- ✅ "AiKa Box 回本期 6-12 個月 (依使用密度而異)"

---

### 20.2 鐵律 2: 不替代專業建議

所有保險、稅務、投資、法律場景**必須標明**:

```
AI 做整理與分析, Provider 做專業判斷.
```

#### 適用場景

- IRS / 稅務內容 (AI 不做最終稅務建議)
- IUL / Term Insurance (AI 不做最終保險建議)
- Mortgage / 房貸 (AI 不做最終貸款建議)
- Immigration / 移民 (AI 不做最終法律建議)
- 投資 / 退休規劃 (AI 不做最終投資建議)

#### 邊界執行 (產品層)

- 每個 AI 回應底部自動加 disclaimer
- 高風險場景自動觸發「請諮詢持牌專業者」提示
- Skill Marketplace Provider Skill 標明「Provider 最終審核」

---

### 20.3 鐵律 3: 不急著硬體量產

**前期**:

```
software runtime + mini PC (貼牌, 不開模)
```

**避免**:
- 硬體庫存壓力
- 模具開發 6-12 個月延遲
- 硬體 ROI 不確定

**Phase 5+** 若驗證大量需求 (1000+ Provider Pro 訂閱), 再考慮自有硬體開模.

---

### 20.4 鐵律 4: 不自研聊天 UI

**使用**:

```
LibreChat (首選, MIT)
OpenWebUI (備胎, Ollama 生態)
```

**GOAA 自建** (護城河, 不假手他人):

```
backend hooks / Worker / Credits / Governance / Runtime Truth
```

**理由** (規範 #27 Integration First):
- 對話 UI 開源世界已成熟, 4-6 週工程資源不浪費
- GOAA 核心競爭力在 Runtime / Worker / Credits, 不在對話氣泡
- Fork LibreChat 1 天 PoC 可跑, 自研 6 週都未必跑通

---

### 20.5 鐵律 5: 不做 Credits 提現

**前期只做**:

```
抵扣、成本、審計、內部結算
```

**禁止** (Phase 5 前):

```
法幣提現
固定收益承諾
投資回報行銷
Worker payout marketing
```

**Phase 5+ 開放條件**:

```
律師意見書完成 (SEC + 州金融 + FinCEN)
KYC / AML 流程完整
用戶協議明確 (Terms of Service)
不對外行銷 "投資回報"
```

---

## 21. Final Action Principle (最高行動原則)

### 21.1 第一原則 — 三端職責定義

```
Worker 負責生產能力,
Provider 負責交付服務,
Client 負責提出需求與查看結果.
```

### 21.2 第二原則 — Provider-First 鐵律

```
拋棄全民 AI 幻想,
前 6 個月死磕每月 $39.99 的華人 Provider AI 自動化工作台.

等 Worker 真正能幫 Provider 處理文件、跟進客戶、生成草稿並創造現金流,
再把它升級成 GOAA.AI 的 AI Runtime OS 與 AI 勞動力平台.
```

### 21.3 戰略順序鐵律 (永不調亂)

```
第一步: Worker V5.0 內部生產線先跑通
第二步: Provider AI 自動化工作台先產生現金流
第三步: AiKa Box / 本地 Worker Runtime 做 Provider 場景 PoC
第四步: 高頻 Provider 流程沉澱為 Skill
第五步: Client 平台承接訂單與生活化 Skill
第六步: Skill Marketplace / 成果市場逐步開放
第七步: Worker 成熟後再開放給外部開發者
```

**一句話**:

```
先有生產線, 再有工作台;
先有 Provider 現金流, 再有 Client 平台;
先有內部 Worker 成熟, 再開放開發者.
```

---

## 22. 交付回報清單 (對齊 SUPREME DIRECTIVE 19 點)

| # | SUPREME 要求 | 本次交付 |
|---|---|---|
| 1 | 是否更新 `docs/marketing/GOAA_PORTAL_CONTENT_MATRIX_V2.md` | ✅ Section 11-21 新增 |
| 2 | 是否加入 Provider-First Strategy | ✅ Section 12 完整 |
| 3 | 是否加入 Worker / Provider / Client 三端產品邊界 | ✅ Section 13 完整 |
| 4 | 是否保留 Portal V2.0 原始內容矩陣 | ✅ Section 0-10 完整保留, 0 修改 |
| 5 | 是否明確 Worker 當前是內部測試生產線 | ✅ Section 13.1 完整 |
| 6 | 是否明確 Provider 工作台不是開發者平台 | ✅ Section 13.2 完整 |
| 7 | 是否明確 Client 平台是需求方入口 | ✅ Section 13.3 完整 |
| 8 | 是否明確 Skill Marketplace 三層分類 | ✅ Section 14 完整 |
| 9 | 是否明確前 6 個月聚焦 Provider Pro | ✅ Section 15 + 12.1 + 21.2 |
| 10 | 是否明確 Client Plus 後置 | ✅ Section 18.5 |
| 11 | 是否明確公開 Skill Marketplace 後置 | ✅ Section 14.3 + 19.5 |
| 12 | 是否明確 Worker Credits 不做法幣提現 | ✅ Section 17.3 + 20.5 |
| 13 | 是否加入軟體先行、硬體貼牌原則 | ✅ Section 17.1 + 20.3 |
| 14 | 是否加入 LibreChat / OpenWebUI 包裝自動化腳本策略 | ✅ Section 17.2 + 20.4 |
| 15 | 是否加入 Provider Pro / Setup Fee / Runtime 三個近期盈利點 | ✅ Section 18.1 + 18.2 + 18.3 |
| 16 | 是否沒有修改 production | ✅ 0 production 變更 |
| 17 | 是否沒有 Publish Framer | ✅ 0 Framer Publish |
| 18 | 是否沒有修改 api.py / db.py / Worker Agent | ✅ 0 程式碼變更 |
| 19 | Git commit hash | 待 push 後填入 |

---

**Provider-First Strategy Update 簽發**: 2026-05-19 (PT)  
**修訂規模**: Section 11-21 新增, ~1,400 行 / ~36 KB  
**規範遵守**: #11 只增不毀 ✅ / #21 拆短 ✅ / #28 不靜默 ✅ / #36 v2 真實狀態 ✅  
**SUPREME DIRECTIVE 19 點交付清單**: 18/19 完成 (Commit hash 待 push 後補)

# 拋棄全民 AI 幻想, 前 6 個月死磕 Provider Pro $39.99/月. 先有生產線, 再有工作台; 先有 Provider 現金流, 再有 Client 平台.
