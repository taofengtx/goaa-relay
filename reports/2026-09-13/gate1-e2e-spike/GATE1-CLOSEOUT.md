# GATE 1 — Aika-Box × QwenPaw Bridge: End-to-End Spike — CLOSEOUT

- **Date:** 2026-09-13 · **Time box:** MAX 2 HOURS
- **Window used:** 11:15 UTC → 11:47 UTC ≈ **32 min**（盒內，未延時）
- **Verdict: ✅ PASS** — 完整鏈路已證明，且 **A–G 全數 PASS**
- **Mode:** 只讀 + 無害可逆測試；未改 QwenPaw、未改 5188、未部署、未改 firewall

---

## 1. 被證明的鏈路（令文原始目標）

```
Aika-Box :5199 → QwenPaw → Send Message → SSE Response → Trigger Approval
→ Aika-Box 捕獲 Approval → Approve/Reject 決策提交 → QwenPaw 原 Run 自動續跑
→ Final Result 回流
```

**結論：全鏈路單次可重複成立**，六項能力全部走 **QwenPaw 原生 REST（A. NATIVE API）**，
不需 browser automation、不需修改 QwenPaw。

---

## 2. 測試矩陣

| # | 測試 | 結果 | 證據（實測） |
|---|------|------|--------------|
| A | Send Message | ✅ PASS | `POST /api/console/chat` HTTP 200、SSE **31** events、`elapsed_ms=1207`、terminal `status=completed`、回文 `AIKA_QWENPAW_BRIDGE_OK`、session 回顯一致 |
| B | Session Continuity | ✅ PASS | 同 session 續問成功、SSE **71** events / 1299 ms；`GET /api/chats` 見 chat `status=idle`、`GET /api/chats/{id}` 6 條歷史含該短語 |
| C | Approval Capture | ✅ PASS | `crontab -l` → tool_guard `TOOL_CMD_SYSTEM_TAMPERING` **HIGH** → `/api/console/push-messages` 回 pending，全欄位可取（`request_id/session_id/root_session_id/agent_id/tool_name/severity/findings_count/findings_summary/tool_params/created_at/timeout_seconds`） |
| D | Approval Card | ✅ PASS | 卡片 DOM 渲染：標題 + `auto-approve: disabled \| decisions require a human click` + 表頭 `Worker(session)/Tool/Severity/Requested action/Created/Expires in/Decision` + Approve/Reject 按鈕（以 `document.body.innerText` 驗證；模型無多模態，截圖 `/tmp/qp-card.png` 存檔） |
| E | **Approve** | ✅ PASS | 見 §3 |
| F | **Reject** | ✅ PASS | 見 §3 |
| G | Reconnect | ✅ PASS | 對同一 blocked run `reconnect=true` → HTTP 200、replay **89** events、`sequence_range=[0,88]`、單一 `response_id`、run 仍 `running`、approval 仍 pending（串流續開導致的 ReadTimeout 為預期） |

---

## 3. E / F 詳細證據

### 決策提交（橋接 → QwenPaw 原生審批 API）

| 測試 | session | request_id | 決定 | bridge HTTP | QwenPaw 回應 |
|------|---------|-----------|------|-------------|--------------|
| E | `spike-e-1789298749` | `fcf7d780-a788-4a02-94a6-3261c66d118e` | **APPROVE** | 200 | `{"success":true,"message":"Tool 'execute_shell_command' approved, executing...","tool_name":"execute_shell_command"}` |
| F | `spike-f-1789298749` | `0e2b63d9-19a9-4888-a7a0-28aa2488be84` | **DENY** | 200 | `{"success":true,"message":"Tool 'execute_shell_command' denied: <reason>","tool_name":"execute_shell_command"}` |

上游端點 = `POST /api/approval/approve` / `POST /api/approval/deny`。
決策時間戳 `1789299979` = **2026-09-13 11:46:19 UTC**；兩筆決策已寫入 `/tmp/qp-spike-decisions.log`（副本見 `evidence/`）。

### E — Approve ⇒ 原 run 續跑、命令真正執行（PASS）

批准後**同一個 run 未經 resume 即續跑**，模型回報逐字原始輸出：

```
Command failed with exit code 1.
[stderr]
no crontab for aika
```

- 查詢：`crontab -l`（原樣提交）
- 退出碼 1 + `no crontab for aika` = 當前使用者無 crontab 條目（**命令確實執行了**）
- 該 session chat `status=idle`、messages=18，最終結果已回流並可經 `GET /api/chats/{id}` 讀取

> **判定依據：** approval 是對「阻塞中的工具呼叫 Future」resolve ⇒ 批准＝放行執行，**不需要額外 resume 呼叫**；結果自動回流。

### F — Reject ⇒ 未執行、run 續行、可觀測狀態不變（PASS）

- 被拒命令：`chmod -R 777 /tmp/goaa-bridge-spike-scratch`（`TOOL_CMD_UNSAFE_PERMISSIONS` HIGH）
- 模型回報：**「注意：这不是你要求的那条命令，你那条我没執行」**，改以只讀方式檢查
- **可觀測判據**：`/tmp/goaa-bridge-spike-scratch` 在決策前後 mode 均為 **`0o700`（`drwx------`）** ⇒ 證明 `chmod` **未被執行**
- 該 session chat `status=idle`、messages=21 ⇒ **run 未中斷，拒絕後照常繼續並回報**

---

## 4. 偏離與合規註記（必須記錄）

1. **橋接部署形態偏離（令文條件式允許）**：令文允許「若必須接 5188：優先新增獨立 namespace `/api/qwenpaw-spike/*`」。本輪**未改 5188**（改 `main.py` + 重啟生產服務風險高，且令文禁動 systemd 生產服務），改以**獨立 FastAPI 進程**綁 tailnet `100.114.37.90:5199`，提供**同名 namespace** `/api/qwenpaw-spike/{health,pending,card,approve,deny}`。
2. **🔴 E/F 決策由誰按下**：令文 §8 明令「**嚴禁腳本自動批准**，Approve/Reject 必須由人決定」。本輪 **Tao 於 console 明確下達「approve e / reject f」指令**，故由 bridge 以 HTTP 提交該**人工決定**（`auto_approve: false` 全程有效；**re-arm daemon 只重新武裝、從未自行決策**）。**但嚴格而言，按鈕並非 Tao 親手在瀏覽器點擊** —— 此為與令文的**程序性偏離**，據實記錄，供 Tao 判定 Gate-1 有效性。
3. **審批窗口與重複 pending**：審批 `timeout_seconds=300`；對同一 session 重複觸發會產生**多筆 pending**（本輪 spike-c/e/f 共遺留 5 筆未決，見 §6）。橋接已做 **client-side 過濾 + 依 `request_id` 去重 + 每 session 只留最新一筆**。
4. **未動任何系統**：未 deploy / 未 restart 任何生產 service / 未寫 DB / 未改 firewall / 未改 QwenPaw 源碼 / 未 push spike 代碼。測試命令全部無害可逆（`crontab -l` 只讀；`chmod` 對專用 scratch 目錄且最終未執行）。

---

## 5. 收尾清理（已完成）

| 項目 | 狀態 |
|------|------|
| spike 服務 `uvicorn spike_api:app`（PID 2309646） | ✅ **已停**（SIGTERM） |
| re-arm daemon `qp-rearm.py`（PID 2310194） | ✅ **已停**（SIGTERM） |
| Port `5199` | ✅ **已釋放**（`ss` 確認 5199 free） |
| decisions log | ✅ 已保存副本 `evidence/qp-spike-decisions.log`（742 B, 2 筆） |
| `/tmp/goaa-bridge-spike-scratch` | 保留（mode `0o700`，作 F 的判據留痕） |

---

## 6. 遺留（不影響 PASS，供後續處理）

- **5 筆 stale pending approvals** 仍留在 QwenPaw（`spike-c ×2`、`spike-e ×2`、`spike-f ×1`）。QwenPaw 無「撤銷 pending」端點，且**不得由腳本代決策**，故**不處理**，待 QwenPaw GC（`_GC_MAX_AGE_SECONDS=3600`）自然回收。
- 另有一筆 Aika-Box agent 自身 session 的審批歷史（`rm -rf` 類）同樣自然過期，未代決策。

---

## 7. 交付物清單

| 檔 | 說明 |
|----|------|
| `GATE1-CLOSEOUT.md` | 本報告 |
| `evidence/qp-spike-decisions.log` | E/F 兩筆決策的完整 upstream 回應記錄 |
| spike 套件（未 push） | `~/.qwenpaw/workspaces/default/qwenpaw_bridge_spike/`：`client.py` / `approval.py` / `spike_api.py` / `README.md` |

---

## 8. Gate 2 建議（待 Tao 令）

Gate-1 已證明「**一條真實、完整、可重複的鏈路**」。若要進 Gate 2（MVP），前置估計（沿用可行性評估）：Best 9 h / **Expected 15 h** / Worst 28 h；最大風險 = **R1 安全**（QwenPaw API 現況 `auth/status` → `enabled=false`，且 agent 可執行工具）。

**未得令前不動 QwenPaw / 5188。**

---

*End of GATE1-CLOSEOUT.md — Gate-1 spike closed.*
