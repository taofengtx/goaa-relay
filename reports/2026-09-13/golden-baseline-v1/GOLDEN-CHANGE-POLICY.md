# GOLDEN CHANGE POLICY — GOAA + Aika-Box Golden Baseline

- **Applies to:** GOLDEN-01 … GOLDEN-05（見 `GOLDEN-BASELINE-V1.md`）
- **Version:** 1.0 · 2026-09-13
- **Owner of approval:** Tao（人類）

---

## 1. 五條鐵律

1. **只增不減（Additive-only）** — 新能力以新增路由 / 新增欄位 / 新增 feature flag 落地。
2. **兼容優先（Backward-compatible-first）** — 舊 URL、舊 API 回應欄位、舊角色名必須保留可用。
3. **修改前必先說明影響 + 獲 Tao 審批** — 無審批 = 不動。
4. **刪除 / rename / 破壞性 DB migration / route removal / role semantic change = 單獨批准項。**
5. **暫時不用的功能優先 HIDE，不 DELETE。**

---

## 2. 變更分類與要求

| 類別 | 例子 | 需要 | 可否回滾要求 |
|------|------|------|--------------|
| **A. 加性（Additive）** | 新路由、新頁面、新旗標（預設 off/HIDE） | 影響評估 + Tao 審批 | 必須有回滾點 |
| **B. 修改（Modify）** | 改文案、改 UI、改非破壞性 API 回應（僅新增欄位） | 影響評估 + Tao 審批 | 必須有回滾點 |
| **C. 破壞性（Destructive）** | 刪除路由、rename、破壞性 migration、role semantic change | **單獨 Tao 批准** + 遷移計畫 + 兼容 alias + 回滾演練 | 強制 |
| **D. 緊急（Incident）** | 生產中斷修復 | 可先行動，**事後 24h 內**補影響報告 + 更新 Manifest | 強制 |

**禁止（永不）：**
- 未經批准改 Golden 語義（如把 agent 直接改名 provider 而不留 alias）。
- 就地覆寫 release 目錄（`/opt/goaa-frontend/current` 必須走新 release dir + symlink 切換）。
- 在無 DB dump 的情況下執行破壞性 migration。

---

## 3. 每次變更的固定流程（Checklist）

1. **影響評估**：受影響 surface / 路由 / API / DB 表 / 角色 / 依賴（Clerk、Stripe、3103）。
2. **回滾點確認**：新 release dir、DB dump、relay snapshot 之一必須存在且可回復。
3. **Tao 審批**（書面）。
4. **執行**（單獨事件；一次一個變更）。
5. **驗證**：公開 GET / 登入路徑 / 關鍵 API 冒煙。
6. **更新 Golden Registry**：更新指紋（URL / commit / build id / sha256）、版本號 +0.1。
7. **記錄**：relay 報告 + 記憶。

---

## 4. 各 Golden 面的「回滾錨點」

| ID | 回滾錨點 | 型態 |
|----|----------|------|
| GOLDEN-01 | Framer 版本歷史 | 外部 CMS |
| GOLDEN-02/03/04 | `/opt/goaa-frontend/releases/76af718b0568992c900b72d1aff5aad2516046dc`（前一個 release）+ 22 個 releases | 目錄 + symlink |
| GOLDEN-05 | repo HEAD `02a17ffe`（D0 本地） | git ref |

---

## 5. 版本號規則

- **v1.0** = 本凍結（2026-09-13）。
- 任何 **A/B** 類變更 → **v1.x**（小版本）；更新 Registry 指紋。
- 任何 **C** 類變更 → **v2.0**（大版本）；需單獨批准 + 兼容層。
- Golden 面**新增** → **GOLDEN-06**、`GOLDEN-07`…（編號只增，不重用）。

---

*End of GOLDEN-CHANGE-POLICY.md*
