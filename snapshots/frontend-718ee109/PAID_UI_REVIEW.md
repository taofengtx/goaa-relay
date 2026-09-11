# Paid-order entry guard and invoice status display

Parent: `9dff89b6719179de764c3977afb5c93e2a950e9c`.
Source-only follow-up, authorized for these two frontend fixes, tests and commit.
No deployment, restart, callback/Agent URL change, live order access or payment.

## Exact scope (4 files)

- M `app/connect-pass/page.tsx`: add the known `order.connectPaid` condition to
  guardedBuyPass's early return and the existing button's disabled/opacity expressions.
  A paid order cannot be used to re-enter verification by clicking this purchase entry,
  even when navigation has been requested but the document remains mounted.
- M `app/customer-order-live/page.tsx`: the invoice Payment Status value and color
  now use the same explicit `invoice.status === 'paid'` check as the existing badge.
  All other statuses, including absent/null/unrecognized values, display Pending,
  never Paid. Pending here is unconfirmed display, not proof of payment failure.
- A `scripts/test-paid-ui-regressions.cjs`: 13 focused offline regression cases.
- A `PAID_UI_REVIEW.md`: this handoff.

No edits to protected handlers, protected hashes, original 25/13 test assertions,
prices, state transitions, servicePaid derivation, Invoice data/PDF/actions, backend,
shared runtime, auth, dependency manifests or lockfiles. The earlier review's
"Invoice untouched" applies to its original commit; this follow-up explicitly changes
only the invoice Payment Status display, not its business logic or data.

## Provenance and evidence

Both edited source files matched the exact GitHub parent before editing. The invoice
row was already hardcoded Paid in `d889c3f15adac46d6ab8a3d87350e346e236ff33`;
customer-order-live/page.tsx was modified, not newly added, by 9dff89b.

The new suite failed on the unpatched parent: 4 passed / 9 failed, exit 1.
The exact same assertions after the source patch: 13 passed / 0 failed, exit 0.
Cases include saved old-journey paid/matched and paid/unmatched orders, delayed document
unload, direct/repeated handler invocation, matching pending/failure, an unpaid purchase
positive control, and paid/unpaid/pending/absent/null/unrecognized invoice status.
The invoice test parses the rendered JSON tree and checks the specific Payment Status
row plus the service-payment progress row; it does not rely on a global text regex.
The fixture models successful matching by updating its returned order snapshot.

Original recovery suite: 25 PASS, exit 0 (including all protected function hashes).
Original product handoff suite: 13 PASS, exit 0; its local source/test blob hashes were
verified against the candidate's GitHub tree. This unchanged suite ran in its existing
inspection directory; this was not a full-repository integration build.

Actual local toolchain: Node v24.19.0, React 18.2.0, react-test-renderer 18.2.0,
TypeScript 5.0.4. Existing isolated tools were reused, no dependency installation.
React resolution paths matched; require('react') === renderer-relative require('react')
was true. This is NOT an 18.3.1 rerun; Aika's approved isolated 18.3.1 environment
must rerun the three suites below.

Commands from a complete clean checkout, with isolated tools resolved consistently:

```sh
node scripts/test-paid-ui-regressions.cjs
node scripts/test-order-recovery.cjs
node scripts/test-product-handoff.cjs
```

## Remaining validation / no production authorization

Full Next production build was NOT run here: this scratch checkout contains selected
inspection files, no complete build checkout, and no Next.js dependency/cache. Existing
parent BUILD_IDs are not proof for this commit. Aika must run the existing fail-closed
build on this exact new commit and return versions, direct exits and the new BUILD_ID.
No new BUILD_ID or browser/production acceptance is claimed.

Review the four-file diff, rerun 13 + 25 + 13 tests with the approved same-instance
React 18.3.1 tooling, then perform the isolated production build. Existing conservative
unknown/cancelled-operation locks remain; normal automatic paid-order matching remains.
Production Loading/Processing diagnosis and the old Vercel callback configuration are
separate unresolved work. Do not deploy, merge, force-push, restart, create Checkout,
replay webhooks or change configuration under this handoff.
