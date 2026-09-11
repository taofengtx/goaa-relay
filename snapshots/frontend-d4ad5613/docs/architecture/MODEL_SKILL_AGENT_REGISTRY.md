# GOAA Model / Skill / Agent Registry — 架構設計

> **狀態**:設計文檔(V5.2.C-1)。僅設計,不部署。
> **定位**:GOAA V5.2+ / V5.3 系統設置中,必須區分三類資源:Model(腦)、Skill(手腳)、Agent(數字員工)。

---

## 1. 三層概念

| 資源 | 比喻 | 定義 | 例子 |
|---|---|---|---|
| **Model** | 腦袋 | 負責推理和生成 | DeepSeek、Qwen、Claude、Ollama、通義千問、nomic-embed-text、qwen2.5:3b |
| **Skill** | 手腳 | 可調用的工具或工作流 | OCR、PDF 處理、發郵件、生成視頻、客戶跟進、dispatch_task、embed_corpus、top_k_search、exec_embed_corpus_full、exec_topk_query_verify |
| **Agent** | 數字員工 | 模型+技能+角色+記憶+權限+工作流,可直接承接某類任務 | 保險方案 Agent、房產內容 Agent、RAG 記憶查詢 Agent、雲端數字人 Agent、本地數字人 Agent |

關係:**Agent = Model + Skill + 角色 + 記憶 + 權限 + 工作流**。Model 和 Skill 是組件,Agent 是組裝好的成品。

> **商業結構定位**:Model / Skill / Agent Registry 服務於 **Skill Marketplace 與 Achievement Marketplace**。Skill 不是單純功能菜單,而是未來**可資產化、可訂閱、可調用、可審計**的能力;Agent 是可組合的數字員工;Achievement 是 Worker 產出的可復用成果資產(護城河)。完整產品結構見 `docs/business/GOAA_BUSINESS_CONSTITUTION_V1.md`。

## 2. Model Registry 字段

```
model_id
provider              # DeepSeek / Anthropic / Qwen / Ollama / ...
model_name
runtime               # local / cloud
capability            # chat / embedding / vision / ...
supported_execution_targets   # cloud | local | hybrid
enabled
local_or_cloud
cost_profile
default_for_task_type
```

## 3. Skill Registry 字段

```
skill_id
skill_name
skill_type
executor              # 對應 task_runner 的 handler 或外部工具
supported_execution_targets   # cloud | local | hybrid
input_schema
output_schema
permission_level
billing_mode          # api_cost | local_compute | credits placeholder | subscription
enabled
audit_required
```

**已實作的 Skill(對應 task_runner handler)**:`exec_embed_corpus_full`、`exec_topk_query_verify`。

## 4. Agent Registry 字段

```
agent_id
agent_name
agent_type
agent_deployment_type    # cloud / local / hybrid
agent_category           # digital_human / video_generation / marketing_content / training_content / rag_memory / workflow_agent
agent_provider           # Alibaba WonderClip / AiKa-Box Local / OpenAI / Anthropic / Qwen / other
agent_runtime            # external_api / local_worker / hybrid_router
bound_models
bound_skills
supported_execution_targets   # cloud | local | hybrid
permission_scope         # provider_only / internal_only / client_visible / admin_only
billing_mode             # api_cost / local_compute / credits / subscription
status                   # candidate / alpha / connected / published / disabled
enabled
```

## 5. Digital Human Agent 分類

### 5.1 Cloud Digital Human Agent(雲端數字人)

- **定義**:由外部雲端平台提供完整數字人視頻生成能力
- **代表**:萬鏡一刻 / WonderClip、HeyGen、Synthesia、D-ID、騰訊智影、火山引擎數字人
- **萬鏡一刻 / WonderClip 歸類**:`external_cloud_digital_human_agent`,狀態 `candidate / alpha`
- **用途**:數字人口播、營銷視頻、知識講解、Provider 視頻內容、保險方案/房產/稅務講解視頻、客戶教育、團隊培訓、社交短視頻
- **運行**:Cloud API

| GOAA 職責 | 外部 Cloud Agent 職責 |
|---|---|
| 腳本生成、行業知識庫、客戶資料整理、任務編排、權限控制、訂單管理、成本與 Credits 記錄、審計、結果交付 | 數字人口播、成片生成、語音合成、鏡頭編排、視頻渲染 |

> **注意**:萬鏡一刻 API / 鑒權 / 成本 / IO 格式未完成查證前,**不開放正式 Provider 付費調用**。第一版只作為 Agent Registry **candidate** 入庫。

### 5.2 Local Digital Human Agent(本地數字人)

- **定義**:由 AiKa-Box 本地執行的視頻/語音/圖像/數字人工作流
- **代表**:AiKa-Box Local Digital Human、本地 Ollama/Qwen、Wan、FLUX、PuLID、ComfyUI、本地 TTS、本地字幕/剪輯
- **定位**:隱私優先、低成本、可離線、可控,適合本地預覽與內部內容生成
- **場景**:內部培訓視頻、客戶敏感資料講解草稿、本地預覽版、低成本短視頻、離線演示、個人品牌內容
- **AiKa-Box 職責**:本地模型推理、本地素材處理、本地客戶資料保護、本地視頻生成、本地任務執行、本地緩存與審計

## 6. Cloud / Local Agent 路由策略

Provider 提交數字人視頻任務後,GOAA Agent Router 依以下條件選 Cloud 或 Local:

- 是否含敏感客戶數據
- 是否需商業級畫質
- 是否需快速交付
- 是否有預算
- 是否允許雲端處理
- 本地 AiKa-Box 算力是否足夠
- 是否需離線執行

**默認策略**:

| 條件 | 路由 |
|---|---|
| 高質量商業視頻 | Cloud Digital Human Agent(如萬鏡一刻/WonderClip) |
| 隱私 / 成本 / 離線優先 | Local Digital Human Agent(AiKa-Box 本地數字人) |

## 7. 第一版 Registry skeleton 範圍

V5.2.C-1 只做 **skeleton + 只讀展示**:
- Model Registry:列出 Ollama nomic-embed-text / qwen2.5:3b / DeepSeek / Qwen / Claude / 通義千問(只讀)
- Skill Registry:列出已實作的 exec_embed_corpus_full / exec_topk_query_verify + placeholder(OCR / PDF / send_email / video_generation placeholder)
- Agent Registry:列出 candidate(WonderClip = external_cloud_digital_human_agent / candidate)+ Local Digital Human(candidate)+ RAG Memory Agent + Provider Assistant Agent

V5.2.C-2 起再做 SQLite 持久化 + 可寫入。

## 8. Patent Continuation Evidence(Registry 作為證據)

Model/Skill/Agent 三註冊表,在專利語境下不是「商業菜單」,而是**可調度計算資源的抽象層**(resource abstraction layer):

- **Model/Skill/Agent 三註冊表** = 計算資源抽象層,將異構的推理模型、工具能力、組裝好的執行單元統一為可調度資源
- **Agent Registry 的 cloud/local/hybrid 字段** = 混合雲邊協同(hybrid cloud-edge orchestration)的證據
- **Skill executor 指向 task_runner allowlist handler** = tool invocation 受控執行,非任意 shell
- **Cloud/Local Agent Router** = 依資源/隱私/算力條件的動態路由機制

記錄時用技術語言,避免商業話術(不寫「幫保險人員賺錢」「分潤」「佣金」「客戶營銷自動化」)。WonderClip 在 API 查證前只作 candidate 占位。詳見 `docs/ip/PATENT_CONTINUATION_EVIDENCE_LEDGER.md`。

## 9. 補強說明(比原文檔更扎實處)

- **Skill 與 task_runner 的對應**:Skill Registry 的 `executor` 字段應指向 task_runner 的 allowlist handler 名,讓「Skill 註冊」和「task 執行」單一真相來源,避免兩處定義漂移。
- **Agent 的 bound_skills 應引用 skill_id**(而非複製 skill 定義),確保 Skill 改動時 Agent 自動跟隨。
- **billing_mode 與 Credits**:`credits` 模式需等 Credits 系統(本地不結算,雲端綁定後同步)成熟才啟用;第一版本地 task 用 `local_compute` 占位。
- **WonderClip candidate 邊界**:在查證 API/鑒權/成本/IO 前,Registry 裡 status 鎖 `candidate`,permission_scope 鎖 `internal_only`,不讓 Provider 誤觸發付費。

## Workflow Graph Layer(V5.4+ 設計)

> GOAA 任務不是單一 prompt,而是可審計的工作流圖。關係:Agent 調用 Skill → Skill 綁定 Workflow Graph → Graph 含多個 Node → Node 調用 Model/Tool/API/Local Task → Execution Engine 執行 → Audit Layer 記錄全程。

### 第一批 Node Types(12)
`input_node` / `ocr_node` / `extraction_node` / `rag_query_node` / `llm_analysis_node` / `compliance_check_node` / `decision_node` / `provider_review_node` / `form_draft_node` / `export_node` / `audit_node` / `sync_node`

### 候選 Executor(Adapter Layer)
`goaa_task_runner`(已有)/ `local_aikabox_executor` / `cloud_agent_executor` / `comfyui_adapter`(candidate) / `external_api_adapter`(candidate)

### Skill 新增字段
```
skill.workflow_graph_id          # 指向 Workflow Graph 模板(可為 ComfyUI template,read_only)
skill.supported_executors        # goaa_task_runner | comfyui_adapter | ...
skill.requires_provider_review   # 專業場景(稅/保險/房產)= true
skill.default_execution_target   # cloud | local | auto
```

### Agent 新增字段
```
agent.bound_workflows            # 引用 workflow_graph_id(不複製定義)
```

### Model 新增字段
```
model.allowed_node_types         # 該模型可承接的 node 類型
```

### Provider Review Hold — Stateful Breakpoint 字段
> 設計原則:workflow 執行到 `provider_review_node` 時,執行器**不得阻塞長期進程**等待人工。應持久化狀態、切 `STATUS_HELD_FOR_REVIEW`、釋放進程;Provider 在 Console/Dashboard approve/reject/modify/retry 後,Task Runner 從 `next_node_id` 斷點恢復。
```
workflow_status      # STATUS_HELD_FOR_REVIEW | running | done | failed
review_status        # pending | approved | rejected | modified | escalated
current_node_id
next_node_id
draft_output_ref
task_result_ref
review_actor
review_timestamp
resume_token
```

### Skill Black-box Encapsulation 字段(ComfyUI 隔離)
> Provider 端 Skill 只暴露最小 input schema;底層節點圖**內部、只讀、版本化**;Adapter 只對**已批准 placeholder** 做受控參數注入。Provider 不得編輯節點圖/模型路徑/採樣器內參/顯存參數/檔案路徑。
```
workflow_graph_id
template_status              # read_only
parameter_injection          # approved_placeholders_only
```

### Cost Guardrail 字段(Video Digital Human candidate)
> WonderClip/萬境一刻超出 internal candidate 前,必須定義成本網閘。不寫 Credits USD、不寫收益承諾、API pending verification 前不開放付費調用。
```
max_service_credits_per_task
rate_limit_per_provider
daily_task_limit_per_provider
max_video_duration_seconds
max_batch_size
requires_cost_estimate_before_dispatch
requires_provider_confirmation_above_threshold
execution_blocked_if_cost_unknown
```

### Sandbox Review Gate 狀態(Developer Skill Digital Human 產物)
> Antigravity 產物先寫 staging(`/opt/goaa/tasks/staging/`,設計占位,非已創建),審核前視為不可信。須過:git diff / test / redaction check / secret pattern / unsafe command / path safety / 人工審核 / rollback。**redaction check required before merge**(未實跑工具前不得寫 redaction_hits=0)。

## Digital Human Function Options

| 類型 | 候選 | 狀態 | 邊界 |
|---|---|---|---|
| **Provider Assistant Digital Human** | GOAA 內建 | 設計 | 輔助 Provider 業務 |
| **Video Digital Human** | WonderClip / 萬境一刻 | candidate / API pending verification | 不開放 Provider 付費調用,需成本網閘 |
| **Developer Skill Digital Human** | Antigravity (SDK/CLI/IDE/2.0) | candidate | **非 production executor、非部署權限、非 secret-bearing**;產物須過 Sandbox Review Gate |

> **ComfyUI 定位**:`external node-graph workflow executor candidate`。Adapter not replacement;Candidate first;GOAA owns orchestration;Provider sees Skill not node graph;No secret access。Local backend + Comfy Cloud backend 皆 candidate。**標記:high-priority candidate for V5.4/V5.5 Workflow Graph execution layer**(非已上線、非已驗證、非 Provider 可付費)。

---

*GOAA Model/Skill/Agent Registry — 設計文檔 V5.2.C-1 — 先設計不部署*
