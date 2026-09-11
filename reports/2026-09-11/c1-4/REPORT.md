# Round C1.4 — R (new-account signup redirect fix) + K (leaked-key redaction)

**Date:** 2026-09-11
**Scope:** C2 only (frontend candidate `31f7676`, deploy dir `/opt/goaa-test/ui-clerk-20260910`,
`goaa_c2test`) and `aika-core-01`. C1 production was **not** restarted or modified.
**Deploy dir backup:** `ui-clerk-20260910.bak-20260911-024044`

---

## R1 — patch 0007 (Claude Code, segment A)

| Item | Expected | Actual |
|---|---|---|
| Patch sha256 | `ee9180cca6ad76326178e45c8ba564e065b01fe00645ec98a627df0943053ccb` | **match** |
| Diff shape | 2 props added, `app/client-login/page.tsx` untouched | match (2 files, +30; new `scripts/test-clerk-signup-redirect.cjs`) |
| Pre-patch FE HEAD | `d4ad5613ce03914fa4a4c8de741942bff153a7f8` | match |
| Post-patch FE HEAD | — | **`31f7676b5006b602ec24a43d5171a44933c41da6`** |
| `npx tsc --noEmit` | 0 errors | **0 errors** |
| `scripts/test-*.cjs` | 28 files, all green | **28 files, 28 pass / 0 fail** |
| `scripts/c2-clerk/run-all.sh` | `99/99` | **`TOTAL: 99 passed, 0 failed, group_rc=0`** |
| Snapshot | `snapshots/frontend-<short>` | **`snapshots/frontend-31f7676b`, 633 files** |
| Relay push | — | **`81d0c08`** (then `0c2213d` filed the patch under `patches/`) |

The change adds only `signUpForceRedirectUrl={next}` and `signUpFallbackRedirectUrl={next}`
to the existing `<SignIn withSignUp>` card. `forceRedirectUrl` / `fallbackRedirectUrl`
(which govern only the sign-in branch) are unchanged, as are the middleware marker check,
the switch check and the `next` validation.

## R2 — build and deploy (Aika)

| Item | Expected | Actual |
|---|---|---|
| `next build --no-lint` | rc=0 | **rc=0** |
| Clerk vars in build shell | 0 | **0** (count only) |
| Prerendered routes `/`, `/planning`, `/client-login` | none | **none** (0006 dynamic behaviour preserved) |
| Artifact tar sha256 | — | `60f23296e1c78344eb0463366633a5c855f33f9f9783bcd25f1bb8d25f47bb78` |
| C2-side tar sha256 | must match | **match** |
| On-host manifest re-verify | 0 mismatches | **0** (1968 files) |
| Deployed env file | untouched | untouched (`root:goaa-c2loop 440`, 10 lines) |
| Unit restart | rc=0 | **rc=0**, no approval card appeared on Aika's side |
| New MainPID | — | **`2012347`** |
| BFF health | 200, `goaa_c2test` | **200, reachable=true, name=goaa_c2test** |

> Restart note: the `systemctl restart goaa-c2-clerk-ui-3102.service` command was submitted
> directly (not wrapped in a script, not replaced by `kill`). On Aika's side **no approval
> card was raised**. Whether it went through an approval on Tao's side is Tao's record to state.

Server-side check of the new props (plain HTTP):
`GET /client-login?next=%2Fagent-loop%2Fcustomer` -> 200, and the served payload contains
`signUpForceRedirectUrl` and `signUpFallbackRedirectUrl` (2 occurrences each). Font 200
`font/woff2` 32292 B; `/planning` 200.

## R3 — browser verification

**Fix verified: a first-time signup now lands on the validated `next`, not `/`.**

The two Clerk branches are distinguishable in the card URL hash:
signup = `#/create/verify-email-address` ("Verify your email"), signin = `#/factor-one` ("Check your email").

| Step | Expected | Actual |
|---|---|---|
| New account signup via `/client-login?next=%2Fagent-loop%2Fcustomer` | signup branch | `#/create/verify-email-address` OK |
| OTP (test mode `424242`) | accepted | accepted |
| **Landing URL** | `/agent-loop/customer`, **not** `/` | **`http://localhost:13102/agent-loop/customer`** OK |
| Business session on landing | minted | `POST /api/agent-loop/golden/session` -> 200; `client_token` set (32 hex) OK |
| Existing account (`c2e2e`) sign-in, same `next` | same landing | **`/agent-loop/customer`** OK (`Switch to Agent Portal` visible) |
| Logout, both accounts | tokens revoked | `c2e2e2b` -> `/client-login?next=...`, token cleared, Clerk signed out; `c2e2e` -> LOG OUT clicked |
| DB after both logouts | 0 live tokens | `f99342a6` (c2e2e2b) **1 total / 0 live**; `4717531f` (c2e2e) **4 total / 0 live** OK |
| Re-open `/agent-loop/customer` signed out | -> login | `-> /client-login?next=%2Fagent-loop%2Fcustomer`, `clerkUser=null` OK |

Screenshot: `r3-newuser-landing.jpg` (91640 B, 1440x813) - new account's landing page.

### Deviations and findings (reported, not hidden)

1. **Account name deviates.** The first attempt used exactly `c2e2e2+clerk_test@example.com`
   but it ran during the environment fault described in finding 2, so its signup consumed the
   account before the landing could be observed cleanly. The clean run therefore used a fresh
   account `c2e2e2b+clerk_test@example.com`. `goaa_c2test` had **no** rows for `c2e2e2`
   (`users`, `user_identities`, `identity_events` all 0), so nothing was orphaned.
   Re-running with exactly `c2e2e2` would require deleting that Clerk test user first
   (a destructive operation on the identity provider, not performed).
2. **`CLERK_AUTHORIZED_PARTIES` has a stale entry - NOT caused by this patch, NOT modified.**
   `/opt/goaa-test/env/clerk-api-3103.env`:
   `CLERK_AUTHORIZED_PARTIES=http://localhost:13102,http://127.0.0.1:3102`
   The second entry still carries the **old port 3102**, while the C2 topology was moved to
   port 13102. Consequence: browsing over `127.0.0.1:13102` makes the Clerk token's `azp`
   fail the allow-list, the backend answers **401 `invalid_clerk_session`**, no business
   session can be minted, and `/agent-loop/customer` -> 307 -> `/agent-loop/login` ->
   `/client-login` loops. Browsing over **`localhost:13102`** (the first entry) works
   completely. This is why T3 earlier passed: it browsed `localhost:13102`.
   Suggested one-line fix (awaiting Tao): set the second entry to `http://127.0.0.1:13102`.
3. **Existing-account landing mints the business token on page load, not on the redirect.**
   For `c2e2e` (sign-in branch) the landing page rendered at `/agent-loop/customer` with no
   `client_token` immediately after the redirect; a page load minted it
   (`4717531f` -> 4 total / 1 live). The new-account signup path minted during the landing
   itself. Recorded as an observation; no assertion is made about whether it is intended.

---

## K — leaked key redaction (`aika-core-01`)

Trigger: Tao confirmed the key had been **rotated**. Rotation itself is Tao's action,
outside this round; only the local residue was handled.

### K1 — in-place, same-length overwrite
`/home/aika/.qwenpaw/qwenpaw.log` line **41380** held one match of the live-key pattern
(50 bytes). It was overwritten in place with 50 `X` bytes via `python3` `open(...,"r+b")`
+ `seek` + `write`, including the key prefix. No `sed -i`, no whole-file rewrite,
no line removed, no truncation, no new file (the live logger keeps writing to the same inode).

### K2 — verification
| Value | Result |
|---|---|
| inode before / after | `32276497` / `32276497` - **identical** |
| size before / after | `6034761` / `6034761` - **identical** |
| `grep -cE` (live-key pattern) on qwenpaw.log | **0** |

### K3 — follow-up scan (paths and hit counts only; no contents printed)
| Scope | Result |
|---|---|
| `/home/aika/.qwenpaw/qwenpaw.log.*` and `*.gz` | no such files exist (nothing to scan) |
| binary-inclusive rescan of `/home/aika/.qwenpaw` (`grep -a`, no `-I`) | **`workspaces/default/dialog/2026-09-11.jsonl` - 1 line** |
| `~/.claude` | 0 |
| `/tmp/claude-*.log` (5 files) | all 0 |

**Not handled, per K3 instruction:** the `dialog/2026-09-11.jsonl` hit is left untouched and
listed above for Tao's decision. It is the conversation record, i.e. the message in which the
key was pasted; it is not a log the agent writes to on its own.

---

*No key value, token value, session secret or connection string appears in this report.*
