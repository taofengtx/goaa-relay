# 17 — 服務入口／Tunnel／反向代理（唯讀）

## 1. DNS 與外層

- 四個名稱（`goaa.ai`、`www.goaa.ai`、`planning.goaa.ai`、`api.goaa.ai`）皆指向 **Cloudflare**（`104.21.54.⟨131⟩`、`172.67.138.⟨183⟩`）。
- `https://goaa.ai/` → 308 → `https://www.goaa.ai/`（Framer 託管首頁）。

## 2. C1：Cloudflare Tunnel ingress（`/etc/cloudflared/config.yml`，只列 route）

| hostname | path | 指向 |
|---|---|---|
| `api.goaa.ai` | `/workers/status`、`/workers/metrics`、`/worker/heartbeat`、`/tasks/dispatch`、`/tasks/status/*`、`/tasks/queue`、`/tasks/cancel/*`、`/tasks/next/*`、`/task/complete`、`/tasks/pool`、`/tasks/pool/add`、`/tasks/pool/add-batch`、`/tasks/pool/stats`、`/tasks/history`、`/cost/status`、`/profit/status`、`/revenue/status`、`/models/status`、`/route`、`/chat` | `http://127.0.0.1:8080`（**goaa-router / 控制面**） |
| `api.goaa.ai` | **（其餘全部）** | `http://127.0.0.1:18789`（**openclaw / golden order API**） |
| `planning.goaa.ai` | `/planning` 及（其餘） | `http://127.0.0.1:3100`（**live 前端**） |
| — | 預設 | `http_status:404` |

- 因此 `https://api.goaa.ai/api/v1/order/*`（前端實際呼叫 9 次）→ **18789 openclaw**，與 16 號報告一致。
- Tunnel UUID 已遮罩；憑證檔未讀取。

## 3. C2：nginx 反向代理

- `/etc/nginx/sites-enabled/goaa-c2-candidate`：`listen 80`（→ 301）、`listen 443 ssl`（`server_name _`）。
- 上游：`http://127.0.0.1:3100`（候選前端）＋ `$api_upstream`（`proxy_ssl_server_name on`）。
- 實測 `https://127.0.0.1/` → **401**（Clerk/中介層守門）；`http://127.0.0.1/` → 301。

## 4. Tailscale 與 SSH tunnel

| 來源 | 形式 | 目的 | 證據 |
|---|---|---|---|
| D0 | `socat TCP-LISTEN:5188,bind=100.114.37.90 → 127.0.0.1:5188` | Aika-Box 主控台 | unit `goaa-local-console-tailscale-proxy` |
| D0 | `socat TCP-LISTEN:8188,bind=100.114.37.90 → 127.0.0.1:8188` | ComfyUI | unit `goaa-comfyui-tailscale-proxy` |
| D0 | `ssh -f -N -L 13102:127.0.0.1:13102 do-c2`（pid 1772631，Sep 10 起） | 看 C2 候選 Clerk UI | `ss -tnp` |
| D0→C1 | worker agent 走 **公網** `134.199.227.⟨108⟩:8080` | 控制面 | unit env（無 tunnel） |

## 5. 埠位矩陣（本輪實測）

| 埠 | D0 | C1 | C2 | C3 |
|---|---|---|---|---|
| 22 | ✅（`0.0.0.0`） | ✅ | ✅ | ✅ |
| 80/443 | — | Cloudflare（無本機 nginx） | ✅ **nginx** | — |
| 3100 | — | ✅ live 前端 | ✅ candidate | — |
| 3102/3103 | ✅（dev worktree） | ✅ 3103 live API | ✅ 3103 clerk API | — |
| 5188 | ✅ Aika-Box console（+tailnet proxy） | — | — | — |
| 8080 | — | ✅ router（ufw 放行） | — | — |
| 13102 | ✅（ssh tunnel → C2） | — | ✅ clerk UI | — |
| 18789 | — | ✅ openclaw | — | — |
| 18790 | ✅ framer-bridge | — | — | — |
| 5432 | — | ✅（docker-proxy；ufw 未放行） | — | — |
| 5433 | — | — | ✅ 原生 PG | — |
| 3389/3390 | ✅ RDP（`*`） | — | — | — |
| 11434 | ✅ ollama | — | — | — |
| 7001/7002/12001/12002/25002 | ✅ NoMachine | — | — | — |

## 6. C1 ufw（現況，未改）

```
allow: OpenSSH, 80/tcp, 443/tcp, 8080/tcp   （v4+v6）
allow out: 587/tcp (Zoho SMTP)
（5432 不在放行清單）
```

- `8080/tcp` 之所以仍放行：**D0/C2/C3 的 worker 走公網連入**（D0.3 收掉 8080 的前提被推翻 → Tao 撤銷 → 已建 `CANCELLED.md`）。
- 前輪 D0.3B 的「遠端 worker 改走 tunnel」為階段一（唯讀）已完成；**階段二（實際改址＋重啟）尚未執行**（重啟會觸發 🛡 審批）。

## 7. 風險

1. `api.goaa.ai` 的 **catch-all 直接指向 openclaw**（含 gold order API）⇒ Cloudflare 是唯一外層守門；若 tunnel 規則被改寬，golden commerce 端點即暴露。
2. C2 的 443 對公網開放（自簽/憑證未核）；staging 有真實 Clerk dev 設定。
3. `planning.goaa.ai` 的 catch-all → 3100（live 前端）⇒ 任何未列路徑都進生產前端。
