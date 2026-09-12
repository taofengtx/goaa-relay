# R7-G1｜引導第一個管理員（`user_roles` 新增一列 `role='admin'`）

- **執行時間（UTC）**：第一輪 2026-09-12 18:2xZ（**STOP**）／第二輪 **2026-09-12 18:42:42Z**（Tao 授權後執行**完成**）
- **主機**：C1 `do-runtime-anchor`（公網 `134.199.227.⟨108⟩`）；DB＝容器 `goaa-postgres`（16.13）／庫 `goaa_platform`
- **結論**：✅ **完成**。唯一寫入 = `user_roles` **1 列**（`admin` 給 `t*****x@gmail.com`）：`INSERT 0 1`、`rc=0`；守衛回歸測試如期擋下（`rc=3`）；業務表、事件表、身分表**零變動**。
- **🛡 核准卡**：未出現（0 次）。
- **本檔＝兩輪合併版**：§A＝第一輪（STOP）原文摘錄；§B＝第二輪執行與驗收。

---

## §0 對象訂正（Tao 指正）

- 第一輪我在**同一則回覆**中把代號對調（表格寫 `A = c*****a@…`，下方選項卻寫 `A = t*****x@…`）⇒ **凡授權對象一律以信箱書寫、禁用代號**；本檔與記憶檔已據此改寫。
- **Tao 明令：`admin` 給 `t*****x@gmail.com`**（＝送出那筆 `submitted` 牌照申請的帳號）。

---

## §A 第一輪：🔴 STOP 於步驟 0-1（`users=2`，非 1）—— 寫入次數 = 0

### A-1 唯讀前置（原始輸出）

```
===== 0-1 users | user_roles | admin_count =====
2|2|0
===== 0-2 user_roles.role =====
user
user
===== 0-3 agent_applications count|status =====
1|submitted
===== 0-4 agent_licenses | agent_license_documents =====
1|1
===== 0-5 pre_review recommendation =====
looks_complete
===== 0-6 表結構（唯讀）user_roles 欄位 =====
user_id|uuid|NO
role|text|NO
granted_at|timestamp with time zone|NO
granted_by|uuid|YES
===== 0-7 觸發器存在性（唯讀）=====
trg_user_roles_guard|O
===== 0-8 目前角色 / session_user 觀察（唯讀）=====
-- as goaa: session_user=goaa current_user=goaa
-- as goaa_c2_app: session_user=goaa_c2_app current_user=goaa_c2_app
```

| 項 | 期望 | 實測 | 判定 |
|---|---|---|---|
| 0-1 | `1 \| 1 \| 0` | `2 \| 2 \| 0` | 🔴 **不符** |
| 0-2 | 只應有 `user` | `user`、`user`（兩列，**皆非 admin**） | ✅（值符合；筆數為 2） |
| 0-3 | `1 \| submitted` | `1 \| submitted` | ✅ |
| 0-4 | 兩者 ≥ 1 | `1 \| 1` | ✅ |
| 0-5 | （僅參考） | `looks_complete` | ✅ |
| 0-7 | 守衛在線 | `O`（origin、enabled） | ✅ |

### A-2 兩個使用者（本檔一律以信箱稱呼）

1. `c*****a@gmail.com`（`dc11cc56…`），`identity.jit_create` @ **17:49:52.891041Z**（＝ R7-F2 那次真實登入）。**無**後續業務事件。**非申請人。**
2. `t*****x@gmail.com`（`e9df19c7…`），`identity.jit_create` @ **18:05:06.548469Z**，並於 18:05:06.758528Z 連帶產生 `business.subject_linked` 與 `business.token_issued`（登入後完成業務主體綁定與 token 簽發）。**牌照申請（`submitted`，18:22:52Z）屬此帳號。**

兩人的 `user_roles` 皆為 `user`、`granted_by = null` ⇒ **當時 0 個 admin**。

### A-3 為何不能照原令執行

原令 SQL 內建硬守衛 `if n <> 1 then raise exception`；以現況 `n = 2` **必然中止**，且 `insert … select id,'admin' from users` 一旦移除守衛**會一次把 admin 發給兩人** —— 正是守衛要防的情況。
⇒ **依令停手：不自行改寫守衛、不自行挑選對象。** 本輪未執行任何 INSERT／UPDATE／DELETE／DDL。

---

## §B 第二輪：Tao 授權後執行（✅ 完成）

### B-1 前置複查（唯讀；與第一輪逐項一致）

```
===== 0-1 users | user_roles | admin_count =====
2|2|0
===== 0-2 user_roles.role =====
user
user
===== 0-3 agent_applications count|status =====
1|submitted
===== 0-4 agent_licenses | agent_license_documents =====
1|1
===== 0-5 pre_review recommendation =====
looks_complete
===== 0-6 表結構（唯讀）user_roles 欄位 =====
user_id|uuid|NO
role|text|NO
granted_at|timestamp with time zone|NO
granted_by|uuid|YES
===== 0-7 觸發器存在性（唯讀）=====
trg_user_roles_guard|O
===== 0-8 目前角色 / session_user 觀察（唯讀）=====
-- as goaa: session_user=goaa current_user=goaa
-- as goaa_c2_app: session_user=goaa_c2_app current_user=goaa_c2_app
```

### B-2 步驟 1｜修正版守衛 SQL（結構上只可能寫 1 列）

**變更點**（唯一處，即 Tao 授權的作業範圍）：守衛由「**全表僅 1 列**」改為下列四條**指定對象**斷言，插入語句改為 `where id = <目標>`：

1. `users` 總數必須仍為 **2**（前置不變）；
2. 目標 id 必須**存在且唯一**；
3. 目標的**遮罩信箱必須等於** `t*****x@gmail.com`（以 SQL 內計算、不寫入完整信箱字面）；
4. 目標必須恰有 **1 筆 `submitted`** 申請；
5. 現況**不得已有任何 `admin`**。

執行檔 `/tmp/r7g1.sql`：**1,330 B**、`sha256_16 = 674077cc4ccaa3b0`（傳輸後於 C1 以 `sha256sum` 複核**相符**）；執行後已刪除。

```sql
\set ON_ERROR_STOP on
begin;

do $$
declare
  n_users  int;
  n_target int;
  n_app    int;
  m        text;
  tgt      uuid := 'e9df19c7-…';   -- 節錄：uuid 中間段以 … 遮罩，執行檔為完整值
begin
  select count(*) into n_users from users;
  if n_users <> 2 then
    raise exception 'precondition changed: expected 2 users, found %', n_users;
  end if;

  select count(*) into n_target from users where id = tgt;
  if n_target <> 1 then
    raise exception 'expected exactly 1 user %, found %', tgt, n_target;
  end if;

  select left(email,1) || repeat(chr(42),5) || substr(email, position(chr(64) in email)-1, 1) || substr(email, position(chr(64) in email))
    into m from users where id = tgt;
  if m <> 't*****x@gmail.com' then
    raise exception 'target masked-email mismatch: %', m;
  end if;

  select count(*) into n_app from agent_applications where user_id = tgt and status = 'submitted';
  if n_app <> 1 then
    raise exception 'expected exactly 1 submitted application for target, found %', n_app;
  end if;

  if exists (select 1 from user_roles where role = 'admin') then
    raise exception 'an admin role already exists; refusing to add another';
  end if;
end $$;

insert into user_roles (user_id, role)
select id, 'admin' from users where id = 'e9df19c7-…'
on conflict (user_id, role) do nothing;

commit;
```

守衛回歸測試檔 `/tmp/r7g1-guard.sql`：**126 B**、`sha256_16 = aa692358171eebb3`（傳輸後複核相符）；執行後已刪除。

```sql
begin;
insert into user_roles (user_id, role)
select id, 'admin' from users
on conflict (user_id, role) do nothing;
rollback;
```

**執行**（以 **migration 角色** `goaa_c2_migrate` 連線，屬設計本意）：

```
docker exec -i goaa-postgres psql -U goaa_c2_migrate -d goaa_platform -v ON_ERROR_STOP=1 -f - < /tmp/r7g1.sql
```

原始輸出：

```
BEGIN
DO
INSERT 0 1
COMMIT
sql_rc=0
```

⇒ **恰好 1 列**（`INSERT 0 1`），交易成功提交。

### B-3 步驟 2｜驗收（原始輸出）

```
===== 2-1 目標帳號的角色列（遮罩）=====
user|c*****a@gmail.com|2026-09-12 17:49:52.891041+00|null
admin|t*****x@gmail.com|2026-09-12 18:42:42.086247+00|null
user|t*****x@gmail.com|2026-09-12 18:05:06.548469+00|null
===== 2-2 admin 計數 / 角色分布 =====
1|3
admin|1
user|2
===== 2-3a 應用角色權限（唯讀）=====
t|t
===== 2-3b 守衛回歸測試（以 goaa_c2_app 真實連線，必須失敗）=====
BEGIN
psql:<stdin>:4: ERROR:  the application role may not grant the admin role
CONTEXT:  PL/pgSQL function goaa_c2_guard_user_roles() line 5 at RAISE
guard_test_rc=3
===== 2-4 業務表未變（唯讀）=====
1|1|1|1|0|6|2
===== 2-5 users x roles 全表對照（遮罩）=====
c*****a@gmail.com|user
t*****x@gmail.com|admin,user
===== 2-6 寫入痕跡（identity_events 不應有新增）=====
4
```

### B-4 判定表

| 項 | 期望 | 實測 | 判定 |
|---|---|---|---|
| 2-1 | 目標帳號取得 `admin` | `admin \| t*****x@gmail.com \| 2026-09-12 18:42:42.086247+00 \| null` | ✅ |
| 2-1 | 另一帳號不受影響 | `user \| c*****a@gmail.com \| 17:49:52.891041+00 \| null`（原值） | ✅ |
| 2-2 | `admin` 計數 = 1 | `1 \| 3`（admin 1、user 2） | ✅ |
| 2-3a | 應用角色確實有 INSERT 權 | `t \| t`（`user_roles` INSERT、`users` SELECT） | ✅ |
| 2-3b | 應用角色插 `admin` **必須失敗** | `ERROR: the application role may not grant the admin role`（`rc=3`） | ✅ |
| 2-4 | 業務表零變動 | `apps=1 \| submitted=1 \| licenses=1 \| docs=1 \| sessions=0 \| migrations=6 \| users=2` | ✅ |
| 2-5 | 全域角色對照 | `c*****a: user`／`t*****x: admin,user` | ✅ |
| 2-6 | `identity_events` 不新增 | 4 筆，**最新 `18:05:06.758528Z`**（早於本次寫入 `18:42:42Z`） | ✅ |

### B-5 副作用核對（唯一寫入的證據）

- `identity_events` **4 筆且時間戳全部 ≤ 18:05:06.758528Z** ⇒ 本次寫入**未產生任何身分事件**。
- `users = 2`、`schema_migrations = 6`、`user_sessions = 0`、`agent_applications = 1`（`submitted` 1）、`agent_licenses = 1`、`agent_license_documents = 1` ⇒ **除 `user_roles` 新增 1 列外，全庫無變動**。
- 未改任何檔案；未重啟任何服務；未動 `current`／env／migrations；`granted_by = null`（依令不指定授予者）。

### B-6 清理

`/tmp/r7g1.sql` 與 `/tmp/r7g1-guard.sql` 以 `python3 os.remove` 刪除，複核 `cleanup_ok False False`。

---

## 附註

1. 本輪以 **migration 角色** 連線（設計本意）；守衛僅限制**應用角色**。
2. `trg_user_roles_guard` 定義＝`BEFORE INSERT OR DELETE OR UPDATE ON public.user_roles FOR EACH ROW EXECUTE FUNCTION goaa_c2_guard_user_roles()`；錯誤訊息出自該函式第 5 行 `RAISE`。
3. 2-3b 的失敗**確實來自守衛、不是權限不足**（2-3a 已證應用角色對 `user_roles` 具 INSERT、對 `users` 具 SELECT）。
4. 角色為**每次請求重讀**（後端 `current_user` 每次查 `user_roles`）⇒ 不需重啟即可生效。

## 秘密掃描（掃描對象＝本檔自身）

掃描器：`/tmp/r5c-scanrep.py`（通用 16 樣式；樣式字面在掃描器內以字串相接書寫）。
**掃描表標籤一律使用切分寫法**，以免說明段自我膨脹命中數。

| # | 樣式標籤 | 命中數 |
|---|---|---|
| 1 | stripe-live-VALUE | 0 |
| 2 | stripe-test-VALUE | 0 |
| 3 | clerk-pk-live-VALUE | 0 |
| 4 | clerk-pk-test-VALUE | 0 |
| 5 | clerk-sk-live-VALUE | 0 |
| 6 | pem | 0 |
| 7 | aws | 0 |
| 8 | github-pat | 0 |
| 9 | pg-uri | 0 |
| 10 | pg-pass-assign | 0 |
| 11 | password-assign | 0 |
| 12 | jwt-shape | 0 |
| 13 | pg-pass-name | 0 |
| 14 | clerk-keyname | 0 |
| 15 | clerk-secret-assign | 0 |
| 16 | session-secret-assign | 0 |

**TOTAL_HITS = 0**

**未切分可路由 IPv4 檢查 = 0 筆**。可路由位址一律 `⟨N⟩` 切分（本檔僅出現 `134.199.227.⟨108⟩`）。

## 本報告指紋

- first3 = `# R`、BOM = False、bytes = 10,952、sha256_16 = da2902323dba731e（此欄以等長 `0` 佔位後計算 ⇒ 可自我驗證）
