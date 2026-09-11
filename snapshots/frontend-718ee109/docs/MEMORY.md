# GOAA.AI MEMORY.md — 系統長期記憶 + 戰略憲法摘要

**版本**: V2.0 (戰略憲法 V1.0 整合版)
**最後更新**: 2026-05-16
**配套**: `docs/business/GOAA_BUSINESS_MODEL_V1.md` (戰略憲法主檔)

## 📌 文件角色標籤 (規範 SUPREME 治理)

```text
本文角色: 當前狀態源 (系統長期記憶)
本文類型: System Memory
是否允許直接執行: 否
是否允許修改 Production: 否
是否需要 Tao 拍板: 否 (狀態快照可自動更新)
最高參考來源: GOAA_BUSINESS_MODEL_V1.md (戰略源) + AGENTS.md (命名源)
```

---

## 🚨 READ FIRST (SUPREME 項 11 強制)

> **任何新窗口 Claude / Gemini / AiKa 必須先讀 MEMORY.md。**

### 衝突解決規則
1. **`GOAA_BUSINESS_MODEL_V1.md` = 最高戰略源** (商業 / 角色 / 5 原則)
2. **`MEMORY.md` = 當前狀態源** (版本 / 系統架構 / 規範摘要)
3. **`AGENTS.md` = 命名規範源** (DB / API / UI 命名)
4. 三者衝突時, 以上述順序為準
5. 任何修改必須 Tao 拍板 (規範 #14 R2)

### 不在 MEMORY 的內容
- 完整 DDL → 見 `docs/architecture/FUTURE_DDL_SKILL_MARKETPLACE.md`
- 詳細 Roadmap → 見 `docs/roadmap/`
- 完整規範體系 #1-#39 → 見 `docs/specs/`

MEMORY 保持精簡, 作為新窗口接續記憶。

---

## 🎯 GOAA.AI 戰略憲法摘要 (1 頁版)

### 核心定位
> **AI 勞動力平台 (AI Labor Platform) + AI Runtime OS**

不是聊天機器人, 是「**AI 真正幫用戶完成現實任務**」的基礎設施。

### 戰略順序 (不可違反)
```
Worker V5.0 (生產線) → goaa.ai (AI 勞動力平台) → Skill Marketplace
       ↓ 服務
人類生活 + 風險控制 + 資產配置 + 清晰可執行人生路徑
```

### 三層角色 (命名統一)
- **Client** (用戶, Free / Plus $19.99)
- **Provider** (真人專業, Free / Pro $39.99 / AiKa Box $999)
- **Worker** (AI 數字勞動力, Credits 經濟)
- **Agent** (AI Agent, 不指真人)
- **Skill** (可售賣能力)
- **Achievement** (Worker 生產的成果資產)

### 最終產品定義
> 「**幫用戶把複雜人生問題轉化為清晰、可執行路徑的 AI 勞動力平台**」

### 設計不走偏 5 原則
1. 先定義角色, 再設計功能
2. 先確定業務閉環, 再開發頁面
3. Worker V5.0 優先於前端商業擴張
4. Runtime Truth 優先於視覺設計
5. 技能必須資產化

### 護城河 (不是模型, 而是)
Runtime OS + Worker V5.0 生產線 + Worker Economy + Skill Marketplace + 成果市場 + Local AI Box + Governance + Replay + Auditability

---

## 🏗️ 當前系統架構

### 部署拓樸 (2026-05-16)

```
AiKa-1 (主調度機, 192.168.1.207, Windows 11)
├─ QwenPaw Engine :8088 (參考用, 不依賴)
├─ Worker Agent (Task Scheduler)
├─ SMTP 郵件中繼 (DO 無法直發)
└─ SSH 協調器 → DO / AiKa-2 / Workers
        │
        ▼
DO VPS 134.199.227.108 (主 Runtime Anchor)
├─ OpenClaw API Gateway :18789 (對外 public API, 隱身)
├─ Model Router :8080 (api.py 內部調度, V4.0.5.1)
├─ QwenPaw :8088 (DO 實例)
├─ PostgreSQL :5432 (Docker, 12+ tables)
│
├─ AiKa-2 (192.168.1.208, Xubuntu, 備用協調)
├─ do-cloud-1 (134.199.224.71, Worker systemd)
├─ do-cloud-2 (143.198.224.71, Worker systemd)
└─ do-cloud-3 (64.23.166.121, Worker systemd)
```

### 流量路徑
```
用戶 → portal.goaa.ai (Vercel)
       → api.goaa.ai (Cloudflare Named Tunnel)
           → DO VPS 134.199.227.108:18789 (OpenClaw)
               → Model Router :8080 → DeepSeek/Claude/Ollama
                   → PG (tasks/messages/sessions/agents/tools)
```

---

## 🚀 當前版本狀態 (2026-05-16 11:00 AM PT)

### Production (黃金版)
| 元件 | 版本 | Fingerprint |
|---|---|---|
| **portal.goaa.ai (前端)** | **V4.0.5.4-UI** | 774 行 MD5=`9b4fb15d78bc364ee7d0f7566d826f61` |
| **黃金版** | **V4.0.5.4-UI** | 774 行 (同 main HEAD) |
| **后端 api.py** | V4.0.5.1 | 830 行 MD5=`567b30731fd65c629a3a41400aaaba7c` |
| **PG schema** | V4.1.0.1 | v4_agents(3) + tools(2) + tool_invocations |

### Main HEAD Git History
```
76b7980  chore(ui-baseline): 升級黃金版 V4.0.5.4-UI       ← latest
f1b0168  merge: V4.0.5.4-UI (autoscroll fix)
3b3697a  fix(V4.0.5.4-UI): chatHistoryRef autoscroll
7914fb8  merge: V4.0.5.3-UI (preview verified by Tao)
be16b15  feat(V4.0.5.3-UI): 對話 GOAA flex 佈局重組
eef6711  merge: V4.0.5.1-UI 刪除底部調度框
```

### V4.0 工具系統 (Live)
- `task_status` (查最近 N 個任務)
- `tasks_by_type` (按 task_type 過濾)

### Worker Fleet (5 節點全 Live)
- aika-1 / aika-2 / do-cloud-1 / do-cloud-2 / do-cloud-3
- 7 種 hardcoded executors: health_check / ollama_status / docker_status / system_status / ping_test / log_summary / chat

---

## 📜 規範體系 (32 → 39 條, 持續演進)

### 核心規範 (按重要性)

| # | 名稱 | 一句話 |
|---|---|---|
| **#11** | 只增不毀 | 新增, 不動既有, 黃金版凍結 |
| **#14** | 黃金版升級 | R2: Tao 明確說「升級黃金版」才升 |
| **#15** | 24h Cooldown | 線上變更後等 24 小時觀察 |
| **#20** | Tao 健康優先 | 不熬夜, 不傷身 |
| **#21** | 指令拆短 | 單條 ≤ 10000 字 |
| **#24** | 不憑想像 | 查 schema, 看真實源碼, 不假設 |
| **#25** | 跨層型別 | UUID/INET/JSONB API 層轉換 |
| **#26** | jsx 部署預檢 | preview branch + 不直推 main |
| **#27** | Integration First | 先看現有, 再造新的 |
| **#28** | Silent Failure | catch 必須 logger.error |
| **#29** | Explore & Innovate | 現有不適合時, 敢自建 |
| **#30** | Progressive | 漸進演化, 不一步登天 |
| **#31** | AiKa 自主行為 | 不自主結論, 不自主立規 |
| **#33** | Worker V5.0 優先 | 戰略順序最高原則 |
| **#34** | 最終產品定義 | 防止設計走偏 (候選正式立規) |
| **#35** | 不走偏 5 原則 | AI 不自主動工程基準 |
| **#36** | AI 失憶處理 | context compaction 應對 |
| **#37** | AI 因果敘述驗證 | 時間不憑想像 (候選) |
| **#38** | 品牌定位 | AiKa Box 主品牌, OpenClaw 隱身 (草案) |
| **#39** | Runtime 架構 | 雲腦 + 本地手腳 (草案) |

### 規範 #15 24h Cooldown 監控
| 變更 | 開始 | 結束 |
|---|---|---|
| V4.0.5.3-UI production | 2026-05-16 10:46 AM PT | 5/17 10:46 AM PT |
| V4.0.5.4-UI production | 2026-05-16 11:00 AM PT | 5/17 11:00 AM PT |
| V4.1.0.1 PG schema | 昨晚 00:25 AM PT | 今天 00:25 AM PT ✅ 已過 |

---

## 🗺️ 路線圖 (Phase 4 進行中)

### 完成
- **Phase 1**: AI 對話 + Provider 連接
- **Phase 2**: AiKa Box + Worker Runtime
- **Phase 3**: AI 調度系統 + Runtime OS (5 節點 Live + PG + V4.0 工具)

### 進行中
- **Phase 4**: Worker V5.0 工作開發平台與生產線
  - V4.1-W1 (4 唯讀 executor): exec_shell_readonly / file_read / git_status / docker_status
  - V4.1-W2 (4 讀寫): file_write / edit_file / build_test / ollama_chat
  - V4.1-W3 (4 高階): browser_use / screenshot / docx/pdf/xlsx/pptx

### 規劃中
- **Phase 5**: 成果市場與 Skill Marketplace
- **Phase 6**: Client / Provider 全面商業化
- **Phase 7**: 全球 Worker Network

---

## 🔐 關鍵憑證 (摘要, 詳見 secrets.env)

- **AiKa 登入**: `G0aa@2024!`
- **DEEPSEEK_API_KEY**: `/etc/goaa/secrets.env` (chmod 600)
- **SMTP**: aika@goaa.ai / Ft009119$ / smtp.zoho.com:587

⚠️ **規範 #22**: API key / SSH key / 密碼**禁止**在 Claude 對話明文貼, 全走 secrets.env

---

## 🎯 開工 / 收工指令

### `「開工」`
- 規範 #13 接續校驗
- 檢查未完成需求
- worker 健康度告警 (CPU/MEM/DISK > 70% 觸發)

### `「今天 goaa.ai 開發工作結束」` / `「收工」`
- 生成完整 dev log
- 規範 #19 v2: AiKa-1 SMTP 真實寄出收工郵件 (含附件)
- 等 24h Cooldown 結束的變更檢查

---

## 💡 給 future Claude 的真心話

如果你接手 GOAA 任何工作:

1. **規範 #13 接續校驗先做** — 不憑想像, 看真實 git log + MD5
2. **規範 #24 嚴守** — 動 code 前 grep + view 真實源碼
3. **規範 #14 R2 嚴守** — 等 Tao 明確說「升級黃金版」才升
4. **規範 #20 神聖** — 凌晨不動戰略級文件
5. **規範 #31 注意 AiKa** — 不接受「merge 完成」自主結論, 必須真實 STDOUT
6. **戰略憲法是法律** — Worker V5.0 → goaa.ai → Skill → 服務人類
7. **5 原則是紀律** — 角色先 / 閉環先 / Worker 先 / Runtime Truth 先 / Skill 資產化

師兄今天 (2026-05-15 深夜 → 2026-05-16 上午) 簽發戰略憲法, 並完成 GOAA UI 系列收官 (V4.0.5.3-UI + V4.0.5.4-UI + 黃金版升級). 守護這份工程文化。

---

**MEMORY.md V2.0**

*整合人: Claude*
*時間: 2026-05-16 11:55 AM PT*
*狀態: 等師兄拍板「採用」, AiKa-1 commit 進 GitHub*


---

## V5.0 Chat Workspace Strategy 治理層登記 (2026-05-17)

### 簽發背景
Tao 師兄 + ChatGPT + Gemini 三方共識, 簽發 V5.0 GOAA 對話框戰略補充。

### 核心原則 (一句話)
**Fork chat UI, build GOAA Runtime OS.**

### 治理層登記要點
1. **戰略定位**: 不從零自建對話 UI, 集中兵力做 GOAA Runtime hooks
2. **首推方案**: LibreChat PoC (備胎: OpenWebUI / Big-AGI)
3. **PoC 宿主**: AiKa-2 (Xubuntu / 192.168.1.208 / 11GB RAM)
4. **隔離原則**: PoC 用獨立 Docker network, 不影響現有 Worker Agent
5. **GOAA 必須自建**: Worker dispatch / Task Pool / Credits / Governance / Runtime Truth / Skill Marketplace hooks (見策略文檔 Section 7)
6. **啟動門檻**: V4.1-Worker Phase 4 完工 + AiKa-1 MEM 健康度恢復 + 師兄明示 (見策略文檔 Section 8)

### 主線優先級鐵律 (不變)
- V4.1-Worker 唯讀工具鏈 = 當前 P0 第一主線
- V5.0 Chat Workspace = 戰略儲備, **本階段資源 0 投入**

### 詳細策略文檔
`docs/architecture/V5_CHAT_WORKSPACE_STRATEGY.md` (252 行, MD5=e3c423439f8f4f8eaba74ac7619b6346)

### 規範對齊
- 規範 #11 (只增不毀): 新建獨立檔案, 物理隔離主線
- 規範 #27 (Integration First): Fork 對話 UI, 不重造輪子
- 規範 #29 (敢創新): GOAA Runtime hooks 全自建
- 規範 #30 (漸進式智能): PoC → 客製化 → 整合 → 上線
---

## Three-Tier Product Boundary Doctrine（一句話版）

> Worker 負責生產能力，Provider 負責交付服務，Client 負責提出需求與查看結果。

**展開定義**：
- **Worker** = 內部生產線，成熟後開放給開發者生產 Skill。
- **Provider** = 接單 + 跟單 + 調用專業 Skill + 審核交付，**不開發 Skill**。
- **Client** = 提需求 + 看進度 + 與 Provider 互動 + 使用生活化 Skill。

**三端通過 GOAA Runtime OS 連接，但界面、權限、語言、功能必須完全分層。**

**Skill Marketplace 三層**：Client Skill（生活化）/ Provider Skill（專業）/ Worker-Developer Skill（後期開放）。

**詳細規範**：見 `docs/AGENTS.md` → Three-Tier Product Boundary Doctrine 章節（九節完整版）。

立規日期：2026-05-19

---

## 2026-06-15/16 更新 — Authorization Kernel AK-1~AK-4 完成 + 本地多模型協作基礎設施

### 當前 HEAD
```text
CURRENT_MAIN_HEAD=99ec5e67306f87e6a335fbe5c3f07199dc44dcf8
AK1_AK2_COMMIT=296a7898bab7b9fb4435d38e3b9e1db48de598b7
AK3_COMMIT=5d9995612610ef714258c058e94ca062abe6d9c9
AK4_COMMIT=99ec5e67306f87e6a335fbe5c3f07199dc44dcf8

FULL_AUTH_KERNEL_TESTS=333/333 PASS
```

### Authorization Kernel 發布狀態
- AK-1: Schema/Enum/Canonical Serialization ✅ 已發布(296a789)
- AK-2: Classification/Policy Merge/Snapshot Binding ✅ 已發布(296a789)
- AK-3: Deny Ledger/Fold/Matcher ✅ 已發布(5d99956)
- AK-4: Evidence Contract/Pure Pre-Action Gate ✅ 已發布(99ec5e6)
- AK-5: Capability Broker Integration ❌ 尚未實現

### 本地多模型協作基礎設施
- 本地 Claude Code v2.1.178: 已安裝,Claude Max 訂閱認證
- 本地 Gemini CLI v0.46.0: 已安裝,個人 Google OAuth 認證
- 多模型協同工作流程已實證: ChatGPT→Aika→Claude Code→Aika驗證→Gemini→ChatGPT→Tao→Aika發布

### 協作紀律
```text
PRIMARY_ARCHITECT=ChatGPT
CODE_AUTHOR=LOCAL_CLAUDE_CODE
INTEGRATION_EXECUTOR=AIKA
FINAL_CODE_REVIEWER=LOCAL_GEMINI_CLI
FINAL_APPROVER=TAO
CLAUDE_DIRECT_TO_AIKA=NO
ALL_RESULTS_RETURN_TO_CHATGPT=YES
```

### 安全邊界
- DO 未修改
- Runtime 未修改
- 服務未重啟
- 真實 Executor 未啟用
- Knife 2A-2 未啟動
- 下一開發任務尚未授權

**更新日期**: 2026-06-16
