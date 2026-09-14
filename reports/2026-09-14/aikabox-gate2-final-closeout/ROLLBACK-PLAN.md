# ROLLBACK PLAN (documented only - NOT executed)

Nothing was applied to `:5188`, so there is nothing to roll back today. This plan is the
pre-authorized procedure for the future cutover.

## 1. Golden-05 (source of truth) - current state

| Item | Value |
|---|---|
| Working dir (serving) | `/home/aika/Projects/goaa-ai-main/local-console` |
| Repo | `/home/aika/Projects/goaa-ai-main`, branch `codex/backend-source-capture-20260902`, HEAD `301b8ea` |
| `main.py` sha256 | `0c78b8e83516613a45b648331e90e07e64e02a034add55aac2920a3a7eb7364e` (152,687 bytes) - **committed clean**, working tree has no tracked modification |
| `auth.py` sha256 | `9665e8d069bca4c87fd59f0534374c082f65a5b58c567b9d7116a4a760e32f14` |
| Service | `goaa-local-console.service` (unit + drop-in as recorded in `GOLDEN05-UNCHANGED-EVIDENCE.md`) |
| Port | `5188` (127.0.0.1 + tailnet proxy) |

Because the golden `main.py` is committed and the tree is clean, rollback can be done
either by `git -C /home/aika/Projects/goaa-ai-main checkout -- local-console/main.py`
or by restoring a byte copy of the file whose hash is recorded above.

## 2. Candidate (to be applied at cutover)

| Item | Value |
|---|---|
| Source | `/home/aika/gate2-ui-wt/local-console/` @ commit `2ede799` |
| `main.py` sha256 | `2b4a1b452ad4595ae1dacea15454bf706c0182fe099dd2a760c9cac62b19e2f3` |
| `project_context.py` sha256 | `8fe454f6adae237701d42d8c926a84dec32190842afd0b420beb55a1192fc526` |
| Files to copy | **two**: `local-console/main.py` and `local-console/project_context.py` |

Note: the candidate's Project Context module reads its store from
`GOAA_PROJECTS_FILE` (default `/tmp/ui-projects.json` on the dev port) and the runtime
env on `:5198` additionally sets `QWENPAW_AUDIT_LOG`, `QWENPAW_SESSIONS_FILE` and
`QWENPAW_WORKERS_FILE`, which the current `:5188` environment file does not carry.
Any future cutover must therefore also decide the environment/drop-in change
(worker registry path, sessions file, audit log path). Without that, the QwenPaw bridge
on `:5188` would fall back to the defaults.

## 3. Pre-cutover (mandatory, not done this round)

1. Record `sha256` of the two target files and the service state (`MainPID`,
   `NRestarts`, `ActiveEnterTimestamp`).
2. Copy the current golden `main.py` to a timestamped backup outside the repo.
3. Record the current env file / drop-in content.

## 4. Cutover procedure (supervised, Tao present)

1. `sudo systemctl stop goaa-local-console.service`
2. Copy candidate `main.py` + `project_context.py` into the golden working directory.
3. Re-verify the copied hashes against the manifest.
4. `sudo systemctl start goaa-local-console.service`
5. Health check: `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5188/health` -> `200`.
6. Login check: open `/login`, authenticate with the console session key, confirm the
   AI workspace tab renders and the worker list loads.
7. Only then, by Tao personally in the UI, exercise a real PENDING approval.

## 5. Rollback procedure (supervised)

1. `sudo systemctl stop goaa-local-console.service`
2. Restore the backed-up `main.py` (or `git checkout -- local-console/main.py`), remove
   `project_context.py` if the cutover added it.
3. Re-verify `main.py` = `0c78b8e83516613a45b648331e90e07e64e02a034add55aac2920a3a7eb7364e`.
4. `sudo systemctl start goaa-local-console.service`
5. Health check `200`, login check, worker list check.
6. Record the outcome in a new append-only relay report.

## 6. State

| Gate | State |
|---|---|
| Rollback Ready | **YES** (procedure known; golden source committed at `301b8ea`) |
| Rollback executed this round | **NO** (forbidden this round) |
| `:5188` restarted this round | **NO** |
