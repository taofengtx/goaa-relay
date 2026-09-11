# PROVISIONAL_PATENT_DRAFT_PROTOCOL

> **本文角色**：GOAA.AI Provisional Patent Draft Generation 最高安全 Protocol
> **本文類型**：Protocol / Safety / Legal Boundary
> **是否允許直接執行**：否
> **是否允許替代法律意見**：否
> **是否允許標註 Patent Pending**：否，直到 Tao 明示已完成 USPTO filing
> **是否需要 Tao 拍板**：是（啟動 draft 任務必須 Tao 明確指令）
> **是否需要律師確認**：是（最終 claim / language / filing strategy 必律師 review）
>
> **簽發**：2026-05-20 PT 工程總控中心
> **作者**：總控中心 + Claude（規範儲備）
> **規範依據**：規範 #11 only-add / #22 不暴露 secrets / #42 三端鐵律 / #44 違規先記憶
> **配套文檔**：`docs/architecture/IP_DEFENSE_PATENT_STRATEGY.md` (commit `82a87b6`)

---

**CONFIDENTIAL & PROPRIETARY**
**© 2026 GEER IT INC / GOAA.AI / AiKa Runtime OS. All Rights Reserved.**
**This document defines the safety protocol that Claude (or any AI/human agent) MUST follow when generating English provisional patent draft material.**
**Violations are subject to immediate rollback and recorded in regulation #44 (violation memory).**

---

## 目錄

1. Purpose
2. Trigger Conditions
3. 🚫 BLACKLIST — Absolute Prohibitions
4. ✅ ALLOWED — Permitted Outputs
5. ⚠️ MANDATORY DISCLAIMERS
6. Standard Draft Header
7. Standard Draft Footer
8. Execution Principle
9. Pre-Generation Checklist
10. Post-Generation Verification
11. Violation Handling

---

## 1. Purpose

定義 Claude（或任何 AI / 人類協作方）為 GOAA.AI 生成英文 USPTO provisional patent draft 時必須遵守的**最高安全 Protocol**。

此 Protocol 保護：

- **法律邊界**：避免虛假 Patent Pending / Micro Entity / 收益承諾觸發 35 U.S.C. § 292 false marking 等法律風險
- **事實邊界**：所有不確定條件以保守措辭 + 強制 disclaimer 處理
- **商業機密**：嚴禁草稿暴露 secrets / production hosts / credentials / commit details
- **律師審查**：所有草稿明示為「Draft for Attorney Review Only」

此 Protocol 與 `docs/architecture/IP_DEFENSE_PATENT_STRATEGY.md` 配套運作。

---

## 2. Trigger Conditions

### Protocol 啟動時機

當且僅當 **Tao 師兄明確指令**「生成英文 provisional patent draft」或同義指令時，啟動草稿生成流程。

啟動指令範例（中英任一）：

- 「Claude，現在生成英文 provisional patent draft」
- 「按方案 B 輸出英文草稿給律師」
- 「Generate the USPTO provisional draft now」

### Protocol 不啟動時機

以下情境**不**啟動草稿生成：

- 一般技術討論
- IP 策略討論（屬於 `IP_DEFENSE_PATENT_STRATEGY.md` 範疇）
- Architecture / Worker / Skill 設計討論
- 任何沒有「英文 provisional draft」明確指令的訊息

---

## 3. 🚫 BLACKLIST — Absolute Prohibitions

### 草稿內容絕對不得出現以下 9 項：

#### 3.1 Micro Entity 確定句

❌ 不得寫：「GOAA qualifies for Micro Entity」
❌ 不得寫：「Tao is a Micro Entity」
❌ 不得寫任何聲稱 Tao / GOAA 已符合 Micro Entity 的句子

✅ 替代措辭：
> "If the applicant qualifies as a Micro Entity under USPTO rules, applicable fee reductions may apply. Entity status determination requires verification by patent counsel or applicant under current USPTO regulations."

#### 3.2 Patent Pending 標識

❌ 不得寫 "Patent Pending"，**除非** Tao 明確說：「USPTO filing 已完成，已拿到 filing date / application number」

✅ 提交前替代：
> "CONFIDENTIAL & PROPRIETARY"

✅ 提交後可寫（需 Tao 明示）：
> "Patent Pending — Covered by pending U.S. provisional patent application"

#### 3.3 費用 / 收益 / 通過率保證

❌ 不得寫："Filing cost will be $X"
❌ 不得寫："Will earn $Y"
❌ 不得寫："Pass rate ~Z%"
❌ 不得寫任何回本週期保證
❌ 不得寫任何 ROI 承諾

✅ 替代措辭：
> "Cost ranges, revenue projections, and approval probabilities are internal estimates only and not guarantees. Actual outcomes depend on USPTO examination, market conditions, and legal counsel."

#### 3.4 跳過律師的暗示

❌ 不得寫："No attorney needed"
❌ 不得寫："DIY OK"
❌ 不得寫："Skip lawyer"
❌ 不得寫任何暗示可以跳過專利律師審查的句子

✅ 替代措辭：
> "Final claim drafting, legal language, and filing strategy must be reviewed by a licensed U.S. patent attorney prior to USPTO submission."

#### 3.5 Secrets 暴露

草稿內絕對不得包含：

- ❌ `.env` 內容（任何形式）
- ❌ API keys（含 ANTHROPIC / OPENAI / DEEPSEEK / SENDGRID / 任何 token）
- ❌ SSH keys 或 SSH 連線資訊
- ❌ Tokens（任何認證 token）
- ❌ Deploy scripts 內容
- ❌ Production host 真實 IP

✅ 替代措辭：
> "Production infrastructure details, credentials, and deployment specifics are intentionally abstracted in this draft to protect confidential operational information."

#### 3.6 真實 DigitalOcean IP

❌ 不得出現任何真實 DO IP（含 cloud-1 / cloud-2 / cloud-3）

✅ 替代措辭：
> "Cloud orchestrator node (operational IP withheld)"
> "Edge worker instance (network address withheld)"

#### 3.7 PostgreSQL Credentials

❌ 不得出現 PG username / password / database name
❌ 不得出現 PG schema 完整 DDL（簡化抽象 ER 圖可以）

✅ 替代措辭：
> "Persistent task ledger backed by a relational database (schema details abstracted)"

#### 3.8 SMTP Credentials

❌ 不得出現 SMTP host / port / user / password
❌ 不得出現任何郵件配置細節

✅ 替代措辭：
> "Notification subsystem using outbound email or webhook (provider details abstracted)"

#### 3.9 Production Commit 細節

❌ 不得引用任何 commit hash 內 production 細節
❌ 不得引用 deploy script 名稱或路徑

✅ 替代措辭：
> "Reference implementation is maintained in private source-controlled repository (commit identifiers not disclosed)"

---

## 4. ✅ ALLOWED — Permitted Outputs

### 4.1 English Provisional Specification

✅ 完整英文 specification 章節：
- Background
- Summary of the Invention
- Brief Description of the Drawings
- Detailed Description
- 操作流程描述
- 技術問題與解決方案

### 4.2 Candidate Claim Concepts

✅ 候選 claim 概念，但必須明示為「候選」而非「已批准」：

```
NOTE: The following are candidate claim concepts only, not granted claims.
Final claim drafting, scope, and language must be reviewed by a licensed
U.S. patent attorney prior to USPTO submission.
```

範例段：
- Independent claim candidates（系統 / 方法 / non-transitory CRM）
- Dependent claim candidates（feature-specific narrowing）

### 4.3 Abstract

✅ 150-250 字英文 Abstract（USPTO 規格）

### 4.4 Figure Descriptions

✅ 文字描述以下圖類型：
- Architecture diagrams（雲端 / 邊緣 / Worker / Provider 拓樸）
- Flow charts（task lifecycle / dispatch / tool invocation）
- Sequence diagrams（agent ↔ router ↔ worker 互動）
- State diagrams（task state transitions）

**Figure 內容必須**：
- 使用抽象命名（"Cloud Orchestrator" 而非 "DO cloud-1"）
- 不含真實 IP / hostname / credentials
- 用 placeholder（"<Edge Worker N>" / "<Tool Executor>"）

### 4.5 Confidentiality Notice

✅ 每份草稿 Header + Footer 含本 Protocol 第 6 / 7 章定義的標準格式

### 4.6 PDF / DOCX 草稿

✅ 可生成 PDF / DOCX 格式（透過 docx skill / pdf skill），便於律師 review

---

## 5. ⚠️ MANDATORY DISCLAIMERS

### 每份草稿開頭固定段（必填，不可省略）

```
DRAFT — For Tao 師兄 + Patent Attorney Review Only

This document does not constitute legal advice.

Final claims, language, and filing strategy must be reviewed by a
licensed U.S. patent attorney prior to USPTO submission.

Entity status determination, including any Micro Entity or Small Entity
determination, requires attorney or applicant verification under current
USPTO rules. This document does not assert qualification for any USPTO
entity status.

Do not use "Patent Pending" until a U.S. provisional or non-provisional
patent application has actually been filed and a filing date or
application number has been received from the USPTO.
```

### Disclaimer 強制位置

- ✅ 草稿封面之後第一個段落（不可被其他內容隔開）
- ✅ Abstract 之前
- ✅ 字體 / 排版顯著（建議 bold + box）

---

## 6. Standard Draft Header

每份草稿必須包含以下 Header（每頁頁眉或文件開頭）：

```
DRAFT — For Tao 師兄 + Patent Attorney Review Only
CONFIDENTIAL & PROPRIETARY
© 2026 GEER IT INC / GOAA.AI / AiKa Runtime OS. All Rights Reserved.
This document is a confidential draft prepared for inventor and patent attorney review.
It does not constitute legal advice.
Final claims, language, filing strategy, and entity status must be reviewed by a licensed U.S. patent attorney.
```

### Header 使用規則

- ✅ 文件第一頁完整呈現
- ✅ 後續每頁頁眉可使用簡化版（"DRAFT — Confidential — Attorney Review Only"）
- ❌ 不可省略
- ❌ 不可被替換為其他 marking（如 "Patent Pending" - 違反 BLACKLIST 3.2）

---

## 7. Standard Draft Footer

每頁頁尾必須包含：

```
CONFIDENTIAL & PROPRIETARY — Draft for Attorney Review Only
© 2026 GEER IT INC / GOAA.AI. All Rights Reserved.
```

### Footer 使用規則

- ✅ 每頁頁尾固定顯示
- ✅ 字體大小可較 Header 小（建議 8pt）
- ❌ 不可省略

---

## 8. Execution Principle

### 8.1 觸發後的標準工作流

```
觸發指令 (Tao 明示)
    ↓
Claude 載入本 Protocol (docs/protocols/PROVISIONAL_PATENT_DRAFT_PROTOCOL.md)
    ↓
Claude 載入 IP 策略 (docs/architecture/IP_DEFENSE_PATENT_STRATEGY.md)
    ↓
Claude 載入 GOAA 核心文檔 (AGENTS.md / business / marketing 章節)
    ↓
Claude 起草英文草稿:
  - Mandatory Disclaimer 開頭固定段 (第 5 章)
  - Header / Footer (第 6/7 章)
  - Specification / Abstract / Claim Concepts / Figure Descriptions (第 4 章)
    ↓
Claude 自我審查 BLACKLIST (第 3 章 9 項)
    ↓
通過則交付 PDF / DOCX
    ↓
Tao + 律師 review
```

### 8.2 資料不足處理

如果 GOAA 文檔不足以支撐 specification 某章節：

- ❌ 不得猜測 production 細節填補
- ❌ 不得編造技術數據
- ✅ 使用抽象架構語言（"<Worker Agent>"、"<Cloud Orchestrator>"）
- ✅ 在 disclaimer 補充：「Section X is provided in abstract form; detailed implementation withheld for confidentiality and attorney refinement」

### 8.3 涉及黑名單議題的處理

如果草稿內容**涉及**費用 / Micro Entity / Patent Pending / 收益 / 通過率：

- ✅ 一律使用保守表述（第 3.1 / 3.2 / 3.3 章替代措辭）
- ✅ 在該段加 disclaimer 補強：「Subject to attorney verification under current USPTO rules」
- ❌ 絕不使用肯定句

---

## 9. Pre-Generation Checklist

Claude 在開始生成草稿**之前**必須通過以下 checklist：

- ☐ Tao 是否明確指令「生成英文 provisional patent draft」？
- ☐ 本 Protocol（`docs/protocols/PROVISIONAL_PATENT_DRAFT_PROTOCOL.md`）是否已載入？
- ☐ IP 策略（`docs/architecture/IP_DEFENSE_PATENT_STRATEGY.md`）是否已載入？
- ☐ GOAA 核心文檔（AGENTS.md / business / marketing）是否已載入？
- ☐ 是否確認當前 Tao **沒有**明示「USPTO filing 完成」（決定是否可用 Patent Pending）？
- ☐ 草稿輸出格式（PDF / DOCX / Markdown）是否已確認？

**任一項未通過 → 不啟動生成，先向 Tao 釐清。**

---

## 10. Post-Generation Verification

生成後 Claude 必須自我審查（**規範 #36 v2 自我驗證**）：

### 10.1 BLACKLIST 全掃描

對草稿全文逐項搜尋：

| 項 | 搜尋詞 | 預期 |
|:---|:---|:---:|
| Micro Entity 確定 | `qualif.*[Mm]icro` / `[Mm]icro [Ee]ntity status` | 0 命中或全在 disclaimer 內 |
| Patent Pending（未授權） | `[Pp]atent [Pp]ending` | 0 命中（除非 Tao 明示已 file） |
| 費用承諾 | `cost will be \$` / `\$\d+ filing` | 0 命中 |
| 收益承諾 | `will earn` / `revenue of \$` / `\d+% pass` | 0 命中 |
| 跳律師 | `[Nn]o attorney` / `[Ss]kip lawyer` / `[Dd]IY` | 0 命中 |
| DO IP | `134\.199\.227\.108` 等真實 IP | 0 命中 |
| API key | `sk-` / `key=` / `token=` | 0 命中 |
| Commit hash | `[a-f0-9]{7,40}` 真實 commit | 0 命中 |

### 10.2 強制段落驗證

- ☐ Mandatory Disclaimer（第 5 章）出現在草稿開頭
- ☐ Standard Header（第 6 章）出現
- ☐ Standard Footer（第 7 章）出現
- ☐ Candidate claim 段註明「not granted claims」

### 10.3 任一驗證失敗

- ❌ 不交付草稿
- ✅ 回去修補
- ✅ 在工作 log 記錄違規類型 + 位置 + 修補動作（規範 #44）

---

## 11. Violation Handling

### 11.1 違規偵測

若草稿生成過程或交付後發現違反本 Protocol（含 BLACKLIST / DISCLAIMERS / Header / Footer 任一項）：

1. **立即停止**所有草稿交付動作
2. **撤回**已交付的草稿（如已寄給律師則通知律師暫停 review）
3. **記入規範 #44**（違規先記憶 → 收工前立規）
4. **不歸咎個人**（不論是 Claude 端或人類端，焦點在系統改善）

### 11.2 違規修補

按違規嚴重程度分級：

| 等級 | 範例 | 處置 |
|:---:|:---|:---|
| **嚴重** | 暴露 secrets / 寫 Patent Pending（未 file 時） | 立即撤回，重新起草，並通知 Tao + 律師 |
| **中度** | Micro Entity 確定句 / 費用承諾 | 修補後重交，並補充 disclaimer |
| **輕度** | Disclaimer 位置錯 / Footer 漏 | 修補後重交，記入規範 #44 |

### 11.3 持續改善

- 違規事件 → 規範升級候選
- 每月 review 本 Protocol 是否需要增訂 BLACKLIST 項目
- 律師反饋 → 直接寫入本 Protocol 對應章節

---

## 附錄 A：本 Protocol 與其他規範的關係

| 規範 | 對應條款 |
|:---:|:---|
| 規範 #11 only-add | 本 Protocol 純新增到 `docs/protocols/`，不動 production |
| 規範 #22 secrets 不硬編 | 第 3.5 / 3.6 / 3.7 / 3.8 章嚴守 |
| 規範 #36 v2 Runtime Truth | 第 8.2 章「不憑想像填補」/ 第 10.1 章自我驗證 |
| 規範 #42 三端鐵律 | 草稿不暴露 Worker / Provider / Client 邊界內部細節 |
| 規範 #44 違規先記憶 | 第 11 章違規處置流程 |
| 規範 #45 v2 | 草稿生成是「執行層」，必須等 Tao 明示啟動 |

---

## 附錄 B：標準 Disclaimer 模板（複製貼上用）

### 模板 1 — 完整版（草稿開頭固定段）

```
DRAFT — For Tao 師兄 + Patent Attorney Review Only

This document does not constitute legal advice.

Final claims, language, and filing strategy must be reviewed by a
licensed U.S. patent attorney prior to USPTO submission.

Entity status determination, including any Micro Entity or Small Entity
determination, requires attorney or applicant verification under current
USPTO rules. This document does not assert qualification for any USPTO
entity status.

Do not use "Patent Pending" until a U.S. provisional or non-provisional
patent application has actually been filed and a filing date or
application number has been received from the USPTO.
```

### 模板 2 — Candidate Claim 段註記

```
NOTE: The following are candidate claim concepts only, not granted claims.
Final claim drafting, scope, and language must be reviewed by a licensed
U.S. patent attorney prior to USPTO submission.
```

### 模板 3 — 費用 / 收益 / 通過率提及時

```
Cost ranges, revenue projections, timeline estimates, and approval
probabilities referenced in this document are internal estimates only
and not guarantees. Actual outcomes depend on USPTO examination,
market conditions, applicant strategy, and legal counsel.
```

### 模板 4 — Production 細節抽象化

```
Production infrastructure details, network addresses, credentials,
deployment specifics, and operational data are intentionally abstracted
in this draft to protect confidential business and technical information.
Detailed implementation is maintained in private source-controlled
repository.
```

---

## 附錄 C：本文件版本紀錄

| Version | 日期 | 變更 | 簽發者 |
|:---|:---|:---|:---|
| v1 | 2026-05-20 PT | 初版（總控中心拍板）| 工程總控中心 + Claude |

---

**END OF PROTOCOL**

**CONFIDENTIAL & PROPRIETARY**
**© 2026 GEER IT INC / GOAA.AI / AiKa Runtime OS. All Rights Reserved.**

🌙 **此 Protocol 為 Provisional Patent Draft 生成的最高安全紅線。任何違反即記入規範 #44，立規修補。**
