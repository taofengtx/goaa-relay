# GATE2-ROLLBACK — GOLDEN-05 (:5188) Aika-Box Local Console

- Date: 2026-09-13 (PDT)
- Applies to: `GCR-2026-09-13-AIKABOX-QWENPAW-MVP` (Gate-2 MVP loaded into GOLDEN-05, ADD ONLY).
- Status: **Rollback Ready = YES.** The Golden instance was NOT rolled back to produce this proof.

---

## 1. Restart capability (must-read)

`systemctl restart goaa-local-console.service` is **unavailable to user `aika`**:
polkit answers `interactive authentication is required`. The sudoers drop-in grants only
`systemctl show *`, `journalctl -u *`, `docker ps *`, `docker stats --no-stream *`.

**Official current restart path = supervised MainPID restart**, and `rollback.sh` uses exactly this
mechanism:

1. read `MainPID` (`systemctl show -p MainPID --value`);
2. `kill -TERM <MainPID>`;
3. the unit's own `Restart=always` has systemd relaunch it;
4. poll for a new `MainPID`, then poll `GET /health` until 200.

Constraints honoured: no modification of `sudoers`, `polkit`, or the systemd unit / drop-in.

- Unit file sha256: `dd9572d95116a7dc11abf1fc749689f21a073b8b40113d1192d095ce212f02e1` (unchanged)
- Drop-in `override.conf` sha16: `6fab895d84668204` (unchanged)

**The mechanism is already proven in production:** during the cut-over, `MainPID 6113 → 2412403`
with `NRestarts 0 → 1` and `ActiveState=active`. Therefore:

- RESTORE STEPS = DRY-RUN verified
- RESTART MECHANISM = PROVEN

---

## 2. Bundle

`/home/aika/gate2-rollback/`

| File | sha16 | Bytes | Check |
|---|---|---|---|
| `main.py.pre` | `7f62dfea43d025f6` | 138,956 | equals the Golden frozen fingerprint |
| `main.py.post` | `64fdc422d39a3cb9` | 162,056 | equals the file live on disk |
| `new-files.list` | — | 425 | 10 entries, 0 missing (resolved against the repo root) |
| `rollback.sh` | — | 1,824 | `bash -n` PASS |

---

## 3. What the script does

```
cp -p $BUNDLE/main.py.pre $SRC/main.py
mv qwenpaw_api.py qwenpaw_workers.json integrations tools -> $QUAR/
find $SRC -name __pycache__ -type d -prune -exec rm -rf {} +
kill -TERM $(MainPID)   # supervisor restarts the unit
poll new MainPID; poll GET /health until 200
```

- `$SRC` = `/home/aika/Projects/goaa-ai-main/local-console` — matches the unit's WorkingDirectory.
- `$QUAR` = `/home/aika/gate2-rollback/quarantine-20260913/` — recoverable, nothing is deleted.
- Over-quarantine risk: **none.** At ref `02a17ffe` neither `local-console/integrations` nor
  `local-console/tools` existed (0 files each); the diff `02a17ffe..HEAD` is 10 added, 1 modified.

---

## 4. Proof performed (non-destructive)

| Check | Method | Result |
|---|---|---|
| Bundle complete | `ls -la` | PASS (4 files) |
| pre hash correct | `sha256sum` | PASS `7f62dfea43d025f6` |
| post == live | `sha256sum` | PASS `64fdc422d39a3cb9` |
| new-files.list complete | loop over entries | PASS 10/10, 0 missing |
| script syntax | `bash -n` | PASS |
| restore target paths | compare with unit WorkingDirectory + pre-Gate-2 tree | PASS |
| supervised restart logic | empirical, from the real cut-over | PASS (6113 → 2412403) |
| health wait logic | code inspection; endpoint reachable | PASS |
| dry run | `DRY=1 bash rollback.sh` | PASS — prints before-state (`MainPID=2412403`, `64fdc422d39a3cb9`), changes nothing |

Machine-readable: `evidence/rollback-proof.json`.

---

## 5. Usage

```
DRY=1 bash /home/aika/gate2-rollback/rollback.sh    # inspect
bash /home/aika/gate2-rollback/rollback.sh          # execute
```

After execution the unit should report a new `MainPID`, and `GET /health` should return 200; the
restored source should hash to `7f62dfea43d025f6`.
