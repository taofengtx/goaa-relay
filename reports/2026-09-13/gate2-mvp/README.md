# Gate-2 MVP — Aika-Box × QwenPaw AI Workspace (2026-09-13)

Minimal AI workspace added to the existing Aika-Box Local Console, built on the Gate-1 verified bridge.

| File | What it is |
|---|---|
| `GATE2-MVP-REPORT.md` | build report, T1–T15 test matrix, worker roster, risks, next step |
| `GCR-2026-09-13-AIKABOX-QWENPAW-MVP.md` | change record for GOLDEN-05 (Aika-Box `:5188`), change type **ADD ONLY** |
| `evidence/` | raw test JSON, code inventory with hashes, approval audit decisions |
| `shots/` | browser screenshots of the workspace and the approval card |

**Status**: built and verified on alternate port `:5198`; **GOLDEN-05 `:5188` not modified, not restarted**
(go-live on the Golden surface still needs Tao's explicit approval).

**Architecture**: `Browser → Aika-Box Local Console → server-side QwenPaw adapter → selected Worker QwenPaw`
(browser never talks to QwenPaw directly).

**Related**: Gate-1 closeout `../gate1-e2e-spike/GATE1-CLOSEOUT.md` (relay `b934c8c`);
Golden Baseline v1.0 `../golden-baseline-v1/` (canonical `GOLDEN-SURFACE-MANIFEST.json`).
