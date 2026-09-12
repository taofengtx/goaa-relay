# D0.2 — 收掉 5432 公網可達（方案 A：`DOCKER-USER` + `/etc/ufw/after.rules`）
## 變更階段：套用 ＋ 驗收 A–H

- **主機**：`do-runtime-anchor`（C1 生產主機，`goaa-aika-cloud-1`）
- **執行窗口**：2026-09-12T00:42:33Z → 00:53:30Z（含 H 的 10 分鐘觀察窗）
- **執行方式**：照 Round D0.2 變更階段**逐字**執行；區塊 10 行 byte 級比對過（em dash `U+2014`、無尾隨空白）才寫入
- **結果**：**`APPLY_RESULT=APPLIED_AND_VERIFIED`**
- **轉寫聲明（重要）**：本報告所有 IPv4 **末段以 `⟨N⟩` 切分書寫**（依令要求，避免掃描器把報告本身算成命中）；`0.0.0.⟨0⟩/0` 即原輸出的全零位址。**未經轉寫的逐字輸出**存於主機 `/tmp/d02-apply-out.txt`（及本機副本），**未進倉**。

---

## 0. 一頁看懂

| 項目 | 結果 |
|---|---|
| `grep -c 'GOAA D0.2'` 套用前／後 | `0` → `2`（BEGIN＋END） |
| `after.rules` 行數 | `30` → **`40`** |
| `after.rules` mode/owner | `640 root:root` → **`640 root:root`（未變）** |
| `after.rules` sha256（前 16 位） | `c1be61c17e850ea1` → **`f6a1794c355b50db`** |
| `iptables-restore --test -n` | **rc=0** |
| `ufw reload` | **rc=0（Firewall reloaded）** |
| **A** 規則就位 | **5 條、順序正確、`(1 references)`** ✅ |
| **B** 本機 DB 仍可連 | **TCP `127.0.0.⟨1⟩:5432` 連得上** ✅（`pg_isready` 未安裝 → 以 TCP 層檢查替代，未用任何憑據） |
| **C** 後端健康 | **`goaa-router` active、`/health` HTTP 200** ✅ |
| **D** 容器行為不變 | heartbeat 照舊、openclaw 無新連線錯誤（僅既有 Censys 掃描＋我 00:33:33 的基線對照 GET）✅ |
| **E** 跳轉仍在 | `FORWARD` rule 1 = `DOCKER-USER`、`(1 references)` ✅ |
| **F** 撐過還原（未重開機） | `iptables -F DOCKER-USER` + `ufw reload` → **5 條完整回來**（6 行）✅ |
| **G** 冪等實測 | **G1=6、G2=6、G3=6 ⇒ 無重複累積** ✅（**更正前置報告的推論**，見第 8 節） |
| **H** 擋下爆破證據 | DROP 計數 **0 → 18 pkts**（10 分鐘）；`goaa-postgres` 近 10 分鐘 **FATAL 1 → 0**；FATAL **總數 484,031 不變** ✅ |
| **I** 外部驗收 | **由 Tao 執行（IPv4）**；本機未對外發起任何掃描或連線 |
| 變更後快照 | `/root/iptables-save.after-d0-2.20260912-005330.txt`（7,579 B、sha256 前 16 位 `7781b46a49f3c1cc`） |

**未做（依令）**：D0.3（8080）、D0.4（`goaa-model-router`）、`17879`、`before.init` / `after.init`、`pg_hba.conf`、`log_line_prefix`、資料庫內容；未重建容器；未重啟 `goaa-web` / `goaa-router` / `goaa-postgres`；未裝套件；未對外掃描。**本輪未重啟任何服務 → 無 🛡 審批卡。**

---

## 1. 步驟 1：套用前檢查（逐字輸出）

```
$ grep -c 'GOAA D0.2' /etc/ufw/after.rules
0                       ← 必須為 0：通過
$ wc -l /etc/ufw/after.rules
30 /etc/ufw/after.rules
$ sha256sum /etc/ufw/after.rules
c1be61c17e850ea1…（全長見 /tmp/d02-apply-out.txt）  /etc/ufw/after.rules
$ sha256sum /etc/ufw/after.rules.bak.20260912-002911
c1be61c17e850ea1…（全長見 /tmp/d02-apply-out.txt）  /etc/ufw/after.rules.bak.20260912-002911
$ stat -c '%a %U:%G' /etc/ufw/after.rules
640 root:root 1004
```

→ 三項皆與前置報告一致（`grep`=0、30 行、**原檔與備份逐位元相同**）；`PERM_BEFORE=640 OWNER_BEFORE=root:root`。

## 2. 步驟 2：追加區塊（檔尾、最後一個 `COMMIT` 之後）

追加內容（10 行，逐字，未增減）：

```
# BEGIN GOAA D0.2 — block public 5432 at the docker FORWARD hook
*filter
:DOCKER-USER - [0:0]
-A DOCKER-USER -m conntrack --ctstate RELATED,ESTABLISHED -j RETURN
-A DOCKER-USER -i docker0 -j RETURN
-A DOCKER-USER -i br-03d6f0fd0feb -j RETURN
-A DOCKER-USER -i br-a8f5e58918aa -j RETURN
-A DOCKER-USER -p tcp --dport 5432 -j DROP
COMMIT
# END GOAA D0.2
```

追加後檢查（逐字輸出）：

```
append_rc=0
$ wc -l /etc/ufw/after.rules
40 /etc/ufw/after.rules
$ stat -c '%a %U:%G' /etc/ufw/after.rules
640 root:root 1358
MODE_AFTER=640 root:root
mode/owner unchanged: OK
$ grep -n 'GOAA D0.2' /etc/ufw/after.rules
31:# BEGIN GOAA D0.2 — block public 5432 at the docker FORWARD hook
40:# END GOAA D0.2
$ tail -12 /etc/ufw/after.rules
# don't delete the 'COMMIT' line or these rules won't be processed
COMMIT
# BEGIN GOAA D0.2 — block public 5432 at the docker FORWARD hook
*filter
:DOCKER-USER - [0:0]
-A DOCKER-USER -m conntrack --ctstate RELATED,ESTABLISHED -j RETURN
-A DOCKER-USER -i docker0 -j RETURN
-A DOCKER-USER -i br-03d6f0fd0feb -j RETURN
-A DOCKER-USER -i br-a8f5e58918aa -j RETURN
-A DOCKER-USER -p tcp --dport 5432 -j DROP
COMMIT
# END GOAA D0.2
$ sha256sum /etc/ufw/after.rules
f6a1794c355b50db…（全長見 /tmp/d02-apply-out.txt）  /etc/ufw/after.rules
```

語法驗證：

```
$ iptables-restore --test -n < /etc/ufw/after.rules
iptables_restore_test_rc=0        ← 通過
```

→ 行數 30→40（+10，與令預期一致）；`mode/owner` **未被改動**；既有 30 行未動（區塊自第 31 行起）。

## 3. 步驟 3：套用

```
$ ufw reload
Firewall reloaded
ufw_reload_rc=0
$ grep -c 'GOAA D0.2' /etc/ufw/after.rules
2
```

→ 套用成功（未用 `ufw disable` / `enable` / `reset`）；`ssh` 未斷線。

## 4. 驗收 A–H（每項：指令 ＋ 輸出）

### A — 規則就位

```
$ iptables -vnL DOCKER-USER --line-numbers
Chain DOCKER-USER (1 references)
num   pkts bytes target     prot opt in     out     source               destination
1        0     0 RETURN     0    --  *      *       0.0.0.⟨0⟩/0            0.0.0.⟨0⟩/0            ctstate RELATED,ESTABLISHED
2        0     0 RETURN     0    --  docker0 *       0.0.0.⟨0⟩/0            0.0.0.⟨0⟩/0
3        0     0 RETURN     0    --  br-03d6f0fd0feb *       0.0.0.⟨0⟩/0            0.0.0.⟨0⟩/0
4        0     0 RETURN     0    --  br-a8f5e58918aa *       0.0.0.⟨0⟩/0            0.0.0.⟨0⟩/0
5        0     0 DROP       6    --  *      *       0.0.0.⟨0⟩/0            0.0.0.⟨0⟩/0            tcp dpt:5432
```

→ **5 條、順序與令完全相同**（conntrack RETURN → docker0 RETURN → br-03d6f0fd0feb RETURN → br-a8f5e58918aa RETURN → tcp dpt:5432 DROP），`(1 references)`。

### B — 本機 DB 仍可連

```
NOTE: pg_isready is NOT installed on this host (and psql is not either);
      B is therefore done at TCP level against the published port, no credentials used.
$ timeout 5 bash -c '</dev/tcp/127.0.0.⟨1⟩/5432'
tcp_connect_127.0.0.⟨1⟩_5432=OK
$ ss -tanp | grep -c '127.0.0.⟨1⟩:5432'
13
```

→ **通過**。`pg_isready` 在本機不存在（`psql` 亦然），故 B 以 TCP 層對已發佈埠驗證（**未帶密碼、未進資料庫**）；輔證：主機側仍有 13 個 `127.0.0.⟨1⟩:5432` socket（含 `goaa-router` 的 uvicorn 連線）。

### C — 後端健康

```
$ systemctl is-active goaa-router
active
$ curl -s -o /dev/null -m 5 -w '%{http_code}' http://127.0.0.⟨1⟩:8080/health
200
C_SVC=active C_HTTP=200 C_OK=1
```

→ **通過**。

> B／C 皆通過 ⇒ 未觸發失敗處理（未回滾）。

### D — 容器行為不變

```
$ docker logs --tail 20 goaa-heartbeat
heartbeat × 20
$ docker logs --tail 20 goaa-openclaw
66.132.195.⟨76⟩ ... 400 (TLS 亂碼)                     ← 2026-09-10 既有掃描
66.132.172.⟨41⟩ ... 400 / GET / 200 / PRI * HTTP/2.0 400 / favicon 404 / login 404 / 400
             （User-Agent: CensysInspect/1.1；host: 134.199.227.⟨108⟩:17879）
66.132.195.⟨74⟩ ... GET / 200 / 400 / PRI * 400 / favicon 404 / security.txt 404 / 400
             （同為 CensysInspect/1.1；host: 134.199.227.⟨108⟩:17879）
172.18.0.⟨1⟩ - - [12/Sep/2026:00:33:33 +0000] "GET / HTTP/1.1" 200 896 "-" "curl/8.5.0"
             ← 本報告前置階段「路徑實測」的那一次本機 GET（已知、非本次變更造成）
```

→ **與前置報告第 1.3 節基線一致**：heartbeat 照舊輸出；openclaw 只有**既有**的外部掃描紀錄（最新外部條目停在 `2026-09-11 16:58:01`）與我前置階段的對照 GET，**無任何新的連線錯誤**。（長 hex 載荷為可讀性以 `...` 略，狀態碼／時間／來源皆原樣。）

### E — 跳轉仍在

```
$ iptables -vnxL FORWARD --line-numbers
Chain FORWARD (policy DROP 0 packets, 0 bytes)
num      pkts      bytes target                    prot opt in     out     source               destination
1      144537 11624235 DOCKER-USER               0    --  *      *       0.0.0.⟨0⟩/0            0.0.0.⟨0⟩/0
2      144537 11624235 DOCKER-FORWARD            0    --  *      *       0.0.0.⟨0⟩/0            0.0.0.⟨0⟩/0
3           0        0 ufw-before-logging-forward 0   --  *      *       0.0.0.⟨0⟩/0            0.0.0.⟨0⟩/0
...（ufw-before-forward / ufw-after-forward / ufw-after-logging-forward / ufw-reject-forward / ufw-track-forward）
```

```
Chain DOCKER-USER (1 references)
```

→ **rule 1 仍是 `DOCKER-USER`，且 `1 references`** ⇒ 我們放進去的規則**有人引用**，不會變孤兒。

### F — 撐過重開機的證明（不重開機）

```
$ iptables -F DOCKER-USER && ufw reload && iptables -S DOCKER-USER
flush_rc=0
Firewall reloaded
reload_rc=0
-N DOCKER-USER
-A DOCKER-USER -m conntrack --ctstate RELATED,ESTABLISHED -j RETURN
-A DOCKER-USER -i docker0 -j RETURN
-A DOCKER-USER -i br-03d6f0fd0feb -j RETURN
-A DOCKER-USER -i br-a8f5e58918aa -j RETURN
-A DOCKER-USER -p tcp -m tcp --dport 5432 -j DROP
F_line_count=6
```

→ 清空後 `ufw reload` **把 5 條完整還原** ⇒ 證明 `/etc/ufw/after.rules` 在開機流程（`ufw-init start`）會被還原，規則**撐得過重開機**。

### G — 冪等實測（Tao 指定）

```
G1=6            ← 乾淨狀態（F 之後）：-N + 5 條
$ ufw reload
Firewall reloaded
reload_rc=0
G2=6
NO_DUPLICATION: G2=6 == G1=6
G3_after_cleanup=6
```

→ **G1=G2=G3=6 ⇒ 每次 `ufw reload` 不會追加第二份**；故未觸發「收尾必做」的清理（清理指令仍已備妥且有記錄）。**此結果與前置報告的推論相反 → 見第 8 節更正。**

### H — 擋下爆破的直接證據（10 分鐘窗口）

| | t0（00:42:43Z） | t1（00:53:06Z，+10 分） | 差異 |
|---|---|---|---|
| `DOCKER-USER` 第 5 條（`tcp dpt:5432` DROP）pkts | **0** | **18** | **+18**（1,080 bytes） |
| `docker logs --since 10m goaa-postgres \| grep -c FATAL` | **1** | **0** | **−1** |
| `docker logs goaa-postgres \| grep -c FATAL`（總數） | **484,031** | **484,031** | **±0** |

→ **三重證據**：① 有 18 個外部連線封包被規則**丟棄**（規則確實攔在 FORWARD 前段、外部路徑上）；② 近 10 分鐘的 postgres 認證失敗由 **1 降到 0**；③ FATAL **總數在整個窗口內完全不動**（前置報告的日基線為每日 300–460 次，10 分鐘期望值約 2–3 次 ⇒ 實際 0）。**爆破已被切斷。**（外部視角的獨立驗收 = 步驟 I，由 Tao 執行。）

## 5. 收尾：變更後快照

```
$ iptables-save > /root/iptables-save.after-d0-2.20260912-005330.txt
AFTER_SNAPSHOT=/root/iptables-save.after-d0-2.20260912-005330.txt
-rw-r--r-- 1 root root 7579 Sep 12 00:53 /root/iptables-save.after-d0-2.20260912-005330.txt
7781b46a49f3c1cc…（全長見 /tmp/d02-apply-out.txt）
```

最終狀態複驗（在 F／G 的 flush＋reload 之後才做）：

```
$ iptables -S DOCKER-USER | wc -l        → 6
$ timeout 5 bash -c '</dev/tcp/127.0.0.⟨1⟩/5432'   → OK
$ ss -tanp | grep -c '127.0.0.⟨1⟩:5432'  → 13
$ systemctl is-active goaa-router        → active
$ curl .../health                        → 200
$ /etc/ufw/after.rules                   → 40 行、640 root:root、1358 B、sha256 前 16 位 f6a1794c355b50db
```

## 6. 改前／改後對照

| | 改前 | 改後 |
|---|---|---|
| `DOCKER-USER` | 0 條（`-N` 一行） | **5 條**（順序：ESTABLISHED RETURN、docker0、br-03d6f0fd0feb、br-a8f5e58918aa、tcp 5432 DROP） |
| `after.rules` | 30 行 / 1,004 B / `c1be61c17e850ea1` | **40 行 / 1,358 B / `f6a1794c355b50db`** |
| `after.rules` mode/owner | `640 root:root` | **`640 root:root`（未變）** |
| 外部 5432 | 公網可達、**持續被爆破**（累計 48.4 萬次 FATAL） | **被 DROP**；窗口內 FATAL 0、總數凍結在 484,031 |
| 本機 5432／`goaa-router` DB | 正常 | **正常（不變）** |
| `17879`（openclaw） | 公網可達、被外部掃描 | **未處理（依令，另一輪）** |

## 7. 回滾步驟

1. 刪除 `/etc/ufw/after.rules` 內 `# BEGIN GOAA D0.2` 起、`# END GOAA D0.2` 止的整段（第 31–40 行），或直接以備份還原：
   `cp -a /etc/ufw/after.rules.bak.20260912-002911 /etc/ufw/after.rules`
2. `ufw reload`
3. `iptables -F DOCKER-USER`（清掉已生效的 5 條；基線時該鏈為空 ⇒ 回到基線）
4. 覆核：`iptables -S DOCKER-USER | wc -l` = 1；`timeout 5 bash -c '</dev/tcp/127.0.0.⟨1⟩/5432'` OK；`systemctl is-active goaa-router` = active
5. （必要時）以 `/root/iptables-save.before-d0-2.20260912-002911.txt` 全量還原 iptables

**已備份／可還原**：`/etc/ufw/after.rules.bak.20260912-002911`（1,004 B、與改前原檔逐位元相同）、`/root/iptables-save.before-d0-2.20260912-002911.txt`（7,348 B）、`/root/iptables-save.after-d0-2.20260912-005330.txt`（7,579 B）。

## 8. 與前置報告的差異（**更正**）

前置報告第 4.2/4.3 節曾**以源碼推論**預測「`-n`（noflush）＋既有 `DOCKER-USER` ⇒ 每次 `ufw reload` 會追加 5 行」，並據此提出「選項 2：改 `before.init` 讓它冪等」。**實測推翻此推論**：

- **G1=G2=6**：`ufw reload` 兩次後仍是 6 行 ⇒ **本機 ufw 0.36.2 / iptables 的 `iptables-restore -n` 對「已在輸入中宣告的鏈」具有重置效果，不會累加**。
- 因此：**不需要 `before.init` 修補輪**；`before.init` 全程未動（依令）。**Tao 的原始草案即為冪等設計，維持原樣。**
- 教訓（已寫入記憶）：**init 腳本的旗標語義不能只靠源碼推論，必須實測**；驗收 G 正是那個實測，感謝指定。

## 9. 掃描（推送前）

對本報告（`APPLY.md`）與前置報告（`REPORT.md`）執行掃描，樣式均以**切分形式**書寫以免自我命中：

| 樣式（切分寫法） | 命中數 |
|---|---|
| `sk_li` + `ve` | 0 |
| `BEGIN PRIVATE` + ` KEY` | 0 |
| `AK` + `IA` | 0 |
| `gh` + `p_` | 0 |
| `postgres` + `://` | 0 |
| IPv4 實字（四段數字） | 0（皆已 `⟨N⟩` 切分） |
| hex32+ | 0（sha256 只留前 16 位） |
| 其餘（Bearer 實字、JWT 形、`pass` + `word=`、full key 形） | 0 |

命令與輸出見提交訊息附註；本輪**未讀取任何 env 值或金鑰**（僅出現變數名與檔名）。

## 10. 收尾後續確認（唯讀；2026-09-12T00:59:39Z，套用後約 17 分鐘）

| 項目 | 值 |
|---|---|
| `DOCKER-USER` 第 5 條（`tcp dpt:5432` DROP）pkts | **27**（H 的 t1 為 18 ⇒ **持續攔阻中**） |
| `/etc/ufw/after.rules` | 40 行、`640 root:root`、sha256 前 16 位 **`f6a1794c355b50db`（未變）** |
| `goaa-postgres` FATAL 總數 | **484,031（仍凍結，與 H 的 t0/t1 相同）** |
| FATAL 最後一筆時間 | **`2026-09-12 00:38:18`Z** ⇒ **早於本次套用（00:42:33Z）** ⇒ **套用後零認證失敗** |
| `docker logs --since 10m` FATAL | **0** |
| `goaa-router` / `/health` | **active / 200** |

→ 止血**持續有效**（非僅 H 的單一窗口）；外部視角驗收（步驟 I）仍由 Tao 執行。本主機全程未對外發起任何連線或掃描。

## 11. 外部視角驗收（步驟 I，由 Tao 執行，2026-09-12）

Tao 從本機 Windows 執行 `Test-NetConnection`，逐字結果：

```
22 -> True ；5432 -> False（WARNING: TCP connect to (<C1 公網 IP> : 5432) failed）
```

**結論**：外部 IPv4 已無法連上 5432；對照組 22 通，證明測試路徑有效。

→ D0.2 全項（A–H 由 Aika 於主機內執行、I 由 Tao 於外部執行）**驗收閉環完成**；本輪止血目標達成。
