# 15 — 唯一身分映射（D0／C1／C2／Worker）（唯讀）

- 目的：**停止依賴舊記憶、IP 猜測與機器暱稱**；以下每一列都有本輪實測證據。

## 1. 統一命名（本輪起）

| 代號 | 角色 | 唯一身分 |
|---|---|---|
| **D0** | **Local Development（Aika-Box）** | `aika-core-01` |
| **C1** | **Live / Production** | `goaa-aika-cloud-1` |
| **C2** | **Test / Staging** | `goaa-aika-cloud-2-01` |
| **W1…W6** | **Worker 云节点／協調者** | 見 §3（由 `worker_id` 定義） |

## 2. 三台主機（本輪實測）

| | D0 | C1 | C2 |
|---|---|---|---|
| hostname | `aika-core-01` | `goaa-aika-cloud-1` | `goaa-aika-cloud-2-01` |
| 角色 | 本地開發 / Aika-Box Pro | 生產 | 測試/預備 |
| OS | Ubuntu 26.04 LTS | （前輪已錄；本輪未重測） | （同上） |
| Public IP | `165.162.8.⟨177⟩`（家用 NAT） | `134.199.227.⟨108⟩` | `143.198.224.⟨71⟩` |
| Tailscale | `100.114.37.90` | — | — |
| LAN/內網 | `192.168.1.24/24` | `10.48.0.5/16`、`10.124.0.2/20` | `10.48.0.6/16`、`10.124.0.3/20` |
| ssh 別名 | （本機） | `do-runtime-anchor` → `134.199.227.⟨108⟩` | `do-c2` → `143.198.224.⟨71⟩` |
| 對外入口 | Tainet 家居 NAT（無 tunnel） | **Cloudflare Tunnel** `66ad1cc0-…-992285d` 系列 | nginx 80/443（無 tunnel） |
| 主要服務 | console 5188、5×next、framer-bridge 18790 | web 3100、api 3103、router 8080、openclaw 18789、PG 5432 | clerk-ui 13102、clerk-api 3103、candidate 3100、nginx 80/443、PG 5433 |
| worker | `aika-core-01` | `do-cloud-1` | `do-cloud-2` |

- 另有一台 **C3 = `goaa-aika-cloud-3`**（`64.23.166.⟨121⟩`，`do-c3`）：**純 worker 節點**，無任何監聽埠。

## 3. Worker ↔ 機器 ↔ 代號（建議）

| 建議代號 | worker_id | role | 承載 | 位置 |
|---|---|---|---|---|
| W1 | `aika-1` | `primary_coordinator` | aika-1（Windows 11） | LAN `192.168.1.207` |
| W2 | `aika-2` | `secondary_coordinator` | aika-2（Xubuntu 24.04） | LAN `192.168.1.208` |
| W3 | `do-cloud-1` | `cloud_worker` | **C1** | `134.199.227.⟨108⟩` |
| W4 | `do-cloud-2` | `cloud_worker` | **C2** | `143.198.224.⟨71⟩` |
| W5 | `do-cloud-3` | `cloud_worker` | **C3** | `64.23.166.⟨121⟩` |
| W6 | `aika-core-01` | `aika-box-pro-alpha` | **D0** | tailnet `100.114.37.90` |

> 以上為**建議**；實際改名需 Tao 裁定（本輪唯讀，未改名）。

## 4. DNS（本輪實測）

| 名稱 | 解析（IPv4） | 判定 |
|---|---|---|
| `goaa.ai` | `104.21.54.⟨131⟩`、`172.67.138.⟨183⟩` | **Cloudflare 代理** |
| `www.goaa.ai` | 同上 | Cloudflare 代理 |
| `planning.goaa.ai` | 同上 | Cloudflare 代理 |
| `api.goaa.ai` | 同上 | Cloudflare 代理 |

- `https://goaa.ai/` → **308** → `https://www.goaa.ai/`。

## 5. Tailscale（D0 視角）

`aika-core-01-1`（`100.114.37.90`, linux, active）、`aika-1`（windows, offline）、`aika-2`（linux, offline ~1d）、`fq168-sm-mini-it12`、`ipad156`、`iphone182`、**`tap`**（windows, active, direct `192.168.1.161`）。

## 6. 🔴 待澄清（重要）

- 令文 §C1 寫「IPv4 = `134.199.227.⟨10⟩`」，**本輪實測為 `134.199.227.⟨108⟩`**（`eth0/20`＋`curl ipify` 雙證）。若兩者皆存在，`…10` 可能是**另一台** Droplet ⇒ 需 Tao 由 DO 面板確認（本輪不連面板）。

## 7. 更正

- `known_hosts` 為 **hashed（`|1|…`）** ⇒ 不能由它列舉主機；主機清單以 `~/.ssh/config` 別名＋Tailscale 實測為準。
