# D0.3B 階段一 — 遠端 worker 改走 tunnel（唯讀勘查 ＋ 安全探測）

- **主機**：`do-runtime-anchor`（C1，`goaa-aika-cloud-1`）＋ 本機 `aika-core-01` ＋ 唯讀盤點 `do-c2` / `do-c3`
- **執行窗口**：2026-09-12T01:35:40Z → 01:42Z
- **性質**：**唯讀**。未改任何設定、未重啟任何服務、未動 ufw／`DOCKER-USER`、未改 cloudflared、未碰 worker。
- **轉寫聲明**：IPv4 末段一律以 `⟨N⟩` 切分；sha256 只取前 16 位。
- **結論摘要**：**B 案可行** —— tunnel 已具備 worker 需要的三個端點；tunnel 路徑 200、不快取、worker 的真實 UA 也不被挑戰。**唯一障礙是「aika-1 我進不去」**，其餘三台可改。

---

## 0. 一頁看懂

| 項目 | 結果 |
|---|---|
| cloudflared ingress | 23 條真實規則（`api.goaa.ai` 20 條 → `127.0.0.⟨1⟩:8080`；`planning.goaa.ai` 2 條 → `3100`；`api.goaa.ai` 1 條 catch-all → `18789`）＋ 1 條 `http_status:404` |
| worker 需要的端點是否都在 ingress？ | **是** —— `/worker/heartbeat`(line 11)、`/tasks/next/*`(line 26)、`/task/complete`(line 29) **全部都在** ⇒ **不需改 cloudflared** |
| 探針（選定 `/workers/status`） | `via_tunnel` **200**（0.153 s）／`via_local` **200**（0.003 s） |
| CDN 快取 | `cf-cache-status: DYNAMIC`（不快取）、`server: cloudflare` vs `server: uvicorn` |
| 兩側是否同一後端 | body 同為 **2,311 B**、top-level keys 同為 `['ts','workers']` |
| worker 真實 UA（`python-requests/2.31.0`） | tunnel **200**、**無 `cf-mitigated`／無挑戰頁** |
| POST 端點可達性 | `HEAD /worker/heartbeat` → **405**（由路由器回的「方法不允許」⇒ 請求確實到達後端） |
| Aika 可改的機器 | `do-c2` ✅、`do-c3` ✅、`aika-core-01`（本機）✅ |
| Aika 進不去的機器 | **`aika-1` ❌**（Tailscale 網路可達 `100.109.7.⟨85⟩`，但 publickey 被拒）→ 由 Tao 改 |

## 1. 步驟 1 — tunnel ingress 全貌

`grep -n -E '^[[:space:]]*-?[[:space:]]*(hostname|path|service):' /etc/cloudflared/config.yml`（節錄；共 72 行、`grep -c 'service:'` = 24）：

| line | hostname | path | service |
|---|---|---|---|
| 4–6 | api.goaa.ai | `/workers/status` | `http://127.0.0.⟨1⟩:8080` |
| 7–9 | api.goaa.ai | `/workers/metrics` | 同上 |
| **10–12** | api.goaa.ai | **`/worker/heartbeat`** | 同上 |
| 13–15 | api.goaa.ai | `/tasks/dispatch` | 同上 |
| 16–18 | api.goaa.ai | `/tasks/status/*` | 同上 |
| 19–21 | api.goaa.ai | `/tasks/queue` | 同上 |
| 22–24 | api.goaa.ai | `/tasks/cancel/*` | 同上 |
| **25–27** | api.goaa.ai | **`/tasks/next/*`** | 同上 |
| **28–30** | api.goaa.ai | **`/task/complete`** | 同上 |
| 31–33 | api.goaa.ai | `/tasks/pool` | 同上 |
| 34–36 | api.goaa.ai | `/tasks/pool/add` | 同上 |
| 37–39 | api.goaa.ai | `/tasks/pool/add-batch` | 同上 |
| 40–42 | api.goaa.ai | `/tasks/pool/stats` | 同上 |
| 43–45 | api.goaa.ai | `/tasks/history` | 同上 |
| 46–48 | api.goaa.ai | `/cost/status` | 同上 |
| 49–51 | api.goaa.ai | `/profit/status` | 同上 |
| 52–54 | api.goaa.ai | `/revenue/status` | 同上 |
| 55–57 | api.goaa.ai | `/models/status` | 同上 |
| 58–60 | api.goaa.ai | `/route` | 同上 |
| 61–63 | api.goaa.ai | `/chat` | 同上 |
| 64–66 | planning.goaa.ai | `/planning` | `http://127.0.0.⟨1⟩:3100` |
| 67–69 | planning.goaa.ai | （無 path，catch-all） | `http://127.0.0.⟨1⟩:3100` |
| 70–71 | api.goaa.ai | （無 path，catch-all） | `http://127.0.0.⟨1⟩:18789` |
| 72 | — | — | `http_status:404` |

**worker 實際使用的三個端點都在 ingress 內** ⇒ **B 案不需改 cloudflared**。

## 2. 步驟 2 — 探針端點的挑選

`GET /openapi.json` 共 28 條路徑（GET 16／POST 12）。**無副作用的 GET 候選**：

```
GET /health            GET /workers/status      GET /workers/metrics
GET /models/status     GET /cost/status         GET /profit/status
GET /revenue/status    GET /tasks/pool          GET /tasks/pool/stats
GET /tasks/queue       GET /tasks/history       GET /tasks/status/{task_id}
（禁區：GET /tasks/next/{worker_id} —— 會消耗真實任務，全程未呼叫）
```

**選定 `/workers/status`**，理由：
1. **在 ingress 內**（line 5 → `127.0.0.⟨1⟩:8080`）；
2. 純讀取（列出 worker 狀態），無任何副作用；
3. **`/health` 不可用** —— 它**不在** ingress 內，`https://api.goaa.ai/health` 會落到 api.goaa.ai 的 catch-all → `127.0.0.⟨1⟩:18789`（openclaw），**探到的會是別的服務**，結論會假陽性。

## 3. 步驟 3 — tunnel 連通性探測

```
$ curl -sS -m 15 -o /dev/null -w "via_tunnel http=%{http_code} time=%{time_total}s\n" https://api.goaa.ai/workers/status
via_tunnel http=200 time=0.152978s

$ curl -sS -m 15 -o /dev/null -w "via_local  http=%{http_code} time=%{time_total}s\n" http://127.0.0.⟨1⟩:8080/workers/status
via_local  http=200 time=0.002733s
```

回應標頭（快取檢查）：

```
$ curl -sS -m 15 -D - -o /dev/null https://api.goaa.ai/workers/status | grep -i -E "^(server|cf-cache-status|cache-control):"
server: cloudflare
cf-cache-status: DYNAMIC          ← 未被 CDN 快取

$ curl -sS -m 15 -D - -o /dev/null http://127.0.0.⟨1⟩:8080/workers/status | grep -i -E "^(server|cf-cache-status|cache-control):"
server: uvicorn
```

同一後端驗證（內容形狀，不列值）：

```
tunnel_bytes=2311  local_bytes=2311
tunnel json_ok top_level= ['ts', 'workers']
local  json_ok top_level= ['ts', 'workers']
```

**追加風險探測（worker 的真實 User-Agent）** —— worker 用 Python `requests`，UA 為 `python-requests/2.x`，與 curl 不同，需確認不被 bot 保護挑戰：

```
$ curl -sS -m 15 -o /dev/null -w "py_ua http=%{http_code} time=%{time_total}s\n" -A "python-requests/2.31.0" https://api.goaa.ai/workers/status
py_ua http=200 time=0.094917s

$ curl ... -A "python-requests/2.31.0" -D - ... | grep -iE "cf-mitigated|server|cf-cache-status"
HTTP/2 200
server: cloudflare
cf-cache-status: DYNAMIC          ← 無 cf-mitigated、無挑戰頁

$ （對照）py_ua_local http=200
```

**POST 端點可達性**（不發 POST，用 HEAD 探路；405 = 路由器回的「方法不允許」，證明請求確實到達後端）：

```
$ curl -sS -m 15 -o /dev/null -w "head_heartbeat http=%{http_code}\n" -I https://api.goaa.ai/worker/heartbeat
head_heartbeat http=405
```

⇒ **全部通過，未出現 403／503／1010／挑戰頁**，B 案無需先解 CDN 問題。

## 4. 步驟 4 — 4 台遠端 worker 盤點（唯讀）

| worker | 對端（基線 10 min） | unit | 設定檔 | 環境變數名 | 目前 host | Aika 可達 |
|---|---|---|---|---|---|---|
| do-cloud-2 | `143.198.224.⟨71⟩` | `goaa-worker-agent.service` | `/etc/systemd/system/goaa-worker-agent.service` | **`ROUTER_API`**, `POLL_SEC` | `134.199.227.⟨108⟩:8080` | ✅ `do-c2`（root） |
| do-cloud-3 | `64.23.166.⟨121⟩` | `goaa-worker-agent.service` | 同上 | **`ROUTER_API`**, `POLL_SEC` | `134.199.227.⟨108⟩:8080` | ✅ `do-c3`（root） |
| aika-core-01 | `165.162.8.⟨177⟩` | `goaa-worker-agent.service` | `/etc/systemd/system/goaa-worker-agent.service` | **`ROUTER_URL`（⚠️見下）**, `TAILSCALE_IP` | `134.199.227.⟨108⟩:8080` | ✅ 本機 |
| aika-1 | `98.191.202.⟨15⟩` | 未知 | 未知 | 未知 | 未知 | ❌ **不可達** |
| （do-cloud-1） | `127.0.0.⟨1⟩` | `goaa-worker-agent.service`（C1） | `/etc/systemd/system/goaa-worker-agent.service` | `ROUTER_API` | `127.0.0.⟨1⟩:8080` | 本來就走 loopback，**不需遷移** |

**各機 unit 細節**

- **do-cloud-2 / do-cloud-3**（`HostName` 分別為 `143.198.224.⟨71⟩`／`64.23.166.⟨121⟩`）：
  ```
  User=root            WorkingDirectory=/opt/goaa/workers
  ExecStart=/opt/goaa/venv/bin/python3 /opt/goaa/workers/agent.py
  Environment=<redacted> × 3   （即 WORKER_ID / ROUTER_API / POLL_SEC，inline 於 unit 檔）
  is-active=active
  ```
- **aika-core-01（本機）**：
  ```
  User=aika            WorkingDirectory=/opt/goaa
  Environment="WORKER_ID=aika-core-01"
  Environment="ROUTER_URL=http://134.199.227.⟨108⟩:8080"
  Environment="TAILSCALE_IP=100.114.37.⟨90⟩"
  ExecStart=/opt/goaa/venv/bin/python /opt/goaa/workers/agent.py   （pid 6356，active）
  ```

### ⚠️ 遷移必踩的坑（aika-core-01 專屬）

worker 程式 `/opt/goaa/workers/agent.py` 第 9 行（本機版，sha256 前16 `8b1ce13e532fd8e4`、5,918 B、May 13）：

```python
ROUTER_URL = os.getenv("ROUTER_API", "http://134.199.227.⟨108⟩:8080")   # 原文末段為 108，此處依轉寫規則切分
```

**程式讀的是 `ROUTER_API`，但本機 unit 設的是 `ROUTER_URL`** ⇒ 本機那個 Environment 行**從來沒被讀到**，實際走的是**程式碼硬寫的公網 IP 預設值**。因此 aika-core-01 遷移時**必須新增/設定 `ROUTER_API=https://api.goaa.ai`**（只改 `ROUTER_URL` 無效）。

worker 使用的端點（第 23/32/101 行）：`POST /worker/heartbeat`、`GET /tasks/next/<WORKER_ID>`、`POST /task/complete` —— **三者皆在 ingress 內**（見 §1）。

### aika-1 可達性判定

- tailnet 名稱解析：`aika-1.tailffe219.ts.net` → `100.109.7.⟨85⟩`（本機 tailnet IP 為 `100.114.37.⟨90⟩`）
- 連線測試（單次、`BatchMode`）：SSH 服務有回應（host key 已接受）但 **`Permission denied (publickey,password,keyboard-interactive)`**；以 `aika`、`root` 及金鑰 `goaa_do_core_ed25519` 皆被拒。
- ⇒ **網路可達、憑據不可達 ⇒ 判定「不可達」**，由 Tao 自行修改（我另附指令）。

## 5. 步驟 5 — 基線（2026-09-12 01:26:31Z ~ 01:36:31Z，10 分鐘窗）

```
$ journalctl -u goaa-router --since "10 min ago" --no-pager | grep "tasks/next" | awk '{print $7}' | sed "s/:[0-9]*$//" | sort | uniq -c | sort -rn
    116 64.23.166.⟨121⟩      （do-cloud-3）
    116 143.198.224.⟨71⟩     （do-cloud-2）
    116 127.0.0.⟨1⟩          （do-cloud-1，本機 loopback）
    115 165.162.8.⟨177⟩      （aika-core-01）
    108 98.191.202.⟨15⟩      （aika-1）

$ （同窗 POST /worker/heartbeat）
     20 64.23.166.⟨121⟩    19 165.162.8.⟨177⟩    19 143.198.224.⟨71⟩
     19 127.0.0.⟨1⟩        18 98.191.202.⟨15⟩
```

⇒ 遷移後比對基準：**這 4 個公網來源的 `/tasks/next` 與 `/worker/heartbeat` 次數應歸零**，同時 `https://api.goaa.ai` 的對應流量應上升（改由 cloudflared 以 loopback 進站，於日誌中顯示為 `127.0.0.⟨1⟩`）。

## 6. 階段二前的注意事項（尚待處理，未動）

1. **aika-1 我進不去** ⇒ 需 Tao 自行改（Tao 決定指令內容；要點：unit 內把 `ROUTER_API` 指向 `https://api.goaa.ai`，`daemon-reload` + `restart`）。
2. **aika-core-01 的變數名陷阱**（§4 末）：改 `ROUTER_URL` 無效，必須設 `ROUTER_API`。
3. **不要把 `/health` 當探針**（不在 ingress，會落到 openclaw）。
4. **每個 worker 的 unit 都是 inline `Environment=`**（無 `EnvironmentFile`）⇒ 需編輯 unit 檔 + `daemon-reload` + `restart`；C2/C3 的 worker 以 **root** 執行。
5. 本次**未測 POST**（`/worker/heartbeat` 真呼、`/task/complete` 真呼都具副作用）—— 端點存在性以 `HEAD` 的 405 佐證；**真正的遷移驗證放階段二（單台試遷移）**。
6. Cloudflare 端風險已先行排除：`cf-cache-status: DYNAMIC`（不快取）、Python UA 無挑戰、無 `cf-mitigated`。

## 7. 本階段「未做」清單（紀律自證）

未呼叫 `/tasks/next/*`（禁區）、未發任何 POST、未改任何檔案、未重啟任何服務、未動 ufw／`DOCKER-USER`／cloudflared、未動 D0.3 規則、未碰 D0.4、未安裝任何套件；對外僅對 **自家 `api.goaa.ai`** 發出 5 次探測（3 次 GET、1 次 HEAD、1 次確認 GET）＋ 對 `aika-1` 的 4 次 SSH 連線嘗試（皆被拒）；env 只列變數名與 host 部分。
