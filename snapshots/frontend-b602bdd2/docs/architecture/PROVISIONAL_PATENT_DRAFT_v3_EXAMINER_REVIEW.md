# PROVISIONAL_PATENT_DRAFT_v3_EXAMINER_REVIEW

> **本文角色**：對「GOAA Provisional Patent Draft v3 (101 Technical Rewrite, Attorney Review)」做 USPTO Patent Examiner 視角深度技術 review
> **本文類型**：Patent Review / Internal Analysis / Confidential Planning
> **是否為法律意見**：**否** — 本文非法律意見，所有 finding 須由 licensed U.S. patent attorney 確認
> **是否替代律師 review**：**否** — 本文為 attorney review 的補強輸入，不替代律師專業判斷
> **規範依據**：規範 #11 only-add / #14 v2 git-then-DO / #22 不暴露 secrets / #36 v2 Runtime Truth / #44 違規先記憶
> **配套文檔**：
>   - `docs/architecture/IP_DEFENSE_PATENT_STRATEGY.md` (commit `82a87b6`)
>   - `docs/protocols/PROVISIONAL_PATENT_DRAFT_PROTOCOL.md` (commit `dda91f0`)
>
> **被 review 的草稿**：`GOAA_Provisional_Patent_Draft_101_Technical_Rewrite_v3_Attorney_Review.pdf` (8 pages)
> **Reviewer 角色**：USPTO Patent Examiner 模擬（Software / AI Art Unit ~2126/2127, ~10 年資深 Examiner 視角）
> **Review 範圍**：35 U.S.C. § 101 / § 112 / § 102&103 初步觀察 + 15 candidate claims 逐條批註 + v4 rewriting 建議

---

**CONFIDENTIAL & PROPRIETARY**
**© 2026 GEER IT INC / GOAA.AI / AiKa Runtime OS. All Rights Reserved.**
**This document is a confidential internal review prepared for inventor and patent attorney consideration.**
**It does not constitute legal advice. Final determination of patentability, claim scope, and filing strategy must be reviewed by a licensed U.S. patent attorney.**

---

## 目錄

1. Executive Summary
2. Phase A — Protocol BLACKLIST Verification（已通過）
3. Dimension 1 — 35 U.S.C. § 101 Subject Matter Eligibility
4. Dimension 2 — 35 U.S.C. § 112 Enablement & Written Description
5. Dimension 3 — § 102 / § 103 Initial Prior Art Observations
6. Dimension 4 — 15 Candidate Claims 逐條批註
7. Dimension 5 — v4 Rewriting Recommendations
8. Overall Recommendation
9. Attorney Review Questions
10. Appendix A — § 101 Alice/Mayo Framework Quick Reference

---

## 1. Executive Summary

### 1.1 Overall Patentability Assessment（初步）

| 維度 | 評估 | Confidence |
|:---|:---:|:---:|
| **§ 101 Subject Matter Eligibility** | ✅ Likely Eligible (with refinement) | 中高 |
| **§ 112 Enablement** | ⚠️ Moderate — needs deeper technical disclosure | 中 |
| **§ 112 Written Description** | ✅ Adequate for provisional | 中高 |
| **§ 102 Novelty (initial)** | ⚠️ Several areas may have prior art exposure | 低（需專業 prior art search） |
| **§ 103 Non-Obviousness (initial)** | ⚠️ Combination claims need stronger differentiation | 低 |
| **Claim Scope Design** | ⚠️ Method claim weaker than system claim | 中 |

### 1.2 Key Findings 一句話總結

**正面**：
- 第 1 頁標題已「技術化」（State-Synchronized / Local Hardware / Persistent Ledger）— Section 101 友善
- Claim 1 引入 "physical edge worker appliances" + "one or more processors, memory" — 物理 hooks 強
- Specification 第 7 章九個子系統技術細節合理
- 沒有 means-plus-function 結構（避免 § 112(f) 風險）

**待強化**：
- Claim 11（method claim）缺乏明確 technical effect 描述
- DAG decomposition 技術細節不夠（容易被視為 abstract idea）
- "Persistent tool invocation ledger" 需更明確「technical advantage over conventional logging」
- "Provider Review Hold State" 在 Claim 9 較像「business rule」而非「technical state machine」

### 1.3 GO / NO-GO 判斷

**初步意見**：**GO with refinement**（建議律師 review 後修補後提交，**不建議當前版本直接提交**）。

---

## 2. Phase A — Protocol BLACKLIST Verification

按 `docs/protocols/PROVISIONAL_PATENT_DRAFT_PROTOCOL.md` 第 10 章自我審查，**v3 草稿已通過**：

| BLACKLIST 項 | 結果 |
|:---|:---:|
| 1. Micro Entity 確定句 | ✅ 全在 disclaimer 內 |
| 2. Patent Pending（未授權）| ✅ 明確禁止使用 |
| 3. 費用 / 收益 / 通過率 | ✅ 第 1 頁明示 avoidance |
| 4. 跳律師 | ✅ 反覆強調 attorney review required |
| 5. Secrets 暴露 | ✅ 第 1 頁明示 avoidance |
| 6. 真實 DO IP | ✅ 0 命中 |
| 7. PG credentials | ✅ 0 命中 |
| 8. SMTP credentials | ✅ 0 命中 |
| 9. Commit hash | ✅ 0 命中 |

**強制段落**：Disclaimer / Header / Footer / Candidate Claim 註記全部到位。

**v3 草稿已通過 Protocol 第 10 章驗證**，可進入深度技術 review。

---

## 3. Dimension 1 — 35 U.S.C. § 101 Subject Matter Eligibility

### 3.1 Alice/Mayo Two-Step Framework 分析

#### Step 1：Is the claim directed to a judicial exception?

> *Examiner's question: Are the claims directed to an abstract idea, law of nature, or natural phenomenon?*

**Claim 1（System Claim）分析**：

```
[Reviewing] A distributed computing system ... comprising:
  - cloud-based state-synchronized task orchestrator
  - one or more PHYSICAL edge worker appliances
  - sandbox runtime
  - local file-access abstraction adapter
  - persistent telemetry tool invocation ledger
```

**Examiner View**：
- ✅ 「PHYSICAL edge worker appliances ... one or more processors, memory」明確物理結構
- ✅ Sandbox runtime / local file-access abstraction adapter 是 technical components
- ⚠️ **但** "state-synchronized task orchestrator" 本質仍可被解讀為「organizing information」或「mental process」（Alice 風險點）

**裁定**：Step 1 可能進入 abstract idea grouping，但 **Step 2 有充足彈藥**。

**Claim 11（Method Claim）分析**：

```
[Reviewing] A computer-implemented method for state-synchronized cloud-to-edge execution, 
comprising:
  - receiving an input request at a cloud task orchestrator;
  - decomposing the input request into an ordered dependency graph;
  - storing the task structures in a task registry;
  - selecting an edge worker node;
  - retrieving an assigned task structure;
  - executing the assigned task structure within a sandbox runtime;
  - recording tool invocation telemetry;
  - returning a structured result.
```

**Examiner View**：
- ⚠️ **較大風險** — 「receiving / decomposing / selecting / retrieving / executing / recording / returning」**七個 abstract verb**，沒有對應到具體 technical effect
- ⚠️ 缺乏「**improvement to the functioning of a computer**」或「**improvement to a technology**」的明確 framing
- 比較 *Enfish v. Microsoft*（2016, Fed. Cir.）：claim 必須 directed to improvement in computer functionality

**裁定**：Method claim 在 Step 1 **較易被認定為 abstract idea**（organizing information / mental process）。

#### Step 2：Does the claim contain inventive concept "significantly more"?

**Inventive Concept 候選**：

1. ✅ **Physical edge worker appliance** with sandbox runtime + local file access adapter — **強 hook**
2. ✅ **Persistent transaction-level ledger** with result integrity metadata — **較強 hook**
3. ⚠️ **DAG-based task decomposition** — 中等 hook（DAG 本身不新，需強化 "DAG over heterogeneous worker types" 的具體技術效果）
4. ⚠️ **Provider Review Hold State** — 較弱 hook（容易被視為 business rule）
5. ⚠️ **Skill Lifecycle State Machine** — 較弱 hook（business workflow 嫌疑）

**裁定**：Step 2 **可以建立 inventive concept**，但需要 v4 強化「technical advantage」描述。

### 3.2 § 101 風險矩陣

| Claim # | Step 1 風險 | Step 2 強度 | 整體裁定 |
|:-:|:---:|:---:|:---|
| 1 (System) | 中 | 強 | ✅ Likely Eligible |
| 2 (DAG) | 中 | 中 | ⚠️ 需強化 |
| 3 (Sandbox) | 低 | 強 | ✅ Likely Eligible |
| 4 (File adapter) | 低 | 強 | ✅ Likely Eligible |
| 5 (Local execution) | 低 | 強 | ✅ Likely Eligible |
| 6 (Cryptographic hash) | 低 | 強 | ✅ Likely Eligible |
| 7 (Worker selection) | 中 | 中 | ⚠️ 需強化 |
| 8 (Role boundaries) | **高** | 弱 | ⚠️ Business method 風險 |
| 9 (Provider Review Hold) | **高** | 弱 | ⚠️ Business rule 風險 |
| 10 (Skill state machine) | 中 | 中 | ⚠️ Business workflow 嫌疑 |
| 11 (Method) | **高** | 中 | ⚠️ 較高風險 |
| 12 (Replay/rollback) | 中 | 中 | ⚠️ 需強化 |
| 13 (Local document) | 低 | 強 | ✅ Likely Eligible |
| 14 (Review Hold method) | **高** | 弱 | ⚠️ Business rule 風險 |
| 15 (CRM) | 中 | 中 | ✅ Likely Eligible（標準 Beauregard）|

### 3.3 § 101 重大風險點（律師必看）

#### 風險 1：Claim 8 「Role-Segmented Permission Architecture」

```
Claim 8: ... role-segmented permission architecture including a Worker execution boundary,
a Provider review boundary, and a Client progress boundary.
```

**Examiner 心聲**：「**Worker / Provider / Client 是 business label, 不是 technical artifact**」。即使說 "implemented as permissioned interfaces rather than business labels"，仍須在 Spec 內**強化 technical implementation**：
- 具體 authentication mechanism？
- 具體 access control matrix？
- 具體 runtime enforcement（e.g., per-endpoint authorization decorator）？

#### 風險 2：Claim 9 「Provider Review Hold State」

```
Claim 9: ... a Provider Review Hold State that prevents a generated output 
from being delivered to a client interface until a provider review action is recorded.
```

**Examiner 心聲**：「**This sounds like a business workflow, not a technical state machine**」。需要強化：
- State 是怎麼 enforced 在 runtime？（database constraint? middleware check?）
- "review action" 怎麼被 recorded？（cryptographic signature? immutable log?）

#### 風險 3：Method claim（Claim 11）缺 technical effect framing

需要明確的「**improvement to a technology or technical field**」陳述。

### 3.4 § 101 修補建議（v4 必加）

```
建議在 Spec 第 9 章「Technical Advantages」前加一個新章節:

  Section 8.5 — Computational Improvements Over Conventional Cloud-Only Architectures

  本系統相對於 conventional cloud-only AI orchestration 的技術改進:
  
  (a) Reduced bandwidth consumption — local sandbox execution avoids 
      transmitting raw files; only normalized output + telemetry is returned.
      Conventional systems: O(file_size). 本系統: O(metadata).
      
  (b) Reduced latency — local network context preservation avoids 
      cloud round-trip for state-dependent operations.
      Conventional: ~100-500ms cloud RTT per state check.
      本系統: ~1-10ms local execution.
      
  (c) Reduced cloud compute load — orchestrator delegates execution 
      to physical edge appliances, freeing cloud compute for orchestration.
      
  (d) Improved data locality — files may remain within provider-controlled 
      boundary, reducing data exposure surface.
      
  (e) Improved auditability — transaction-level ledger enables replay, 
      diagnosis, and rollback that conventional log-only architectures 
      cannot support.
```

**這個章節是 Alice Step 2 的最強彈藥**，律師 review 後若同意，建議寫入 v4。

---

## 4. Dimension 2 — 35 U.S.C. § 112 Enablement & Written Description

### 4.1 § 112(a) Enablement Analysis

> *Examiner's question: Does the specification enable a person having ordinary skill in the art (PHOSITA) to make and use the invention without undue experimentation?*

**已 enabled 的元件**：

| 元件 | Enablement 強度 | 評價 |
|:---|:---:|:---|
| Cloud task orchestrator | ✅ 中 | Spec 7.1 / 7.2 有合理描述 |
| Physical edge worker appliance | ✅ 高 | 第 6 章定義清晰 + 7.4 詳述 |
| Sandbox runtime | ✅ 中 | 7.4 描述 permission control，但未詳述 isolation mechanism |
| Local file access adapter | ⚠️ 低 | 7.4 描述太抽象，PHOSITA 可能無法實作 |
| Persistent tool invocation ledger | ✅ 中 | 7.6 有 column-level 描述 |
| DAG task decomposition | ⚠️ 低 | 7.2 描述 node fields 但缺乏 decomposition algorithm |
| Skill lifecycle state machine | ⚠️ 低 | 7.8 描述 states 但缺乏 transition rules |
| Provider Review Hold State | ⚠️ 低 | 7.7 描述 concept 但缺乏 implementation |

**重點缺口**：

#### 缺口 1：DAG decomposition algorithm

當前 Spec 只說「AI planning layer converts an unstructured request into a DAG」，**沒有具體 algorithm**。

**律師 review 時可能問**：
- AI planning 用什麼 model？
- Decomposition 是 rule-based 還是 LLM-based？
- 衝突 resolution 怎麼做？

**修補建議**：v4 第 7.2 加入 pseudo-code 或 algorithm 描述（即使是 high-level）。

#### 缺口 2：Sandbox isolation mechanism

當前 Spec 說「sandbox runtime enforces permission controls」，**沒有具體 isolation 技術**。

**修補建議**：v4 第 7.4 列舉具體 isolation 候選（containerization / namespace isolation / capability-based security / seccomp filter / firejail / Docker container 等抽象描述），保留實作彈性。

#### 缺口 3：Local file access adapter

當前描述「expose only approved directories」，但**沒說怎麼 expose**。

**修補建議**：v4 第 7.4 加 "may include filesystem chroot, bind mounts, capability-based file handles, or policy-driven access control lists"。

### 4.2 § 112(b) Definiteness Analysis

> *Examiner's question: Are the claim terms reasonably clear to PHOSITA?*

**清晰的 term**：
- ✅ "task structure" — 第 6 章有定義
- ✅ "edge worker node" — 第 6 章有定義
- ✅ "tool invocation ledger" — 第 6 章有定義

**可能 ambiguous 的 term**：
- ⚠️ "state-synchronized" — 沒有明確定義什麼叫 "synchronized"
- ⚠️ "provider-controlled computing environment" — "controlled" 邊界不清
- ⚠️ "controlled asynchronous communication channel" — "controlled" 邊界不清
- ⚠️ "permission class" — 定義不夠 enumerable

**修補建議**：v4 第 6 章 Definitions 加入這 4 個 term 的明確定義。

### 4.3 § 112(a) Written Description Analysis

**有 written description support 的**：
- ✅ Claim 1 → Spec 4 + 7.1
- ✅ Claim 3 (sandbox) → Spec 7.4
- ✅ Claim 4 (file adapter) → Spec 7.4
- ✅ Claim 6 (cryptographic hash) → Spec 7.6
- ✅ Claim 9 (Review Hold) → Spec 7.7
- ✅ Claim 10 (skill state machine) → Spec 7.8

**Written description 較弱的**：
- ⚠️ Claim 2 (DAG) → Spec 7.2 太抽象，需強化
- ⚠️ Claim 7 (worker selection criteria) → Spec 7.3 列了 criteria 但沒說 algorithm

---

## 5. Dimension 3 — § 102 / § 103 Initial Prior Art Observations

> **重要免責**：本節僅為 Examiner 初步印象，**非完整 prior art search**。律師必須做 independent prior art search（PatentScope, Google Patents, USPTO PAIR）。

### 5.1 可能相關的 prior art 領域

| 技術領域 | 風險度 | 代表性 prior art 方向 |
|:---|:---:|:---|
| **Distributed task scheduling** | 中 | Apache Airflow / Celery / Temporal — DAG task orchestration |
| **Cloud-edge computing** | **高** | AWS Greengrass / Azure IoT Edge / Google Distributed Cloud Edge |
| **Browser automation orchestration** | 中 | Selenium Grid / Playwright Cloud / Browserstack |
| **AI agent + tool calling** | **高** | OpenAI Function Calling / Anthropic Tool Use / LangChain |
| **Audit logging for distributed systems** | 中 | OpenTelemetry / Datadog APM / Honeycomb |
| **Sandbox execution** | 中 | gVisor / Firecracker / Docker / Kubernetes |
| **Workflow approval state machines** | 中 | Camunda / Apache Airflow approval gates / Workflow tools |

### 5.2 較高風險的 prior art 對應

#### Prior Art 風險 1：AWS Greengrass

AWS Greengrass 提供「cloud-orchestrated edge worker execution」，本草稿須在 v4 內**明確 distinguishment**：

| 維度 | AWS Greengrass | 本系統 |
|:---|:---|:---|
| Worker 類型 | IoT 設備 | 通用 mature hardware appliance |
| Task 類型 | 預定義 Lambda | DAG-decomposed AI tasks |
| Audit | CloudWatch logs | Transaction-level ledger with integrity metadata |
| Role boundaries | IAM | Runtime-enforced Worker/Provider/Client |

**律師建議**：在 v4 Section 3「Technical Background and Problem Statement」**明確點出與 Greengrass 等系統的技術差異**。

#### Prior Art 風險 2：AI Agent + Tool Calling

OpenAI / Anthropic / LangChain 都有 tool calling architecture。本系統的 **distinguishment** 應該是：

| 維度 | Generic Tool Calling | 本系統 |
|:---|:---|:---|
| Execution location | Cloud function | **Physical edge worker appliance** |
| Persistent ledger | 多為 conversation history | **Transaction-level with integrity metadata** |
| Local file access | 通常 sandbox | **Local file abstraction adapter with provider-controlled env** |
| Replay/rollback | 較弱 | **Ledger-driven replay/rollback workflow** |

**律師建議**：在 v4 Section 4「Summary of the Technical Solution」內加 paragraph 對比這些 generic tool calling 架構的限制。

#### Prior Art 風險 3：Apache Airflow

Airflow 也是 DAG-based task orchestration。**distinguishment**：

| 維度 | Apache Airflow | 本系統 |
|:---|:---|:---|
| Worker | Generic Python executor | **Physical edge appliance + sandbox + local file adapter** |
| Use case | Data pipeline | **AI agent + edge AI workflow** |
| Audit | XCom + log | **Transaction-level ledger + integrity hash** |
| State sync | Database-backed | **Cloud-to-edge state synchronization protocol** |

### 5.3 § 102 / § 103 修補建議（v4 必加）

```
建議在 Section 3「Technical Background and Problem Statement」加一段:

  3.5 — Limitations of Existing Approaches
  
  Existing cloud-edge orchestration systems (e.g., generic IoT edge platforms, 
  containerized worker pools, conventional AI agent frameworks) provide partial 
  solutions but exhibit one or more of the following technical limitations:
  
  (a) Edge nodes are typically purpose-built IoT devices, not mature 
      general-purpose hardware appliances suitable for office or service 
      provider workflows.
  
  (b) Audit logging is typically transaction-naive (e.g., CloudWatch-style 
      append-only event logs without per-tool-invocation integrity metadata),
      making transaction-level replay, rollback, and integrity verification 
      difficult.
  
  (c) Local file processing typically requires either uploading raw files to 
      a cloud endpoint or running a single-tenant agent on the edge device, 
      neither of which preserves both data locality and centralized 
      orchestration.
  
  (d) Permission boundaries are typically expressed as IAM policies or 
      role-based access controls applied at the API endpoint level, rather 
      than enforced as runtime state transitions distinguishing Worker, 
      Provider, and Client execution contexts.
  
  The disclosed invention addresses these limitations through ...
```

---

## 6. Dimension 4 — 15 Candidate Claims 逐條批註

### Claim 1 — Independent System Claim

> *A distributed computing system for state-synchronized cloud-to-edge task execution, comprising: a cloud-based state-synchronized task orchestrator configured to receive an input request, decompose the input request into an ordered dependency graph of machine-executable task structures, and store the task structures in a task registry; one or more physical edge worker appliances communicatively coupled to the task orchestrator through a controlled asynchronous communication channel; each physical edge worker appliance comprising one or more processors, memory, a sandbox runtime, a local file-access abstraction adapter, a local network interface associated with a provider-controlled computing environment, and a task reporting module; and a persistent telemetry tool invocation ledger configured to store transaction-level execution records including tool identifier, input schema, output telemetry, error state, duration, associated task identifier, associated worker identifier, and result integrity metadata.*

**✅ 強項**：
- "physical edge worker appliances ... one or more processors, memory" — 強物理 hook
- 「sandbox runtime + local file-access abstraction adapter + local network interface」三件套 — strong technical components
- "result integrity metadata" — 較新穎的 audit hook

**⚠️ 改進建議**：
1. 「controlled asynchronous communication channel」太抽象，可改為：「a network protocol selected from secure polling, long-polling, message queue, webhook, or WebSocket」
2. 「task registry」未明確 — 加 "comprising a relational database or equivalent persistent storage"
3. 考慮加入 limit：「wherein the result integrity metadata comprises at least one of a cryptographic hash, checksum, or digital signature」

**§ 101 評**：✅ Likely Eligible

---

### Claim 2 — DAG Dependency

> *The system of Claim Concept 1, wherein the ordered dependency graph is a directed acyclic graph in which graph nodes correspond to tool invocation tasks and graph edges correspond to execution dependencies.*

**✅ 強項**：清晰明確
**⚠️ 改進建議**：
- 加 narrowing："wherein the DAG is generated by a language model based on natural language interpretation of the input request, **and validated against a schema of available tools in the task registry**"

**§ 101 評**：⚠️ 中度風險 — DAG 本身在 prior art 很多（Airflow / DAGs），需在 Spec 強化「DAG over heterogeneous worker types」的新穎性

---

### Claim 3 — Sandbox Permission

> *The system of Claim Concept 1, wherein the sandbox runtime restricts task execution according to a permission class associated with the assigned task structure.*

**✅ 強項**：簡潔有力
**⚠️ 改進建議**：
- 加 dependent claim 列舉 permission class："wherein the permission class is selected from at least one of: read-only system inspection, read-only file query, write-restricted local document processing, network-restricted browser automation, container execution, or local model inference"

**§ 101 評**：✅ Likely Eligible

---

### Claim 4 — Local File Access Adapter

> *The system of Claim Concept 1, wherein the local file-access abstraction adapter exposes only approved local file directories or file handles to the sandbox runtime.*

**✅ 強項**：technical
**⚠️ 改進建議**：
- 加 implementation 候選："wherein the adapter is implemented using at least one of: filesystem namespace isolation, bind-mount restrictions, capability-based file handles, or policy-driven access control lists"

**§ 101 評**：✅ Likely Eligible

---

### Claim 5 — Edge Worker Operations

> *The system of Claim Concept 1, wherein the edge worker node executes OCR processing, document field extraction, browser-runtime operations, containerized tools, local inference operations, or local network-context-dependent operations within a provider-controlled local environment.*

**✅ 強項**：列舉具體 operations
**⚠️ 改進建議**：
- 拆成多個 dependent claim（每個 operation 一條）— 增加 claim count，給律師更多 fallback 空間

**§ 101 評**：✅ Likely Eligible

---

### Claim 6 — Result Integrity

> *The system of Claim Concept 1, wherein the persistent tool invocation ledger stores a cryptographic hash, checksum, or integrity metadata associated with a task result.*

**✅ 強項**：cryptographic hash 是強 hook
**⚠️ 改進建議**：
- 加 dependent："wherein the cryptographic hash is computed using a one-way hash function selected from SHA-256, SHA-3, or Blake2"
- 考慮加："wherein the ledger is append-only and the hash chain links sequential tool invocations into a tamper-evident sequence"（**這個會大幅提升新穎性！**）

**§ 101 評**：✅ Likely Eligible
**🌟 重要建議**：**Hash chain / Merkle tree 結構是強差異化點**，律師可考慮加入

---

### Claim 7 — Worker Selection

> *The system of Claim Concept 1, wherein the task orchestrator selects an edge worker node based on availability, execution capability, locality requirement, permission class, historical reliability, data sensitivity, or runtime telemetry.*

**⚠️ 風險**：列舉的 selection criteria 太多（7 個）+ 「or」連接 — Examiner 可能認為太 broad
**⚠️ 改進建議**：
- 拆成多個 dependent claim（每個 criterion 一條）
- 或改為 "based on a weighted combination of [criteria]"

**§ 101 評**：⚠️ 中等 — Selection algorithm 本身可能被視為 abstract

---

### Claim 8 — Role-Segmented Permission Architecture

> *The system of Claim Concept 1, further comprising a role-segmented permission architecture including a Worker execution boundary, a Provider review boundary, and a Client progress boundary.*

**🔴 高風險**：Worker / Provider / Client **聽起來像 business labels**

**⚠️ 改進建議**（必改）：
- 強化 technical implementation：「**wherein each boundary is implemented as a separate runtime permission domain enforced by authentication middleware and per-endpoint authorization decorators**」
- 加 Spec support 在 7.7 章

**§ 101 評**：🔴 **建議律師考慮從 independent claim 移除**，或徹底重寫

---

### Claim 9 — Provider Review Hold State

> *The system of Claim Concept 8, wherein the Provider review boundary includes a Provider Review Hold State that prevents a generated output from being delivered to a client interface until a provider review action is recorded.*

**🔴 高風險**：聽起來像 business workflow

**⚠️ 改進建議**：
- 強化 "review action is recorded" 的 technical 性：「**recorded as an immutable database transaction with cryptographic signature**」
- 強化 "prevents delivery" 的 technical 性：「**enforced by a runtime delivery gate that consults the database state before serving output to the client interface**」

**§ 101 評**：🔴 **較高風險** — 需在 Spec 7.7 內強化 technical implementation

---

### Claim 10 — Skill Lifecycle State Machine

> *The system of Claim Concept 1, further comprising a skill lifecycle state machine configured to transition a reusable workflow capability between draft, testing, review, published, paused, upgraded, rolled back, archived, or deprecated states.*

**⚠️ 風險**：State machine 本身不新穎，draft → testing → review → published 在很多 workflow 工具都有

**⚠️ 改進建議**：
- 強化 differentiation：「**wherein each state transition is associated with a tool invocation record in the persistent ledger and a cryptographic version identifier**」
- 強化 connection 到 Claim 1 的 ledger

**§ 101 評**：⚠️ 中等 — 需 strong differentiation

---

### Claim 11 — Independent Method Claim

> *A computer-implemented method ... comprising: receiving an input request ...; decomposing ...; storing ...; selecting ...; retrieving ...; executing ...; recording tool invocation telemetry ...; and returning a structured result.*

**🔴 較大風險**：缺乏明確 technical effect

**⚠️ 改進建議**（必改）：
- 加 introductory 段落 emphasize improvement：「**wherein the method improves computational efficiency in distributed AI execution by ...**」
- 加 wherein clauses 強化 technical effect：
  - "wherein the decomposing reduces total cloud computation by delegating execution to edge workers"
  - "wherein the executing preserves data locality by processing files within a local file boundary"
  - "wherein the recording enables transaction-level audit, replay, and rollback"

**§ 101 評**：🔴 **較高風險** — Method claim 是 § 101 最易被 reject 的 claim type

---

### Claim 12 — Ledger Replay/Rollback

> *The method of Claim Concept 11, further comprising using the persistent tool invocation ledger to replay, diagnose, retry, or roll back a failed task.*

**✅ 強項**：將 ledger 連結到具體 use case
**⚠️ 改進建議**：
- 加 narrowing：「**wherein replay comprises retrieving the original input schema from the ledger, re-executing the tool with the same input, and comparing the new output integrity metadata against the original**」

**§ 101 評**：⚠️ 中等

---

### Claim 13 — Local Document Processing

> *The method of Claim Concept 11, further comprising processing a local document within an approved local file boundary and returning normalized extracted fields or metadata without transmitting the raw file to the cloud task orchestrator unless authorized.*

**✅ 強項**：明確的 data locality 技術效果

**⚠️ 改進建議**：
- 加 "wherein the normalized extracted fields are determined by a schema specified in the task structure"

**§ 101 評**：✅ Likely Eligible

---

### Claim 14 — Review Hold Method

> *The method of Claim Concept 11, further comprising storing a generated output in a Provider Review Hold State until provider approval, modification, rejection, or escalation is recorded.*

**🔴 高風險**：跟 Claim 9 同樣問題（business rule 嫌疑）

**⚠️ 改進建議**：
- 同 Claim 9 — 強化 technical enforcement

**§ 101 評**：🔴 **較高風險**

---

### Claim 15 — Non-Transitory CRM

> *A non-transitory computer-readable medium storing instructions that, when executed by one or more processors, cause a distributed computing system to perform the method of Claim Concept 11.*

**✅ 強項**：標準 Beauregard claim，無 § 101 風險
**⚠️ 改進建議**：無 — 此 claim 標準格式

**§ 101 評**：✅ Likely Eligible（標準 CRM claim）

---

### 6.16 Claim 設計總結

```
強度排序 (高 → 低):
  Tier A (✅ Strong):
    1, 3, 4, 5, 6, 13, 15
  
  Tier B (⚠️ Needs Refinement):
    2, 7, 10, 12
  
  Tier C (🔴 High Risk, Consider Restructuring):
    8, 9, 11, 14
```

**律師策略建議**：
- Tier A 7 條 → core claims，保留並強化
- Tier B 4 條 → 補 narrowing language
- Tier C 4 條 → 重寫或考慮移除

---

## 7. Dimension 5 — v4 Rewriting Recommendations

### 7.1 必加的 5 個新段落（按優先級）

#### 7.1.1 Section 3.5（前文已給）— Limitations of Existing Approaches

對抗 § 102 / § 103 prior art 的最強彈藥。**律師同意後寫入**。

#### 7.1.2 Section 8.5（前文已給）— Computational Improvements

對抗 § 101 Alice Step 2 的最強彈藥。**律師同意後寫入**。

#### 7.1.3 Section 7.6.5 — Hash Chain / Merkle Tree Ledger Structure（新增）

```
Section 7.6.5 — Ledger Integrity through Hash Chaining

In one embodiment, the persistent tool invocation ledger maintains 
cryptographic integrity through hash chaining. Each ledger entry stores:

  - prev_hash: hash of the previous ledger entry
  - tool_call_id: unique invocation identifier
  - input_hash: hash of the input schema  
  - output_hash: hash of the output result
  - entry_hash: hash of (prev_hash || tool_call_id || input_hash || 
                       output_hash || timestamp || worker_id)

This chained structure creates a tamper-evident sequence. Modification 
of any historical entry invalidates all subsequent entry_hash values, 
enabling integrity verification through hash chain replay.

Alternative embodiments may use Merkle tree structures for batch 
integrity verification, append-only event sourcing, or blockchain-style 
distributed consensus where multiple worker nodes co-sign critical 
ledger transactions.
```

**為什麼必加**：
- 提升 Claim 6 新穎性
- 對抗 conventional logging prior art
- Examiner 喜歡看到 cryptographic technical detail

#### 7.1.4 Section 7.7.5 — Runtime-Enforced Permission Domains（新增）

```
Section 7.7.5 — Runtime-Enforced Permission Domain Implementation

In one embodiment, the role-segmented permission architecture is 
implemented as follows:

  1. Each runtime endpoint is associated with a permission domain 
     attribute (Worker / Provider / Client).
  
  2. Incoming requests are authenticated using bearer tokens, 
     session cookies, mutual TLS, or equivalent mechanisms.
  
  3. The authenticated principal's role is checked against the 
     endpoint's permission domain attribute by an authorization 
     middleware before request handling.
  
  4. Cross-domain operations require explicit elevation tokens 
     recorded in the persistent ledger.
  
  5. Role transitions are logged as ledger entries with 
     cryptographic integrity metadata.

This implementation distinguishes the disclosed system from 
conventional IAM/RBAC schemes by tying role boundaries to:

  (a) Runtime state transitions rather than static API permission lists
  (b) Persistent ledger records for cross-domain operations  
  (c) Distinct execution boundaries (Worker execution, Provider review, 
      Client viewing) enforced as separate runtime state machines
```

**為什麼必加**：
- 強化 Claim 8 / 9 / 14 的 technical 性
- 對抗 "business labels" 質疑

#### 7.1.5 Section 7.2.5 — DAG Generation Algorithm（新增）

```
Section 7.2.5 — DAG Generation Algorithm

In one embodiment, the AI planning layer generates the DAG through 
the following steps:

  1. Parse the input request using a language model to extract 
     intent, entities, and required operations.
  
  2. Query the task registry for available tools matching the 
     extracted operations.
  
  3. Generate candidate task nodes for each operation, populating 
     task_id, tool_id, input_schema, output_schema, and 
     permission_class.
  
  4. Establish dependency edges based on:
       - Input/output schema matching (output of A feeds input of B)
       - Tool prerequisite metadata (tool B requires tool A's output)
       - Permission elevation requirements
       - Provider review requirements
  
  5. Validate the resulting graph for:
       - Acyclicity (no circular dependencies)
       - Closure (all required inputs are available or generatable)
       - Schema consistency (output schema of source node matches 
         input schema of dependent node)
  
  6. Optionally optimize execution order through topological sort 
     with locality, latency, and worker availability constraints.
```

**為什麼必加**：
- 強化 Claim 2 enablement（§ 112(a)）
- 加 Spec written description support

### 7.2 必改的 4 個 Claim（按優先級）

| Claim | 修改方向 |
|:---:|:---|
| **11** (Method) | 加 technical effect framing：「wherein the method improves [specific metric]」|
| **8** (Role boundaries) | 加 implementation：「each boundary is implemented as ... runtime permission domain ...」|
| **9** (Review Hold) | 強化 technical enforcement：「enforced by a runtime delivery gate consulting database state」|
| **6** (Cryptographic hash) | 加 hash chain：「append-only ledger with hash chain linking sequential invocations」|

### 7.3 v4 結構建議

```
v3 結構 (12 章 + 2 appendix):
  1. Title
  2. Field
  3. Background
  4. Summary
  5. Drawings
  6. Definitions
  7. Detailed Description (10 subsections)
  8. Example Workflows (4 subsections)
  9. Technical Advantages
  10. Candidate Claims (15 claims)
  11. Abstract
  12. Confidentiality

v4 建議結構 (新增 3 sub-sections + 修補):
  1. Title (no change)
  2. Field (no change)
  3. Background
     3.1-3.4 (existing)
     3.5 [NEW] Limitations of Existing Approaches
  4. Summary (slight rewrite for clarity)
  5. Drawings (no change)
  6. Definitions
     + 加 4 個 ambiguous terms 定義
  7. Detailed Description
     7.1-7.10 (existing)
     7.2.5 [NEW] DAG Generation Algorithm
     7.6.5 [NEW] Ledger Integrity through Hash Chaining
     7.7.5 [NEW] Runtime-Enforced Permission Domain Implementation
  8. Example Workflows
     8.1-8.4 (existing)
     8.5 [NEW] Computational Improvements Over Conventional Architectures
  9. Technical Advantages (rewrite to mirror 8.5)
  10. Candidate Claims (with 4 修改 + 補 dependent claims)
  11. Abstract (slight rewrite)
  12. Confidentiality (no change)
  + Appendix A/B (slight update)
```

**v4 預估 pages**：8 → 12-14 pages（增加部分為 technical depth）

---

## 8. Overall Recommendation

### 8.1 律師評估表（建議律師對照這個表 review）

| 評估項 | 當前 v3 狀態 | 律師建議行動 | 預估工時 |
|:---|:---:|:---|:---:|
| § 101 Subject Matter Eligibility | ⚠️ Moderate | 加 Section 8.5 Computational Improvements | 2-3h |
| § 112 Enablement | ⚠️ Moderate | 加 Section 7.2.5 DAG Algorithm + 7.6.5 Hash Chain + 7.7.5 Permission | 3-4h |
| § 112 Definiteness | ⚠️ Moderate | 補 4 個 term 定義 | 1h |
| § 102 / § 103 distinguishment | ⚠️ Moderate | 加 Section 3.5 Limitations of Existing Approaches | 2h |
| Claim 1 (System) | ✅ Strong | 微調 wording | 30 min |
| Claim 11 (Method) | 🔴 High Risk | 重寫加 technical effect framing | 1.5h |
| Claims 8/9/14 (Role/Review) | 🔴 High Risk | 強化 technical enforcement language | 1.5h |
| Tier A claims (1,3,4,5,6,13,15) | ✅ Strong | 補 narrowing dependent claims | 1.5h |
| 總工時估算 | | | **13-17h** |

### 8.2 提交前必做 checklist（給律師）

- ☐ 完成 v4 rewriting（按 Section 7 建議）
- ☐ 完整 prior art search（PatentScope / Google Patents / USPTO PAIR）
- ☐ § 101 Alice Step 1/Step 2 詳細分析（針對每個 independent claim）
- ☐ § 112 enablement 對 v4 重新評估
- ☐ Claim 11 重寫加 technical effect
- ☐ Inventor / Assignee / Entity Status 確認（按 IP_DEFENSE_PATENT_STRATEGY.md 第 2 章 5 項 checklist）
- ☐ Final 律師 sign-off

### 8.3 提交時程建議

| 階段 | 預估工時 | 累計 |
|:---|:---:|:---:|
| 律師初次 review v3 + 本文 | 2-3h | 3h |
| Tao + 律師 v4 改寫 collaboration | 4-6h | 9h |
| 律師完成 v4 + claim 設計 | 6-8h | 17h |
| 律師 final review + filing prep | 2-3h | 20h |
| **建議提交**：v4 完成後 1-2 週內 |  |  |

---

## 9. Attorney Review Questions（給律師的問題清單）

### 9.1 § 101 相關

1. Claim 11（method）的 abstract idea 風險如何評估？是否該加 technical effect framing？
2. Claim 8/9/14 的 "role boundary" 是否需要徹底重寫，還是用 dependent claim 細化 implementation 即可？
3. Section 8.5 Computational Improvements 是否合適加入（避免 implicit performance guarantees）？

### 9.2 § 112 相關

4. DAG generation algorithm 描述到什麼粒度合適（避免揭露 trade secret，但滿足 enablement）？
5. Hash chain 結構是否值得寫入 v4（會否限制 alternative embodiment）？
6. 4 個 ambiguous term（"state-synchronized", "provider-controlled", "controlled asynchronous", "permission class"）的 definition 該寫多細？

### 9.3 § 102 / § 103 相關

7. AWS Greengrass / OpenAI Function Calling / Apache Airflow 等 prior art 的 distinguishment 是否充分？
8. 需要做哪些範圍的 prior art search？
9. Provisional 階段是否需要正式 prior art search report？

### 9.4 Claim 範圍策略

10. Tier C 4 條 claim（8, 9, 11, 14）是否該重寫，移除，還是用 continuation 處理？
11. 是否考慮拆分為多個 provisional（核心架構 / 局部 Edge 工作流 / Skill Lifecycle 各一）？
12. Hash chain 結構是否作為獨立 candidate claim（新增 Claim 16+）？

### 9.5 Entity Status & Filing Strategy

13. Tao 是否符合 Micro Entity（按 USPTO 現行規則）？需要哪些 documentation？
14. Assignment 流程：Tao → GEER IT INC 何時做？
15. 12 個月內轉 utility 的 timing 建議？

---

## 10. Appendix A — § 101 Alice/Mayo Framework Quick Reference

### Step 1：Is the claim directed to a judicial exception?

Judicial exceptions 包括：
- **Laws of nature**（e.g., E=mc²）
- **Natural phenomena**（e.g., 自然存在的化合物）
- **Abstract ideas**：
  - **Mathematical concepts**（formulas, calculations, relationships）
  - **Mental processes**（observation, evaluation, judgment, opinion）
  - **Certain methods of organizing human activity**（fundamental economic practices, commercial interactions, managing personal behavior, legal obligations）

### Step 2：Does the claim recite "significantly more"?

「Significantly more」可以是：
- **Improvement to the functioning of a computer** 或 **technology**（Alice v. CLS Bank, Enfish v. Microsoft）
- **Applies a judicial exception with a particular machine** 或 **adds a meaningful limitation**（DDR Holdings v. Hotels.com）
- **Effects a transformation** of an article to a different state（Bilski v. Kappos）

**對本 v3 草稿**：Step 2 主要建立在「**physical edge worker appliance**」 + 「**persistent tool invocation ledger with integrity metadata**」 + 「**local file abstraction adapter**」三個技術 hooks，律師應強化這三點。

---

## 附錄 B：本文版本紀錄

| Version | 日期 | 變更 | 簽發者 |
|:---|:---|:---|:---|
| v1 | 2026-05-21 PT | 初版深度 Examiner Review（針對 v3 PDF） | Claude + Tao 師兄 |

---

**END OF EXAMINER REVIEW**

**CONFIDENTIAL & PROPRIETARY**
**© 2026 GEER IT INC / GOAA.AI / AiKa Runtime OS. All Rights Reserved.**

🛡️ **本文非法律意見。所有 finding 須由 licensed U.S. patent attorney 確認。Tao 師兄與律師討論時可作為 attorney review 補強輸入。**
