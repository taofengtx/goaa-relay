# GATE2-FINAL-PATCH-CANDIDATE — Gate-2 defect fixes (verification candidate)

- Date: 2026-09-13 (PDT)
- Status: **CANDIDATE — verified on :5198 only. NOT applied to GOLDEN-05 (:5188).**
- Predecessor: `GATE2-GOLDEN05-CUTOVER.md` (A–K PASS; Duplicate JS YES; Session History FAIL; Rollback Ready YES)
- Authorization: Tao, 2026-09-13 — fix the two defects on :5198, report back, wait for a separate approval before touching :5188.

---

## 1. Delivery

| Item | Value |
|---|---|
| Dev worktree | `/home/aika/gate2-patch-wt` (branch `gate2-final-patch`, based on `68d6f38`) |
| Code commit | **`a68fd85`** (dev branch only) |
| File changed | `local-console/main.py` |
| Golden on disk | `/home/aika/Projects/goaa-ai-main/local-console/main.py` — sha16 `64fdc422d39a3cb9`, **unchanged** |
| Candidate | sha16 **`0c78b8e83516613a`**, 152,687 bytes, 2,117 lines |
| Verification instance | `:5198` (pid 2423736), cwd = the dev worktree |
| Patches | `patch/fix-a-remove-login-stray-script.diff`, `patch/fix-b-session-history.diff`, `patch/combined-golden-to-candidate.diff` |

The fix was authored in a **separate git worktree**, so the Golden working tree was never edited.
If a later `systemd` restart were to occur, GOLDEN-05 would still load exactly the code it runs today.

---

## 2. Fix A — remove the stray QwenPaw script from the login template

**Diff:** 193 lines removed, nothing added. `patch/fix-a-remove-login-stray-script.diff`

The identical ~10.2 KB QwenPaw script block had been appended to both HTML templates. Only the
login-template copy was removed; the index-template copy is untouched.

**Verification (byte level):** the candidate's `/login` is **byte-identical** to the pre-cutover
(Golden-frozen `7f62dfea43d025f6`) `/login` — 3,560 bytes, identical sha256. The live Golden
`:5188` `/login`, by contrast, carries 2 script tags and a 10,220-byte stray block that throws
`TypeError: Cannot set properties of null (setting 'onchange')`.

Evidence: `evidence/patch-login-comparison.json`, screenshots `shots/patch-login-before-5188.png`
and `shots/patch-login-after.png`.

**Not touched:** login auth logic, cookie, session key, login API, or the index QwenPaw block.

---

## 3. Fix B — restore a session's transcript when the session is selected

**Diff:** net +27 lines — a 26-line function plus three one-line call-site changes.
`patch/fix-b-session-history.diff` (2283 → 2090 after Fix A → 2117 after Fix B).

```js
function loadHistory(){
  var wid=st.worker, sid=st.session;
  if(!wid||!sid) return Promise.resolve();
  if(st.es) return Promise.resolve();          // never clobber a live run
  var box=el('qp-log');
  box.innerHTML='';liveEl=null;st.live='';
  logLine('載入歷史…',false);
  return jget(API+'/sessions/'+encodeURIComponent(sid)+'?worker_id='+encodeURIComponent(wid))
    .then(function(d){
      if(st.session!==sid||st.worker!==wid) return;   // selection changed meanwhile
      box.innerHTML='';liveEl=null;st.live='';
      var msgs=d.messages||[];
      if(!msgs.length){ logLine(d.resumed?'（此 session 尚無文字訊息）':'（此 session 在本機尚無歷史）',false); return; }
      msgs.forEach(function(m){ logLine((m.role==='user'?'我：':'QwenPaw：')+(m.text==null?'':m.text),false); });
    })
    .catch(function(e){ logLine('載入歷史失敗: '+e.message,true); });
}
```

Trigger points: the session selector's `onchange`, and `loadSessions(true)` — used only for the
initial population (from `loadWorkers`). The calls made from `send()` and `newSession()` pass no
flag, so a live transcript is never wiped. A history failure renders one inline error line and
does not affect sending.

Reuses the existing `logLine()`, `jget()` and `esc()`. No DB, no schema change, no QwenPaw upstream
change.

---

## 4. Test matrix (:5198)

| Test | Result | Evidence |
|---|---|---|
| T1 /login has no stray QwenPaw script | PASS | 1 script tag, 0 QwenPaw refs, 0 setInterval |
| T2 /login has no JS error | PASS | only the legacy script; page byte-identical to the Golden legacy page |
| T3 login wiring intact | PASS | `doLogin` ×1, button bound, `POST /login` → 401 |
| T4 index QwenPaw script = 1 | PASS | 1 |
| T5 index qwenpaw nav = 1 | PASS | 1 nav item, 1 page div |
| T6 approval poll timer = 1 | PASS | one `startPoll`/`setInterval`; 7 approval requests in a 10 s window |
| T7 existing session restores history | PASS | auto-rendered on open, and on selector change |
| T8 user/assistant order | PASS | matches the history API order |
| T9 cross-session isolation | PASS | neither transcript contains the other's text |
| T10 new session can Send | PASS | `abx-…-171329-66f668` → `AIKA_PATCH_T10_OK` |
| T11 SSE | PASS | run `71e7ed86f9b1`, 32 SSE events, streamed text deltas |
| T12 approval card | PASS | HIGH · crontab -l · PENDING · ttl 300s · Approve/Reject |
| T13 Approve / Reject | PASS | Reject → run Completed, not executed; Approve → executed, output returned |
| T14 stale card not clickable | PASS | STALE · age 324.1 s · no buttons |
| T15 audit | PASS | 50 rows, all `ui-click`/`tao`, no key-like markers |

Full machine-readable results: `evidence/patch-candidate-test-matrix.json`.

---

## 5. Regression

| Check | Result |
|---|---|
| `aika-core-01` | Online / console |
| `do-cloud-1` | Online / **basic** (not presented as a full console worker) |
| `do-cloud-2`, `do-cloud-3` | Offline |
| GOLDEN-01..04 | untouched |
| GOLDEN-05 on-disk `main.py` | `64fdc422d39a3cb9` — unchanged |
| C1 / C2 | untouched |
| DB | no migration, no writes |
| systemd unit / drop-in | `dd9572d95116a7dc…` / `6fab895d84668204` — unchanged |
| `auth.py` | `9665e8d069bca4c8`, 0 changes |
| canonical Golden manifest | `d7404862d4c93ad1` — unchanged |

---

## 6. Scan

| Check | Result |
|---|---|
| 16 secret patterns | **0** |
| BOM | **False** |
| Routable IPv4 (unmasked) | 2 occurrences — **both pre-existing** in the Golden baseline source (present at `02a17ffe`, at HEAD and in the Golden on-disk file); the candidate's count is identical (2), so the patch adds none |

---

## 7. Rollback impact of applying this patch

Applying the candidate to GOLDEN-05 would change only `local-console/main.py`
(`64fdc422d39a3cb9` → `0c78b8e83516613a`). The existing rollback bundle
(`/home/aika/gate2-rollback/`) restores `main.py.pre` (`7f62dfea43d025f6`) and quarantines the
Gate-2 additions; it remains valid. An additional pre-patch copy of `64fdc422d39a3cb9` would be
taken before any application.

Restart path remains the supervised MainPID restart of `GATE2-GOLDEN05-CUTOVER.md` §1
(`systemctl restart` is unavailable to `aika`).

---

## 8. Not done (by instruction)

- :5188 / GOLDEN-05 was **not** modified.
- The P0 session-key entropy debt is **recorded only** — no auth, cookie, env or exposure change.
- `/rag/stats` remains PRE-EXISTING / NOT REGRESSION — not fixed.
- No GOAA mainline work was started.

**Awaiting Tao's approval before applying anything to GOLDEN-05.**
