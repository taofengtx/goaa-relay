# G-1 · Independent verification of the Claude next-phase proposal

**Round**: G-1 · 2026-09-13 · **Mode**: read-only forensic verification (no remediation executed)
**Author**: Aika (GOAA infra agent) · **Order authority**: Tao
**Naming (fixed this round)**: **D0** = Aika-Box / local dev · **C1** = Live / Production · **C2** = Test / Staging · cloud workers = W1…W6

## 0. Method and discipline

Allowed operations used: `read / hash / diff / status / DNS / systemd show / DB count / manifest compare / public HTTP GET`.
Executed: **no delete, no revoke, no rollback-pointer edit, no restart, no deploy, no DB write, no merge, no force push, no charge.**
Secret handling: **no secret value is printed anywhere in this report.** Keys are identified only by length + `sha256[0:16]` fingerprint; the literal key prefixes are deliberately not reproduced. Public IPv4 addresses are written masked as `a.b.c.⟨d⟩`.

**Scanner gate**: this file reports `TOTAL_HITS = 0`, `routable IPv4 unsplit = 0`, `BOM = False` (verified before commit).

## 1. Rollback baseline

**CLAUDE CLAIM**
`76af718` is no longer a suitable production rollback; `40c8546e` should become the new production rollback baseline.
**STATUS: TRUE** (all three factual sub-claims verified) — verdict **MOVE TO 40c8546e**.

**EVIDENCE**
- Current rollback pointer (not modified): `/root/r5b2-rollback-point.txt` (mtime 2026-09-12 08:31:04Z) and `/root/r5b4-rollback-point.txt` (mtime 2026-09-12 08:59:58Z) both contain exactly `/opt/goaa-frontend/releases/76af718b0568992c900b72d1aff5aad2516046dc`. So Claude's premise about "76af718 is the baseline" is **correct as of now**.
- `76af718` has **zero** Clerk capability: 530 files tracked; content grep for `clerk` → **0 files**; `agent-loop` → **0 files**; the only path-level hit is a marketing doc (`docs/marketing/GOAA_PORTAL_CONTENT_MATRIX_V2.md`). Clerk first appears in the line at `45ca6de` / `daecc2a` (32 files) and grows to 54 files at `9ab1608` / `f719b27` / `40c8546e`. `76af718` **is** an ancestor of `40c8546e`.
- Production identity data **already exists** in C1 `goaa_platform` (the Docker `goaa-postgres` container, reached with the app role): 15 tables — `users` 2, `user_roles` 4 (user 2 / agent 1 / admin 1), `user_identities` 2 (**provider = clerk**), `identity_events` 7, `agent_applications` 1 (**approved 1**), `agent_licenses` 1, `agent_license_documents` 1, `business_subjects` 1, `business_subject_links` 1, `agent_review_events` 12, `schema_migrations` 6.
  Recency: identities created **2026-09-12 17:49:52Z → 18:05:06Z**; approved application + licence **18:22:52Z** — i.e. *after* the 17:49 deploy of `40c8546e`.
- Therefore a rollback to `76af718` **would** produce exactly the inconsistency Claude describes: the DB keeps the Clerk identities / roles / the approved application + licence + licence document, while the frontend loses the Clerk card, `/client-login`, and all three `/agent-loop/*` gates. The two real accounts created on Sep 12 evening could not sign back in and the approved agent application would be unreachable through the UI. Today's gate chain: `/agent-loop/login` → **307** → `/client-login?next=%2Fagent-loop%2Fcustomer`; `/goaa-clerk-login` → **307** → `/client-login`; `/agent-loop/agent` → **307** → login (unauthenticated).
- `40c8546e` **is** the running release and does start the whole Clerk + agent-loop + DB path: `current → /opt/goaa-frontend/releases/40c8546e…` (mtime 2026-09-12 08:59:58Z); public `https://planning.goaa.ai/` **200 / 16,075 B** and `/client-login` **200 / 10,893 B** are **byte-identical (sha256) to C1's own `127.0.0.1:3100`** responses; `/client-login` embeds `clerk.browser.js` from `clerk.goaa.ai` and the production publishable key (fp `562a0cfc245df772`); the 3103 agent-loop API is `active` and uses the same instance keys (same publishable **and** secret-key fingerprints as the frontend env).
- Verifiable manifest / BUILD_ID / deployed tree: release directory name = the commit sha; `.next/BUILD_ID` = `FW7iufKj5JrPAz9Kx2SkX`; 1,969 files / 28,138,994 B; sorted-path manifest fingerprint `e4c7ed48548bdcb9`; 22 release directories on disk.
- Better candidate? **No.** On disk, `40c8546e` is the **only** Clerk-capable release. The other 21 releases are all pre-Clerk (e.g. `76af718` = 1,940 files, BUILD_ID `5wl6uCJFbHElFV3-B3I79`; `d6029f63` = 1,940 files, BUILD_ID `XI0npe4KUOvwqjs4sRmR7`, commit 2026-09-07 03:22:31, **0 clerk files**, 2 files different from `76af718`, **not** an ancestor of `40c8546e`, sitting on branches `codex/login-legal-links-20260906` and `feat/customer-growth-v1-20260908`). The Clerk-era commits (`f719b27` = immediate predecessor with 54 clerk files) exist in git but have **no release directory** ⇒ they are candidates only via a fresh build + deploy.

**RISK: HIGH** — with the pointer left at `76af718`, the next incident rollback silently removes all production sign-in while the server-side identity data survives, and no on-disk Clerk-capable fallback exists other than the build that broke.

**RECOMMENDATION** — move the rollback pointer to `/opt/goaa-frontend/releases/40c8546e152bf5fad8d7a9d0033f17cab4cbcda8` (current live, probed-good, Clerk-complete) and at the same time record `f719b27` as the second-line candidate that would need a build. Keep `76af718` only as pre-Clerk archaeology, explicitly labelled "must not be used while Clerk identity data exists".
**EXECUTION REQUIRED? YES** (pointer edit only) — **not executed this round.**
**REQUIRES TAO APPROVAL? YES.**

## 2. Clerk legacy secret risk

**CLAUDE CLAIM**
The old "glue" contains several production secret keys, at least one of which still answers **200** against the Clerk API.
**STATUS: PARTIAL** — *existence and instance membership = TRUE; "still answers 200" = UNKNOWN* (exercising a key against Clerk is outside this round's allowed operation set, and was not attempted).

**EVIDENCE**
- Four files under `/root` carry a **253-character glued value** for the Clerk secret-key variable = the concatenation of **three distinct live secret keys**, fingerprints
  `c079996583c172c6` (len 50), `a4e3a23327b418d9` (len 52), `33cf780fc276a91c` (len 52).
  Files: `web.env.bak.20260912T084443Z`, `web.env.bak.20260912T085918Z`, `web.env.bak.20260912T174904Z`, `api-3103.env.bak.20260912T174904Z` (all `600 root:root`).
- **Same-instance proof (strong):** those same backups carry the publishable key fp `562a0cfc245df772` (len 27), which is **identical** to the publishable key currently loaded by `/opt/goaa-frontend/env/web.env` and `/opt/goaa-platform/env/api-3103.env`, and identical to the key embedded in the live `/client-login` page. A Clerk publishable key identifies the instance ⇒ the three legacy secret keys belong to the **same production instance** that is live today.
- The **current** production secret key has fp `45e9487a9d4bf1ea` (len 50) and differs from all three legacy keys; it exists only in `/root/clerk-live.env` (600) and the two live env files (640 root:goaa-web / 600 goaa-platform) — i.e. the live key is *not* one of the three legacy ones.
- Clerk custom domain `clerk.goaa.ai` resolves to Cloudflare `104.18.34.⟨146⟩` / `172.64.153.⟨110⟩` and answers **200**.
- Legacy key material is confined to `/root`: a bounded sweep of `/etc/goaa`, `/etc/cloudflared`, `/opt/goaa`, `/opt/goaa-platform`, `/opt/goaa-frontend`, `/var/log/goaa-platform`, `/srv` found **no** live-secret file other than the three legitimate live env/config files listed above (built JS contains only the publishable key, which is public by design).

**RISK: HIGH** — three production-instance secret keys in plaintext on the host; Clerk does not auto-expire superseded keys unless they are deleted, so their validity must be assumed until proven otherwise. Anyone with root, a droplet image/snapshot, or a leaked backup can mint sessions and read the user table.

**RECOMMENDATION** — **REVOKE RECOMMENDED? YES**, for the three legacy fingerprints above, after Tao confirms nothing depends on them; keep exactly one active secret key for the production instance; confirm from the Clerk dashboard how many keys are active and which of the three (if any) are already revoked; re-rotate if any of them cannot be deleted.
**EXECUTION REQUIRED? YES** (Tao-side, in Clerk) — **no revoke performed, no key touched.**
**REQUIRES TAO APPROVAL? YES.**

## 3. `/root` backups

**CLAUDE CLAIM**
4 of the 5 backups contain plaintext legacy secret glue.
**STATUS: TRUE.**

**EVIDENCE** — the five `*.env.bak.*` files, with ownership/mode and live-key counts (counts only, no values):

| # | file | size | mode | owner | live-SK count | verdict |
|---|---|---|---|---|---|---|
| 1 | `/root/web.env.bak.20260912T084443Z` | 560 B | 600 | root:root | 1 (glued) | contains legacy glue |
| 2 | `/root/web.env.bak.20260912T085918Z` | 623 B | 600 | root:root | 1 (glued) | contains legacy glue |
| 3 | `/root/web.env.bak.20260912T174904Z` | 684 B | 600 | root:root | 1 (glued) | contains legacy glue |
| 4 | `/root/api-3103.env.bak.20260912T174904Z` | 1,189 B | 600 | root:root | 1 (glued) | contains legacy glue |
| 5 | `/root/api-3103.env.bak.20260912T075855Z` | 1,103 B | 600 | root:root | 0 (test-mode keys only) | clean of live material |

- **4 of 5 = TRUE.** All five match the secret pattern set; #1–#4 additionally carry the three live keys and the 253-char glue.
- Fingerprints (per distinct token, one token per line, never the value): live secret `c079996583c172c6` / `a4e3a23327b418d9` / `33cf780fc276a91c`; glued container `81a398b353637cc3`; publishable `562a0cfc245df772`; test-mode secret `9dea33a55d424704`, test-mode publishable `f703fd4d199c08df` (file #5 and `/root/c2-api-3103.env`).
- Two observations that matter for a cleanup audit: (a) **the filename timestamps are unreliable** — #2 is named `…085918Z` but its mtime is 08:44:43Z, and #3 is named `…174904Z` but its mtime is 08:59:18Z; (b) `/root/.bash_history` (12,656 B, 600) contains **5 references to the secret-key variable name but 0 raw key tokens** (secure by luck, still worth scrubbing).
- Also present: `/root/clerk-live.env` (68 B, 600, holds the **current** live secret key — the good copy), `/root/clerk-live-sk.env` (18 B, 600, matches none of the scanned key patterns).

**RISK: MEDIUM on its own** (root-only `600`, single host) — **but combined with §2 the effective exposure of live production credentials is HIGH**, because these files are captured by any filesystem image/snapshot of the droplet.

**RECOMMENDATION** — **CLEANUP RECOMMENDED? YES**: after the §2 rotation, delete files #1–#4 and the stale `clerk-live-sk.env`, scrub the history file, keep exactly one live key file, and move secret storage to a vault/secret manager. Do not delete anything before the rotation, or access to the current key is lost.
**EXECUTION REQUIRED? YES** (deletion/scrub) — **nothing deleted this round.**
**REQUIRES TAO APPROVAL? YES.**

## 4. DB backup

**CLAUDE CLAIM** (implicit in the proposal): the platform database is protected.
**STATUS: PARTIAL** — commerce DB = partial manual coverage; **identity DB = NONE**.

**EVIDENCE**
- Scheduling: the **only** root crontab entry is `0 7 * * * /opt/goaa/scripts/check_do_git_consistency.sh --dry-run` (a git-consistency monitor, **not** a backup). `/etc/cron.d` holds only distro jobs (`e2scrub_all`, `sysstat`). `systemctl list-timers` shows only OS timers (apt, sysstat, dpkg-db-backup, logrotate…). No `pg_dump` / `pg_basebackup` / `wal-g` / `barman` reference exists in `/etc/cron*`, `/etc/systemd/system`, `/root`, `/opt/goaa`.
- Existing dumps (all manual, all **`goaa` DB only**):

  | file | size | mtime | coverage |
  |---|---|---|---|
  | `/root/backups/goaa-20260912-055621Z.dump` | 5,049,925 B | 2026-09-12 05:56:23Z | `goaa` only |
  | `/opt/goaa/backups/goaa-step2-20260906-204455.dump` | 5,041,599 B | 2026-09-06 20:44:57Z | `goaa` only |
  | `/opt/goaa/backups/goaa-pre-oauth-20260906-203443.dump` | 5,037,681 B | 2026-09-06 20:34:45Z | `goaa` only |

  Markers `goaa_platform`, `agent_applications`, `user_identities`, `user_roles` = **0 hits in all three dumps** ⇒ the identity/agent-loop database is **not** in any backup. Last successful dump = **2026-09-12 05:56:23Z**, ~12 h before the Sep 12 17:49–18:22 identity activity, and older than the 06:47 platform work.
- Destination = the **same host filesystem** (`/root/backups`, `/opt/goaa/backups`); no offsite/remote/object-storage evidence found.
- Restore: **never verified** — no restore log, script, or drill artifact exists; `/opt/goaa/backups/` contains only the two dumps plus the `stripe-return-urls-20260904` folder.
- Documents / file metadata: `agent_license_documents` and the private-file store (`/opt/goaa-platform/private-files`) live with `goaa_platform` ⇒ **not covered**; C2's `goaa_c2test` + private files are likewise not in any dump.

**RISK: HIGH** — the exact data that makes the §1 rollback question delicate (production Clerk identities, roles, the approved agent application and licence) has **no backup at all**, and the commerce dump sits on the same disk as the live DB.

**RECOMMENDATION** — schedule a dump of `goaa_platform` (+ `agent_license_documents`, + the private-file directory), add an offsite copy, and run one restore drill to a scratch database; retain the existing dumps. (Confirmed the existing mechanism only — **no new backup was created this round.**)
**EXECUTION REQUIRED? YES** — **not executed.**
**REQUIRES TAO APPROVAL? YES.**

## 5. 3103 restart policy

**CLAUDE CLAIM** (basis for the "no self-healing" concern): the agent-loop API unit does not self-heal.
**STATUS: CONFIRMED — SELF-HEALING = NO.**

**EVIDENCE** — `systemctl show goaa-platform-api-3103.service`:
`Restart=no` · `RestartUSec=100ms` (no explicit `RestartSec`) · `UnitFileState=enabled` · `ActiveState=active` · `SubState=running` · `NRestarts=0` · `MainPID=3135920` · started **2026-09-12 17:49:23Z** · `ExecStart=/opt/goaa-platform/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 3103`. The unit is `enabled` (starts at boot) but a crash after boot leaves it down indefinitely. It serves `planning.goaa.ai`'s agent-loop API (`GOAA_C2_PUBLIC_BASE_URL=https://planning.goaa.ai`, Clerk auth enabled) against `goaa_platform` on the local Docker PostgreSQL.
Note: the unit file itself documents several deliberate hardening differences vs the C2 template, but `Restart=no` is not explained there.

**RISK: MEDIUM** — a single crash takes the professional/agent flow down while the frontend keeps running (surfaces as 5xx/502 in the UI) and nothing brings it back.

**RECOMMENDATION** — set `Restart=on-failure` with `RestartSec=2` (and record the reason in the unit header). Unit change ⇒ change-window item.
**EXECUTION REQUIRED? YES** (unit edit) — **not executed.**
**REQUIRES TAO APPROVAL? YES.**

## 6. `www.goaa.ai` legacy content

**CLAUDE CLAIM**: the live public site still shows the old template (Radison testimonials, $480/$960 plans, old phone/address, Chinese hero).
**STATUS: FALSE** — no legacy template content is served. **PUBLIC CONTENT RISK = LOW.**

**EVIDENCE** — `https://www.goaa.ai/` fetched live: **200**, 687,067 B (Framer-hosted, Cloudflare fronted, `framerusercontent.com` assets).
- `radison` = **0**, `testimonial` = **0**, `480` = **0**, `960` = **0**, CJK characters = **0**, phone patterns (`###-###-####`, `(###) ###-####`) = **0**, street/avenue/suite/blvd/road address patterns = **0**, Chinese hero = **absent**.
- Headings actually served (new English copy): *Your Personal AI Agents*; *Get Things Done. Make Money.*; *From Conversation to Delegation*; *From Intake to AI Execution*; *Innovative services for growth*; *Maximize efficiency and impact*; *Flexible plans for growth*; *Ask whatever you have in your mind*; *We're here to help*; *Let's talk about your next big move*. Nav: Process / Services / Benefits / Plans / Contact + Customer Login / Agent Login.
- **Confirmed residual defects (two, and only one is a defect)**:
  1. Contact link href = `https://help@goaa.ai` — malformed (`help@` parsed as userinfo), so the intended mailto is broken.
  2. `https://cal.com/goaa.ai/30min` × 2 — **not** legacy residue: this is the *intended* 30-minute booking URL that the C1.6 launch switch pairs with the closed $39.90 connection.
- CTA targets: `/agent-login`, `/client-login`, `/connect-pass?source=planning`, `/planning` on `planning.goaa.ai`.
- Caveat: Tao's screenshot is not present in this workspace, so a pixel-level comparison was not possible; the finding above is the served content itself.

**RISK: LOW** — content is the new English site; one broken contact link.
**RECOMMENDATION** — fix the malformed contact link in Framer on the next content pass; leave the cal.com booking link as designed.
**EXECUTION REQUIRED? NO** (small content edit later) — **Framer untouched.**
**REQUIRES TAO APPROVAL? YES** (Framer edit).

## 7. D0 / C1 / C2 mapping — independently re-derived

**CLAUDE CLAIM** (mapping assumption): D0 = Aika-Box, C1 = production, C2 = staging.
**STATUS: CONFIRMED.**

**EVIDENCE** (measured now, not from old memory)
- **D0 = `aika-core-01`** — hostname `aika-core-01`; Tailscale `100.114.37.90/32`; LAN `192.168.1.24/24` (enp4s0); kernel `7.0.0-29-generic`; Ubuntu 26.04; uptime 4 weeks 5 days.
- **C1 = Live / Production, and `planning.goaa.ai` is served by C1** — hostname `goaa-aika-cloud-1`, public `134.199.227.⟨108⟩` (confirmed by the host's own egress IP). Active tunnel config **`/etc/cloudflared/config.yml`** (tunnel `66ad1cc0-7754-45db-9ba9-99237900285d`, `cloudflared` active + enabled) ingress: `planning.goaa.ai → http://127.0.0.1:3100` (2 rules: `/planning` then catch-all), `api.goaa.ai` → 20 path rules to `127.0.0.1:8080` (worker control plane), `api.goaa.ai` catch-all → `127.0.0.1:18789` (openclaw = golden order API), terminal `http_status:404`.
  Public↔local equality: `https://planning.goaa.ai/` = 200 / 16,075 B / sha `314361aee777d01e` **== C1 `127.0.0.1:3100`**; `/client-login` = 200 / 10,893 B / sha `82fea21ae3411e42` **== local**; `/agent-loop/login` = 307 / 43 B / sha `20b64d81f2b80120` **== local**.
- **C2 = Test / Staging = `goaa-aika-cloud-2-01`** — public `143.198.224.⟨71⟩`; nginx `80`/`443` (`server_name _`, → `127.0.0.1:3100`; local https root = 401 gate, http = 301); `goaa-c2-clerk-ui-3102` (active, listening **13102**, BUILD_ID `28IP1GvAGURvF1PHRk8EL`), `goaa-c2-clerk-api-3103` (active, 127.0.0.1:3103), `goaa-c2-agent-loop` (enabled), `goaa-web-candidate` (→3100), `goaa-worker-agent` (WORKER_ID `do-cloud-2`); native PostgreSQL cluster `postgresql@16-goaa_c2test` on `5433` with `goaa_c2test` (15 tables) and `goaa_c2` (10 tables). C2 holds **real Clerk test data**: `users` 49, `user_roles` 55 (user 47 / admin 6 / agent 2), `user_identities` 23 (all provider `clerk`), `identity_events` 82, `agent_applications` 12 (**approved 2**), `agent_licenses` 11, `business_subjects` 6, `business_subject_links` 6.
- **Correction worth recording**: `/root/.cloudflared/config.yml` (mtime May 13) is a **stale duplicate** that lists only `api.goaa.ai` and would have led to the wrong conclusion ("planning.goaa.ai is not in the tunnel"). The authoritative file is the one the unit loads: `/etc/cloudflared/config.yml` (Sep 3).

**RISK: LOW** (mapping unambiguous; the only traps are the stale duplicate config and the disabled-but-active C2 Clerk units).
**RECOMMENDATION** — adopt this as the fixed map (D0 = `aika-core-01` / `100.114.37.90`; C1 = `goaa-aika-cloud-1` / `134.199.227.⟨108⟩` / serves `planning.goaa.ai`; C2 = `goaa-aika-cloud-2-01` / `143.198.224.⟨71⟩` / staging) and remove or clearly mark the stale `/root/.cloudflared/config.yml` in a later cleanup.
**EXECUTION REQUIRED? NO.**
**REQUIRES TAO APPROVAL? NO** (informational).

## 8. Verdict summary

| # | Claude claim | STATUS | Exec now? | Tao approval? |
|---|---|---|---|---|
| 1 | move rollback baseline to `40c8546e` | **TRUE** → MOVE TO `40c8546e` | pointer edit: YES (not done) | YES |
| 2 | several production keys, one still live (200) | **PARTIAL** (exposure TRUE, "200" UNKNOWN) → revoke: **YES** | YES (Tao/Clerk) | YES |
| 3 | 4 of 5 `/root` backups hold plaintext glue | **TRUE** → cleanup: **YES** | YES | YES |
| 4 | DB backup exists | **PARTIAL** (commerce partial; identity **NONE**) | YES | YES |
| 5 | 3103 does not self-heal | **CONFIRMED** → SELF-HEALING = NO | unit edit: YES (not done) | YES |
| 6 | `www` still shows old template | **FALSE** → PUBLIC CONTENT RISK = LOW | content tweak only | YES (Framer) |
| 7 | D0/C1/C2 mapping | **CONFIRMED** | NO | NO |

## 9. Blockers and open items (no action taken)

1. **Rollback pointer still targets the pre-Clerk `76af718`**; no remediation performed (forbidden this round).
2. **Activeness of the three legacy Clerk secret keys is UNKNOWN** — it cannot be established without exercising the keys against Clerk, which is outside this round's allowed operations. This is the single biggest unknown in §2.
3. **`goaa_platform` (identity) and the private-file store have no backup**, and no restore has ever been verified.
4. `40c8546e` is currently the *only* Clerk-capable build on disk; any rollback that must keep Clerk requires either `40c8546e` or a rebuild of `f719b27`.
5. C2's two Clerk units are `disabled` yet `active` (they would not come back after a reboot) — a staging-side fragility noted for a later window.
6. The active cloudflared config lives in `/etc/cloudflared/`, not `/root/.cloudflared/` — the stale copy should be removed or marked.

**End of report. No remediation was executed in this round.**
