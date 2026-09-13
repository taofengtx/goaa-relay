# 14 — Worker 拓扑與唯一身分（唯讀）

- 令文：**Worker 云节点統一為 W1/W2/W3…，不得再與 C1/C2 混用**。
- 本輪處置：**只建立映射，不改名、不動服務**（唯讀）。

## 1. 控制面事實

- 控制面 = `https://api.goaa.ai` → C1 `127.0.0.1:8080`（`goaa-router`），端點：`/workers/register|status|metrics`、`/worker/heartbeat`、`/tasks/dispatch|next/{id}|queue|status/*|cancel/*|history|pool*`、`/task/complete`、`/cost|profit|revenue|models/status`、`/route`、`/chat`。
- 本輪唯讀查詢：`GET http://127.0.0.1:8080/workers/status`（C1 本機）。

## 2. 註冊表（6 個 worker，全部 `online`）

| worker_id | role | 承載主機 | 承載主機對外 | 心跳（UTC） |
|---|---|---|---|---|
| `aika-1` | `primary_coordinator` | aika-1（Windows 11） | LAN `192.168.1.207` | `2026-09-13T07:35:16Z` |
| `aika-2` | `secondary_coordinator` | aika-2（Xubuntu 24.04, docker+ollama） | LAN `192.168.1.208` | `2026-09-12T06:29:16Z` |
| `do-cloud-1` | `cloud_worker` | **C1** `goaa-aika-cloud-1` | `134.199.227.⟨108⟩` | `2026-09-13T08:14:17Z` |
| `do-cloud-2` | `cloud_worker` | **C2** `goaa-aika-cloud-2-01` | `143.198.224.⟨71⟩` | `2026-09-13T08:14:18Z` |
| `do-cloud-3` | `cloud_worker` | **C3** `goaa-aika-cloud-3` | `64.23.166.⟨121⟩` | `2026-09-13T08:14:29Z` |
| `aika-core-01` | `aika-box-pro-alpha` | **D0** `aika-core-01` | tailnet `100.114.37.90` | `2026-09-13T08:14:39Z` |

- 全部 `tasks_today = 0`、`active_tasks = 0`、`revenue/cost/profit_today = 0` ⇒ **拓撲活著，但沒有流量**。
- 映射結論：**D0/C1/C2/C3 四台「機器」＝ 4 個 worker 身分；另有 2 個家用協調者（aika-1/aika-2）**。故建議命名：`W1=aika-1`、`W2=aika-2`、`W3=do-cloud-1`、`W4=do-cloud-2`、`W5=do-cloud-3`、`W6=aika-core-01`（**由 Tao 裁定後才改名**）。

## 3. 各 worker 的 unit 實況

| 承載主機 | unit | WORKER_ID | ROUTER 變數 | POLL |
|---|---|---|---|---|
| C1 | `goaa-worker-agent.service` | `do-cloud-1` | `ROUTER_API=http://127.0.0.1:8080` | 5s |
| C2 | `goaa-worker-agent.service` | `do-cloud-2` | `ROUTER_API=http://134.199.227.⟨108⟩:8080` | 5s |
| C3 | `goaa-worker-agent.service` | `do-cloud-3` | `ROUTER_API=http://134.199.227.⟨108⟩:8080` | 5s |
| D0 | `goaa-worker-agent.service` | `aika-core-01` | `ROUTER_URL=http://134.199.227.⟨108⟩:8080`（**名無效**，靠程式預設值生效） | （預設 5s） |
| aika-1 | （Windows 端，未由本輪直接登入） | `aika-1` | — | — |
| aika-2 | （未由本輪直接登入） | `aika-2` | — | — |

## 4. 🔴 更正

- 前輪曾以「D0 unit 設 `ROUTER_URL`、程式讀 `ROUTER_API`」推論 **D0 worker 不註冊**；本輪 `/workers/status` 顯示 `aika-core-01` **在線且心跳新鮮** ⇒ **推論錯誤，已更正**（見 11 號報告 §5）。
- 真正風險不是「不註冊」，而是：**(a)** env 名不一致易在換址時靜默失效；**(b)** D0/C2/C3 走 **C1 公網 IP**，故 `8080/tcp` 必須維持開放（D0.3 被撤銷的前提）。

## 5. C3（純 worker 節點）

- hostname `goaa-aika-cloud-3`；`64.23.166.⟨121⟩`（`eth0/20`）、`10.48.0.7/16`、`10.124.0.4/20`。
- unit：**僅** `goaa-worker-agent.service`（enabled+active, MainPID 1941060，自 Sep 11 06:26 UTC 起）。
- **無任何監聽埠（3100/8080/5432… 全無）**、無 docker、無 cloudflared、`/opt` 只有 `digitalocean/`、`goaa/`。
- `grep -ril stripe /opt` → **0**。
- 結論：**C3 = 最乾淨的雲 worker 節點**（僅出站連 C1:8080）。
