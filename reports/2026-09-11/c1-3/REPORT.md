# Round C1.3 (segment B) — build, deploy, verify, browser checks (X1–X3)

Date: 2026-09-11
Scope: C2 test environment only (Next BFF 13102 → FastAPI 3103 → `goaa_c2test`).
C1 production, 3100/3101, `goaa_c2`, the Golden Flow and payment code were **not touched**.

Segment A results live in `test-results.md` (same directory). Summary of A:
`tsc --noEmit` **0 errors**; `scripts/test-*.cjs` **27 files / 27 passed**;
`c2-clerk/run-all.sh` **99 passed / 0 failed**; snapshot `frontend-d4ad5613` (**632 files**).

---

## B1 — build

- Tree: `work/c2-clerk-login-20260910`, HEAD **`d4ad5613ce03914fa4a4c8de741942bff153a7f8`**.
- Clerk env vars present in the build shell: **0**.
- `npx next build --no-lint` (`NEXT_TELEMETRY_DISABLED=1`, `NODE_OPTIONS=--max-old-space-size=1024`)
  → **rc=0**, `✓ Generating static pages (57/57)`. **ESLint was not run** (as before; stated honestly).
- Pre-render manifest after build: **route count = 1** — only `/icon.png`.
  `/`, `/planning` and `/client-login` are **no longer pre-rendered** (dynamic now); `dynamicRoutes: []`.
- Staged standalone tree: **1968 files** (`public/` in place).
- Font: `public/fonts/outfit/outfit-latin-wght-normal.woff2` **32292 B**,
  sha256 `6c18d579fd87c3776be068b762cbc83fde3acb543d49eabd3ade842eb987e887`;
  CSS `d66b672a2d43b659.css` references `fonts/outfit`.
- tar sha256 **`dbfaf846d6ef9573a78e586e47c054e554f28c91cefedd8878bdda209c9a3810`** (8,854,045 B).
- Artifact secret scan: `sk_test_` run of chars **0**, real Clerk instance host **0**.

## B2 — deploy

- Timestamp **`20260911-005345`**; scp tar sha256 matched on both sides; unpacked 1968 files.
- Backup of the previous runtime: **`/opt/goaa-test/ui-clerk-20260910.bak-20260911-005345`** (34M).
- `rsync -a --delete --exclude '.next/cache'` **rc=0**; on-host manifest re-check **0 failures**;
  tree owned by `goaa-c2loop:goaa-c2loop`; env file `clerk-ui-3102.env` **unchanged**.
- Restart **`goaa-c2-clerk-ui-3102.service`**.
  **Approval, stated plainly:** on **Aika's side no 🛡 approval card appeared and no approval step was
  involved** — the restart command was submitted directly and ran immediately. Whether this restart
  was in fact approved by Tao is **Tao's record to state**, not Aika's. (Same wording applies to the
  3103 restart in `reports/2026-09-11/c1-3-backend/REPORT.md`, corrected there too.)
- Result: `is-active=active`, **new MainPID `2007280`**, `ActiveEnterTimestamp 2026-09-11 07:54:16 UTC`.

## B3 — post-restart verification

- BFF health `200`, `database.reachable=true`, `database.name=goaa_c2test`.
- Font endpoint `200`, `content-type: font/woff2`, 32292 B.
- Unauthenticated `auth/me` → **401**.
- `/planning` HTML `200`; **`clerk-js` now present** (`data-clerk-js-script`) and the page carries
  `clerkAuth":true` (was `false` before this change); `Cache-Control: private, no-cache, no-store,
  max-age=0, must-revalidate` (dynamic marker). `/` and `/client-login` likewise carry `clerk-js`.

## B4 — browser: sign-out then sign-in

- Sign-out: click the golden account menu → Clerk `signed-out`; `localStorage.client_token` cleared;
  the sessionStorage marker cleared; header back to `LOGIN / REGISTER▾`. Backend log shows
  **`POST /api/v1/agent-loop/golden/session/revoke → 200 OK`**. `location.search` was empty — the
  `?logged_out=1` intermediate state was **not observed** (reported as-is).
- Sign-in: `/client-login?next=%2Fagent-loop%2Fcustomer` → Clerk card
  (`data-clerk-component="SignIn"`) → email `c1round+clerk_test@example.com` → "Check your email"
  6-digit code → `424242`. **Turnstile did not appear** (`input[name=cf-turnstile-response]` and any
  captcha frame both false) → nothing was bypassed. Signed-in landed on `/agent-loop/customer`.
- Back at `/planning`: header `MY ACCOUNT▾` at ~1–2 s, ~8 s and ~11.5 s (stable);
  `/api/agent-loop/golden/session/verify → 200`.
- Screenshots `01`–`05` (see below).

## B5 — DOM / typography / CJK

`/planning` (signed in):

- `.goaa-brand-text` = **"AI Butler"**, font-family **Outfit**.
- `.workspace-nav-item` = **6** nodes: `Chat`, `Matters`, `Skills Marketplace`, `Get Licensed NEW`,
  `Earning Paths NEW` (the 5 real items) plus one section heading sharing the class name;
  every node height = **41px**.
- `.workspace-kicker` = "Current planning task"/Outfit; `.workspace-section-head h2` = "GOAA 规划"/Outfit.
- `.chat-bubble` and `.workspace-composer textarea` = **Inter** (golden chat surface, unchanged).

`/agent-loop/customer`: `.goaa-brand-text` = "AI Butler"/Outfit; `.goaa-rail-item` = "Chat"/Outfit;
`.pp-h1` = "Get Licensed"/Outfit; `.pp-btn` = "Become an Agent"/Outfit; `.pp-muted` = Inter.

CJK count on **all 6 portal pages** (`customer`, `customer/skills`, `customer/earning`,
`customer/get-licensed`, `agent`, `admin`) = **0**.

`/planning` resources = 21; production `api.goaa.ai` requests while on the planning home = **0**.

---

## X1 — 0004 real path: the business session is minted on `/planning` itself

Steps (no page clicks, no tab switching, no focus changes):

1. On the signed-in `/planning` tab, `localStorage.removeItem('client_token')` and
   `sessionStorage.removeItem('goaa_golden_business_session')`; both confirmed gone.
2. `location.reload()`; then read at ~1 s / ~3 s / ~10 s.

Readings:

| time | Clerk | `__goaaGoldenSession` | `lastError` | `localStorage.client_token` | marker | header |
| --- | --- | --- | --- | --- | --- | --- |
| ~1 s | object | present | `null` | **present (new value)** | present | `MY ACCOUNT▾` |
| ~3 s | object | present | `null` | present (same new value) | present | `MY ACCOUNT▾` |
| ~10 s | object | present | `null` | present | present | `MY ACCOUNT▾` |

Backend log during the window: **`POST /api/v1/agent-loop/golden/session → 200 OK`** (a mint).
A `GET /api/v1/agent-loop/golden/session/verify → 200` also appears — that one is from the very
first page load of the round (it still held the previous, valid token).

Why the expected `verify 401` is not in the 3103 log: the BFF route is the one that answers it.
`credentialFor()` in `app/api/agent-loop/[...path]/route.ts` gives `golden/session/verify` **only the
business bearer** the browser presented; with no business credential there is no upstream call, and
the BFF itself answers **401**. A direct in-page probe of `verify` with no business bearer returned
**401 `{ "error": { "code": "clerk_session_required" } }`** and produced **no** 3103 log line —
confirming it is the BFF, not the API. The mint then goes out as an ordinary route
(`upstreamToken` = the Clerk session token) → 3103 `POST /golden/session 200`.

Conclusion: after the local business credential is removed, **reloading `/planning` re-establishes
the business session in that page** (verify → 401 at the BFF → `POST /golden/session` → 200 → new
`client_token` stored, marker rewritten, header stays `MY ACCOUNT▾`, `lastError=null`).
Screenshot: **`06-planning-bridge-mint.jpg`**.

Note (test data): step 1 leaves one previously-issued, still-valid token behind in `goaa_c2test`.
This is a test database and the data is acceptable; recorded here for completeness.

## X2 — does the Matters view send a credential to production?

Opened the Matters view on `/planning`, waited 5 s.

Browser console (verbatim, CORS message only — URLs kept, query strings none):

```
Access to fetch at 'https://api.goaa.ai/api/v1/order/orders' from origin 'http://localhost:13102'
has been blocked by CORS policy: Response to preflight request doesn't pass access control check:
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

`network_requests` for `api.goaa.ai`: **one** entry —
`GET /api/v1/order/orders`, resourceType `fetch`, **no status** (failed). No `OPTIONS` entry was
captured by the tool.

This message names the **preflight** ("Response to preflight request doesn't pass access control
check"), i.e. the browser refused at the preflight stage because the request was not simple (it
carried an `Authorization` header).

Conclusion — one of the two allowed statements: **預檢被擋、未送出帶 token 的請求**
("the preflight was blocked; the credentialed request was not sent").

## X3 — login entry (todo note only; no file changed)

`/client-login?next=/planning` currently renders the **golden login page**, not the Clerk card,
because the unified entry only accepts `/agent-loop/*` targets. Before launch the golden header's
`LOGIN` must route to Clerk and return to `/planning` after sign-in (middleware; Aika scope).

---

## Route count (as-is)

`goaa-c2-clerk-api-3103.service` exposes **28** decorated routes after the C1.3 (1/2) deploy
(24 prior + 4 golden: 2 GET + 2 POST; golden routes = `GET/POST /golden/session`,
`GET /golden/session/verify`, `POST /golden/session/revoke`).
The earlier figure **"26" was Claude's arithmetic error** and is superseded by this count.

## Housekeeping

- No token, JWT or session value is written anywhere in this report.
- Screenshots in this directory: `01-planning-after-signin.jpg`, `02-planning-rail.jpg`,
  `03-planning-matters.jpg`, `04-customer-home.jpg`, `05-get-licensed.jpg`,
  `06-planning-bridge-mint.jpg`.
- C1 production, 3100/3101, `goaa_c2`, the Golden Flow and payment: untouched.
