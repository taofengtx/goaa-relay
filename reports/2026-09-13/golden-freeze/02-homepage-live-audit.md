# 02 — 首頁 live 稽核（goaa.ai / www.goaa.ai）

- 日期：2026-09-13；方法：`curl -s -D` 兩次（唯讀 GET），落檔後逐字串統計。
- 檔案：`www.goaa.ai` 回應 body = **687,067 bytes**，與 `goaa.ai`（308 → www）同。

## 1. 標頭

| 項目 | 值 |
|---|---|
| HTTP | `goaa.ai/` → **308** → `https://www.goaa.ai/`；`www.goaa.ai/` → **200** |
| server | `cloudflare` |
| cf-cache-status | `DYNAMIC` |
| last-modified | `Sun, 13 Sep 2026 07:18:33 GMT`（**今日**，即 Framer 當日重新發佈） |
| cache-control | `public, max-age=0, must-revalidate` |

## 2. 新定位（已上線）✓

| 字串 | 出現次數 |
|---|---|
| `Your Personal AI Agents` | **2** |
| `Get Things Done` | **2** |
| `Make Money` | **2** |

## 3. 仍為舊定位（未更新）⚠️

| 字串 | 出現次數 | 位置 |
|---|---|---|
| `GOAA.AI Life&Asset Intelligence` | **3** | `<title>`、`og:title`、`twitter:title`（HTML 中以 `Life&amp;Asset` 形式） |
| `GOAA is an AI planning assistant that helps you organize your life and assets` | 1 | `description` |

⇒ 頁面「身體」已是新定位，但**社群/搜尋預覽（metadata）仍是舊品牌字串**。這是外部看到「舊內容」最可能的原因之一（另一可能是搜尋引擎舊快取）。**本輪未修改**。

## 4. 殘留與異常（唯讀發現）

| 項目 | 命中 | 說明 |
|---|---|---|
| `https://cal.com/goaa.ai/30min` | **1** | 與 `GOAA_PAID_CONNECTION` 關閉後的「30 分鐘預約」替代路徑同源（見 08 報告）；目前首頁仍留此 CTA |
| `https://help@goaa.ai` | **1** | **疑似壞連結**（`https://` 後直接接 `help@`），待確認是否應為 `mailto:` |
| `planning.goaa.ai/agent-login` | **5** | 舊路徑，live 會 307 → `/client-login?next=/agent-loop/agent`（多一跳） |
| `planning.goaa.ai/client-login` | **4** | 統一入口 ✓ |
| `connect-pass` | **3** | 指向已關閉的 $39.90 連線流程（見 08 報告） |
| `39.90` | **0** | 首頁未再出現價格 ✓ |

## 5. 舊內容指紋（全部 0 命中）✓

`Radison` / `480` / `李` / 電話 / `预约` / `預約` / `模板` / `草稿` / `Telegram` / `WhatsApp` 皆 **0**。
`960` 的 11 次命中經核為 **CSS token UUID**（假陽性），非舊價格。

`og:image` = `https://framerusercontent.com/images/6uVqogXv0jnucc67CxBdOfLHw0.png`；`canonical` = `https://www.goaa.ai/`；`robots` = `max-image-preview:large`。

## 6. 判讀

1. **live HTML 不含任何舊內容** ⇒ 若外部仍見舊版，來源不是當前 live HTML（推測：搜尋引擎索引快取、或 Framer 舊 draft/preview 連結）。
2. 但 **metadata 三個 title 仍是舊定位**，社群分享卡與搜尋結果會顯示舊文案 —— 這是**真實且可修**的落差。
3. `cal.com` 與 `agent-login`（5 處）為待收尾項，**本輪不動**。
