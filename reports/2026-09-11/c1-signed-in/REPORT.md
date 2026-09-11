# Round C1 — signed-in screenshots (2026-09-11)

Isolated C2 test pair only: headless agent browser -> SSH tunnel -> Next BFF
`localhost:13102` -> FastAPI `127.0.0.1:3103` -> PostgreSQL `goaa_c2test`.
No files were changed, no C2 artifact was touched, nothing was restarted.

## Sign-in
- Path: `/client-login?next=/agent-loop/customer` -> Email -> code (Clerk dev test account).
- Identifier: `c1round+clerk_test@example.com`, verification code `424242` (Clerk test-mode convention).
- **No `cf-turnstile-response` field and no captcha frame appeared at any step** (re-checked before
  submitting the identifier, right after it, and on the code step) — the bot-protection change the
  repo owner made is effective for this environment.
- Resulting session: Clerk `user_3JAdiNJklkQofAB4hgSmYlEbLSx`, `session.status = "active"`,
  cookies `__session` / `__client_uat` present.
- Login card title is now **"Continue to GOAA"** (was "Continue to GOAA C2 Auth Test") -> the
  dashboard rename is live; no code change was involved.

## Screenshots
| file | route | what it shows |
| --- | --- | --- |
| 01-customer.jpg | /agent-loop/customer | signed-in customer portal (AI Butler shell + rail) |
| 02-customer-skills.jpg | /agent-loop/customer/skills | Skills page inside the shell |
| 03-customer-get-licensed.jpg | /agent-loop/customer/get-licensed | Get Licensed page inside the shell |
| 04-customer-earning.jpg | /agent-loop/customer/earning | Earning page inside the shell |
| 05-agent-gate.jpg | /agent-loop/agent | Gate card `agent_role_required` |
| 06-admin-gate.jpg | /agent-loop/admin | Gate card `admin_required` |
| 07-logout-menu.jpg | /agent-loop/customer | MY ACCOUNT expanded -> LOG OUT |

## DOM measurements (read from the live pages)
- header brand text (`.goaa-brand-text`): **"AI Butler"**
- rail items (five): **Chat / Matters / Skills Marketplace / Get Licensed (NEW) / Earning Opportunities (NEW)**
- `document.body.innerText` CJK count: customer **0**, skills **0**, get-licensed **0**, earning **0**, agent **0**, admin **0**
- 05 gate text: `agent_role_required` — "Agent panel is locked ... needs an approved agent licence on the signed-in account."
- 06 gate text: `admin_required` — "Administrator access required ... only available to accounts holding the admin role."

## Observations (reported, not changed)
1. The golden AI Butler header still renders "LOGIN / REGISTER" while a Clerk session is active,
   and the `goaa_signed_in` cookie is not set for this flow. The portal shell itself reflects the
   session correctly (email shown, MY ACCOUNT / LOG OUT present). This is a golden-header gap, not
   something this round touched.
2. `/agent-loop/customer` shows the licence notice "Agent Portal opens after your licence is approved."
   (expected for a fresh test identity with no licence).
