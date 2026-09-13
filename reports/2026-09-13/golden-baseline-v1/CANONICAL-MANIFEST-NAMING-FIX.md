# CANONICAL MANIFEST NAMING FIX — Golden Baseline v1.0

- **Date:** 2026-09-13 · **Scope:** minimal naming standardization only
- **Mode:** no code / no route / no service / no env / no DB / no screenshot / no Golden semantic change

---

## 1. Before

```
reports/2026-09-13/golden-baseline-v1/
├── GOLDEN-BASELINE-V1.md
├── GOLDEN-CHANGE-POLICY.md
├── GOLDEN-REGISTRY.json          <-- 唯一機器可讀入口（非 canonical 名稱）
└── README.md
```

- 機器可讀 Golden 入口檔名 = `GOLDEN-REGISTRY.json`
- 與原始規範要求的 canonical 檔名 `GOLDEN-SURFACE-MANIFEST.json` 不一致
- 無兼容別名層；舊引用只能指向 `GOLDEN-REGISTRY.json`

## 2. After

```
reports/2026-09-13/golden-baseline-v1/
├── GOLDEN-BASELINE-V1.md            (updated: canonical/alias 聲明)
├── GOLDEN-CHANGE-POLICY.md          (updated: canonical/alias 聲明)
├── GOLDEN-SURFACE-MANIFEST.json     <-- CANONICAL = TRUE  (NEW)
├── GOLDEN-REGISTRY.json             <-- LEGACY_ALIAS / COMPATIBILITY_ALIAS
├── CANONICAL-MANIFEST-NAMING-FIX.md (NEW: 本報告)
└── shots/  (5 PNG, 未觸碰)
```

**統一規則：** Canonical = `GOLDEN-SURFACE-MANIFEST.json`；Alias = `GOLDEN-REGISTRY.json`。
未來 Aika-Box / QwenPaw / ChatGPT / Worker **只認** `GOLDEN-SURFACE-MANIFEST.json`。

## 3. Canonical file

| 項 | 值 |
|----|-----|
| 檔名 | `GOLDEN-SURFACE-MANIFEST.json` |
| `canonical` | `true` |
| `status` | `canonical` |
| `canonical_manifest` | `GOLDEN-SURFACE-MANIFEST.json` |
| `legacy_alias` | `GOLDEN-REGISTRY.json` |
| bytes | 14,500 |
| sha256[0:16] | `d7404862d4c93ad1` |
| BOM | `False` |
| JSON parse | **PASS** |

## 4. Compatibility alias

| 項 | 值 |
|----|-----|
| 檔名 | `GOLDEN-REGISTRY.json`（**未刪除**） |
| `canonical` | `false` |
| `status` | `compatibility_alias` |
| `canonical_manifest` | `GOLDEN-SURFACE-MANIFEST.json` |
| bytes | 14,469 |
| sha256[0:16] | `2e93faf1463cd06a` |
| BOM | `False` |
| JSON parse | **PASS** |

> 只在原 schema 上**新增 3 個 metadata 欄位**（`canonical` / `status` / `canonical_manifest`），**未變更任何既有欄位與業務語義**。

## 5. Files changed（diff 範圍）

| 檔 | 變更型態 |
|----|----------|
| `GOLDEN-SURFACE-MANIFEST.json` | **新增**（canonical） |
| `GOLDEN-REGISTRY.json` | 新增 alias metadata（`canonical:false` / `status:"compatibility_alias"` / `canonical_manifest`） |
| `GOLDEN-BASELINE-V1.md` | 新增 canonical / alias 聲明區塊（header 下方） |
| `GOLDEN-CHANGE-POLICY.md` | 新增 canonical / alias 聲明區塊（header 下方） |
| `README.md` | canonical / alias 兩行 + 頂部聲明 |
| `CANONICAL-MANIFEST-NAMING-FIX.md` | **新增**（本報告） |

**Must-not-appear（已確認全部未出現）**：source code change / route change / service change / env change / DB change / screenshot change / Golden content semantic change / 任何 Golden 證據刪除。

## 6. JSON validation

| 檢查 | 結果 |
|------|------|
| `GOLDEN-SURFACE-MANIFEST.json` parse | **PASS** |
| `GOLDEN-REGISTRY.json` parse | **PASS** |
| BOM check（兩檔） | **False / False** |

## 7. Semantic match（canonical vs alias）

剝除 4 個 metadata 欄位後，兩份 JSON 的業務 payload **完全相等**：

| 檢查 | canonical | alias | 一致 |
|------|-----------|-------|------|
| version | `1.0` | `1.0` | ✅ |
| frozen_at_utc | `2026-09-13` | `2026-09-13` | ✅ |
| surfaces count | **5** | **5** | ✅ |
| surface ids | 01,02,03,04,05 | 01,02,03,04,05 | ✅ |
| future / NOT GOLDEN count | **6** | **6** | ✅ |
| future ids | D1..D6 | D1..D6 | ✅ |
| fingerprints identical | — | — | ✅ |

**逐面指紋未變（抽查）**：
- GOLDEN-01 HTML sha16 `fb19c2bdc879dcac`（687,067 B）
- GOLDEN-02 build `FW7iufKj5JrPAz9Kx2SkX` / commit `40c8546e152bf5fad8d7a9d0033f17cab4cbcda8` / `.next/BUILD_ID` sha16 `c32c710cb001b8f0`
- GOLDEN-03 commit `40c8546e…` + `naming_discipline` = rename FORBIDDEN（**未變**）
- GOLDEN-05 repo HEAD `02a17ffef4544adb00b92ce630616a69846b8ee2`
- 5 張截圖 refs / bytes / sha16 **全部未變**

**指定檢查項**：
| # | 要求 | 結果 |
|---|------|------|
| 3 | Golden surfaces count = 5 | ✅ 5 |
| 4 | Future / NOT GOLDEN 未減少 | ✅ 6（未減） |
| 5 | Get Licensed 仍存在 | ✅（D4, PARTIAL） |
| 6 | Earning Opportunities 仍存在 | ✅（D5, PARTIAL） |
| 7 | AI Agent Marketplace 仍 = future / not golden | ✅ `state: NOT_YET_EXISTS` |
| 8 | Provider legacy mapping 未變化 | ✅ `naming_discipline` 原文未動；GOLDEN-03 legacy_urls = 7 |
| 9 | 任何 Golden Surface fingerprint 未變化 | ✅ |

## 8. Secret scan

16 patterns applied（類別敘述，刻意不寫出字面樣式以免掃描器自命中）：

1. Stripe secret key prefix, live / test（各 1）
2. Stripe publishable key prefix, live / test（各 1）
3. Clerk live key variant
4. PEM private-key header
5. AWS access key id
6. GitHub personal token prefix
7. PG connection URI scheme
8. pg pass-file name
9. 大寫 env 賦值形式
10. 小寫 env 賦值形式
11. JWT 形狀前綴
12. Clerk secret 賦值形式
13. Session secret 賦值形式
14. 未遮罩 routable IPv4
15. BOM（UTF-8）

**TOTAL_HITS = 0 · BOM = False · JSON = valid** → **PASS**

> 註：掃描器涵蓋的樣式**字面清單**不寫入交付文件（避免文件本身觸發掃描命中）；樣式定義見掃描腳本本身（不隨本報告交付）。

## 9. Final verdict

**GOLDEN BASELINE V1 NAMING FIX = COMPLETE**

- Canonical machine-readable manifest 已建立並標記 CANONICAL = TRUE
- Legacy alias 保留且明確標記 COMPATIBILITY_ALIAS（不破壞舊引用）
- 所有 Golden 內容 / 指紋 / 語義 **零變更**
- 未動 C1/C2、未 deploy/restart、未寫 DB、未改 route/role/domain/pricing/auth/Framer、未啟 Gate-2

*End of CANONICAL-MANIFEST-NAMING-FIX.md*
