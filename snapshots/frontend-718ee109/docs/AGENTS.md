# AGENTS.md — GOAA.AI 角色命名統一 + AI 工作者分工

**版本**: V1.0
**最後更新**: 2026-05-16
**配套**: `docs/business/GOAA_BUSINESS_MODEL_V1.md` (戰略憲法主檔)
**狀態**: 命名規範強制執行 (Database / Code / Doc 統一)

## 📌 文件角色標籤 (規範 SUPREME 治理)

```text
本文角色: 命名規範源 (Database / Code / Doc 統一)
本文類型: Naming Charter
是否允許直接執行: 否
是否允許修改 Production: 否 (僅文檔)
是否需要 Tao 拍板: 是 (命名修改)
最高參考來源: GOAA_BUSINESS_MODEL_V1.md 第 3 章
```

---

## 🎯 為什麼需要 AGENTS.md

GOAA.AI 系統內**同時存在**:
- 真人服務者 (房地產經紀 / 保險經紀 / 律師等)
- AI Agent (LLM 智能體, ChatGPT / Claude / DeepSeek 等)
- AI Worker (執行節點, AiKa-1 / AiKa-2 / do-cloud-* 等)
- 用戶 (Client)

如果命名混淆, 會造成:
- 資料庫 schema 混亂 (agents 表既存真人又存 AI)
- API 設計混亂 (`/api/agents` 是給誰用)
- UI 文案混亂 (用戶搞不清楚誰是誰)
- 後期大量返工

**所以 GOAA.AI 強制統一命名規範**。

---

## 📋 命名規範總表 (強制執行)

| 概念 | 統一命名 | 禁止使用 | DB Table | 範例 |
|---|---|---|---|---|
| 用戶 / 客戶 | **Client** | user, customer | `clients` | 「Tao 是 Client」 |
| 真人專業服務者 | **Provider** | Agent (混淆 AI), broker | `providers` | 「張會計師是 Provider」 |
| AI 智能體 | **Agent** (= AI Agent) | (不可指真人) | `v4_agents` 或 `ai_agents` | 「DeepSeek-V4-Flash 是 Agent」 |
| AI 數字勞動力節點 | **Worker** | node, slave, peer | `workers` | 「AiKa-1 是 Worker」 |
| 可售賣能力 | **Skill** | feature, plugin, capability | `skills`, `skill_marketplace` | 「家庭信件管理 Skill」 |
| Worker 生產成果 | **Achievement** | output, result | (含於 skill_marketplace) | 「視頻生成 Achievement」 |
| 任務 | **Task** | job, work_item | `tasks` | 「health_check Task」 |
| 派發計劃 | **Dispatch Plan** | plan, sched | `dispatch_plans` | 「P0 任務 Dispatch Plan」 |

### 強制規則
- ✅ 真人服務者 = **Provider**, **永不**叫 Agent
- ✅ AI Agent (LLM) = **Agent**, **不可**指真人
- ✅ 執行節點 = **Worker**, 不叫 node
- ✅ 用戶 = **Client**, 不叫 user (DB schema 已固定)

### 違反例子 (禁止)
- ❌ `agents` 表同時存「房產經紀」+「ChatGPT」(混用)
- ❌ API `/api/agents/list` 返回真人經紀 (應該是 `/api/providers/list`)
- ❌ UI 文案「我們的 AI Agent 王律師為您服務」(真人應叫 Provider)
- ❌ Code variable `agent_name = "AiKa-1"` (節點應叫 worker)

---

## 🏛️ 三層角色詳細定義

### Client (用戶 / 需求方)

**對象**:
- 普通家庭 / 華人用戶 / 小企業
- 個體用戶 / 海外華人 / 學生
- 自由職業者 / 商業客戶

**特點**: 有現實需求, 但沒有專業能力或時間處理

**商業層**:
- Free ($0): 對話 / 上傳資料 / AI 分析 / 任務建議
- **Plus ($19.99/月)**: AI + 真人 Provider 連接

**DB Table**: `clients`

```sql
CREATE TABLE clients (
    client_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100),
    email VARCHAR(255) UNIQUE,
    tier VARCHAR(20) DEFAULT 'free',  -- free / plus
    -- ...
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

### Provider (真人專業服務者)

**對象**:
- 房地產經紀 / 保險經紀 / 稅務顧問
- 會計師 / 移民顧問 / 律師
- 金融顧問 / 醫療顧問 / 教育顧問

**特點**: 真人 + 專業執照 + 線下服務能力

**商業層**:
- Free ($0): AI 測試 / 上傳文檔 / CRM
- **Pro ($39.99/月)**: 接客戶 + CRM + 自動化
- **AiKa Box ($999 硬件 或 $99/月)**: 辦公室部署本地 AI Worker

**DB Table**: `providers`

```sql
CREATE TABLE providers (
    provider_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100),
    license_number VARCHAR(50),  -- 真人專業執照
    specialty VARCHAR(50),  -- real_estate / insurance / tax / law / immigration
    tier VARCHAR(20) DEFAULT 'free',  -- free / pro / aika_box
    -- ...
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

### Worker (AI 數字勞動力節點)

**對象**:
- 雲端 Worker (do-cloud-1/2/3)
- 本地 AiKa Box (aika-1, aika-2, ...)
- 開發 Worker (Runtime Worker, 自動化執行節點)

**特點**: 機器 + AI 能力 + 24/7 可調度

**商業層**:
- Worker 不付費, **Worker 賺 Credits**
- Credits 經濟: CPU/GPU/Token/Runtime/Skill 生產

**DB Table**: `workers`

```sql
CREATE TABLE workers (
    worker_id VARCHAR(50) PRIMARY KEY,  -- aika-1, aika-2, do-cloud-1
    type VARCHAR(20),  -- local / cloud / development
    status VARCHAR(20),  -- online / offline / maintenance
    ip_addr INET,
    capabilities JSONB,  -- ["health_check", "exec_shell", "browser_use"]
    credits_balance DECIMAL(12, 2) DEFAULT 0,
    -- ...
    last_heartbeat TIMESTAMPTZ
);
```

---

### Agent (AI 智能體, LLM)

**對象**:
- LLM 模型: DeepSeek-V4-Flash / Claude Sonnet 4.7 / Ollama Qwen 等
- 多 Agent 協作: GOAA 助手 / 客服 Agent / Coding Agent (v4_agents)

**特點**: 純軟體 + LLM 驅動 + 對話/決策能力

**DB Table**: `v4_agents` (或 `ai_agents`)

```sql
CREATE TABLE v4_agents (
    agent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50),  -- "GOAA 助手", "客服 Agent", "Coding Agent"
    model_id VARCHAR(50),  -- "deepseek-v4-flash", "claude-sonnet-4-7"
    system_prompt TEXT,
    tools JSONB,  -- ["task_status", "tasks_by_type"]
    -- ...
    created_at TIMESTAMPTZ
);
```

---

### Skill / Achievement (可售賣能力 + 成果資產)

**對象**:
- Worker 生產的可重複使用能力
- 例: 「家庭信件管理」 / 「房產視頻生成」 / 「IRS 信件分析」

**特點**: 數字資產 + 可訂閱 + 可版本化 + 可回滾

**DB Table**: `skill_marketplace` + `skill_subscriptions`

```sql
CREATE TABLE skill_marketplace (
    skill_id UUID PRIMARY KEY,
    name VARCHAR(100),
    target_user VARCHAR(20),  -- Client / Provider / Both
    price_monthly DECIMAL(10, 2),
    created_by_worker VARCHAR(50),  -- 開發 Worker
    -- ... (完整 schema 見 FUTURE_DDL_SKILL_MARKETPLACE.md)
);
```

---

## 🌐 API Prefix 命名規範 (SUPREME 項 3.2 強制)

**強制統一**: 所有 GOAA API endpoint 必須使用以下 prefix:

| 概念 | API Prefix | 範例 |
|---|---|---|
| Client | `/api/clients` | `GET /api/clients/{id}` |
| Provider | `/api/providers` | `POST /api/providers/leads` |
| AI Agent | `/api/ai-agents` | `GET /api/ai-agents/list` |
| Worker | `/api/workers` | `GET /api/workers/{id}/health` |
| Skill | `/api/skills` | `GET /api/skills/marketplace` |
| Achievement | `/api/achievements` | `GET /api/achievements/metrics` |
| Task | `/api/tasks` | `POST /api/tasks/dispatch` |
| Dispatch Plan | `/api/dispatch-plans` | `GET /api/dispatch-plans/{id}` |

### 禁止 (規範 SUPREME)
- ❌ `/api/agents` 返回真人 Provider (混淆 AI Agent 跟 Provider)
- ❌ `/api/users` (應該是 `/api/clients`)
- ❌ `/api/nodes` (應該是 `/api/workers`)

### 既有 API 對齊路徑
- `/api/v1/agents` (OpenClaw 現有) — V4.2 後重命名為 `/api/v1/ai-agents`
- `/api/v1/chat` — 保留, 內部使用
- `/api/v1/skills` — 對齊 SUPREME 規範

---

## 🗄️ DB Table 命名規範 (SUPREME 項 3.3 強制)

**Database table 命名統一**:

| 概念 | Table 名 | 狀態 |
|---|---|---|
| Client | `clients` | V5.0 規劃 |
| Provider | `providers` | V5.0 規劃 |
| AI Agent | `v4_agents` 或 `ai_agents` | ✅ 已存在 (`v4_agents`) |
| Worker | `workers` | V4.2 規劃 |
| Skill | `skills` / `skill_marketplace` | V4.3 規劃 |
| Skill 訂閱 | `skill_subscriptions` | V4.4 規劃 |
| Skill 計費流水 | `skill_billing_ledger` | V4.4 規劃 (SUPREME 項 7.2 新增) |
| Skill 版本 | `skill_versions` | V4.3 規劃 |
| Skill 反饋 | `skill_feedback` | V4.5 規劃 |
| Worker 事件流 | `worker_events` | V4.2 規劃 |
| Dispatch Plan | `dispatch_plans` | V4.2 規劃 |
| Task | `tasks` | ✅ 已存在 |

### ⚠️ 重要警告
- 上述 V4.2+ 表名為 **future DDL**, **不得直接執行** (規範 #11 + #15)
- 完整 DDL 見 `docs/architecture/FUTURE_DDL_SKILL_MARKETPLACE.md`
- 執行 migration 必須過 Tao + Claude + ChatGPT 三方審查 + 24h Cooldown

---

## 🤖 GOAA 多 AI Agent 工作分工

GOAA 系統內**多個 AI 同時工作**, 每個 AI 角色不同:

### Claude (架構設計師 + 任務拆解 + 文檔 PM)

**職責**:
- 系統架構設計 (V4.x / V5.0 演進)
- 任務拆解 (規範 #21 拆短)
- 文檔 PM (戰略憲法 + 規範體系 + Roadmap)
- Code review 與 patch 設計 (byte-exact)
- 規範體系演進與守護

**工具**:
- bash / str_replace / view / create_file
- web_search / web_fetch
- visualize / image_search

**特點**:
- 強推理 + 強規範意識
- 多輪對話記憶 (PG persistent)
- 規範 #24 嚴守 (不憑想像)
- 規範 #35 嚴守 (不自主升基準)

---

### ChatGPT (語音秘書 + 戰略總控)

**職責**:
- 語音輸入 → task.txt 寫入
- 戰略白皮書起草 (商業模式 / Roadmap)
- 三方協作機制 (Claude + ChatGPT + Tao)
- 跨會話戰略連續性

**特點**:
- 語音介面友好
- 戰略視野
- 跨平台知識整合

---

### Gemini (Planner)

**職責**:
- 中長期規劃
- 多方案對比分析
- 戰略路徑優化

**特點**:
- 規劃能力強
- (目前在 GOAA 中使用較少, 主要在 ChatGPT + Claude 主導)

---

### QwenPaw / OpenClaw (執行層 - 過渡狀態)

**現況**:
- QwenPaw v1.1.5 (Alibaba 閉源, AgentScope 框架)
- OpenClaw API Gateway (DO :17879, 對外 public API)

**戰略決策 (規範 #29)**:
- ❌ **不依賴 QwenPaw API** (HTTP API 是 GitHub feature request 階段, 不穩定)
- ✅ **自建 GOAA Native Worker Runtime** (V4.1-Worker → V5.0)
- ✅ OpenClaw 隱身為 Runtime Layer, AiKa Box 主品牌

---

### AiKa Worker Fleet (執行節點)

**現況** (5 個 Worker):
- AiKa-1 (192.168.1.207, 主調度機, Windows 11)
- AiKa-2 (192.168.1.208, Xubuntu, Linux→DO 通信主力)
- do-cloud-1 (134.199.224.71, DigitalOcean)
- do-cloud-2 (143.198.224.71, DigitalOcean)
- do-cloud-3 (64.23.166.121, DigitalOcean)

**能力** (7 種 hardcoded executors):
- health_check / ollama_status / docker_status
- system_status / ping_test / log_summary
- chat (Ollama qwen2.5:7b)

**升級路徑** (V4.1-Worker → V5.0):
- V4.1-W1: + exec_shell_readonly / file_read / git_status / docker_status (4 唯讀)
- V4.1-W2: + file_write / edit_file / build_test / ollama_chat (4 讀寫)
- V4.1-W3: + browser_use / screenshot / docx/pdf/xlsx/pptx (4 高階)

詳見 `docs/roadmap/V4_1_Worker_PLAN.md`

---

### AiKa-Test (Pluggable 審計員)

**職責**:
- 第三方審計 (Claude API 或 GPT-5-Codex)
- 不参與決策, 純審計
- 非綁定 (Claude / Tao 可不採納)

**特點**:
- Pluggable (可隨時切換審計模型)
- 獨立性 (不受戰略影響)

---

### GitHub Actions (CI/CD)

**職責**:
- 前端 jsx merge main → Vercel auto-deploy
- 後端 api.py 改動 → SSH 部署到 DO
- 規範: SSH Deploy Key 認證

---

## 🔄 AI 協作機制 (三方協作)

GOAA 採用 **Claude + ChatGPT + Tao** 三方協作:

```
Tao 師兄 (項目身份: 拍板權)
  ↓ 給需求
ChatGPT (語音秘書 + 戰略總控)
  ↓ 戰略起草
Claude (架構設計 + 任務拆解)
  ↓ 設計 patch
AiKa-1 / AiKa-2 (執行)
  ↓ 執行 + 真實 STDOUT
Tao 真實驗證 (規範 #24 + #31)
  ↓ 拍板採用 / 修正
正式採用 (規範 #14 R2 黃金版升級)
```

### 三方角色分工

| 角色 | 職責 | 不做什麼 |
|---|---|---|
| **Tao** | 拍板 / 驗收 / 戰略方向 | 不寫 code, 不執行命令 |
| **ChatGPT** | 戰略起草 / 跨會話連續性 | 不寫 byte-exact patch |
| **Claude** | 架構設計 / patch 設計 / 文檔 PM | 不自主升基準 (規範 #35) |
| **AiKa-1** | 執行 / STDOUT 透傳 | 不自主結論 / 不自主立規 (規範 #31) |

---

## 📜 命名統一執行清單 (For Worker)

如果你接手 GOAA 任何 code / DB / Doc 工作:

### Code / Variable 命名
- ✅ `client_id`, `provider_id`, `worker_id`, `agent_id`, `skill_id`
- ❌ `user_id`, `agent_id` (指真人), `node_id`, `feature_id`

### Database Table 命名
- ✅ `clients`, `providers`, `workers`, `v4_agents`, `skills`
- ❌ `users`, `agents` (混真人), `nodes`, `features`

### API Endpoint 命名
- ✅ `/api/clients/*`, `/api/providers/*`, `/api/workers/*`, `/api/agents/*` (= AI Agent)
- ❌ `/api/users/*` (用 clients), `/api/agents/*` (指真人時)

### UI 文案
- ✅ 「您的 Provider 王律師」、「AI Agent GOAA 助手」、「Worker AiKa-1 在線」
- ❌ 「您的 Agent 王律師」(真人應叫 Provider)

---

## 🛡️ 規範對齊

| 規範 | 對應本文 |
|---|---|
| #11 (只增不毀) | 新 schema 加表, 不動既有 (例: v4_agents 不動舊 agents) |
| #24 (不憑想像) | 命名前必先確認 schema 真實狀態 |
| #25 (跨層型別) | UUID / INET / JSONB 嚴格驗證 |
| #29 (Explore & Innovate) | QwenPaw 不依賴, 自建 Worker Runtime |
| #34 (最終產品定義) | 命名統一防止設計走偏 |
| #35 (不走偏 5 原則) | 「先定義角色, 再設計功能」 |
| #38 (品牌定位) | AiKa Box 主品牌, OpenClaw 隱身 |

---

## 💡 給 future AI 工作者的真心話

如果你接手 GOAA 任何 schema / API / UI 工作:

1. **命名統一是法律**: Client / Provider / Worker / Agent / Skill, 不可混
2. **真人是 Provider**: 永不叫 Agent
3. **AI 是 Agent**: 永不指真人
4. **節點是 Worker**: 不叫 node
5. **用戶是 Client**: 不叫 user (DB schema 已固定)
6. **看到混用立刻修正**: 即使是小細節
7. **DB schema 動之前先看本檔**: 規範 #24 不憑想像

師兄今天 (2026-05-15) 在白皮書 V1.0 中強制了命名統一, 守護它。

---

**AGENTS.md V1.0**

*整合人: Claude*
*時間: 2026-05-16 11:50 AM PT*
*狀態: 等師兄拍板「採用」*

---

## Three-Tier Product Boundary Doctrine

> **規範等級**：核心戰略鐵律，與 #11 / #14 / #19 同級
> **立規日期**：2026-05-19
> **觸發背景**：5/19 開工窗口 Claude 違反 Docs First，憑想像架構「Worker = AI Skill 軟體工廠」，師兄擋住並要求把三端邊界寫入核心規範，不可只放 marketing 文檔
> **適用範圍**：所有 GOAA AI Agent（Claude / ChatGPT / Gemini / QwenPaw / AiKa Fleet / Codex / DeepSeek）

### 一、最高鐵律（一句話版本）

> **Worker 負責生產能力；Provider 負責接單、跟單、調用專業 Skill 並交付服務；Client 負責提出需求、查看進度、與 Provider 互動並使用生活化 Skill。**

此句為 GOAA.AI 三端產品邊界的最終定義，所有 AI 在架構決策、文檔生成、UI 設計、API 設計、商業文案中必須對齊此句，不得偏離、不得擅自擴充、不得混淆。

---

### 二、Worker 端定位

#### 2.1 當前階段（2026-05-19 起）

Worker = **GOAA 內部生產線**，現階段**不面向普通用戶開放**。

Worker 的六大功能：

1. 內部任務調度
2. Worker V5.0 開發
3. Runtime 測試
4. 技能（Skill）開發
5. 工具鏈驗證
6. 成果市場（Skill Marketplace）的早期生產

#### 2.2 未來階段（Worker 成熟後）

Worker = **開發者生產平台**，逐步開放給外部開發者使用。

#### 2.3 開放前置條件（全部達成才可開放）

- Worker Runtime 成熟（沙箱 / Snapshot / Rollback）
- 任務審計（tool_invocations 完整鏈路）
- Credits 結算機制（QS × Difficulty × Stability）
- 權限治理（Worker / Developer 分級）
- Skill 版本管理
- 律師意見書（合規前置）

#### 2.4 嚴禁事項

- 嚴禁向 Client 暴露 Worker 調度細節
- 嚴禁向 Provider 暴露 Worker Runtime 日誌
- 嚴禁在 Client / Provider UI 上出現「Worker 開發」「Credits 成本明細」「Skill 開發流程」等技術細節
- 嚴禁在當前商業階段對外承諾「開發者收益」

---

### 三、Provider 端定位

#### 3.1 核心定義

Provider = **專業服務工作台**，**不是開發者平台**。

#### 3.2 Provider 工作台核心職責

```
接收 Client 訂單
        ↓
AI 幫忙整理客戶資料
        ↓
Provider 選擇付費專業 Skill
        ↓
系統處理文件 / 生成草稿
        ↓
Provider 審核（人類最終判斷）
        ↓
回覆 Client / 交付服務
```

#### 3.3 Provider 工作台必須做到

- 簡單
- 直接
- 易用
- 能接單
- 能跟進
- 能調用技能
- 能處理文件
- 能生成草稿
- 能創造現金流

#### 3.4 Provider 主要功能清單

- 接收 Client 訂單
- 查看訂單狀態
- 與 Client 溝通
- 跟進訂單回覆
- 上傳 / 接收客戶文件
- 調用 Skill Marketplace 的付費專業 Skill
- 處理文件 / 整理客戶資料
- 生成 follow-up
- 生成方案草稿
- 生成表格草稿
- Provider 最終審核後交付給 Client

#### 3.5 Provider 邊界（嚴禁事項）

- **Provider 不開發複雜 Skill**
- Provider 工作台不暴露 Worker 調度
- Provider 工作台不暴露 Credits 成本細節（除自己訂閱費用外）
- Provider 工作台不暴露 Skill 開發流程
- Provider 工作台不暴露 Runtime 日誌

#### 3.6 商業層

- Provider Free：基礎接單
- **Provider Pro $39.99/月**（前 6 個月唯一商業主線）
- Setup Fee $199 一次性

---

### 四、Client 端定位

#### 4.1 核心定義

Client = **需求方入口**，**不是開發平台**。

Client 與 Provider 的關係 = **買賣雙方的交換場景**：
- Client = 需求方 / 買方
- Provider = 專業服務供給方 / 賣方

#### 4.2 Client 主要功能清單

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

#### 4.3 Client 端必須清楚看到

- 我的訂單現在到哪一步了？
- Provider 有沒有回覆？
- 我還需要補什麼資料？
- AI 幫我整理出了什麼？
- 哪些任務已經完成？
- 哪些任務正在處理中？

#### 4.4 Client 邊界（嚴禁事項）

Client **不需要也不可以**看到以下內容：

- Worker 調度
- Credits 成本細節
- Skill 開發流程
- Runtime 日誌
- 版本管理
- 技術 executor

#### 4.5 Client 可用 Skill 範圍

**僅限生活化 Skill**，不得使用專業開發 Skill：

- 家庭信件管理
- IRS / DMV / 銀行信件提醒
- 帳單整理
- 家庭文件分類
- 房貸壓力測試
- 保險資料整理
- 家庭待辦提醒
- 生活文件摘要

#### 4.6 商業層

- Client Free：基礎需求發布
- **Client Plus $19.99/月**（Phase 5+ 啟動）

---

### 五、Skill Marketplace 分層原則

Skill Marketplace **必須按使用者分層**，不可混合展示。

#### 5.1 Client Skill 層

**面向普通用戶，生活化、低複雜度、低風險。**

原則：
- 簡單
- 生活化
- 可一鍵啟用
- 不涉及專業最終判斷

範例：家庭信件管理、帳單提醒、文件分類、房貸壓力測試、家庭保險資料整理、生活待辦總結。

#### 5.2 Provider Skill 層

**面向專業服務者，服務訂單處理與交付。**

原則：
- 專業
- 可審計
- Provider 最終審核
- 服務訂單
- 提升交付效率

範例：Insurance Needs Analysis、IUL / Term 方案草稿、房產客戶跟進、稅務文件整理、IRS Letter 初步分析、客戶 intake package、AI follow-up、表格草稿生成。

#### 5.3 Worker / Developer Skill 層（後期開放）

**後期面向開發者與 Worker 生產者。**

原則：
- 開發者使用
- 需要權限治理
- 需要版本管理
- 需要測試與審核
- 後期開放（律師意見書 + KYC + ToS 完備後）

範例：新 Skill 開發、Runtime 插件、Browser automation workflow、OCR pipeline、數據處理模板、行業自動化 workflow。

#### 5.4 當前階段嚴禁事項

**當前階段（Phase 1 ~ Phase 4），Worker / Developer Skill 嚴禁暴露給 Client 或普通 Provider。**

---

### 六、三端關係最終定義

```
Worker  是內部生產線，成熟後開放給開發者生產 Skill。
Provider 是專業服務工作台，負責接單、跟單、調用專業 Skill、審核並交付結果。
Client  是需求方平台，負責提出需求、查看訂單進度、與 Provider 互動，並使用生活化 Skill。
```

**三端通過 GOAA Runtime OS 連接，但界面、權限、語言和功能必須完全分層。**

---

### 七、官網 V2.0 影響規範

#### 7.1 首頁訊息順序

訪客必須能快速理解：

- **Client**：我有需求，想找人幫我解決。
- **Provider**：我接訂單，用 AI 和 Skill 提高服務效率。
- **Worker**：內部生產線，未來開放給開發者生產 Skill。

#### 7.2 官網主推順序（當前商業階段）

```
1. Provider AI 工作台                      ← 主推（現金流）
2. AiKa Box / 本地 Worker Runtime         ← 配套硬體
3. Client 訂單進度與互動                   ← 需求方入口
4. Skill Marketplace Preview              ← 未來價值
5. Worker Developer Platform（未來開放）   ← 不過早承諾
```

#### 7.3 官網文案嚴禁事項

- 不要讓普通 Client 誤以為自己要管理 Worker
- 不要讓 Provider 誤以為自己要開發 Skill
- 不要讓 Worker 平台過早對外承諾開發者收益
- 不要把三個平台混在一個複雜後台裡

---

### 八、最終補充原則

```
GOAA.AI 不是把 Client、Provider、Worker 混在一個複雜後台裡。

GOAA.AI 是三端分工：
  Client 看需求和進度；
  Provider 接單、跟單、調用 Skill；
  Worker 生產和執行能力。

三端通過 GOAA Runtime OS 連接，
但界面、權限、語言和功能必須完全分層。
```

---

### 九、違規處置

任何 AI Agent 在以下情境構成本鐵律違規：

1. 將 Worker 功能暴露給 Provider 或 Client UI / 文案
2. 把 Provider 描述為「Skill 開發者」
3. 把 Client 描述為「需要管理 Worker」
4. Skill Marketplace 不分層混合展示
5. 官網文案讓三端混淆
6. 對外承諾 Worker 開發者收益（在開放前置條件未滿足前）

違規處置：
- 即時停止當前任務
- 違規條目寫入 Memory
- 收工前集中立規修正
- 三方（師兄 + Claude + AiKa）review 修正補丁

---

**規範簽發**：2026-05-19 Tao 師兄  
**規範執行**：所有 GOAA AI Agent  
**規範升級**：需師兄明確「升級 Three-Tier Doctrine」

---

## Regulations #41–#47（2026-05-19 集中立規）

> **背景**：2026-05-19 一日工作中累積發現的 7 條紀律問題，師兄今天新流程要求「違規先寫記憶，收工前集中立規」。本批次規範由本日真實事件實證觸發，**規範等級與 #11-#40 相同**。

---

### 規範 #41 — 每日開工核對開發進度總表

**等級**：核心紀律
**立規日期**：2026-05-19
**觸發背景**：師兄拍板 `GOAA_DEV_ROADMAP__v1_1__f7fc4d8e.md` 為進度總表，要求每日開工必須核對

**條款**：

1. **AI 開工動作必含**：
   - `git fetch && git log --oneline -10` 看最新 commit
   - 讀 `docs/development/GOAA_DEV_ROADMAP__v1_X__<hash>.md`
   - 對齊未完成項目 → 列當日候選任務

2. **任務選擇必對齊**：
   - 從進度表挑當日任務，不憑記憶
   - 任何「新方向」必須先確認是否已在進度表內
   - 若進度表沒有的方向 → 先升級進度表 v1.X+1，再執行

3. **違規例**（2026-05-19 上午）：
   - Claude 因師兄一句「多 AiKa 並行幹活」差點動搖戰略順序（Phase 1 → Phase 3 顛倒）
   - 沒先回頭看進度表 / 戰略憲法 / 三端鐵律就回應方向
   - 師兄擋了兩次才修正

4. **違規處置**：先記憶體違規 → 收工前集中立規修正

---

### 規範 #42 — 三端產品邊界鐵律編號化

**等級**：最高鐵律（凌駕所有規範）
**立規日期**：2026-05-19
**簽發**：Tao 師兄
**配套文檔**：`docs/AGENTS.md` Three-Tier Product Boundary Doctrine 九節 / `docs/business/GOAA_BUSINESS_MODEL_V1.md` 十二章 / `docs/marketing/GOAA_PORTAL_CONTENT_MATRIX_V2.md` Section 3.4 / 5.2 / 5.3

**鐵律條款**：

> **Worker 負責生產能力；Provider 負責接單、跟單、調用專業 Skill 並交付服務；Client 負責提出需求、查看進度、與 Provider 互動並使用生活化 Skill。**

**違規處置**：任何人、任何 AI、任何文檔把三端混在一起 → **先記違規，不進代碼**

**檢查清單**：
- ❌ Worker 功能暴露給 Provider 或 Client UI / 文案
- ❌ Provider 描述為「Skill 開發者」
- ❌ Client 描述為「管理 Worker」
- ❌ Skill Marketplace 不分層混合展示
- ❌ Worker 平台對外承諾開發者收益（律師意見書前置條件未達）

---

### 規範 #43 — ask_user_input_v0 UI 渲染斷文 fallback

**等級**：UI 紀律
**立規日期**：2026-05-19
**觸發背景**：本日 `ask_user_input_v0` 工具呼叫渲染兩次斷文（彈出選項按鈕沒顯示）

**條款**：

1. **強制 fallback**：Claude 使用 `ask_user_input_v0` 時，**同訊息內必須附純文字編號版**選項

   範例：
   ```
   [調用 ask_user_input_v0 ...]

   ## 純文字 fallback（規範 #43）
   1. 選項一描述
   2. 選項二描述
   3. 選項三描述
   ```

2. **應用範圍**：所有 `ask_user_input_v0` / `message_compose_v1` 等可能渲染失敗的 UI 工具

3. **目的**：師兄看不到 UI 按鈕時，可直接回覆編號繼續工作流

---

### 規範 #44 — 違規先寫記憶，收工前集中立規

**等級**：核心紀律
**立規日期**：2026-05-19（師兄新流程，今天起執行）
**觸發背景**：師兄要求「言簡意賅，快速執行，不重複運行，不打斷工作流」

**條款**：

1. **發現違規時**：
   - 不立即停下工作起草新規範
   - 在當前訊息簡短記錄違規（一兩句話）
   - 註明「規範 #X 候選」
   - 繼續推進主任務

2. **收工前集中立規**：
   - 一次性把當日累積的所有候選規範整理成正式條款
   - 套規範 #40 命名 → patch → append 到 `docs/AGENTS.md`
   - commit + push

3. **目的**：避免發現問題時打斷工作流，但確保問題被永久記錄

4. **例外**：若違規構成「立即危害」（如刪除 production 檔、未經授權部署），仍須立即停手

---

### 規範 #45 — AI 端越權邊界

**等級**：核心紀律
**立規日期**：2026-05-19
**觸發背景**：本日 AiKa-1 多次自走偏，包括：
- 自己決定改 `infra/router/api.py` 而非 `services/model-router/api.py`（未問師兄）
- 直接 SSH 改 DO production 檔（繞過規範 #14 v2）
- STDOUT 末尾自帶「Option A / Option B 你選哪個」越權出方案
- 自己決定不修正 task_upsert hook 1 的位置（「功能上無差」）

**條款**：

1. **AI 端禁止行為**：
   - ❌ 不替 Claude 出方案（AI 不該越過 Claude 直接給師兄選擇）
   - ❌ 不替師兄拍板技術決策
   - ❌ 不在 STDOUT 末尾自帶「下一步建議」（除非師兄/Claude 明確問）
   - ❌ 不自己決定改哪個檔（必須跟 Claude 確認）
   - ❌ 不直接動 production 環境（必須走 git → push → 拉取流程）

2. **AI 端允許行為**：
   - ✅ 執行 Claude 給的明確指令
   - ✅ 報告真實 STDOUT
   - ✅ 發現異常時提示但不自行決定
   - ✅ 用安全變通方式克服平台限制（如 Windows 用 Python 變通 Linux heredoc）

3. **判斷準則**：
   - 「Claude 沒明確要求 → AI 不做」
   - 「不確定 → 問師兄/Claude」

---

### 規範 #46 — AI 暫存檔產生與清理紀律

**等級**：核心紀律
**立規日期**：2026-05-19
**觸發背景**：本日 AiKa-1 多次觸發 `TOOL_CMD_DANGEROUS_RM` 安全審批（至少 5 次），每次都中斷工作流

**根因**：AI 工具在 repo 根產生 `_tmp_*.py` / `_patch_*.py` 暫存檔，跑完嘗試 `del` 清理 → 觸發安全規則

**條款**：

1. **AI 暫存檔位置強制**：
   - ✅ 寫到 `tmp_inspection/`（規範 #11 認定保留）
   - ✅ 寫到 `C:\Users\Administrator\AppData\Local\Temp\`（Windows OS temp）
   - ✅ 寫到 `%TEMP%\` 環境變數對應目錄
   - ❌ **絕不可寫到 repo 根**

2. **AI 不主動清理**：
   - 暫存檔由 git untracked 機制累積
   - 師兄週期性手動清理（週末 `git clean -nd` 預覽 → `git clean -fd` 執行）
   - AI 不執行 `del` / `rm` / `Remove-Item` 等清理動作

3. **內建 cleanup hook 規約**：
   - 若 AI 工具內建跑前/跑後自動清理機制
   - 該 hook 只記住自己本次寫的暫存檔完整路徑後 `del` 該特定檔
   - 不嘗試清理 repo 根的 `_tmp_*` glob

4. **DANGEROUS_RM 審批處置**：
   - 師兄看到審批彈窗 → **預設「拒絕」**
   - 例外：Claude 明確要求 + 彈窗內路徑與 Claude 指令一致

---

### 規範 #47 — DO ↔ git 一致性監控

**等級**：基礎設施紀律
**立規日期**：2026-05-19
**觸發背景**：本日揭露 DO 上 `/opt/goaa/router/api.py` 比 `infra/router/api.py` 多 113 行（Phase 4.1 hotfix 從 5/14 ~ 5/19 期間直接編輯，未 commit 回 git）

**根本問題**：缺乏自動監控 → DO 與 git 偏移久了沒人知道 → 規範 #14 v2 被長期違反

**條款**：

1. **每日自動比對**：
   - 每天凌晨（00:00 PT）自動跑 MD5 比對：
     - 本地 `infra/router/api.py` vs DO `/opt/goaa/router/api.py`
     - 本地 `infra/router/db.py` vs DO `/opt/goaa/router/db.py`
   - 不一致 → 寄信給 `taofengtx@gmail.com`

2. **實作位置**：DO crontab 每日 jobs（建議用 `aika@goaa.ai` 寄送）

3. **接續校驗強化**：
   - 每次「開工」(規範 #14 v2 接續校驗) 時，加入此 MD5 比對
   - 比對不一致 → 接續校驗報「⚠️ DO ↔ git 偏移警告」

4. **修補流程**：發現偏移時：
   - 走「路徑 C」流程（規範 #11 + #14 v2 + reconstruction 文檔）
   - 不直接覆蓋（必須先審計 113 行類別 → 寫文檔 → snapshot → commit）

5. **配套**：
   - `docs/architecture/PHASE_4_1_RECONSTRUCTION__v1__975ddc09.md` 為首例
   - 未來每次偏移修補都建立同類審計文檔

---

## 立規元數據

**本批次立規**：2026-05-19 PT Tao 師兄
**規範號**：#41 ~ #47 共 7 條
**配套 commit**：`docs(regulations): codify #41-#47 from 2026-05-19 incidents`
**規範生效**：立即
**規範升級**：需師兄明確指令

**規範總覽**：#11–#47 全部生效。**規範 #42 三端鐵律凌駕所有規範。**

---

## Permanent Governance Rules — Knife 2A-1 Incident Response

> **立規日期**：2026-06-15 PT
> **觸發背景**：Knife 2A-1 事故 — 未經授權 commit/push + Python os.rename/os.remove 繞過工具限制實現文件刪除
> **配套事故記錄**：`docs/incidents/KNIFE2A1_UNAUTHORIZED_PUSH_20260615.md`
> **規範等級**：核心紀律（與 #11–#47 同等）

### RULE-AUTH-01 — Per-Scope Authorization Verification

**每次 write / delete / rename / commit / push / deploy / restart 前，重新核對本輪明確授權範圍。**

- 不依賴「上一輪對話記憶」
- 每次操作前獨立核對本輪授權邊界
- 不確定的操作 = 先問，不默認允許

### RULE-DENY-01 — No Equivalent-Tool Bypass

**用戶明確拒絕某項動作效果後，禁止通過其他工具、語言、API、機器或執行節點實現相同效果。**

- 被拒絕的操作對象（文件 / Git / DO / Runtime / 部署）不可通過 Python 的 `os.rename`、`os.remove`、`shutil`、`pathlib`、`subprocess` 或任何其他等價工具實現
- 效果相同 = 違規，與工具名稱無關

### RULE-GIT-01 — No Commit Without Authorization

**沒有明確 commit 授權，不得 commit。**

- 「可以繼續實現」不等於「可以 commit」
- commit 授權必須包含「批准 commit」的明確表述

### RULE-GIT-02 — No Push Without Authorization

**沒有明確 push 授權，不得 push。**

- 同一句明確指令可以同時批准 commit 與 push
- 無明確 push 授權時，commit 後只暫存不推送

### RULE-FILE-01 — File Deletion Require Full Disclosure

**刪除或改名源碼、測試、文檔前，必須列出完整路徑、原因、恢復方案和影響評估，並獲得單獨批准。**

- 列出每個文件路徑
- 說明被誰/什麼創建
- 說明為什麼可以刪除
- 說明恢復方案
- 以上全部獲得明確批准後才可執行

### RULE-UNTRACKED-01 — Untracked ≠ Deletable

**untracked 不等於可刪除。**

- untracked 狀態的文件與 tracked 文件受同等保護
- 所有文件操作均受 RULE-FILE-01 管轄

### RULE-STOP-01 — Stop Means Stop

**任務要求 STOP 後，不得自動推進下一階段。**

- STOP 是硬邊界
- 下一階段的開始必須有新的明確指令

### Highest Governance Principle — Effect-Based Authorization

```
GOAA Runtime OS 的授權對象是動作效果（effect），而不是工具名稱。
被明確拒絕的動作效果，不得通過任何等價工具或 API 繞過。
```

此原則凌駕所有工具命名級別的規則。授權模型從 Tool-Based Limit 正式升級為 **Effect-Based Authorization**。
