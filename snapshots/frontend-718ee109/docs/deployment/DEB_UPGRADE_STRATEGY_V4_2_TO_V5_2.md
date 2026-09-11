# GOAA / AiKa-Box .deb Upgrade Strategy (V4.2 → V5.2)

> **狀態**:設計文檔。僅設計,不動 .deb 實包、不跑 migration、不部署。
> **背景**:既有 `aika-node_1.0.5.deb` 太輕(bootstrap 殼,postinst 依賴遠程腳本),不適合長期作 AiKa-Box Pro Alpha 生產安裝包。V5.2.C 後需支持 V4.2 → V5.2 平滑升級。

---

## 1. 核心目標

1. 支持舊版節點從 V4.2 / V4.5 升級到 V5.2
2. **不覆蓋 secrets**
3. **不刪除 corpus**
4. **不刪除 task_results**
5. 不破壞 systemd
6. **不誤開公網端口**
7. **不自動執行 full import**
8. 不自動接入真實雲端 Agent
9. **不把 WonderClip API key 打包進 .deb**
10. **支持 rollback**

## 2. 包版本線

| Package | 內容 |
|---|---|
| **V4.2** | 基礎 worker agent、heartbeat、router registration |
| **V4.5** | aika-core-01 / AiKa-Box Pro Alpha 支持、limited sudo allowlist、worker registry 對齊 |
| **V5.1** | LLM dispatch task 支持、task execution result 回報 |
| **V5.2** | embed_worker.py、task_runner.py、exec_embed_corpus_full、exec_topk_query_verify、pgvector client 依賴、Ollama model check、local runtime logs、task_results 目錄 |
| **V5.2.C** | GOAA Local Runtime Console 5188、Model/Skill/Agent Registry skeleton、local_user.db setup flow、settings pages、RAG stats/top-k verify UI、local console systemd |

## 3. 安裝包目錄標準

```
/opt/goaa/
  workers/
    agent.py
    embed_worker.py
    task_runner.py
    topk_query.py
  tasks/
    exec_embed_corpus_full.json
    exec_topk_query_verify.json
  task_results/
  logs/
  local-console/
    main.py
    static/
    templates/
    local_user.db
  registry/
    models.json
    skills.json
    agents.json
  migrations/

/etc/goaa/
  worker_secrets.env       # 永不打包真實值
  local-console.env        # 只放 console 非敏感配置
  version                  # 當前 installed runtime version

/etc/systemd/system/
  goaa-worker-agent.service
  goaa-local-console.service
```

## 4. 分包策略(Console 與 Worker 分開)

| Package | 內容 |
|---|---|
| `aika-node-runtime` | worker agent、task runner、embed worker、registry files、task_results/logs 目錄 |
| `aika-local-console`(optional) | FastAPI console、static HTML、local auth、5188 systemd、settings pages |

**理由**:Console 出問題不影響 Worker Daemon。(後續可合併為 `aika-box-runtime`,但當前建議分包。)

## 5. maintainer scripts 策略

### postinst 必須:
1. 創建目錄,但**不覆蓋已有目錄**
2. 安裝或升級代碼文件
3. 若 `/etc/goaa/worker_secrets.env` 已存在,**絕不覆蓋**
4. 若 `local_user.db` 已存在,**絕不覆蓋**
5. 若 `task_results` 已存在,**絕不刪除**
6. 若 `corpus_all.jsonl` 已存在,**絕不刪除**
7. `systemctl daemon-reload`
8. enable 但**不強制 start 高風險服務**,除非 Tao 明確允許
9. 5188 第一版只綁 `127.0.0.1`
10. **不自動運行 full import**
11. **不自動 CREATE TABLE**
12. **不自動 CREATE EXTENSION**
13. **不自動接 WonderClip API**
14. **不打印 secrets**
15. 寫入 install log:`/var/log/goaa-install.log`

### prerm 必須:
1. stop service 前先記錄狀態
2. **不刪除** worker_secrets.env / local_user.db / task_results / logs / corpus
3. 只移除 package-owned files

### postrm 必須:
1. purge 時也保護 secrets,**除非用戶明確 `--purge-goaa-secrets`**
2. 默認不刪 `/etc/goaa`
3. 默認不刪 `/opt/goaa/task_results`
4. 默認不刪 `/opt/goaa/logs`

## 6. 遷移腳本(/opt/goaa/migrations/)

```
001_v4_2_to_v4_5_worker_registry.sh
002_v4_5_to_v5_1_dispatch_task.sh
003_v5_1_to_v5_2_rag_embedding.sh
004_v5_2_to_v5_2c_local_console.sh
```

每個 migration 要求:
1. **idempotent,可重複執行**
2. 寫 migration log
3. 有 precheck
4. 有 postcheck
5. **不觸碰 secret 明文**
6. **不自動跑高風險任務**
7. **失敗時 STOP**,不繼續後續 migration
8. 記錄當前版本到 `/etc/goaa/version`

## 7. .deb 安全升級硬性規則

1. .deb 包不含真實 secret
2. .deb 包不含真實 cloud API key
3. .deb 包不含 WonderClip credential
4. .deb 包不含客戶 corpus 原文
5. .deb 包不自動上傳日誌
6. .deb 包不自動打開公網端口
7. .deb 包不自動執行 task full import
8. .deb 包不自動覆蓋用戶配置
9. .deb 包必須支持 dry-run inspect
10. .deb 包必須支持 fingerprint verification
11. 每次發布必須輸出:SHA256、MD5、package file list、maintainer scripts review

## 8. Release Notes 要求

每次 .deb 發布生成 `docs/releases/RELEASE_NOTES_vX.Y.Z.md`,必含:

版本號 / 日期 / 變更摘要 / 新增技術能力 / 修改文件 / 新增 systemd service / 新增端口 / 目錄變化 / 數據庫變化 / 是否需手動遷移 / 是否觸碰 secret / 是否需 Tao 手動輸入 / 是否影響現有 worker / rollback 方法 / package hash / maintainer scripts 摘要

## 9. Rollback 原則

- 升級前記錄當前 `/etc/goaa/version`
- 保留前一版 package(可 `dpkg -i` 回裝)
- secrets / corpus / task_results / local_user.db 跨版本保留,rollback 不丟資料
- migration 失敗即 STOP,不留半殘狀態(對齊建表時 ROLLBACK 經驗)

---

*GOAA .deb Upgrade Strategy V4.2 → V5.2 — 設計文檔,不動實包,無 secret*
