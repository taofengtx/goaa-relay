# Relay initial snapshots + secret scan — 2026-09-11

Repo: `taofengtx/goaa-relay` (public) · content = code + reports only.

## Snapshots

| dir | source | files | notes |
| --- | --- | --- | --- |
| `snapshots/frontend-daecc2a4/` | FE candidate commit `daecc2a40a7cb9b4e4db1e3b620f8c8ebe1113da` (branch `feat/c2-clerk-unified-login-v1`) | 603 | `git archive` of the commit → no `node_modules/`, no `.next/`, no untracked files |
| `snapshots/backend-dc64591b/` | BE candidate commit `dc64591ba7485aa973f373d5340842297f28b630`, path `services/c2_agent_loop` only | 37 | same, stripped of the `services/c2_agent_loop/` prefix |

## Secret scan (grep -rIn, path-only reporting)

| pattern | hits | classification |
| --- | --- | --- |
| `sk_live` | 0 | — |
| `client_secret` | 0 | — |
| `BEGIN PRIVATE KEY` | 0 | — |
| `AKIA` | 0 | — |
| `re_[A-Za-z0-9]{20}` | 0 | — |
| `sk_test` | 12 | synthetic fixtures: 24-char sequential payloads (`abcdefghijklmnopqrstuvwx`), non-Clerk length; plus one bare `sk_test_` placeholder in a doc |
| `pk_test` | 9 | synthetic fixtures (59-char base64 of the same sequential payload) + fixtures in tests |
| `pk_live` | 1 | `scripts/c2-clerk/test-entry-rules.mjs` — negative-test literal; payload is 47 chars with a `.`, not base64, does not decode to any Clerk host ⇒ not a key |
| `CLERK_SECRET` | 22 | environment-variable **names** only (config + tests) |
| `ghp_` | 14 | redaction regexes / docs (followed by non-token chars) — no token-shaped match |
| `postgres://` | 5 | 4 known allowances in `services/rag/*redact*`; 1 documentation sentence about redaction patterns (`docs/architecture/GOAA_LOCAL_TASK_RUNNER_F_LITE.md`) |
| email domains | — | `goaa.ai` (own), `example.com` / `example.test` / `b.test` (placeholders), `gmail.com` = owner's own handle already public in git history, `izs.me` = npm metadata in `package-lock.json` |

Removed from the snapshot: nothing secret — only `.env`-shaped files were filtered; the two repo-provided
templates (`.env.example`, `.env.production.example`) are kept only if they hold placeholders/allowlisted literals.

Reports and screenshots for later rounds go in `reports/<date>/`.

## Relay-only redaction (agreed with the repo owner, 2026-09-11)

GitHub's server-side push protection (rule GH013) rejected the first push with
`Stripe Test API Secret Key`, pointing at a synthetic fixture: `sk_test_` followed by a
24-character sequential payload (`abcdefghijklmnopqrstuvwx`) used to stub a secret-key env var.
It is not a real key (wrong length/charset for Stripe or Clerk). The detector matches the prefix only.

Per the owner's decision, **only the relay copies** of those literals were replaced with
`sk_test_FIXTURE_REDACTED`. **The candidate source trees are untouched.**

| file (inside the relay) | line(s) | occurrences |
| --- | --- | --- |
| `snapshots/frontend-daecc2a4/scripts/c2-clerk/test-bff.mjs` | 13, 63 | 2 |
| `snapshots/frontend-daecc2a4/scripts/c2-clerk/test-entry-rules.mjs` | 28 | 1 |
| `snapshots/frontend-daecc2a4/scripts/c2-clerk/test-golden-routes.mjs` | 23, 291 | 2 |
| `snapshots/frontend-daecc2a4/scripts/c2-clerk/test-middleware.mjs` | 15, 80 | 2 |

Total: 7 occurrences in 4 files (GitHub listed at most 5 locations per attempt, which is why the
two rejection messages named different subsets). After the replacement the relay tree contains
**0** remaining `sk_test_<8+>` literals; the rest of the snapshot is byte-identical to the candidate
commits `daecc2a4` (frontend) and `dc64591b` (backend).
