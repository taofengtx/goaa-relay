# GOAA V5.2.C → V5.5 Roadmap(整合更新)

> **狀態**:設計文檔。標記 ✅ 為已完成、⬜ 為待做。
> **戰略**:GOAA 要能上天(雲端 API、外部 Agent、多模型、多雲端智能體),也要能入地(AiKa-Box 本地執行、本地模型、本地記憶、本地任務、本地日誌、本地安全閉環)。當前 V5.2.C 階段 **先入地**。

---

## 最高產品結構(Business Constitution — 為何做這些)

> 本 roadmap 的技術項目,服務於 GOAA 的最高產品結構。完整定義見 `docs/business/GOAA_BUSINESS_CONSTITUTION_V1.md`。

```
GOAA = Cloud SaaS Platform + AiKa-Box Edge Runtime + Worker Economy + Skill / Achievement Marketplace
```

- **Cloud SaaS**:賬號/訂閱/Credits/Marketplace/多節點 Dashboard/Provider Workspace/Client Interface
- **AiKa-Box Edge Runtime**:本地技能/任務/RAG/Ollama/隱私數據/離線/Local Console(本 roadmap 的 V5.2.C 主軸)
- **Worker Economy**:AiKa-Box 多餘算力可貢獻回 Worker Network,依質量/穩定/貢獻/難度/審計返還 **internal credits / service credits**(合規審查前只 placeholder,不承諾收益)
- **Skill / Achievement Marketplace**:Worker 產出的可復用能力(Skill)與成果資產(Achievement)進入市場;Achievement Marketplace 是護城河

三層角色:Client(用需求)/ Provider(交付服務)/ Worker(數字勞動力+技能生產+算力)。Agent = 數字員工(Model+Skill+Role+Memory+Permission+Workflow)。

---

## 已奠定的基礎(V5.2.B → V5.2.C-1 至今)

- ✅ **V5.2.B Golden Baseline R1**:RAG 閉環 corpus → embed → pgvector → top-k(tag `v5.2b-golden-r1`)
- ✅ **全量 RAG 基線**:corpus 1080 → 分塊後 **1165 筆**入庫(dim768 全綠,13 sessions)
- ✅ **超長文本分塊能力**:embed_worker `_chunk_text`(1500 字/塊,overlap 150),failed 從 2 → **0**,131 分塊
- ✅ **V5.2.C-1 Local Task Runner**:`task_runner.py`,dispatch + task_result + runtime log
- ✅ **Skill: exec_embed_corpus_full**(寫入,task framework 化)
- ✅ **Skill: exec_topk_query_verify**(檢索驗證,不返正文,task framework 化)
- ✅ 全程 secret 只 Tao 親手、零洩漏、每步指紋驗證

---

## V5.2.C-1 — 靜態骨架與本地控制台架構確立

| 項目 | 狀態 |
|---|---|
| Local Task Runner(task_runner.py) | ✅ |
| exec_embed_corpus_full / exec_topk_query_verify 接入 | ✅ |
| GOAA Local Runtime Console 5188 架構設計文檔 | ✅(本批次) |
| Model/Skill/Agent Registry 設計文檔 | ✅(本批次) |
| FastAPI 門面搭建 | ⬜ |
| 本地三角色 login mock | ⬜ |
| /health、/rag/stats、/rag/topk verify | ⬜ |
| /tasks/results、/settings/{models,skills,agents} | ⬜ |
| 安全邊界實作 | ⬜ |
| 5188 systemd service draft | ✅(草案於 Console 文檔) |
| Agent/Model/Skill Registry skeleton | ⬜ |
| WonderClip candidate 入 Registry | ⬜ |
| Local Digital Human Agent candidate 入 Registry | ⬜ |

## V5.2.C-2 — 數據交互與嵌入任務自動化

- ⬜ 本地 task_results 可視化
- ⬜ SQLite 儲存 Model / Skill / Agent registry(從只讀 skeleton → 可寫)
- ⬜ Local Console 觸發 allowlist task(/tasks/run)
- ⬜ Console 對接已實作的兩個 task

## V5.3 — 雲端帳號綁定 + Cloud/Local Hybrid Task Command

### 已完成(Console 入地線)
- ✅ Console 真實 Local Auth(argon2 + session + 三角色 + 端點保護)
- ✅ Tailscale Phase 1(綁 100.114.37.90,跨設備可達 + Auth 生效)
- ✅ /settings 三註冊表端點(models/skills/agents)
- ✅ Stepper UI(輕量狀態)+ 網頁登入頁
- ✅ systemd 自啟(goaa-local-console.service,重啟自我恢復實證)

### C2 — Aika Memory Context Fetch(記憶補給層,設計階段)
- ✅ C2 設計文檔(重定位為記憶補給,純檢索不經 LLM)
- ⬜ `exec_memory_context_fetch(task_keywords)` 內部 worker 函數(待實作)
- ⬜ 優先長 chunk + 強過濾 ChatML 噪音(1165 chunks 中 249 短噪音)
- ⬜ session 聚合 + top_k 8-12 + max_context_chars
- ⬜ 正文限同信任域本地執行層內存(不落盤/不入 log/不回前端)
- ⬜ /rag/chat(用戶聊天)後續單獨設計,第一版不開放

### 雲端綁定線
- ⬜ **Cloud Task Command Center**
- ⬜ **execution_target schema**(cloud / local / auto 三模任務路由)
- ⬜ **sync_pending results**(斷網結果緩存,恢復網路後同步)
- ⬜ Cloud Auth OAuth2 握手
- ⬜ portal.goaa.ai 綁定
- ⬜ Provider 權限同步
- ⬜ Local Console 與 Cloud Dashboard 同步邊界

### 五端產品導航 IA(2026-06-07 新增)
GOAA 從單一 dashboard 升級為五端統一產品體系:Command Center / AiKa-Box Console / Worker / Providers / Clients。統一交互模塊 = AI Workspace;統一智能執行實體 = AI Agents。文檔:docs/product/GOAA_PRODUCT_NAVIGATION_IA_V1.md。
- ✅ **Phase A — IA 文檔確認**(五端導航 + 能力矩陣 + Cyber-Noir 設計系統 + 命名拍板 + 合規護欄,V1.1)
- ✅ **Phase B — Cloud Dashboard IA 重構設計**(現狀 6-tab → 目標 13 項遷移 schema,不動黃金版,留 golden backup;docs/product/GOAA_CLOUD_DASHBOARD_IA_MIGRATION_V1.md)
- ✅ **Phase C — Local Console Cyber-Noir Skin**(本地 Console main.py 飽滿 UI:呼吸燈真實 LOGO + 藍線流動 + 心跳掃描 + 五頁切換;黃金版 fc76397d)
- ⬜ Phase D — AI Workspace 組件化(五端複用)
- ⬜ Phase E — 代碼實現(須 Tao 單獨確認 + branch/diff/審計/rollback)

### AiKa-Box Dogfooding Roadmap(自舉開發路線圖,2026-06-07 確認)
最高目標:GOAA.ai 後續開發逐步遷移到第一台 AiKa-Box Pro Alpha 樣機上做真實開發/測試/運行, 形成對外案例「GOAA.ai 這個 SaaS 是用 AiKa-Box 本地盒子開發出來的」。工程誠實:非立刻完全取代 QwenPaw; QwenPaw 執行層逐步被 AiKa-Box AI Workspace + 半自動執行層吸收; secret/production/deploy 仍須 Tao 親手確認。
順序 **B → C → D → A → E → F**:
- ✅ **B 節點數據真實化**(Node Health 接真實本地 telemetry;Local Fleet Health Probe Protocol;B-1 設計✅ + B-2 telemetry_writer+systemd✅ + B-3 /node/health 端點✅ + B-4 UI 接真實數據✅ + B-5 reboot 自恢復驗證✅;aika-core-01 本機卡顯示真實 CPU/MEM/DISK/GPU/service,每 8s 刷新;Console UI 黃金版升級 fc76397d → 72e88cce)
- ✅ **C AI工作區接真實 LLM**(C.1 + D.1 閉環 6/9, 端到端真實 DeepSeek 對話)  # v1.2 2026-06-12
- 🟡 **D Cloud Binding**(鏈路通:心跳自 6/9 未斷, PG nodes 持久化; 閉環缺口: Router 實時狀態未完整 PG 化, 文檔未補)  # v1.2 2026-06-12
- ⬜ **A 補 SOON 頁做實**(Aika Memory/Logs/Settings/Cloud Binding)
- ⬜ **E 產品化**(AiKa-Box Pro Alpha $1299 出貨打包 / 安裝流程)
- ⬜ **F 半自動執行 + Dogfooding**(本次設計目標; 基礎: Router 生產 api.py 已內建風險引擎雛形: TASK_REVENUE risk 1-4 + select_model 高風險走 Claude + auto_dispatcher_loop P0/P1+risk≥4 阻擋, 對齊 P3-7 四級治理)  # v1.2 2026-06-12
- ⬜ 本地 GPU 推理能力擴展
- ⬜ Local Digital Human 進入 Beta

> **C2 定位說明(避免混淆)**:
> - `exec_memory_context_fetch` = **第一版 C2**,Aika memory hydration,internal worker,純檢索補給(見上方 V5.3 C2 區)
> - `/rag/chat` / `exec_rag_context_fetch` = **後續受控** RAG chat / LLM context injection,單獨設計,**非當前第一版**;當前 C2 不是聊天功能

### Task Schema(execution_target / fallback / network_mode)

```
execution_target : cloud | local | auto
worker_id        : aika-core-01 | do-cloud-1 | any
fallback_policy  : no_fallback | local_if_cloud_unavailable
                   | cloud_if_local_unavailable | queue_until_available
network_mode     : online | offline | sync_pending
```

示例任務:
```json
{
  "task_id": "v52c_embed_full_001",
  "task": "exec_embed_corpus_full",
  "execution_target": "local",
  "worker_id": "aika-core-01",
  "fallback_policy": "queue_until_available",
  "network_mode": "online",
  "params": {
    "corpus_path": "/opt/goaa/workers/corpus_all.jsonl",
    "target_table": "qwenpaw_memory_chunks"
  }
}
```

> 註:資料庫為 **DO 上 postgres:16-alpine + pgvector 0.8.0**(非本地 Docker PG)。Credits 相關一律 credits placeholder / cost placeholder / service credits placeholder。

## V5.4 — External Agent Integration + Auto Route

- ⬜ **Auto Route policy**(依條件自動選 cloud/local)
- ⬜ **cloud/local fallback**
- ⬜ 萬鏡一刻 / WonderClip 作為 Cloud Digital Human Agent **candidate**(API 待查證,不開放付費調用)
- ⬜ WonderClip cloud Agent routing
- ⬜ External Agent Adapter 設計
- ⬜ API / SDK / 鑒權 / 成本 / IO 格式查證

## V5.4 — Workflow Graph Layer + External Agent Integration

> **能力分層提醒(專業建議)**:外部執行器(ComfyUI/Antigravity/WonderClip)全為 candidate,排在 Workflow Graph Spec 之後。地基(Graph Spec + Provider Review Hold 機制)先行,外部執行器是它的後端候選,不得擠掉地基。

- ⬜ **Workflow Graph Spec**(nodes / edges / execution targets / review gates / logs)
- ⬜ **12 核心 Node Types**(input/ocr/extraction/rag_query/llm_analysis/compliance_check/decision/provider_review/form_draft/export/audit/sync)
- ⬜ **Executor Adapter Layer**(goaa_task_runner / local_aikabox_executor / cloud_agent_executor / comfyui_adapter / external_api_adapter)
- ⬜ **ComfyUI Adapter candidate**(external node-graph executor;local backend + Comfy Cloud backend 皆 candidate;不暴露給 Provider)
- ⬜ **Video Digital Human Agent candidate**(WonderClip/萬境一刻;API pending verification)
- ⬜ **Developer Skill Digital Human candidate**(Antigravity;非 production executor)
- ⬜ **Provider Review Hold — Stateful Breakpoint 設計**(STATUS_HELD_FOR_REVIEW + resume_token + next_node_id,不阻塞進程)
- ⬜ **Cost Guardrail / Rate Limit Gate 設計**(Video Digital Human candidate 成本網閘)
- ⬜ Auto Route policy + cloud/local fallback
- ⬜ External Agent Adapter / API / SDK / 鑒權 / 成本 / IO 格式查證

## V5.5 — Provider Workspace + Graph-backed Skills + Marketplace

- ⬜ **Skill 綁定 Workflow Graph**(skill.workflow_graph_id)
- ⬜ Provider Workspace 調用 graph-backed Skills
- ⬜ Digital Human function options(Provider Assistant / Video / Developer Skill)
- ⬜ ComfyUI local / cloud backend 評估
- ⬜ Antigravity SDK / CLI / IDE / 2.0 評估
- ⬜ WonderClip / 萬境一刻 API pending verification
- ⬜ **Skill Black-box Encapsulation**(Provider 只見最小 input schema,原始節點圖內部只讀)
- ⬜ **Sandbox Review Gate**(Antigravity 產物 → staging → git diff/test/redaction/secret/unsafe-cmd/path/人工審核/rollback)
- ⬜ Provider 可選 Cloud vs My AiKa-Box
- ⬜ Skill Marketplace / Achievement Marketplace 入口
- ⬜ cost / credits placeholder 審計

### V5.5 客戶可見性細則

- ⬜ 已購 AiKa-Box 的客戶看到「My AiKa-Box」;未購的看到「Cloud only / Buy or activate AiKa-Box」
- ⬜ 視頻生成任務流程(經 Video Digital Human candidate,API pending verification)

---

## 長期文檔關聯(V5.2.C 本批次新增)

| 文檔 | 用途 |
|---|---|
| `docs/ip/PATENT_CONTINUATION_EVIDENCE_LEDGER.md` | V4.2→V5.2 技術演進證據鏈,供一年後正式專利申請;技術語言、無商業話術、無專利號 |
| `docs/deployment/DEB_UPGRADE_STRATEGY_V4_2_TO_V5_2.md` | .deb 從 V4.2→V5.2 平滑升級;不覆蓋 secret/corpus、支持 rollback |

**V4.2 → V5.2 package evolution**:V4.2(基礎 worker)→ V4.5(AiKa-Box Pro Alpha)→ V5.1(LLM dispatch)→ V5.2(RAG embedding + task runner)→ V5.2.C(Local Console + Registry)。

**V5.2.C package split**:`aika-node-runtime`(worker)+ `aika-local-console`(optional console),分包確保 Console 故障不影響 Worker。

**V5.3 / V5.4 與專利 claim 關聯**:Model/Skill/Agent Registry(resource abstraction)、Cloud/Local Agent Router(hybrid orchestration)、External Agent Adapter 等技術特徵,作為未來 claim 的技術支撐,記入證據 ledger。

## 關鍵安全紀律(貫穿所有階段)

1. secret 只由 Tao 親手處理,只允許 SET/LEN 驗證,Aika/Claude/QwenPaw 不接觸明文
2. 不輸出 RAG 正文到聊天/前端/log
3. 每個交付檔附 Lines + Bytes + NormMD5,部署前驗指紋
4. 不部署未經設計確認的東西;每階段先設計、後實作、再驗證
5. Console 與 Worker Daemon 解耦:Console 崩潰不影響 task 執行
6. 第一版本地優先:不開公網、不接真實支付、不接真實外部 Agent API

## C2 的特別提醒(為何留到 V5.3+)

**(後續版,非第一版 C2)** `exec_rag_context_fetch`(把檢索到的正文餵給 LLM)是讓「對話窗用上 RAG 庫」的關鍵,但它涉及正文落地——必須單獨慎重設計:正文是否寫盤?是否只進內存注入 LLM 後即丟?誰有權看?如何審計?log 如何脫敏?這些決策關係到客戶資料安全,不能在實作其他功能時順手做。故明確排在 V5.3+,作為獨立設計題。**注:當前第一版 C2 是 `exec_memory_context_fetch`(純檢索、不經 LLM),此段描述的 LLM 注入版為後續受控功能。**

---

*GOAA V5.2.C → V5.5 Roadmap — 整合更新 — 先設計不部署*

## F-lite 進度更新 (2026-06-13)
- 第一刀 redact：✅ 合入 main (f95eb8b)，真實環境 10/10 測過
- 第二刀 2a approve：✅ 落地生產 Router (POST /task/approve)
  真實閉環：dispatch P0+risk4 → awaiting_approval → approve → approved + audit_written
  ⚠️ 架構債：在生產 router/api.py，未進 git，下次 deploy 需重新同步
- backlog：2b reject、approval 持久化、5188 審批 UI
