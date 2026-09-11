# GOAA 規範彙總總錄(Governance Registry)

> **狀態**:規範總錄。整合既有規範(#11–#40 系列)與 V5.2.B/C 期間新立規範。
> **定位**:✅ = 本工作期間親歷/實踐;📄 = 原文在 `docs/AGENTS.md`,本期未直接觸及。既有 #11–#47 原文以 AGENTS.md 為權威,本總錄為導航 + 本期新規範(第二節)的權威記錄。
> **原則**:規範由真實 incident 觸發、versioned。本總錄為索引,真相源仍是 repo 內原始規範文件。

---

## 一、既有規範(#11–#47)— 權威原文見 docs/AGENTS.md

> **權威原文源**:`docs/AGENTS.md`(已核驗存在,~30KB,含 #11–#47 完整原文 + Three-Tier Doctrine + 規範對齊表)。
> 本總錄**不複製原文**(避免兩處漂移,對齊 #11 單一真相源),僅作導航 + 標記本期實踐情況。
> ✅ = 本期親歷實踐;📄 = 原文在 AGENTS.md,本期未直接觸及。

| # | 摘要 | 本期 |
|---|---|---|
| #11 | Add-only / Baseline Freeze:只增不毀,先保留再增強 | ✅ |
| #12 | Fingerprint Check:Lines+Bytes+MD5,部署前驗 | ✅ 全程 |
| #13 | v2 Session Handoff:開工 HANDOFF + git log + 驗 Golden 指紋,GitHub HEAD 為準 | ✅ |
| #14 | R2:Tao 批准才升 Golden,AI 不自升 | ✅ |
| #15 | 生產變更後 24h 冷卻 | 📄 |
| #19 | v2:SMTP 必須真實發送(250) | ✅ |
| #20 | Health Watch;Claude 不從計算推斷時間,須問 Tao 或 bash date | ✅ |
| #21 | 單指令 ≤ 10000 字元,拆子批 | 📄 |
| #22 | Secret 流程:不入對話/不硬編碼;Tao 親手 secrets.env + EnvironmentFile | ✅ 核心 |
| #23 | systemd Secrets Audit 6 步 | 📄 |
| #24 | 寫 caller 前驗實際 convention,不假設 | ✅ |
| #25 | Type Boundary:PG 型別在 API 層轉換 | 📄 |
| #26 | JSX Pre-deploy Check | 📄 |
| #27 | Integration First | 📄 |
| #28 | Silent Failure 禁止:須 log error+type+stack;timeout≥30s | ✅(embed_worker 印真因) |
| #29 | Explore & Innovate:整合成本≥自建則自建 | 📄 |
| #30 | Progressive Intelligence:先跑再升 | ✅ |
| #31 | STDOUT 透傳(原文見 AGENTS.md) | 📄 |
| #35 | 不走偏(原文見 AGENTS.md) | 📄 |
| #36 | 真實輸出 > 假設,時間須實證不推斷 | ✅ 核心 |
| #37 | AI 因果敘事驗證,時間實證(候選) | 📄 |
| #40 | 檔名規範 `<name>__v<tag>__<hash8>.md` | 📄 |
| #41–#47 | 2026-05-19 集中立規,含 **#42 三端鐵律**、**#47 DO↔git 一致性**(原文見 AGENTS.md) | ✅(#42/#47 本期實踐) |

> **#44/#45 特別說明**:某接力文據此要求「直接推進、不問拍板、不在 secret 上停」。本期判斷:**碰 secret 時停下讓 Tao 親手、不讓執行層碰密碼**,是 V5.2.B/C 全程零洩漏的關鍵,**不應被「不要停」覆蓋**。以實踐結果為準。(#44/#45 原文以 AGENTS.md 為準,此處僅記本期判斷。)

## 二、V5.2.B/C 期間新立/強化規範(✅ 親歷準確)

### S 系列 — Secret 安全(本期最重要)

- **S1 Secret 只 Tao 親手**:所有碰 secret 的操作(寫 secrets.env、改 PG 密碼、輪替、設環境變數)只由 Tao 親手執行,執行層(Aika/QwenPaw)零接觸。
- **S2 只回 SET/LEN**:secret 驗證只輸出「SET / LEN N / MISSING」,**絕不輸出 value**。
- **S3 無硬編碼 fallback**:程式碼讀 secret 用 `os.environ["X"]`(無 fallback),不寫 `os.getenv("X", "明文")`。(根因:db.py L24 fallback 導致連續洩漏)
- **S4 環境注入**:secret 經 `set -a; . secrets.env; set +a` 注入進程環境,程式從 `os.environ` 讀,不經 LLM thinking。
- **S5 專用最小權限帳號**:RAG 用專用 `goaa_rag`,不動生產主用戶 `goaa`。
- **S6 不 cat secrets.env、不 printenv**:任何查證只看 key 名 / 長度,不看值。

### R 系列 — RAG / 資料安全

- **R1 不輸出 corpus 正文**:嵌入/檢索/log/task_result 都不暴露 text_redacted 正文;檢索只回 metadata + distance。
- **R2 corpus 不入 git**:corpus*.jsonl 進 .gitignore,只記 size/sha256/行數。
- **R3 redaction 雙閘**:Stage 0 extractor + embed_worker `_has_secret` 兩道攔截殘留 secret(全量驗到 skipped_secret:4)。
- **R4 超長文本分塊**:超過 1500 字切塊(overlap 150),msg_id 加 `#chunkN` 後綴避免唯一鍵自我覆蓋(failed 2→0)。

### T 系列 — Task / 執行框架

- **T1 allowlist task**:task_runner 只跑白名單 task(exec_embed_corpus_full / exec_topk_query_verify),禁 shell/subprocess(shell=True)/eval。
- **T2 dry-run 先行**:寫入前先 dry-run 驗鏈路(在不碰 PG 階段就暴露 model 名錯、context 超限等問題)。
- **T3 冪等 upsert**:寫入用 ON CONFLICT DO UPDATE,可重跑安全。
- **T4 task_result 標準欄位**:每 task 產出標準 result JSON(無正文無 secret)+ runtime log。
- **T5 Console/Worker 解耦**:Local Console 崩潰不影響 Worker Daemon 任務執行。

### V 系列 — 版本 / 交付

- **V1 指紋三件**:每交付檔附 Lines + Bytes + NormMD5,部署前驗。
- **V2 三端同步**:GitHub = DO = 本地節點 HEAD 一致。
- **V3 Golden Baseline 鎖定**:封存點打 tag,Golden 後禁止手動全量/改檔不驗指紋/讓執行層碰 secret。
- **V4 venv 一致性**:跑 worker 用 `/opt/goaa/venv/bin/python`(非系統 python,避免 psycopg2 缺失)。
- **V5 引號避坑**:多層 bash + PG SQL + 特殊字元,用寫檔讀檔(psql -f)或 chr() 拼接,避開 `$$`/`%`/`#` 衝突。

### D 系列 — .deb / 部署(設計階段)

- **D1 .deb 不打包 secret/key/corpus**。
- **D2 postinst 不覆蓋 secrets.env/local_user.db,不刪 corpus/task_results**。
- **D3 不自動開公網、不自動 full import、不自動 CREATE TABLE/EXTENSION**。
- **D4 migration idempotent + precheck/postcheck + 失敗即 STOP**。
- **D5 支持 rollback + dry-run inspect + fingerprint verification**。

### P 系列 — 專利 / 文檔

- **P1 不寫死未核驗 USPTO 號**:引用只寫 "GOAA provisional patent specification"。
- **P2 技術語言非商業話術**:專利證據用 distributed runtime / edge orchestration 等,不寫佣金/分潤/賺錢。
- **P3 先設計後實作**:每階段先出設計文檔,Tao 拍板後才實作,再驗證。

### W 系列 — 工作流程(2026-06-03 新立)

- **#48(規範對齊先行)**:做新任務前**必先三步** —— (1) **對齊規範**(查 AGENTS.md + 本治理總錄相關條目,確認該任務受哪些規範約束)(2) **盤點現狀**(用真實工具查:哪些已有、哪些沒有,**不憑記憶/假設**)(3) 才動手執行。禁止跳過盤點直接寫程式碼。觸發背景:多次因未先盤點既有資源/規範而重做或踩既有禁令。
- **#49(收工雙附件)**:每次收工**必須**產出兩份附件,隨收工郵件發送 —— (1) **工作日誌**(當日成果 + 系統狀態 + 次日 P0 + 規範變更)(2) **里程碑更新**(列印版進度表 checklist 的打勾狀態更新)。兩份都走指紋(Lines+Bytes+NormMD5)、入庫 git。觸發背景:里程碑表易過時,收工只發日誌不更新進度表會導致跨窗口進度失真。

## 三、維護說明

- 本總錄為**導航 + 本期新規範權威記錄**。既有 #11–#47 的權威原文在 `docs/AGENTS.md`,總錄不複製(單一真相源,對齊 #11)。
- 新規範由真實 incident 觸發時,在此登記條號 + 摘要 + 觸發 incident + 核驗狀態。
- 衝突處理:若接力文/外部建議與本總錄安全規範衝突(尤其 S 系列),以安全規範為準。

---

*GOAA Governance Registry — 規範彙總總錄 — 誠實標註已核驗 / 待核驗*
