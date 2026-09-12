# Round R1 · 階段二前檢 — migration 內容的硬編碼檢查（RECON / 唯讀）

- **時間**：2026-09-12 05:47 UTC（= 2026-09-11 22:47 PDT）
- **執行者**：Aika（經 `ssh do-c2`；**未連 C1**、未建任何物件、未跑任何 migration）
- **範圍**：canonical 樹 `/opt/goaa-test/backend-clerk-20260910/` 的 `migrations/*.sql` 與 `tools/migrate.py`
- **目的**：確認 `0001–0006` 是否把**角色名／庫名／schema 名**寫死成 C2 的值 —— 這決定新庫要建幾個角色、遷移前要不要先建角色。
- **紀律**：唯讀；env 只列名（未印任何值）；未讀 pgpass 值；IPv4 切分；sha256 前 16。

---

## 0. 結論（TL;DR）

| # | 問題 | 答案 |
|---|---|---|
| **Q1** | 角色名有寫死嗎？ | **有，而且是關鍵。** 硬編碼 `goaa_c2_app` 出現於 **0001(L82–86)、0002(L122–127)、0003(L27,28,31)、0005(L140–142)、0006(L158–160)** 的 `grant`/`revoke`；**且 0004(L16) 用 `session_user = 'goaa_c2_app'` 做授權守衛的判斷條件**。 |
| **Q2** | 庫名有寫死嗎？ | **沒有。** `goaa_c2test` / `goaa_c2` 只出現在**註解**（0005 L16–17、0006 L22–23）。實際庫由 runner 的 `-d $GOAA_C2_DB_NAME` 決定。 |
| **Q3** | schema 名有寫死嗎？ | **沒有。** 全樹**零** `CREATE SCHEMA`、**零** `SET search_path`、**零** `CREATE EXTENSION` ⇒ 一切落在 **`public`**（由連線時 search_path 預設）。 |
| **Q4** | 遷移前要先建角色嗎？ | **必須。** 全樹**零** `CREATE ROLE` / `CREATE USER` / `ALTER ROLE` / `OWNER TO` / `SET ROLE`。角色不存在 ⇒ `GRANT` 直接失敗。 |
| **Q5** | 要建幾個角色？ | **至少要 2 個**：① **schema/owner 角色**（執行遷移的角色，決定表的 owner）；② **`goaa_c2_app`**（被 GRANT 的應用角色）。 |

> ### 🔴 對階段二最要緊的一句話
> Tao 拍板的新庫角色是 **`goaa_platform`**，但 **canonical `0001–0006` 認的角色名是 `goaa_c2_app`（＋ owner 角色）**。
> ⇒ 若只建 `goaa_platform` 就跑遷移，**會 `GRANT` 失敗**；而若把應用角色改名，**0004 的 admin-grant 守衛會靜默失效**（見 §7）。**這一件事需要 Tao 裁決，我不自行決定。**

---

## 1. 角色相關語句（全文，未截斷）

> 註：第一次以 `grep -E "GRANT"`（大小寫敏感）執行，只命中 1 行；以下是**補跑的大小寫不敏感版本**，才是完整清單。

```
0001_identity.sql:3:-- are normalised into one `users` row plus a `user_roles` grant table).
0001_identity.sql:40:    granted_at timestamptz not null default now(),
0001_identity.sql:41:    granted_by uuid        references users (id) on delete set null,
0001_identity.sql:73:    revoked_at timestamptz
0001_identity.sql:77:    on user_sessions (user_id) where revoked_at is null;
0001_identity.sql:80:-- explicit grants (do not rely solely on default privileges)
0001_identity.sql:82:grant select, insert, update, delete on users               to goaa_c2_app;
0001_identity.sql:83:grant select, insert, update, delete on user_roles          to goaa_c2_app;
0001_identity.sql:84:grant select, insert, update, delete on email_verifications to goaa_c2_app;
0001_identity.sql:85:grant select, insert, update, delete on user_sessions       to goaa_c2_app;
0001_identity.sql:86:grant select on schema_migrations                           to goaa_c2_app;
0002_applications.sql:120:-- explicit grants
0002_applications.sql:122:grant select, insert, update, delete on agent_applications        to goaa_c2_app;
0002_applications.sql:123:grant select, insert, update, delete on agent_licenses            to goaa_c2_app;
0002_applications.sql:124:grant select, insert, update, delete on agent_license_documents   to goaa_c2_app;
0002_applications.sql:125:grant select, insert                 on agent_review_events       to goaa_c2_app;
0002_applications.sql:126:grant select, insert, update, delete on idempotency_keys          to goaa_c2_app;
0002_applications.sql:127:grant usage, select on all sequences in schema public             to goaa_c2_app;
0003_audit_append_only.sql:5:--   2. table privileges that never grant UPDATE/DELETE/TRUNCATE to the app role.
0003_audit_append_only.sql:27:revoke update, delete, truncate on agent_review_events from goaa_c2_app;
0003_audit_append_only.sql:28:grant select, insert on agent_review_events to goaa_c2_app;
0003_audit_append_only.sql:31:grant usage, select on all sequences in schema public to goaa_c2_app;
0004_role_grant_guard.sql:16:    if session_user = 'goaa_c2_app' then
0005_user_identities.sql:140:grant select, insert, update on user_identities to goaa_c2_app;
0005_user_identities.sql:141:grant select, insert         on identity_events to goaa_c2_app;
0005_user_identities.sql:142:revoke update, delete, truncate on identity_events from goaa_c2_app;
0006_golden_business_session.sql:158:grant select, insert on business_subjects to goaa_c2_app;
0006_golden_business_session.sql:159:grant select, insert on business_subject_links to goaa_c2_app;
0006_golden_business_session.sql:160:grant select, insert, update on business_tokens to goaa_c2_app;
```

**要點**：
- **只有一個被 GRANT/REVOKE 的角色：`goaa_c2_app`**（共 20 條授權語句）。
- **`CREATE ROLE` / `CREATE USER` / `ALTER ROLE` / `OWNER TO` / `SET ROLE`：全樹 0 命中** ⇒ **角色必須先存在**。
- **`goaa_c2_migrate`（C2 的 schema owner 角色）在 migrations 中完全沒提及**（見 §2 補查）—— 表的 owner 純粹是「**誰跑遷移**」。
- `session_user` 只在 **0004:16** 出現一次（授權守衛）；`current_user` 0 命中。

---

## 2. 硬編碼的識別字

### 2a. 題目指定樣式（`goaa_c2|goaa_c2test|goaa_c2_app|c2test|localhost|5433`，大小寫不敏感）

```
0001_identity.sql:82:grant select, insert, update, delete on users               to goaa_c2_app;
0001_identity.sql:83:grant select, insert, update, delete on user_roles          to goaa_c2_app;
0001_identity.sql:84:grant select, insert, update, delete on email_verifications to goaa_c2_app;
0001_identity.sql:85:grant select, insert, update, delete on user_sessions       to goaa_c2_app;
0001_identity.sql:86:grant select on schema_migrations                           to goaa_c2_app;
0002_applications.sql:122:grant select, insert, update, delete on agent_applications        to goaa_c2_app;
0002_applications.sql:123:grant select, insert, update, delete on agent_licenses            to goaa_c2_app;
0002_applications.sql:124:grant select, insert, update, delete on agent_license_documents   to goaa_c2_app;
0002_applications.sql:125:grant select, insert                 on agent_review_events       to goaa_c2_app;
0002_applications.sql:126:grant select, insert, update, delete on idempotency_keys          to goaa_c2_app;
0002_applications.sql:127:grant usage, select on all sequences in schema public             to goaa_c2_app;
0003_audit_append_only.sql:10:create or replace function goaa_c2_review_events_append_only()
0003_audit_append_only.sql:24:    for each row execute function goaa_c2_review_events_append_only();
0003_audit_append_only.sql:27:revoke update, delete, truncate on agent_review_events from goaa_c2_app;
0003_audit_append_only.sql:28:grant select, insert on agent_review_events to goaa_c2_app;
0003_audit_append_only.sql:31:grant usage, select on all sequences in schema public to goaa_c2_app;
0004_role_grant_guard.sql:11:create or replace function goaa_c2_guard_user_roles()
0004_role_grant_guard.sql:16:    if session_user = 'goaa_c2_app' then
0005_user_identities.sql:16-17:-- ... (註解，見 2b)
0005_user_identities.sql:121:create or replace function goaa_c2_identity_events_append_only()
0005_user_identities.sql:135:    for each row execute function goaa_c2_identity_events_append_only();
0005_user_identities.sql:140:grant select, insert, update on user_identities to goaa_c2_app;
0005_user_identities.sql:141:grant select, insert         on identity_events to goaa_c2_app;
0005_user_identities.sql:142:revoke update, delete, truncate on identity_events from goaa_c2_app;
0006_golden_business_session.sql:22:--   * Nothing here touches `goaa_c2`, C1, the golden runtime, payments or the
0006_golden_business_session.sql:23:--     existing authentication code. Target database for this round: goaa_c2test.
0006_golden_business_session.sql:158:grant select, insert on business_subjects to goaa_c2_app;
0006_golden_business_session.sql:159:grant select, insert on business_subject_links to goaa_c2_app;
0006_golden_business_session.sql:160:grant select, insert, update on business_tokens to goaa_c2_app;
```

**`goaa_c2test` 的完整出現處（全部是註解）**：
```
0005_user_identities.sql:17:-- (goaa_c2 and C1 are NOT migrated.)
0006_golden_business_session.sql:22:--   * Nothing here touches `goaa_c2`, C1, the golden runtime, payments or the
0006_golden_business_session.sql:23:--     existing authentication code. Target database for this round: goaa_c2test.
```

**`localhost` / `5433`：0 命中**（連線資訊完全不在 SQL 內）。

### 2b. 補查：`goaa_c2_migrate` 是否也被寫死？

```
$ grep -n -i "goaa_c2_migrate" $M/*.sql
（空 —— 0001–0006 完全未提及 migrate 角色）
```

⇒ **owner 角色名不出現在 migrations 裡**；它由 runner 的 `-U`（見 §5）決定，因此**表 owner = 執行遷移的角色**（C2 實況即 `goaa_c2_migrate`，見 §6a）。

### 2c. 補充：`schema_migrations` 的寫入方式

每支 migration 檔尾皆為：
```sql
insert into schema_migrations (version) values ('000N_<name>')
    on conflict (version) do nothing;
```
（`schema_migrations` 由 **0001** 建立；forward-only、可重跑。）

### 2d. 補充：函式安全屬性

```
$ grep -n -i -E "security definer|security invoker|set search_path|search_path" $M/*.sql
（空 —— 0 命中）
```
⇒ `goaa_c2_guard_user_roles()` 既非 `SECURITY DEFINER`、也**未固定 `search_path`**；且**無 `SET search_path`**。**函式內以 `session_user` 判斷身分** ⇒ 守衛只在「**應用真的以 `goaa_c2_app` 登入**」時才生效。

---

## 3. schema 與擴充

```
$ grep -n -E "CREATE SCHEMA|SET search_path|CREATE EXTENSION" $M/*.sql
（空 —— 0 命中）
```

⇒ **全部物件落在連線當時的預設 schema（`public`）**；未使用任何 extension（`uuid`、`citext` 等皆未 `CREATE EXTENSION` ⇒ 若有用到，是靠 PG 內建型別）。

---

## 4. `0004_role_grant_guard.sql` 全文（逐行）

```sql
-- 0004_role_grant_guard.sql
-- The runtime application role must be able to grant the `agent` role (that is
-- what an approval does) but must never be able to mint an administrator —
-- not even if a SQL injection ever reached an INSERT/UPDATE/DELETE on
-- user_roles. Administrator grants are an out-of-band operator action performed
-- as the schema-owning migration role.
-- Forward-only and safe to re-run.

\set ON_ERROR_STOP on

create or replace function goaa_c2_guard_user_roles()
returns trigger
language plpgsql
as $$
begin
    if session_user = 'goaa_c2_app' then
        if tg_op = 'INSERT' and new.role = 'admin' then
            raise exception 'the application role may not grant the admin role'
                using errcode = 'insufficient_privilege';
        end if;
        if tg_op = 'UPDATE' and (old.role = 'admin' or new.role = 'admin') then
            raise exception 'the application role may not modify the admin role'
                using errcode = 'insufficient_privilege';
        end if;
        if tg_op = 'DELETE' and old.role = 'admin' then
            raise exception 'the application role may not revoke the admin role'
                using errcode = 'insufficient_privilege';
        end if;
    end if;
    if tg_op = 'DELETE' then
        return old;
    end if;
    return new;
end;
$$;

drop trigger if exists trg_user_roles_guard on user_roles;
create trigger trg_user_roles_guard
    before insert or update or delete on user_roles
    for each row execute function goaa_c2_guard_user_roles();

insert into schema_migrations (version) values ('0004_role_grant_guard')
    on conflict (version) do nothing;
```

**逐行要點**：
- **L16 `if session_user = 'goaa_c2_app' then`** —— **整個守衛的有效性掛在這個字面字串上**。
  - 若執行身分**不是** `goaa_c2_app`（例如新庫的應用角色改叫 `goaa_platform`），**守衛整段被跳過 ⇒ admin 角色可被應用任意授與** —— **靜默的安全回歸**。
- 守衛只擋 **`admin`** 這個值；`agent` 等其它角色**允許**應用自行授與（符合設計）。
- 函式**非 `SECURITY DEFINER`**、**未固定 `search_path`** ⇒ 呼叫者權限即執行權限（安全性 OK，但名字依賴不變）。
- 觸發器 `trg_user_roles_guard` 為 `before insert or update or delete`、`for each row`。

---

## 5. runner 怎麼決定「連哪個庫、用哪個角色」

```
$ grep -n -E "DB_NAME|DB_USER|MIGRATE|PGPASSFILE|psql|schema_migrations|dsn|conn" tools/migrate.py

3:Each migration is executed by ``psql -1 -f <file>`` as the dedicated
8:and its version is recorded in ``schema_migrations``.
32:def _psql_args() -> list[str]:
34:        _env_or("GOAA_C2_PSQL", "/usr/lib/postgresql/16/bin/psql"),
37:        "-U", _env_or("GOAA_C2_MIGRATE_USER", "goaa_c2_migrate"),
38:        "-d", _env_or("GOAA_C2_DB_NAME", "goaa_c2"),
46:    env["PGPASSFILE"] = _env_or("GOAA_C2_MIGRATE_PASSFILE", "/opt/goaa-test/env/migrate.pgpass")
51:    args = _psql_args()
54:        args.insert(len(_psql_args()), "-1")  # single transaction per migration file
60:        "select version from schema_migrations order by version"
```

**解讀**：
- **角色**：`-U $GOAA_C2_MIGRATE_USER`（預設 `goaa_c2_migrate`）⇒ 遷移以**該角色**執行，**表的 owner 就是它**。
- **庫**：`-d $GOAA_C2_DB_NAME`（預設 `goaa_c2`）⇒ **庫名不在 SQL 內，全靠這個變數**。
- **主機／埠**：`_env_or("GOAA_C2_DB_HOST"…)` / `…PORT`（見上輪 RECON §4.3；此檔第 35–36 行）。
- **憑據**：`env["PGPASSFILE"] = $GOAA_C2_MIGRATE_PASSFILE`（預設 `/opt/goaa-test/env/migrate.pgpass`）⇒ **密碼不進命令列**。
- **交易**：每個檔以 `psql -1`（單一交易）執行；版本記錄於 `schema_migrations`（`--status` 會 `select version …`）。
- ⇒ **換庫／換角色只需改環境變數**，**不需改 SQL**（前提：GRANT 的目標角色名存在）。

---

## 6. C2 現況對照（`goaa_c2test`，唯讀）

連線（沿用上輪方式，**env 值未列印**）：`current_user | current_database() | port` = **`goaa_c2_app | goaa_c2test | 5433`**

### 6a. `public` schema 各表 owner

| tablename | owner |
|---|---|
| agent_applications | **goaa_c2_migrate** |
| agent_license_documents | **goaa_c2_migrate** |
| agent_licenses | **goaa_c2_migrate** |
| agent_review_events | **goaa_c2_migrate** |
| business_subject_links | **goaa_c2_migrate** |
| business_subjects | **goaa_c2_migrate** |
| business_tokens | **goaa_c2_migrate** |
| email_verifications | **goaa_c2_migrate** |
| idempotency_keys | **goaa_c2_migrate** |
| identity_events | **goaa_c2_migrate** |
| schema_migrations | **goaa_c2_migrate** |
| user_identities | **goaa_c2_migrate** |
| user_roles | **goaa_c2_migrate** |
| user_sessions | **goaa_c2_migrate** |
| users | **goaa_c2_migrate** |

（**15 張表，owner 全部 = `goaa_c2_migrate`**，與 §5 的推論一致。）

### 6b. `public` 關聯的 ACL（`relacl`）

```
agent_applications     | {goaa_c2_migrate=arwdDxt/goaa_c2_migrate, goaa_c2_app=arwd/goaa_c2_migrate}
agent_license_documents| {goaa_c2_migrate=arwdDxt/goaa_c2_migrate, goaa_c2_app=arwd/goaa_c2_migrate}
agent_licenses         | {goaa_c2_migrate=arwdDxt/goaa_c2_migrate, goaa_c2_app=arwd/goaa_c2_migrate}
agent_review_events    | {goaa_c2_migrate=arwdDxt/goaa_c2_migrate, goaa_c2_app=ar/goaa_c2_migrate}   ← 僅 SELECT/INSERT
business_subject_links | {goaa_c2_migrate=arwdDxt/goaa_c2_migrate, goaa_c2_app=arwd/goaa_c2_migrate}
business_subjects      | {goaa_c2_migrate=arwdDxt/goaa_c2_migrate, goaa_c2_app=arwd/goaa_c2_migrate}
business_tokens        | {goaa_c2_migrate=arwdDxt/goaa_c2_migrate, goaa_c2_app=arwd/goaa_c2_migrate}
email_verifications    | {goaa_c2_migrate=arwdDxt/goaa_c2_migrate, goaa_c2_app=arwd/goaa_c2_migrate}
idempotency_keys       | {goaa_c2_migrate=arwdDxt/goaa_c2_migrate, goaa_c2_app=arwd/goaa_c2_migrate}
identity_events        | {goaa_c2_migrate=arwdDxt/goaa_c2_migrate, goaa_c2_app=ar/goaa_c2_migrate}   ← 僅 SELECT/INSERT
schema_migrations      | {goaa_c2_migrate=arwdDxt/goaa_c2_migrate, goaa_c2_app=arwd/goaa_c2_migrate}
user_identities        | {goaa_c2_migrate=arwdDxt/goaa_c2_migrate, goaa_c2_app=arwd/goaa_c2_migrate}
user_roles             | {goaa_c2_migrate=arwdDxt/goaa_c2_migrate, goaa_c2_app=arwd/goaa_c2_migrate}
user_sessions          | {goaa_c2_migrate=arwdDxt/goaa_c2_migrate, goaa_c2_app=arwd/goaa_c2_migrate}
users                  | {goaa_c2_migrate=arwdDxt/goaa_c2_migrate, goaa_c2_app=arwd/goaa_c2_migrate}
```

**要點**：
- owner（`goaa_c2_migrate`）持 `arwdDxt`（含 `D`=TRUNCATE、`x`=REFERENCES、`t`=TRIGGER）。
- 應用（`goaa_c2_app`）持 `arwd`（SELECT/INSERT/UPDATE/DELETE）。
- **`agent_review_events` 與 `identity_events` 只給 `ar`（SELECT/INSERT）** ⇒ **append-only 在 ACL 層生效**（0003/0005 的 `revoke update, delete, truncate` 兌現）。
- **沒有任何 `=…`（PUBLIC）條目** ⇒ 未對 PUBLIC 開放。
- 未見為 `schema_migrations` 以外的表列出 `goaa_c2_migrate` 之外的 owner。

### 6c. 該庫可見的角色

```
goaa_c2_app
goaa_c2_migrate
（其餘為 pg_* 內建：pg_checkpoint / pg_database_owner / pg_monitor / pg_read_all_data / …）
```

⇒ **該叢集的自建角色只有這 2 個**，與 §0-Q5「至少要 2 個角色」一致。

---

## 7. 對「階段二（C1 上建新庫）」的含意 —— **需要 Tao 裁決的 3 點**

### 決策點 ①：新庫的「應用角色」叫什麼？

| 選項 | 做法 | 代價 / 風險 |
|---|---|---|
| **A. 沿用同名** | 在 **C1 叢集**建立 **同名** 角色 `goaa_c2_app`（＋ owner 角色），`0001–0006` **原封不動**套用 | **零改檔、sha 不變、C2 已驗的 ACL 形態可完全複製**；代價：C1 上出現名帶 `c2` 的角色（命名觀感） |
| **B. 改名 `goaa_platform`** | 只建 `goaa_platform`（＋ owner 角色） | **`GRANT` 全部失敗**（`role "goaa_c2_app" does not exist`）⇒ 必須**改寫 0001/0002/0003/0005/0006 的 20 條授權 + 改 0004 L16** ⇒ **動到已驗收的 migration（sha 改變）** |
| **C. 混合（不建議）** | 建 `goaa_platform` 當 login，另建 `goaa_c2_app` 當 group role 並 `GRANT goaa_c2_app TO goaa_platform` | 授權語句可通過，**但 0004 的守衛用 `session_user`（＝ login 角色 = `goaa_platform`）⇒ 守衛靜默失效**（見決策點 ②） |

### 決策點 ②：`0004` 的 admin-grant 守衛要不要保留？

- 守衛條件是 **`session_user = 'goaa_c2_app'`**（`session_user` 是**登入角色**，不受 `SET ROLE` 影響）。
- ⇒ **只有「應用真的以 `goaa_c2_app` 登入」時，守衛才生效。**
- 若階段二讓應用改以別的名字登入，**admin 角色將可被應用自行授與** —— 這是 **靜默安全回歸**，且**不會有任何錯誤訊息**。
- 若採**選項 A**，此風險**不存在**（守衛照常生效）。

### 決策點 ③：owner / migrate 角色叫什麼？

- `0001–0006` **不提 owner 角色名** ⇒ **可自由命名**（建議 `goaa_platform` 或 `goaa_platform_migrate`），因為 owner 純由 `-U` 決定。
- 但請注意：**owner 角色決定表的 owner**，且 owner 擁有 `D`(TRUNCATE)/`x`/`t` 與 `DROP` 能力 ⇒ 仍應**與應用角色分離**（C2 現況即如此）。

---

## 8. 本階段「未做 / 未碰」清單

- ❌ **未連 C1**（本輪 SSH 僅 `do-c2`，共 3 次）。
- ❌ 未建任何角色／庫／物件；未 `CREATE`／`ALTER`／`DROP`。
- ❌ 未跑任何 migration。
- ❌ 未改 env／設定檔；未重啟任何服務。
- ❌ 未讀 pgpass／secret 值（僅確認變數名存在）。
- ✅ 全程唯讀：`grep` / `cat` / `SELECT`（系統目錄 + `pg_tables`/`pg_class`/`pg_roles`）。

---

## 9. 附錄

| 本機暫存 | 用途 |
|---|---|
| `/tmp/r1p.sh`、`/tmp/r1p2.sh`、`/tmp/r1p6.sh` | 前檢腳本（items 1–5 / 補查 / item 6） |
| `/tmp/r1p-out.txt`、`/tmp/r1p2-out.txt`、`/tmp/r1p6-out.txt` | 原始輸出 |

**主機位址切分書寫**：C1 `134.199.227.⟨108⟩`、C2 `143.198.224.⟨71⟩`、C3 `64.23.166.⟨121⟩`。

---

## 10. 秘密掃描（推送前，須為 0 命中）

樣式（切分書寫）：`"sk_" + "live_"`、`"BEGIN " + "PRIVATE KEY"`、`"AK" + "IA"`、`"gh" + "p_"`、`"postgres" + ":" + "//"`。

**掃描回報（推送前，逐樣式統計）**：

| 樣式（切分書寫） | 命中 |
|---|---|
| `"sk_" + "live_"`（Stripe live 前綴） | **0** |
| `"BEGIN " + "PRIVATE KEY"`（PEM 私鑰標頭） | **0** |
| `"AK" + "IA"`（AWS access key 前綴） | **0** |
| `"gh" + "p_"`（GitHub PAT 前綴） | **0** |
| `"postgres" + ":" + "//"`（Postgres URI scheme） | **0** |
| **合計** | **0** ✅ |

**檔案完整性**：`PRECHECK-ROLES.md` = **20,972 bytes**、`sha256` 前16 = `67cbfd749460b4c4`、首三 byte = `b'# R'`（**無 BOM**）。

**relay main sha**：`28b4ef1aef172a30baa17f115da683ff9fbe19c3`
（本報告**內容** commit；其後的子提交僅用於寫入本行與上方掃描回報，未改動任何檢查結論。）
