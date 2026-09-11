# GOAA.AI Development Roadmap v1.3

**簽發**: 2026-06-14 (基於 v1.2 + 主開發遷移至 aika-core-01 完成)
**上一版本**: GOAA_DEV_ROADMAP__v1_2__a9118de0.md (2026-06-12)
**戰略鐵律**: 先有生產線 → 再有工作台 → 先 Provider 現金流 → 再 Client 平台 → 先內部 Worker → 再開放開發者
**最高戰略鐵律 (7d49efd)**: Worker 負責生產能力；Provider 負責接單、跟單、調用專業 Skill 並交付服務；Client 負責提出需求、查看進度、與 Provider 互動並使用生活化 Skill。
**v1.3 變更摘要**: 主開發遷移至 aika-core-01 完成（PR #2 合併、Node 22 / ESLint / build 驗證通過、aika-1 凍結為只讀遷移源）；HANDOFF V2.2 同步更新；本版記錄遷移後基線。

---

## 1. 文件定位與事實層級

本文件為 GOAA.AI 開發進度的**正式權威記錄**。事實層級：

1. **Runtime Truth** — 實時節點/服務狀態（每次開工重新盤點）
2. **Git Truth** — GitHub main HEAD + migration 分支記錄
3. **Documentation Truth** — 本文件 + HANDOFF.md + DevLog
4. **Migration History** — migration/aika-core-01 分支（完整遷移記錄）

不一致時：Runtime > Git > Documentation > Memory。

---

## 2. 當前權威基線

```text
GitHub main:                a5e8c6eaafeaae9a90022d6bd2fc655acfbd6adb
aika-core-01 local main:    a5e8c6e（已 fast-forward 同步 GitHub）
遷移歷史分支:                 migration/aika-core-01 @ 9793cdc（已推送、PR #2 已合併）
Runtime repo:               /opt/goaa/repo @ 53f599f（未隨遷移修改）

主要開發工具鏈:
  Node.js:  v22.22.3（nvm 用戶級安裝）
  npm:      10.9.8
  ESLint:   8.57.1 + eslint-config-next@14.2.35
  Next.js:  14.2.35
  npm ci:   通過
  lint:     通過（0 errors, 2 warnings）
  build:    通過（8 routes, 10 static pages）
```

---

## 3. 已完成里程碑 (2026-05-16 → 06-14)

| ☑ | 日期 | 戰績 | Commit |
|:-:|:----|:----|:----|
| ☑ | 5/16 | 戰略憲法 V1.0 + Marketing v1 + UI 黃金版 | c909c3b / 76b7980 |
| ☑ | 5/17 | V5.0 Chat Workspace + HANDOFF.md V1.0 | 32ea682 / c9f289b |
| ☑ | 5/19 | 三端最終鐵律全線部署 | 7d49efd |
| ☑ | 6/9 | C 線 Console AI Workspace 閉環 + B 線 Node Health 真實化 | 908ec2a |
| ☑ | 6/10 | D 線 Cloud Binding 核心鏈路通 + db.py 密碼移除 | deebcc6 |
| ☑ | 6/12 | 三端盤點 + F 線真實定位 | 9a7b580 |
| ☑ | 6/13 | systemd 埠競爭根治 + 5188 指揮入口盤點 | 1d67bd6 |
| ☑ | 6/14 | **主開發遷移至 aika-core-01（PR #2）** | d8ec7d0→9793cdc |
| ☑ | 6/14 | Node 22 / ESLint / build 驗證 + HANDOFF V2.2 + Roadmap v1.3 | 本次文檔 |

---

## 4. 六節點拓撲

```text
雲端（DO）:
  - do-cloud-1（134.199.227.108）— git repo (/opt/goaa) + PostgreSQL + OpenClaw
  - do-cloud-2
  - do-cloud-3

本地:
  - aika-core-01 — 唯一主開發節點（RTX 4060, Tailscale 100.114.37.90, Node 22, 全工具鏈就緒）
  - aika-1 — 凍結為只讀歷史遷移源（不再承擔新代碼/文檔寫入、Git 主操作、build/lint/deploy）
  - aika-2
```

備註：在線狀態必須在每次「開工」時重新盤點，不以本文件靜態記錄為準。

---

## 5. 主開發遷移狀態

```text
✅ aika-core-01 已成為唯一主開發入口
✅ GitHub SSH 已可用
✅ Node.js 22 / npm 已安裝且驗證
✅ npm ci / lint / build 三項全部通過
✅ PR #2 已合併到 main（2026-06-14）
✅ aika-1 已凍結為只讀歷史遷移源
✅ .env.production 已停止追蹤（補 .env.production.example 模板 + .gitignore 規則）
✅ F-lite 2a historical milestone 已還原並納入 Git
✅ HANDOFF.md 已更新為 V2.2（全域事實修正 + 新增遷移章節）
✅ Roadmap v1.3 已創建（本文件）
✅ 遷移分支 migration/aika-core-01 本地保留，未刪除
✅ Runtime repo (/opt/goaa) 未隨遷移變更
```

---

## 6. Worker Runtime OS 主線

### 6.1 Phase 1 — Worker V5.0 內部生產線

| 子項 | 狀態 | 說明 |
|:-----|:----:|:----|
| B 線 節點數據真實化 | ✅ | B1-B5 完整 |
| C 線 AI 工作區接 LLM | ✅ | C.1 + D.1 端到端 |
| D 線 Cloud Binding | 🟡 | 鏈路通，閉環缺口：Router 實時狀態未完整 PG 化 |
| P1.4 dispatch_task async | ✅ | auto_dispatcher_loop 已在生產運行 |
| P1.2.0 tasks 表 PG 持久化 | 🟡 | Router dispatch 已寫 PG，task_upsert() 4 個 hook 未全接入 |
| F 線 安全執行層 (F-lite) | ⬜ | 設計階段：形式化 Router 風險引擎 + 審批 UI + 節點白名單 |

### 6.2 執行層定位

```text
QwenPaw:     過渡備用執行器（位於 aika-core-01，Tailscale 內網訪問）
              真正目標是 Worker Runtime OS 具備 Shell Capability
OpenClaw:    位於 DO，用於 SaaS 執行能力
              後續通過 FastAPI 調用
ComfyUI:     candidate，不替代 GOAA Runtime OS
CosyVoice:   candidate
```

### 6.3 安全邊界

```text
Provider Review Hold:     保留
外部 API 成本網閘:          保留
Run in Cloud / Run on My AiKa-Box / Auto Route:  保留為執行目標三模
secret 分域:              持續執行（Tao 親手，Aika 不碰 secret）
```

---

## 7. OpenClaw / QwenPaw 執行層定位

```text
現狀:
  - QwenPaw = 本地過渡備用執行器（已綁定 Tailscale IPv4，本機可達）
  - OpenClaw = DO 上的 SaaS 執行能力（通過 FastAPI 調用）

目標:
  - Worker Runtime OS 具備完整 Shell Capability
  - 定義 FastAPI → OpenClaw 執行契約
  - QwenPaw 保持為備用執行層
  - DeepSeek 主模型 + 本地 Ollama (qwen2.5:3b) 斷網備用
```

---

## 8. 當前 P0 / P1 任務

### P0 — 必須完成

| # | 任務 | 狀態 |
|:-:|:----|:----|
| P0-1 | 更新並固定開工協議（每次開工先盤點 6 節點 + GitHub） | ⬜ |
| P0-2 | 每次開工先盤點 6 節點在線狀態 | ⬜ |
| P0-3 | 對齊 GitHub / Runtime / Documentation Truth | 🟡 |
| P0-4 | 完成 Worker Runtime OS Shell Capability | ⬜ |
| P0-5 | 定義 FastAPI → OpenClaw 執行契約 | ⬜ |
| P0-6 | 處理 HANDOFF 與 Runtime repo 的版本漂移 | 🟡 |

### P1 — 應盡快完成

| # | 任務 | 狀態 |
|:-:|:----|:----|
| P1-1 | QwenPaw 備用運行策略（何時啟用、何時停用） | ⬜ |
| P1-2 | DeepSeek 主模型與本地 Ollama 斷網備用策略 | ⬜ |
| P1-3 | 修復兩個 lint warning（useEffect deps + <img>→<Image>） | ⬜ |
| P1-4 | 確定 Vercel 與 Aika commit identity 的長期策略 | ⬜ |
| P1-5 | Roadmap / DevLog 自動交叉索引 | ⬜ |

---

## 9. 安全與審批邊界

```text
- secret 只 Tao 親手（pgpass、console.env、worker_secrets.env、admin 密碼）
- Aika 不碰 secret（Aika 會把它接觸的東西印出來）
- 5 級風險定級（P3-P7）：LOW / MEDIUM / HIGH / CRITICAL / BLOCK
- HIGH 以上須審批彈窗（5188 審批 UI，後續）
- 安全執行層（F-lite）設計中：白名單 + 危險命令黑名單 + secret 攔截
- .env / .env.production / secrets.env 已加入 .gitignore
- .env.production 已從 Git 追蹤中移除
```

---

## 10. 下一窗口開工流程

收到「開工」指令後，Aika / Claude 必須執行：

```text
1. 盤點 6 個節點狀態（health check + systemd is-active）
2. 檢查 GitHub main HEAD（git fetch + log，不憑記憶）
3. 對齊 HANDOFF、Roadmap、DevLog（不一致時列出差異，請 Tao 拍板）
4. 列出當天任務（從 Tao 指令 + Roadmap P0/P1 提取）
5. 逐項拆解為可執行步驟
6. 由 Aika 執行（非 secret 操作）
7. 高風險操作（涉及生產部署、secret、DO 連線）必須等待 Tao 明確批准
8. 每一步完成後驗證 Runtime / Git / Documentation Truth
```

---

**戰略順序鐵律 (永不調亂)**

```
1. Phase 1 Worker V5.0 內部生產線跑通  ← F 線執行中
2. Phase 2 官網 V2.0 Framer 落地      ← 並行
3. Phase 3 Provider AI 工作台 MVP (Insurance Priority A)
4. Phase 4 AiKa Box Software Kit 出貨
5. Phase 5 高頻流程資產化 → Skill Marketplace
6. Phase 5+ Client Plus + Worker Developer 開放
```

---

**進度表簽發**: 2026-06-14 (PT)
**v1.3 變更**: 主開發遷移完成 / PR #2 合併 / aika-1 凍結 / Node 22 + ESLint + build 驗證 / HANDOFF V2.2 / 新增章節 2(基線) 5(遷移狀態) 7(執行層定位) 8(P0/P1) 10(開工流程)
**上一版本**: v1.2 (2026-06-12, commit f9aa7f1)
**規範遵守**: #11 / #12 / #15 / #19 v2 / #20 / #28 / #36 v2 / #40 / #42 / 三端最終鐵律 (凌駕所有)
