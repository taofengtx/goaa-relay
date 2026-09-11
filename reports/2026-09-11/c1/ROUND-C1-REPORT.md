# Round C1 — applied, built, deployed, captured (2026-09-11)

Author: Aika (agent). Everything below was run on the isolated C2 test pair
(Next BFF `localhost:13102` -> FastAPI `127.0.0.1:3103` -> PostgreSQL `goaa_c2test`).
No production system, no C1 host, no real data, no payment path was touched.

## 1. Patch
- file: `patches/0001-round-c1-three-portal-shell.patch` (uploaded by the repo owner at the repo root; moved here for the record)
- sha256: `d4a3871f29e1ab9ceeb6c893b8542f3b2718c69cc669ca1bdf55499ef2eeb710`
- applied with `git am` (patch's own message kept): `51c9914aeaaecf9b05ccc931610cdfe61d53b707`
  "Round C1: three-portal shell, growth pages, golden sign-out wiring, tests"
- parent: `daecc2a40a7cb9b4e4db1e3b620f8c8ebe1113da` (the daecc2a candidate)
- 46 files changed, +1123 / -335

## 2. Checks on the applied tree
- `npm ci` rc=0 (383 packages), @clerk/nextjs 6.39.6 / next 14.2.35 / react 18.3.1
- `npx tsc --noEmit` rc=0
- `scripts/test-*.cjs`: **23 files, 23 green, 0 failing**
  (incl. test-portal-shell 7, test-signout-wiring 8, test-customer-growth-pages 6,
   test-portal-preview-isolation 8 — the isolation test now uses a direction check, not git status)
- `bash scripts/c2-clerk/run-all.sh`: **99 passed, 0 failed** (7 groups)
  entry-rules 16, middleware 15, bff 14, sign-out 7, candidate-shape 8, golden-routes 16, golden-session 23

## 3. Build + deploy
- `npx next build --no-lint` rc=0. **ESLint was NOT run** (stated honestly).
- artifact bundle sha256 `b2d93c0f8bc353d179a396b44c758dbc415e47b4696af5aa4386a4d72c85963f`
- deployed to `/opt/goaa-test/ui-clerk-20260910` (previous tree backed up to
  `ui-clerk-20260910.bak-20260911-053254`, 34M); 2075/2075 manifest lines verify OK
- unit `goaa-c2-clerk-ui-3102.service` restarted (approved), MainPID 1999231, "Ready in 101ms"
- health `/api/agent-loop/health` 200, `database.name=goaa_c2test`; unauth `/api/agent-loop/auth/me` 401
- unauth `/agent-loop/customer|skills|agent|admin` -> 307 -> `/client-login?next=...` -> 200 (2 hops, all on `localhost:13102`)

## 4. Screenshots (this directory)
| file | what it shows |
| --- | --- |
| 01-client-login.jpg | `/client-login` (golden page, unchanged bytes) |
| 02-client-login-clerk-card.jpg | `/client-login?next=%2Fagent-loop%2Fcustomer` -> Clerk card with `goaaClerkAppearance` |
| 03-planning.jpg | `/planning` (AI Butler workspace, left rail) |
| 04..07-*gated.jpg | the four `/agent-loop/*` pages unauthenticated -> login card |

Appearance evidence (computed styles in the live DOM): `--goaa-accent: #6944cc`,
dark page background `rgb(5,5,7)`, pill buttons (border-radius 999px), Clerk logo = `/goaa-logo.svg`.

### Not captured: the four signed-in portal views
Signing in was attempted with a Clerk test identifier
(`c1round+clerk_test@example.com`). After submitting the identifier a **Cloudflare
Turnstile** challenge was injected (`cf-turnstile-response` field present), so the
automated attempt was **stopped immediately and not bypassed** (standing rule).
Consequence: the four gated pages could only be captured in their unauthenticated
state. A human-completed sign-in in a visible browser is required to capture the
signed-in shells.

## 5. CJK scan
- source scan over the 46 files changed by this patch: **1084 CJK chars before, 1084 after, delta +0**
  (all pre-existing: golden AI Butler copy in `app/components/ChatComponent.tsx` = 852, test fixtures = 232)
- `scripts/test-workspace-english.cjs` 4/4 (workspace rail labels are English)
- rendered `/planning` still shows 132 CJK chars — that is the golden Butler's own
  Chinese conversation copy, unchanged by this round.
