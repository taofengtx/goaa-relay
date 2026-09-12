# D0.3（收掉 8080 公網放行）— **CANCELLED / 撤銷**

- **裁決**：Tao，2026-09-12（PT 2026-09-11）
- **本輪對 ufw 的變更**：**無**。D0.3 只做到前置（唯讀＋備份＋預演）階段即 STOP 回報；`ufw delete allow 8080/tcp` **從未執行**。
- **正式結論**：

> D0.3 經 Tao 裁示撤銷：公網 8080 的使用者是 Aika-Box 專案的 worker 機隊，與本次 goaa.ai 三端發版無關；且同樣端點已由 api.goaa.ai 的 ingress 對外提供，關埠無實質收益。
> 正解為 worker 端點加鑑權，歸入 Aika-Box 專案待辦。本輪未對 ufw 做任何變更。

## 附：為何會走到撤銷（前置階段的發現）

前置檢查一度被 D0.1 的結論誤導（「沒有客戶端依賴公網 8080」）。深入取證後推翻了該前提：

- `ss` 快照只看到 loopback，但**路由器日誌**顯示 **4 台遠端 worker 直接連公網 8080**，每台約 1,600 reqs/2h（≈ 每 5 秒一次 `GET /tasks/next/<worker>` ＋ `POST /worker/heartbeat`）：

| worker | 對端 | 專案角色 |
|---|---|---|
| do-cloud-2 | `143.198.224.⟨71⟩` | Aika-Box worker 機隊 |
| do-cloud-3 | `64.23.166.⟨121⟩` | Aika-Box worker 機隊 |
| aika-core-01 | `165.162.8.⟨177⟩` | Aika-Box worker 機隊 |
| aika-1 | `98.191.202.⟨15⟩` | Aika-Box worker 機隊 |

- 前置階段已完成、且**保持原狀未使用**的備份：`/etc/ufw/user.rules.bak.20260912-012545`（1,908 B）、`/etc/ufw/user6.rules.bak.20260912-012545`（1,887 B）、`/root/iptables-save.before-d0-3.20260912-012545.txt`（7,581 B）。
- 備份與預演結果僅為當時的取證紀錄；**8080 的 ufw 放行規則目前仍在原樣（`ufw status numbered` 之 [4]/[9]）**，無需回滾。

## 交接

- **正解**：worker 端點加鑑權（`/tasks/next/*`、`/worker/heartbeat`、`/task/complete`）。
- **歸屬**：**Aika-Box 專案待辦**（與 goaa.ai 三端發版無關）。
- **未完成、已作廢的後續事項**：D0.3 刪除 ufw 規則 → **不再執行**。
- 相關（唯讀勘查、供 Aika-Box 參考，本輪未變更任何設定）：`reports/2026-09-12/d0-3b-tunnel-migration/RECON.md`。
