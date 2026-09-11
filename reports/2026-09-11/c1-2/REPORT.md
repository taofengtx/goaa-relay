# Round C1.2 — build, deploy and signed-in verification (2026-09-11)

Isolated C2 test pair only: Next BFF `localhost:13102` -> FastAPI `127.0.0.1:3103` -> PostgreSQL
`goaa_c2test`, reached over an SSH tunnel. No production system, no C1 host, no real data.
Built from frontend candidate `b602bdd2556143ff6ba7330bd858304459a5b770`.

## B1 build
- `npx next build --no-lint` rc=0, `✓ Generating static pages (57/57)`. **ESLint was NOT run**
  (`--no-lint` as instructed) — stated plainly rather than claiming a full check.
- standalone composed with `public/`; artifact contains
  `public/fonts/outfit/outfit-latin-wght-normal.woff2` (32292 B, sha256 `6c18d579…e887`).
- bundle 8,926,530 B, sha256 `685b616cd76c35bbe48fa38d5f136fe1d49ad33ae092c9d9f7545b4c42dc3799`;
  2077 files (was 2075 before the two font files).

## B2 deploy (13102 runtime)
- scp sha256 matched on both sides before unpacking; unpacked 2077 files.
- previous tree kept at `/opt/goaa-test/ui-clerk-20260910.bak-20260911-000731` (35M).
- `rsync -a --delete --exclude '.next/cache'` rc=0; owner `goaa-c2loop:goaa-c2loop`;
  on-host `sha256sum -c` over the manifest: **0 failures**.
- service restarted (this time no approval prompt was raised; the command ran directly and is
  reported as such). New MainPID **2002135**, `ActiveState=active`, "✓ Ready in 99ms",
  listening `127.0.0.1:13102`.

## B3 post-restart gates
- `GET /api/agent-loop/health` -> 200, `database.reachable=true`, `database.name=goaa_c2test`.
- `HEAD /fonts/outfit/outfit-latin-wght-normal.woff2` -> **200**, `Content-Type: font/woff2`,
  `Content-Length: 32292`.
- unauthenticated `/api/agent-loop/auth/me` -> 401.

## B4 screenshots
| file | route | note |
| --- | --- | --- |
| 01-customer-home.jpg | /agent-loop/customer | "Not started" pill and the Earning Paths rail item each on one line |
| 02-skill-to-planning.jpg | /planning (after "Use this skill" on Tax & income) | prompt arrives as a chat bubble |
| 03-rail-matters.jpg | /planning (after clicking Matters in the rail) | Matters view, not Chat |
| 04-golden-rail.jpg | /planning | golden left rail, Earning Paths on one line |
| 05-account-menu.jpg | /agent-loop/customer | MY ACCOUNT expanded -> LOG OUT |

Signed in as the Clerk dev test account `c1round+clerk_test@example.com` (OTP path, code 424242);
**no Turnstile and no captcha frame appeared at any step**.

## B5 DOM readings (live values)
Fonts:
- `document.fonts.check('600 16px Outfit')` — `/agent-loop/customer`: **true**; `/planning`: **true**.
- `getComputedStyle(.goaa-brand-text).fontFamily` — portal: `Outfit, Inter, system-ui, -apple-system,
  "Segoe UI", sans-serif`; on `/planning` the golden header wins: `Inter, ui-sans-serif,
  -apple-system, BlinkMacSystemFont, …`.
- `performance.getEntriesByType('resource')` entries matching outfit — exactly one,
  `outfit-latin-wght-normal.woff2`, `responseStatus` **200**, on both routes.

Layout:
- 01 "Not started" (`span.pp-status.pp-status-muted`): height **31 px**, width 83 px,
  line-height 18.6 px => single line.
- 01 rail "Earning Paths": wrapper `div` height **51 px** (w 230) and `a.goaa-rail-item` height
  **51 px** (w 230); inner label `span` height 25 px, line-height 24.8 px => single line.
  All five rail items measure 51 px each.
- 04 `/planning` rail `a.workspace-nav-item` "Earning Paths NEW": height **41 px** (line-height 21 px)
  => single line.
- 02 after "Use this skill" on Tax & income: `location.href` = `http://localhost:13102/planning`
  (the `?prompt=` parameter is consumed on arrival — `location.search` is empty) and the text
  "Help me with tax & income" is present in the conversation as `div.chat-bubble` (height 54 px);
  the composer textarea is empty.
- 03 after clicking Matters: `location.href` = `http://localhost:13102/planning`, **no `view=`**
  (search empty); the element carrying the active class is `div.workspace-nav-item.active` with the
  text **Matters**.
- `document.body.innerText` CJK count: customer **0**, skills **0**, get-licensed **0**, earning **0**.

## B6 read-only observations (nothing changed)
- After signing in, on `/planning`: `localStorage.client_token` — **absent**.
- `goaa_signed_in` cookie — **absent**.
- Golden header on `/planning` shows **"LOGIN / REGISTER ▾"**, not MY ACCOUNT, even though the Clerk
  session is active and the portal shell on `/agent-loop/*` does show the signed-in account.
  Reported as-is; no file was modified for this round.

## Note on one transient error
The first navigation to `/agent-loop/customer` right after the restart returned
`net::ERR_TOO_MANY_REDIRECTS`, and a cookie-less `curl` at the same moment followed the normal
2-hop chain to `/client-login?next=…`. Re-navigating immediately afterwards rendered the page
correctly and every subsequent navigation was clean; treated as a transient browser/session state
right after the restart, not a server-side loop. Recorded here rather than omitted.
