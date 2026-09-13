# Golden Baseline v1.0 — Freeze Package (READ-ONLY)

**Date:** 2026-09-13 · **Mode:** read-only · **Owner of approval:** Tao

> **Canonical machine-readable manifest:** `GOLDEN-SURFACE-MANIFEST.json`（CANONICAL = TRUE）
> **Legacy compatibility alias:** `GOLDEN-REGISTRY.json`（LEGACY_ALIAS，內容語義一致，僅為兼容保留）

| File | Purpose |
|------|---------|
| `GOLDEN-BASELINE-V1.md` | 主報告：Golden 定義、5 個 surface 完整 manifest、Registry、Roadmap（§D/§E） |
| **`GOLDEN-SURFACE-MANIFEST.json`** | **CANONICAL** 機器可讀 Golden Surface Manifest（surface 指紋 / 依賴 / 缺口 / 未來增項 / 角色方向）— 未來 Aika-Box / QwenPaw / ChatGPT / Worker **只認此檔名** |
| `GOLDEN-REGISTRY.json` | **LEGACY_ALIAS / COMPATIBILITY_ALIAS**（保留以防舊腳本與歷史引用失效；機器語義與 canonical 相同，**勿再新增引用**） |
| `GOLDEN-CHANGE-POLICY.md` | 變更審批規則（只增不減、兼容優先、破壞性單獨批准、回滾錨點） |
| `shots/GOLDEN-01-marketing-www.png` | www.goaa.ai 截圖（324,221 B · sha16 `8193054c230ffe6f`） |
| `shots/GOLDEN-02-user-portal-customer-preview.png` | Customer 面截圖（71,668 B · sha16 `528d2e9f17d8511b`） |
| `shots/GOLDEN-03-provider-legacy-agent-preview.png` | Provider(agent) 面截圖（65,807 B · sha16 `5dbe4dd514ceb605`） |
| `shots/GOLDEN-04-admin-console-preview.png` | Admin 面截圖（112,332 B · sha16 `95b4ef55fcdca574`） |
| `shots/GOLDEN-05-aikabox-5188.png` | Aika-Box `:5188` 截圖（111,648 B · sha16 `b71b6f4cf9564250`） |

## 一句話結論
GOLDEN-01…05 = **FROZEN**（v1.0）。AI Agent Marketplace / Matters 等**未存在**能力明確標為 **NOT GOLDEN**（§D）。本輪**未動任何系統**（無 deploy / restart / DB write / rename）。
