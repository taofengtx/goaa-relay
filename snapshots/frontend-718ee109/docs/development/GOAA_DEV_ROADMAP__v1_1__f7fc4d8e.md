# GOAA.AI 完整開發進度表 v1.1

**簽發**: 2026-05-19 (基於 v1.0 + 5/19 真實盤點 + 三端鐵律 7d49efd)
**戰略鐵律**: 先有生產線 → 再有工作台 → 先 Provider 現金流 → 再 Client 平台 → 先內部 Worker → 再開放開發者
**最高戰略鐵律 (7d49efd)**: Worker 負責生產能力；Provider 負責接單、跟單、調用專業 Skill 並交付服務；Client 負責提出需求、查看進度、與 Provider 互動並使用生活化 Skill。
**v1.1 變更摘要**: 拆 P1.2 為 P1.2.0/.1/.2 三階段（基於 5/19 api.py + db.py 真實盤點，揭露「記憶體 + PG 脫節」過渡狀態）

---

## 📌 已完成里程碑 (2026-05-16 → 05-19)

| ☑ | 日期 | 戰績 | Commit |
|:-:|:----|:----|:----|
| ☑ | 5/16 | 戰略憲法 V1.0 + Marketing v1 + UI 黃金版 V4.0.5.4 升級 | c909c3b / 76b7980 |
| ☑ | 5/17 | V5.0 Chat Workspace Strategy + HANDOFF.md V1.0 | 32ea682 / c9f289b |
| ☑ | 5/19 凌晨 | HANDOFF.md 文末修補 + V2.0 Marketing Matrix (2939 行) | 363ac4a / 28c574f |
| ☑ | 5/19 凌晨 | Provider-First Strategy Update (+1383 行) | 3358360 |
| ☑ | 5/19 早上 | AiKa-Box Pro Alpha docx (真實 spec + 4 張產品照) | 37e453a |
| ☑ | 5/19 早上 | 規範 #40 立規 (文檔交付命名) + Memory 3 條升級 | — |
| ☑ | 5/19 中午 | **三端最終鐵律全線部署 (4 docs + Memory + GitHub)** | **7d49efd** |
| ☑ | 5/19 中午 | agent.py + api.py + db.py + PG schema 真實盤點 | — |

---

# 🎯 Phase 1 — Worker V5.0 內部生產線跑通 (現在 → 2 週內)

> **目標**: 同一個任務, QwenPaw 能做, GOAA Worker 也能做
> **戰略憲法**: 第 2 章主線優先級永不變
> **v1.1 重大發現** (5/19 盤點): 當前架構是「**記憶體調度 + PG 持久化脫節**」過渡狀態。task_pool 是 dict、task_queue 是 list、tool_invocations 表存在但完全沒接線。P1.2 必須拆三階段。

## P1.1 — db.py 物理審查 (5/19 已完成 60%)

| ☑ | 子任務 | 規範 | 預估 | 狀態 |
|:-:|:----|:----|:----|:----|
| ☑ | db.py 完整函數清單盤點 (init_pool/get_conn/_exec/task_*/session_*/message_*) | #24 | 30m | 5/19 完成 |
| ☐ | _exec() 接口契約最終確認 (直接呼叫式, 不是 context manager) | #24 | 30m | 待 P1.2.1 寫 wrapper 時驗證 |
| ☐ | 廣域 try/except 盤點 (agent.py 已查 ✅, api.py 待) | #18 | 1h | api.py 564 行待掃 |
| ☑ | tasks / tool_invocations / tools 表 schema 驗證 | #36 v2 | 30m | 5/19 完成 |

## P1.2 — PG 持久化打通 ⭐ v1.1 重新拆解

### P1.2.0 — tasks 表 PG 持久化（**新增前置任務**）

> **背景**: db.py 有 task_upsert() 函數但 api.py 任務管理全在記憶體 dict + queue list, task_upsert 幾乎沒被調用。process 重啟所有任務丟失, tool_invocations 無法做 FK 關聯。
> **必要性**: 沒有 PG 化的 task_id, tool_invocations 寫入無意義 (記憶體 ID 沒持久性)。

| ☐ | 子任務 | 規範 | 預估 |
|:-:|:----|:----|:----|
| ☐ | api.py 4 個 hook point 接入 task_upsert(): /tasks/dispatch / /tasks/next / /task/complete / dispatch error | #11 #24 | 2h |
| ☐ | task_id 規範: 沿用現有 gen_task_id() 字串格式 (tasks.id 是 varchar PK) | #25 | 0.5h |
| ☐ | 記憶體 dict 改為「持久化備份 + 記憶體緩存」混合模式 (規範 #11 only-add) | #11 | 0.5h |

### P1.2.1 — tool_invocations 雙寫機制（原 P1.2）

| ☐ | 子任務 | 規範 | 預估 |
|:-:|:----|:----|:----|
| ☐ | API 層 POST /tool_invocations 端點 (新增, 非嵌入式) | #24 接口契約 | 1h |
| ☐ | Worker 端 record_invocation(tool_id, args, result, duration_ms, error) helper | #25 跨層型別 | 1h |
| ☐ | tool_invocations 寫入 4 個 hook point: tool_start / tool_success / tool_error / tool_timeout | #28 不靜默 | 1h |
| ☐ | session_id 取得策略 (從 task 反查 message 反查 session) | #25 #36 v2 | 1h |

### P1.2.2 — tools 表預填基礎註冊

| ☐ | 子任務 | 規範 | 預估 |
|:-:|:----|:----|:----|
| ☐ | tools 表插入 6 個 read-only tool 註冊 (health_check / docker_status / ...) | #25 | 0.5h |
| ☐ | category 字段確認 (現有 enum: query/dispatch/communication/compute/storage) | #25 | 0h (現有) |

## P1.3 — 6 個 Read-only Executor (依賴 P1.2.1 完成)

| ☐ | 子任務 | 規範 | 預估 |
|:-:|:----|:----|:----|
| ☐ | exec_shell_inventory (白名單 read-only 命令, 5s timeout) | #22 #18 | 1.5h |
| ☐ | exec_file_read (限定路徑 + 1MB cap) | #28 | 1h |
| ☐ | exec_git_status (--no-fetch) | #11 | 0.5h |
| ☐ | exec_docker_status 升級 (shutil.which 預檢, 規範 #18) | #18 | 1h |
| ☐ | exec_log_summary 升級 (path allowlist + tail + grep) | #28 | 1h |
| ☐ | exec_system_status 升級 (psutil 整合) | — | 1h |
| ☐ | **每個 executor 都呼叫 record_invocation()** | #36 v2 | (內建) |

## P1.4 — dispatch_task async (依賴 P1.2.0 完成)

| ☐ | 子任務 | 規範 | 預估 |
|:-:|:----|:----|:----|
| ☐ | async 改造 (不阻塞心跳) | #28 | 3h |
| ☐ | worker_events 事件流 (Runtime Truth) | #36 v2 | 2h |
| ☐ | Quality Score 結算 (QS < 0.6 退回 redo) | 憲法 | 2h |

## P1.5 — Phase 1 驗收

| ☐ | 子任務 | 規範 | 預估 |
|:-:|:----|:----|:----|
| ☐ | QwenPaw vs GOAA Worker 並排測 10 個任務 | #36 v2 | 4h |
| ☐ | 5 個 Live 節點 (aika-1/2 + do-cloud-1/2/3) 全部過測 | — | 2h |
| ☐ | DO model-router 補 systemd unit (P1 改善項) | #18 兩階段 | 1h |
| ☐ | tool_invocations 表寫入率 ≥ 95% (規範 #36 v2 Runtime Truth) | #36 v2 | (驗收項) |

**Phase 1 v1.1 預估總工時**: ~33h (原 30h + P1.2.0 新增 3h)

---

# 🎯 Phase 2 — 官網 V2.0 Framer 落地 (沿用 v1.0, 無變化)

> v1.1 變更: 加入「Section 3.4 / 5.2 / 5.3 三端邊界 polish」為一次性任務 (1h, 從 marketing patch append 末尾 polish 到精確位置)

## P2.0 — MARKETING_MATRIX_V2 polish (v1.1 新增, 收工前做)

| ☐ | 子任務 | 預估 |
|:-:|:----|:----|
| ☐ | Section 3.4 / 5.2 / 5.3 精準 polish 到位置 (從文末 append 移到正確 section 內) | 1h |

(其餘 P2.1 ~ P2.6 沿用 v1.0 進度表)

---

# 🎯 Phase 3 ~ Phase 5 — 沿用 v1.0 進度表

(P3 / P4 / P5 全部章節不變, 商業順序鐵律不變)

---

# 🎯 並行任務 — v1.1 新增

## PA.5 — 規範立規 (收工前集中)

| ☐ | 候選規範 | 規範 # |
|:-:|:----|:----|
| ☐ | 每日開工核對開發進度總表 | #41 候選 |
| ☐ | 三端產品邊界鐵律 (已部署於 docs/AGENTS.md, 補規範號) | #42 候選 |
| ☐ | ask_user_input_v0 UI 渲染斷文時 Claude 必須附純文字 fallback | #43 候選 |
| ☐ | 違規先記憶, 收工前集中立規 (5/19 已執行, 補規範號) | #44 候選 |

(其他並行任務 PA.1-PA.4 沿用 v1.0)

---

# 📋 每日工作 checklist 模板 (沿用 v1.0)

(模板章節不變)

---

# 🎯 戰略順序鐵律 (永不調亂, 與 v1.0 一致)

```
1. Phase 1 Worker V5.0 內部生產線跑通  ←現在 (v1.1 P1.2 拆三階段)
2. Phase 2 官網 V2.0 Framer 落地     ←並行
3. Phase 3 Provider AI 工作台 MVP (Insurance Priority A)
4. Phase 4 AiKa Box Software Kit 出貨
5. Phase 5 高頻流程資產化 → Skill Marketplace
6. Phase 5+ Client Plus + Worker Developer 開放
```

**最高行動原則 (v1.1 對齊三端鐵律 7d49efd)**:

> Worker 負責生產能力；Provider 負責接單、跟單、調用專業 Skill 並交付服務；Client 負責提出需求、查看進度、與 Provider 互動並使用生活化 Skill。

> 拋棄全民 AI 幻想, 前 6 個月死磕每月 $39.99 的華人 Provider AI 自動化工作台.

---

**進度表簽發**: 2026-05-19 (PT) Claude (基於師兄 v1.0 框架 + 5/19 真實盤點)
**v1.1 變更**: P1.2 拆三階段 / P1.4 依賴 P1.2.0 / 加入 P2.0 polish / 加入 PA.5 立規清單 / 對齊 7d49efd 三端鐵律
**下次版本**: 完成 P1.2.0 後升級為 v1.2 (記錄 commit hash)
**規範遵守**: #11 / #12 / #15 / #19 v2 / #20 / #28 / #36 v2 / #40 / 三端最終鐵律 (凌駕所有)
