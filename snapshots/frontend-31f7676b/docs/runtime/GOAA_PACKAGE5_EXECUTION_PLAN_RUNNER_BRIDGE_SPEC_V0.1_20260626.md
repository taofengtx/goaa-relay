# GOAA Package 5 — Execution Plan / Runner Bridge Dry-run Spec V0.1

## 0. Purpose

Package 5 starts the bridge from AI Workspace task intent to controlled task execution.

Package 5 does not execute real tasks.

It only defines and surfaces an execution plan that can later be consumed by a mock executor, readonly executor, or approved real executor.

## 1. Non-negotiable Safety Boundary

Package 5 must not:

- enable real executor
- call subprocess / Popen / os.system / shell
- mutate Runtime
- connect DO
- deploy
- write audit persistence
- write database
- perform real task execution
- create approve-and-run behavior

Allowed output modes remain:

- blocked
- preview_only
- plan_only
- dry_run_only

## 2. New Core Concepts

### ExecutionPlan

A response-only or in-memory object describing:

- plan_id
- request_id
- task_id
- intent
- actor_id
- approval_state
- execution_mode
- risk_level
- runner_target
- planned_steps
- required_capabilities
- forbidden_capabilities
- expected_inputs
- expected_outputs
- rollback_hint
- no_execution=true
- generated_at_utc
- source=execution_plan_gateway

### RunnerTarget

Describes where a future task could run:

- target_type: local_console | local_runner | cloud_runner | aika_box | disabled
- target_node
- target_runtime
- executor_required
- executor_enabled=false
- real_execution_allowed=false

### DryRunResult

A non-executing result:

- dry_run_id
- plan_id
- status=dry_run_only
- simulated=true
- task_executed=false
- mutation_performed=false
- evidence_package
- audit_log

## 3. Endpoint Decision — Frozen

Package 5 V0.1 uses:

POST /tasks/plan

This endpoint is plan-only and must not execute real tasks.

Package 5 V0.1 must not extend `/tasks/run` with `dry_run=true`.

Reason:

- Package 4 closed `/tasks/run` with a strict `blocked` / `preview_only` contract.
- Package 5 should introduce planning through a separate endpoint to avoid weakening the Package 4 safety boundary.
- Any future `/tasks/run` execution expansion must be handled in a later package with separate Tao approval and Baton 8 review.

## 4. Policy Matrix

| Intent Type | Package 5 Result |
|---|---|
| pure_chat | no plan |
| task_status | plan_only |
| topk_verify | plan_only |
| memory_fetch | blocked |
| embed | blocked |
| approve_task | blocked |
| reject_task | blocked |
| unknown | blocked |


## 4.1 Package 5 V0.1 Boundary

Package 5 V0.1 is not the readonly execution package.

Readonly execution allowlists are deferred to Package 8 or later.

Package 5 V0.1 may generate an ExecutionPlan and a non-executing DryRunResult, but must not read external/runtime data as a task execution side effect.

## 5. Package 5 Task Breakdown

Task 1: Spec freeze
Task 2: ExecutionPlan / RunnerTarget / DryRunResult models
Task 3: /tasks/plan endpoint skeleton
Task 4: Policy matrix + risk classification
Task 5: AI Workspace UX display for plan
Task 6: Regression + forbidden surface scan
Task 7: Baton 12 archive

## 6. Acceptance Criteria

Package 5 is complete only when:

- no real task execution occurs
- all execution flags remain false
- plan_only / dry_run_only are clearly distinct from execution
- no executor path is enabled
- no persistence is introduced
- UX clearly states plan only / no execution
- tests prove blocked and plan_only behavior
- Baton 8 review passes
- Tao approves commit and push
- Baton 12 archive is committed and pushed
