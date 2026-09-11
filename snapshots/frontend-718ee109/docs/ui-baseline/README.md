# UI Golden Baseline — 黃金快照

> **定位**：GOAA.AI Dashboard 的「真相基準」物理位置。
> 任何 AI（Claude / Gemini / GPT 等）或人類動 `components/GoaaDashboard.jsx` 前，
> **必須**先與此黃金版 `diff` 比對，確認 working copy 沒有意外偏離。

## 📁 目錄結構

```
docs/ui-baseline/
├── GoaaDashboard.golden.jsx      # 當前黃金版完整副本
├── CHANGELOG.md                  # 黃金版升級歷史
└── README.md                     # 本文件（使用守則）
```

## 🔄 工作流（強制）

### 動 jsx 前

```powershell
# 1. 確認 working copy 與黃金版一致
fc components\GoaaDashboard.jsx docs\ui-baseline\GoaaDashboard.golden.jsx

# 若有差異 → 立刻停手，先搞清楚為什麼偏離（可能上一次部署沒走完整流程）
# 若無差異 → 安全動手
```

### 動 jsx 後（部署成功 + 師兄驗收後）

```powershell
# 2. 升級黃金版（只能在師兄明確指示下）
Copy-Item components\GoaaDashboard.jsx docs\ui-baseline\GoaaDashboard.golden.jsx -Force

# 3. 在 CHANGELOG.md 加一條記錄
# 格式：
# ## [yyyy-mm-dd] commit <hash> — 簡述
# - Lines: NNN  MD5: xxxxxxxx
# - 改動: ...
```

## 🛡️ 鎖定規則（必須遵守）

| 規則 | 說明 |
|------|------|
| **R1** | AI（Claude / AiKa / Gemini / GPT）**不能自己**升級黃金版 |
| **R2** | 只有 Tao（師兄）明確說 **"升級黃金版"** 或 **"今天 goaa.ai 開發工作結束"** 時，才升級 |
| **R3** | 每次升級必須在 CHANGELOG.md 寫明 commit hash + 變更摘要 + 新版 Lines/MD5 |
| **R4** | 若黃金版與線上 `components/GoaaDashboard.jsx` 不一致，**以黃金版為準**，working copy 須回滾 |
| **R5** | 黃金版本身不能直接修改，只能透過 `Copy-Item` 從已驗收的 working copy 覆蓋 |

## 🔗 配套規範

本黃金快照機制與以下既有規範配套運作：

- **規範 #11 Baseline Freeze** — 「只增不毀」原則（邏輯約束）
- **規範 #12 Fingerprint Check** — 部署前 MD5 校驗（傳輸保障）
- **規範 #13 Session Handoff** — 窗口接續時讀真相基準（接續保障）
- **規範 #14 UI Golden Baseline** — 黃金版物理位置（本機制）

四規合力 = 整檔覆蓋風險近似歸零。

## 💡 為何需要黃金快照

**單純有規範文字還不夠**，必須有個**可 `diff` 的物理對照物**：

| 缺它之前 | 有它之後 |
|---------|---------|
| 「線上 jsx 是什麼狀態？」需 git log + cat | `fc components\GoaaDashboard.jsx docs\ui-baseline\GoaaDashboard.golden.jsx` 一行 |
| 「我這次改動有沒有破壞？」靠記憶 | `diff` 看到哪幾行不一樣，一目了然 |
| 「黃金版」概念抽象 | 黃金版 = 某個 .jsx 檔案，存在 disk 上，可手動打開看 |

## 📜 歷史

詳見 [CHANGELOG.md](./CHANGELOG.md)
