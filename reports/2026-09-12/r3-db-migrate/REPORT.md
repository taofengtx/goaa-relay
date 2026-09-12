# Round R2 · 階段二 第二段 — 套用 migration 0001–0006 ＋ 驗 schema

- **時間**：步驟 1 於 2026-09-12 06:19–06:20 UTC（= 2026-09-11 23:19 PDT）
- **主機**：C2 `do-c2`（來源，`goaa-aika-cloud-2-01`，`143.198.224.⟨71⟩`）→ C1 `do-runtime-anchor`（目標，`goaa-aika-cloud-1`，`134.199.227.⟨108⟩`）
- **執行者**：Aika
- **🔴 本輪狀態**：**步驟 1（取檔並校驗）✅ 完成，6/6 檔 sha256 前16 與行數全等於期望值；步驟 2（套用）、步驟 3（驗收 A–H）⏸ 未執行 —— 依 Tao 指令之閘門等待核准。**
  - 依據：Tao 在步驟 2 標題寫明 **「（我核准後再做；先把步驟 1 的校驗表回報給我）」**。此閘門優先於本輪標題，故**停在步驟 1**。
  - **未套用任何 migration**：`goaa_platform` 仍為 **0 張表**（見下方前提覆核）。
  - 若 Tao 意為一次做完，回一句 go 即續作步驟 2–3。

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

## 步驟 2：套用（⏸ 未執行 —— 等待 Tao 核准）

**預定指令**（逐檔、單獨交易、任一非 0 立即停手）：

```bash
docker cp /root/mig goaa-postgres:/tmp/mig
# 另將 goaa_c2_migrate 密碼以 PGPASSFILE 形式送入容器（只引用路徑，值不列）

docker exec -e PGPASSFILE=/tmp/.pgp_m goaa-postgres \
  psql -h 172.17.0.⟨2⟩ -U goaa_c2_migrate -d goaa_platform \
       -v ON_ERROR_STOP=1 -1 -f /tmp/mig/0001_identity.sql
# … 依序 0002 → 0006，每檔一條、各自獨立交易（-1）
```
- 走 **`172.17.0.⟨2⟩`（非 loopback）⇒ 命中 `scram-sha-256`**，順帶再驗一次密碼路徑（R2 教訓）。
- 收尾刪除容器內 `/tmp/mig` 與暫存密碼檔。

**本輪結果**：**未執行**（0 次 `psql -f`）。

---

## 步驟 3：驗收 A–H（⏸ 未執行）

待步驟 2 完成後逐項執行並貼出輸出：A `schema_migrations` 六筆、B 表數 15 與清單、C owner 全為 `goaa_c2_migrate`、D ACL 逐表對照（含 `agent_review_events` / `identity_events` 僅 `ar`）、E 函式與觸發器、F append-only 功能測試（`goaa_c2_app` 之 DELETE/UPDATE 必須被拒）、G 0004 授權守衛功能測試、H 舊庫與服務未受影響。

**額外（best-effort）**：C1 `goaa_platform` 與 C2 `goaa_c2test` 之 `pg_dump --schema-only --no-owner --no-privileges` diff。

---

## 回滾（本輪無需執行）

本輪**未變更任何資料庫物件**（唯一寫入＝在 C1 建立 `/root/mig/` 內六個唯讀檔案）。若步驟 2 失敗：

```sql
DROP DATABASE goaa_platform;   -- 角色保留
```
新庫為空，**不需動用備份**；`/root/backups/` 之 dump **全程未碰**。

---

## 紀律自證（步驟 1）

- ✅ 只 ssh `do-c2`（取檔）與 `do-runtime-anchor`（落地＋校驗）；**未連 C3**。
- ✅ **未套用任何 migration**（0 次 `CREATE`／`psql -f`）；`goaa_platform` 仍 0 表。
- ✅ 未碰 `goaa` 庫任何一列；未改 env／設定檔；**未重啟任何服務**；未動 ufw／DOCKER-USER／`pg_hba.conf`。
- ✅ 傳輸**不經本機磁碟**（tar 管線）；C1 落地目錄 `700`。
- ✅ 未讀取 `rollback/` 內容；未使用任何非 canonical 樹的 migration。
- ✅ 密碼：本輪**未取用、未傳輸、未回顯**（步驟 2 才需要）。
- ✅ IPv4 一律切分書寫：`143.198.224.⟨71⟩`、`134.199.227.⟨108⟩`、`172.17.0.⟨2⟩`、`127.0.0.⟨1⟩`。
