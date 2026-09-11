# GOAA Runtime OS 戰略架構 V1.0 — 雲腦 + 本地手腳

**版本**: V1.0
**最後更新**: 2026-05-16
**配套**: `docs/business/GOAA_BUSINESS_MODEL_V1.md` (戰略憲法主檔)
**狀態**: 架構基線 (Architecture Baseline)

## 📌 文件角色標籤 (規範 SUPREME 治理)

```text
本文角色: Runtime OS 架構基線
本文類型: Architecture Baseline
是否允許直接執行: 否
是否允許修改 Production: 否 (僅架構參考)
是否需要 Tao 拍板: 是 (架構修改)
最高參考來源: GOAA_BUSINESS_MODEL_V1.md 第 11 章
```

---

## ⚡ 核心宣言 (SUPREME 項 8.2 置頂)

> # **雲端決策, 本地執行**
> # **Decision in Cloud, Execution at Edge**

這是 GOAA Runtime OS 的最高架構原則, **不可違反**。

---

## 🎯 OpenClaw / Router / Worker 邊界 (SUPREME 項 8.1 強制)

避免未來再把 OpenClaw 誤解為 Worker, 必須明確邊界:

| 元件 | 真實角色 | Port | 對誰服務 |
|---|---|---|---|
| **OpenClaw** | **Public API Gateway / API Layer** | DO :18789 | 對外開發者 / Framer 官網 |
| **GOAA Task Router** | **Internal Runtime Dispatcher** | DO :8080 | portal.goaa.ai + Worker Agents |
| **Worker Agent** | **Execution Runtime** | (主動 poll Router) | 自己的節點 |

### 三層職責不可混淆
- OpenClaw ≠ Worker
- OpenClaw ≠ Router
- Worker ≠ Agent (AI Agent)
- Worker = AI 數字勞動力節點

詳見 `AGENTS.md` 命名規範。

---

## 🧠 一、核心原則: 雲腦 + 本地手腳

> **AI 大腦在雲端決策, 本地 Worker 真實執行**

### 為什麼不是純雲端
- 用戶本機檔案 / cookies / session 雲端拿不到
- 隱私場景 (代碼 / 醫療 / 金融) 不允許上雲
- 本地 GPU / OCR / 自動化能力是差異化護城河

### 為什麼不是純本地
- LLM 推理 laptop 跑不動 (Claude / GPT 動輒百 G)
- 跨機協作 / 長期記憶 / 計費結算需要雲端
- 用戶要的是「最強 AI」, 不是「最近 AI」

### 答案: **混合架構**, 各取所長

---

## 🏗️ 二、完整架構圖

```
┌──────────────────────────────────────────────────────────────────┐
│  雲端: GOAA Runtime OS  (DO 134.199.227.108)                    │
│                                                                  │
│  職責 (大腦):                                                    │
│  ├─ 調度 (Task Dispatch via /tasks/dispatch)                    │
│  ├─ 記憶 (PG: messages / tool_invocations / dispatch_plans)     │
│  ├─ Orchestration (multi-step workflow)                         │
│  ├─ Routing (DeepSeek 85% / Claude 10% / Ollama 5%)             │
│  ├─ Governance (規範體系 + 安全限制)                            │
│  ├─ Replay (從 PG 重建任務)                                     │
│  ├─ Analytics (token usage / cost / 效率)                       │
│  └─ Credits 結算                                                 │
│                                                                  │
│  元件:                                                           │
│  ├─ portal.goaa.ai  (用戶 UI, Vercel)                           │
│  ├─ api.goaa.ai  (Cloudflare Tunnel)                            │
│  ├─ OpenClaw API Gateway  (port 18789, public API, 隱身)        │
│  ├─ GOAA Task Router  (port 8080, api.py 內部調度)              │
│  └─ PostgreSQL  (Docker, 12+ tables)                            │
└──────────────────────────────────────────────────────────────────┘
                          ↑↓ 心跳 + Task Poll (HTTP)
┌──────────────────────────────────────────────────────────────────┐
│  本地: AiKa Box  (用戶機器 / VPS)                                │
│                                                                  │
│  職責 (手腳):                                                    │
│  ├─ shell (任意命令執行, 含 git/docker/system)                  │
│  ├─ file (read/write/edit/glob/grep)                            │
│  ├─ browser (playwright 自動化)                                 │
│  ├─ media (screenshot/video/image view)                         │
│  ├─ local LLM (Ollama qwen2.5:7b, GPU 本地推理)                 │
│  ├─ OCR / docx / pdf / xlsx / pptx (文檔處理)                   │
│  └─ automation (cron / scheduler)                               │
│                                                                  │
│  元件:                                                           │
│  ├─ Worker Agent  (Python agent.py, systemd)                    │
│  └─ 本地能力庫 (V4.1-W1 → V4.1-W3 逐階段建設)                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔄 三、真實任務生命週期 (5 階段)

```
[1] 用戶在 portal.goaa.ai 對話:「在 aika-1 跑 git log」
        │
        ▼
[2] GOAA Task Router /chat (DeepSeek function calling)
    └─ LLM 判斷: 這需要 dispatch_task 工具
    └─ POST /tasks/dispatch 加入任務池
        │
        ▼
[3] Worker Agent on aika-1 (每 5 秒 poll)
    └─ GET /tasks/next/aika-1 → 拉到 task
    └─ 本機執行 exec_shell("git log")
    └─ POST /task/complete 上報結果
        │
        ▼
[4] GOAA 寫 PG (tool_invocations / worker_events)
    └─ 結果回傳給 portal.goaa.ai
        │
        ▼
[5] portal 顯示給用戶
```

**關鍵**: 每一步都**可審計可回放** (戰略憲法護城河 #8 Auditability)

---

## ⚖️ 四、三層職責劃分

### 4.1 雲腦 Only (不下放本地)

| 能力 | 為什麼在雲 |
|---|---|
| LLM 決策邏輯 (判斷意圖) | 模型太大, 本機跑不動 |
| 跨節點 orchestration | 需要全局視角 |
| 用戶長期記憶 (PG sessions) | 跨裝置同步 |
| 規範強制 (安全層 + 白名單) | 統一審計 |
| 計費 / Credits 結算 | 防止本地竄改 |

### 4.2 本地 Only (雲端不能取代)

| 能力 | 為什麼必須本地 |
|---|---|
| shell / file 系統 IO | 用戶本機檔案雲端拿不到 |
| 本機 docker / git 操作 | 環境依賴本機 |
| browser automation | 用戶 cookies / session 私密 |
| 本地 LLM 推理 | 隱私場景不允許上雲 |
| 桌面截圖 / OCR | 涉及本機桌面內容 |

### 4.3 混合 (可雲可本地)

| 能力 | 選擇邏輯 |
|---|---|
| LLM chat | DeepSeek 雲 (快) vs Ollama 本地 (隱私) |
| 文檔處理 | docx/pdf 雲傳或本地 (檔案大小決定) |
| 簡單查詢 | PG 雲 (準) vs 本地 SQLite cache (快) |

---

## 🚨 五、Failure Path (SUPREME 項 8.3 補強)

任務生命週期不只是 happy path, 必須處理失敗:

### 完整失敗路徑

```
[Task dispatched]
        │
        ├─→ ✅ Worker online + 接收 → 正常執行
        │
        ├─→ ❌ Worker offline
        │   └─ Router 標記 task = 'worker_offline', 重派發到其他 Worker
        │
        ├─→ ❌ Worker timeout
        │   └─ Router 監控 task 超時 (predefined timeout), 標記 'timeout'
        │   └─ 嘗試 retry (最多 3 次)
        │
        ├─→ ❌ Permission denied
        │   └─ Worker 收到但 Class C / 路徑黑名單匹配
        │   └─ 立即拒絕 + 通報 portal + 寫 worker_events
        │
        ├─→ ⚠️ Need human confirmation
        │   └─ Class B (file_write / edit_file 等) → POST /task/preview
        │   └─ portal 顯示「確認執行」按鈕 → 師兄拍板才繼續
        │
        ├─→ ❌ Task failed (execution error)
        │   └─ Worker 回報 stderr + exit_code
        │   └─ Router 寫 PG, 標記 'failed'
        │
        ├─→ 🔄 Retry
        │   └─ 短暫失敗 (network / transient) → 自動 retry (exponential backoff)
        │
        ├─→ 🔙 Rollback
        │   └─ 寫入操作失敗 → 自動回到 backup state (Class B 必須有 backup)
        │
        └─→ 🚨 Human escalation
            └─ 自動重試 3 次仍失敗 → 通報師兄 (SMTP / portal alert)
```

### 失敗類型對應 Permission Class (參見 V4.1 Worker Plan)

| 失敗類型 | Class A | Class B | Class C |
|---|---|---|---|
| Worker offline | 自動重派 | 自動重派 | 拒絕 |
| Worker timeout | 自動 retry | 通報師兄 | 拒絕 |
| Permission denied | N/A | 預先確認 | 立即拒絕 |
| Task failed | 自動 retry | Rollback + 通報 | 拒絕 |

---

## 📡 六、Polling 演進 (SUPREME 項 8.4 補強)

### 當前 (V4.1 階段)

**5 秒 polling**, 優先**安全與可審計**:
- Worker Agent 每 5 秒 `GET /tasks/next/{worker_id}`
- 心跳 30 秒一次 (每 6 個 POLL cycle)
- 結果回報: `POST /task/complete`

**優點**:
- 簡單可靠, 失敗易恢復
- 可審計 (HTTP 日誌完整)
- 後端 stateless

**缺點**:
- 任務延遲 5 秒起 (一個 cycle)
- 高頻 polling 對 Router 有壓力

### V4.2.5 後評估升級 (3 個選項)

| 方案 | 優點 | 缺點 | 適用 |
|---|---|---|---|
| **Long Polling** | 即時 (~ms) | Worker 占用連線 | 短任務多 |
| **WebSocket** | 即時雙向 + 低延遲 | 複雜, 心跳機制要重做 | 高頻互動 |
| **Server-Sent Events (SSE)** | 簡單, 服務器推送 | 單向 (server → worker) | 通知為主 |

### 目標

V4.2.5+: 任務下發與回報延遲降低至 **200ms - 1s**

### 演進策略 (規範 #30 漸進)

```
V4.1 階段: 5 秒 polling (現在)
   ↓ 24h 觀察期 + 性能瓶頸分析
V4.2.5: Long Polling 試點 (1-2 個節點先)
   ↓ 24h 觀察
V5.0: WebSocket 全面切換 (含 fallback to polling)
```

---

## 🎯 七、跟競品的差異化

| 競品 | 它的架構 | AiKa Box 對比 |
|---|---|---|
| ChatGPT | 純雲, 沒本地手腳 | **我有本地執行能力** |
| LM Studio | 純本地, 沒雲腦 | **我有雲端調度 + 記憶** |
| Cursor | 雲腦 + IDE 手腳 (限程式員) | **我覆蓋任意 shell / 桌面** |
| AutoGen | 框架, 用戶要自己組 | **我是完成品 Appliance** |
| QwenPaw | 純本地, 閉源 | **我有雲端 governance + 自建開源** |
| n8n / Zapier | 雲端 workflow, 沒 AI 決策 | **我有 LLM 智能判斷** |

---

## 📈 六、演進階段 (對齊 Phase 4 → 7)

| 階段 | 雲腦能力 | 本地能力 | 對應規範 |
|---|---|---|---|
| **現在 (V4.0.5.4)** | LLM tools (task_status, tasks_by_type) | 7 hardcoded executor (唯讀) | 已上線 |
| **V4.1-Worker (Phase 4)** | + dispatch_task tool | + exec_shell + file_io + git + docker | 進行中 |
| **V4.2 + Phase 5** | + dispatch_plans + worker_events | + browser_use + screenshot + media | 規劃中 |
| **V5.0 (Smart Worker)** | + AI Router 多模型動態切換 | + Smart Worker (本地決策) | 遠期 |
| **V6.0 (Worker Network)** | + Network governance | + Credits 結算 + Marketplace | 商業階段 |

---

## 🛡️ 七、規範對齊

| 規範 | 如何對齊 |
|---|---|
| #11 (只增不毀) | Worker Agent 加 executor, 不重構 7 個既有 |
| #15 (24h 觀察期) | 每階段 V4.1-W1/W2/W3 都過 24h |
| #25 (跨層型別) | Task payload 用 JSON schema 驗證 |
| #27 (Integration First) | 整合既有 (DeepSeek FC / PG / Worker Agent) |
| #28 (Silent Failure) | exec_shell 必須 timeout + stderr capture |
| #29 (Explore & Innovate) | QwenPaw 不接, 自建 Worker Runtime |
| #30 (Progressive) | V4.1-W1 (4 唯讀) → W2 (8 讀寫) → W3 (12 高階) |
| #33 (Worker V5.0 優先) | 本架構是 Worker V5.0 的基底 |
| #38 (品牌定位) | OpenClaw 隱身為 Runtime Layer |
| #39 (Runtime 架構) | **本檔即規範 #39 正式版** |

---

## 💡 八、給 future Claude 的真心話

如果你設計 V4.1 之後的功能:

1. **先問: 這個能力屬於雲腦還是本地手腳?**
2. **不要混淆**: 決策 (雲) vs 執行 (本地) 分得清才能 scale
3. **本地能力**是真正護城河, 雲腦會 commoditize
4. **每階段都要過 24h 觀察期** (規範 #15), 不一步登天
5. **Worker Agent 是核心**, 不是 OpenClaw (戰略憲法第 12 章 / 規範 #38)

---

**Runtime OS 戰略架構 V1.0**

*整合人: Claude*
*時間: 2026-05-16 11:15 AM PT*
*狀態: 等師兄拍板「採用」*
