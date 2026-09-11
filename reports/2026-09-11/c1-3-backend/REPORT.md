# Round C1.3 (1/2) — backend: deploy the golden-session routes to 3103

**Scope honoured:** only the C2 test environment was touched — the 3103 service and the
`goaa_c2test` database. C1 production, 3100/3101, `goaa_c2`, the Golden Flow and payments were
not touched. No code was pushed to any application repository; this report is the only artefact.

**Root cause being fixed** (`reports/2026-09-11/c1-2-diag/REPORT.md`): the deployed backend
`/opt/goaa-test/backend-clerk-20260910` had no `golden_session.py` and no `/golden/session`
routes, so `POST /api/v1/agent-loop/golden/session` answered **404**.

---

## E1 — candidate identity and tests

- backend worktree `/home/aika/.qwenpaw/workspaces/default/work/c2-pg-agent-loop-20260909`
  (candidate root `services/c2_agent_loop`), branch `feat/c2-pg-agent-loop-v1`
- `git rev-parse HEAD` = **`dc64591ba7485aa973f373d5340842297f28b630`** ✓ (the required commit)
- working tree clean (`git status --porcelain` empty)
- tests, run with the existing DB-free/network-free guard
  (`PYTHONPATH=/tmp/c2-clerk-block:/tmp/c2-pylib:. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3
  /tmp/c2-clerk-block/run_unit.py …`, which always passes `--noconftest`):

| file | result |
| --- | --- |
| `tests/test_clerk_identity_unit.py` | passed |
| `tests/test_golden_session_lifecycle.py` | 24 passed |
| `tests/test_golden_business_contract.py` | 9 passed |
| **total** | **45 passed / 0 failed** (`rc=0`) |

- guard report: `blocked DB/network attempts during the run: 0`

## E2 — diff, listed before touching anything

Deployed tree (31 files, excluding `__pycache__`) vs candidate `dc64591b`:

**Modified (2)**
| file | sha256 (candidate, first 16) | size | previous sha256 (first 16) |
| --- | --- | --- | --- |
| `app/main.py` | `32d8f4e5be4ca726` | 61290 B | `150b89e679cd2f90` |
| `app/config.py` | `25963a0e08c2c105` | 8006 B | `ca0320e45a9d6e28` |

**New (6)**
| file | sha256 (first 16) | size |
| --- | --- | --- |
| `app/golden_session.py` | `8355f41af72d971c` | 14903 B |
| `migrations/0006_golden_business_session.sql` | `59d6383d743caef9` | 9349 B |
| `migrations/rollback/0006_golden_business_session.down.sql` | `79481cabc6cca185` | 1490 B |
| `tests/support/sqlite_double.py` | `1966fb0ae0741e65` | 11342 B |
| `tests/test_golden_session_lifecycle.py` | `feaa3dae0b924bef` | 20126 B |
| `tests/test_golden_business_contract.py` | `80afa95380afbbc1` | 12604 B |

**Deleted:** none.

Scope check: every changed path is one of `app/main.py`, `app/config.py`,
`app/golden_session.py`, `migrations/0006*`, `migrations/rollback/0006*`, `tests/*golden*` and the
golden tests' support module `tests/support/sqlite_double.py` (used only by those two golden test
files). Nothing outside the golden-session scope changed, so the deploy was allowed to proceed.

## E3 — database `goaa_c2test` (127.0.0.1:5433)

Pre-state: `schema_migrations` held `0001_identity` … `0005_user_identities`; **none** of
`business_subjects`, `business_subject_links`, `business_tokens` existed (query for the three names
returned nothing), so migration 0006 had never been applied.

Backup taken **before** applying anything:

- file `/tmp/goaa-c2test-pre0006-20260911-074214.sql`
- size **76340 bytes**
- sha256 **`cfbb0d709a387f7c04a5edd41701e91d4075287cc008010b3f0b0b5a8c394c1e`**
- produced with `pg_dump -h 127.0.0.1 -p 5433 -U goaa_c2_migrate -d goaa_c2test --no-owner
  --no-privileges` (`dump_rc=0`), i.e. through the dedicated migrate role over TCP as all previous
  rounds did

Guard before applying: `select current_database()` returned `goaa_c2test @ 127.0.0.1/32:5433`;
an explicit assertion query returned `OK: goaa_c2test`.

Apply: `0006_golden_business_session.sql` was copied to the host (sha256 **both sides**
`59d6383d743caef9ed1a26f388cafc77bfad2cb673e2ce950b5b21dafeef253d`) and executed with
`psql -1 -v ON_ERROR_STOP=1 -X -h 127.0.0.1 -p 5433 -U goaa_c2_migrate -d goaa_c2test -f …`
→ **apply_rc=0**, no error output.

Post-state verification (all read-only queries):

- the three tables exist: `business_subject_links`, `business_subjects`, `business_tokens`
- columns
  - `business_subjects`: `id:uuid`, `kind:text`, `created_at:timestamptz`, `updated_at:timestamptz` (all NOT NULL)
  - `business_subject_links`: `user_id:uuid`, `subject_id:uuid`, `linked_via:text`, `issuer:text`, `subject:text`, `created_at:timestamptz` (all NOT NULL)
  - `business_tokens`: `id:uuid`, `user_id:uuid`, `token:text`, `role:text`, `created_at:timestamptz`, `issued_at:timestamptz`, `last_used_at:timestamptz`, `revoked_at:timestamptz` (only the last two nullable)
- constraints
  - `business_subjects_pkey`, `business_subjects_kind_known CHECK (kind = 'customer')`
  - `business_subject_links_pkey PRIMARY KEY (user_id)`, `business_subject_links_subject_id_key UNIQUE (subject_id)`, FKs to `users(id)` and `business_subjects(id)` `ON DELETE CASCADE`, `business_subject_links_via_known CHECK (linked_via = 'clerk_issuer_subject')`
  - `business_tokens_pkey`, `business_tokens_user_id_fkey`, `business_tokens_token_key UNIQUE (token)`,
    **`business_tokens_user_token_key UNIQUE (user_id, token)`**, `business_tokens_role_known CHECK (role = 'customer')`
- indexes: the two unique keys above plus `business_tokens_user_idx (user_id)` and
  `business_tokens_live_user_idx (user_id) WHERE revoked_at IS NULL`
- `identity_events_type_known` now carries the four business events in addition to the six
  identity ones: `business.subject_linked`, `business.token_issued`, `business.token_revoked`,
  `business.token_rejected`
- grants on all three tables: `goaa_c2_app` and `goaa_c2_migrate`
- `schema_migrations`: `0001_identity … 0006_golden_business_session`
- row counts, new tables empty as expected: `business_subjects=0 business_subject_links=0 business_tokens=0`
- existing tables still present: `users`, `user_identities`, `identity_events`, `user_sessions`, …

`migrations/rollback/0006_golden_business_session.down.sql` exists (1490 B, sha256
`79481cabc6cca185…`) and was **not executed** — existence check only.

## E4 — deployment

1. full backup of the deployed tree:
   `/opt/goaa-test/backend-clerk-20260910.bak-20260911-074259` (356K, `cp -a`)
2. the 8 files above were copied one by one with `scp`; sha256 checked on both sides for each file
   → all **OK** (one retry was needed for `tests/support/sqlite_double.py` because the deployed tree
   had no `tests/support/` directory; it was created and the file re-sent, hashes matching)
3. `chown -R goaa-c2loop:goaa-c2loop` on the deployed tree; ownership verified
   (`goaa-c2loop:goaa-c2loop`, mode 644 on each changed file)
4. pre-restart syntax check without writing anything (`ast.parse` over the six changed Python files
   with the service venv) → `syntax OK: 6 files`
5. restart requested: `ssh do-c2 'systemctl restart goaa-c2-clerk-api-3103.service'`

**Approval, stated plainly:** **no 🛡 approval card appeared and no approval step was involved.**
The restart command was submitted directly and ran immediately; it was therefore **not** "approved
by Tao and then executed". Same behaviour as the previous round's restart.

Result: `is-active=active`, **new MainPID `2006405`**, `ActiveEnterTimestamp
2026-09-11 07:43:33 UTC`; startup log shows `Finished server process [1992667]` →
`Started server process [2006405]` → `Application startup complete.`

## E5 — post-restart verification (curl on the C2 host itself)

| check | result |
| --- | --- |
| `GET 127.0.0.1:3103/api/v1/agent-loop/health` | **200**, `database.reachable=true`, `name=goaa_c2test`, `user=goaa_c2_app` |
| `POST …/golden/session` with no identity | **401** `{"error":{"code":"missing_clerk_session","message":"a sign-in is required"}}` — **not 404** |
| `GET …/golden/session/verify` with no `Bearer` | **401** `{"error":{"code":"invalid_business_token","message":"a business token is required"}}` |
| `GET …/golden/session` with no identity | **401** `missing_clerk_session` |
| `POST …/golden/session/revoke` with no identity | **401** `not_authenticated` |
| control: `GET …/golden/does-not-exist` | still **404** (so the 401s above are real routes, not a catch-all) |
| `GET 127.0.0.1:13102/api/agent-loop/health` (BFF) | **200**, same body, `name=goaa_c2test` |
| listeners | `127.0.0.1:3103` pid 2006405; `127.0.0.1:13102` pid 2002135 (BFF untouched) |
| `golden/session` 404s logged **after** the restart | **0** (the last 404s in the log are historical, all before the restart line) |

Route count: the deployed `app/main.py` now registers **28** route decorators
(old tree: 24; +4 golden routes = `GET/POST /golden/session`, `GET /golden/session/verify`,
`POST /golden/session/revoke`). The figure 26 in the round brief comes from counting only
`app.get`/`app.post` (22 in the old tree) and adding the 4 golden routes; the full decorator count
includes one `@app.put` and one `@app.delete`, i.e. **24 + 4 = 28**.

## Untouched, verified

- `goaa_c2` (dev): **no** `business_*` tables, `schema_migrations` still `0001_identity …
  0004_role_grant_guard` — nothing was applied there
- C1 production, 3100/3101, the Golden Flow and payment code: not touched, not restarted
- no application repository received a push; the 8 files came from the already-committed candidate
  `dc64591b` and exist unchanged in that worktree

## Notes

- the 3103 service is still `disabled` at boot (unchanged); the tunnel to 13102 and the BFF were
  left running
- `/tmp/c13-mig/0006_golden_business_session.sql` and
  `/tmp/goaa-c2test-pre0006-20260911-074214.sql` remain on the host (and `/tmp/c13-apply.log`),
  left in place as evidence rather than deleted
- this round changes no golden code, so the golden test suite was not re-run
