# Aika-Box Local Console — Unified ChatGPT-style Scrollbars (CSS-only)

Round: 2026-09-13 (Tao 令 23:52 PDT) · D0 / Aika-Box local development only
Status: **implemented & verified on the D0 dev instance `:5198` · NOT applied to Golden `:5188`**

---

## 1. Authorization & boundary (as instructed)

| Item | Ruling |
|---|---|
| Scope | **CSS only** — a single scrollbar skin block inside the existing `<style>` |
| Forbidden | JS, QwenPaw adapter, Worker API, Session API, SSE protocol, Approval API, Audit API, Auth, DB, systemd, C1, C2, Golden `:5188` |
| Where | D0 verification instance `:5198` only (`100.114.37.90:5198`, tailnet-bound) |
| Golden `:5188` | **not modified, not restarted** (§5 evidence) |
| Target visual | width ≈6px · transparent track · translucent grey thumb · radius 999px · no visible border · no bright white · dark theme untouched |

No other feature was carried in: `git diff --numstat` = **10 / 0 on `local-console/main.py`**, CSS insertions only.

---

## 2. Change content

Inserted immediately before `</style></head>` (the closing of the single console stylesheet), 10 lines / 601 bytes:

```
/* === Aika-Box: unified ChatGPT-style scrollbars (CSS-only) === */
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(255,255,255,.18);border-radius:999px;border:none}
::-webkit-scrollbar-thumb:hover{background:rgba(255,255,255,.30)}
::-webkit-scrollbar-corner{background:transparent}
/* Firefox only: thin + coloured (engines with ::-webkit-scrollbar skip this) */
@supports (-moz-appearance:none) or (not selector(::-webkit-scrollbar)){
  *{scrollbar-width:thin;scrollbar-color:rgba(255,255,255,.18) transparent}
}
```

### Why the Firefox lines are behind an engine guard (measured, not assumed)

Chromium ≥121 implements `scrollbar-width` / `scrollbar-color`; when `scrollbar-color` is not `auto`
the engine drops the legacy `::-webkit-scrollbar` styling and falls back to its own thin scrollbar.
Measured on the very same page, same content, only the CSS differing:

| Variant (injected live) | computed `::-webkit-scrollbar` | chat | approvals | audit | code (horizontal) | nav |
|---|---|---|---|---|---|---|
| A: WebKit rules only | 6px | **6** | **6** | **6** | **8** | 7 |
| B: A + un-guarded `*{scrollbar-width:thin;scrollbar-color:…}` | 6px (ignored) | **10** | **10** | **10** | **12** | 11 |
| C: A + `@supports (-moz-appearance:none) or (not selector(::-webkit-scrollbar))` | 6px | **6** | **6** | **6** | **8** | 7 |

Variant B breaks the requested 6px look in Chromium (bars become 10–12px), so the shipped block uses
variant C: Chromium evaluates `selector(::-webkit-scrollbar)` = true and skips the block
(verified in-browser: `CSS.supports('selector(::-webkit-scrollbar)') === true`,
`CSS.supports('-moz-appearance','none') === false`, `scrollbar-width` computed stays `auto`),
while Firefox — which has no `::-webkit-scrollbar` — applies `scrollbar-width:thin` +
`scrollbar-color: rgba(255,255,255,.18) transparent`.

### Traceability

| Artefact | Value |
|---|---|
| Worktree / branch | `/home/aika/gate2-ui-wt` · `gate2-ui-patch` |
| `local-console/main.py` before | `b5371dbaf5441f14` (2244 lines / 160,684 B) |
| `local-console/main.py` after | **`deea05988031b503`** (2254 lines / 161,285 B, BOM=False, CRLF=0, `ast.parse` OK) |
| Patch method | unique-anchor byte replace, `count(anchor) == 1` asserted pre-write (2 `</style></head>` exist in the file → anchor = media-query close `}` + `</style></head>`), CSS occurrences asserted `== 1` post-write |
| Diff | `/tmp/sb-scrollbar.diff` 985 B · `sha16 99ded6dec4e42f39` · +10/−0 |
| Served page (`GET /` on `:5198`) | 107,703 B · `sha16 0826dc6f2e5f30d9` · 7 occurrences of the scrollbar words |
| Served page (`GET /` on `:5188`) | 99,105 B · `sha16 0ac695507342933b` · **0 occurrences** |

---

## 3. Objective verification (Chromium 1440×813 and 420×900)

Same probe, same injected overflow content, executed once before and once after the change.
`getComputedStyle(el, '::-webkit-scrollbar…')` is readable in Chromium, so every visual claim below is a number.

Scrollbar thickness = `offsetWidth − clientWidth` (`offsetHeight − clientHeight` for the horizontal case);
+1 px on `.side` and +2 px on the code block is their own border, not bar thickness.

| Measured element | Before | After | Requested |
|---|---|---|---|
| page (`html` / `body`) | 0 | **0** | page must not scroll |
| left nav `.side` | 16 | **7** | thin |
| chat scroller `#qp-log` | 15 | **6** | ≈6px |
| `#qp-approvals` | 15 | **6** | ≈6px |
| `#qp-audit` | 15 | **6** | ≈6px |
| code block, horizontal bar | 17 | **8** | ≈6px |
| `::-webkit-scrollbar` width/height | `auto` | **`6px` / `6px`** | 6px |
| thumb background | `rgba(0,0,0,0)` | **`rgba(255,255,255,0.18)`** | translucent grey |
| thumb border-radius | `0px` | **`999px`** | rounded |
| thumb border width | — | **`0px`** | no visible border |
| track / corner background | transparent | **`transparent`** | transparent |

Narrow screen **420×900** (same candidate): nav 7, chat 6, approvals/audit 0 (no overflow ⇒ no bar, correct),
`::-webkit-scrollbar` 6px, thumb `rgba(255,255,255,0.18)` radius `999px`,
document 900 = viewport height, horizontal overflow 0, composer visible at `[30,673,360,50]`.

---

## 4. Regression check (layout must not move)

Nine containers measured before vs after the change — **all identical**, i.e. the pure scrollbar
restyle did not shift any content:

| Container | rect [x, y, w, h] (before = after) |
|---|---|
| `.side` | [0, 0, 216, 813] |
| `.main` | [216, 0, 1224, 813] |
| `.qp-main` | [245, 316, 1166, 475] |
| `#p-qwenpaw .chat` | [245, 316, 805, 475] |
| `.qp-side` | [1066, 316, 345, 475] |
| composer | [262, 723, 771, 50] |
| `#qp-log` | [262, 399, 771, 317] |
| `#qp-approvals` | [1085, 357, 308, 171] |
| `#qp-audit` | [1085, 602, 308, 171] |

Also: document height 813 = viewport (no page scrollbar), horizontal overflow 0,
console **JS errors 0 / uncaught exceptions 0** after the change (listener count unchanged;
favicon request is pre-existing), and `git diff --name-only` = `local-console/main.py` only —
no JS, no adapter, no API, no Session/Approval/Audit code, no auth, no DB, no systemd unit.

---

## 5. Golden `:5188` untouched (re-verified after the change)

| Check | Value |
|---|---|
| `goaa-local-console` MainPID / NRestarts | `2457759` / `2` (unchanged) |
| ActiveEnterTimestamp | Sun 2026-09-13 20:58:15 PDT (unchanged ⇔ no restart) |
| listeners | `100.114.37.90:5188` + `127.0.0.1:5188` (PID 2457759) |
| serving `main.py` | `0c78b8e83516613a` (== pre-round, == the Gate-2 Final Golden Patch file) |
| `GET /` | 99,105 B `0ac695507342933b` · scrollbar CSS occurrences **0** |
| `GET /login` | 3,560 B `8aa6a59c5f0271b1` (byte-identical to pre-round) |
| D0 dev `:5198` | PID 2489870, `LISTEN 100.114.37.90:5198` (tailnet only, no new public entry), `GET /health=200`, `/login=200`, `/=200` |

---

## 6. Screenshots

| File | Bytes | sha16 | Content |
|---|---|---|---|
| `SC-01-scrollbar-chat-desktop.png` | 215,182 | `a30a21f3dc3b51a4` | 1440×813, real session history (14 messages, chat overflows) |
| `SC-02-scrollbar-narrow-420x900.png` | 108,103 | `a960abc0c48b77d3` | 420×900 narrow workbench |
| `SC-03-scrollbar-approvals-audit-code.png` | 237,896 | `1908f54ce6d97042` | approvals + audit + horizontal code bar (overflow content injected by the probe) |

Honest limitation: this agent has **no image perception** — the screenshots were captured but not
viewed. Every visual statement in this report is therefore backed by the geometry/computed-style
numbers in §3–§4, not by eyeballing the images.

---

## 7. Not done / open

* Not applied to Golden `:5188` (per instruction); the change lives in the D0 worktree commit only.
* No push of the worktree branch; no deploy; no restart of `:5188`; no systemd change.
* Firefox behaviour is reasoned from engine capability (`::-webkit-scrollbar` unsupported ⇒ guard
  applies) and could not be executed in a Firefox instance in this environment.
