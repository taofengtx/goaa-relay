# Round R2 · 階段二 第一段 — 備份（步驟 1）＋ 建角色與庫（步驟 2–3）

- **時間**：步驟 1 於 2026-09-12 05:56 UTC；步驟 2–3 於 06:03–06:05 UTC（= 2026-09-11 22:56–23:05 PDT）
- **主機**：C1 `do-runtime-anchor`（`goaa-aika-cloud-1`，`134.199.227.⟨108⟩`）
- **執行者**：Aika
- **🔴 本輪狀態（06:03 UTC 更新）**：**步驟 1（備份）✅、步驟 2（建角色與庫）✅、步驟 3（驗收 A–E）✅ 全數完成。**
  - 06:03 UTC Tao 正式核准步驟 2–3（原「我核准後才做」為其模板殘留），並補充三點：① 核准此刻生效，先前停手回報為正確；② 密碼檔只列路徑、`/root/mkroles.sql` 用完即刪（含容器內副本）；③ 驗收 A 須確認兩角色**僅有 LOGIN**，若 `\du` 出現任何額外屬性即停手回報、不得自行 `ALTER`。
  - **A 全綠**：五項危險屬性皆 `f`、僅 `rolcanlogin=t` ⇒ 未觸發停手條件。
  - **migration 尚未執行**（依令）—— 階段二第二段（0001–0006 + 驗 schema）等待 Tao 另行下令。
- **紀律**：未碰 `goaa` 庫任何一列；未重啟任何服務；未動 ufw／DOCKER-USER／`pg_hba.conf`；未跑 migration；密碼僅存於 `600` 檔案、**未上命令列／未回顯／未進報告**；IPv4 切分；sha256 前 16。

---

## 步驟 1：備份（✅ 完成，先做且不失敗）

### 1.1 實際執行（逐字）

```bash
TS=$(date -u +%Y%m%d-%H%M%SZ)                    # → 20260912-055621Z
mkdir -p /root/backups; chmod 700 /root/backups

docker exec goaa-postgres pg_dump -U goaa -Fc -d goaa -f /tmp/goaa-$TS.dump
docker cp goaa-postgres:/tmp/goaa-$TS.dump /root/backups/
docker exec goaa-postgres sh -c "rm -f /tmp/goaa-$TS.dump"

docker exec goaa-postgres pg_dumpall -U goaa --roles-only --no-role-passwords \
  > /root/backups/roles-$TS.sql
chmod 600 /root/backups/*
```

**返回碼**：`pg_dump_rc=0`、`docker_cp_rc=0`、`rm_rc=0`、`dumpall_rc=0` —— **四步全 0，無失敗**。

### 1.2 驗收輸出（全部貼出）

**① `ls -l /root/backups/`**
```
total 4936
-rw------- 1 root root 5049925 Sep 12 05:56 goaa-20260912-055621Z.dump
-rw------- 1 root root     640 Sep 12 05:56 roles-20260912-055621Z.sql
```

**② `sha256sum /root/backups/goaa-20260912-055621Z.dump | cut -c1-16`**
```
defab73054b178f2
```

**③ 主機是否有 `pg_restore`？**
```
HOST_HAS_NO_PG_RESTORE
```
⇒ 依 Tao 指令的備援路徑，改用容器內 `pg_restore`（見 ④）。

**④ 容器內 `pg_restore --list /tmp/v.dump | wc -l`**
```
283
```
⇒ **283 個物件（> 0 ✅）**，與自訂格式（`-Fc`）相符。驗證後已清掉容器內 `/tmp/v.dump`。

**⑤ `wc -l /root/backups/roles-20260912-055621Z.sql`**
```
35
```

**⑥ 權限（補查）**
```
drwx------ 2 root root 4096 Sep 12 05:56 /root/backups
/root/backups/goaa-20260912-055621Z.dump       5049925 bytes 600
/root/backups/roles-20260912-055621Z.sql           640 bytes 600
```
⇒ 目錄 `700`、兩檔 `600` **✅**。

**⑦ 現有 `goaa` 庫未受影響（即時抽查）**
```
docker exec goaa-postgres psql -U goaa -tAc "select count(*) from pg_database where datname='goaa';"
→ 1
```

### 1.3 備份物件彙總

| 項目 | 值 |
|---|---|
| 備份檔（自訂格式，可 `pg_restore`） | `/root/backups/goaa-20260912-055621Z.dump` |
| 大小 | **5,049,925 bytes**（≈ 4.8 MB；`-Fc` 已壓縮，來源 `goaa` 庫 18 MB） |
| sha256 前16 | **`defab73054b178f2`** |
| 物件數（`pg_restore --list`） | **283** |
| 角色清單（`--roles-only --no-role-passwords`） | `/root/backups/roles-20260912-055621Z.sql`（640 bytes、35 行） |
| 權限 | 目錄 700；檔案 600 |
| `TS` | `20260912-055621Z` |

> **備註**：Tao 指令預期「dump 大小應為十幾 MB 量級」，實測 **4.8 MB** —— 因為 `-Fc` 為**壓縮**格式，而來源庫僅 18 MB。**物件數 283 > 0** 才是有效性判據，該項通過。

---

---

## 步驟 2：建角色與庫（✅ 完成，2026-09-12 06:03 UTC）

### 2.1 執行方式（逐字）

```bash
umask 077
openssl rand -base64 32 | tr -d '\n=+/' | cut -c1-32 > /root/.goaa_platform_migrate.pw
openssl rand -base64 32 | tr -d '\n=+/' | cut -c1-32 > /root/.goaa_platform_app.pw
chmod 600 /root/.goaa_platform_migrate.pw /root/.goaa_platform_app.pw

# SQL 以檔案產生（printf；密碼值只存在於檔案，不經命令列）
printf '%s\n' \
 "CREATE ROLE goaa_c2_migrate LOGIN PASSWORD '<migrate-pw>';" \
 "CREATE ROLE goaa_c2_app     LOGIN PASSWORD '<app-pw>';" \
 "CREATE DATABASE goaa_platform OWNER goaa_c2_migrate ENCODING 'UTF8' LC_COLLATE 'en_US.utf8' LC_CTYPE 'en_US.utf8' TEMPLATE template0;" \
 "REVOKE ALL ON DATABASE goaa_platform FROM PUBLIC;" \
 "GRANT CONNECT ON DATABASE goaa_platform TO goaa_c2_migrate, goaa_c2_app;" \
 > /root/mkroles.sql
chmod 600 /root/mkroles.sql

docker cp /root/mkroles.sql goaa-postgres:/tmp/mkroles.sql
docker exec goaa-postgres psql -U goaa -d postgres -v ON_ERROR_STOP=1 -f /tmp/mkroles.sql
```

- 連線一律 **`-U goaa`**（C1 超管是 `goaa`，**不是** `postgres` —— R1 階段一 K1 教訓）。
- 輸出管線加 `sed "s/PASSWORD '[^']*'/PASSWORD '<redacted>'/g"`：即使 psql 回顯失敗語句，**密碼也不會進日誌或報告**。
- **不加 `-1`**（`CREATE DATABASE` 不可在交易區塊內）。

### 2.2 密碼產生（**只報長度／檔指紋，永不報值**）

```
migrate_pw_chars=32
app_pw_chars=32
migrate_pw_file_sha16=d865da8ac7acb3d8
app_pw_file_sha16=d2af56823eebe2bf
-rw------- 1 root root 33 Sep 12 06:03 /root/.goaa_platform_app.pw
-rw------- 1 root root 33 Sep 12 06:03 /root/.goaa_platform_migrate.pw
```

（`33 bytes` = 32 字元 + 換行；權限 `600`。抽樣後剔除 `\n = + /`，實際長度恰為 32。）

### 2.3 SQL 檔與執行結果

`/root/mkroles.sql`：**5 行 / 5 條語句**、sha256 前16 `b8fa45d13b56cad5`、權限 `600`。

```
CREATE ROLE
CREATE ROLE
CREATE DATABASE
REVOKE
GRANT
psql_pipeline_rc=0
```

⇒ **五條語句全部成功**，`ON_ERROR_STOP=1` 下 `psql` 返回碼 0，**無 ERROR、無 WARNING**。

### 2.4 清理（依 Tao 第 2 點：用完即刪，含容器內副本）

```
mkroles_host_exists=NO
mkroles_container_exists=NO
```

⇒ 主機 `/root/mkroles.sql` 與容器 `/tmp/mkroles.sql` **皆已刪除**；密碼檔保留（供後續 migration 使用）。

---

## 步驟 3：驗收 A–E（✅ 全數通過）

### A. 角色屬性 —— **僅有 LOGIN**

**A1 `\du goaa_c2_*`**
```
        List of roles
    Role name    | Attributes
-----------------+------------
 goaa_c2_app     |
 goaa_c2_migrate |
```

**A2 精確布林屬性（`pg_roles`）**
```
goaa_c2_app|f|f|f|f|f|t
goaa_c2_migrate|f|f|f|f|f|t
(欄序: rolname|rolsuper|rolcreatedb|rolcreaterole|rolreplication|rolbypassrls|rolcanlogin)
```

⇒ **SUPERUSER=❌、CREATEDB=❌、CREATEROLE=❌、REPLICATION=❌、BYPASSRLS=❌、CANLOGIN=✅** —— 完全符合 Tao 第 3 點要求。**無任何額外屬性 ⇒ 未觸發停手條件，未執行任何 `ALTER`。**

**A3 角色成員關係**（`pg_auth_members`）→ **0**：兩角色皆非任何角色之成員，亦未被授予任何角色。

### B. 新庫屬性（與舊庫一致）

```
goaa|goaa|UTF8|en_US.utf8|en_US.utf8
goaa_platform|goaa_c2_migrate|UTF8|en_US.utf8|en_US.utf8
(欄序: datname|owner|encoding|collate|ctype)
```

⇒ `goaa_platform`：owner **`goaa_c2_migrate`**、encoding **UTF8**、collate/ctype **`en_US.utf8`** —— 與現有 `goaa` **完全一致** ✅。

### C. 連線驗證（PGPASSFILE；密碼不上命令列）

| 測項 | 內容 | 結果 |
|---|---|---|
| C1 | `goaa_c2_migrate` → `select current_user, current_database();` | `goaa_c2_migrate\|goaa_platform`（rc=0） ✅ |
| C2 | `goaa_c2_app` → 同上 | `goaa_c2_app\|goaa_platform`（rc=0） ✅ |
| **C4** | 同上兩角色，改走**非 loopback**（scram 路徑） | 兩者皆成功 ✅ |
| **C5** | 同 C4 但**故意用錯密碼** | `FATAL: password authentication failed for user "goaa_c2_app"` ✅ 被拒 |
| **C6** | 無關角色 `goaa_rag` 連 `goaa_platform` | `FATAL: permission denied for database "goaa_platform"` / `User does not have CONNECT privilege.` ✅ |
| **C7** | 對照：`goaa_rag` 連舊庫 `goaa` | `goaa_rag\|goaa` ✅（未受影響） |

> **🔴 本輪一次設計失誤（誠實記錄，已追查並修正）**
> 初版 C3 用 **loopback** 做「無密碼應被拒」負向測試 → 竟回傳 `1`（連上了）。追查後確認**容器 `pg_hba.conf` 對 loopback 為 `trust`**（**既有設定，本輪未改動**）：
> ```
> local   all             all                          trust
> host    all             all   127.0.0.⟨1⟩/32           trust
> host    all             all   ::1/128                trust
> local   replication     all                          trust
> host    replication     all   127.0.0.⟨1⟩/32           trust
> host    replication     all   ::1/128                trust
> host    all             all   all                    scram-sha-256
> ```
> ⇒ 結論：**loopback 免密是既有環境事實**（連舊庫 `goaa` 亦然），故 **C1/C2 只能證明「角色可連新庫」，不能證明「密碼正確」**。遂改以**容器網橋位址 `172.17.0.⟨2⟩`（非 loopback ⇒ 命中最後一條 `scram-sha-256`）**＋ PGPASSFILE 重做，得出 **C4（正確密碼可連）／C5（錯密碼被拒）／C6（無權角色被拒）**。
> **附帶安全觀察（非本輪造成，僅報告，未改動）**：容器內任何程序（含 `docker exec` 的 root）可經 loopback 以**任意角色免密登入**；對外路徑（經發布埠，來源為 `172.17.0.⟨1⟩` 非 loopback）仍強制 `scram-sha-256`，且 D0.2 已收掉公網 5432。**是否收緊 loopback 為 `scram`／`peer`，請 Tao 裁示。**

### D. 現有 `goaa` 庫毫髮無傷

```
D1  datname='goaa' 計數                        → 1
D2  goaa 的 public 表數                        → 45
D3  goaa 的 public 表清單（45 張）：
    agent_documents agent_memory agents audit_log conversation_memory credits
    goaa_agent_knowledge_chunks goaa_agent_knowledge_docs goaa_agent_leads
    goaa_agent_preferences goaa_agent_profiles goaa_agent_skills goaa_agent_tokens
    goaa_email_send_log goaa_order_* (14) goaa_planning_sessions goaa_verify_codes
    messages models nodes projects qwenpaw_memory_chunks sessions tasks
    tool_invocations tools v4_agents
D4  systemctl is-active goaa-router            → active
D5  curl 127.0.0.⟨1⟩:8080/health               → http_code=200
```

⇒ 表數 **45**、`goaa-router` **active**、健康檢查 **200** ✅。

### E. 新庫此刻為空

```
information_schema.tables where table_schema='public'  → 0
pg_namespace（非系統 schema）                          → public
```

⇒ **0 張表**、schema 僅 `public`（migration 尚未執行）✅。

### 收尾檢查

```
pw_files_perm:      -rw------- 1 root root 33 /root/.goaa_platform_{app,migrate}.pw
容器內殘留臨時檔:     NONE
host 上 .pgp_* 殘留:  0
```

---

## 回滾

**本輪無需回滾**（`goaa` 庫全程未被觸碰；`goaa_platform` 為全新物件、尚未跑 migration）。如需完全撤除：

```sql
DROP DATABASE goaa_platform;
DROP ROLE goaa_c2_app;
DROP ROLE goaa_c2_migrate;
```

備份檔保留於 `/root/backups/`（見步驟 1），可完整還原 `goaa`。

## 密碼檔路徑（**僅路徑，永不列值**）

| 檔案 | 用途 | 權限 | 檔案指紋 sha256 前16 |
|---|---|---|---|
| `/root/.goaa_platform_migrate.pw` | `goaa_c2_migrate` 密碼 | 600 | `d865da8ac7acb3d8` |
| `/root/.goaa_platform_app.pw` | `goaa_c2_app` 密碼 | 600 | `d2af56823eebe2bf` |

> 指紋僅供「檔案未遭更動」比對，**無法還原密碼**。第二段（migration）將以 `PGPASSFILE`（`/opt/goaa-test/env/*.pgpass`，屆時建立）取用，全程不上命令列、不回顯。

---

## 紀律自證（步驟 2–3）

- ✅ 只 `ssh do-runtime-anchor`（C1）；**未連 C2／C3**。
- ✅ **未跑任何 migration**（依令）；`goaa_platform` 表數仍為 **0**。
- ✅ 未改 env／設定檔；**未重啟任何服務**（`goaa-router` 仍 active、`/health` 200）。
- ✅ 未動 ufw／DOCKER-USER／`pg_hba.conf`。
- ✅ 未讀寫 `goaa` 庫任何一列（僅 `information_schema` 計數與表名）。
- ✅ 密碼：`openssl rand` 產生後只寫入 `600` 檔案；**未上命令列、未進 `ps`、未回顯、未進報告**；psql 輸出另加 redaction。
- ✅ `/root/mkroles.sql` 與容器內副本**用完即刪**（已驗 `NO / NO`）。
- ✅ 臨時 PGPASSFILE（`/root/.pgp_*`、容器 `/tmp/.pgp_*`）全部清除（`host_left=0`、`CONTAINER_CLEAN`）。
- ✅ IPv4 一律切分書寫：`172.17.0.⟨2⟩`、`172.17.0.⟨1⟩`、`127.0.0.⟨1⟩`、`134.199.227.⟨108⟩`。

---

## 秘密掃描（推送前，須為 0 命中）

樣式（切分書寫）：`"sk_" + "live_"`、`"sk_" + "test_"`、`"BEGIN " + "PRIVATE KEY"`、`"AK" + "IA"`、`"gh" + "p_"`、`"postgres" + ":" + "//"`、`"PGPASSWORD" + "="`、`"pass" + "word="`、`"ey" + "J"`。

**掃描回報（推送前，逐樣式統計）**：

| 樣式（切分書寫） | 命中 |
|---|---|
| `"sk_" + "live_"`（Stripe live 前綴） | **0** |
| `"sk_" + "test_"`（Stripe test 前綴） | **0** |
| `"BEGIN " + "PRIVATE KEY"`（PEM 私鑰標頭） | **0** |
| `"AK" + "IA"`（AWS access key 前綴） | **0** |
| `"gh" + "p_"`（GitHub PAT 前綴） | **0** |
| `"postgres" + ":" + "//"`（Postgres URI scheme） | **0** |
| `"PGPASSWORD" + "="`（密碼環境變數賦值） | **0** |
| `"pass" + "word="`（密碼賦值） | **0** |
| `"ey" + "J"`（JWT 形態前綴） | **0** |
| **合計** | **0** ✅ |

**未切分 IPv4 掃描**：**0 命中**（本報告 IPv4 一律以 `⟨N⟩` 切分書寫，如 `134.199.227.⟨108⟩`、`172.17.0.⟨2⟩`）。

**檔案完整性**：`REPORT.md` = **12,835 bytes**、`sha256` 前16 = `2ef242c695ba1d20`、首三 byte = `b'# R'`（**無 BOM**）。

**relay main sha**：`cf7fba0ca846350a0e962df6bdc3123fb24cb3c7`
（本報告**內容** commit；其後的子提交僅用於寫入本行與上方掃描回報，未改動任何驗收結論。）
