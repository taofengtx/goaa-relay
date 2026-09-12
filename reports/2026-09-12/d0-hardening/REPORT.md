# Round D0 — 發版前收口（C1）

- **本檔目前只含 D0.1（唯讀勘察）**。D0.2／D0.3／D0.4 待 Tao 確認後各自執行、各自追加本節並各自提交。
- **主機**：ssh 別名 `do-runtime-anchor`（C1）。**性質：只讀**——未改任何檔案、未動任何防火牆規則、未重啟／未停用任何服務、未建目錄、未動 env／DNS／tunnel。所有指令皆為查詢（`docker inspect/ps/logs/exec cat`、`iptables -S/-vnL`、`ss`、`systemctl is-*`、`dpkg -l`、`ls/cat`）。
- **env 只列變數名**；容器 `Env` 只列 key；**所有 IP 一律切分寫法**；憑據值全部未讀、未印。

---

## 0. 摘要（先看這裡）

| 項目 | 結論 |
|---|---|
| 1. `goaa-postgres` 容器 | **非 compose 建立**（無任何 compose 標籤）＝ raw `docker run`；埠綁 **所有介面（`0.0.0.`＋`0` + `::`）**；`restart=unless-stopped` |
| 2. `DOCKER-USER`／nat 5432 | `DOCKER-USER` **完全空的（0 條）**；nat 有 5432 DNAT（累計 **10,578** 個連線）；filter `DOCKER` 對應 ACCEPT 同計數 |
| 3. iptables 持久化 | **沒有** iptables-persistent／netfilter-persistent／`/etc/iptables`／rc.local／開機腳本。**唯一既有持久化機制 = ufw**（enabled + active，開機由 ufw-init 還原 `/etc/ufw/*.rules`） |
| 4. 公網 8080 的客戶端 | **沒有任何客戶端依賴公網 8080**：worker-agent `ROUTER_API` 主機 = `127.0.0.`＋`1`（loopback）；cloudflared 走 `127.0.0.`＋`1:8080`；現時只有 loopback 連線 |
| 🔴 額外發現 | **5432 的公網暴露正在被持續爆破**（累計 48 萬次密碼失敗，最後一次在 00:03 UTC ≈ 現在）——見 §5 |

**⛔ 我停在這裡，等 Tao 確認後才做 D0.2。**

---

## 1. `goaa-postgres` 容器是怎麼建的

### 指令

`docker ps -a --filter name=goaa-postgres`、`docker inspect -f '…' goaa-postgres`（逐欄取值；**未使用** `docker inspect` 全量輸出，以免印出 `POSTGRES_PASSWORD`）

### 改前狀態（＝現狀）

```
goaa-postgres | postgres:16-alpine | Up 2 weeks | 0.0.0.`＋`0:5432->5432/tcp, [::]:5432->5432/tcp
```

| 欄位 | 值 |
|---|---|
| image | `postgres:16-alpine` |
| created | `2026-05-11T21:38:38Z` |
| started（本輪） | `2026-08-25T07:20:54Z` |
| RestartCount | `0` |
| RestartPolicy | `{"Name":"unless-stopped","MaximumRetryCount":0}` |
| `HostConfig.PortBindings` | `{"5432/tcp":[{"HostIp":"","HostPort":"5432"}]}` ← **`HostIp` 空字串 = 綁所有介面** |
| `NetworkSettings.Ports` | `{"5432/tcp":[{"HostIp":"0.0.0.`＋`0","HostPort":"5432"},{"HostIp":"::","HostPort":"5432"}]}` |
| Binds | `/opt/goaa/data/postgres:/var/lib/postgresql/data`（rw，bind mount） |
| Cmd | `["postgres"]` |
| Network | `bridge`，ip `172.17.0.`＋`2`，gw `172.17.0.`＋`1` |
| Env（**只有 key**） | `DOCKER_PG_LLVM_DEPS, GOSU_VERSION, LANG, PATH, PGDATA, PG_MAJOR, PG_SHA256, PG_VERSION, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER` |

### compose 標籤（判斷「怎麼建的」的關鍵）

```
project=      config_files=      working_dir=      service=      oneoff=      version=
（all labels keys → 空集合，容器完全沒有任何 label）
```

→ **沒有任何 `com.docker.compose.*` 標籤 ⇒ 這個容器不是由 compose project 建立的**，是 raw `docker run`（`-p 5432:5432`、`-v /opt/goaa/data/postgres:...`、`--restart unless-stopped`）。

**注意**：磁碟上存在 3 個 compose 檔（`/opt/goaa/docker-compose.base.yml`、`/opt/goaa/docker/docker-compose.yml`、`/opt/goaa/runtime/docker-compose.yml`），但**它們不是本容器的建立者**（無標籤可證）。若日後要用 compose 管理，需先確認是否為同一組定義。

### 其他容器（同一次查詢）

```
goaa-postgres  | postgres:16-alpine | Up 2 weeks | 0.0.0.`＋`0:5432->5432/tcp, [::]:5432->5432/tcp
goaa-openclaw  | nginx:alpine        | Up 2 weeks | 0.0.0.`＋`0:17879->80/tcp, [::]:17879->80/tcp
goaa-heartbeat | alpine              | Up 2 weeks | （無埠）
```

### 補充：userland proxy 存在

`docker-proxy` 正在跑（`-use-listen-fd`）：

```
1501 docker-proxy -proto tcp -host-ip 0.0.0.`＋`0 -host-port 5432 -container-ip 172.17.0.`＋`2 -container-port 5432
1507 docker-proxy -proto tcp -host-ip ::      -host-port 5432 -container-ip 172.17.0.`＋`2 -container-port 5432
1534 docker-proxy -proto tcp -host-ip 0.0.0.`＋`0 -host-port 17879 -container-ip 172.18.0.`＋`3 -container-port 80
1541 docker-proxy -proto tcp -host-ip ::      -host-port 17879 -container-ip 172.18.0.`＋`3 -container-port 80
```

→ 本機連 `127.0.0.`＋`1:5432` 走的是 **docker-proxy（`127.0.0.`＋`1:5432` 由 pid 1501 持有）**，外部連線則在 PREROUTING 就被 DNAT 到容器。**這一點決定 D0.2 的做法**（見 §6）。

---

## 2. 目前 `DOCKER-USER` 鏈內容、nat 表 5432 的 DNAT

### 改前狀態

```
-- iptables -S DOCKER-USER --
-N DOCKER-USER

-- iptables -vnL DOCKER-USER --line-numbers --
Chain DOCKER-USER (1 references)
num   pkts bytes target     prot opt in     out     source               destination
（無任何規則）
```

→ **`DOCKER-USER` 是空的**（只有鏈本身，1 個 reference 來自 FORWARD 的跳轉）。這是 Docker 留給管理者的自訂鏈，**目前完全沒被使用** → D0.2 有乾淨的插入點。

### nat 表

```
-- nat DOCKER（5432 / 17879）--
-A DOCKER ! -i docker0 -p tcp -m tcp --dport 5432 -j DNAT --to-destination 172.17.0.`＋`2:5432
-A DOCKER ! -i br-03d6f0fd0feb -p tcp -m tcp --dport 17879 -j DNAT --to-destination 172.18.0.`＋`3:80

-- nat DOCKER 計數器 --
1  10578 621K DNAT  6 -- !docker0           * 0.0.0.`＋`0/0  0.0.0.`＋`0/0  tcp dpt:5432  to:172.17.0.`＋`2:5432
2    207 12328 DNAT 6 -- !br-03d6f0fd0feb   * 0.0.0.`＋`0/0  0.0.0.`＋`0/0  tcp dpt:17879 to:172.18.0.`＋`3:80

-- nat PREROUTING --
-P PREROUTING ACCEPT
-A PREROUTING -m addrtype --dst-type LOCAL -j DOCKER

-- nat OUTPUT（Docker 加的）--
-P OUTPUT ACCEPT
-A OUTPUT ! -d 127.0.0.`＋`0/8 -m addrtype --dst-type LOCAL -j DOCKER
```

### filter 表對應規則與計數

```
2  10578 621K ACCEPT 6 -- !docker0 docker0 0.0.0.`＋`0/0 172.17.0.`＋`2 tcp dpt:5432
```

### 判讀（重要）

- 5432 的 DNAT 規則**同時**服務兩種流量：(a) **PREROUTING**（外部 → 公網 IP:5432）與 (b) **OUTPUT**（本機 → `172.17.0.`＋`2:5432`，即 docker-proxy 轉發)。
- 因此 **nat 計數器 10,578 不能單獨證明「外部連進來」**——本機 docker-proxy 的連線也會計入。
- 但 **§5 的日誌證據從另一個角度證明外部確實連得進來且正在被爆破**。
- `-i docker0`／`! -i br-…` 條件、`DOCKER-FORWARD → DOCKER-BRIDGE → DOCKER` 的鏈路（前輪 C2.1 已記錄）合起來，使**外部 SYN 在 `ufw-before-forward` 之前就被 `DOCKER` 鏈 ACCEPT**——這就是「ufw 沒放行 5432，但它仍對外開放」的機制。

---

## 3. 主機上有沒有 iptables 持久化機制

### 逐一查核結果

| 檢查 | 結果 |
|---|---|
| `dpkg -l` → iptables-persistent／netfilter-persistent | **無**（`NONE`） |
| `systemctl list-unit-files` → netfilter／iptables | **無**（`NONE`） |
| `/etc/iptables/` | **不存在** |
| `/etc/network/if-pre-up.d/`、`if-up.d/` | 只有 `ethtool`（無任何 iptables 還原腳本） |
| `/etc/rc.local` | **不存在** |
| 任何 unit／腳本引用 `iptables-restore` | **無**（`/etc/systemd/system`、`/lib/systemd/system`、`/etc/network` 全掃） |
| `/etc/docker/daemon.json` | **不存在**（Docker 用預設 → `firewall_backend={iptables []}`） |
| root crontab | 僅 `0 7 * * * /opt/goaa/scripts/check_do_git_consistency.sh --dry-run`（與防火牆無關） |
| `/etc/cron.d` | `e2scrub_all`、`sysstat`（無防火牆相關） |

### 但主機**有**一個既有的持久化機制：**ufw**

```
/etc/ufw/ufw.conf:ENABLED=yes
systemctl is-enabled ufw → enabled
systemctl is-active  ufw → active
/etc/default/ufw: DEFAULT_INPUT_POLICY="DROP" ; DEFAULT_FORWARD_POLICY="DROP"

/etc/ufw/ 內含：before.rules、before6.rules、after.rules、after6.rules、
               user.rules、user6.rules（＋after.init/before.init）
```

- ufw 由 **`ufw.service` 開機還原上述 rules 檔**（`ufw-init`，`Before=network-pre.target`）。
- **`/etc/ufw/` 內完全沒有 `DOCKER-USER` 相關內容**（`grep -rn DOCKER-USER /etc/ufw/` → 無）。
- ufw 的 8080 放行規則位於 `user.rules:29-30` 與 `user6.rules:29-30`（comment = `GOAA Model Router API`）：
  ```
  -A ufw-user-input -p tcp --dport 8080 -j ACCEPT
  -A ufw6-user-input -p tcp --dport 8080 -j ACCEPT
  ```

### 結論（供 D0.2 決策）

> **主機沒有任何通用的 iptables 持久化套件／腳本；唯一「開機會自動還原」的機制是 ufw 自己。**
> 因此若要在 **DOCKER-USER** 放規則並撐過重開機，**既有機制下最正統的落點是 `/etc/ufw/after.rules`**（ufw 業界標準的 Docker 整合做法：在 after.rules 末端建立／維護 `DOCKER-USER` 規則），再 `ufw reload` 套用。
> **依令「沒有的話回報，先不要自己裝新套件」——我不會安裝 iptables-persistent，也不會自行新增 systemd unit；上面的落點屬「既有機制」，但仍會動防火牆，故先回報等您確認。**

---

## 4. 有沒有任何客戶端在用公網 8080

### 指令與結果

| 檢查 | 結果 |
|---|---|
| `systemctl cat goaa-worker-agent.service` | `Environment="ROUTER_API=http://127.0.0.`＋`1:8080"` ← **主機部分是 `127.0.0.`＋`1`（loopback）**；`Environment="WORKER_ID=do-cloud-1"`、`Environment="POLL_SEC=5"`；`ExecStart=/opt/goaa/venv/bin/python3 /opt/goaa/workers/agent.py`；`Restart=on-failure` |
| `ss -ltnp \| grep :8080` | `LISTEN 0.0.0.`＋`0:8080 users:(("uvicorn",pid=2994296))` ← 只有 goaa-router 一個 listener |
| `ss -tnp state established` 過濾 8080 | **沒有任何 established 連線** |
| `ss -tanp \| grep :8080` | 除 listener 外，**全部都是 `127.0.0.`＋`1:<port> → 127.0.0.`＋`1:8080` 的 TIME-WAIT**（本機 worker-agent 輪詢留下的） |
| `grep -n 8080 /etc/cloudflared/config.yml` | **20 條 ingress 全部指向 `http://127.0.0.`＋`1:8080`**（`api.goaa.ai` 走 tunnel → 本機環回） |
| `grep ':8080'`（`/opt/goaa`、`/etc/goaa`、`/etc/cloudflared`、`/etc/systemd` 檔案名清單） | 只有：cloudflared 設定（含 2 個 `.bak`、1 個 `.next`）、worker-agent unit、以及**文件／舊腳本／舊 dashboard**（`docs/**`、`PHASE2-*.ps1`、`AIKA2-HEARTBEAT-ONELINER.md`、`components/GoaaDashboard.jsx` 等）。**沒有任何 active 客戶端設定指向非 loopback 的 8080。** |

### 結論

> **沒有任何客戶端依賴「公網（非 loopback）的 8080」。**
> - worker-agent（唯一的服務間呼叫者）用 `127.0.0.`＋`1`
> - 對外流量全走 cloudflared tunnel → `127.0.0.`＋`1:8080`
> - 現時與歷史連線紀錄都只有 loopback
>
> ⇒ **D0.3 的前置條件（先確認沒有客戶端依賴公網 8080）在現有證據下成立**；但這一條請 Tao 覆核後我才動 ufw。

---

## 5. 🔴 額外發現：5432 的公網暴露**正在被持續爆破**（本輪最嚴重發現）

D0.1 只要求查 4 項，但第 2 項的計數器異常（10,578），促使我進一步用**唯讀的容器日誌**（`docker logs`，非資料庫內容）交叉查證：

### 證據

```
$ docker logs goaa-postgres 2>&1 | grep -c "FATAL"
484026

$ docker logs goaa-postgres 2>&1 | grep "FATAL" | tail -5
2026-09-11 23:35:58.333 UTC [1499642] FATAL:  password authentication failed for user "administrator"
2026-09-11 23:42:51.521 UTC [1499716] FATAL:  password authentication failed for user "administrator"
2026-09-11 23:49:45.345 UTC [1499790] FATAL:  password authentication failed for user "administrator"
2026-09-11 23:56:38.562 UTC [1499864] FATAL:  password authentication failed for user "administrator"
2026-09-12 00:03:34.309 UTC [1499937] FATAL:  password authentication failed for user "administrator"
```

- **累計 484,026 次密碼認證失敗**，最早始於容器建立當天（`2026-05-11 23:22:16 UTC`）。
- **最後一次是 `2026-09-12 00:03:34 UTC`——就在取證當下**（約每 7 分鐘一次的節奏，用 `administrator` 帳號）。
- 近 7 天每日量：`461 / 304 / 342 / 367 / 381 / 370 / 291`（持續、穩定、非一次性事件）。

**被嘗試的帳號（前 12 名）**

| 次數 | 帳號 |
|---|---|
| 241,755 | `postgres` |
| **111,523** | **`goaa`** ← 真實業務角色名 |
| 24,139 | `zabbix_web` |
| 11,414 | `user1` |
| 7,147 | `backup` |
| 2,198 | `root` |
| 2,148 | `admin` |
| 1,970 | `test` |
| 1,928 | `user` |
| 1,809 | `guest` |
| 1,797 | `administrator` |
| 1,657 | `demo` |

→ 這是**典型的公網掃描器／憑據填充**，不是內部程式行為（內部只用 `goaa` 且密碼正確）。

### 為什麼它能被連到（容器內部設定）

```
$ docker exec goaa-postgres cat /var/lib/postgresql/data/pg_hba.conf | grep -vE '^#|^$'
local   all  all                      trust
host    all  all  127.0.0.`＋`1/32    trust
host    all  all  ::1/128             trust
local   replication all               trust
host    replication all  127.0.0.`＋`1/32  trust
host    replication all  ::1/128      trust
host    all  all  all                 scram-sha-256      ← 允許任意來源嘗試密碼認證

$ docker exec goaa-postgres cat .../postgresql.conf | grep '^listen_addresses'
listen_addresses = '*'
```

- **`host all all all scram-sha-256`**：**任何來源 IP** 都可以對**任何角色**嘗試密碼認證 → 爆破面完全敞開。
- 目前尚未被攻破（沒有成功登入的痕跡、`goaa` 的密碼未被猜到），但**這是靠密碼強度在擋，不是靠網路邊界**。
- **日誌缺口**：`log_line_prefix` 未設 `%h`（預設 `%m [%p] `）⇒ **日誌裡沒有來源 IP**，無法列舉攻擊者位址（也不需為此改設定；只是說明為何本報告沒有來源 IP 清單）。`conntrack` 未安裝，故也無法從連線追蹤取源。

### 對計畫的意涵

1. **D0.2 不是「清理面子的收尾」，是止血**。建議列為**最高優先**。
2. 攻擊者已在嘗試**真實角色名 `goaa`**（111,523 次）→ 角色名不是秘密，防線全在密碼與網路邊界。
3. 修好邊界後，**密碼輪換**可另行評估（本輪不做，且我從未讀取任何密碼）。

---

## 6. 對 D0.2／D0.3／D0.4 的建議（**尚未執行，等 Tao 確認**）

### D0.2（收掉 5432 公網可達）— 建議做法

**方案 A（推薦，符合「優先用 `DOCKER-USER` 限制來源、不重建容器」）**
- 在 `DOCKER-USER` 鏈插入：**允許**來自 `docker0`（及既有 Docker 網段）的 5432，**DROP** 其餘來源的 5432 新連線（並放行 `RELATED,ESTABLISHED`）。
- **持久化落點**：寫進 **`/etc/ufw/after.rules`**（既有機制，見 §3；ufw 開機還原），再 `ufw reload`。
- **預期效果**：外部 SYN→5432 在 FORWARD 被 DROP；**本機 `127.0.0.`＋`1:5432` 走 docker-proxy / OUTPUT 不受影響** → 正好滿足令要求的驗收（本機可連、外部被拒）。
- **風險／注意**：`ufw reload` 會重建 ufw 自有的鏈（Docker 鏈不受 ufw 管理）；需驗證**重複套用不會累積重複規則**（我會用 `iptables -C` 做幂等，而不是盲目 `-A`）。
- **回滾**：刪掉 `after.rules` 中的該段 + `ufw reload`（或直接 `iptables -D` + 還原備份檔）。

**方案 B（更徹底但需重建容器，與「不重建」衝突，故僅列為替代）**
- 把埠綁定改成 `127.0.0.`＋`1:5432:5432`（重建容器）。一勞永逸、不依賴 iptables 規則，但**需停／建容器**，且要處理 `goaa-heartbeat`／`goaa-openclaw` 等其他容器對它的存取。**不建議在本輪做。**

**必做驗收（依令）**：① 宿主 `127.0.0.`＋`1:5432` 能 `SELECT 1`；② `goaa-router` API 健康檢查正常；③ **外部連 5432 被拒 → 請 Tao 從您的機器或 DO 主控台測**（**我不會對外發起掃描**）。

### D0.3（收掉 8080 的公網放行）— 建議做法

- **前置**：§4 顯示無客戶端依賴公網 8080（請您覆核）。
- **做法**：`ufw delete allow 8080/tcp`（此指令同時處理 v4 與 v6；等效於移除 `user.rules:29-30`／`user6.rules:29-30` 那兩條）。
- **驗收**：`api.goaa.ai` 照常（走 tunnel → `127.0.0.`＋`1:8080`）；**外部直連 8080 被拒**（同樣請您從外部測）。
- **回滾**：`ufw allow 8080/tcp`（comment 會是新的）。

### D0.4（停用 `goaa-model-router`）— **依令先回報一個狀況**

令：「`systemctl disable`（不要 stop，本來就沒在跑；**若在跑則先回報**）」

**現況查核 → 它在跑，而且是 restart 迴圈：**

```
systemctl is-enabled goaa-model-router → enabled
systemctl is-active  goaa-model-router → activating      ← 不是 inactive
Restart=always / RestartSec=5
ExecStart=… uvicorn api:app --host 0.0.0.`＋`0 --port 8080  ← 與 goaa-router 搶同一個 8080
goaa-router 的 drop-in：ExecStartPre=-/bin/sh -c 'fuser -k 8080/tcp 2>/dev/null; sleep 2; exit 0'
```

→ 兩者**互相拉扯**：`goaa-router` 啟動前會 `fuser -k 8080/tcp` 殺掉佔用者，而 `goaa-model-router` 每 5 秒重試一次。**故「本來就沒在跑」的前提不成立。**
**我在這裡回報，尚未 `disable`。** `disable` 本身不會停掉這個迴圈（要能真正止血需同時 `stop`，但令說不要 stop）——**請您指示**：(a) 只 `disable`（迴圈可能仍在，直到下次 `daemon-reload`／重開機）；(b) `disable` + `stop`；(c) 其他。

---

## 7. 本輪未做的事（D0.1 邊界）

未改任何檔案（含 `/etc/ufw/*`、`/etc/systemd/*`、容器設定）、**未新增／刪除任何 iptables 或 ufw 規則**、未重啟或停用任何服務、未重建任何容器、未建目錄、未動 env／DNS／tunnel、未安裝任何套件；**未讀取任何密碼／secret 值**；**未對外發起任何連通性測試或掃描**；未碰資料庫內容（僅讀取容器的 **stdout 日誌** 與 **`pg_hba.conf`／`postgresql.conf` 檔案**，皆非資料列）。
