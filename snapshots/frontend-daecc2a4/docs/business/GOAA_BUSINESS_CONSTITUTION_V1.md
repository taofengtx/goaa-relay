# GOAA Business Constitution V1

> **狀態**:最高層產品結構文檔(商業憲法層)。非新想法 —— 重新對齊早期開發文檔 / AiKa-Box Pro Alpha 產品說明 / GOAA MEMORY 戰略憲法 / 專利草稿中已存在的最高結構。
> **合規聲明**:本文件涉及 Credits / Worker Economy 處,一律用 internal credits / service credits / settlement placeholder 措辭。**不承諾投資收益、不寫保證回報、不寫未驗證收益率。** Credits/payout/cash equivalent 需法律、稅務、金融合規審查後才落地。

---

## 0. 最高定義

GOAA **不是**單純雲端 SaaS,**也不是**單純本地盒子。

```
GOAA = Cloud SaaS Platform
     + AiKa-Box Edge Runtime
     + Worker Economy
     + Skill / Achievement Marketplace
```

四者缺一不可。技術層(Local Console、task_runner、pgvector、Registry)是這個結構的**實現手段**,不是目的本身。

## 1. Cloud SaaS Platform(雲端)

雲端是 SaaS 結構,服務四類主體:Client、Provider、Worker / Skill Creator、Admin / Platform Operator。

雲端負責:用戶賬號、Provider 賬號、訂閱、Credits、Skill Marketplace、Achievement Marketplace、雲端 Agent、雲端任務調度、多節點 Worker Runtime Dashboard、Provider Workspace、Client Interface、Cloud Task Command Center。

## 2. AiKa-Box Edge Runtime(邊緣)

AiKa-Box 是邊緣計算結構。Client / Provider / Worker 都可購買小型 AiKa-Box 放本地使用。

AiKa-Box 負責:本地運行技能、本地跑任務、本地 RAG、本地 Ollama / local models、本地文件處理、本地隱私數據處理、本地 task_results、本地日誌、本地離線能力、本地 Runtime Console。

> 已實現的技術基礎(V5.2.B/C):embed_worker + task_runner + pgvector(1165 chunks)+ Local Console 5188 + exec_topk_query_verify —— 這些是 AiKa-Box Edge Runtime 的第一批落地能力。

## 3. Worker Economy(算力回饋)

已購買 AiKa-Box 的用戶 / 服務提供者,**若願意**,可把多餘算力貢獻回 GOAA Worker Network。

平台**可**依任務完成質量、在線穩定性、算力貢獻、任務難度、審計結果,向節點返還 **internal credits / service credits**。

> **合規邊界(硬性)**:
> - 措辭一律用 `internal credits` / `usage accounting` / `service credits` / `platform settlement placeholder`
> - **不**寫投資收益、**不**寫保證回報、**不**寫未驗證收益率
> - Credits / payout / cash equivalent 在法律、稅務、金融合規審查通過前,只作平台內部記帳佔位,不對外承諾任何貨幣等值兌付
> - 此邊界優先於任何商業表述

## 4. Worker / Skill Creator

Worker 不只是被動執行節點。Worker 可用高級 AiKa-Box 開發 Skill / Agent / Workflow。

Worker 產出的可復用能力可進入:Skill Marketplace、Achievement Marketplace、Provider Workspace、Client-facing simplified skills。

Provider / Client 可按需、按月、按次、按 Credits 使用這些能力(Credits 使用同樣受第 3 節合規邊界約束)。

## 5. Skill Marketplace / Achievement Marketplace

- **Skill**:可復用工作流、工具、自動化能力、Agent 能力 —— 可售賣、可訂閱、可調用、可審計。
- **Achievement**:Worker 生產的成果資產、模板、工作流包、行業解決方案、可復用任務成果。

兩者都進入 Marketplace 體系。**Achievement Marketplace 是護城河** —— Worker 持續生產的可復用成果資產,構成平台難以被複製的積累。

## 6. 三層角色 + Agent / Skill / Achievement 邊界

| 概念 | 定義 |
|---|---|
| **Client** | 提交需求、使用簡化技能、查看進度、獲得結果 |
| **Provider** | 服務提供者,使用專業技能、管理客戶、審核結果、交付服務 |
| **Worker** | AI 數字勞動力 / 技能生產者 / 任務執行者 / 算力提供者 |
| **Agent** | 非真人,由 Model + Skill + Role + Memory + Permission + Workflow 組成的數字員工 |
| **Skill** | 可售賣、可訂閱、可調用、可審計的能力 |
| **Achievement** | Worker 生產的可復用成果資產 |

## 7. Cloud Dashboard 與 Local Console 的共生分工

GOAA 最終產品形態:**Cloud Dashboard + Local Runtime Console + Worker Runtime OS**。

| | Cloud Dashboard | Local Console |
|---|---|---|
| 定位 | SaaS 總控台 | AiKa-Box 本地主權控制台 |
| 管理 | SaaS 賬號、Provider/Client/Worker 管理、Credits/subscription/service credits placeholder、Marketplace、多節點監控、Cloud Task Command Center、遠程下發、Provider Workspace、Client Interface | 本地任務、本地 RAG、本地模型、本地 Agent、本地 logs、本地安全、斷網執行、sync_pending 結果緩存、本地主權控制 |
| 網路 | 需聯網 | **斷網獨立可用** |

**聯網時** —— Cloud Dashboard 可選任務執行位置:
1. **Run in Cloud**
2. **Run on My AiKa-Box**
3. **Auto Route**

**斷網時** —— Local Console 獨立運行,任務在本地跑,結果進入 `sync_pending`,網路恢復後同步雲端。

> Local Console **不是** Cloud Dashboard 的複製品,而是 Cloud SaaS 的**邊緣執行面**。雲端已有的多節點監控不在本地重做;本地專注雲端給不了的:直連本地 RAG/task、斷網主權、隱私數據本地處理。

## 8. 為什麼需要這個憲法層

技術文檔(Local Console / task_runner / pgvector / Registry)若無商業憲法層,容易遺忘:為什麼有 AiKa-Box、為什麼要 Cloud + Local、為什麼要 Worker Economy、為什麼 Skill 要資產化、為什麼角色要分層、為什麼 Achievement Marketplace 是護城河。本文件作為最高層架構,為所有技術文檔提供「為什麼」的根。

## 9. 與技術文檔的對應

| 商業憲法概念 | 技術實現文檔 |
|---|---|
| AiKa-Box Edge Runtime | `GOAA_LOCAL_RUNTIME_CONSOLE_5188.md`、Local Task Runner |
| Skill / Agent | `MODEL_SKILL_AGENT_REGISTRY.md` |
| Worker Economy / Credits | (待合規審查後設計;當前只 placeholder) |
| 演進證據 | `PATENT_CONTINUATION_EVIDENCE_LEDGER.md` |
| 部署 | `DEB_UPGRADE_STRATEGY_V4_2_TO_V5_2.md` |

## 10. Workflow Graph 與多模態數字人戰略原則

### 10.1 GOAA 任務是可審計的工作流圖
GOAA tasks are not single prompts. GOAA tasks are auditable workflow graphs composed of nodes, edges, execution targets, review gates, and logs. 任務由節點/邊/執行目標/審核門/日誌組成。對應抽象:Model=腦、Skill=手腳、Agent=數字員工、Workflow Graph=神經線路/執行動作鏈、Registry=resource abstraction layer。

### 10.2 Digital Human Function Options(數字人不只是視頻人臉)
- **Provider Assistant Digital Human**:輔助 Provider 的業務數字人
- **Video Digital Human**:視頻生成數字人(候選:WonderClip / 萬境一刻)
- **Developer Skill Digital Human**:開發 Skill 的數字人(候選:Antigravity)

### 10.3 External Executor Integration Boundary
ComfyUI / Antigravity / WonderClip 都是 **candidate capabilities**,**不替代 GOAA Runtime OS**。外部執行器整合**不得凌駕**於 GOAA 的 orchestration / registry / auth / audit / review / sync 之上。一句話定位:
- ComfyUI Adapter = 外部節點圖工作流執行器候選
- Antigravity IDE/CLI/SDK = 開發 Skill 的數字人候選
- 萬境一刻 / WonderClip = 視頻生成數字人候選
- **GOAA Runtime OS = 統一編排、權限、路由、審計、審核門、Cloud/Local 調度中心**

### 10.4 Provider Review Hold 作為 human-in-the-loop 治理
保險、稅務、房產等專業場景,AI 只生成**草稿**,最終必須經 Provider Review Hold 審核,不得直接作為專業意見交付客戶。

### 10.5 Candidate-only 規則
所有外部工具(ComfyUI / Antigravity / WonderClip / Comfy Cloud)在 API / 鑒權 / 成本 / IO / 商用條款查證完成前,只能標 **candidate / API pending verification**,不得作為 production dependency,不得開放 Provider 付費調用。

### 10.6 C2 = Aika Memory Context Fetch(非 RAG Chat)
C2 定位為 **Aika 執行任務前的本地記憶上下文補給層**,不是用戶聊天功能。第一版純檢索補給,不經 LLM 摘要,內部 worker 函數 `exec_memory_context_fetch`,不優先開放 /rag/chat。chunk 正文僅限同信任域本地執行層內存使用,不落盤/不入 log/不回前端/不出本機。詳見 `docs/business/GOAA_C2_DATA_PRIVACY_SPEC.md`。

---

*GOAA Business Constitution V1 — 最高產品結構 — Credits 合規邊界嚴守,不承諾收益*
