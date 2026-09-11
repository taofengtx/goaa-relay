# IP_DEFENSE_PATENT_STRATEGY

> **本文角色**：GOAA.AI 知識產權與 provisional patent 策略儲備
> **本文類型**：Architecture / IP Strategy / Confidential Planning
> **是否允許直接執行**：否
> **是否允許替代法律意見**：否
> **是否允許標註 Patent Pending**：否，直到完成 USPTO filing
> **是否需要 Tao 拍板**：是
> **是否需要律師確認**：是
>
> **簽發**：2026-05-20 PT 工程總控中心
> **作者**：Claude (架構總控 + 文檔 PM) under Tao 師兄與總工指導
> **規範依據**：規範 #11 only-add / #14 v2 git-then-DO / #42 三端鐵律 / #44 違規先記憶

---

**CONFIDENTIAL & PROPRIETARY**
**© 2026 GEER IT INC / GOAA.AI / AiKa Runtime OS. All Rights Reserved.**
**This document contains confidential business, technical, and architectural information.**
**Do not distribute without written authorization.**

---

## 目錄

1. Strategy Summary
2. Entity Status Policy
3. Provisional Filing Cost Strategy
4. Three-Layer Document System
5. Patent Pending Marking Policy
6. Core Invention Candidate Areas
7. Confidential Header Templates
8. What Not To Publish
9. Integration With Provider-First Strategy
10. Action Checklist

---

## 1. Strategy Summary

GOAA.AI 應採用「**高質量 provisional 先行**」策略，目標是先鎖定 USPTO filing date，再進行招商、Demo、Provider MVP、AiKa Box PoC 與後續 utility patent 規劃。

### 推薦路線

```
AI 結構化整理 (Claude)
       ↓
Tao 補充商業與技術材料
       ↓
專利律師進行 claim 與 legal language 加固
       ↓
提交 USPTO provisional
       ↓
取得 filing date / application number
       ↓
再使用 Patent Pending 標識
```

### 策略理由

這是**成本、速度與保護力度之間最平衡**的路線：

- **成本**：律師費用集中在 claim 加固階段，前期 AI + Tao 整理大幅降低律師工時
- **速度**：provisional 申請流程快，filing date 鎖定後即可推進招商與 Demo
- **保護力度**：12 個月內可轉 non-provisional / utility，期間享有 priority date 保護

### 戰略對齊

此策略服務於 GOAA Phase 1 - Phase 5 商業節奏：

- **Phase 1 (Worker V5.0)**：提交 provisional 鎖定 dispatch / worker / tool_invocations 結構
- **Phase 2 (Provider 工作台)**：取得 application number 後加上 Patent Pending 增信招商
- **Phase 3 (Skill Marketplace)**：12 個月內評估是否轉 utility patent
- **Phase 5 (AiKa Box)**：硬體 PoC 完成後評估獨立 design patent

---

## 2. Entity Status Policy

### USPTO 三種 Entity 等級

| Entity 等級 | 官方費用基準 | 條件 |
|:---|:---:|:---|
| **Large Entity** | 100% | 預設等級 |
| **Small Entity** | 50% | 員工 < 500 人 |
| **Micro Entity** | 25% | Small + 額外四項條件 |

### Micro Entity 條件清單（USPTO 規定）

**若 Tao / GOAA 符合 USPTO Micro Entity 條件，可優先按 Micro Entity 路線準備 provisional，以降低官方費用。但不得在未核實前聲稱已符合 Micro Entity。**

正式提交前必須逐項核對以下條件：

- ☐ 是否符合 small entity 基礎條件（員工 < 500 人）
- ☐ 是否符合 micro entity 收入條件（前一年總收入低於官方規定的 gross income limit，當前金額以 USPTO 最新公告為準）
- ☐ 是否符合既往專利申請數條件（先前作為發明人的非 provisional 美國專利申請不超過官方上限，目前為 4 件）
- ☐ 是否存在轉讓、授權或義務轉讓給非 micro entity 的情況（若已 / 將授權給大公司，可能取消 micro entity 資格）
- ☐ 是否需要提交 USPTO micro entity certification form（提交時必填）

**警告**：

- ❌ 不得在未經律師核實前在任何文件、commit message、招商材料聲稱已符合 Micro Entity
- ❌ 不得用「我們是 Micro Entity」當定論
- ✅ 正確說法：「若符合 USPTO Micro Entity 條件，採用 Micro Entity 路線可降低費用；正式提交前需律師確認資格」
- ✅ 若不符合 Micro Entity，則按 Small Entity 或 Large Entity 正常處理

---

## 3. Provisional Filing Cost Strategy

### 三種申請路線比較

#### A. DIY provisional（不推薦作為唯一保護）

- 由發明人自行起草 specification + 簡化 claim
- 官方費用最低
- **風險**：
  - claim 寫得太窄或太廣，影響後續 utility patent 範圍
  - specification 缺乏 enablement（足以實施的揭露程度），可能被 USPTO 拒絕作為 priority date 依據
  - 不熟悉 35 U.S.C. § 101 software patent 案例法（Alice v. CLS Bank 等）容易誤踩雷區
- **適用**：純粹搶 priority date，後續一定會找律師重做的應急方案

#### B. AI + Tao 文檔整理 + 律師潤色（**推薦路線**）

- 利用現有 GOAA 文檔（AGENTS.md / docs/architecture/* / docs/business/* / 本文等）降低律師整理成本
- AI 負責結構化、技術抽象、流程圖、架構圖
- Tao 負責商業背景、發明動機、市場定位
- 律師補強：
  - claim 範圍與層次設計
  - enablement / written description requirements (35 U.S.C. § 112)
  - prior art risk 評估
  - 101 software patent 風險規避（Alice 框架）
  - 競品專利圖譜分析

- **成本特性**：律師工時集中在最有價值的 claim 與法律語言階段
- **適用**：GOAA 當前 Phase 1 - Phase 3 階段最佳路線

> **internal estimate, not a guarantee**：律師費用範圍因事務所、技術複雜度、claim 數量而異，正式報價需詢問 1-3 家事務所比較。

#### C. 傳統律師全包（後置選項）

- 律師從零起草所有材料
- 保護最完整
- 適合：
  - 融資後現金流穩定階段
  - 正式轉 non-provisional / utility patent 階段
  - 涉及多項 claim 或多國申請的複雜案件

### 推薦結論

**先走路線 B，必要時後續升級 utility patent**。

對應 GOAA 階段：
- **2026 Q2 - Q3**：路線 B 提交 provisional
- **2026 Q4 - 2027 Q1**：評估是否轉 utility patent（路線 C 或進階 B+）

---

## 4. Three-Layer Document System

建立三層文檔體系，根據受眾與場景控制揭露程度。

### A. Internal Core Version（內部核心版）

**用途**：內部研發、專利素材、核心架構決策

**包含**：
- Runtime OS 完整實現細節
- Worker V5.0 內部生產線實作
- dispatch / task / worker_events / sessions / messages 完整 schema
- Credits 計算公式與審計邏輯
- Skill / Achievement Marketplace lifecycle 完整流程
- AiKa Box local runtime 完整架構
- Provider workflow 詳細流程
- database schema planning 與 migration 紀錄

**標註 Header**：
```
STRICTLY CONFIDENTIAL
GOAA Runtime OS Internal Architecture
© 2026 GEER IT INC. All Rights Reserved.
Internal use only. Contains proprietary runtime, worker, dispatch, and system design information.
```

**存放位置**：private GitHub repo / 本機 / 律師專屬資料夾
**禁止公開到**：public repo / 招商材料 / 官網 / 公開 Demo

---

### B. Partner / Investor Version（合作 / 招商版）

**用途**：合作夥伴洽談、投資人路演、戰略合作

**內容**（高層抽象，不暴露完整實現）：
- 商業模式總覽
- 三端角色（Worker / Provider / Client）
- Provider-First strategy
- AiKa Box 定位與價值
- Skill Marketplace 高層架構
- Demo screenshots
- 市場機會與成長路徑
- 收益模型抽象（不含具體公式）

**不暴露**：
- 完整 executor 實現
- 完整 db schema
- 完整 routing 邏輯
- secrets / env / API key
- deploy script 細節
- 完整 patent claim

**標註 Header**（提交 provisional 前）：
```
CONFIDENTIAL & PROPRIETARY
© 2026 GEER IT INC / GOAA.AI. All Rights Reserved.
```

**標註 Header**（提交 provisional 後）：
```
CONFIDENTIAL & PROPRIETARY
Patent Pending
© 2026 GEER IT INC / GOAA.AI. All Rights Reserved.
```

**搭配 NDA**：分享給合作夥伴或投資人前建議簽署 NDA。

---

### C. Public Marketing Version（公開行銷版）

**用途**：官網、公開 Demo、公開 README、社交媒體、blog

**內容**：
- 願景與使命
- 用戶場景（Provider 文件處理 / follow-up / 表格草稿等）
- 產品價值主張
- Provider AI 工作台高層描述
- AiKa Box 作為 local AI runtime appliance 的高層表述

**禁止**：
- ❌ 暴露核心 claims / 實現細節
- ❌ 承諾收益（任何 Credits 收益 / Worker payout / ROI 承諾）
- ❌ 寫死未定硬體 spec（CPU 型號 / GPU 規格 / 容量等隨時可能調整）
- ❌ 公開 prompts / system instructions
- ❌ 公開 anti-bot / browser automation bypass 細節

**標註**：
```
© 2026 GEER IT INC / GOAA.AI. All Rights Reserved.
```

**提交 provisional 後可加**：
```
Patent Pending
```

---

## 5. Patent Pending Marking Policy

### 提交 USPTO Provisional 前

**❌ 嚴禁使用 Patent Pending**

虛假使用 Patent Pending 違反美國聯邦法 35 U.S.C. § 292，可能被罰款（每次最高 $500，可累積）。

提交前所有文檔只允許標註：
```
CONFIDENTIAL & PROPRIETARY
© 2026 GEER IT INC / GOAA.AI / AiKa Runtime OS. All Rights Reserved.
```

### 提交 USPTO Provisional 後

取得 **USPTO filing date / application number** 後，可在以下位置使用 Patent Pending：

- 白皮書封面
- 招商 PPT 首頁
- 官網 Footer
- GitHub README
- Demo 頁面 Footer
- Partner deck 封面

**不需要每頁都寫。**

### 推薦格式

**格式 1（簡短）**：
```
GOAA Runtime OS™
Patent Pending
Confidential & Proprietary
© 2026 GEER IT INC. All Rights Reserved.
```

**格式 2（明確指向）**：
```
Covered by pending U.S. provisional patent application.
```

### 注意事項

- ⚠️ **Patent Pending 不是已授權專利**
- ❌ 不得寫「Patented」（除非已取得 issued patent number）
- ❌ 不得寫「Patent #XXX,XXX」直到實際取得 issued patent
- ❌ 若 provisional 未在 12 個月內轉 non-provisional / utility，或已過期，**必須立即停止使用 Patent Pending**
- ✅ 提交多個 provisional / non-provisional 時，應在 utility patent application 中明確 claim priority 於 earlier provisional

---

## 6. Core Invention Candidate Areas

**重要說明**：本節列出的是「candidate invention areas」（候選發明領域），**不是已批准的 claim**。

正式 claim 撰寫由律師主導，本節僅供律師參考與技術佐證材料。

### 候選方向 1：Cloud Brain + Edge Execution Architecture

- 雲端 Task Router / AI Agent 負責任務理解、調度、審計
- 本地 AiKa Box / Worker 負責本地文件處理、browser automation、local runtime、OCR、desktop action
- 雲端與本地之間的任務分發 / 結果回收 / audit trail 雙向同步機制
- 任務優先級、難度、收益、成本的綜合調度演算法

### 候選方向 2：Three-Tier Product Boundary

- **Worker**：負責生產能力（內部生產線）
- **Provider**：負責接單、跟單、調用專業 Skill 並交付服務
- **Client**：負責提出需求、查看進度、與 Provider 互動並使用生活化 Skill
- 三端嚴格邊界（規範 #42 三端鐵律）：違規即不進代碼
- 三端 Skill 分層：Provider Skill 對 Provider 開放，Client Skill 對 Client 開放，Worker 不對外暴露

### 候選方向 3：Persistent Task Memory / Tool Invocation Ledger

- 持久化鏈路：`messages` → `dispatch` → `tasks` → `events` → `tools` → `tool_invocations`
- 目標：避免 AI Agent 失憶
- 支援：audit、replay、rollback
- 雙寫機制：tool 執行同時寫 audit trail（duration_ms / args / result / error）
- 透過 task_id 反查 session_id / message_id 的鏈式查詢

### 候選方向 4：Worker Credits / Runtime Cost Accounting

- 任務成本、內部 credits、runtime cost、skill usage、worker quality score 的審計模型
- Quality Score 與 Stability 加權計算
- Security Score = 0 觸發強制歸零
- **重要**：前期 Credits 只作內部結算與抵扣，**不做法幣提現**
- 提現機制涉及 KYC / AML / Money Transmitter License 等合規議題，需獨立評估

### 候選方向 5：Skill / Achievement Marketplace Lifecycle

- Worker 內部生產 Skill（不對 Provider/Client 直接開放）
- Provider 調用專業 Skill（透過 Provider 工作台）
- Client 使用生活化 Skill（透過 Client 介面）
- Skill 支援：版本管理、啟停、訂閱、反饋、升級、回滾
- Skill 收益分潤模型（後置，待律師意見書）

### 候選方向 6：AiKa Box Local Runtime Appliance

- 成熟硬體按需組裝 / 貼牌
- 預裝 GOAA Runtime OS / Worker Agent
- 用途：
  - 本地文件處理
  - browser automation
  - Docker
  - OCR
  - 本地模型推理
  - 專業服務工作流（會計 / 法律 / 醫療 / 教育）
- 硬體規格與定價屬於商業策略，**不在 patent claim 範圍內**

---

## 7. Confidential Header Templates

### 提交 USPTO Provisional 前文檔 Header

```
CONFIDENTIAL & PROPRIETARY
© 2026 GEER IT INC / GOAA.AI / AiKa Runtime OS. All Rights Reserved.
This document contains confidential business, technical, and architectural information.
Do not distribute without written authorization.
```

### 內部核心版 Header

```
STRICTLY CONFIDENTIAL
GOAA Runtime OS Internal Architecture
© 2026 GEER IT INC. All Rights Reserved.
Internal use only. Contains proprietary runtime, worker, dispatch, and system design information.
```

### 提交 Provisional 後可選 Footer

```
GOAA Runtime OS™ • Patent Pending • Confidential & Proprietary • © 2026 GEER IT INC. All Rights Reserved.
```

### 給律師 / NDA 簽署方文檔 Header

```
PRIVILEGED & CONFIDENTIAL — ATTORNEY-CLIENT COMMUNICATION
GOAA Runtime OS / AiKa Runtime OS
© 2026 GEER IT INC. All Rights Reserved.
Prepared for legal counsel review. Subject to attorney-client privilege.
```

---

## 8. What Not To Publish

以下內容**禁止公開**到 public repo / 官網 / Demo / 招商材料：

- ❌ 完整 `db.py` / `api.py` 核心邏輯
- ❌ Worker executor 白名單與安全策略細節
- ❌ `dispatch_task` 完整實現
- ❌ Credentials / env / API keys（規範 #22）
- ❌ Deploy scripts with host details（IP 地址、SSH key、cron entries）
- ❌ 完整 schema migration（特別是 tool_invocations / Credits 表）
- ❌ Proprietary prompts（system instructions / role definitions）
- ❌ Full claim logic（屬於 patent claim 範疇，律師專屬）
- ❌ Detailed Credits calculation formula
- ❌ Anti-bot / browser automation bypass details
- ❌ 規範 #40 命名以下的 `__v\d+__<hash>` 內部設計文檔（除非經 Tao 拍板可公開）
- ❌ AiKa Box BOM（Bill of Materials）細節
- ❌ Provider / Worker / Client 數量、營收等內部數據

**原則**：公開版可以講「**抽象價值**」，不講「**可複製實現**」。

---

## 9. Integration With Provider-First Strategy

IP 策略必須服務 **Provider-First 商業落地**。

### 前 6 個月（2026 Q2 - Q3）聚焦

- **Provider Pro $39.99/mo** (commercial main line)
- **Provider AI 工作台**（接單 / 跟單 / Skill 調用 / 交付）
- **文件處理**（Word / PDF / Excel）
- **Follow-up**（客戶溝通自動化）
- **表格草稿**（合約 / 報價 / 提案）
- **AiKa Box Runtime PoC**
- **Worker V5.0 內部生產線**

### 後置項目（律師意見書或商業條件成熟前不啟動）

- **Client Plus**（消費者端訂閱）
- **公開 Skill Marketplace**（涉及 platform liability）
- **Worker Developer Platform**（涉及第三方開發者協議）
- **Worker Credits payout**（涉及法幣提現合規）

### Provisional 策略支撐

- Provisional 鎖定 priority date → 招商時可說「核心技術已啟動 IP 保護」
- 取得 application number 後可在招商 PPT 首頁加 Patent Pending → 顯著增信
- 12 個月內可根據商業進展決定 utility patent 範圍

---

## 10. Action Checklist

### 提交 Provisional 前

- ☐ 收集核心文檔
  - `docs/AGENTS.md`（含三端鐵律 + 規範體系）
  - `docs/architecture/PHASE_4_1_RECONSTRUCTION__v1__975ddc09.md`
  - `docs/business/GOAA_BUSINESS_MODEL_V1.md`
  - `docs/marketing/GOAA_PORTAL_CONTENT_MATRIX_V2.md`
  - 本文 `docs/architecture/IP_DEFENSE_PATENT_STRATEGY.md`
  - 其他 `__v\d+__<hash>` 設計文檔
- ☐ 列出候選發明點（第 6 章 6 個方向）
- ☐ 製作 internal invention disclosure（律師通常會提供範本）
- ☐ 整理架構圖（Cloud Brain + Edge / Three-Tier / Task lifecycle）
- ☐ 整理流程圖（dispatch / task_complete / tool_invocations 雙寫）
- ☐ 整理 database schema abstract（不含完整 SQL，只用 ER 圖層級）
- ☐ 整理 task / worker / skill abstract 流程
- ☐ 標註所有材料為 `Confidential & Proprietary`
- ☐ 找專利律師 review（建議比較 2-3 家）
- ☐ 確認 entity status（第 2 章核對清單）
- ☐ 律師潤色 claim 與 specification
- ☐ 提交 USPTO provisional
- ☐ 保存 filing receipt（USPTO 會回傳）
- ☐ 取得 application number / filing date

### 提交 Provisional 後

- ☐ 在以下關鍵資料使用 `Patent Pending`（第 5 章 marking policy）：
  - 白皮書封面
  - 招商 PPT 首頁
  - 官網 Footer
  - GitHub README
  - Demo 頁面 Footer
  - Partner deck 封面
- ☐ 更新 investor deck（含 Patent Pending）
- ☐ 更新 website footer
- ☐ 更新 README
- ☐ **安排 utility patent deadline reminder**（provisional + 12 個月）
- ☐ 12 個月內決定是否轉 non-provisional / utility patent

### 持續維護

- ☐ 律師年度 review 一次
- ☐ 新增重大技術突破時評估是否補申請 continuation / continuation-in-part
- ☐ 維護「invention disclosure log」紀錄每個重要技術里程碑
- ☐ 競品專利監控（PatentScope / Google Patents 定期搜尋）

---

## 附錄 A：禁止事項彙整

本文件任務範圍內**禁止**：

- ❌ 修改 `api.py` / `db.py` / Worker Agent / `agent.py`
- ❌ 修改 DO production 任何檔案
- ❌ 執行 SQL（含 migration / DDL / DML）
- ❌ Publish Framer 官網
- ❌ 在提交 USPTO provisional 前使用 `Patent Pending` 標識
- ❌ 在 public docs 暴露核心實現
- ❌ 宣稱已取得專利
- ❌ 宣稱一定符合 Micro Entity
- ❌ 宣稱收益保證或硬體效果保證

---

## 附錄 B：免責聲明

**本文件不構成法律意見**。

所有 USPTO 規則、Patent Pending 使用規範、Micro Entity 條件、35 U.S.C. § 101 / § 112 / § 292 等法律議題，**正式提交前必須由有執業資格的美國專利律師確認**。

本文件僅作為 GOAA.AI 內部策略儲備與律師討論材料的起點。

---

## 附錄 C：本文件版本紀錄

| Version | 日期 | 變更 | 簽發者 |
|:---|:---|:---|:---|
| v1 | 2026-05-20 | 初版起草 | 工程總控中心 + Claude |

---

**END OF DOCUMENT**

**CONFIDENTIAL & PROPRIETARY**
**© 2026 GEER IT INC / GOAA.AI / AiKa Runtime OS. All Rights Reserved.**
