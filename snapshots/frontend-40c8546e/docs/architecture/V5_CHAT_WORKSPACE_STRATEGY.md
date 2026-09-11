\# V5.0 GOAA Chat Workspace Strategy



> \*\*戰略儲備文檔 — 2026-05-17 簽發\*\*

> 一句話原則: \*\*Fork chat UI, build GOAA Runtime OS.\*\*

> 對話 UI 可復用, Runtime OS 必須自建。



\---



\## 0. 文檔定位 (規範 #11 「只增不毀」聲明)



本文檔為 \*\*V5.0 對話框方向戰略儲備\*\*, \*\*不打亂當前 V4.1-Worker 主線\*\*。



\- 當前主線優先級不變: db.py 物理審查 → V4.1-W1 readonly executors → dispatch\_task async → worker\_events / task result → Runtime Truth → Worker 安全邊界

\- 本文檔屬於 docs/architecture/ 層, 與 V4.1-Worker 主線 (docs/roadmap/V4\_1\_Worker\_PLAN.md) \*\*物理隔離\*\*, 互不污染

\- PoC 啟動時機: V4.1-Worker 主線完工後 (預估 2-3 週)



\---



\## 1. 戰略動機 (Why V5.0 Chat Workspace)



\### 1.1 三方共識來源



\- \*\*Tao 師兄\*\*: 統一對話入口, 解 AiKa-1 工作站 MEM 邊緣化問題

\- \*\*ChatGPT\*\*: 多模型路由統一, 避免多客戶端碎片化

\- \*\*Gemini\*\*: 對話即 GOAA 入口, 對話結果可直接觸發 Worker 派發



\### 1.2 規範 #27 三問驗證



| 問 | 答 | 結論 |

|---|---|---|

| 現有系統有沒有? | Claude.ai / Claude Desktop / ChatGPT 客戶端 / QwenPaw 客戶端 | ❌ 碎片化, 每家獨立 UI, 無法接 GOAA Worker 派發 |

| 開源世界有沒有? | LibreChat / OpenWebUI / Big-AGI (MIT/Apache 可商用) | ✅ 對話 UI 部分有, 但 GOAA Worker hooks 都沒有 |

| 必須自建的部分? | Worker dispatch / Task Pool / Credits / Governance / Runtime Truth hooks | ✅ 這些是 GOAA 護城河, 必須自建 |



\*\*結論\*\*: Fork 對話 UI + 自建 GOAA Runtime hooks, 雙線並進。



\### 1.3 規範 #29 反問驗證



> 「強行 fork 對話 UI vs 完全自建」



\- 強行自建消息氣泡 / Markdown 渲染 / 歷史列表 / 移動端適配 = 至少 4-6 週工程, 純重造輪子

\- Fork LibreChat = 1 天 PoC + 1-2 週客製化, 工程資源節省 80%+

\- \*\*裁決\*\*: Fork 對話 UI 是規範 #27 「整合已有」的勝利, 不是規範 #29 「敢創新」的失敗。GOAA 創新點在 Worker / Credits / Governance, 不在對話氣泡。



\---



\## 2. 鐵律 (Iron Rules)



\### 鐵律 1: 不從零自建對話 UI



禁止把工程資源浪費在:

\- 自研消息氣泡

\- 自研多輪對話 UI

\- 自研 Markdown 渲染

\- 自研停止生成按鈕

\- 自研歷史對話列表

\- 自研附件上傳

\- 自研手機端聊天適配

\- 自研基礎模型切換 UI



\*\*除非現成方案經過 PoC 實測後明確不可用。\*\*



\### 鐵律 2: 研發資源 100% 聚焦 GOAA 護城河



研發資源必須投在:

\- Worker 派發 / Task Pool

\- Worker Events 事件流

\- Credits Economy 經濟層

\- Governance 治理層

\- Runtime Truth 真相層

\- Skill / Achievement Marketplace

\- AiKa Box 本地執行

\- GOAA Runtime OS backend hooks



\### 鐵律 3: 主線不容動搖



V4.1-Worker 唯讀工具鏈為當前第一優先。\*\*禁止因調研開源 UI 而延誤主線。\*\*



PoC 啟動條件: V4.1-Worker 主線達到 Phase 4 完工 + 師兄明示放行。



\### 鐵律 4: 拒絕憑印象拍板



LibreChat / OpenWebUI / Big-AGI 最終選型 \*\*必須基於 PoC 實測\*\*, 不准憑印象。



\---



\## 3. 候選方案



| 候選 | License | 多模型 | 部署 | GOAA 適配難度 |

|---|---|---|---|---|

| \*\*LibreChat\*\* | MIT | ✅ OpenAI/Anthropic/Google/local | Docker Compose | 中 (plugin 系統可接 hook) |

| OpenWebUI | MIT | ✅ Ollama 為主, 多 provider | Docker | 中 (函數調用框架成熟) |

| Big-AGI | MIT | ✅ 多 provider | Node.js / Docker | 中低 (UI 漂亮, hook 機制較弱) |

| 其他 | — | — | — | — |



\*\*首推 PoC\*\*: LibreChat (License 友善 + plugin 機制成熟 + 多 provider 完整)

\*\*備胎\*\*: OpenWebUI (Ollama 生態整合度高, 本地優先派可考慮)



\---



\## 4. PoC 14 項嚴苛檢查清單



PoC 1 天驗證, 每項必須有實測結論 (✅ / ❌ / ⚠️ + 證據截圖或日誌):



1\. \*\*License 是否適合商業 fork\*\* — MIT/Apache 可, GPL 不可

2\. \*\*Docker Compose 是否能在 AiKa-2 穩定運行\*\* — 24 小時連續跑無 crash

3\. \*\*RAM / CPU / Disk 消耗\*\* — 基線 idle 與滿載各記錄一次

4\. \*\*是否支持多模型 provider\*\* — OpenAI/Anthropic/DeepSeek/Ollama 都過

5\. \*\*是否支持 custom endpoint\*\* — 能指向 DO Task Router :8080

6\. \*\*是否支持 plugin / tool / MCP 類擴展\*\* — 能掛 GOAA Worker dispatch hook

7\. \*\*是否能接 GOAA Task Router\*\* — Custom endpoint 真實打通

8\. \*\*是否能在對話中觸發 Worker dispatch\*\* — 訊息 → Task Pool → Worker 全鏈路

9\. \*\*是否能展示 worker\_events\*\* — 事件流可在對話框內 stream

10\. \*\*是否能接 Credits / Governance / Runtime Truth\*\* — 三層 API hook 可掛

11\. \*\*是否能保留 GOAA 命名規範\*\* — Client / Provider / Agent / Worker / Skill 可自定義

12\. \*\*是否能保留 GOAA 品牌風格\*\* — 不破壞現有 Dashboard 黃金版 (規範 #11)

13\. \*\*是否會引入過重依賴\*\* — MongoDB / Redis / Meilisearch 等接受度評估

14\. \*\*是否會影響現有 Worker Agent / SSH / Runtime 任務\*\* — 必須 0 影響



\*\*PoC 通過標準\*\*: 14 項至少 12 項 ✅, 不可有任何一項是 deal-breaker 等級的 ❌。



\---



\## 5. PoC 部署拓撲



\### 5.1 宿主選擇: AiKa-2

