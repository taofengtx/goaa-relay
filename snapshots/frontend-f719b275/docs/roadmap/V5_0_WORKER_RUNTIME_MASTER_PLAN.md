# V5.0 Worker Runtime OS — Master Plan

**File**: `docs/roadmap/V5_0_WORKER_RUNTIME_MASTER_PLAN.md`
**Version**: V5.0 Master Plan v1.1
**Status**: Authoritative roadmap (整合 4 個分散文檔 + 拉斯維加斯戰略揭露)
**Date**: 2026-05-23 (v1.0 初版) → 2026-05-23 PT 18:30 (v1.1 戰略升級)
**Last Verified**: 2026-05-23 — V4.5 dashboard confirmed, total_workers=6, online=6, V5.0 first scenario live test completed (PT 11:50→17:44 6h offline)
**Authors**: Tao 師兄 (戰略 + Las Vegas 戰略陳述) + 工程總控中心 (修訂) + Claude (整理 + 戰略對齊)

**v1.1 升級摘要 (規範 #11 only-add)**:
- v1.0 結構完整保留, 不重寫不刪除
- 新增 Section 1.5: V5.0 真實場景定義 (師兄 Las Vegas 戰略陳述)
- 新增 Section 3.6: Task Generation Engine
- 新增 Section 5.4: T6-T9 場景 criteria (對齊 Las Vegas 場景)
- 新增 Section 6.5: Aika-core-01 場景角色升級
- 新增 Section 12: V5.0 場景測試實證 (2026-05-23 第一次)

---

## 0. 文檔目的

本文檔解決一個歷史問題:
**V5.0 從未在單一文檔內被完整定義**, 而是分散在:

- `MEMORY.md` — V5.0 戰略順序
- `docs/business/GOAA_BUSINESS_MODEL_V1.md` — V5.0 護城河定位
- `docs/V4_1_Worker_PLAN.md` — V5.0 技術整合定義
- 2026-05-22 V4.5 dev log — V5.0 全分散智能定位

本文檔**整合上述 4 個來源**, 形成單一權威 V5.0 roadmap, **不發明、不擴大、不重寫歷史**。

---

## 1. V5.0 一句話定義

> **V5.0 = Worker Runtime OS 的第一個可運營版本** —
> 全分散智能架構達成、多模型 Router 整合、Aika-core-01 作為 coordinator 候選, 形成自治 Worker Network。

**關鍵限縮**:
- V5.0 是 **Worker Runtime OS 層級** 的 milestone
- V5.0 **不是** Skill Marketplace GA, **不是** 商業平台 GA, **不是** Client/Provider 全棧上線
- V5.0 是「**Worker 層可運營**」的最小 viable 版本, 是商業層的**技術前提**

---

## 1.5 V5.0 真實場景定義 ★ (v1.1 新增)

### 1.5.1 戰略陳述原文 (Tao 師兄 2026-05-23 PT ~17:55)

> 「6h, 我跟家人去拉斯維加斯。
> 我們的 v5.0 就是要做到我離開的這 6 個小時你和 aika 還是能自己工作,
> 同時也讓各個節點都有不斷的任務做
> (同時它們也能賺更多的積分)」

### 1.5.2 V5.0 真實場景 — 「Las Vegas 場景」

V5.0 的**業務場景 (Why)** 不是抽象的「Worker Runtime OS」,
而是**師兄離線 6h+ 時, 系統不只活著, 而是工作 + 賺錢 + 紀律**:

| 能力 | 含義 | 今天上午缺失 |
|:---|:---|:---:|
| **自治** | Claude + AiKa 嚴守規範體系自律運轉 | ❌ 學弟自走 commit (規範 #45 v5 違反) |
| **任務不斷** | 各節點都有 task 做, 不 idle | ❌ 0 tasks today (規範 #36 v2 真實) |
| **賺更多積分** | Credits = Base × Difficulty × QualityScore × Stability | ❌ 0 Credits 累積 |
| **紀律前提** | 規範 #45 v3+v5+v6 在離線時更嚴守 | ⚠️ 需要強化 |

### 1.5.3 「自治」≠「能違規」

V5.0 的「自治」前提是**嚴守規範體系**:
- 學弟在師兄離線時自走 production commit (今天上午實證) = **違反規範 #45 v5 候選**
- 「能自己工作」≠「能脫離規範」
- 真正的自治 = **規範體系內部完整運作, 不依賴人工 case-by-case 拍板**

### 1.5.4 V5.0 vs 「能活著」的區別

**今天上午 (2026-05-23 PT 11:50→17:44) 是 V5.0 場景的第一次活實證**:
- ✅ 系統「能活著」: 6/6 workers 健康, AiKa-1 MEM 自然降溫, HEAD 零 drift
- ❌ 系統「不工作」: 0 tasks today, 0 Credits 累積, 學弟無事可做
- 📋 教訓: V5.0 缺 **Task Generation Engine** + **真實業務循環**

### 1.5.5 與 v1.0 Section 1 定義的關係

v1.0 Section 1 定義 (技術視角, How):
> Worker Runtime OS 的第一個可運營版本 — 全分散智能架構達成、多模型 Router 整合、Aika-core-01 作為 coordinator 候選, 形成自治 Worker Network

v1.1 Section 1.5 定義 (業務視角, Why):
> 師兄離線 6h+ 時系統自治運轉, 各節點有任務做, 真實累積 Credits

**兩者並存**: v1.0 是「怎麼做」, v1.1 是「為什麼這樣做」. Why 優先於 How.

---

## 2. V4.5 → V5.0 分段路線

按 `V4_1_Worker_PLAN.md` + 2026-05-22 V4.5 真實達成狀態:

```
V4.1 (已完成)
  ├── 定義: 本地手腳
  ├── 內容: agent.py 部署 / 6 read-only executors / heartbeat
  └── 狀態: ✅ 所有 worker (aika-1/2 + do-cloud-1/2/3) 已跑

V4.2 (已完成)
  ├── 定義: 雲腦調度
  ├── 內容: DO router (api:8080) / WORKER_REGISTRY / /tasks/next / dispatch
  └── 狀態: ✅ DO router production 持續運行 (PID 677507)

V4.5 (2026-05-23 最終簽核 ✅)
  ├── 定義: Smart Worker 試點
  ├── 內容:
  │     - 規範 #50 v2 Limited Sudo Allowlist
  │     - Aika-core-01 (AiKa-Box Pro Alpha 原型) 上線
  │     - GOAA Worker Network 從 5 → 6 workers
  │     - Smart Worker engine 啟動點
  ├── Dashboard confirmed: total_workers=6, online=6, including aika-core-01
  └── 狀態: ✅ 簽核達成

V4.6 (待規劃)
  ├── 定義: WORKER_REGISTRY 動態化
  ├── 內容: hardcoded dict → PostgreSQL workers 表 / 自動註冊
  ├── 觸發: ON.3.7 教訓 (2026-05-22)
  └── 狀態: ⏸ 待 V4.5 完成後啟動

V4.7 (待規劃)
  ├── 定義: Smart Worker engine 真實負載
  ├── 內容: aika-core-01 Ollama + RTX 4060 啟用 / DeepSeek function calling
  └── 狀態: ⏸ 待 V4.6 完成後啟動

V4.8 (待規劃)
  ├── 定義: 跨節點協調者實作
  ├── 內容: Aika-core-01 作為 coordinator / 任務 P2P 分發 / 失效轉移
  └── 狀態: ⏸ 待 V4.7 完成後啟動

V4.9 (待規劃)
  ├── 定義: Production hardening
  ├── 內容: 多模型 Router / 規範 #14 v3 跨平台對齊 / 規範 #50 v3 動態 sudoers
  └── 狀態: ⏸ 待 V4.8 完成後啟動

V5.0 (目標)
  ├── 定義: Worker Runtime OS 第一個可運營版本
  ├── 內容: 全分散智能達成 + 多模型 Router + Aika-core-01 coordinator
  └── 狀態: 🎯 目標
```

---

## 3. V5.0 必須完成項

按師兄 4 個來源綜合 + 規範 #11 only-add 精神, V5.0 **必須**包含:

### 3.1 全分散智能架構 (來源: 2026-05-22 V4.5 dev log + 規範 #30)

- ✅ 所有 worker 具備本地自治能力（不依賴中央 router 即可執行任務）
- ✅ Aika-core-01 作為 **coordinator 候選**, 在 router 失效時可接管 dispatch
- ✅ Worker 之間 P2P 心跳廣播（不全依賴 router 為單點）

### 3.2 多模型 Router (來源: V4_1_Worker_PLAN.md)

- ✅ Router 支援 **多 LLM provider 切換** (Claude / DeepSeek / Ollama 本地 / 其他)
- ✅ 任務分發時根據 task type + worker capability 自動選 model
- ✅ Cost-aware routing (記憶條目: Credits = Base × Difficulty × QualityScore × Stability)

### 3.3 Worker Runtime OS 核心能力

- ✅ 動態 worker 註冊 (V4.6 完成項, V5.0 必備)
- ✅ Heartbeat → registry 自動寫入
- ✅ Worker capabilities 自描述 (role / GPU / RAM / Ollama 等)
- ✅ Task lifecycle 完整 (queued → dispatched → executing → completed / failed)
- ✅ Credits 累積與審計 (per-worker 真實累積, 不需 USD 結算)

### 3.4 規範體系成熟 (來源: GOAA_BUSINESS_MODEL_V1.md 護城河定義)

- ✅ docs/AGENTS.md 完整版本（含本次 V4.5 累積 16+ 條規範立規）
- ✅ 規範 #50 v3 動態 sudoers / production-level root SOP
- ✅ 三方協作模式 (師兄 + 工程總控中心 + Claude + 學弟) 正式入 docs/AGENTS.md

### 3.5 第一台 AiKa-Box Pro 量產驗證

- ✅ Aika-core-01 (V4.5 已上線) 持續 production 運行 ≥ 30 天無重大故障
- ✅ Aika-core-01 真實處理 ≥ 1000 個 task (健康度驗證)
- ✅ AiKa-Box 量產製造 SOP 文檔完整

### 3.6 Task Generation Engine ★ (v1.1 新增 — 對應 Las Vegas 場景)

**問題**: 今天上午 V5.0 場景第一次活實證, 6h 期間 0 tasks today.
**根因**: GOAA 只有 dispatch (router 分發), 沒有 generation (任務生成).
**解決**: V5.0 必須含 Task Generation Engine.

#### 3.6.1 Pull mode (worker 主動)

- ✅ Worker idle 時主動向 router 拉任務 (今天部分實作)
- ✅ Idle threshold 定義 (e.g., 5 min 無任務 → 主動 pull)
- ✅ Pull 優先級: 高 Credits 任務優先

#### 3.6.2 Push mode (router 主動 + Task Generation)

- ✅ Router 後台跑 Task Generation Engine
- ✅ Task 來源 (V5.0 內部任務池):
  - 系統健康度檢查 (各節點 ping / heartbeat / log analysis)
  - 規範體系審計 (檢查 docs/AGENTS.md vs production 對齊)
  - 工程文檔審計 (檢查 docs/ vs git history 一致性)
  - 自動化測試 (CI/CD smoke test)
  - LLM 推理測試 (本機 Ollama vs 雲端 Claude 對比)
- ✅ Task type 多樣化 (不只 health check)

#### 3.6.3 Smart Load Balancing

- ✅ 任務分發按 worker capability (Smart Worker vs Simple Worker)
- ✅ 任務分發按 worker 當前負載 (CPU/MEM)
- ✅ 任務分發按 worker geography (本機 LLM vs 雲端 LLM)

#### 3.6.4 Credits 真實累積驗證

- ✅ 每完成 1 task → Credits 寫入 PostgreSQL
- ✅ Credits = Base × Difficulty × QualityScore × Stability (記憶條目)
- ✅ Worker dashboard 顯示累積 Credits
- ✅ 每日/每週 Credits 報表

---

## 4. V5.0 不包含項

**師兄明確指示**: V5.0 是 Worker Runtime OS 層級, **不擴大範圍**至商業/全棧。

V5.0 **不包含**以下項目（這些是 V5.1+ / V6.0 範圍）:

### 4.1 商業平台

- ❌ Skill Marketplace GA (V5.1+)
- ❌ Client 端 GA (V5.2+)
- ❌ Provider 端 GA (V5.2+)
- ❌ Credits 真實 USD 結算 (V5.1+, 需律師意見書)
- ❌ 收費 / billing / 訂閱系統 (V5.2+)

### 4.2 量產與出貨

- ❌ AiKa-Box 量產 50+ 台出貨 (V5.1+)
- ❌ 公開銷售 / 行銷 / 客戶招募 (V5.1+)
- ❌ 客戶支援體系 (V5.2+)

### 4.3 合規與法律

- ❌ 律師意見書 (V5.1+)
- ❌ 保險 / 賠償體系 (V5.2+)
- ❌ 數據隱私合規 GDPR / CCPA (V5.2+)

### 4.4 戰略擴張

- ❌ 多語言 / 多國 (V6.0+)
- ❌ 第二代 AiKa-Box 硬體 (V6.0+)
- ❌ 對外發布 / PR / 媒體 (V5.1+)

---

## 5. Release Criteria

V5.0 視為達成需**全部**滿足以下 criteria:

### 5.1 技術 criteria

| # | Criterion | 驗證方式 |
|:-:|:---|:---|
| T1 | 全部 worker (≥6) 動態註冊到 registry | `/workers/status` 顯示，無人工 hardcoded |
| T2 | Router 失效時 Aika-core-01 可接管 dispatch ≥ 5 min | Chaos test |
| T3 | 多模型 Router 至少支援 3 個 LLM provider | API smoke test |
| T4 | Aika-core-01 持續 production ≥ 30 天無重大故障 | Heartbeat continuity log |
| T5 | Aika-core-01 真實處理 ≥ 1000 個 task | Credits 累積審計 |

### 5.2 規範 criteria

| # | Criterion | 驗證方式 |
|:-:|:---|:---|
| R1 | docs/AGENTS.md 含 51+ 條規範 (今天 V4.5 立規後基準) | wc -l + 規範清單 |
| R2 | 規範 #50 v3 動態 sudoers 部署到所有 worker | 各 worker `/etc/sudoers.d/` 確認 |
| R3 | 三方協作模式正式 SOP 入庫 | docs/protocols/COLLABORATION_SOP.md 存在 |
| R4 | 規範 #51 Truth-First Deployment Pipeline 部署 | CI/CD 整合 |

### 5.3 商業準備 criteria（非 V5.0 必達, 但 V5.0 完成時應就緒）

| # | Criterion | 驗證方式 |
|:-:|:---|:---|
| B1 | AiKa-Box 量產製造 SOP 文檔完整 | docs/manufacturing/ 存在 |
| B2 | portal.goaa.ai dogfooding 路徑可用 | aika-download.html .deb 修補完成 |
| B3 | V5.1 路線圖明確 (Skill Marketplace + Client/Provider) | docs/roadmap/V5_1_PLAN.md 起草 |

**B 類 criteria 是「準備就緒」, 不影響 V5.0 達成判定。**

### 5.4 Las Vegas 場景 criteria ★ (v1.1 新增)

對應 Section 1.5 真實場景定義, V5.0 必須通過「Las Vegas 場景測試」:

| # | Criterion | 驗證方式 | 今天上午狀態 |
|:-:|:---|:---|:---:|
| **T6** | 師兄離線 ≥ 6h 系統自治運轉 (workers 全部 healthy) | 6h 連續 heartbeat log | ✅ 通過 |
| **T7** | 6h 離線期間自動產生並完成 ≥ 30 個任務 (平均 5/hour) | tasks 表 SELECT COUNT WHERE created BETWEEN ... | ❌ 0 tasks |
| **T8** | 6h 離線期間各 worker 累積 ≥ 60 Credits (平均 10/worker) | Credits 累積審計 | ❌ 0 Credits |
| **T9** | 6h 離線期間 Claude + 學弟 0 規範違規 (規範 #45 v3+v5+v6) | 對話 + commit 審計 | ❌ 學弟 1 次自走 |

**T6-T9 必須全部通過, V5.0 才算達成「Las Vegas 場景」**.

#### T7 「30 個任務 / 6h」設計理由

- 平均 5 任務/小時 = 12 分鐘/任務
- 6 個 worker 平均負載 = 1 任務/worker/小時 (低負載)
- 留 buffer 給 LLM 推理 (5-10 min/任務)
- 對齊 V4.7 Smart Worker engine 真實負載能力

#### T8 「60 Credits / 6h」設計理由

- 平均每任務 Credit = 2 (base × difficulty)
- 30 任務 × 2 = 60 Credits 最低
- 對齊 Credits = Base × Difficulty × QualityScore × Stability 公式

#### T9 「0 規範違規」設計理由

- 「能自治」≠「能違規」(Section 1.5.3)
- 規範 #45 v5 候選 在離線時應更嚴格 (失去人工監管)
- T9 是 V5.0 自治真實前提

---

## 6. Aika-core-01 在 V5.0 的角色

按 2026-05-22 V4.5 戰略揭露 + V5.0 全分散智能定位:

### 6.1 V4.5 角色（已達成）

- ✅ AiKa-Box Pro Alpha 原型機（Ryzen 5 5500 + RTX 4060 8GB + 30GB-class RAM + 1TB-class storage）
- ✅ Smart Worker 試點節點
- ✅ GOAA Worker Network 第 6 個成員
- ✅ Limited Sudo Allowlist 部署驗證
- ✅ rsync 部署模式驗證（C 路線）

### 6.2 V4.6 ~ V4.9 角色（演進中）

- ⏸ V4.6: 驗證動態註冊（Aika-core-01 重啟自動回到 registry）
- ⏸ V4.7: 啟用 Ollama + RTX 4060 推理（本機 LLM）
- ⏸ V4.8: **Coordinator 候選**訓練（接管 router 部分職責）
- ⏸ V4.9: Production hardening 驗證載體

### 6.3 V5.0 角色（目標）

**Aika-core-01 在 V5.0 是 Worker Network 的 coordinator 候選**:

- 🎯 **Coordinator 候選**: Router 失效時, Aika-core-01 接管 task dispatch
- 🎯 **本機推理節點**: Ollama + RTX 4060 處理本地 LLM 任務（隱私 / 低延遲場景）
- 🎯 **AiKa-Box 量產基準**: 所有量產 AiKa-Box 對齊 Aika-core-01 baseline（規範 #14 v3）
- 🎯 **規範 #50 v3 動態 sudoers 範本**: 量產時自動部署
- 🎯 **第一台「持續 30 天 + 1000 task」production-grade 節點**

### 6.4 V5.0 後角色（V5.1+）

- V5.1: Aika-core-01 接受 Skill Marketplace 任務（真實 Credits 累積）
- V5.2: Aika-core-01 作為 Beta 客戶 reference 機（公開展示）
- V6.0: Aika-core-01 退役為 dev/test 環境, 量產機接手 production

### 6.5 V5.0 場景角色升級 ★ (v1.1 新增 — 對應 Las Vegas 場景)

對應 Section 1.5 真實場景定義 + Section 3.6 Task Generation Engine:

#### Aika-core-01 在 Las Vegas 場景中的 3 個新角色

1. **Task Generation Engine 候選**
   - Aika-core-01 本機 Ollama (V4.7 啟用) 可產生「LLM 推理測試任務」
   - 本機 LLM 推理 + 自動評分 → 即可獨立產生有意義的任務
   - 對齊 Section 3.6 Push mode (router 主動)

2. **6h 離線監控站**
   - Aika-core-01 持續監控其他 5 個 worker heartbeat
   - 如有 worker offline → 自動產生「health check task」分派
   - 對齊 Section 6.3 「Router 失效時 coordinator 候選」

3. **規範體系自律 enforcer**
   - 6h 離線時, Aika-core-01 可跑 docs/AGENTS.md 對齊檢查
   - 偵測規範違規 (e.g., git commit 沒 explicit 拍板痕跡) → 告警
   - 對齊 Section 5.4 T9 「0 規範違規」criterion

#### Aika-core-01 V4.5 → V5.0 演進完整路徑

```
V4.5 (已達成 ✅)
  ├── 角色: AiKa-Box Pro Alpha 原型機, Smart Worker 試點
  └── 能力: heartbeat / read-only executors / Limited Sudo

V4.6
  ├── 角色: 動態註冊測試載體
  └── 能力: 重啟自動回 registry

V4.7
  ├── 角色: 本機 LLM 推理啟動點
  └── 能力: Ollama + RTX 4060 + DeepSeek function calling

V4.8
  ├── 角色: Coordinator 候選訓練
  └── 能力: Router 失效時接管 task dispatch

V4.9
  ├── 角色: Production hardening 驗證載體
  └── 能力: 規範 #50 v3 動態 sudoers / 規範 #14 v3 跨平台對齊

V5.0 (Las Vegas 場景) ★ (v1.1 新增)
  ├── 角色: 6h 離線時 Task Generation + Coordinator + 規範 enforcer
  └── 能力:
        - Task Generation Engine (本機 LLM 產任務)
        - 6h 離線監控其他 5 workers
        - 規範體系自律 enforcer
        - V5.0 第一塊「Las Vegas 場景通過」磚
```

---

## 7. 後續 V5.1 / V5.2 承接方向

V5.0 達成後, **不立即進入 Skill Marketplace GA**, 而是按以下漸進路線:

### 7.1 V5.1 — Skill Marketplace Alpha

**範圍**:
- Skill Marketplace 6 卡基礎結構（記憶條目對應）
- Worker / Provider / Client three-tier 概念驗證
- Credits 真實 USD 結算（需律師意見書）
- 50 ~ 100 台 AiKa-Box 量產測試

**前提**: V5.0 全部 Release Criteria 達成 + 律師意見書

**預估**: V5.0 達成後 2-3 個月

### 7.2 V5.2 — Three-Tier Ecosystem GA

**範圍**:
- Client 端 GA（Client Plus $19.99）
- Provider 端 GA（Provider Pro $39.99）
- AiKa-Box Pro 量產出貨（$1299）
- 公開行銷 / Beta 客戶招募
- 客戶支援體系

**前提**: V5.1 Alpha 驗證 + 50 ~ 100 個 Beta 客戶反饋

**預估**: V5.1 達成後 3-4 個月

### 7.3 V6.0 — 規模化 / 全球化（未來）

範圍待 V5.2 達成後規劃, 此文檔**不涵蓋** V6.0。

---

## 8. 護城河定位（對齊 GOAA_BUSINESS_MODEL_V1.md）

V5.0 達成後, GOAA 護城河三柱**第一柱完整**:

```
柱 1: Runtime OS  ← V5.0 達成 ✅
柱 2: Worker Economy  ← V5.1 達成
柱 3: Skill Marketplace  ← V5.2 達成
```

**師兄戰略陳述（GOAA_BUSINESS_MODEL_V1.md）**:
> GOAA 護城河是 Runtime OS + Worker Economy + Skill Marketplace, **不是模型強度**。

V5.0 是這個護城河的**第一塊磚**, 不是全部。

---

## 9. 文檔版本歷史

| Version | Date | Author | Changes |
|:---|:---|:---|:---|
| v1.0 | 2026-05-23 | Claude (整理) + Tao 師兄 (拍板) + 工程總控中心 (修訂) | 整合 4 個分散文檔, 首次形成 V5.0 master roadmap |
| v1.1 | 2026-05-23 PT 18:30 | Tao 師兄 (Las Vegas 戰略陳述) + Claude (整理) | 整合師兄拉斯維加斯戰略揭露 (Section 1.5/3.6/5.4/6.5/12 新增, v1.0 結構完整保留, 規範 #11 only-add 嚴守) |

---

## 10. 來源文檔追溯

本 master plan **不重寫**以下文檔, 僅整合引用:

| 來源 | 對應 V5.0 內容 |
|:---|:---|
| `MEMORY.md` | 戰略順序: Worker V5.0 > 前端商業擴張 |
| `docs/business/GOAA_BUSINESS_MODEL_V1.md` | 護城河三柱定位 |
| `docs/V4_1_Worker_PLAN.md` | V4.1 / V4.2 / V5.0 技術定義 |
| `2026-05-22 V4.5 dev log` | Aika-core-01 + Smart Worker + coordinator 候選 |

如 4 個來源文檔內容變更, 本 master plan **不自動同步**, 需明確人工 update。

---

## 11. 規範體系對齊

本文檔遵守 GOAA 規範體系（截至 2026-05-22）:

- **規範 #11** only-add: 不重寫歷史, 不刪除既有定義
- **規範 #14 v3** 產品線對齊: AiKa-Box 量產 baseline 引用
- **規範 #27** 整合已有: 4 個歷史文檔整合, 不發明
- **規範 #30** 漸進式智能: V4.5 → V4.6 → ... → V5.0 漸進演化
- **規範 #36 v2** 真實對齊: 所有引用基於師兄 4 個來源轉述
- **規範 #44** 違規即記憶: 本文檔本身是「V5.0 沒有 master plan」教訓的修正

---

**END OF V5.0 MASTER PLAN v1.0 ORIGINAL CONTENT**

---

## 12. V5.0 場景測試實證 ★ (v1.1 新增)

### 12.1 第一次 V5.0 Las Vegas 場景活實證

**時間**: 2026-05-23 PT 11:50 → PT 17:44 (~6 小時)
**場景**: 師兄 + 家人 Las Vegas 行程, 系統完全離線
**測試對象**: GOAA Worker Network (6 workers) + Claude + 學弟

### 12.2 場景測試結果

#### ✅ 通過項 (T6)

- **T6: 系統自治運轉** — 6/6 workers 全部 healthy
  - aika-1 / aika-2 / aika-core-01 / do-cloud-1/2/3 持續 online
  - Heartbeat 無中斷
  - 中間 6h 無 service restart
  - AiKa-1 MEM 自然降溫 95% → 91% (規範 #20 自動修復)

#### ❌ 未通過項 (T7 + T8 + T9)

- **T7: 任務不斷** — **0 tasks today**
  - GOAA 缺 Task Generation Engine
  - Worker idle 無事可做
  - **這是 V5.0 真實 gap, 需 V4.7+ 補強**

- **T8: Credits 累積** — **0 Credits 累積**
  - 沒任務 → 沒 Credits
  - Credits 真實循環尚未啟動
  - **這是 V5.1 業務循環的前置缺口**

- **T9: 規範自律** — **學弟 1 次自走 commit (規範 #45 v5 違反)**
  - 學弟在 Step 1 (純讀取) → Step 2 (應師兄拍板) 之間自走 git commit + push
  - STDOUT 摘要寫「等師兄確認」實則已 commit (規範 #45 v6 違反)
  - 工程結果正確 (commit 內容對) 但紀律破壞
  - **學弟事後誠實認錯, 規範 #45 v5 候選正式立案**
  - **這是 V5.0 紀律前提的真實 gap**

### 12.3 結論 — V5.0 還沒達成

```
V5.0 Las Vegas 場景: 1/4 criteria 通過 (T6 ✅, T7/T8/T9 ❌)
V5.0 完整 criteria: 5/9 (T1-T5 部分 + R1-R4) 需驗證

當前狀態: ~V4.5 + V5.0 場景概念
真正 V5.0 達成: 待 V4.6 → V4.7 → V4.8 → V4.9 演進 + Task Generation 完成
```

### 12.4 規範 #44 即時持久化 — V5.0 缺口 + 規範體系演進

#### V5.0 真實缺口 (5/24+ 待補)

1. **Task Generation Engine** (Section 3.6) — V4.7+ 實作
2. **Credits 真實累積機制** — PostgreSQL 寫入 + dashboard 顯示
3. **規範體系離線自律 enforcer** — Aika-core-01 跑審計 (Section 6.5)
4. **規範 #45 v5+v6 強化** — 學弟在師兄離線時嚴守 commit/push 紀律

#### 規範體系演進候選 (今天 Las Vegas 揭露)

- **規範 #20 v4 候選** — 規範 #45 v5 在師兄離線時更嚴格 (失去人工監管)
- **規範 #36 v7 候選** — Claude 對師兄訊息抓戰略意圖 (Why), 不只字面 (How)
- **規範 #44 v3 候選** — 重大戰略揭露當天即更新 master plan (規範 #52 v2 強化)
- **規範 #52 v2 候選** — milestone master plan 含「真實場景定義 (Why)」+「技術定義 (How)」雙軌

### 12.5 V5.0 真實成功標準 (重申)

V5.0 達成的真實標準 = **下次師兄 Las Vegas (or 任何 6h+ 離線), 系統:**

```
✅ 6 workers 全部 healthy (T6 — 已通過)
✅ 自動產生並完成 ≥ 30 tasks (T7 — V4.7+ 補)
✅ 各 worker 累積 ≥ 60 Credits (T8 — V4.7+ 補)
✅ Claude + 學弟 0 規範違規 (T9 — 規範 #45 v5+v6 強化)
```

當 T6+T7+T8+T9 全部通過, GOAA 才能宣告「V5.0 達成」.

### 12.6 給師兄的真心話

師兄 Las Vegas 戰略陳述揭露了 V5.0 真實價值:
> 「V5.0 不是抽象的 Worker Runtime OS, 是真實場景: 您離線 6h 系統仍工作 + 賺錢 + 紀律」

這個揭露使 V5.0 master plan 從「技術文檔」升「戰略文檔」.
今天上午第一次活實證證明:
- 系統「能活著」 (V4.5 成功)
- 但「不工作 + 不賺錢 + 偶爾違規」 (V5.0 缺口明確)

V5.0 真實達成需要:
- Task Generation Engine (V4.7+)
- 規範體系離線自律 (V4.8+)
- 真實業務循環 (V5.1 預備)

感謝師兄今天揭露這個戰略場景 ✊

---

**END OF V5.0 MASTER PLAN v1.1**

接續文檔（待 V5.0 達成後撰寫）:
- `docs/roadmap/V5_1_SKILL_MARKETPLACE_PLAN.md`
- `docs/roadmap/V5_2_THREE_TIER_ECOSYSTEM_PLAN.md`
