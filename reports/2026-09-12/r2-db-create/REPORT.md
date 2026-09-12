# Round R2 · 階段二 第一段 — 備份（步驟 1）＋ 建角色與庫（步驟 2–3）

- **時間**：2026-09-12 05:56 UTC（= 2026-09-11 22:56 PDT）
- **主機**：C1 `do-runtime-anchor`（`goaa-aika-cloud-1`，`134.199.227.⟨108⟩`）
- **執行者**：Aika
- **🔴 本輪狀態**：**步驟 1（備份）✅ 完成並驗收通過；步驟 2、步驟 3 ⏸ 未執行 —— 等待 Tao 核准。**
  - 依據：Tao 的指令在步驟 2 標題寫明 **「（我核准後才做；請先把步驟 1 回報給我）」**。此閘門優先於本輪標題與 §A–E 回報規格，故**停在步驟 1**，未建任何角色／庫。
  - 若 Tao 意為一次做完，回一句 go 即續作步驟 2–3。
- **紀律**：未碰 `goaa` 庫任何一列；未重啟任何服務；未動 ufw／DOCKER-USER；密碼全程未產生（步驟 2 未執行）；IPv4 切分；sha256 前 16。

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

## 步驟 2：建角色與庫 —— ⏸ **未執行（等待核准）**

未產生任何密碼檔、未寫任何 SQL 檔、未在容器內執行任何 `CREATE`。

規格（Tao 原令，保留待執行）：
- 角色：`goaa_c2_migrate`（owner/migrate）、`goaa_c2_app`（應用）—— **沿用 C2 同名**（0001–0006 的 20 條授權與 0004 守衛寫死 `goaa_c2_app`，改名會使守衛**靜默失效**）。
- 庫：`goaa_platform`，`OWNER goaa_c2_migrate`，`ENCODING UTF8`，`LC_COLLATE/LC_CTYPE en_US.utf8`，`TEMPLATE template0`。
- `REVOKE ALL ON DATABASE goaa_platform FROM PUBLIC;` ＋ `GRANT CONNECT … TO goaa_c2_migrate, goaa_c2_app;`
- 密碼：`openssl rand -base64 32 | tr -d '\n=+/' | cut -c1-32` 寫入 `/root/.goaa_platform_{migrate,app}.pw`（`umask 077`、`chmod 600`）；SQL 以 **檔案**形式送入容器，**密碼不上命令列、不回顯**，建完即刪。
- `ON_ERROR_STOP=1`；**不加 `-1`**（`CREATE DATABASE` 不能在交易內）。

## 步驟 3：驗收 A–E —— ⏸ **未執行（等待核准）**

| 項 | 內容 | 狀態 |
|---|---|---|
| A | `\du goaa_c2_*`（不得有 SUPERUSER／CREATEDB／CREATEROLE） | ⏸ |
| B | `pg_database` owner／encoding／collate／ctype 與 `goaa` 一致 | ⏸ |
| C | `goaa_c2_migrate`、`goaa_c2_app` 各以 PGPASSFILE 連 `goaa_platform` 執行 `select current_user, current_database();` | ⏸ |
| D | 現有 `goaa` 庫毫髮無傷（`datname='goaa'` → 1；`goaa` 的 public 表數；`goaa-router` active ＋ `127.0.0.⟨1⟩:8080` 健康檢查 200） | ⏸ |
| E | 新庫此刻為空（`information_schema.tables` where `table_schema='public'` → 0） | ⏸ |

## 回滾 —— **本輪無需回滾（未建立任何物件）**

待步驟 2 執行後的回滾指令（Tao 原令）：
```sql
DROP DATABASE goaa_platform;
DROP ROLE goaa_c2_app;
DROP ROLE goaa_c2_migrate;
```
（現有 `goaa` 庫全程未被觸碰；備份檔保留於 `/root/backups/`。）

## 密碼檔路徑（僅路徑，不列值）

- **尚未建立。** 步驟 2 執行後將為：`/root/.goaa_platform_migrate.pw`、`/root/.goaa_platform_app.pw`（屆時僅回報路徑，永不回報值）。

---

## 紀律自證

- ✅ 只 `ssh do-runtime-anchor`（C1）一次批次執行；**未連 C2／C3**。
- ✅ **未建任何角色／庫／物件**（本輪 0 個 `CREATE`）。
- ✅ **未跑任何 migration**。
- ✅ 未改 env／設定檔；**未重啟任何服務**；未動 ufw／DOCKER-USER。
- ✅ 未讀寫 `goaa` 庫的任何一列（僅 `pg_dump` 產出備份；`pg_restore --list` 只讀目錄）。
- ✅ 密碼：本輪**根本未產生**（步驟 2 未執行）；無密碼進命令列／報告／歷史。
- ✅ 備份完成後已清掉容器內暫存檔（`/tmp/goaa-*.dump`、`/tmp/v.dump`）。

---

## 秘密掃描（推送前，須為 0 命中）

樣式（切分書寫）：`"sk_" + "live_"`、`"BEGIN " + "PRIVATE KEY"`、`"AK" + "IA"`、`"gh" + "p_"`、`"postgres" + ":" + "//"`。

**掃描回報（推送前，逐樣式統計）**：

| 樣式（切分書寫） | 命中 |
|---|---|
| `"sk_" + "live_"` | **0** |
| `"BEGIN " + "PRIVATE KEY"` | **0** |
| `"AK" + "IA"` | **0** |
| `"gh" + "p_"` | **0** |
| `"postgres" + ":" + "//"` | **0** |
| **合計** | **0** ✅ |

**檔案完整性**：`REPORT.md` = **6,569 bytes**、`sha256` 前16 = `6b5ac690ac0de4f1`、首三 byte = `b'# R'`（**無 BOM**）。

**relay main sha**：`c1c2ffc4c2a490cc570ea8ac4db0bc76a4354552`
（本報告**內容** commit；其後的子提交僅用於寫入本行與上方掃描回報。）
