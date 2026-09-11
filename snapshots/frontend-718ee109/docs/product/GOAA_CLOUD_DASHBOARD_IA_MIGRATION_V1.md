# GOAA Cloud Dashboard IA Migration Design V1 (Phase B)

> **狀態**: 設計文檔(Phase B)。僅設計, 不寫代碼、不改 GoaaDashboard.jsx、不部署、不碰 secret。
> **依據**: docs/product/GOAA_PRODUCT_NAVIGATION_IA_V1.md(五端 IA V1.1)
> **目標**: 在不動黃金版前提下, 設計雲端 Command Center 從現狀 6-tab 遷移到 IA 目標 13 項的 schema 與漸進方案。

---

## 1. 真實現狀(盤點自 DO 真實代碼, 非憑記憶)

GoaaDashboard.jsx = **774 行單頁 tab 式導航**(非多頁 app)。golden 基線與 production 一致(皆 774 行)。

現狀 6 tab:
| tab id | label | icon |
|---|---|---|
| dispatch | AI調度 | ti-cpu |
| taskpool | 任務池 | ti-list-check |
| workers | 節點監控 | ti-server |
| finance | 損益審計 | ti-report-money |
| logs | 日誌歷史 | ti-terminal-2 |
| settings | 系統設置 | ti-settings |

---

## 2. 現狀 → IA 目標導航對照(Command Center 13 項)

| 現狀 6 tab | IA 目標 | 動作 | 備註 |
|---|---|---|---|
| dispatch(AI調度) | 總覽 Dashboard + AI Workspace | 拆分 | 調度對話 → AI Workspace; 概覽數字 → 總覽 |
| taskpool(任務池) | Cloud Task Command Center | 改名擴充 | 加 execution_target 三模路由 |
| workers(節點監控) | AiKa-Box Fleet + Worker Network | 拆分 | 節點卡片 → Fleet; 開發端 → Worker Network |
| finance(損益審計) | Billing/Usage + Audit Logs | 拆分 | 財務 → Billing; 審計 → Audit Logs |
| logs(日誌歷史) | Audit Logs | 併入 | 與 finance 審計合併 |
| settings(系統設置) | System Settings | 保留 | 基本不變 |
| — | Workflow Graphs | 新增 | Coming Soon 佔位 |
| — | Provider Workspace | 新增 | Coming Soon 佔位 |
| — | Skill Marketplace | 新增 | Coming Soon 佔位 |
| — | Achievement Marketplace | 新增 | Coming Soon 佔位 |
| — | AI Agents | 新增 | Coming Soon 佔位 |

對照原則:現有 6 tab 的功能**只增不毀**(規範 #11)——拆分/改名時保留原有內容, 新增項先佔位。

---

## 3. 新導航 schema(設計用, 這輪不寫代碼)

建議結構(未來代碼參考, 非當前實作):
```
nav = [
  { id: "overview",     label: "總覽 Dashboard",          group: "core",        status: "active" },
  { id: "ai_workspace", label: "AI 工作區",               group: "core",        status: "active" },
  { id: "task_center",  label: "Cloud Task Command Center", group: "ops",       status: "active" },
  { id: "workflow",     label: "Workflow Graphs",         group: "ops",         status: "coming_soon" },
  { id: "provider_ws",  label: "Provider Workspace",      group: "business",    status: "coming_soon" },
  { id: "worker_net",   label: "Worker Network",          group: "business",    status: "coming_soon" },
  { id: "fleet",        label: "AiKa-Box Fleet",          group: "infra",       status: "active" },
  { id: "skill_market", label: "Skill Marketplace",       group: "marketplace", status: "coming_soon" },
  { id: "achv_market",  label: "Achievement Marketplace", group: "marketplace", status: "coming_soon" },
  { id: "ai_agents",    label: "AI Agents",               group: "marketplace", status: "coming_soon" },
  { id: "audit",        label: "Audit Logs",              group: "governance",  status: "active" },
  { id: "billing",      label: "Billing / Usage",         group: "governance",  status: "active" },
  { id: "settings",     label: "System Settings",         group: "governance",  status: "active" },
]
```
- `status: coming_soon` 的項顯示 Coming Soon 佔位面板, 不是一上來全功能(誠實邊界)
- group 用於側欄分組(core/ops/business/infra/marketplace/governance)

---

## 4. Golden Backup 策略(動黃金版前必做, 規範 #11/#12)

任何修改 GoaaDashboard.jsx 前:
1. `cp GoaaDashboard.jsx GoaaDashboard.golden.<date>.jsx`(日期版備份)
2. 記錄當前 MD5 + 行數(774 行基線)
3. 修改後新版獨立 MD5, 與 golden 並存
4. 出問題可隨時 rollback 到 golden
5. golden 基線文件不刪(只增不毀)

---

## 5. 漸進遷移階段(不一次全改, 規範 #30)

- **B-1**: 側欄擴展為 13 項結構(新增項先 Coming Soon 佔位)+ 現有 6 tab 內容原樣保留映射到新 id
- **B-2**: dispatch 拆分為 總覽 + AI Workspace(AI Workspace 對齊五端統一組件, Phase D 預備)
- **B-3**: workers 拆分為 Fleet + Worker Network
- **B-4**: finance 拆分為 Billing + Audit
- **B-5**: 逐個把 Coming Soon 項替換為真實功能(各自獨立, 須 Tao 確認)

每階段:先 golden backup → 改 → diff → 審計 → 驗證 → 可 rollback。

---

## 6. 誠實邊界

- 本文檔為**設計**, 未修改任何代碼, 未動黃金版。
- 新增導航項(Workflow/Provider/Marketplace/AI Agents)當前為 **Coming Soon 佔位**, 非已上線完整功能。
- 雲端 dashboard 中金額/節點數/任務數為 mock 示例, 非真實運營數據。
- ComfyUI/Antigravity/WonderClip/Video Agent/Developer Agent 為 candidate, 非 production available, 非 Provider paid callable。
- 進入代碼階段(Phase E)前須 Tao 單獨確認 + branch/diff/審計/rollback。

---

*GOAA Cloud Dashboard IA Migration V1 — Phase B 設計 — 不動黃金版, 漸進遷移, 只增不毀*
