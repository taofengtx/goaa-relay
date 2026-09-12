# R4 步驟 1–4｜在 C1 重建 Clerk 後端（取碼／venv／身分權限秘密／unit）

- 輪次：**R4 步驟 1–4**
- 日期：2026-09-12（C1 UTC 06:46–06:48）
- 主機：C1 `goaa-aika-cloud-1`（`do-runtime-anchor`）
- 範圍：**只做步驟 1、2、3、4**
- 明令邊界：**不 `systemctl start`、不 `enable`**；不碰 `goaa` 庫、不動 `goaa-web` / `goaa-router` / `cloudflared` / `ufw` / `DOCKER-USER` / `pg_hba`；不重啟任何既有服務；秘密全程不回顯、不進報告、不上命令列（只進 0600 檔）；IPv4 可路由者切分、sha256 只取前 16；relay 不 force-push。
- 結論：**步驟 1–4 全部完成並逐項驗收通過；未啟動、未 enable。** 唯一需要 Tao 裁定的事項見 §1.4（RECON 樹摘要的**報告瑕疵**，非內容差異）。

---

## 0. 前提覆核（開工前）

| 項 | 期望（R4 RECON） | 實測 | 判定 |
|---|---|---|---|
| C1 Python | 3.12.3 | `Python 3.12.3` | ✅ |
| `/opt/goaa-platform` | **不存在**（R4 目標） | 不存在（本輪建立） | ✅ |
| 埠 3103 | 空閒 | 空閒 | ✅ |
| `docker.service` | 存在（PG 走容器） | `enabled` | ✅ |
| 既有服務 | 不得被打擾 | 見 §4.4 | ✅ |
| 取碼來源 | 本機 worktree `dc64591b`（不從 C2 拷檔） | 一致 | ✅ |

---

## 1. 步驟 1｜取碼到 `/opt/goaa-platform/backend`

### 1.1 程序

- 起點：本機 `work/c2-pg-agent-loop-20260909`，子樹 `services/c2_agent_loop/`，`HEAD=dc64591ba7485aa973f373d5340842297f28b630`，`status` 乾淨。
- 方式：**本機 `tar -cf -` → `ssh` 管線 → C1 端 `tar -xf -`**；**中繼檔不落地本機**。
- 排除：`__pycache__`、`*.pyc`。

### 1.2 驗收（C1 端重算 37 檔 sha256）

| 檢核 | 期望 | 實測 | 判定 |
|---|---|---|---|
| 檔數 | 37 | **37** | ✅ |
| 只在 C2 有 | 0 | **0** | ✅ |
| 只在 C1 有 | 0 | **0** | ✅ |
| 內容不同 | 0 | **0（37/37 逐檔相同）** | ✅ |
| 樹摘要（同一程序兩端各算一次） | 相同 | **`bbb5c0bf45d88da1` == `bbb5c0bf45d88da1`** | ✅ |
| 非預期檔案（pyc/pycache） | 0 | **0** | ✅ |

外加：`migrations/` 落地的 6 檔 + 2 個 rollback 檔名完整（`0001_identity.sql` … `0006_golden_business_session.sql`）。

### 1.3 ⚠️ 落地後的屬主

解壓後所有物件屬主為 **`1000:1000`**（來源 worktree 的 uid/gid）；已於步驟 3b 依令改為 **`root:root 0755`**。

### 1.4 ★ 必須揭露：RECON 樹摘要 `81b17744f8134956` 是**報告瑕疵**，不是內容差異

- R4 RECON §A1b 刊出的樹摘要 `81b17744f8134956`，**無法**由那 37 個檔案的 sha256 清單重現。
- 根因（本輪已定位）：當時的正規化腳本只濾掉 `---FILE_COUNT---` 這行標記，但**把緊接其後的「檔數行 `37`」也一併納入了雜湊輸入**（該行首字元 `3` 落在十六進位字元集內）。⇒ 摘要實際是「37 行清單 **+** 一行 `37`」的雜湊，多算一行。
- 重現驗證：
  - 含該瑕疵行的算法 → **`81b17744f8134956`**（與 RECON 刊出值一致）
  - 乾淨的 37 行算法 → **`bbb5c0bf45d88da1`**
- **實質判定不變**：`r4-cmp.py` 已先證 37/37 逐位元相同，本輪又以 C1 端重算再次確認 **37/37、單邊 0/0、內容不同 0**。即 **`81b17744f8134956` 與 `bbb5c0bf45d88da1` 描述的是同一棵樹**；差異純粹來自一行統計數字被誤納入雜湊輸入。
- 因此本輪的**步驟 1 驗收判準採「兩端用同一支程序各算一次、互相比對」**（`bbb5c0bf45d88da1` == `bbb5c0bf45d88da1`），此判準不受上述瑕疵影響。
- 已在 `reports/2026-09-12/r4-backend/RECON.md` 末尾追加 **## 勘誤** 一節（附錄式補正，**不回改原刊出的數字**，以免遮蔽歷史）。

---

## 2. 步驟 2｜目錄、venv、相依

### 2.1 程序與結果

| 動作 | 結果 |
|---|---|
| 建 `/opt/goaa-platform/{backend,env,private-files}`、`/var/log/goaa-platform` | ✅（**於任何 `useradd` 之前**） |
| `python3 -m venv /opt/goaa-platform/venv` | ✅ |
| `venv/bin/python -V` | **`Python 3.12.3`** |
| `pip --version`（升級前） | `24.0` |
| `pip install --upgrade pip` | ✅ → **`26.2.1`** |
| 相依鎖取得 | 直接自 C2 `cat /root/r4-requirements.lock` 經 ssh 管線，**未經對話** |
| 鎖檔內容 | **23 行**、`sha256[:16] = deea988f19166741` |
| `pip install -r <lock>` | ✅ `install_rc=0` |
| `pip freeze` 行數 | **23** |

### 2.2 驗收：23/23 完全相同

正規化比對（`-`/`_`/`.` 視為同字元、不分大小寫）後：

- 只在鎖檔有：**（無）**
- 只在 C1 有：**（無）**
- 版本不同：**（無）**
- **版本相同數 = 23 / 23 → PASS**

實裝版本（節錄）：`fastapi 0.115.6`、`uvicorn 0.32.1`、`starlette 0.41.3`、`pydantic 2.13.5`、`pydantic_core 2.46.5`、`psycopg 3.2.3`、`psycopg-binary 3.2.3`、`httpx 0.28.1`、`clerk-backend-api 7.0.0`、`PyJWT 2.13.0`、`cryptography 50.0.1`、`bcrypt 4.2.1`、`cffi 2.1.1`、`anyio 4.15.1`、`httpcore 1.0.9`、`h11 0.16.0`、`click 8.5.0`、`idna 3.19`、`certifi 2026.7.22`、`pycparser 3.0`、`annotated-types 0.8.0`、`typing-inspection 0.4.4`、`typing_extensions 4.16.0`。

註：`pip` 本身升級至 26.2.1（C2 為 24.0）；`pip` 不在 `pip freeze` 的 23 行內，不影響 23/23 驗收。

---

## 3. 步驟 3｜身分、目錄權限、秘密

### 3.1 服務帳號

```
goaa-platform:x:997:986::/home/goaa-platform:/usr/sbin/nologin
```

`useradd --system --no-create-home --shell /usr/sbin/nologin`。**uid=997、gid=986。**

### 3.2 目錄與權限

| 路徑 | 屬主:屬群 | 權限 | 設計理由 |
|---|---|---|---|
| `/opt/goaa-platform` | `root:root` | `0755` | 上層 |
| `/opt/goaa-platform/backend` | `root:root` | `0755` | **服務只讀** |
| `/opt/goaa-platform/venv` | `root:root` | `0755` | **服務只讀** |
| `/opt/goaa-platform/env` | `goaa-platform:goaa-platform` | **`0500`** | 服務可讀可穿越、**不可寫** |
| `/opt/goaa-platform/private-files` | `goaa-platform:goaa-platform` | **`0700`** | 執行期唯一可寫資料目錄 |
| `/var/log/goaa-platform` | `goaa-platform:goaa-platform` | **`0750`** | 日誌 |

env 目錄內容：

| 檔案 | 權限 | 位元組 |
|---|---|---|
| `api-3103.env` | `0600 goaa-platform:goaa-platform` | 1103 |
| `app.pgpass` | `0600 goaa-platform:goaa-platform` | 74 |

### 3.3 秘密（**只列名、長度與 sha256 前 16；值全程不回顯、不進報告、不上命令列**）

| 項 | 來源 | 長度 | `sha256[:16]` |
|---|---|---|---|
| DB 應用密碼（寫入 `app.pgpass`） | 既有 `/root/.goaa_platform_app.pw`（R2 建庫時產物） | 32 | `d4ce521d0de0a9bf` |
| `GOAA_C2_SESSION_SECRET` | **本輪全新生成**（`openssl rand -hex 32`） | 64 | `3dff22ace7b1f641` |

`app.pgpass` 為**單行單筆**，欄位數 5，格式 `127.0.0.1:5432:goaa_platform:goaa_c2_app:<密碼>`；密碼字元集檢查通過（純英數）、無 `:` / `\` 需轉義。權限 `0600`。

### 3.4 env 檔

作法：以 C2 `/opt/goaa-test/env/clerk-api-3103.env`（27 鍵、1172 B）為底，**只改令中列舉者、只移除令中列舉者，其餘逐字照抄**。

**改寫（8 鍵）**

| 鍵 | 值 |
|---|---|
| `GOAA_C2_DB_HOST` | `127.0.0.1` |
| `GOAA_C2_DB_PORT` | `5432` |
| `GOAA_C2_DB_NAME` | `goaa_platform` |
| `GOAA_C2_DB_USER` | `goaa_c2_app` |
| `GOAA_C2_DB_PASSFILE` | `/opt/goaa-platform/env/app.pgpass` |
| `GOAA_C2_PRIVATE_FILES_DIR` | `/opt/goaa-platform/private-files` |
| `GOAA_C2_PUBLIC_BASE_URL` | `https://planning.goaa.ai` |
| `GOAA_C2_SESSION_SECRET` | （新生成，見 3.3） |

**移除（2 鍵）**：`GOAA_C2_MIGRATE_USER`、`GOAA_C2_MIGRATE_PASSFILE`（**migrate 角色憑據不進執行期環境**）

**其餘照抄（17 鍵）**：`CLERK_PUBLISHABLE_KEY`、`CLERK_SECRET_KEY`、`CLERK_AUTHORIZED_PARTIES`、`CLERK_ISSUER`、`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`、`GOAA_C2_CLERK_AUTH_ENABLED`、`GOAA_C2_DB_SSLMODE`、`GOAA_C2_ENV`、`GOAA_C2_SESSION_COOKIE`、`GOAA_C2_SESSION_TTL`、`GOAA_C2_DOWNLOAD_TTL`、`GOAA_C2_MAX_UPLOAD_BYTES`、`GOAA_C2_EMAIL_DELIVERY`、`GOAA_C2_STORAGE_LABEL`、`GOAA_C2_SCANNER`、`GOAA_C2_OCR`、`GOAA_C2_PSQL`

**鍵數守恆核對**：27 − 2 = **25**（改寫不增減鍵數）✅

**殘留掃描（值層）**

| 樣式 | 行數 |
|---|---|
| `/opt/goaa-test` | **0** |
| `postgresql@` | **0** |
| `c2test` | **0** |

⇒ 無 C2 路徑、無 C2 專屬 systemd 單元名殘留。

### 3.5 兩項「先查未改」的觀察（**依令不擴大範圍，只報告**）

1. **`GOAA_C2_PSQL`** 之值仍指向 host 上的 `/usr/lib/postgresql/16/bin/psql`（31 字元）。C1 **沒有** host 版 PG16（PG 走容器），故此路徑在 C1 不存在。**但**：`app/` 內**沒有任何**地方呼叫 `psql`（R4 RECON §A8 已證 `app/` 內 0 個外部程序呼叫），只有 `tools/migrate.py` 會用；而 **C1 的 3103 不執行 migration**（migration 已於 R2 在 C1 手動套用完畢）。⇒ **不影響 3103 啟動與運行**，本輪不動它。
2. **`GOAA_C2_ENV=c2-dev`** 為 C2 語境值，令中未列舉 ⇒ **逐字照抄**（未改）。若 Tao 希望改為平台語境（例如 `platform-dev`），請明示；本輪不動。
3. 附帶事實：`GOAA_C2_PUBLIC_BASE_URL` 在 C2 原檔為**空值**（長度 0）；本輪依令填入 `https://planning.goaa.ai`。

---

## 4. 步驟 4｜systemd unit

### 4.1 落盤

- 檔案：`/etc/systemd/system/goaa-platform-api-3103.service`
- 權限：`0644 root:root`、**2627 B**、`sha256[:16] = bc68be75fc5595f4`、**首三 byte `# ␠`（無 BOM）**
- **無 drop-in 目錄**（刻意不建立 `.service.d/`）

### 4.2 藍本與刻意的差異（對照 C2 `goaa-c2-clerk-api-3103.service` + 2 個 drop-in）

| # | C2 原樣 | C1 本 unit | 依據 |
|---|---|---|---|
| 1 | `Requires=postgresql@16-goaa_c2test.service` / `After=… postgresql@16-goaa_c2test.service` | `After=network-online.target docker.service` / `Wants=network-online.target` | C1 的 PG 是 **Docker 容器** `goaa-postgres`，非 host systemd 單元；C1 **不存在** `postgresql@16-goaa_c2test.service` ⇒ 照抄會使 unit 直接載入失敗 |
| 2 | `IPAddressDeny=any` + `IPAddressAllow=localhost` | **不設** | **Tao 已核可之決策**：改靠 host 防火牆 + loopback 綁定 + `ProtectSystem=strict`；IP 白名單註定脆 |
| 3 | drop-in `10-clerk-egress.conf`（放行 api.clerk.com 之 Cloudflare 兩 IP） | **不繼承** | 同 #2；無 `IPAddressDeny=any` 時該 drop-in 亦無意義 |
| 4 | drop-in `20-c2test-private-files.conf`（`ReadWritePaths=/opt/goaa-test/private-files-c2test`） | **不繼承**；於本 unit 直接宣告 `ReadWritePaths=/opt/goaa-platform/private-files /var/log/goaa-platform` | 去除 C2 路徑 |
| 5 | `User/Group=goaa-c2loop`、`WorkingDirectory=/opt/goaa-test/backend-clerk-20260910`、`EnvironmentFile=/opt/goaa-test/env/clerk-api-3103.env`、`ExecStart=/opt/goaa-test/venv3103-clerk/bin/python` | 對應改為 `goaa-platform`、`/opt/goaa-platform/backend`、`/opt/goaa-platform/env/api-3103.env`、`/opt/goaa-platform/venv/bin/python` | 本輪新樹 |
| 6 | `StandardOutput/StandardError=append:/var/log/goaa-c2-clerk-20260910/api-3103.log` | `append:/var/log/goaa-platform/api-3103.log` | 同 #5 |

**逐字保留（與 C2 相同、未動）**：`Type=exec`、`PYTHONDONTWRITEBYTECODE=1`、`PYTHONUNBUFFERED=1`、`--host 127.0.0.1 --port 3103 --no-server-header --log-level info`、`Restart=no`、`TimeoutStopSec=20`、`KillSignal=SIGTERM`，以及整組沙箱化指令（`NoNewPrivileges`、`PrivateTmp`、`PrivateDevices`、`ProtectSystem=strict`、`ProtectHome`、`ProtectKernel*`、`ProtectControlGroups`、`ProtectClock`、`ProtectHostname`、`ProtectProc=invisible`、`ProcSubset=pid`、`RestrictNamespaces`、`RestrictRealtime`、`RestrictSUIDSGID`、`RestrictAddressFamilies=AF_UNIX AF_INET`、`LockPersonality`、`SystemCallArchitectures=native`、`SystemCallFilter=@system-service`、`SystemCallErrorNumber=EPERM`、空 `CapabilityBoundingSet`/`AmbientCapabilities`、`UMask=0077`）。

新增的 `ReadOnlyPaths=/opt/goaa-platform/backend /opt/goaa-platform/venv /opt/goaa-platform/env` 為顯式宣告（`ProtectSystem=strict` 下本就唯讀；此為防誤改的雙保險）。

### 4.3 驗收

| 檢核 | 結果 | 判定 |
|---|---|---|
| `systemd-analyze verify` | `verify_rc=0`（無輸出＝無抱怨） | ✅ |
| `systemctl daemon-reload` | `reload_rc=0` | ✅ |
| `systemctl is-enabled` | **`disabled`** | ✅ |
| `systemctl is-active` | **`inactive`** | ✅ |
| `Loaded:` 行 | `loaded (…/goaa-platform-api-3103.service; disabled; preset: enabled)` | ✅ |
| 是否被 `enable`／`start` | **完全沒有**（本輪未執行 `start`／`enable`／`restart`） | ✅ |
| 埠 3103 | 仍**空閒**、無人監聽 | ✅ |
| `systemctl cat` | 內容與落盤檔一致（見 §4.2） | ✅ |

相依解析（`systemctl show`）：

- `User=goaa-platform`、`Group=goaa-platform`
- `After=` … `docker.service` `network-online.target` …
- `Wants=network-online.target tmp.mount`
- `ExecStart.path=/opt/goaa-platform/venv/bin/python`
- `Requires=` 無 `postgresql@*`（符合預期）

### 4.4 既有服務未受影響（反證）

| 服務 | MainPID | `ActiveEnterTimestamp`（UTC） |
|---|---|---|
| `goaa-router` | **2994296** | **Fri 2026-09-11 06:21:50** |
| `goaa-web` | **2995017** | **Fri 2026-09-11 06:21:57** |
| `cloudflared` | **2111569** | **Thu 2026-09-03 00:27:23** |

三者的 PID 與進入 active 的時間戳**與進入本輪前完全相同** ⇒ 本輪**未重啟任何既有服務**。`daemon-reload` 只重載 unit 定義、不觸碰運行中的程序（上表為證）。

---

## 5. 驗收總表

| 步驟 | 驗收項 | 期望 | 實測 | 判定 |
|---|---|---|---|---|
| 1 | 37 檔逐位元 | 37/37 | 37/37 | ✅ |
| 1 | 單邊檔案 | 0/0 | 0/0 | ✅ |
| 1 | 樹摘要（兩端同程序） | 相等 | `bbb5c0bf45d88da1` = `bbb5c0bf45d88da1` | ✅ |
| 2 | Python | 3.12.3 | 3.12.3 | ✅ |
| 2 | 相依 | 23/23 相同 | 23/23 相同 | ✅ |
| 3 | 服務帳號 | 建立 | `goaa-platform` 997:986 nologin | ✅ |
| 3 | 目錄權限 | backend/venv 只讀；env/priv/log 專屬 | 見 §3.2 | ✅ |
| 3 | 秘密落檔 | 0600、不回顯 | `app.pgpass` 0600、`SESSION_SECRET` 新生成 | ✅ |
| 3 | env 鍵數守恆 | 27−2=25 | 25 | ✅ |
| 3 | C2 殘留路徑 | 0 | 0 | ✅ |
| 4 | unit 落盤 | 0644 root:root、無 BOM | 是 | ✅ |
| 4 | `systemd-analyze verify` | rc=0 | rc=0 | ✅ |
| 4 | 未啟動／未 enable | disabled+inactive | disabled+inactive | ✅ |
| 4 | 既有服務不動 | PID/時間戳不變 | 不變 | ✅ |

---

## 6. 未動清單（本輪完全未觸碰）

`goaa_platform`／`goaa_c2test`／`goaa_c2` 三個資料庫與其任何一列；`goaa-web`、`goaa-router`、`cloudflared`、`goaa-model-router`、`ufw`、`DOCKER-USER`、`pg_hba.conf`、`/etc/cloudflared/config.yml`；`goaa-postgres` 容器與其 data 目錄；C2 的任何檔案；Golden 版本；`/tasks/next/*`（絕不呼叫）。**未新增任何防火牆規則；未改任何埠綁定。**

## 7. 下一步（待 Tao 放行）

**步驟 5**：`systemctl start goaa-platform-api-3103.service`（是否同時 `enable` 請一併示明）。本輪**不執行**。

啟動後建議驗收（供 Tao 勾選）：`is-active=active`；`curl 127.0.0.1:3103/health`；日誌 `/var/log/goaa-platform/api-3103.log` 無 Traceback；`ss -ltnp` 確認**只綁 `127.0.0.1:3103`**（非 `0.0.0.0`）；以 `goaa_c2_app` 走 scram 驗 DB 連通（證據只回報 rc 與錯誤字串，不回顯秘密）。

## 8. 唯一待裁事項

**§1.4**：R4 RECON 刊出的樹摘要 `81b17744f8134956` 係**雜湊輸入多含一行統計數字**所致；同一棵樹的乾淨摘要為 `bbb5c0bf45d88da1`。**內容層面 37/37 相同，已三方一致**（RECON 的逐檔比對、本機、C1 端）。已於 `RECON.md` 追加 **勘誤** 節，**不回改原數字**。請 Tao 確認此處理方式可接受。
