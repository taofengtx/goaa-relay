# Round C1 fix — build, deploy, screenshots (2026-09-11)

Isolated C2 test pair only (Next BFF `localhost:13102` -> FastAPI `127.0.0.1:3103` -> PG `goaa_c2test`).
No production system, no C1 host, no real data.

## Build
- `npx next build --no-lint` rc=0 (Compiled successfully; 57/57 static pages). **ESLint was NOT run** (stated honestly).
- deployed bundle: 8,994,709 B, sha256 `1295a83ee4752be6e5130f7fb38b69b5c5b61f8a0c6300da2ab50da1c90ee58d`
- unit `goaa-c2-clerk-ui-3102.service` restarted (approved), MainPID 2000007, "Ready in 132ms"
- previous runtime tree kept at `/opt/goaa-test/ui-clerk-20260910.bak-20260911-060539`
- 2075/2075 manifest lines verify OK on the host

## Root cause fixed (verified numerically, not only visually)
Golden butler chat avatar already carries `class="goaa"`; the C1 token sheets scoped their
rules to `.goaa`, so `min-height:100vh` stretched that avatar into a full-column purple ellipse.
The fix re-scopes the token sheets to `.goaa-portal`.

Live DOM measurement on `/planning` after the fix:

| element | size | border-radius | background | min-height |
| --- | --- | --- | --- | --- |
| `span.chat-avatar.goaa` | 32 x 32 px | 50% | transparent | auto |

Deployed CSS contains no bare `.goaa` scope rule from the token sheets (the remaining
`.goaa` rules are the pre-existing golden butler rules for that avatar).

## Screenshots
| file | what it shows |
| --- | --- |
| 01-planning-avatar-fixed.jpg | `/planning` full page — avatar back to a 32px circle, no purple column |
| 02-client-login-clerk-card.jpg | `/client-login?next=%2Fagent-loop%2Fcustomer` — Clerk card |

## Left rail (as rendered)
`+ New` | Chat | Matters | Skills Marketplace | Get Licensed (NEW) | Earning Opportunities (NEW)
= the five rail items plus the "+ New" action; `记忆与能力` is the pre-existing golden
section label (Chinese), unchanged by this round.

## Clerk card title (task C)
Still reads **"Continue to GOAA C2 Auth Test"** (logo alt = `GOAA C2 Auth Test`) on this
build. No code change is involved: it follows the Clerk application name in the dashboard.
Once the app is renamed to `GOAA` the card will read "Continue to GOAA".
