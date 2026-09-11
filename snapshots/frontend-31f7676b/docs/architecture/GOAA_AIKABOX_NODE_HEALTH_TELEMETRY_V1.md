# GOAA AiKa-Box Node Health Telemetry Design V1 (B 線)

> **狀態**: 設計文檔。只設計, 不寫代碼、不改 main.py、不新增 endpoint、不重啟 Console、不改 systemd、不碰 /etc/goaa、不讀 secret。
> **所屬**: AiKa-Box Dogfooding Roadmap (B → C → D → A → E → F) 第一戰役 B 線。
> **協議名稱**: Local Fleet Health Probe Protocol(本地 Fleet 健康探針協議)— 第一版為靜態清單 + 主節點輪詢, 非完整去中心化發現協議。

---

## 1. Purpose

讓 AiKa-Box Local Console 的 Node Health / Fleet / Local Node Identity, 從靜態 mock 數據逐步接入真實本地 telemetry。同時為客戶未來購買多台 AiKa-Box 在本地內網組成私有 AI Worker 集群做好架構地基。

採用 **文件級 IPC / sanitized telemetry cache** 方向: worker-agent 採集 → atomic write 本地 JSON → Console 只讀。職責分離, Console 崩潰不影響採集, Console 不碰 secret。

---

## 2. 真實盤點結果(來自 aika-core-01 真實審計, 非憑記憶)

| # | 問題 | 真實結果 |
|---|---|---|
| 1 | 是否已有 /node/health | **無** |
| 2 | 是否已有 /workers/status | **無** |
| 3 | /workers/status 返回什麼 | N/A(不存在) |
| 4 | Node Health/Fleet UI 是否 mock | **是, 全 mock**(本輪 Cyber-Noir UI 的佔位數字) |
| 5 | main.py 哪些是靜態 mock | 節點卡 CPU/MEM/DISK 進度條寫死寬度; 損益 $0.00; 任務計數 0 |
| 6 | 是否已裝 psutil | heartbeat.py 已使用(B-3 寫碼前須確認 venv 內可 import) |
| 7 | 是否有 heartbeat.py | **有** |
| 8 | heartbeat 是否只 POST 雲端、無本地 cache | **是**: 每 30s POST 雲端 router /worker/heartbeat; 無本地寫檔 |
| 9 | goaa-worker-agent.service | running |
| 10 | goaa-local-console.service | running |
| 11 | 是否已有 telemetry cache 檔 | **無**(/opt/goaa/run 不存在) |
| 12 | 是否有 task_result summary | /tasks/results 端點存在, 可複用做 count summary |
| 13 | /rag/stats 是否只返 count 不返正文 | **是**(C2 階段已確認: metadata/count only, 無正文) |
| 14 | Console bind | **127.0.0.1:5188** |

**現有 15 端點**(B 線不動這些): /login(GET+POST) · /logout · /health · /session · /rag/stats · /rag/topk · /rag/chat · /tasks/results · /tasks/results/{id} · /logs/recent · /settings/{models,skills,agents} · /(Dashboard)。

**盤點關鍵結論:**
- 沒有任何 telemetry 真實化基礎 → B 線從零搭(地基性質)。
- heartbeat 只發雲端 → 本地 Console 看不到自己的數據 → B 需要新的本地 cache 鏈, 不依賴雲。
- /opt/goaa/run 不存在 → B-2/B-3 寫碼階段需建(本輪只設計, 不建)。

---

## 3. B-1 / B-2 分階段目標

- **B-1 本機真實健康探針**: 每台 AiKa-Box 提供統一只讀端點 `GET /node/health`, 返回本機真實、脫敏、只讀運行狀態。
- **B-2 本地內網 Fleet 匯總**: 主 Console 經靜態清單 `/etc/goaa/nodes.json` 逐台查詢 `{base_url}/node/health`, 匯總為 `GET /fleet/health`, 顯示本地多 AiKa-Box 私有內網 Fleet 健康狀態。第一版靜態清單, **不做自動掃描 / mDNS / UDP broadcast / LAN 網段掃描**。

---

## 4. Local Console 與 Worker Agent 職責邊界

- **worker-agent**: 負責採集真實 telemetry, atomic write 到本地 cache 檔。
- **Local Console 5188**: 不直接計算底層狀態, 不讀 secret, 不調 worker 內部敏感邏輯。只讀 cache 檔並返回前端。
- **解耦保證**: Console 崩潰不影響 worker-agent 採集; worker-agent 崩潰時 Console 只顯示 stale/offline, 不影響 5188 /health(仍 200)。

---

## 5. /node/health Endpoint Design(B-1)

`GET /node/health` — 只讀, 返回本機 sanitized telemetry。

**讀取來源(兩種設計, B-3 寫碼時定):**
- **方案甲(cache 檔)**: worker-agent 每 ~10s 採集寫 `/opt/goaa/run/telemetry_local.json`(atomic), Console 讀此檔。優: 解耦、Console 零採集負擔。
- **方案乙(當場採)**: Console 被呼叫時用 psutil 當場採。優: 少一個寫檔環節。缺: Console 承擔採集、與 worker-agent 職責混。

**本設計傾向方案甲**(符合「文件級 IPC」指令方向 + 解耦), B-3 確認 run 目錄權限後定案。

---

## 6. Sanitized Telemetry Schema(B-1)

示例為 **mock example, 非真實生產數據**:
```json
{
  "node_id": "aika-core-01",
  "hostname": "aika-core-01",
  "status": "online",
  "collected_at": "2026-06-06T22:34:00-07:00",
  "age_sec": 0,
  "uptime_sec": 86400,
  "telemetry": { "cpu_pct": 23.4, "mem_pct": 41.0, "disk_pct": 54.0, "gpu_pct": null },
  "services": { "ollama": "active", "worker_agent": "active", "local_console": "active" },
  "network": { "tailscale_ip": "100.114.37.90", "lan_ip": "192.168.1.53", "console_bind": "127.0.0.1:5188" },
  "safety": { "contains_secret": false, "contains_rag_text": false, "contains_env": false, "source": "sanitized_local_telemetry" }
}
```

**字段說明:**
- node_id / hostname / status / collected_at / age_sec / uptime: 基本身份與時間。
- telemetry: 純數值。
- services: 只 active/inactive 字串。
- network: tailscale_ip / lan_ip optional(讀失敗 → null); console_bind 固定。
- safety: 脫敏標記。

---

## 7. Optional GPU Design

- `gpu_pct` optional。
- 來源: nvidia-smi snapshot(aika-core-01 有 RTX 3060)。
- **nvidia-smi 不可用 → gpu_pct = null, 端點不得崩潰**。
- 不返回 GPU 序號 / 完整 nvidia-smi 輸出 / driver 版本等多餘資訊, 只取 utilization 數值。

---

## 8. Service Status Design

- ollama / worker_agent / local_console 三項。
- 來源: systemctl is-active 或 localhost 端口探測。
- **只輸出 active / inactive / unknown**, 不輸出 PID、不輸出 cmdline、不輸出 env、不輸出完整 systemctl status 文本(可能含路徑/參數)。

---

## 9. Stale / Warning / Offline Rule

worker-agent 預計每 ~10s 刷新一次(方案甲)。判定(可配置, 非寫死):
- `age_sec <= 30` → **online**
- `30 < age_sec <= 90` → **stale / warning**
- `age_sec > 90` → **offline**
- cache 檔不存在 → **unknown / offline**
- JSON parse error → **telemetry_error**(但 /health 仍 200)

閾值最終可配置化, 不寫死為不可變規則。

---

## 10. Error Handling

- telemetry 採集失敗 → 不讓 Console 崩潰, 對應字段 null + status 降級。
- cache 檔半截(寫入中) → atomic write 機制避免(見 §11)。
- JSON parse error → 返回 telemetry_error 標記, 不拋給前端 traceback。
- nvidia-smi / tailscale / lan_ip 讀取失敗 → 對應字段 null, 不影響整體。
- **任何錯誤路徑不得返回 traceback 中的敏感資料 / env / secret / 路徑細節**。

---

## 11. Atomic Write(worker-agent 寫 cache 時)

不得直接覆蓋目標檔。必須:
1. 寫臨時檔 `/opt/goaa/run/telemetry_local.json.tmp`
2. fsync 或確保寫入完成
3. atomic rename 到 `/opt/goaa/run/telemetry_local.json`

原因: 避免 Console 正讀時讀到半截 JSON。

---

## 12. Safety / Redaction Rules

**telemetry 與端點禁止包含/返回:**
secret · env · DATABASE_URL · PGPASSWORD · token · API key · worker_secrets · RAG raw text · raw prompt · raw task content · 含敏感資料的 traceback · 完整 network config · 完整 process env。

**cache 檔禁止寫入:** secret / env / raw RAG text。

---

## 13. UI Field Mapping

| UI Field | Source | Phase | Risk | Redaction |
|---|---|---|---|---|
| CPU | /node/health telemetry.cpu_pct | B-1 | low | numeric only |
| MEM | /node/health telemetry.mem_pct | B-1 | low | numeric only |
| DISK | /node/health telemetry.disk_pct | B-1 | low | numeric only |
| GPU | optional /node/health telemetry.gpu_pct | B-1 | low | numeric/null |
| Ollama | /node/health services.ollama | B-1 | low | active/inactive only |
| Worker Agent | /node/health services.worker_agent | B-1 | low | active/inactive only |
| Local Console | /node/health services.local_console | B-1 | low | active/inactive only |
| heartbeat age | /node/health age_sec | B-1 | low | seconds only |
| Fleet Cards | /fleet/health nodes[] | B-2 | medium | sanitized summary |
| RAG Chunks | /rag/stats | separate | medium | count only, no text |
| task count | /tasks/results summary | separate | medium | count only |

---

## 14. B-2 Local Fleet Design

主 AiKa-Box Console 經靜態清單讀取內網其他 AiKa-Box, 逐台查 `/node/health`, 匯總 `/fleet/health`。

### 14.1 /etc/goaa/nodes.json 設計預覽(本輪只設計, 不創建)
```json
{
  "local_node_id": "aika-core-01",
  "cluster_mode": "static_local_fleet",
  "nodes": [
    { "node_id": "aika-core-01", "base_url": "http://127.0.0.1:5188", "role": "primary" },
    { "node_id": "aika-box-02",  "base_url": "http://192.168.1.54:5188", "role": "worker" }
  ]
}
```
安全要求: 不含 secret / token / API key / 資料庫連接串 / 客戶數據; 不自動掃描 LAN; 不接雲端。

### 14.2 /fleet/health 設計預覽
讀 nodes.json, 並發查每台 /node/health。要求:
- 每節點查詢有 timeout
- 單節點失敗不影響整體返回
- 失敗節點標 offline / timeout
- 返回 sanitized summary, 不返 raw traceback / secret / env / RAG 正文
```json
{
  "fleet_status": "degraded",
  "total_nodes": 3, "online_nodes": 2, "offline_nodes": 1,
  "nodes": [
    { "node_id": "aika-core-01", "status": "online", "cpu_pct": 23.4, "mem_pct": 41.0, "disk_pct": 54.0, "age_sec": 1 },
    { "node_id": "aika-box-02", "status": "timeout", "error_type": "timeout" }
  ]
}
```

---

## 15. Why No Auto LAN Scanning in V1

第一版**不做**自動 LAN 掃描 / mDNS / UDP broadcast / 整網段掃描, 原因:
- 掃描慢、有網路權限與防火牆問題。
- 自動發現會在客戶內網產生非預期流量, 安全與合規風險高。
- 靜態清單簡單可靠, 客戶手動加節點即可滿足「多 Box 集群」場景。
- 自動發現留待 v2(屆時需專門設計安全發現協議 + auth)。

---

## 16. 網絡邊界

當前 systemd 第一版綁定 `127.0.0.1:5188` → B-1 只需本機可用。
B-2 若要讓其他 Box 訪問 /node/health, 須**另行設計網絡階段**(本輪不開放):
Tailscale Phase 1 · LAN mode Phase 2 · allowed subnet/IP list · local auth/token/mTLS 是否需要 · firewall rule · timeout · audit。
**本輪不得寫成已對 LAN/Tailscale 開放。**

---

## 17. Implementation Phases

- **B-1 設計(本文檔)** ✅ — 盤點 + /node/health 設計 + schema + 規則
- **B-2 worker-agent telemetry cache** — 採集 + atomic write + optional GPU + no secret(寫碼, 須 Tao 確認)
- **B-3 Console read-only endpoint** — 5188 讀 cache + stale/offline 判定 + parse error fallback + no crash(寫碼, 須 Tao 確認)
- **B-4 UI 接真實數據** — Node Health/Local Node Identity 卡替換 mock, 保留 Cyber-Noir UI, no RAG text(改 main.py HTML, 須 golden diff + Tao 確認)
- **B-5 reboot/systemd/audit** — reboot 後服務自恢復, telemetry 刷新, endpoint 正常, journal 無 secret, devlog 記錄

每階段獨立做、獨立驗、獨立入庫, 進寫碼前須 Tao 單獨確認。

---

## 18. Rollback Plan

- B-2/B-3/B-4 任一階段出問題 → golden backup(main.golden.20260607.py / Console golden fc76397d)隨時 cp 回 + 重啟。
- worker-agent 改動前先備份 heartbeat.py / agent.py。
- /opt/goaa/run 與 nodes.json 為新增, 出問題刪除即回到當前狀態(不影響現有 15 端點)。
- 每階段保留指紋, 可逐步回退。

---

## 19. Open Questions Before Code(寫碼前須答)

1. **方案甲 vs 乙**: telemetry 由 worker-agent 寫 cache(甲)還是 Console 當場採(乙)? 設計傾向甲, 待確認。
2. **/opt/goaa/run 權限**: 由哪個運行用戶可寫? worker-agent 與 console 是否同用戶? 不確定則先不改權限。
3. **psutil 是否在 console venv**: heartbeat 用了 psutil, 但 console venv 是否可 import 待驗(B-3 前確認)。
4. **採集頻率**: worker-agent 每 10s? 與現有 30s 雲端 heartbeat 是否共用採集還是分開?
5. **GPU 採集方式**: nvidia-smi subprocess vs pynvml? 頻率?
6. **B-4 改 main.py**: Node Health UI 接真實要改 index() HTML(動黃金版 UI)— 須 golden diff + Tao 確認後才動。

---

## 20. Audit Checklist 增量建議(僅建議, 不直接改 checklist)

### 分布式邊緣集群健康度核驗(B-1/B-2)
- [ ] B-1 /node/health 本機真實健康端點設計完成
- [ ] B-1 psutil CPU/MEM/DISK 採集設計完成
- [ ] B-1 optional GPU fallback 設計完成
- [ ] B-1 service status sanitized 輸出設計完成
- [ ] B-1 secret/env/RAG raw text 阻斷規則完成
- [ ] B-2 /etc/goaa/nodes.json 靜態清單設計完成
- [ ] B-2 /fleet/health 聚合設計完成
- [ ] B-2 timeout/offline/degraded 規則完成
- [ ] B-2 第一版明確不做 LAN auto-scan / mDNS / UDP broadcast
- [ ] UI Field Mapping 完成
- [ ] atomic write 機制設計完成
- [ ] stale/warning/offline 判定規則設計完成

---

*GOAA AiKa-Box Node Health Telemetry V1 — B 線設計 — Local Fleet Health Probe Protocol — 只設計不寫碼 — 無 secret / 無 RAG 正文 / 無未核驗專利號 / 無收益承諾*
