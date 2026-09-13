# GATE2-GOLDEN05-CUTOVER — Aika-Box Local Console (:5188)

- Date: 2026-09-13 (PDT)
- Scope: load the Gate-2 MVP (QwenPaw AI Workspace) into GOLDEN-05 = D0 Aika-Box Local Console (`:5188`), ADD ONLY.
- Authorization: Tao, 2026-09-13 15:56 PDT (explicit). Scope limited to the D0 Aika-Box local console.
- Result of this round: **verification NOT closed.** Two defects were confirmed and require a decision before a Final PASS can be issued (see §7).

> Environment naming: D0 = Aika-Box / Local Development; C1 = Live / Production; C2 = Test / Staging.

---

## 1. Restart mechanism (accepted by Tao)

`systemctl restart goaa-local-console.service` is **UNAVAILABLE to user `aika`**
(polkit returns `interactive authentication is required`; the sudoers drop-in grants only
`systemctl show *`, `journalctl -u *`, `docker ps *`, `docker stats --no-stream *`).

**Official current restart path = supervised MainPID restart:**

1. read the unit's `MainPID` (`systemctl show -p MainPID --value`);
2. `kill -TERM <MainPID>`;
3. the unit's own `Restart=always` has systemd relaunch it; wait for a new `MainPID` and `GET /health` = 200.

This is still "a controlled restart of that unit": systemd records `NRestarts + 1`, the unit file and
drop-in are untouched, and no interactive authorization is needed.

- `sudoers` / `polkit` / systemd unit: **NOT modified.**
- Unit file sha256: `dd9572d95116a7dc11abf1fc749689f21a073b8b40113d1192d095ce212f02e1` (unchanged)
- Drop-in `override.conf` sha16: `6fab895d84668204` (unchanged)

Proof this mechanism already works: during this cut-over, `MainPID 6113 → 2412403`, `NRestarts 0 → 1`,
`ActiveState=active` (2026-09-13 15:58:50 TERM → 15:58:56 back up).

---

## 2. Before / after

| Item | Before | After |
|---|---|---|
| Unit | `goaa-local-console.service` | unchanged |
| MainPID | `6113` | `2412403` |
| NRestarts | `0` | `1` |
| ActiveState | active/running | active/running |
| WorkingDirectory | `/home/aika/Projects/goaa-ai-main/local-console` | unchanged |
| ExecStart | `/opt/goaa/venv/bin/uvicorn main:app --host 127.0.0.1 --port 5188` | unchanged |
| Restart / RestartSec | `always` / `5` | unchanged |
| EnvironmentFiles | `console.env` | unchanged |
| User | `aika` | unchanged |
| `main.py` sha16 | `7f62dfea43d025f6` (== Golden frozen) | `64fdc422d39a3cb9` |
| `main.py` bytes | 138,956 | 162,056 |
| Unit file sha256 | `dd9572d95116a7dc…` | unchanged |
| Drop-in sha16 | `6fab895d84668204` | unchanged |

DB migration: **none.** Proxy change: **none.** systemd config change: **none.**
GOLDEN-01/02/03/04: **UNCHANGED.** C1 / C2: **NO CHANGE.**
Code delta: ADD ONLY (10 added files + `main.py` additive insertions; see `evidence/code-inventory.json`).

---

## 3. §5 acceptance

| Step | Result | Evidence |
|---|---|---|
| A health | PASS | `GET /health` 200 on `:5188` |
| B legacy functions | PASS (one pre-existing defect, see §6) | `/settings/models`, `/settings/skills`, `/settings/agents`, `/tasks/results`, `/node/health`, `/logs/recent`, `/session` all 200 with byte counts identical before/after; all 11 nav pages render; 0 console errors; `POST /login` 401 for bad credentials |
| C AI workspace appears | PASS | nav `qwenpaw` present; `#p-qwenpaw` renders |
| D worker roster correct | PASS | `aika-core-01` Online (console, v1.1.5.post1); `do-cloud-1` Online (**basic**) — not presentable as a full console worker; `do-cloud-2/3` Offline |
| E new session | PASS | `abx-20260913-160614-630ef5` created from the UI |
| F send message | PASS | `Reply exactly: AIKA_GOLDEN05_OK` streamed, Completed, returned `AIKA_GOLDEN05_OK` |
| G approval card | PASS | `HIGH · execute_shell_command · crontab -l · PENDING · ttl 300s · findings 1`, Approve + Reject buttons present |
| H Reject (human click) | PASS | audit `16:07:21 reject · tao · ui-click · ok`; command not executed; run Completed |
| I Approve (human click) | PASS | audit `16:09:14 approve · tao · ui-click · ok`; command executed in a fresh session; raw history shows `$ crontab -l` → `no crontab for aika` (exit 1); result returned to the run |
| J audit | PASS | 8 decisions, all `source=ui-click`, all success (`evidence/golden05-cutover-acceptance.json`) |
| K stale approval not clickable | PASS | seed `abx-20260913-161008-49cf0a`: age 281.4s → `PENDING/clickable=true`; age 328.5s → `STALE/clickable=false`; UI renders `STALE · age 340.3s / ttl 300s` with `button_count = 0` (`evidence/k-stale-expiry-ui.json`) |

Human-in-the-loop note: H and I were performed by a **real person clicking the actual
Approve/Reject buttons** in the browser; the decision rows are recorded with `source=ui-click`,
`actor=tao`. No agent-side submission was used.

Negative control note: an attempted smuggle (`crontab -l ; touch <marker>`) was **refused by the
QwenPaw agent itself**, which stated it would not bypass the security boundary; no approval card
was produced for it. No automatic decision was ever observed (the K seed stayed `PENDING` for its
whole lifetime).

---

## 4. Session history UI

The adapter endpoint `GET /api/qwenpaw/sessions/{sid}?worker_id=…` works and returns merged
history. **The UI never calls it**: switching the session selector only updates the header and
re-polls approvals, so the transcript panel keeps its placeholder text. Classification: **B — real
UI gap**, not a test-method artifact.

Minimal fix (not applied): a ~10-line `loadHistory()` in the QwenPaw UI block, called from the
session `onchange` handler and after `loadSessions()`. See
`evidence/session-history-ui-diagnosis.json`.

---

## 5. JavaScript duplication

**Within the Golden landing page:** no duplicate — 2 script tags, 1 QwenPaw nav item, 1 QwenPaw
page div, 1 set of handlers, 1 polling timer.

**In the source:** the identical ~10.2 KB QwenPaw script block appears **twice** in
`local-console/main.py`:

- lines `168-360` — appended to the **login** template
- lines `2090-2282` — appended to the **index** template

On `/login` the stray block throws at load:
`TypeError: Cannot set properties of null (setting 'onchange')`. Login remains functional
(`doLogin` is bound by the preceding script; `POST /login` returns 401 for bad credentials), but
the page carries dead code and a console error.

Cause: the original insertion anchored on a string present in both HTML templates, and the edit
operation replaced every occurrence.

Minimal fix (not applied): delete lines `168-360`. Low risk — the index page keeps its own copy.
See `evidence/js-duplication-diagnosis.json`.

---

## 6. `/rag/stats`

Classification: **PRE-EXISTING / NOT A REGRESSION.**

`/rag/stats` hangs past the client timeout. Control run: the **pre-cutover** source
(`main.py.pre`, sha16 `7f62dfea43d025f6`) was started on a temporary instance at `:5197` and
exhibited the same timeout. The route resolves a Postgres connection to C1 (`POSTGRES_HOST` from
`console.env`), which is unreachable from D0. Identical before and after the cut-over.
Not fixed in this round; tracked as a separate technical-debt item.

---

## 7. P0 security debt — session signing key entropy

- `CONSOLE_SESSION_KEY`: present in `console.env`; **length 4**; sha256[0:16] `bedc725da6f59c82`.
- Impact: the console session cookie is an HMAC over this key; 4 characters of entropy is
  insufficient and permits **session forgery**.
- Status: **RECORDED, NOT CHANGED.** No change was made to auth, cookie behaviour, the env secret,
  sudoers, or public exposure.
- Required: rotate before any broader/public access. This is a new Golden/Auth change and needs a
  separate Tao approval.

Observation recorded for completeness: a cookie issued earlier in the day validates against `:5198`
but not against `:5188`, so a fresh cookie was issued for this acceptance run. `console.env` was not
modified (mtime unchanged).

---

## 8. Rollback

Bundle: `/home/aika/gate2-rollback/` (`main.py.pre`, `main.py.post`, `new-files.list`, `rollback.sh`).

```
bash /home/aika/gate2-rollback/rollback.sh          # execute
DRY=1 bash /home/aika/gate2-rollback/rollback.sh    # print only
```

`rollback.sh` restores `main.py.pre`, quarantines the Gate-2 additions into
`quarantine-20260913/`, and restarts via the supervised MainPID mechanism of §1.
**Rollback Ready = YES** — see `GATE2-ROLLBACK.md` and `evidence/rollback-proof.json`.
The Golden instance was **not** rolled back to obtain this proof.

---

## 9. Process inventory (at time of writing)

| Process | PID | Notes |
|---|---|---|
| `:5188` Golden console | `2412403` | `goaa-local-console.service`, post-cut-over |
| `:5198` verification console | `2371500` | retained pending decision |
| tunnel `do-cloud-1` | `2314785` | `127.0.0.1:18088` — official worker channel |
| tunnel `do-cloud-2` | `2372459` | `127.0.0.1:18089` — remote has no listener |
| tunnel `do-cloud-3` | `2372462` | `127.0.0.1:18090` — remote has no listener |

---

## 10. Verdict of this round

A–K: all PASS. Duplicate JS: **YES** (source / login template). Session history UI: **FAIL (real
gap)**. Rollback Ready: **YES**.

Per the Final Gate, `GOLDEN-05 CUT-OVER` and `GATE-2 FINAL` are **NOT PASS** until the two defects
above are either fixed through the `:5198 → test → Tao approval → :5188 patch` path, or explicitly
accepted by Tao as known limitations.
