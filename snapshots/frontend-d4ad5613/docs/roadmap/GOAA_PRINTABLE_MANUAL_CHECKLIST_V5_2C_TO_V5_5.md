# GOAA V5.2.C → V5.5 Printable Manual Checklist

> 本清單用於線下列印、手動打勾、階段簽核。不得寫入 secret、token、password、未核驗專利號或承諾性收益表述。
> 標記:`[x]` = 已完成(本工作期間實證);`[ ]` = 待做(線下手動勾)。
> 資料庫基準:**DO 上 postgres:16-alpine + pgvector 0.8.0**。

---

## A. V5.2.B Golden Baseline 數據對齊確認

- [x] V5.2.B Golden Baseline R1 已歸檔
- [x] corpus_all.jsonl 指紋已記錄(sha256 151bbb75…a494bd7,1080 行)
- [x] embed_worker.py 指紋已記錄(NormMD5 04633802…)
- [x] qwenpaw_memory_chunks 表結構已記錄
- [x] DO PostgreSQL postgres:16-alpine + pgvector 0.8.0 已確認
- [x] 1080 原始語料 / 1165 chunks 全量入庫已確認
- [x] dim=768 全量檢查已通過
- [x] top-k similarity query 已通過
- [x] secret 零洩漏記錄已歸檔

簽核人:________ 日期:________

---

## B. V5.2.C-1 Local Task Runner

- [x] task_runner.py 已歸檔(NormMD5 ec9fd0e0…)
- [x] exec_embed_corpus_full 已接入
- [x] exec_topk_query_verify 已接入
- [x] task_result JSON 已生成
- [x] runtime log 已生成
- [x] allowlist handler 已確認
- [x] 不返回 RAG 正文
- [x] 不讀取 worker_secrets.env 明文

簽核人:________ 日期:________

---

## C. V5.2.C-2 / V5.3 Local Runtime Console 5188

- [x] /opt/goaa/local-console/ 目錄規劃完成
- [x] FastAPI main.py 第一版完成(NormMD5 d77635bd…)
- [x] /health 完成並驗證(200)
- [x] /rag/stats 完成並驗證(total 1165 / dim 768)
- [x] /rag/topk 完成並驗證(不返正文)
- [x] /tasks/results 完成並驗證
- [x] /settings/models 完成並驗證(登入後 200)
- [x] /settings/skills 完成並驗證
- [x] /settings/agents 完成並驗證(WonderClip candidate)
- [x] local_user.db 不存明文密碼(argon2id)
- [x] argon2 hash 方案確認(argon2-cffi 25.1.0)
- [ ] Tailwind / CSS 生產本地化方案確認(待 .deb 打包階段)
- [x] 5188 第一階段僅綁定 127.0.0.1
- [x] Tailscale 100.114.37.90 綁定策略已審查(四階段,Auth 後才綁)
- [x] 不開公網

### V5.3 Console 實證(本批次完成)
- [x] 真實 Local Auth:argon2 + signed session + 三角色(401/200/401 驗證)
- [x] 受保護端點認證(/rag/*、/tasks/*、/settings/* 需登入,/health 公開)
- [x] Tailscale Phase 1:綁 100.114.37.90 + AiKa-1 跨設備 200 + Auth 生效
- [x] Stepper UI:輕量 workflow 狀態(非節點編輯器,不顯正文/secret)
- [x] 網頁登入頁 + authbar + 登出
- [x] systemd 自啟(goaa-local-console.service,User=aika,EnvironmentFile)
- [x] secret 分域:console.env(aika:aika 600)vs worker_secrets.env(root:root 600 未放寬)
- [x] **重啟實證:aika-core-01 reboot 後 Console 自我恢復 health 200**
- [ ] 更換 admin 密碼 + CONSOLE_SESSION_KEY(明文暴露過,建議後續)
- [ ] Tailscale Phase 1 systemd 自啟(需 After=tailscaled)

簽核人:________ 日期:________

---

## D. Cloud / Local Hybrid Task Command

- [x] execution_target schema 已定義(cloud/local/auto)
- [x] cloud / local / auto 三模式已定義
- [x] worker_id 指定邏輯已定義
- [x] fallback_policy 已定義
- [x] sync_pending 已定義
- [ ] Cloud Dashboard 任務下發窗口設計完成
- [ ] Local Console 斷網執行策略完成
- [ ] 網路恢復同步策略完成

簽核人:________ 日期:________

---

## E. Model / Skill / Agent Registry

- [x] Registry 設計文檔完成(含三層定義 + 字段)
- [x] supported_execution_targets 已加入
- [x] Skill executor 指向 task_runner allowlist handler
- [x] Agent bound_skills 引用 skill_id(不複製定義)
- [ ] Model Registry skeleton 落地(JSON/SQLite)
- [ ] Skill Registry skeleton 落地
- [ ] Agent Registry skeleton 落地
- [ ] WonderClip candidate 入庫(status=candidate,不開放調用)
- [ ] Local Digital Human candidate 入庫
- [ ] RAG Memory Agent 入庫
- [ ] Provider Assistant Agent 入庫

簽核人:________ 日期:________

---

## F. V5.3

- [ ] Cloud Auth OAuth2 設計完成
- [ ] portal.goaa.ai 綁定設計完成
- [ ] Credits / Provider 權限同步設計完成(credits placeholder)
- [ ] exec_memory_context_fetch 內部 worker 實作(C2 第一版,見 L 區)
- [x] C2 正文邊界策略完成:同信任域本地執行層內存,不落盤、不入 log、不回前端、不出本機
- [ ] sync_pending 同步策略完成
- [ ] Local Digital Human Beta 規劃完成

簽核人:________ 日期:________

---

## G. V5.4

- [ ] WonderClip API 查證完成
- [ ] API / SDK / 鑒權 / 成本 / IO 格式記錄
- [ ] External Agent Adapter 設計完成
- [ ] Cloud Digital Human Agent 路由完成
- [ ] Auto Route policy 完成

簽核人:________ 日期:________

---

## H. V5.5 — AI 工作區「對話 → 任務執行」(當前兩週目標)

> 當前開發主線:完成 AI Workspace 對話 → 任務執行管道,使 AI workspace 聊天能自動觸發結構化任務 dispatch。
> 兩週 deadline,默認 2 節點(local-aika-core-01 + local-aika-2)。
> 慢速升級規則:進度遲緩或 deadline 風險時向 Tao 申請拉入更多節點。

- [ ] `docs/runtime/GOAA_AI_WORKSPACE_CONVERSATION_TASK_FLOW_V0.1.yaml` — 規格文件創建
- [ ] `POST /tasks/run` allowlist-task dispatch 端點(Console)
- [ ] Conversation→Task Intent Detection:AI chat 自動識別用戶意圖並 dispatch
- [ ] Task schema 與 conversation session_id 綁定
- [ ] `exec_memory_context_fetch` C2 memory hydration 啟用
- [ ] `/rag/chat` 接入真實 RAG 上下文
- [ ] Local 端 task approval UI(approve/reject)
- [ ] Provider Workspace Agent Invocation 設計完成
- [ ] Provider 可選擇 Cloud vs My AiKa-Box
- [ ] 視頻生成任務流程完成
- [ ] cost / credits placeholder 審計完成
- [ ] Skill Marketplace 入口設計完成
- [ ] Achievement Marketplace 入口設計完成

簽核人:________ 日期:________

---

## I. Patent / IP 文檔體系

> 四份構成完整鏈條(策略 → 起草協議 → 草稿 → 證據)。全部無寫死專利號(已驗)。

**專利文檔(已存在於 repo):**
- [x] IP_DEFENSE_PATENT_STRATEGY.md(策略:entity/路線/成本/三層揭露,10 章)
- [x] PROVISIONAL_PATENT_DRAFT_PROTOCOL.md(起草協議,492 行,BLACKLIST/ALLOWED/DISCLAIMERS)
- [x] PROVISIONAL_PATENT_DRAFT_v3_EXAMINER_REVIEW.md(provisional 草稿已到 v3,908 行,含審查意見模擬)
- [x] PATENT_CONTINUATION_EVIDENCE_LEDGER.md(V4.2→V5.2 技術演進證據鏈)
- [x] 四份均無寫死 USPTO 專利號(合規已驗)
- [ ] 四份交叉引用對齊(策略↔草稿↔證據)
- [ ] entity status 律師核實(Micro/Small,提交前)
- [ ] 律師 review claim 與 specification
- [ ] 提交 USPTO provisional(取得 filing date / application number)

**.deb / Release Evidence:**
- [x] DEB_UPGRADE_STRATEGY_V4_2_TO_V5_2.md 創建
- [ ] RELEASE_NOTES 模板創建
- [x] .deb 不覆蓋 secrets 規則確認
- [x] .deb 不刪除 task_results / corpus / logs 規則確認
- [x] migration idempotent 規則確認
- [x] 每個 release 輸出 SHA256 / MD5 / filelist(規則確認)
- [x] 不寫未核驗專利號 / 不寫收益承諾

簽核人:________ 日期:________

---

## J. 前端 / Framer 官網(goaa.ai)

> 對比基準(2026-06-03 實抓 goaa.ai):線上仍為 Radison Framer 模板 + 半套中文 Hero。
> 設計藍圖:`docs/marketing/GOAA_PORTAL_CONTENT_MATRIX_V2.md`(4477 行,Section 8 Framer Notes / 12 Provider-First / 14 Skill Marketplace);`goaa_ai_framer_phase_A_emergency.md`。

**藍圖(已完成):**
- [x] V2.0 Marketing Matrix 藍圖(4477 行,commit 28c574f)
- [x] Provider-First 商業策略(Section 12)
- [x] Skill Marketplace 分層(Section 14)
- [x] Framer Implementation Notes(Section 8)
- [x] Hero 中文已上線(能做事能賺錢 / AI 數字龍蝦)

**執行(待做 — 線上仍是模板):**
- [ ] 移除 Radison 模板殘留(Services / Benefits / Testimonials 英文原文)
- [ ] 移除假評價 / 假人名(Jack Daniel / Justin Rocks 等)
- [ ] 價格改為 Provider Pro $39.99/mo(現為模板 $480 / $960)
- [ ] meta description 改為 GOAA 自有(現為 Radison 模板原文)
- [ ] 「Go with this plan」連結改為 GOAA(現連 framer 模板作者推廣連結)
- [ ] 三層生態(Client / Provider / Worker)內容上線
- [ ] AiKa-Box / Worker Economy 內容上線
- [ ] Skill / Achievement Marketplace 入口
- [ ] Framer 6 輪重構執行(Round 1-6)
- [ ] 合規:Credits 表述 placeholder、無收益承諾(上線前法務確認)

簽核人:________ 日期:________

---

## K. Workflow Graph / Digital Human Candidate Layer(V5.4+ 設計)

- [ ] workflow graph spec 定義
- [ ] 12 核心 node types 定義
- [ ] skill.workflow_graph_id 加入
- [ ] provider_review_node 定義
- [ ] provider_review_node stateful breakpoint 行為定義
- [ ] STATUS_HELD_FOR_REVIEW 定義
- [ ] resume_token / next_node_id 設計記錄
- [ ] audit node 定義
- [ ] sync_pending node 定義
- [ ] ComfyUI Adapter 標 candidate only
- [ ] Local ComfyUI backend 標 candidate
- [ ] Comfy Cloud backend 標 candidate
- [ ] Skill Black-box Encapsulation 定義
- [ ] parameter injection 限 approved placeholders
- [ ] raw ComfyUI workflow JSON 對 Provider/Client 隱藏
- [ ] Antigravity Developer Skill Digital Human 標 candidate
- [ ] Antigravity SDK / CLI / IDE / 2.0 子選項記錄
- [ ] Antigravity Sandbox Review Gate 定義
- [ ] redaction check required before merge
- [ ] unsafe command / secret pattern 檢查要求
- [ ] WonderClip / 萬境一刻 Video Digital Human 標 candidate
- [ ] API / auth / pricing / IO pending verification 記錄
- [ ] cost guardrail / rate limit gate 字段定義
- [ ] no production dependency added
- [ ] no secret touched
- [ ] no Provider paid callable Skill exposed
- [ ] no RAG 正文 exposed
- [ ] no fake Lines / Bytes / NormMD5 written

簽核人:________ 日期:________

---

## L. Aika Memory Context Fetch Layer(C2 記憶補給,設計階段)

- [x] C2 重定位:RAG Chat → Aika Memory Context Fetch
- [x] C2 設計文檔(20 節,純檢索補給不經 LLM)
- [x] 正文邊界精確化:同信任域本地執行層內存,八條負約束
- [ ] exec_memory_context_fetch(task_keywords)內部 worker(待實作)
- [ ] 優先長 chunk(1165 中 340 長 chunk)
- [ ] 強過濾 ChatML 噪音(249 短噪音)
- [ ] STOP_WORDS_SET 短句過濾
- [ ] 高密度短文本保留(模型名/端口/IP/編號)
- [ ] session 聚合(避免碎片)
- [ ] top_k 8-12 + max_context_chars
- [ ] 審計記 hash/chunk_ids 不記正文
- [ ] context_sha256 邊界誠實(無雲端 100% 宣稱)
- [ ] best-effort cleanup(非物理清零)
- [ ] 異常脫敏(無 raw log)
- [ ] ENABLE_MEMORY_FETCH 開關
- [ ] 第一版不開放 /rag/chat
- [ ] 第一版不經 LLM 摘要
- [ ] no secret touched / no cloud send

簽核人:________ 日期:________

---

## M. 五端產品導航 IA(2026-06-07)

- [x] Phase A — IA 文檔確認(GOAA_PRODUCT_NAVIGATION_IA_V1.md, V1.1)
- [x] 五端統一體系(Command Center/AiKa-Box Console/Worker/Providers/Clients)
- [x] 命名拍板(Agents→Providers / Providers→Worker / 數字人→AI Agents)
- [x] AI Workspace 統一規則 + 五端差異
- [x] 五端能力矩陣(Full/Limited/View Only/Hidden/N/A)
- [x] Cyber-Noir Design System(顏色/字體/組件)
- [x] V1.1 合規護欄(詞彙邊界/5188 telemetry/Review Hold/candidate 占位/可審計性)
- [x] Phase B 設計 — Cloud Dashboard IA 遷移(6-tab → 13 項 schema, golden backup 策略)
- [ ] Phase C — Local Console Cyber-Noir Skin
- [ ] Phase D — AI Workspace 組件化
- [ ] Phase E — 代碼實現(須 Tao 單獨確認)

簽核人:________ 日期:________

---

## N. AiKa-Box Dogfooding(B→C→D→A→E→F,2026-06-07)

### Phase C — Local Console Cyber-Noir UI(完成)
- [x] 本地 Console main.py 飽滿 UI(五頁:總覽/AI工作區/任務池/Node Health/損益審計)
- [x] 呼吸燈真實 LOGO(原圖 + 圓形淺底 + 圖片本身呼吸,彩色眼睛)
- [x] 副標 Worker Runtime OS V5.3
- [x] 頂部藍線左右流動 + 心跳線上下掃描
- [x] 後端 15 端點 + 認證零改動(只改 HTML/CSS)
- [x] Console UI 黃金版 fc76397d 入庫
- [x] **黃金版升級 fc76397d → 72e88cce(Node Health 真實化完成版)**

### B 線 — Node Health 真實化(完成)
- [x] B-1 /node/health 本機真實健康端點設計
- [x] B-1 psutil CPU/MEM/DISK 採集設計 + optional GPU fallback
- [x] B-1 service status sanitized 輸出設計
- [x] B-1 secret/env/RAG raw text 阻斷規則
- [x] B-2 /etc/goaa/nodes.json 靜態清單設計
- [x] B-2 /fleet/health 聚合設計 + timeout/offline/degraded 規則
- [x] B-2 第一版明確不做 LAN auto-scan / mDNS / UDP broadcast
- [x] UI Field Mapping + atomic write + stale 判定設計
- [x] **B-2 telemetry_writer.py + systemd 常駐(10s,psutil+nvidia-smi,atomic write,no secret)**
- [x] **B-3 /node/health 端點(需登入,讀 cache,stale/offline 判定,真實數據驗證)**
- [x] **B-4 UI 接真實數據(aika-core-01 本機卡 CPU/MEM/DISK/GPU/service,8s 刷新,正名)**
- [x] **B-5 reboot 自恢復驗證(四服務 active,cache 刷新 uptime 122s,/health 200,journal 無 secret)**

簽核人:________ 日期:________

---

## O. F-lite 半自動執行層(approval 持久化閉環,2026-06-13)

> **證據級別(#28 雙證據)**:Git Truth(commit 於 dev repo,git cat-file 驗證)+ Runtime Truth(2026-06-14 DO 生產 grep 確認 + 服務 active)。
> **DO 生產真相**:`/opt/goaa` HEAD = `1d67bd6`,goaa-router.service active。
> **架構債**:DO 生產 `/opt/goaa/router/api.py` 不由 `/opt/goaa/repo`(aika-node 部署線)追蹤;dev repo `infra/router/` 與生產檔需手動同步(memory #12 / 2a 里程碑 Backlog #1 記載)。

### F-lite 第一刀 — Secret Redaction 擴充
- [x] `f_lite_redact.py`:base_redact 5 pattern + F_LITE_PATTERNS 3 類(PG/SSH/sudo)
- [x] 單元測試 `test_f_lite_redact.py` 全自造假樣本 10/10 通過(無真實 secret)
- [x] 合入 main(commit f95eb8b,真實環境測過)

### F-lite 第二刀 — 2a approve 端點(POST /task/approve)
- [x] `ApproveReq`(task_id/approved_by/note,note max_length 2000)
- [x] 端點落地生產 Router `/opt/goaa/router/api.py`
- [x] note + approved_by 過第一刀 redaction(f_lite_sanitize,防審批備註夾帶 secret)
- [x] audit_log INSERT(target_id=NULL nullable 已查證,task_id 走 details JSONB,型別邊界 #25)
- [x] status 改動 + audit 包 try/except,audit 失敗回滾 status(避免狀態已 approved 但審計沒寫)
- [x] 端到端閉環:dispatch P0+risk4 → awaiting_approval → approve → approved + audit_written(真實 curl + PG 查詢,無 mock)
- [x] 邊界誠實標記:resume_behavior="pending_dispatcher_support"(不過度承諾)

### F-lite 第三刀 — approval 持久化(C + A + B)
- [x] **C:approve 端點 PG 持久化**(671c32f / DO 生產 grep `UPDATE tasks SET status='approved'` ✅)
      — UPDATE 先於 audit INSERT(失敗安全:UPDATE 掛則 except 回滾記憶體,PG+memory 一致)
- [x] **A:rebuild 重啟恢復 awaiting_approval**(22906de / DO 生產 db.py grep `awaiting_approval` ✅)
      — task_rebuild_pool status IN 加 awaiting_approval;刻意排除 approved(無消費點,#30);Rebuilt 真日誌驗證
- [x] **B:dispatcher 偵測即落盤**(0930806 / DO 生產 grep `task_upsert(tid, task)` ✅)
      — dispatcher 設 awaiting_approval 後 task_upsert + logger.error(非靜默 #28)

### 基礎設施 — systemd 埠競爭根治
- [x] **goaa-router.service ExecStartPre 埠清理**(d562d8c / systemctl 確認 fuser ✅)
      — ExecStartPre=-fuser -k 8080/tcp + sleep 2 + RestartSec=3;drop-in 不動主檔(#23)
      — 實證:假進程佔 8080 → start → ExecStartPre 清除 → Router 搶回 8080
- [x] goaa-router.service 主 unit 首次納入版控(infra/systemd/,原僅生產存在=架構債)

### 待做(無證據,維持未勾)
- [ ] F-lite 2b — reject 端點(複用 approve 模式)
- [ ] 5188 Console 審批 UI(依賴持久化就緒,現已具備前置)
- [ ] dev repo infra/ ↔ DO 生產 api.py 同步機制(架構債根治,memory #12)
- [ ] dispatcher 認 approved 狀態 + 真正執行(Worker 執行層,2a Backlog #3)

簽核人:________ 日期:________

---

## P. Security Gate — Authorization Kernel & Effect-Based Governance (2026-06-15)

> **狀態**: Authorization Kernel AK-1~AK-4 已全部發布並推送到 GitHub main。AK-5 未實現。
> **最高原則**: GOAA Runtime OS 的授權對象是動作效果(effect),而不是工具名稱。

### Authorization Kernel V0 Design
- [x] 正式設計文檔已發布:commit `20d0530`,SHA `154f3614`
- [x] 設計文檔 L1 最終只讀驗收已完成(2026-06-15,1277 行,27 節,4 附錄,0 blocking)
- [x] AK-1:Schema / Enum / Canonical Serialization — **已發布**(commit `296a789`)
- [x] AK-2:Deny Ledger Event-Sourced Model — **已發布**(commit `296a789`)
- [x] AK-3:Action Effect Classification + Attestation — **已發布**(commit `5d99956`)
- [x] AK-4:Pre-Action Gate — **已發布**(commit `99ec5e6`)
- [ ] AK-5:Capability Broker Integration — **尚未實現**

### Effect-Based Authorization Model
> 從 Tool-Based Limit 正式升級為 Effect-Based Authorization。
- [x] 14 execution action effects 已定義(READ / WRITE / CREATE / DELETE / RENAME / EXECUTE / COMMIT / PUSH / DEPLOY / SERVICE_RESTART / MOVE_OUT_OF_DISCOVERY / SECRET_READ / NETWORK_EGRESS / PERMISSION_CHANGE)
- [x] 4 control plane events 已定義(APPROVAL_REQUESTED / APPROVAL_DECIDED / POLICY_UPDATED / ROLE_CHANGED)
- [x] 13 equivalent action groups 已定義
- [x] 9 typed resource scopes 已定義
- [x] 11-step Pre-Action Gate architecture 已設計
- [x] Factual effect model:DEPLOY secondary effects = factually recomputed
- [x] Strictest policy merge:DENY > REQUIRES_APPROVAL > ALLOW
- [x] Action effect classification — **已實現**(AK-1/AK-2 classification_attestation.py)
- [x] Classification attestation — **已實現**(AK-2 classification_attestation.py)
- [x] Pre-action permission check — **已實現**(AK-4 pre_action_gate.py)

### Knife 2A-2 Status
- [x] Knife 2A-2 remains frozen (AK-1 through AK-4 reviewed and approved, 2A-2 separately frozen)
- [ ] Real subprocess Executor — **未開放**
- [ ] DO / Runtime deployment — **未批准**

### Governance Rules Applied
- [x] RULE-AUTH-01:Per-scope authorization verification
- [x] RULE-DENY-01:No equivalent-tool bypass
- [x] RULE-GIT-01:No commit without authorization
- [x] RULE-GIT-02:No push without authorization
- [x] RULE-FILE-01:File deletion requires full disclosure
- [x] RULE-UNTRACKED-01:Untracked ≠ deletable
- [x] RULE-STOP-01:Stop means stop

### Incident Record
- [x] Incident doc created:`docs/incidents/KNIFE2A1_UNAUTHORIZED_PUSH_20260615.md`
- [x] Commitment:technical content retained ≠ execution discipline excused

### Local Multi-Model Collaboration Infrastructure
- [x] 本地 Claude Code v2.1.178 — 已安裝,Claude Max 訂閱已認證
- [x] 本地 Gemini CLI v0.46.0 — 已安裝,個人 Google OAuth 已認證
- [x] 本地多模型協同 POC — 完整驗證通過(Claude編碼→Aika驗證→Gemini審核)
- [x] 隔離 detached worktree 協作流程 — 已實證可用
- [x] 完整協同流水線:ChatGPT→Aika worktree→Claude Code→Aika驗證→Gemini審核→ChatGPT裁決→Tao批准→Aika發布

### Next Development Line
- [ ] AK-5:Capability Broker Integration — **尚未實現**
- [ ] Real subprocess Executor — **未開放**
- [ ] Knife 2A-2 — **繼續凍結**
- [ ] DO / Runtime deployment — **未批准**

簽核人:________ 日期:________

---

## Q. Phase 2 Multi-Node Scheduling (A～K) — 已完成

> 本節記錄 Phase 2 多節點調度/並行節點加速主線開發全過程的已簽核狀態。
> 2026-06-21 整鏈完成,11 階段全部 CLOSED PASS,零安全違規。
> 關鍵文件全部在 origin/main 上,雙節點 ready。
> **Runtime Truth > Git Truth > Documentation Truth** 嚴格遵守。

### Q-1. Phase 2A — Node Registry V0.1 (2026-06-21)
- [x] `GOAA_NODE_REGISTRY_V0.1.yaml` 創建 → commit → PR #5 merge → post-merge verify
- [x] 8 節點盤點(5 local + 3 DO),多節點調度 Phase 0 只讀盤點完成

### Q-2. Phase 2B — Dispatch Protocol V0.1 (2026-06-21)
- [x] `GOAA_DISPATCH_PROTOCOL_V0.1.yaml` 創建 → commit → PR #6 merge → post-merge verify

### Q-3. Phase 2C — Worker Capability Matrix V0.1 (2026-06-21)
- [x] `GOAA_WORKER_CAPABILITY_MATRIX_V0.1.yaml` 創建 → commit → PR #7 merge → post-merge verify

### Q-4. Phase 2D — Readonly Dry Run Protocol V0.1 (2026-06-21)
- [x] `GOAA_READONLY_DRY_RUN_PROTOCOL_V0.1.yaml` 創建(438行) → commit → PR #8 merge → post-merge verify

### Q-5. Phase 2E — Local Readonly Dry Run Execution Plan V0.1 (2026-06-21)
- [x] `GOAA_LOCAL_READONLY_DRY_RUN_EXECUTION_PLAN_V0.1.yaml` 創建(420行) → commit → PR #9 merge → post-merge verify

### Q-6. Phase 2F-1 — Core-01 Local Readonly Dry Run Execution (2026-06-21)
- [x] 只讀探針在 local-aika-core-01 執行(identity/OS/network/repo/resource/console)
- [x] 14 項安全標誌全部 NO,0 違規

### Q-7. Phase 2F-2 — Aika-2 Local Readonly Dry Run Execution (2026-06-21)
- [x] 只讀探針在 local-aika-2 執行(identity/OS/network/resource)
- [x] DO 未連接,private key 未讀取,0 違規

### Q-8. Phase 2G — Aika-2 Repo / Worktree Capability Bootstrap (2026-06-21)
- [x] Repo bootstrap root 創建(`/home/tao/goaa-collaboration/repos/`)
- [x] GitHub read-only deploy key 認證 + SSH clone 成功
- [x] Repo 33M, HEAD `d0a152b`,5 Phase 2 文件確認
- [x] Private key 未讀取/複製/打印,DO 未連接

### Q-9. Phase 2H — Aika-2 Repo Readonly Verification & Two-Node Evidence Summary (2026-06-21)
- [x] Aika-2 repo readonly verify:HEAD matches origin/main ✅
- [x] 雙節點證據匯總:core-01 + aika-2 全部 CLOSED PASS
- [x] LOCAL_TWO_NODE_READONLY_READY=YES

### Q-10. Phase 2I — Local Two-Node Readonly Dispatch Simulation Plan V0.1 (2026-06-21)
- [x] `GOAA_LOCAL_TWO_NODE_READONLY_DISPATCH_SIMULATION_PLAN_V0.1.yaml` 創建(226行/7267字節)
- [x] commit `64c9cde` + push → PR merge(c217be0 在 origin/main)
- [x] 6 步模擬生命週期 + envelope schema + evidence schema + stop rules

### Q-11. Phase 2J — Local Two-Node Readonly Dispatch Simulation Execution (2026-06-22)
- [x] Core-01:simulated dispatch envelope 輸出(console only,無文件寫入)
- [x] Aika-2:repo readonly verification + evidence package 輸出
- [x] 6 Phase 文件全部確認,origin/main 已到 c217be0 ✅
- [x] 零安全違規

### Q-12. Phase 2K — Mainline Development Resume Gate (2026-06-22)
- [x] Phase 2A-2J 全部 CLOSED PASS,11/11 完成
- [x] 保留失敗證據(Vercel commit email failure,項目#10)
- [x] MAINLINE_RESUME_GATE=PASS ✅
- [x] 恢復主線開發:AI 工作區「對話→任務執行」,2 weeks deadline
- [x] 默認 2 節點(local-aika-core-01 + local-aika-2),慢速 escalation 規則就緒

### Q-13. 安全紀律貫穿記錄
- [x] 全程 secret 零洩漏(Tao 親手處理)
- [x] 全程不輸出 RAG 正文
- [x] 每個交付檔附 Lines + Bytes + SHA256
- [x] 不部署未經設計確認的東西
- [x] Console 與 Worker Daemon 解耦
- [x] 第一版本地優先:不開公網、不接真實支付、不接真實外部 Agent API
- [x] Runtime Truth > Git Truth > Documentation Truth 貫穿始終

### Q-14. 當前主線開發摘要(2026-06-22)
- [x] 主線目標:Aika Runtime OS AI 工作區「對話 → 任務執行」功能
- [x] 目標 deadline:2 weeks
- [x] 默認開發節點:local-aika-core-01 (控制台+worktree) + local-aika-2 (repo verify)
- [x] 慢速升級:若進度遲緩或 deadline 風險,向 Tao 申請拉入更多節點

簽核人:________ 日期:________

*GOAA V5.2.C → V5.5 Printable Manual Checklist — 線下手動打勾簽核 — 無 secret / 無專利號 / 無收益承諾*
