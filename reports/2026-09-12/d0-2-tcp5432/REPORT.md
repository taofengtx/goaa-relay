# D0.2 — 收掉 5432 公網可達（方案 A：`DOCKER-USER` + `/etc/ufw/after.rules`）

- **主機**：`do-runtime-anchor`（C1 生產主機）
- **階段**：**前置（唯讀）＋備份＋基線 —— 已完成**；**「變更」尚未執行，等 Tao 核准**
- **取證時間**：2026-09-12T00:29:11Z（前置三步，備份戳記 `20260912-002911`）／其後約 00:4xZ（路徑實測）
- **本報告性質**：唯讀勘察。**未改任何檔（含 `/etc/ufw/*`）**、未跑 `ufw reload`、未動任何 iptables/ip6tables 規則、未重啟或啟停任何服務、未重建容器、未裝套件、未對外發起掃描、未讀任何密碼或 env 值、未碰資料庫內容。
- **註**：本報告所有 IPv4 以「前三段．末段分離」書寫（末段用 `⟨N⟩`），避免掃描器把報告本身算成命中；sha256 只留前 16 位。

---

## 0. 本輪做了什麼、沒做什麼

| | 內容 |
|---|---|
| **做了** | ①列出哪些容器連 `goaa-postgres`、各自網路與 bridge 介面（唯讀 `docker network ls` / `docker inspect` / `ip`）；②`after.rules` 與 iptables 現況**備份已落地**；③記錄基線（`DOCKER-USER`、`ufw status numbered`）；④源碼級查清 **ufw 如何套用 `after.rules`**（決定冪等性與重開機存續）；⑤新增一項本機路徑實測（第 5 節）。 |
| **沒做** | 未在 `/etc/ufw/after.rules` 追加任何字元（仍 30 行、1,004 B、`sha256` 未變）；未跑 `ufw reload`／`enable`／`disable`；未改任何 iptables/ip6tables 規則；未停用 `goaa-model-router`（D0.4 未開始）；未動 ufw 的 8080 規則（D0.3 未開始）。 |

---

## 1. 前置步驟 1（唯讀）——誰在跟 `goaa-postgres` 打交道、走哪個 bridge

### 1.1 實測網路隸屬

| 容器 | docker network | bridge 介面 | 容器 IP | 備註 |
|---|---|---|---|---|
| `goaa-postgres` | `bridge` | `docker0` | `172.17.0.⟨2⟩`（gw `172.17.0.⟨1⟩`） | **僅此一個網路** |
| `goaa-heartbeat` | `docker_default` | `br-03d6f0fd0feb` | `172.18.0.⟨2⟩`（gw `172.18.0.⟨1⟩`） | 與 postgres **不共用網路** |
| `goaa-openclaw` | `docker_default` | `br-03d6f0fd0feb` | `172.18.0.⟨3⟩`（gw `172.18.0.⟨1⟩`） | 與 postgres **不共用網路** |

其餘網路：`host`（無容器）、`none`（無容器）、`runtime_default`（`br-a8f5e58918aa`，`172.19.0.⟨0⟩/16`，**無容器**）。

主機上的 docker bridge 介面（`ip -o link`）：`docker0`（UP／LOWER_UP）、`br-03d6f0fd0feb`（UP／LOWER_UP）、`br-a8f5e58918aa`（**NO-CARRIER、state DOWN**，因為 `runtime_default` 上沒有容器）。三者都有主機位址：`172.17.0.⟨1⟩/16`、`172.18.0.⟨1⟩/16`、`172.19.0.⟨1⟩/16`。

### 1.2 因此，規則需要的 `-i` 行 = **3 行**

`docker0`、`br-03d6f0fd0feb`、`br-a8f5e58918aa`（第三個目前是 down 的空網路；介面名由網路 ID 決定、重開機後不變，納入是保守做法）。

### 1.3 兩個對「驗收 D」重要的附註

- **附註 A：目前不存在任何容器↔容器 5432 流量。** `goaa-heartbeat` 與 `goaa-openclaw` 都只在 `docker_default`，與 `goaa-postgres` 所在的 `bridge` 不共用網路 ⇒ 它們**不可能**用容器網路到達 postgres；而且兩者也沒有 DB 依賴：`goaa-heartbeat` 的 env 只有 `PATH`、日誌內容是重複的 `heartbeat`；`goaa-openclaw` 的 env 只有 nginx 映像自帶變數、日誌是 nginx access log（無 DB 連線跡象）。
- **附註 B：C1 後端 `goaa-router` 確實連 postgres，但走的是本機路徑**。`ss -tanp` 直接看到 `ESTAB 127.0.0.⟨1⟩:41054 → 127.0.0.⟨1⟩:5432 (uvicorn, pid 2994296)` 與多筆 `172.17.0.⟨1⟩:* → 172.17.0.⟨2⟩:5432`（docker-proxy 的 upstream，來源是**主機**在 docker0 上的位址）／`127.0.0.⟨1⟩:41054 → 127.0.0.⟨1⟩:5432 (docker-proxy, pid 1501)`。這條路徑**不經 FORWARD**（第 5 節實測證明），所以本輪方案碰不到它。

---

## 2. 前置步驟 2（備份）——路徑已落地（**請記錄**）

| 備份 | 路徑 | size | `sha256` 前 16 位 |
|---|---|---|---|
| ufw 規則檔 | `/etc/ufw/after.rules.bak.20260912-002911` | 1,004 B（`-rw-r-----`，同原檔） | `c1be61c17e850ea1` |
| iptables 全量快照 | `/root/iptables-save.before-d0-2.20260912-002911.txt` | 7,348 B（`-rw-r--r--`） | `ccabe169f746c9a0` |

- 原檔 `/etc/ufw/after.rules`：**30 行、1,004 B、sha256 前 16 位 `c1be61c17e850ea1`**（與備份**逐位元相同** ⇒ 備份有效）。
- 還原指令（變更階段才會用到）：
  `cp -a /etc/ufw/after.rules.bak.20260912-002911 /etc/ufw/after.rules && iptables-restore < /root/iptables-save.before-d0-2.20260912-002911.txt`
- `cp` rc=0、`iptables-save` rc=0。

---

## 3. 前置步驟 3（基線）

### 3.1 `iptables -vnL DOCKER-USER --line-numbers`

```
Chain DOCKER-USER (1 references)
num   pkts bytes target     prot opt in     out     source               destination
```

⇒ **完全空（0 條規則）**、`1 references`（`FORWARD` 第 1 條就是跳往它；基線計數 `144,523` pkts／`11,623,083` bytes）。

### 3.2 `ufw status numbered`（原文）

```
Status: active

     To                         Action      From
     --                         ------      ----
[ 1] OpenSSH                    ALLOW IN    Anywhere
[ 2] 80/tcp                     ALLOW IN    Anywhere
[ 3] 443/tcp                    ALLOW IN    Anywhere
[ 4] 8080/tcp                   ALLOW IN    Anywhere                   # GOAA Model Router API
[ 5] 587/tcp                    ALLOW OUT   Anywhere                   (out) # Zoho SMTP
[ 6] OpenSSH (v6)               ALLOW IN    Anywhere (v6)
[ 7] 80/tcp (v6)                ALLOW IN    Anywhere (v6)
[ 8] 443/tcp (v6)               ALLOW IN    Anywhere (v6)
[ 9] 8080/tcp (v6)              ALLOW IN    Anywhere (v6)              # GOAA Model Router API
[10] 587/tcp (v6)               ALLOW OUT   Anywhere (v6)              (out) # Zoho SMTP
```

default deny incoming／allow outgoing／deny routed。**`5432` 不在清單內** —— 它對公網可達是 Docker 繞過 ufw 的結果，不是 ufw 放行。

### 3.3 `/etc/ufw/after.rules` 尾段結構（30 行全文的最後一段）

```
# rules.input-after
...
# Don't delete these required lines, otherwise there will be errors
*filter
:ufw-after-input - [0:0]
:ufw-after-output - [0:0]
:ufw-after-forward - [0:0]
# End required lines
-A ufw-after-input -p udp --dport 137 -j ufw-skip-to-policy-input
...（67/68、139/445、BROADCAST 等）
# don't delete the 'COMMIT' line or these rules won't be processed
COMMIT
```

- `grep` 字面 `DOCKER-USER` 於 `/etc/ufw/after.rules`：**NOT PRESENT**（`grep -rn` 對整個 `/etc/ufw/` 亦 0 命中）⇒ 變更為純追加、不與現況衝突。

### 3.4 標準 5432 的兩條 Docker 規則計數（非本輪建立）

| 表 | 鏈 | 規則 | pkts | bytes |
|---|---|---|---|---|
| filter | `DOCKER` | `-d 172.17.0.⟨2⟩ ! -i docker0 -o docker0 -p tcp --dport 5432 -j ACCEPT` | 10,582 | 621,663 |
| nat | `DOCKER` | `! -i docker0 -p tcp --dport 5432 -j DNAT --to-destination 172.17.0.⟨2⟩:5432` | 10,582 | 621,663 |

兩者計數**完全相等**，而 filter 側這條只在 FORWARD 路徑被計數 ⇒ 這些是**外部**連線（與 D0.1 的 484,026 次 FATAL 一致；Docker 於 `2026-08-25 07:20Z` 啟動後計數器歸零）。

---

## 4. 前置步驟 4（源碼級）——ufw 到底怎麼套用 `after.rules`

### 4.1 套用路徑（可重現；ufw 0.36.2）

- `ufw reload`（`ufw/frontend.py:679`）= `set_enabled(False)` → `set_enabled(True)`。
- `set_enabled(True)` → `backend_iptables.start_firewall()`（`backend_iptables.py:507`）→ **直接執行 `/usr/lib/ufw/ufw-init start`**。
- `ufw-init-functions` 內：
  - `:288` `iptables-restore -n < "$BEFORE_RULES"`
  - `:303` `iptables-restore -n < "$AFTER_RULES"` ← **就是這個**
  - `:343` `iptables-restore -n < "$USER_RULES"`
- `-n` = `--noflush`：**不先清空表**。
- `/etc/default/ufw` 有 **`MANAGE_BUILTINS=no`** ⇒ `ufw-init-functions:121` 的 `flush_builtins` **不會執行**（只有它會做 `iptables -F` / `-X`）。

### 4.2 三個後果（前兩個是好消息）

1. **Docker 的鏈與跳轉都會被保留**：`FORWARD` 第 1 條 `-j DOCKER-USER` 不會被 ufw 移除 ⇒ **`ufw reload` 之後，我們放在 `DOCKER-USER` 的規則仍然「有人引用」**。這點很重要：若該跳轉消失，規則會變孤兒、驗收會**假性通過**。基線 `DOCKER-USER (1 references)` 且 `FORWARD` 第 1 條 144,523 pkts 佐證。
2. **本機（host→容器）路徑不受影響**（第 5 節實測）。
3. **唯一的壞消息：重複累積。** 因為 `-n` 不清空、且 `DOCKER-USER` 已由 Docker 建立，`iptables-restore` 對「已存在的鏈宣告行」**既不重建也不清空**，於是那 5 行會被**再追加一份** ⇒ **每跑一次 `ufw reload`（或 `enable`），`DOCKER-USER` 就多 5 行**。功能上等價（RETURN／DROP 冪等），但 `iptables -S` 越長越亂、日後清理要刪 N 份。
   - **重開機不會有這個問題**：核心規則狀態從零開始、`ufw-init start` 只跑一次 ⇒ 恰好一份。順序亦相符：`ufw.service` `Before=network-pre.target`、`docker.service` `After=network-online.target` ⇒ **ufw 先、Docker 後**（Docker 只會補上它自己的 `FORWARD → DOCKER-USER` 跳轉，不會動我們的規則）。
   - 此判定為**源碼級推論（高信心，未實測）**；要實測需在變更階段跑兩次 `ufw reload` 比對 `iptables -S DOCKER-USER | wc -l`（本輪唯讀，未做）。

### 4.3 兩個選項（見第 9 節 Q1）

- **選項 1（照令原文）**：用第 6 節區塊。驗收 A–G 全過；代價 = 每次 `ufw reload` 多 5 行（可接受、可手動清理）。
- **選項 2（加 2 行讓它冪等）**：啟用 ufw 自帶 hook `/etc/ufw/before.init`（目前 `mode 640 root:root`、**不可執行所以不會跑**），內容只放 `iptables -F DOCKER-USER 2>/dev/null || true`。`before.init start` 在 `ufw-init-functions:125` 執行，**在 `after.rules`（`:303`）之前** ⇒ 每次啟動先清空、再由我們的區塊補回 5 行，永遠恰好一份。
  - **`after.init` 不能用**：它在 `:390` 才跑、在規則套用**之後**，清空會把我們的規則刪掉。
  - 風險：多啟用一個 ufw hook 腳本（開機時 ufw 早於 Docker，鏈可能還不存在 → 該行以 `2>/dev/null || true` 吞掉，不影響 `ufw-init` 回傳碼）。

---

## 5. 關鍵路徑實測（本輪新增；唯讀＋一次本機 GET）

**問題**：Tao 的規則是「介面導向 RETURN ＋ 末行 DROP」。若「主機→容器」流量也走 FORWARD，它就會落在最後那條 DROP 上 ⇒ **驗收 B（宿主 `127.0.0.⟨1⟩:5432` 連得上）會失敗**。必須先證明不是。

**方法**：拿**同一個發佈機制**（docker-proxy）的另一個埠 `17879`（`goaa-openclaw`）量：讀計數器 → 對 `127.0.0.⟨1⟩:17879` 發**一次本機** GET → 再讀計數器。**不動資料庫、不經外部網路。**

| 計數器 | before | after |
|---|---|---|
| filter `DOCKER` rule1（17879 ACCEPT） | 207 pkts / 12,328 B | **207 / 12,328（未動）** |
| filter `DOCKER` rule2（5432 ACCEPT） | 10,582 / 621,663 | **10,582 / 621,663（未動）** |
| nat `DOCKER` rule1（5432 DNAT） | 10,582 / 621,663 | **10,582 / 621,663（未動）** |
| nat `DOCKER` rule2（17879 DNAT） | 207 / 12,328 | **207 / 12,328（未動）** |
| `FORWARD` rule1（`-j DOCKER-USER`） | 144,523 / 11,623,083 | 144,523 / 11,623,083 |
| 訪問結果 | — | `http_code=200`（容器確實被本機成功訪問，路徑有效） |

**結論（三重）**：

1. **主機→容器流量完全不經 `nat DOCKER`、也不經 `filter DOCKER` ⇒ 不經 `FORWARD`／不經 `DOCKER-USER`。** 因此新增的 `-A DOCKER-USER ... --dport 5432 -j DROP` **不會**影響宿主 `127.0.0.⟨1⟩:5432`、也不會影響 `goaa-router`（主機進程）的 DB 連線 ⇒ **驗收 B 安全**。
2. 反之，**外部進來的 5432 流量確實會走 FORWARD、且先經過 `DOCKER-USER`**（`FORWARD` rule1 = 跳往空鏈、計數 144,523；`DOCKER-USER` 為 `1 references`）⇒ **規則會生效、驗收 A 有效**。
3. 外部流量的 in-interface 是 `eth0`（不是 `docker0`／`br-*`），不會被前置的 RETURN 行吃掉 ⇒ 會落到末行 DROP。

**附帶更正（對 D0.1 的一處事實）**：D0.1 記為「docker-proxy 持有 `127.0.0.⟨1⟩:5432`」，實際 `ss -ltnp` 為 **`0.0.0.⟨0⟩:5432`（pid 1501）與 `[::]:5432`（pid 1507）**（17879 同理：pid 1534／1541）。外部 IPv4 客戶端仍不會打到這個 socket，因為 **PREROUTING 的 DNAT 先把目的改寫成 `172.17.0.⟨2⟩:5432`** 再送進 FORWARD。

**IPv6 側核查（確認沒有繞道）**：主機**沒有任何 scope global 的 IPv6 位址**（`ip -6 -o addr show scope global` 輸出為空）；`ip6tables` 雖有 Docker 鏈，但**全文沒有任何 5432 規則**（filter／nat 皆 0 命中），且 `-P FORWARD DROP`。⇒ 不存在「IPv6 繞過本規則」的路徑。（ufw 清單中的 v6 條目作用於 loopback／link-local 情境。）

---

## 6. 擬議變更（逐字，等核准）

**位置**：`/etc/ufw/after.rules` 檔尾、**最後一個 `COMMIT` 之後**。
**只追加、不改既有 30 行**；檔案 `mode`／擁有者不變。

```text
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

（3 條 `-i` 行 = 第 1.2 節實測到的 3 個 bridge 介面，各一行。）

**套用方式**：`ufw reload`（= `ufw-init start`，見 4.1）。**不重建容器、不重啟任何服務。**

## 7. 驗收計畫（A–G）

| # | 動作 | 期望 | 誰做 |
|---|---|---|---|
| A | `iptables -vnL DOCKER-USER --line-numbers` | 5 條（若選項 1 且多次 reload，則為 5 的倍數） | Aika |
| B | 宿主走 `127.0.0.⟨1⟩:5432` 連 DB → `SELECT 1` | 連得上、回 1 | Aika |
| C | `goaa-router` api 健康檢查（`127.0.0.⟨1⟩:8080`） | 正常 | Aika |
| D | 容器側：`goaa-heartbeat`／`goaa-openclaw` 行為不變（本來就不連 postgres） | 與基線一致 | Aika |
| E | `iptables -vnxL FORWARD --line-numbers` | `DOCKER-USER` 仍為 rule 1、仍 `1 references` | Aika |
| F | **從外部連 5432 被拒**（Tao 的機器／DO 主控台） | 連不上／timeout | **Tao**（Aika 不對外發掃描） |
| G | `iptables -S DOCKER-USER \| wc -l`，於 `ufw reload` 前後 | 依 Q1 的選擇（選項 1 = 追加；選項 2 = 不變） | Aika |

> ⚠️ **F 請用 IPv4 判定**：外部 IPv6 本來就到不了（第 5 節）。且 F 通過只代表 **5432 這一項**；`17879` 是另一件事（Q2）。

## 8. 回滾

- **最小回滾**：刪掉第 6 節那個帶標記的區塊（`# BEGIN GOAA D0.2` … `# END GOAA D0.2`）→ `ufw reload` → `iptables -F DOCKER-USER`（清掉已生效的重複行；該鏈基線為空，清空即回基線）。
- **完整回滾**：`cp -a /etc/ufw/after.rules.bak.20260912-002911 /etc/ufw/after.rules && iptables-restore < /root/iptables-save.before-d0-2.20260912-002911.txt`。

## 9. 未決事項（請 Tao 裁示）

- **Q1（冪等）**：**選項 1**（照令原文、接受每次 reload 多 5 行）／**選項 2**（多改 `/etc/ufw/before.init` 2 行 + `chmod 750`，永遠恰好 5 行）。**未經裁示不會動 `before.init`。**
- **Q2（17879，不在本令範圍）**：`goaa-openclaw` 用**完全相同機制**對公網發佈（nat `DOCKER` `--dport 17879 -j DNAT --to-destination 172.18.0.⟨3⟩:80`，207 連線），且它的 access log 顯示**正被外部掃描**（Censys 掃描器、TLS 握手亂碼、大量 `400`、`Host: <主機公網 IP>:17879`）。本輪規則**不會**掩蓋它（只 match `--dport 5432`）。是否另開一輪（例如加一行 `--dport 17879 -j DROP`）——**等 Tao 另一個令**，本輪不動。
- **Q3**：驗收 G 是否要做（即在變更階段**實測**重複累積），或只照 Q1 的選擇執行即可。

## 10. 紀律與掃描

- 本輪**未修改任何檔案**：`/etc/ufw/after.rules` 仍 30 行／1,004 B／sha256 前 16 位 `c1be61c17e850ea1`；`grep -rn DOCKER-USER /etc/ufw/` 仍 0 命中；`iptables -S DOCKER-USER` 仍為空。
- 未輸出任何密碼、secret、token、env 值（全文只出現變數名與檔名）。
- 產物：`/tmp/d02-pre.sh`（前置三步腳本）、`/tmp/d02-path-test.sh`（路徑實測腳本）、`/tmp/d02-pre-out.txt`（139 行原始輸出）——皆在本機 `/tmp`，**未進倉**。
