# GOAA.AI 完整開發進度表 v1.2

**簽發**: 2026-06-12 (基於 v1.1 + 6/12 真實盤點 + F 線定位)
**戰略鐵律**: 先有生產線 → 再有工作台 → 先 Provider 現金流 → 再 Client 平台 → 先內部 Worker → 再開放開發者
**最高戰略鐵律 (7d49efd)**: Worker 負責生產能力；Provider 負責接單、跟單、調用專業 Skill 並交付服務；Client 負責提出需求、查看進度、與 Provider 互動並使用生活化 Skill。
**v1.2 變更摘要**: 真實盤點 Phase 1 完成狀態 — P1.4/B線/C線 ☐→✅、D線/P1.2.0 ☐→🟡、P1.3 ☐→⬜(歸入 F-lite)、新增 F 線(半自動執行，本次設計目標)；里程碑已存檔 docs/dev-log/2026-06-12-milestone.md (commit 9a7b580)

---

## 📌 已完成里程碑 (2026-05-16 → 06-12)

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
| ☑ | 6/9 | **C 線完整閉環** — Console AI Workspace 接真實 DeepSeek 端到端 (C.1 + D.1) | 908ec2a |
| ☑ | 6/9 | **B 線 Node Health 真實化** — telemetry/systemd//node/health/UI/reboot (B1-B5) | 908ec2a |
| ☑ | 6/10 | **D 線 Cloud Binding 核心鏈路通** — 心跳自 6/9 未斷,節點 online, PG nodes 表已註冊 | 908ec2a→deebcc6 |
| ☑ | 6/10 | **db.py 硬編碼密碼移除** + PG 密碼輪換 (規範 #22) | deebcc6 |
| ☑ | 6/12 | **三端盤點 + F 線真實定位** — Router 風險引擎確認為 F-lite 地基 | 9a7b580 |

---

# 🎯 Phase 1 — Worker V5.0 內部生產線跑通

> **目標**: 同一個任務, QwenPaw 能做, GOAA Worker 也能做
> **v1.2 狀態**: Dogfooding 地基 (B/C/D) 已通；F 線(安全執行層)為本次設計目標

### Phase 1 完成狀態總表 (v1.2 真實盤點)

| # | 子項 | v1.1 狀態 | v1.2 狀態 | 證據 / 備註 |
|:-:|:----|:---------:|:---------:|:----------|
| | **Dogfooding 地基** | | | |
| B | 節點數據真實化 | ☐ | **✅** | B1-B5 完整: telemetry → /node/health → UI → systemd → reboot |
| C | AI 工作區接 LLM | ☐ | **✅** | C.1 /ai/chat + D.1 UI, 真實 DeepSeek 端到端 |
| D | Cloud Binding | ☐ | **🟡** | 鏈路通(心跳 alive, PG nodes 持久化), 閉環缺口: Router 實時狀態未完整 PG 化 + 文檔未補 |
| A | 補 SOON 頁 | ☐ | ⬜ | 未觸及 |
| | **Phase 1 核心** | | | |
| P1.1 | db.py 物理審查 | 🟡 60% | 🟡 60% | 未推進 |
| P1.2.0 | tasks 表 PG 持久化 | ☐ | **🟡** | Router dispatch 已寫 PG, 但 task_upsert() 4 個 hook point 未全接入 |
| P1.2.1 | tool_invocations 雙寫 | ☐ | ⬜ | 仍未接線 |
| P1.2.2 | tools 表預填註冊 | ☐ | ⬜ | 仍未做 |
| P1.3 | Read-only Executor 白名單 | ☐ | **⬜(歸入 F-lite)** | 安全執行層將納入白名單設計 |
| P1.4 | dispatch_task async | ☐ | **✅** | auto_dispatcher_loop thread 已在生產運行 |
| P1.5 | Phase 1 驗收 | ☐ | ⬜ | 待 F 線完成後 |
| | **v1.2 新增** | | | |
| F | 安全執行層 (F-lite) | — | **⬜(本次設計目標)** | 形式化 Router 現有風險引擎 + 審批 UI + 節點白名單 |

## P1.1 — db.py 物理審查

| ☑ | 子任務 | 規範 | 預估 | 狀態 |
|:-:|:----|:----|:----|:----|
| ☑ | db.py 完整函數清單盤點 (init_pool/get_conn/_exec/task_*/session_*/message_*) | #24 | 30m | 5/19 完成 |
| ☐ | _exec() 接口契約最終確認 (直接呼叫式, 不是 context manager) | #24 | 30m | 待 P1.2.1 寫 wrapper 時驗證 |
| ☐ | 廣域 try/except 盤點 (agent.py 已查 ✅, api.py 待) | #18 | 1h | api.py 564 行待掃 |
| ☑ | tasks / tool_invocations / tools 表 schema 驗證 | #36 v2 | 30m | 5/19 完成 |

## P1.2 — PG 持久化打通

### P1.2.0 — tasks 表 PG 持久化

> **v1.2 更新**: Router dispatch 已透過 INSERT INTO tasks / UPDATE tasks 寫入 PG (heartbeat handler 的 nodes 表也通了), 但 task_upsert() 4 個 hook point 未全接入。任務生命週期仍在記憶體 dict + queue list 主導。**狀態: 🟡 核心路通, 閉環缺口。**

| ☐ | 子任務 | 規範 | 預估 | 狀態 |
|:-:|:----|:----|:----|:----|
| ☐ | api.py 4 個 hook point 接入 task_upsert(): /tasks/dispatch / /tasks/next / /task/complete / dispatch error | #11 #24 | 2h | 🟡 部分已通(dispatch→PG), 未完整 |
| ☐ | task_id 規範: 沿用現有 gen_task_id() 字串格式 (tasks.id 是 varchar PK) | #25 | 0.5h | ⬜ |
| ☐ | 記憶體 dict 改為「持久化備份 + 記憶體緩存」混合模式 (規範 #11 only-add) | #11 | 0.5h | ⬜ |

### P1.2.1 — tool_invocations 雙寫機制

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

## P1.3 — 安全執行白名單 (歸入 F-lite)

> **v1.2 變更**: P1.3 不再獨立執行, 其內容(exec_shell_inventory/exec_file_read/exec_git_status/exec_docker_status/exec_log_summary/exec_system_status + record_invocation)將作為 **F 線安全執行層的子項**重新設計。見 `docs/runtime/f-line-execution-layer.md` (待起草)

## P1.4 — dispatch_task async

> **v1.2 更新**: **✅ 已完成**。auto_dispatcher_loop() thread 已在生產運作 (api.py L206-247), 含風險阻擋 (P0/P1 + risk≥4 待審批)、worker 輪詢派發、complete/cancel。Quality Score 結算尚未實現。

| ☑ | 子任務 | 規範 | 備註 |
|:-:|:----|:----|:----|
| ☑ | async 改造 (不阻塞心跳) | #28 | auto_dispatcher_loop daemon thread, 心跳獨立 |
| ☐ | worker_events 事件流 (Runtime Truth) | #36 v2 | ⬜ 待接 |
| ☐ | Quality Score 結算 (QS < 0.6 退回 redo) | 憲法 | ⬜ 待接 |

## P1.5 — Phase 1 驗收 (待 F 線完成後)

| ☐ | 子任務 | 規範 | 預估 |
|:-:|:----|:----|:----|
| ☐ | QwenPaw vs GOAA Worker 並排測 10 個任務 | #36 v2 | 4h |
| ☐ | 5 個 Live 節點 (aika-1/2 + do-cloud-1/2/3) 全部過測 | — | 2h |
| ☐ | DO model-router 補 systemd unit (P1 改善項) | #18 兩階段 | 1h |
| ☐ | tool_invocations 表寫入率 ≥ 95% (規範 #36 v2 Runtime Truth) | #36 v2 | (驗收項) |

---

# 🎯 F 線 — 安全執行層 (v1.2 新增)

> **目標**: 形式化 Router 現有風險引擎 → 補審批 UI → 節點能力白名單 → 半自動 Dogfooding 閉環
> **設計文檔**: `docs/runtime/f-line-execution-layer.md` (待起草)
> **基礎**: Router 生產 api.py 已內建 TASK_REVENUE(risk 1-4) + select_model(高風險走 Claude) + auto_dispatcher_loop(P0/P1+risk≥4 阻擋)

## F.1 — 設計文檔

| ☐ | 子任務 | 規範 | 預估 |
|:-:|:----|:----|:----|
| ☐ | 風險引擎形式化 (對齊 P3-7 四級) | #11 | 1h |
| ☐ | 審批 UI 接 5188 (HIGH/CRITICAL 彈窗) | — | 2h |
| ☐ | 節點能力白名單 (agent-roles.md security_limits) | #22 #28 | 1.5h |
| ☐ | secret 攔截 + 危險命令黑名單 | #22 | 1h |

---

# 🎯 Phase 2 — 官網 V2.0 Framer 落地 (沿用 v1.1, 無變化)

## P2.0 — MARKETING_MATRIX_V2 polish

| ☐ | 子任務 | 預估 |
|:-:|:----|:----|
| ☐ | Section 3.4 / 5.2 / 5.3 精準 polish 到位置 (從文末 append 移到正確 section 內) | 1h |

(其餘 P2.1 ~ P2.6 沿用 v1.0 進度表)

---

# 🎯 Phase 3 ~ Phase 5 — 沿用 v1.0 進度表

(P3 / P4 / P5 全部章節不變, 商業順序鐵律不變)

---

# 🎯 並行任務

## PA.5 — 規範立規

| ☐ | 候選規範 | 規範 # |
|:-:|:----|:----|
| ☐ | 每日開工核對開發進度總表 | #41 候選 |
| ☐ | 三端產品邊界鐵律 (已部署於 docs/AGENTS.md, 補規範號) | #42 候選 |
| ☐ | ask_user_input_v0 UI 渲染斷文時 Claude 必須附純文字 fallback | #43 候選 |
| ☐ | 違規先記憶, 收工前集中立規 | #44 候選 |

---

# 📋 戰略順序鐵律 (永不調亂)

```
1. Phase 1 Worker V5.0 內部生產線跑通  ←F 線執行中
2. Phase 2 官網 V2.0 Framer 落地     ←並行
3. Phase 3 Provider AI 工作台 MVP (Insurance Priority A)
4. Phase 4 AiKa Box Software Kit 出貨
5. Phase 5 高頻流程資產化 → Skill Marketplace
6. Phase 5+ Client Plus + Worker Developer 開放
```

**最高行動原則 (7d49efd)**: Worker 負責生產能力；Provider 負責接單、跟單、調用專業 Skill 並交付服務；Client 負責提出需求、查看進度、與 Provider 互動並使用生活化 Skill。

---

**進度表簽發**: 2026-06-12 (PT)
**v1.2 變更**: 真實盤點 Phase 1 完成狀態 / P1.4☐→✅ / B☐→✅ / C☐→✅ / D☐→🟡 / P1.2.0☐→🟡 / P1.3☐→⬜(歸入F-lite) / 新增 F線 ⬜(本次設計目標) / 里程碑 9a7b580
**下次版本**: 完成 F-lite 設計文檔後升級為 v1.3
**規範遵守**: #11 / #12 / #15 / #19 v2 / #20 / #28 / #36 v2 / #40 / #42 / 三端最終鐵律 (凌駕所有)

## Backlog (2026-06-13 收工)
1. 🔴 2a 未進 git：infra↔router 對齊 + 2a 進版控
2. 🔴 PG 密碼洩漏覆盤（已輪換）
3. 🟡 audit_log 直查驗證
4. 🟡 Aika 紀律 #A1-A7 強化
5. ⬜ 第四刀：5188 審批 UI（proxy 已有）
