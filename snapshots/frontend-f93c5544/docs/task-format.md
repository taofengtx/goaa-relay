# GOAA.AI 標準任務格式規範
**版本：** v1.0.0  
**日期：** 2026-05-07

---

## 標準 task.txt 格式（10個核心欄位）

```
# GOAA TASK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[01] task_id:        GOAA-{YYYY}{MM}{DD}-{序號}
                     例：GOAA-20260507-001

[02] title:          任務標題（一句話描述）

[03] priority:       P0 / P1 / P2 / P3
                     P0=今天必須 P1=本週 P2=本月 P3=長期

[04] assigned_to:    aika-dev / aika-devops / aika-test /
                     aika-browser / aika-security / aika-docs / aika-data

[05] description:    詳細任務描述
                     （可多行，包含背景、目標、範圍）

[06] input_files:    需要的輸入文件或數據
                     例：/opt/goaa/main.py, users.json

[07] steps:          執行步驟（有序列表）
                     1.
                     2.
                     3.

[08] acceptance:     驗收標準（可量化）
                     - 條件1
                     - 條件2
                     - 條件3

[09] risk_level:     LOW / MEDIUM / HIGH / CRITICAL
                     需要審批：HIGH 及以上需 Tao 師兄批准

[10] rollback:       回滾方案
                     如失敗如何恢復到初始狀態

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
輸出格式:    markdown / json / file / none
預計時長:    5min / 30min / 2hr / 1day
```

---

## 完整範例

```
# GOAA TASK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[01] task_id:        GOAA-20260507-001

[02] title:          在 OpenClaw 加入節點心跳 API

[03] priority:       P0

[04] assigned_to:    aika-devops

[05] description:
     現有的 /api/v1/geekom/heartbeat 端點需要擴展，
     支持節點能力自報（CPU/RAM/角色/版本），
     並存入持久化數據庫而非內存。
     目標：服務器重啟後節點數據不丟失。

[06] input_files:
     /opt/goaa/main.py
     /opt/goaa/users.json

[07] steps:
     1. 查看現有 heartbeat 端點代碼
     2. 設計新的數據結構（加入 capabilities 欄位）
     3. 修改端點支持擴展字段
     4. 加入 PostgreSQL 持久化（或 JSON 文件暫代）
     5. 重啟服務測試
     6. 驗證節點數據在重啟後保留

[08] acceptance:
     - POST /api/v1/geekom/heartbeat 返回 200
     - GET /api/v1/geekom/devices 顯示節點詳情含 capabilities
     - 重啟 OpenClaw 後節點數據仍存在
     - 響應時間 < 100ms

[09] risk_level:     MEDIUM
     （修改現有端點，需測試後才上線）

[10] rollback:
     cp /opt/goaa/main.py.bak.latest /opt/goaa/main.py
     systemctl restart openclaw

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
輸出格式:    json（API 測試結果）
預計時長:    2hr
```

---

## 優先級定義

| 等級 | 說明 | 響應時間 |
|------|------|---------|
| P0 | 阻塞生產/用戶無法使用 | 今天內 |
| P1 | 重要功能缺失 | 本週內 |
| P2 | 優化/改進 | 本月內 |
| P3 | 長期規劃/nice-to-have | 季度內 |

## 風險等級定義

| 等級 | 說明 | 審批要求 |
|------|------|---------|
| LOW | 新增功能，不影響現有 | 自動執行 |
| MEDIUM | 修改現有功能 | AiKa 執行 + 記錄 |
| HIGH | 修改核心服務/數據庫 | 需 Tao 師兄批准 |
| CRITICAL | 生產數據操作/密鑰變更 | 雙重確認 |

## AiKa 角色對應

| 角色 | 負責任務類型 |
|------|------------|
| aika-dev | 代碼開發、功能實現 |
| aika-devops | 服務器部署、環境配置 |
| aika-test | 自動化測試、驗收 |
| aika-browser | 瀏覽器自動化、UI 驗證 |
| aika-security | 安全審查、漏洞掃描 |
| aika-docs | 文檔撰寫、changelog |
| aika-data | 數據處理、報表生成 |

---

*文檔維護：Claude | ChatGPT 語音輸入後按此格式整理*
