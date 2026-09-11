# GOAA Local Runtime Console (5188) — 架構設計

> **狀態**:設計文檔(V5.2.C-1)。本文件僅為設計,不含部署、不開端口、不碰 secret。
> **節點**:aika-core-01 / AiKa-Box Pro Alpha
> **定位**:AiKa-Box 的本地 Runtime OS 控制台原型 —— 不是 QwenPaw,是量產機的控制台門面。

---

## 1. 定位與原則

aika-core-01 不再只是「靠 SSH 操作的後台 Linux 盒子」,而是擁有一個本地 OS 門面,作為未來 AiKa-Box Pro Alpha 量產機的控制台原型。

> **商業結構定位**:Local Console 是 **AiKa-Box Edge Runtime 的本地主權入口**,**不是 Cloud Dashboard 的複製品**,而是 GOAA Cloud SaaS 的**邊緣執行面**。雲端已有的多節點監控不在本地重做;本地專注雲端給不了的:直連本地 RAG/task、斷網主權、隱私數據本地處理。完整產品結構見 `docs/business/GOAA_BUSINESS_CONSTITUTION_V1.md`。
>

**核心解耦原則(關鍵設計)**:Local Console 與底層 GOAA Worker Daemon / agent.py **完全解耦**。

| 層 | 職責 | 若崩潰 |
|---|---|---|
| **Local Console**(本文件) | 登入、UI、RAG 查詢觸發、task 觸發、task_results 展示、日誌審計、Model/Skill/Agent 設置 | Console 崩潰 → **底層 worker 任務不受影響** |
| **Worker Daemon / task_runner**(已建) | 真實任務執行、Ollama 調用、PG/pgvector 寫入、task_result 產出 | 獨立運行,不依賴 Console |

Console 是「門面」,Worker 是「引擎」。門面壞了,引擎照跑——這是設計的硬要求。

## 3. Tailscale Access Strategy(訪問四階段)

aika-core-01 已綁定 Tailscale IP **100.114.37.90** —— 這是未來 AiKa-Box 的 private mesh identity / 機器編號之一。訪問策略分四階段,**逐階開放,認證先行**:

| 階段 | 綁定 | 用途 | 前提 |
|---|---|---|---|
| **Phase 0 — Localhost** | `127.0.0.1:5188` | 本機開發驗證,只允許本機訪問 | login mock / skeleton 階段(**當前**) |
| **Phase 1 — Tailscale Private** | `100.114.37.90:5188` | 同一 Tailscale private mesh 內訪問 AiKa-Box Console | **真實 Local Auth 完成**(password hash + session + role) |
| **Phase 2 — Optional LAN** | `192.168.1.53:5188` | 家庭/辦公室局域網訪問 | 用戶明確開啟 LAN mode,**不得默認開啟** |
| **Phase 3 — Public** | (預設禁用) | —— | **默認絕不開放公網、不綁 0.0.0.0**;遠程須經 Cloud Dashboard / Tailscale / VPN / Zero Trust |

**硬性規則**:
- login mock 階段**只能用 `127.0.0.1:5188`**
- 真實 Local Auth 完成後**才允許**綁定 `100.114.37.90:5188`
- Tailscale 是 private mesh,但**仍必須認證** —— 100.114.37.90 是 private mesh identity,**不是公網入口**
- 未認證設備**不得訪問** RAG stats / task_results / settings
- Local Console **不是** Cloud Dashboard 的複製品

### Phase 1 實證驗收記錄(已完成)

> 真實 Local Auth(argon2 + session + 三角色)完成後,Console 綁定 `--host 100.114.37.90`(僅 Tailscale 介面,非 0.0.0.0)。已驗收:

| 驗證 | 結果 |
|---|---|
| 本機 `100.114.37.90:5188/health` | 200 |
| 本機未登入 `/rag/stats` | 401 |
| AiKa-1 跨設備 `/health`(經 Tailscale) | 200(回 hostname=aika-core-01,證跨設備可達) |
| AiKa-1 未登入 `/rag/stats` | 401(Tailscale 網內仍擋未認證) |

啟動方式(secret 由 Tao 親手 source,Aika 不碰):
```
set -a; . /etc/goaa/worker_secrets.env; set +a
export CONSOLE_SESSION_KEY=<Tao 親手>
/opt/goaa/venv/bin/uvicorn main:app --host 100.114.37.90 --port 5188
```

意義:Console 從「僅本機可達」→「Tailscale 私網內跨設備可達且需認證」,為 AiKa-Box 量產機門面奠定基礎。Phase 2(LAN)/ Phase 3(公網禁用)維持原策略。

## 4. 端口規劃(修正:5188,非 8088)

| 端口 | 用途 | 狀態 |
|---|---|---|
| **5188** | **GOAA Local Runtime Console** | 正式統一端口 |
| 8088 | QwenPaw / legacy local AI tools | 保留 |
| 11434 | Ollama | 既有(127.0.0.1) |
| 8080 / 5173 / 3000 | (未占用) | 預留 |

aika-core-01 實測(`ss -lntp`):目前只有 `127.0.0.1:11434`(Ollama)占用,5188/8088/8080/5173/3000 均未占用。

**訪問方式**:
- 第一階段:`http://localhost:5188`(僅 127.0.0.1)
- 後續安全確認後:`http://192.168.1.53:5188`(局域網)
- **第一版不綁 0.0.0.0、不開公網**

## 3. 技術棧(零編譯路線)

```
FastAPI + StaticFiles + 原生 HTML5 + TailwindCSS CDN + Vanilla JS
```

**不採用** Node.js / Next.js / Vite 編譯鏈。理由:零編譯、零打包、改完即生效、適合塞進 .deb 安裝包、AiKa-Box 開箱即用、低維護、本地離線可用。

## 4. Local-first Auth(雙層解耦權限)

### Level 1 — Local Auth(本地主權)

- **位置**:本地 SQLite `local_user.db`
- **特性**:斷網 100% 可用,掌控本機硬體與本地 runtime
- **第一版角色**:

| 角色 | 權限 |
|---|---|
| **admin** | 完全本地主權;改 Model/Skill/Agent 三註冊表;觸發 tasks/run;查系統審計日誌 |
| **provider** | 業務運營主體;調用 RAG 檢索;跑指定任務流;查與自己相關的 task results;可選綁雲端賬號查 Credits/Agent 權限 |
| **viewer** | 只讀;查節點狀態、任務歷史結果、部分日誌摘要;**不能觸發 AI 任務** |

### Level 2 — Cloud Auth(可選綁定)

- **定位**:可選綁定 portal.goaa.ai / GOAA Cloud Account
- **用途**:Credits 同步、Provider 權限同步、雲端 Agent 權限解鎖、萬鏡一刻等外部 Agent 權限、將本機 AiKa-Box 註冊為雲端分身
- **第一版**:只做占位,**不做真 OAuth 流程**

## 5. FastAPI API 草案

> **硬性**:所有 API 嚴禁讀取或返回 `/etc/goaa/worker_secrets.env` 內容。secret 只允許後端進程在必要任務執行時使用,不得返回前端。

| Method | Path | 用途 | 安全約束 |
|---|---|---|---|
| GET | `/health` | 控制台狀態、hostname、端口、CPU/mem 摘要、Ollama 可用性 | 不返 secret |
| POST | `/login` | 本地登入(username+password)→ local session token/cookie | 密碼後端驗,不回顯 |
| POST | `/logout` | 退出本地 session | — |
| GET | `/session` | 當前本地身份與 role | — |
| GET | `/workers/status` | agent.py / goaa-worker-agent.service / Ollama / local runtime 狀態 | 不返 secret |
| POST | `/rag/topk` | RAG 檢索驗證(輸入 query + top_k) | **禁返 text_redacted 正文**;只回 id/session_id/msg_id/role/text_len/dim/cosine_distance |
| GET | `/rag/stats` | qwenpaw_memory_chunks count、vector dim min/max、pgvector version | 不返正文 |
| POST | `/tasks/run` | 手動觸發本地任務 | **allowlist only**:exec_topk_query_verify, exec_embed_corpus_full;**禁 shell/subprocess/eval** |
| GET | `/tasks/results` | 渲染 /opt/goaa/task_results/ JSON 歷史為表格 | 不返正文/secret |
| GET | `/tasks/results/{task_id}` | 單個 task result | 不顯 secret/正文 |
| GET | `/settings/models` | Model Registry | — |
| GET | `/settings/skills` | Skill Registry | — |
| GET | `/settings/agents` | Agent Registry | — |
| GET | `/logs/recent` | 近期 runtime log 摘要 | 不返 secret/正文 |

## 6. 頁面結構(左側固定導航 + 右側主工作區)

1. Local Login
2. Dashboard 總覽大盤
3. AI 對話窗
4. RAG 記憶庫
5. 任務中心
6. 模型 Model
7. 技能 Skill
8. 智能體 Agent
9. 節點狀態
10. 系統設置
11. 雲端綁定
12. 日誌審計

**RAG 記憶庫頁(第一版)**:corpus rows、pgvector version、table count、vector dim min/max、top-k query form;結果只顯示 id/role/text_len/distance。

**任務中心頁(第一版)**:task_id / task / worker_id / status / processed / inserted / failed / duration / created_at / result file path;**不顯正文**。

## 7. systemd 部署草案(僅草案,第一版不部署)

```ini
# /etc/systemd/system/goaa-local-console.service
[Unit]
Description=GOAA Local Runtime Console Service
After=network.target

[Service]
Type=simple
User=aika
WorkingDirectory=/opt/goaa/local-console
Environment=PORT=5188
Environment=CONSOLE_ENV=production
ExecStart=/opt/goaa/venv/bin/uvicorn main:app --host 127.0.0.1 --port 5188 --workers 1
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

- 第一版只綁 `127.0.0.1:5188`,不綁 0.0.0.0、不開公網
- **不直接綁定 `100.114.37.90`,除非真實 Local Auth 完成**(見 Tailscale Access Strategy)
- 後續確認本地登入與權限後,再依四階段策略逐步開放

## 8. 安全邊界(第一階段硬性禁令)

1. 不暴露公網
2. 不接真實雲端支付
3. 不接真實萬鏡一刻 API
4. 不輸出 RAG 正文
5. 不讀取/顯示 secret
6. 前端不可訪問 worker_secrets.env
7. 不提供環境變數 dump API
8. 不開放危險 shell 執行
9. 禁 `os.system()`
10. 禁 `subprocess.Popen(..., shell=True)`
11. 不 cat corpus
12. 不 printenv
13. task_result 中的正文不暴露到聊天
14. cloud token 不寫入前端 localStorage
15. 所有密碼輸入框第一版 disabled / placeholder only

**Secret 紀律(全程不變)**:secret 只由 Tao 親手處理,只允許 SET/LEN 類驗證,QwenPaw / Aika / Claude 不接觸 secret 明文。

## 9. V5.2.C → V5.5 Roadmap

| 階段 | 主題 | 內容 |
|---|---|---|
| **V5.2.C-1** | 靜態骨架與控制台架構確立 | FastAPI 門面、本地三角色 login mock、/health、/rag/stats、/rag/topk verify、/tasks/results、/settings/{models,skills,agents}、安全邊界實作、5188 systemd draft |
| **V5.2.C-2** | 數據交互與嵌入任務自動化 | exec_embed_corpus_full + exec_topk_query_verify 接入 Local Task Runner(✅ 已完成)、task_results 可視化、SQLite 存 Model/Skill/Agent registry、Console 觸發 allowlist task |
| **V5.3** | 雲端帳號綁定與本地模型擴展 | Cloud Auth OAuth2 握手、portal.goaa.ai 綁定、Credits/Provider 權限同步、本地 GPU 推理擴展、Local Digital Human Beta |
| **V5.4** | External Agent Integration | 萬鏡一刻/WonderClip 作為 Cloud Digital Human candidate、API/SDK/鑒權/成本/IO 格式查證、Agent Adapter 設計 |
| **V5.5** | Provider Workspace Agent Invocation | Provider 工作台調用 Agent、視頻生成任務、成本與 Credits 審計、雲端/本地 Agent 路由 |

## 10. 本輪修正(6 項,已併入上文設計)

1. **V5.2.C-1 / C-2 邊界統一**:C-1 已完成 = Local Task Runner + exec_embed_corpus_full + exec_topk_query_verify + task_result/log;C-2 待做 = Console 5188 + 網頁觸發 allowlist task + task_results 可視化 + /settings/{models,skills,agents} 只讀展示。
2. **TailwindCSS CDN vs 離線**:開發階段可用 CDN;**生產 / .deb 打包階段必須 vendored local CSS**,不依賴 CDN(否則離線可用性破功)。
3. **Local Auth 密碼安全**:`local_user.db` **不存明文密碼**,用 argon2 或 bcrypt hash;文檔不寫默認密碼;首次啟動透過本地 setup flow 創建 admin。
4. **/tasks/run 參數約束**:不只校驗 task name,**也校驗 params schema**;不允許前端傳任意 corpus_path / target_table;第一版只允許預定義任務配置檔。
5. **/logs/recent 脫敏器**:必經 redaction filter,過濾 password/token/key/secret/DATABASE_URL/SMTP/PGPASSWORD 等模式;默認只返回最近 100 行;不返 worker_secrets.env、corpus 原文、task stdout 全量。
6. **WonderClip 邊界**:API/鑒權/成本/IO 格式查證完成前,只作 Agent Registry **candidate**,不開放正式 Provider 付費調用。

## 11. Patent Continuation Evidence(專利證據鏈關聯)

Local Console 作為「分布式 AI Runtime OS 的本地控制台」,其技術特徵構成未來正式專利(由 GOAA provisional patent specification 延續)的證據之一。需以**技術語言**(非商業話術)記錄:

- 本地 runtime console 與 worker daemon **解耦**(Console 崩潰不影響 task 執行)
- 本地 RAG 檢索**不返正文**的安全隔離機制
- allowlist task runner **阻斷任意 shell 執行**
- `worker_secrets.env` 與前端 console **物理隔離**

詳細證據鏈見 `docs/ip/PATENT_CONTINUATION_EVIDENCE_LEDGER.md`。**不寫死任何未核驗 USPTO 號。**

## 12. .deb Packaging(Console 作為可選組件)

Local Console 應作為 V5.2.C package 的**可選組件**,與 Worker Runtime **分包**:

| Package | 內容 |
|---|---|
| `aika-node-runtime` | worker agent、task runner、embed worker、registry files、task_results/logs 目錄 |
| `aika-local-console`(optional) | FastAPI console、static HTML、local auth、5188 systemd、settings pages |

**分包理由**:Console 出問題不影響 Worker Daemon。詳細升級策略見 `docs/deployment/DEB_UPGRADE_STRATEGY_V4_2_TO_V5_2.md`。

## 13. 補強說明(比原文檔更扎實處)

本設計在原架構基礎上,工程上補強了以下幾點(供實作時參考):

- **解耦的具體保證**:Console 對 Worker 的所有調用,應透過「讀 task_result 檔案」或「呼叫 task_runner 子進程(allowlist)」,而非直接 import worker 內部狀態 —— 確保 Console 進程崩潰不影響正在跑的 task。
- **`/tasks/run` 的 allowlist 實作建議**:不用 `subprocess(shell=True)`,而用 `subprocess.run([venv_python, "task_runner.py", "--task", <allowlist 校驗後的值>, ...], shell=False)`,task 名先比對白名單常數再傳入,杜絕注入。
- **session token**:第一版本地 session 建議用 signed cookie(後端 secret key 從環境讀,不硬編碼),斷網可用。
- **RAG 正文邊界的程式碼級保證**:`/rag/topk` 的 SQL 用 `length(text_redacted)` 而非 `text_redacted`,從查詢層就不取正文(與已實作的 exec_topk_query_verify 一致),前端永遠拿不到正文。
- **C2 預留**:真 RAG 上下文注入(exec_rag_context_fetch)的正文落地/權限/審計/脫敏策略,在 V5.3+ 單獨設計,本文件不涉及。

## 14. 輕量 Workflow 狀態監控(Stepper UI,非節點編輯器)

> **硬性原則**:Local Console 5188 **絕不做完整 ComfyUI Canvas、不做複雜節點編輯器、不做 Cloud Dashboard、不做 billing、不做 Marketplace 管理**。只顯示輕量執行狀態,保持本地主權入口的簡潔。

Console 可提供 **Stepper UI** 展示高層節點進度(輪詢本地 task result 接口),例如:

```
[客戶上傳 ✅] → [OCR ✅] → [LLM 分析 ✅] → [人工審核中 ⚠️] → [等待導出]
```

可顯示欄位:workflow status、current node、node result status、failed node、retry button、review required badge、sync_pending badge、**STATUS_HELD_FOR_REVIEW** 顯示。

**不得暴露**:RAG 正文、secret、原始 ComfyUI workflow JSON、模型路徑、內部執行器參數。

---

*GOAA Local Runtime Console (5188) — 設計文檔 V5.2.C-1 — 先設計不部署*

## 16. C2 記憶補給與 Console 邊界

C2(Aika Memory Context Fetch)第一版**不開放 /rag/chat**(用戶聊天端點)。Console 對 C2 的可見範圍僅限**脫敏統計**(如 filter_stats / context_char_count / selected_chunk_ids 數量),**不回正文、不回拼接 context、不回 Aika prompt**。C2 是 Aika 內部執行記憶補給,正文限同信任域本地執行層內存,不經 Console 前端。/rag/chat 作為後續受控功能單獨設計。詳見 `docs/business/GOAA_C2_DATA_PRIVACY_SPEC.md`。
