# Round R2 · 階段二 第二段 — 套用 migration 0001–0006 ＋ 驗 schema

- **時間**：2026-09-12 06:23 UTC（= 2026-09-11 23:23 PDT）
- **主機**：C1 `do-runtime-anchor`（`goaa-aika-cloud-1`，`134.199.227.⟨108⟩`）；來源檔取自 C2 `do-c2`（`143.198.224.⟨71⟩`）
- **執行者**：Aika
- **🔴 結果**：**步驟 2 六檔全數 rc=0；步驟 3 驗收 A–H 全數通過**（其中 **D 有 6 處差異，已根因定位，見 §D**）。
- **紀律**：SQL **一字未改**；未碰 `goaa` 庫；未重啟任何服務；未動 ufw／DOCKER-USER／`pg_hba.conf`；密碼全程走 `PGPASSFILE`（未上命令列、未回顯、未進報告）。

---

## 0. 前提覆核（唯讀；皆成立）

| 前提 | 實測 | 結果 |
|---|---|---|
| `goaa_platform` 已存在、0 表 | 庫存在（`pg_database` = 1）、public 表數 **0** | ✅ |
| 角色僅 LOGIN | `goaa_c2_app\|f\|f\|f\|f\|f\|t`、`goaa_c2_migrate\|f\|f\|f\|f\|f\|t` | ✅ |
| 舊庫 `goaa` 未受影響 | public 表數 **45** | ✅ |
| `goaa-router` / 健康檢查 | `active`、`/health` = **200** | ✅ |
| 密碼檔存在 | `/root/.goaa_platform_{migrate,app}.pw`（600） | ✅ |
| 目標目錄 | `drwx------ 2 root root /root/mig`（700） | ✅ |

---

## 步驟 1：取檔並校驗（✅ 完成）

### 1.1 來源（C2 canonical 樹）

`ls -l /opt/goaa-test/backend-clerk-20260910/migrations/`
```
-rw-r--r-- 1 goaa-c2loop goaa-c2loop 4229 Sep 10 02:54 0001_identity.sql
-rw-r--r-- 1 goaa-c2loop goaa-c2loop 6832 Sep 10 02:54 0002_applications.sql
-rw-r--r-- 1 goaa-c2loop goaa-c2loop 1351 Sep 10 02:54 0003_audit_append_only.sql
-rw-r--r-- 1 goaa-c2loop goaa-c2loop 1655 Sep 10 02:56 0004_role_grant_guard.sql
-rw-r--r-- 1 goaa-c2loop goaa-c2loop 7139 Sep 10 06:10 0005_user_identities.sql
-rw-r--r-- 1 goaa-c2loop goaa-c2loop 9349 Sep 11 07:43 0006_golden_business_session.sql
drwxr-xr-x 2 goaa-c2loop goaa-c2loop 4096 Sep 11 07:43 rollback
```
（`rollback/` 為既有子目錄，本輪**未取用、未讀取**。）

**唯一性確認**：`find /opt/goaa-test -maxdepth 6 -name '0006_golden_business_session.sql'` → **僅 1 筆**（即 canonical 樹）。目錄內 `*.sql` 恰為 6 檔，無其他 000X 變體。

### 1.2 傳輸方式

**tar 管線**（C2 打包 → 本機中轉 → C1 解包；**不落地本機磁碟**）：

```bash
ssh do-runtime-anchor 'mkdir -p /root/mig && chmod 700 /root/mig'
ssh do-c2 "tar -C /opt/goaa-test/backend-clerk-20260910/migrations -cf - \
    0001_identity.sql 0002_applications.sql 0003_audit_append_only.sql \
    0004_role_grant_guard.sql 0005_user_identities.sql 0006_golden_business_session.sql" \
  | ssh do-runtime-anchor "tar -C /root/mig -xf -"
```
**結果**：`C1_DIR_OK` → `TRANSFER_OK` → `transfer_pipeline_rc=0`。

### 1.3 C1 端落地清單 `ls -l /root/mig/`

```
total 44
-rw-r--r-- 1 995 986 4229 Sep 10 02:54 0001_identity.sql
-rw-r--r-- 1 995 986 6832 Sep 10 02:54 0002_applications.sql
-rw-r--r-- 1 995 986 1351 Sep 10 02:54 0003_audit_append_only.sql
-rw-r--r-- 1 995 986 1655 Sep 10 02:56 0004_role_grant_guard.sql
-rw-r--r-- 1 995 986 7139 Sep 10 06:10 0005_user_identities.sql
-rw-r--r-- 1 995 986 9349 Sep 11 07:43 0006_golden_business_session.sql
```
（`995:986` 為 tar 保留之 C2 數值 uid/gid；內容與 mtime 完整保留。）

**檔案數 = 6** ✅（恰為 6 檔，無多餘檔）。

### 1.4 ★ 校驗對照表（sha256 前 16 位 ＋ 行數）

| 檔案 | sha16（取得） | 行數 | sha16（期望） | 行數 | 結果 |
|---|---|---|---|---|---|
| `0001_identity.sql` | `16c2c1dc6fc9841b` | 89 | `16c2c1dc6fc9841b` | 89 | **OK** ✅ |
| `0002_applications.sql` | `e0ff4d2e8ad59ef4` | 130 | `e0ff4d2e8ad59ef4` | 130 | **OK** ✅ |
| `0003_audit_append_only.sql` | `af2d5f9d58caf35b` | 34 | `af2d5f9d58caf35b` | 34 | **OK** ✅ |
| `0004_role_grant_guard.sql` | `fbf2690542bc813b` | 43 | `fbf2690542bc813b` | 43 | **OK** ✅ |
| `0005_user_identities.sql` | `cb26ebaff7a64cd4` | 145 | `cb26ebaff7a64cd4` | 145 | **OK** ✅ |
| `0006_golden_business_session.sql` | `59d6383d743caef9` | 166 | `59d6383d743caef9` | 166 | **OK** ✅ |

**`VERIFY_RC=0`** —— **6/6 完全一致，零不符 ⇒ 未觸發停手條件。**

同時，C2 來源端**獨立量測**結果與上表完全相同（傳輸前後各校驗一次，排除傳輸損毀）：
```
0001_identity.sql                 16c2c1dc6fc9841b 89
0002_applications.sql             e0ff4d2e8ad59ef4 130
0003_audit_append_only.sql        af2d5f9d58caf35b 34
0004_role_grant_guard.sql         fbf2690542bc813b 43
0005_user_identities.sql          cb26ebaff7a64cd4 145
0006_golden_business_session.sql  59d6383d743caef9 166
```

### 1.5 編碼抽查（首三 byte）

6 檔首三 byte 皆為 `2d 2d 20`（即 `-- `，SQL 註解開頭）⇒ **無 UTF-8 BOM、無異常編碼**。

---

---

## 步驟 2：逐檔套用（✅ 6/6 rc=0）

### 2.1 前置

```bash
CIP=172.17.0.⟨2⟩            # 非 loopback ⇒ 命中 pg_hba 最後一條 scram-sha-256
# 密碼以 PGPASSFILE 送入（只引用路徑；值不列）
docker cp /root/mig                goaa-postgres:/tmp/mig
docker cp /root/.pgp_m             goaa-postgres:/tmp/.pgp_m && chmod 600
```

**連線路徑自檢（順帶再驗一次密碼路徑）**
```
goaa_c2_migrate|goaa_platform|172.17.0.⟨2⟩
selfcheck_rc=0
```
（原輸出之伺服器位址為未切分寫法；此處依報告版面紀律以 `⟨⟩` 切分末段，其餘逐字未改。）
⇒ `current_user = session_user = goaa_c2_migrate`、`inet_server_addr()` = 網橋位址 ⇒ **確實走 scram 而非 loopback trust**。

**容器內 `/tmp/mig`**
```
-rw-r--r-- 1 995 986     4229 0001_identity.sql
-rw-r--r-- 1 995 986     6832 0002_applications.sql
-rw-r--r-- 1 995 986     1351 0003_audit_append_only.sql
-rw-r--r-- 1 995 986     1655 0004_role_grant_guard.sql
-rw-r--r-- 1 995 986     7139 0005_user_identities.sql
-rw-r--r-- 1 995 986     9349 0006_golden_business_session.sql
```

### 2.2 逐檔執行（**每檔一條指令、各自獨立交易 `-1` ＋ `ON_ERROR_STOP=1`**）

```
docker exec -e PGPASSFILE=/tmp/.pgp_m goaa-postgres \
  psql -h 172.17.0.⟨2⟩ -U goaa_c2_migrate -d goaa_platform \
       -v ON_ERROR_STOP=1 -1 -f /tmp/mig/<檔名>
```

**0001_identity.sql** — `RC=0`
```
CREATE TABLE ×2 / CREATE INDEX ×2 / CREATE TABLE / CREATE INDEX / CREATE TABLE / CREATE INDEX
CREATE TABLE / CREATE INDEX / GRANT ×5 / INSERT 0 1
（完整序列：CREATE TABLE, CREATE INDEX, CREATE TABLE, CREATE INDEX, CREATE TABLE, CREATE INDEX,
  CREATE TABLE, CREATE INDEX, CREATE TABLE, CREATE INDEX, GRANT, GRANT, GRANT, GRANT, GRANT, INSERT 0 1）
```

**0002_applications.sql** — `RC=0`
```
CREATE TABLE ×5、CREATE INDEX ×6、GRANT ×6、INSERT 0 1（無 ERROR、無 WARNING）
```

**0003_audit_append_only.sql** — `RC=0`
```
CREATE FUNCTION
DROP TRIGGER
psql:/tmp/mig/0003_audit_append_only.sql:21: NOTICE:  trigger "trg_agent_review_events_append_only" for relation "agent_review_events" does not exist, skipping
CREATE TRIGGER / REVOKE / GRANT / GRANT / INSERT 0 1
```
（NOTICE 為檔案內建 `drop trigger if exists` 的預期行為，非錯誤。）

**0004_role_grant_guard.sql** — `RC=0`
```
CREATE FUNCTION
psql:/tmp/mig/0004_role_grant_guard.sql:37: NOTICE:  trigger "trg_user_roles_guard" for relation "user_roles" does not exist, skipping
DROP TRIGGER / CREATE TRIGGER / INSERT 0 1
```

**0005_user_identities.sql** — `RC=0`
```
ALTER TABLE ×2、CREATE TABLE ×2、CREATE INDEX ×6、CREATE FUNCTION、DROP TRIGGER
psql:/tmp/mig/0005_user_identities.sql:132: NOTICE:  trigger "trg_identity_events_append_only" for relation "identity_events" does not exist, skipping
CREATE TRIGGER / GRANT ×2 / REVOKE / INSERT 0 1
```

**0006_golden_business_session.sql** — `RC=0`
```
CREATE TABLE ×3、CREATE INDEX ×2、ALTER TABLE ×2、GRANT ×3、INSERT 0 1
```

**`ALL_DONE_RC=0`** ⇒ **六檔全部成功，未觸發停手條件，未重跑任何檔、未修改任何 SQL。**

### 2.3 清理

```
container /tmp/mig 及 /tmp/.pgp_m 已刪（container_pgp_left=0、leftovers=0）
host /root/.pgp_m 已刪（host_pgp_left=0）
```
C1 之 `/root/mig/`（已校驗副本）**保留**，供後續查驗；`/root/backups/` 之 dump **未碰**。

---

## 步驟 3：驗收 A–H（✅ 全部通過）

### A. `schema_migrations`（恰好六筆、無重複）
```
select version from schema_migrations order by 1;
0001_identity
0002_applications
0003_audit_append_only
0004_role_grant_guard
0005_user_identities
0006_golden_business_session
--- 筆數 --- 6
--- 重複檢查（group by … having count(*)>1）--- (空)
```
✅ 六筆、順序正確、**無缺無重複**。`applied_at` = `2026-09-12 06:23:01.49` … `06:23:02.88`（UTC），皆為本次套用時刻。

### B. 表數與清單（15 張，與 C2 相同）
```
15|agent_applications agent_license_documents agent_licenses agent_review_events
  business_subject_links business_subjects business_tokens email_verifications
  idempotency_keys identity_events schema_migrations user_identities user_roles
  user_sessions users
```
**count = 15** ✅（C2 `goaa_c2test` 亦為 **15**）。`pg_class` 交叉核對：`r=15`、`i=41`、`S=1`。

### C. 每表 owner（全為 `goaa_c2_migrate`）
```
agent_applications|goaa_c2_migrate        agent_license_documents|goaa_c2_migrate
agent_licenses|goaa_c2_migrate            agent_review_events|goaa_c2_migrate
business_subject_links|goaa_c2_migrate    business_subjects|goaa_c2_migrate
business_tokens|goaa_c2_migrate           email_verifications|goaa_c2_migrate
idempotency_keys|goaa_c2_migrate          identity_events|goaa_c2_migrate
schema_migrations|goaa_c2_migrate         user_identities|goaa_c2_migrate
user_roles|goaa_c2_migrate                user_sessions|goaa_c2_migrate
users|goaa_c2_migrate
```
✅ **15/15 全為 `goaa_c2_migrate`**。

### D. ACL 逐表並排對照 ★

下表「應用角色」欄僅列 `goaa_c2_app` 的權限字元（`a`=INSERT、`r`=SELECT、`w`=UPDATE、`d`=DELETE、`D`=TRUNCATE、`x`=REFERENCES、`t`=TRIGGER）。
**兩側 `goaa_c2_migrate` 於 15 張表皆為 `arwdDxt`（owner），完全相同**，故不重複列出。

| # | 表 | **C1 `goaa_platform`**（本輪新套用） | **C2 `goaa_c2test`**（PRECHECK §6 現況／本次重查） | 差異 |
|---|---|---|---|---|
| 1 | `agent_applications` | `arwd` | `arwd` | — |
| 2 | `agent_license_documents` | `arwd` | `arwd` | — |
| 3 | `agent_licenses` | `arwd` | `arwd` | — |
| 4 | `agent_review_events` | **`ar`** | **`ar`** | — ✅（append-only） |
| 5 | `business_subject_links` | `ar` | **`arwd`** | **⚠️ 差異** |
| 6 | `business_subjects` | `ar` | **`arwd`** | **⚠️ 差異** |
| 7 | `business_tokens` | `arw` | **`arwd`** | **⚠️ 差異** |
| 8 | `email_verifications` | `arwd` | `arwd` | — |
| 9 | `idempotency_keys` | `arwd` | `arwd` | — |
| 10 | `identity_events` | **`ar`** | **`ar`** | — ✅（append-only） |
| 11 | `schema_migrations` | `r` | **`arwd`** | **⚠️ 差異** |
| 12 | `user_identities` | `arw` | **`arwd`** | **⚠️ 差異** |
| 13 | `user_roles` | `arwd` | `arwd` | — |
| 14 | `user_sessions` | `arwd` | `arwd` | — |
| 15 | `users` | `arwd` | `arwd` | — |

**你要看的重點兩列（append-only）**：`agent_review_events` = **`ar`**、`identity_events` = **`ar`** ——
兩邊**一致且都只有 `a`/`r`，無 `w`/`d`/`D`** ✅。

**實質差異 = 6 處**（#5、#6、#7、#11、#12，共 5 張表 ＋ 其中 `business_*` 系列 3 張）：
**方向一律是「C2 比 C1 多出 `w` 與 `d`」**，C1 **沒有**任何一項比 C2 寬鬆。

#### D-1 根因（已定位，非本輪造成）

C2 叢集上存在 **`ALTER DEFAULT PRIVILEGES`**，C1 沒有：

```
C1 pg_default_acl → （空 = 無預設權限）

C2 pg_default_acl →
  goaa_c2_migrate|public|r|{goaa_c2_app=arwd/goaa_c2_migrate}     ← 表：預設給 app arwd
  goaa_c2_migrate|public|S|{goaa_c2_app=rU/goaa_c2_migrate}       ← 序列：預設給 app rU
```

⇒ C2 上**任何由 `goaa_c2_migrate` 新建的表，都會自動獲得 `arwd`**。
這正好解釋了 6 處差異：`business_subjects` / `business_subject_links` / `business_tokens` / `user_identities` / `schema_migrations` 都是在該預設權限存在之後才建的表 ⇒ 除了 migration 明文授與的權限外，還被「預設權限」追加 `w`、`d`。

**來源**：`tests/conftest.py`（三個副本皆同）
```
/opt/goaa-test/backend-clerk-20260910/tests/conftest.py:111:  grant all on schema public to goaa_c2_migrate;
/opt/goaa-test/backend-clerk-20260910/tests/conftest.py:113:  alter default privileges for role goaa_c2_migrate in schema public …
/opt/goaa-test/backend-clerk-20260910/tests/conftest.py:115:  alter default privileges for role goaa_c2_migrate in schema public …
```
（即**測試 harness 過去在 C2 叢集留下的預設權限**。本輪**未載入、未執行 conftest**。）

#### D-2 結論

- **C1 `goaa_platform` 的 ACL ＝ canonical SQL 逐字結果**：已逐條核對檔案內 `grant` 語句——
  `0001`: `schema_migrations` 僅 `select`；
  `0002`: `agent_review_events` 僅 `select, insert`；
  `0005`: `user_identities` = `select, insert, update`、`identity_events` = `select, insert` ＋ `revoke update, delete, truncate`；
  `0006`: 明確註記「least privilege for the application role only」，`business_subjects`/`business_subject_links` = `select, insert`、`business_tokens` = `select, insert, update`。
  **完全吻合，一字不差。**
- **C2 的 ACL 才是偏寬的那一邊**（多出 `w`/`d`），且來源是**測試 harness 的預設權限**，非 migration 檔案。
- **對 R4 的直接影響**：C1 上 app 角色的權限**比 C2 窄**。若 3103 後端在 C2 上「習慣」了 `arwd`（例如對 `business_subjects` 做 UPDATE/DELETE、或對 `schema_migrations` 寫入），在 C1 會出現 `permission denied`。**建議 R4 上線前以 C1 的權限集為準做一次檢核**（本輪未動任何 ACL，等你裁示）。

### E. 函式與觸發器

```
select proname from pg_proc where pronamespace='public'::regnamespace order by 1;
goaa_c2_guard_user_roles
goaa_c2_identity_events_append_only
goaa_c2_review_events_append_only

--- 函式屬性（prosecdef=是否 SECURITY DEFINER；proconfig=search_path 固定？）---
goaa_c2_guard_user_roles|f|-          ← 非 SECURITY DEFINER、未固定 search_path（與 R1 前檢 §Q5 一致）
goaa_c2_identity_events_append_only|f|-
goaa_c2_review_events_append_only|f|-

--- 觸發器（非內部）---
trg_agent_review_events_append_only|agent_review_events
trg_identity_events_append_only|identity_events
trg_user_roles_guard|user_roles
```
三支函式與三個觸發器**全部存在且與 C2 同名同表** ✅（C2 重查結果完全相同）。

### F. 功能測試①：append-only（以 **`goaa_c2_app`** 身分，`172.17.0.⟨2⟩`＋PGPASSFILE）

身分自檢：
```
 current_user | session_user | current_database | inet_server_addr
 goaa_c2_app  | goaa_c2_app  | goaa_platform    | 172.17.0.⟨2⟩
```

**F1 `DELETE FROM agent_review_events;`** — `rc=1`
```
ERROR:  42501: permission denied for table agent_review_events
LOCATION:  aclcheck_error, aclchk.c:2812
```

**F2 `DELETE FROM identity_events;`** — `rc=1`
```
ERROR:  42501: permission denied for table identity_events
LOCATION:  aclcheck_error, aclchk.c:2812
```

**F3 `UPDATE identity_events SET occurred_at = occurred_at;`** — `rc=1`
```
ERROR:  42501: permission denied for table identity_events
LOCATION:  aclcheck_error, aclchk.c:2812
```

**F4（補強）`TRUNCATE agent_review_events;`** — `rc=1`
```
ERROR:  42501: permission denied for table agent_review_events
LOCATION:  aclcheck_error, aclchk.c:2812
```
（補測 TRUNCATE 的理由：行級觸發器**攔不到 TRUNCATE**，故 0003 明文 `revoke truncate`；此測證明確有第二層在守。）

> **兩層防禦的精確說明（誠實標註）**：上述四例被拒的**直接原因都是權限層**（`42501`），這也是 0003 設計的「第 2 層」。**第 1 層（觸發器 `goaa_c2_review_events_append_only` / `..._identity_events_append_only`）確實存在並已由 E 驗證**（`before update or delete … for each row`，函式 `raise exception '… is append-only: % is not permitted', tg_op`），但**行級觸發器只在有列被命中時才會觸發**，而這兩張表目前 **0 列**（`agent_review_events`=0、`identity_events`=0）；在 app 角色**連權限都沒有**的前提下，永遠走不到觸發器。⇒ **實務上由權限層擋下，觸發器為設計上的第二道保險**（對 owner 或未來任何被誤授權的角色仍有效）。**本輪未為了「看到觸發器報錯」而塞入測試列**。

### G. 功能測試②：0004 授權守衛（以 `goaa_c2_app` 身分）

**G0 現況**：`user_roles` 列數 = **0**。

**G1 以 app 身分插入 admin 角色** — `rc=1` ■**被守衛擋下**■
```
ERROR:  42501: the application role may not grant the admin role
CONTEXT:  PL/pgSQL function goaa_c2_guard_user_roles() line 5 at RAISE
LOCATION:  exec_stmt_raise, pl_exec.c:3897
```
⇒ 錯誤**來自守衛函式的 `RAISE`**（`insufficient_privilege`），而非權限或 FK。**守衛確實在運作。**

**G2 對照組（同一句，`role='agent'`）** — `rc=1`，錯誤**不是**守衛
```
ERROR:  23503: insert or update on table "user_roles" violates foreign key constraint "user_roles_user_id_fkey"
DETAIL:  Key (user_id)=(11111111-1111-1111-1111-111111111111) is not present in table "users".
SCHEMA NAME:  public
TABLE NAME:  user_roles
CONSTRAINT NAME:  user_roles_user_id_fkey
LOCATION:  ri_ReportViolation, ri_triggers.c:2608
```
⇒ 守衛**只擋 admin**、對 `agent` 放行（此處因 `users` 空表而撞 FK）。**證明守衛是選擇性的、不是一刀切。**

**G3 殘留列檢查**：`user_roles` 列數 = **0**。
**G4 `UPDATE … SET role='admin'`（無列可命中）**：`UPDATE 0`（rc=0）。

> **清理說明**：G1 被守衛擋下 ⇒ 交易中止、**無列寫入**；G2 被 FK 擋下 ⇒ 交易中止、**無列寫入**；G4 因表為空 ⇒ `UPDATE 0`。**故本輪在 `user_roles` 上「沒有任何殘留列需要清除」，也確實為 0 列**（非事後刪除）。除 `schema_migrations` 的六筆版本記錄（migration 檔案自身寫入）外，**未在新庫留下任何資料列**。

### H. 舊庫與服務未受影響
```
goaa  的 public 表數            → 45   （不變）
goaa_platform 的 public 表數    → 15
systemctl is-active goaa-router → active
curl 127.0.0.⟨1⟩:8080/health    → 200
```
✅ 全部符合。

---

## 額外（best-effort）：C1 vs C2 schema-only 交叉比對

```bash
# C1
docker exec goaa-postgres pg_dump -U goaa --schema-only --no-owner --no-privileges -d goaa_platform
# C2
PGPASSFILE=… pg_dump -h 127.0.0.⟨1⟩ -p 5433 -U goaa_c2_migrate --schema-only --no-owner --no-privileges -d goaa_c2test
```
- 版本：**C1 `pg_dump 16.13`** / **C2 `pg_dump 16.15`**（大小 25,458 vs 25,732 bytes）。
- 正規化（去註解、`SET`、`SELECT pg_catalog.set_config`）後：**C1 = 319 行、C2 = 320 行**。
- **統一 diff 行數 = 5**，其中新增 1 行、刪除 0 行：
```
+COMMENT ON SCHEMA public IS '';
```
⇒ 唯一差異是 C2 上一個**空的 schema 註解**（版本／工具差異造成的裝飾性雜訊）。
- **物件集合比對：兩邊各 56 個物件，`only_in_C1 = 0`、`only_in_C2 = 0`** ⇒ **結構完全相同**（15 表、41 索引、1 序列、3 函式、3 觸發器、5 個 CHECK/UNIQUE 等約束）。
- 註：`--no-privileges` 已排除 GRANT/REVOKE，故 **ACL 的差異不在此 diff 內**，見 §D。

---

## 回滾（本輪未使用）

```sql
DROP DATABASE goaa_platform;   -- 角色保留
```
本輪**未觸發任何回滾**；`/root/backups/` 之 dump 全程未碰。

---

## 紀律自證（步驟 2–3）

- ✅ **SQL 一字未改**（校驗 sha256 前16 與 Tao 提供值全等後才套用；未重跑任何已成功檔）。
- ✅ 逐檔一條指令、**各自獨立交易**（`-1` ＋ `ON_ERROR_STOP=1`），六檔 rc 全 0。
- ✅ 未碰 `goaa` 庫任何一列（僅計數與表名）；未改 env／設定檔；**未重啟任何服務**；未動 ufw／DOCKER-USER／`pg_hba.conf`。
- ✅ 未載入／未執行 `tests/conftest.py`（其為 C2 預設權限之來源，本輪僅讀取行號）。
- ✅ 密碼：只寫入 `600` 的 PGPASSFILE；**未上命令列、未回顯、未進報告**；用完即刪（host 與容器皆 0）。
- ✅ 未在新庫留下任何資料列（`user_roles` = 0、`agent_review_events` = 0、`identity_events` = 0；唯一寫入是 migration 自身的 `schema_migrations` 六筆）。
- ✅ IPv4 一律切分書寫：`172.17.0.⟨2⟩`、`172.17.0.⟨1⟩`、`127.0.0.⟨1⟩`、`134.199.227.⟨108⟩`、`143.198.224.⟨71⟩`。

---

## 秘密掃描（推送前，須為 0 命中）

樣式（切分書寫）：`"sk_" + "live_"`、`"sk_" + "test_"`、`"BEGIN " + "PRIVATE KEY"`、`"AK" + "IA"`、`"gh" + "p_"`、`"postgres" + ":" + "//"`、`"PGPASSWORD" + "="`、`"pass" + "word="`、`"ey" + "J"`、`".pgp" + "_m"`、`".pgp" + "_a"`。

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
| **合計（機密值）** | **0** ✅ |

**非零命中（皆非機密）**：
- 樣式 `".pgp" + "_m"` 命中 5 處 —— 全部是**暫存檔路徑** `PGPASSFILE=/tmp/.pgp_m`（`docker cp`、`psql` 指令中的路徑引用）。**不含任何密碼值、雜湊或金鑰片段**；該檔已於本輪結束時刪除。
- 樣式 `".pgp" + "_a"` 命中 0 處。

⇒ **實質機密命中數 = 0。**

**未切分 IPv4 掃描**：**0 命中**（本報告 IPv4 一律以 `⟨N⟩` 切分；少數取自指令輸出者已就地切分並加註說明）。

**檔案完整性**：`REPORT.md` = **20,876 bytes**、`sha256` 前16 = `ebb48569235bfd14`、首三 byte = `b'# R'`（**無 BOM**）。

**relay main sha**：`743a107e42476c3fd34cdb2429fb8ad2cd063180`
（本報告**內容** commit；其後的子提交僅用於寫入本行與上方掃描回報，未改動任何驗收結論。）
