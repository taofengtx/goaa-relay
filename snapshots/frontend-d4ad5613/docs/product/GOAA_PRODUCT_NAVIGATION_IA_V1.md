# GOAA.AI Product Navigation IA & UI Alignment Spec V1.1

> **狀態**: 產品設計文檔 / IA 對齊階段。僅文檔, 不寫代碼、不部署、不改 GoaaDashboard.jsx / main.py、不碰 secret。
> **本文定位**: GOAA 後續 Cloud Dashboard / Local Console / Provider Workspace / Worker Studio / Clients Portal 的統一資訊架構基準。
> **圖片性質**: 設計方向參考, 非代碼實現截圖。圖中金額/節點數/任務數/日期/IP/性能數據均為 UI mock 示例, 不代表真實運營數據。

---

## 0. 最終口徑

GOAA 的用戶交互入口不再是單一 dashboard, 而是**五端統一產品體系**:
```
Command Center   = 雲端總控
AiKa-Box Console = 本地執行端
Worker           = AI 開發端
Providers        = 服務商端
Clients          = 客戶端
```
統一智能交互模塊 = **AI Workspace**(五端皆有, 權限/可見內容各異)
統一智能執行實體 = **AI Agents**(所有端可調用, 不再作為單獨「人類角色端」)

產品體驗目標:
- 客戶(Clients)看到的是簡單可信的服務入口
- 服務商(Providers)看到的是案件與審核流程
- 開發端(Worker)看到的是 Skill/Workflow/Adapter 生產工具
- 本地(AiKa-Box Console)看到的是本地主權與運行狀態
- 總控(Command Center)看到的是平台總控與雲地調度

---

## 1. 最高命名決策(全文統一)

| 舊命名(廢止) | 新命名(正式) | 原因 |
|---|---|---|
| Agents(執行代理端) | **Providers(服務商端)** | Agent 留給 AI 系統內部智能執行實體, 避免概念衝突 |
| Providers(供應商端) | **Worker(AI 開發端)** | 貼合 Worker Economy + Skill Marketplace 戰略 |
| Digital Human / 數字人(頂層導航) | **AI Agents** | 避免與真人/Provider/Worker/Agent 混亂 |

**AI Agents 定義**: GOAA 內外部可調用的智能代理能力集合, 含對話代理/任務執行代理/業務助理/視頻生成代理/Skill 開發代理/Provider 助理/Client 服務代理。
- 視頻類能力寫作: `AI Agents / Video Agent candidate`
- 開發類能力寫作: `AI Agents / Developer Agent candidate`
- 「數字人」不再作頂層產品名。

---

## 2. 產品入口結構

```text
GOAA.AI Command Center
         |
         |--- AiKa-Box Console   (本地執行端 / Edge Runtime / Local Sovereignty)
         |--- Worker             (AI 開發端 / Skill Builder / Workflow Graph / Adapter Lab)
         |--- Providers          (服務商端 / 案件處理 / Provider Review Hold / 服務交付)
         |--- Clients            (客戶端 / 我的任務 / 服務 / 文件 / 預約 / 帳單)
```
- Command Center = SaaS 雲端總控台(調度主權入口, 非單純監控面板)
- AiKa-Box Console = 本地主權入口(非 Cloud Dashboard 複製品)
- AI Agents = 所有端可調用的統一智能工作區能力

---

## 3. 五端定位

### 3.1 AiKa-Box Console(本地執行端)
定位: 本地模型/本地 RAG/本地任務/本地日誌/本地安全/本地離線能力。
主要用戶: AiKa-Box 擁有者、本地管理員、技術運維、GOAA 工程團隊。
核心職責: 本地節點身份 / 本地 RAG 狀態 / Aika Memory Context / 本地任務結果 / Stepper / Models / Skills / AI Agents Registry / Node Health / Logs / Local Settings / Cloud Binding。
**邊界(必須強調)**: 不做完整 Marketplace; 不做 billing; 不做全 fleet dashboard; 不暴露 RAG 正文; 不複製 Cloud Dashboard。

**5188 RAG 正文邊界(目標架構與安全要求)**: Local Console 5188 不得接收 raw RAG text。5188 只允許接收 sanitized telemetry DTO, 例如: chunk_id_hash · text_len · context_char_count · filter_stats · distance · task_id · redaction_status · duration_ms。
raw chunk text / raw context / Aika final prompt / raw RAG body 必須留在本地 worker / memory fetch 執行域中, 不得進入 5188 前端響應、browser console、runtime log、journal 或 /logs/recent。
Preferred implementation: isolate raw text handling in worker execution domain and expose only sanitized telemetry to Local Console.(此為目標邊界, 非聲稱「物理級進程隔離已完成」)

### 3.2 Worker(AI 開發端)
定位: AI Skill / Workflow / Adapter / AI Agents 的開發、測試、發布與審計端。
主要用戶: AI 開發者、Skill Builder、Workflow Designer、Adapter Engineer、內部工程團隊、授權外部 Worker。
核心職責: My Skills / Skill Builder / Workflow Graph Editor / Adapter Lab / AI Agents / ComfyUI Adapter candidate / Antigravity candidate / Sandbox·Tests / Publish / Audit / Settings。
產物: Skills / Workflow Graphs / Adapters / AI Agents / Test Reports / Marketplace Packages / Achievement Assets。
重點: 生產能力, 非服務客戶。

### 3.3 Providers(服務商端)
定位: 服務商處理客戶案件、執行專業服務、人工審核 AI 草稿、交付結果的業務工作台。
主要用戶: 保險經紀、稅務顧問、房產顧問、貸款顧問、升學顧問、移民顧問、信託顧問、企業服務 Provider。
核心職責: Dashboard / AI Workspace / Clients / Cases·Tasks / Intake / Workflow Progress / Provider Review Hold / Drafts & Reports / AI Agent Content / Documents / Compliance Notes / Settings。
**邊界(必須強調)**: 不直接編輯複雜 Workflow Graph; 不直接看 ComfyUI Canvas; 不直接看 raw RAG chunk; 不直接接觸 secret; 看到的是業務語言和審核入口。
**Provider Review Hold 是 Provider 端最核心控制點** — 所有專業服務結果必須經人工審核後再交付客戶。

**AI Agent Content 合規邊界**: AI Agent Content 在 Provider 端僅代表 AI 輔助生成的草稿、視頻腳本、客戶跟進內容、營銷素材或內部工作建議。所有涉及稅務、保險、法律、投資、貸款、移民、房產、信託等專業判斷的內容, 必須進入 Provider Review Hold, 由持牌或合格 Provider 人工審核後, 才能交付給 Client。

### 3.4 Clients(客戶端)
定位: 客戶查看任務、上傳文件、預約服務、查看結果、與 AI Workspace 交互的入口。
主要用戶: 個人/企業/家庭客戶、Provider 的終端客戶。
核心職責: Home / AI Workspace / 我的任務 / 我的服務 / 文件中心 / 預約日程 / 消息中心 / 帳單與套餐 / 收藏 / 設置。
**必須簡單、可信、少技術術語。**
不顯示: Workflow Graph JSON / RAG chunk / system logs / worker logs / ComfyUI node graph / internal audit details / secret / low-level model routing。
只顯示: 我的任務狀態 / 服務 / 文件 / 預約 / Provider·AI Agent 協作狀態 / 帳單套餐 / 消息提醒。

**AI Workspace 合規邊界**: Clients 端 AI Workspace 只用於: 需求收集 / 任務狀態查詢 / 文件上傳提醒 / 基礎解釋 / 服務導航 / 與授權 AI Agent 互動。
Clients 端**不得直接輸出**最終稅務、保險、法律、投資、貸款、移民、房產、信託等專業結論。涉及專業判斷的內容必須轉入 Provider Review Hold。

### 3.5 Command Center(雲端總控)
定位: 雲端 SaaS 總控台 / 全局任務路由 / 平台治理 / Marketplace / Fleet / Audit。
主要用戶: 平台管理員、企業管理員、運營團隊、審計團隊、Fleet 管理員。
核心職責: Dashboard / AI Workspace / Cloud Task Command Center / Workflow Graphs / Provider Workspace / Worker Network / AiKa-Box Fleet / Skill Marketplace / Achievement Marketplace / AI Agents / Audit Logs / Billing·Usage / System Settings。
必須承載 execution_target: `cloud | local | auto`(Run in Cloud / Run on My AiKa-Box / Auto Route)。

---

## 4. 統一導航結構(IA)

### AiKa-Box Console
總覽 · AI 工作區 · RAG 狀態 · Aika Memory Context · 任務結果 · Stepper/Workflow · Models · Skills · AI Agents · Node Health · Logs · Local Settings · Cloud Binding

### Worker
總覽 · AI 工作區 · My Skills · Skill Builder · Workflow Graph Editor · Adapter Lab · AI Agents · ComfyUI Adapter · Antigravity Candidate · Sandbox/Tests · Publish · Audit · Settings

### Providers
總覽 · AI 工作區 · Clients · Cases/Tasks · Intake · Workflow Progress · Provider Review Hold · Drafts & Reports · AI Agent Content · Documents · Compliance Notes · Settings

### Clients
首頁 · AI 工作區 · 我的任務 · 我的服務 · 文件中心 · 預約日程 · 消息中心 · 帳單與套餐 · 收藏 · 設置

### Command Center
總覽 Dashboard · AI Workspace · Cloud Task Command Center · Workflow Graphs · Provider Workspace · Worker Network · AiKa-Box Fleet · Skill Marketplace · Achievement Marketplace · AI Agents · Audit Logs · Billing/Usage · System Settings

---

## 5. AI Workspace 統一規則

五端在「總覽/Dashboard」下都加入 **AI 工作區 / AI Workspace**(五端統一交互模塊)。視覺與結構對齊現有雲端「AI 調度」頁, 但文字統一調整:

### 5.1 「節點」字樣改 AI AGENT(僅限 AI Workspace / AI 調度語境)
**僅在 AI Workspace / AI 調度語境**中:
節點 → AI AGENT; 執行節點 → 執行 AI AGENT; 節點實時回報 → AI AGENT 實時回報; 管理節點 → 管理 AI AGENT; 全部在線節點 → 全部在線 AI AGENT。

**以下語境必須保留 Node / Worker Node / AiKa-Box Node**(不改 AI AGENT):
AiKa-Box Fleet · Node Health · Local Node Identity · physical runtime node · logical execution node · Worker Node / Local Worker Appliance。

**詞彙邊界說明(避免命名衝突):**
- `AI Agent` = 智能任務代理 / 對話代理 / 業務代理 / 執行代理
- `Node / Worker Node` = 物理或邏輯運行節點
- `Worker` = AI 開發端產品入口
- `AiKa-Box` = 本地邊緣運行設備

不把 UI 統一改成 `AI WORKER / AGENT`, 避免重新製造命名衝突。

### 5.2 AI Workspace 支持選擇不同 AI Agent 對話
支持: 選擇 AI Agent / 與之對話 / 分派任務 / 查看回報 / 查看任務執行狀態。
示例 Agent: DeepSeek-V4-Flash · Claude · Qwen · Gemini · Research Agent · Tax Agent · Insurance Agent · Real Estate Agent · Legal Draft Agent · Video Agent candidate · Developer Agent candidate。(不同端可顯示不同可用 Agent)

### 5.3 按鈕「ON」→「執行」
`執行` = 把當前輸入作為任務分派給 AI Agent; `發送` = 普通對話消息。

### 5.4 AI Workspace 五端差異
- **Command Center**: 平台級調度 / Cloud·Local·Auto routing / Fleet 指令 / 全局 Agent 分派
- **AiKa-Box Console**: 本地 Agent 執行 / 本地 RAG·Memory Context 任務 / 離線執行 / 本地 task_result
- **Worker**: 協助開發 Skill / 生成測試腳本 / 調試 Adapter / 設計 Workflow Graph / 審查 redaction·security
- **Providers**: 協助處理案件 / 分析 intake / 生成草稿報告 / 準備 Provider Review Hold / 客戶跟進
- **Clients**: 提問 / 提交需求 / 查任務狀態 / 文件上傳提醒 / 與授權 Agent 互動(更簡單、少技術細節)

---

## 6. 五端能力矩陣

標註: Full / Limited / View Only / Hidden / N/A

| Capability | AiKa-Box Console | Worker | Providers | Clients | Command Center |
|---|---|---|---|---|---|
| AI Workspace | Full | Full | Full | Limited | Full |
| Workflow Graph | View Only | Full | Limited | Hidden | Full |
| Skills | View Only | Full | Limited | Hidden | Full |
| AI Agents | Limited | Full | Limited | Limited | Full |
| Provider Workspace | N/A | N/A | Full | N/A | Full |
| Client Management | N/A | N/A | Full | N/A | Full |
| Memory Context | Full | Limited | Hidden | Hidden | Limited |
| RAG Status | Full | Limited | Hidden | Hidden | Limited |
| Local Execution | Full | Limited | N/A | N/A | Limited |
| Cloud Routing | Limited | Limited | View Only | Hidden | Full |
| Marketplace | View Only | Full | Limited | View Only | Full |
| Fleet Management | N/A | N/A | N/A | N/A | Full |
| Audit Logs | Limited | Full | Limited | Hidden | Full |
| Billing / Usage | N/A | Limited | Limited | Full | Full |
| Settings | Full | Full | Full | Full | Full |

(矩陣為設計基準, 實作時各端權限以此為準繩)

**Clients 端 Workflow Graph 可見性注釋**: Clients 的 Workflow Graph 保持 **Hidden**。Clients 可查看任務狀態, 但只能看到極簡 Stepper UI progress indicators, 例如: 資料收集 → AI 分析 → Provider Review Hold → 交付完成。
Clients **不得看到**: raw Workflow Graph / node graph / execution JSON / ComfyUI node graph / RAG chunk / system logs / worker logs / internal audit details。

---

## 7. Cyber-Noir Design System

### 視覺關鍵詞
Cyber-Noir / 黑底 / 青藍 accent / 等寬字體 / 玻璃質感卡片 / 狀態燈 / 霓虹邊框 / 多端統一 / Local·Cloud 一致風格。

### 顏色
```
Background:      #05080C / #0A0F14
Panel:           #0E151B / rgba(12, 20, 28, 0.86)
Primary Accent:  #00C8FF
Success:         #22C55E
Warning:         #FACC15
Danger:          #EF4444
Purple:          #A855F7
Text Primary:    #F5F5F5
Text Secondary:  #A1A1AA
Border:          rgba(0, 200, 255, 0.25)
```

### 字體
```
Primary UI Font: Inter / system-ui
Data / Code Font: JetBrains Mono / SF Mono / Menlo / monospace
```

### 組件清單
Sidebar · Header · Dashboard Cards · Status Chips · Progress Bars · AI Workspace Panel · Agent Selector · Execution Button · Chat Box · Live Report Panel · Workflow Stepper · Review Hold Badge · Sync Pending Badge · Coming Soon Panel。

---

## 8. 後續實施順序

- **Phase A — IA 文檔確認**: 完成本文檔。不寫代碼。
- **Phase B — Cloud Dashboard IA 重構設計**: 不動黃金版前提下, 先設計新導航 schema。保留 golden backup。
- **Phase C — Local Console Cyber-Noir Skin**: 只對齊視覺, 不複製 Cloud Dashboard 功能。Local Console 保持本地主權入口。
- **Phase D — AI Workspace 組件化**: 設計成統一組件, 五端複用, 每端權限/可見內容不同。
- **Phase E — 代碼實現**: 進入前必須 Tao 單獨確認。必須先 branch、diff、審計、rollback。

---

## 9. 設計原則(七項)
一致性(統一導航與元件)· 可擴展性(模塊化設計)· 可用性(降低使用者學習成本)· 即時性(即時狀態與反饋)· 安全性(多層安全防護, 保障資料與權限)· 專業性(清晰結構與呈現專業可信)· **可審計性**(所有任務、AI Agent 調用、Provider Review Hold、Workflow 執行、Cloud/Local/Auto 路由、Skill 發布、Adapter 測試, 都必須留下可追溯審計記錄; 但審計記錄不得洩露 secret、RAG 原文、客戶隱私正文或 raw prompt)。

---

## 10. 圖片對齊說明(誠實聲明)
本輪六張圖(Clients Portal / Cloud Command Center / 五端總覽 / AiKa-Box Local Console / Provider Workspace / Worker Studio)為**設計方向參考, 非代碼實現截圖**。
圖中金額/節點數/任務數/日期/IP/性能數據均為 **UI mock 示例, 不代表真實運營數據**。
AI Agents / ComfyUI / Antigravity / Video Agent / Developer Agent 標 candidate, **非已上線完整商業能力**。

**Candidate / Credits / Pricing 占位邊界**: 所有 Candidate 能力(含 ComfyUI Adapter candidate / Antigravity candidate / Video Agent candidate / Developer Agent candidate / WonderClip·萬境一刻 candidate), 在 API / auth / pricing / commercial terms / IO format 未完成核驗前:
- 不得寫成 production available
- 不得寫成 Provider paid callable
- 不得顯示真實 USD 金額
- 不得顯示真實扣費金額
- 不得承諾生成成本、收益、ROI、分潤
- UI 只能顯示 `candidate` / `sandbox` / `pending verification` / `usage accounting placeholder`
C2 / Memory Context 在 Local Console 顯示脫敏統計, **不暴露 RAG 正文**。/rag/chat 第一版不開放。

---

*GOAA Product Navigation IA V1.1 — 五端統一產品體系 — Cyber-Noir Design System — 設計文檔, 不寫代碼*
