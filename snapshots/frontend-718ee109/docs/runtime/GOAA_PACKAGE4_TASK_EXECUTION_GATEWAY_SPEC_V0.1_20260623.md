# GOAA Package 4 Task Execution Gateway Spec V0.1

## 1. Purpose

Package 4 defines the first safe gateway for `/tasks/run`.

This package does not enable real execution by default. It creates a gated, auditable, policy-controlled execution boundary between AI Workspace task previews and any future real action.

## 2. Current State

Package 1 delivered:
- intent detection
- task envelope preview
- Tao Approval Gate
- readonly evidence preview

Package 2 delivered:
- UX response alignment
- pure_chat preview hiding
- Evidence Preview wording

Package 3 delivered:
- Runtime activation
- 5188 systemd runtime aligned with Git main

## 3. Non-goals

Package 4 Task 1 does not:
- implement `/tasks/run`
- execute tasks
- enable executor
- start workers
- connect DO
- deploy production
- perform real RAG queries
- rebuild embeddings
- mutate Runtime
- read secrets
- read private keys

## 4. Execution Modes

- preview_only
- readonly_dry_run
- approved_local_action
- blocked

## 5. Approval States

- not_required
- required
- approved_by_tao
- rejected_by_tao
- expired

## 6. Risk Levels

- L0 information
- L1 readonly
- L2 local_dry_run
- L3 local_mutation
- L4 critical_runtime

## 7. TaskRunRequest

Required fields:
- request_id
- task_id
- envelope_id
- intent
- risk_level
- execution_mode
- approval_state
- approval_id
- actor_id
- requested_action
- normalized_parameters
- parameter_digest
- created_at
- expires_at
- source_message_hash
- runtime_context
- rollback_plan
- evidence_required
- policy_version

## 8. TaskRunResult

Required fields:
- run_id
- request_id
- status
- execution_mode
- task_executed
- mutation_performed
- worker_started
- executor_enabled
- do_connected
- real_rag_query_executed
- embedding_rebuild_executed
- started_at
- completed_at
- evidence_package_id
- audit_log_id
- result_summary
- error_code
- error_message

## 9. Initial Intent Policy Matrix

| Intent | Initial Mode | Approval | Execution |
|---|---|---|---|
| pure_chat | preview_only | not_required | never |
| task_status | readonly_dry_run | not_required | no mutation |
| topk_verify | readonly_dry_run | not_required | no real RAG in first version |
| memory_fetch | preview_only | required if personal memory | no private access by default |
| embed | blocked | required | no rebuild |
| approve_task | preview_only | approved_by_tao only | approval record only |
| reject_task | preview_only | rejected_by_tao only | rejection record only |

## 10. Permanently Forbidden Without Explicit Tao Approval

- DO connection
- production deployment
- systemd restart
- Runtime mutation
- worker start
- executor enable
- real shell command
- file deletion
- git push
- git merge
- secret read
- private key read
- embedding rebuild
- real RAG query against private corpus
- external cost-incurring API call

## 11. Audit Log

Every `/tasks/run` attempt must produce an audit record, including blocked attempts.

Audit fields:
- audit_log_id
- request_id
- actor_id
- intent
- risk_level
- approval_state
- decision
- denial_reason
- runtime_truth_snapshot
- git_truth_snapshot
- documentation_truth_snapshot
- created_at

## 12. Evidence Package

Every run or dry-run must produce evidence.

Evidence fields:
- evidence_package_id
- request_id
- run_id
- readonly
- preview_only
- task_executed
- runtime_mutation
- worker_started
- executor_enabled
- do_connected
- real_rag_query_executed
- embedding_rebuild_executed
- evidence_summary
- created_at

## 13. Rollback Plan

Any action above L1 must include rollback_plan before it can be approved.

Rollback fields:
- rollback_available
- rollback_steps
- rollback_risk
- rollback_owner
- rollback_test

## 14. Three Truth Layers

Every execution decision must record:

Runtime Truth:
- active runtime
- process/service
- endpoint
- current behavior

Git Truth:
- branch
- commit
- dirty state

Documentation Truth:
- spec version
- policy version
- approval record

## 15. Package 4 Task Breakdown

Task 1:
- Gateway spec only

Task 2:
- TaskRunRequest / TaskRunResult pure data model

Task 3:
- `/tasks/run` endpoint skeleton returning blocked/preview-only responses only

Task 4:
- Approval Gate enforcement

Task 5:
- Audit Log and Evidence Package preview

Task 6:
- UX integration and package-level regression

Task 7:
- Baton 12 archive

## 16. Closure Criteria

Package 4 cannot be considered complete until:
- `/tasks/run` never executes without gate
- blocked attempts are logged
- dry-run attempts produce evidence
- Tao approval state is enforced
- tests prove no worker/executor/DO/task execution occurs by default
