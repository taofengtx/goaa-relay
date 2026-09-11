# GOAA AI Workspace Package 2 UX & Response Alignment Spec V0.1

## 1. Background

Package 1 has completed the first AI Workspace conversation-to-task MVP chain:

text
AI Conversation
→ Intent Detection
→ Task Envelope Preview
→ Frontend Task Preview Card
→ Tao Approval Gate
→ Readonly Dry-run Evidence Preview


Package 1 was merged into `main` via PR #12 (commit `c588d22`) and verified locally on `127.0.0.1:5188`.

## 2. Tao Local Test Findings

Tao tested the local AI Workspace after Package 1 merge on 2026-06-22.

Observed behavior:

| User Input | Detected Intent | Current Result | Status |
|---|---|---|---|
| 你好 | pure_chat | Normal chat reply, but Task Preview card is displayed | Needs UX improvement |
| 查询知识库 | topk_verify | Readonly evidence preview appears, but AI text says tool is unavailable | Needs response alignment |
| 重建索引 | embed | L4 critical risk, Tao Approval Gate blocks execution | Pass |
| 查看目前的所有任務狀態 | task_status | Readonly evidence preview + task status summary appears | Pass |
| 拒绝任务 | reject_task | Approval gate not_required, preview generated | Pass |
| 批准任务 | approve_task | Approval gate not_required, preview generated | Pass |
| 查记忆 | memory_fetch | Detected as memory_fetch, no evidence preview (correct per scope fix) | Pass |

Key issues:

1. `pure_chat` should not show Task Preview / Evidence Preview cards at all.
2. AI reply text does not reflect detected intent (e.g. "I don't have a tool for that" when intent is recognized).
3. Evidence preview card wording is engineering-oriented, not product-facing.

## 3. Package 2 Goals

Package 2 turns the Package 1 engineering MVP into a cleaner user-facing AI Workspace experience.

Goals:

1. Hide Task Preview and Evidence Preview for `pure_chat`.
2. Align AI response text with the detected task intent.
3. Make preview-only behavior explicit and user-friendly.
4. Keep high-risk task blocking clear and reassuring.
5. Preserve all Package 1 safety guarantees.

### Expected Response Alignment

#### pure_chat

Normal chat only — no Task Preview, no Evidence Preview.

#### task_status

AI response should say:

text
已识别为任务状态查询。
当前为只读预览，不会执行真实任务。
下面是系统生成的 Task Preview 与 Evidence Preview。


#### topk_verify

AI response should say:

text
已识别为知识库查询 / Top-K 验证请求。
当前只生成 readonly dry-run evidence preview，不会执行真实 RAG 查询或任务。


#### embed

AI response should say:

text
这是高风险索引操作。
系统已通过 Tao Approval Gate 阻断。
当前不会执行重建索引、不会调用 executor、不会修改 Runtime。


#### memory_fetch

AI response should say:

text
已识别为记忆读取请求。
当前为只读预览，不会执行真实查询。

(Or optionally hide preview entirely.)

#### approve_task / reject_task

AI response should say:

text
已识别为 {approve/reject} 任务请求。
当前为只读预览模式，不会执行真实审批操作。
需 Tao 授权后启用真实执行。


## 4. Non-goals

Package 2 does not do the following:

- No production deployment.
- No DO connection.
- No real executor.
- No real worker.
- No real task execution.
- No `/tasks/run` execution.
- No real RAG query execution.
- No embedding rebuild.
- No Runtime service mutation.
- No authentication system changes.
- No multi-user support.

## 5. Proposed Task Breakdown

### Task 2 — Hide pure_chat Task Preview

- **File**: `local-console/main.py`
- **Change**: In `renderTaskPreview()` and `renderEvidencePreview()`, return early if intent is `pure_chat`.
- **Test**: New test case in `test_ai_chat_intent_preview.py` verifying `pure_chat` does not render cards.

### Task 3 — Align AI Response Copy with Intent Detection

- **File**: `local-console/main.py`
- **Change**: After building the AI reply text, post-process or append context based on `detection_result.intent`.
- **Approach**: Append a localized copy line to the AI answer based on detected intent.
- **Test**: New test file or additions verifying aligned response copy.

### Task 4 — Improve Evidence Preview UI Wording

- **File**: `local-console/main.py` (frontend JS)
- **Change**: Update `renderEvidencePreview()` labels:
  - "Preview only — no task executed"
  - "Task executed: false" → "未执行" or clearer wording
  - "Runtime mutation: false" → "无运行时变更"
  - Safety section: "readonly / no worker / no executor / no DO"
- **Test**: Visual/functional test in browser or JS-rendering test.

### Task 5 — Add UX Regression Tests

- **File**: `local-console/tests/test_package2_ux_alignment.py` (new)
- **Tests**:
  - `pure_chat` no task card.
  - `task_status` aligned copy.
  - `topk_verify` aligned copy.
  - `embed` blocked copy.
  - `memory_fetch` aligned or hidden copy.
  - Legacy response compatibility.
  - All safety flags remain false.

### Task 6 — Package-level Review

- Run full 84+ tests.
- Manual smoke test on local console.
- ChatGPT Baton 8 review of all changes.
- Tao approval for commit/push/merge.

## 6. Acceptance Criteria

Package 2 is accepted when:

1. 普通聊天不显示任务卡。
2. `task_status` 显示 aligned task-status response copy。
3. `topk_verify` 显示 aligned knowledge-query response copy。
4. `embed` 高风险任务显示 Tao Gate blocked response copy。
5. `memory_fetch` 显示 aligned memory-read copy。
6. All task previews remain preview-only.
7. `task_executed=false` remains true for all preview flows.
8. `runtime_mutation=false` remains true for all preview flows.
9. No `/tasks/run` execution is added.
10. No subprocess / os.system calls are added.
11. No secret/private key reads are added.
12. Existing Package 1 tests continue passing (84 tests).
13. New Package 2 UX regression tests pass.

## 7. Safety Boundary

The core rule remains:

text
Preview is not execution.
Tao Gate protects high-risk tasks.
No executor without explicit Tao production authorization.


All Package 2 changes must preserve:

- `task_executed=false` for all preview-only flows
- `runtime_mutation=false`
- No `/tasks/run` calls
- No subprocess / os.system
- No DO connection
- No secret/private key reads
