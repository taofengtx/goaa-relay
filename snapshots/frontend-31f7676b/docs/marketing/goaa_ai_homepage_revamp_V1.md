# goaa.ai 主頁改造 V1.0 — Sitemap + Section 結構

**版本**: V1.0
**最後更新**: 2026-05-16 22:40 PT
**配套**: `docs/business/GOAA_BUSINESS_MODEL_V1.md` (戰略憲法主檔)
**狀態**: 設計藍圖, 等師兄拍板 → Framer 實作

---

## 📌 文件角色標籤

```text
本文角色: goaa.ai 公開主頁改造設計
本文類型: Frontend Public Design Plan
是否允許直接執行: 否 (Framer 改造需師兄真實操作 / AiKa 設計師執行)
是否允許修改 Production: 否 (Framer 由師兄編輯)
是否需要 Tao 拍板: 是
最高參考來源: GOAA_BUSINESS_MODEL_V1.md (戰略源) + AGENTS.md (命名源)
```

---

## 🎯 一、改造目標 (大公司級標準)

### 三大觀眾並重

| 觀眾 | 看完主頁後應該知道 | CTA |
|---|---|---|
| **用戶 (Client / Provider)** | GOAA 能幫我解決什麼問題 | "Try GOAA" / "Talk to GOAA" |
| **投資人** | GOAA 商業模式 / Traction / 護城河 | "Investor Deck" / "Contact" |
| **人才 / Worker** | 為什麼加入 GOAA 生態 | "Join Worker Network" |

### 對標的大公司主頁
- **Stripe** (`stripe.com`) — 開發者友好 + 清晰價值主張
- **Linear** (`linear.app`) — 極簡黑色美學 + 強動畫
- **Vercel** (`vercel.com`) — 技術 + 商業平衡
- **OpenAI** (`openai.com`) — Hero 一句話定義
- **Anthropic** (`anthropic.com`) — 學術氣 + 視覺品質

---

## 🗺️ 二、新版 Sitemap

### 主頁 (`goaa.ai`) — 一頁式滾動

```
[Section 1] Hero
[Section 2] Why GOAA (核心定位)
[Section 3] Three-Layer Architecture (Client / Provider / Worker)
[Section 4] How It Works (4 步驟流程)
[Section 5] Live Workers (Runtime Truth 真實數據)
[Section 6] Skill Marketplace Preview
[Section 7] AiKa Box (本地 AI Worker)
[Section 8] Built for Complex Lives (Use Cases)
[Section 9] Investor Highlights (Metrics + Vision)
[Section 10] Team (Founder + Advisors)
[Section 11] CTA Final (3 個入口)
[Section 12] Footer
```

### 子頁面 (二期, 不今晚做)
- `/portal` → 跳轉 portal.goaa.ai
- `/workers` → Worker Network 詳情
- `/skills` → Skill Marketplace
- `/aika-box` → AiKa Box 產品頁
- `/investors` → Investor Deck (private link)
- `/blog` → Dev Log + Strategy posts
- `/about` → Team + Mission

---

## 📋 三、每個 Section 詳細設計

### Section 1: Hero (核心)

**佈局**: 全屏黑底 (Cyber-Noir 延續) + 德牧 Logo 浮動 + 動態 typing 文字

**標題 (大字)**:
```
The AI Labor Platform
for Complex Lives

AI 勞動力平台, 為複雜人生而生
```

**副標題 (一句話定義 ⭐)**:
```
GOAA.AI turns complex human needs into:
AI understandable / Provider serviceable / Worker executable / Skill sustainable

GOAA.AI 把人的複雜需求, 轉化為:
AI 可理解、Provider 可服務、Worker 可執行、Skill 可沉澱
```

**動態元素**:
- 德牧 Logo 微微呼吸動畫 (3 秒 cycle)
- 背景 cyber-noir 漸層 (#0a0e1a → #0d1830)
- 主標題用 typing animation (3 秒打完)

**CTA 按鈕** (3 個):
```
[Try GOAA Free →]  [Worker Network →]  [Investors →]
   (用戶)            (Worker)            (投資人)
```

---

### Section 2: Why GOAA (核心定位)

**標題**: 「Not another chatbot. Not another SaaS.」

**3 欄對比** (大公司常用):

| ❌ Most AI Tools | ✅ GOAA.AI |
|---|---|
| Answer questions | **Understand life structure** |
| Suggest decisions | **Generate executable paths** |
| Stop at chat | **Connect to real humans + real workers** |

**強訊息**:
- 「We don't sell products or push decisions」
- 「AI designs the blueprint. Humans + Workers execute with precision」

---

### Section 3: Three-Layer Architecture ⭐ 戰略憲法核心

**標題**: 「One platform. Three layers. Real outcomes.」

**3 個大卡片** (黑底 + 不同顏色邊框):

#### 卡片 1: Client (用戶層)
- **色**: 藍色 (#60a5fa)
- **圖示**: 👤 用戶
- **主訊息**: 「For people with complex global lives」
- **副訊息**: 「Income · Identity · Housing · Tax · Education · Risk · Family」
- **價值**: 「Free chat + Plus ($19.99/月 connect to real professionals)」

#### 卡片 2: Provider (專業者層)
- **色**: 綠色 (#34d399)
- **圖示**: 💼 律師/會計師
- **主訊息**: 「For licensed professionals」
- **副訊息**: 「Real estate · Insurance · Tax · Law · Immigration · Finance · Healthcare」
- **價值**: 「Free CRM + Pro ($39.99/月 receive AI-filtered leads)」

#### 卡片 3: Worker (AI 數字勞動力層)
- **色**: 橙色 (#fb923c)
- **圖示**: 🤖 Worker
- **主訊息**: 「For AI labor nodes」
- **副訊息**: 「Cloud + Local AiKa Box · Produces Skills · Earns Credits」
- **價值**: 「Build skills. Earn revenue share. Join the labor economy」

---

### Section 4: How It Works (4 步驟流程, 對齊白皮書)

**標題**: 「From complex need to executable path」

**4 個橫向卡片** (帶箭頭連接):

```
[1. AI Listens]  →  [2. Structure Modeled]  →  [3. Path Generated]  →  [4. Workers Execute]
   收集需求          建模生活結構               生成藍圖               派發執行
   AI 對話           Income/Tax/Risk           Personalized          Provider + Worker
```

**每個步驟下方有小例子**:
- 1: 「I got an IRS letter and don't understand it」
- 2: 「Tax situation + 3 dependents + W-2 income → high audit risk」
- 3: 「3 steps: Reply by Mar 15 → Submit Form 8862 → Schedule CPA call」
- 4: 「GOAA worker drafts reply. Tax Provider reviews. Done in 48 hours.」

---

### Section 5: Live Workers ⭐ (Runtime Truth 真實數據)

**標題**: 「Real workers. Real tasks. Real time.」

**Dashboard 預覽** (從 portal 截圖縮小版):
- 顯示 5 個 worker live (aika-1/aika-2/do-cloud-1/2/3)
- 真實 task 列表 (health_check / tasks 等)
- 真實 today profit / cost (即使是 $0.X, 也是 Runtime Truth)

**底下小字**: 「No mock data. What you see is what's running.」

⚠️ **規範 SUPREME 1.4 Runtime Truth 嚴守**:
- 如果 API 未連接, 顯示「Connecting...」, **不顯示假數字**
- 這條是 GOAA 跟大部分「AI 平台」的根本差異

---

### Section 6: Skill Marketplace Preview (V4.3+ Coming Soon)

**標題**: 「The first AI Skill Marketplace」

**示例卡片**:
- 「Family Mail Manager」 - $2.99/月 - 1,000 subscribers (or "Coming soon")
- 「Tax Document AI」 - $4.99/月 - For Provider
- 「Property Valuation Pro」 - $9.99/月 - For Real Estate Provider

**底下說明**:
「Skills are built by Workers. Subscribed by Clients & Providers. Continuously improved by feedback.」

---

### Section 7: AiKa Box ⭐ (本地 AI 護城河)

**標題**: 「Take AI labor home / to your office」

**3 個賣點**:
1. 🔒 **Local-first** - Your data never leaves your machine
2. ⚡ **GPU-powered** - Run AI inference at the edge
3. 🛠️ **Plug-and-play** - Connect to GOAA cloud OS

**規格**:
- One-time: **$999** hardware
- Subscription: **$99/月** with cloud sync + Skill updates

**圖示**: 德牧 Logo + 機箱 illustration

---

### Section 8: Built for Complex Lives (Use Cases)

**標題**: 「Whose complex life GOAA solves」

**4 個 Use Case 卡片**:

#### Use Case 1: Global Family
「Multinational family with US W-2 + China property + Taiwan parents」
- GOAA models: Tax exposure / Inheritance risk / Healthcare gap
- Connects: US CPA + China lawyer + Taiwan medical

#### Use Case 2: Founder
「Tech founder pre-IPO with stock options + complex tax + family planning」
- GOAA models: Stock vesting strategy / Trust structure / Education planning
- Connects: M&A lawyer + Financial planner + Estate attorney

#### Use Case 3: Provider
「Real estate broker losing leads to bigger agencies」
- GOAA brings: AI-filtered qualified leads / Auto CRM / Doc generation
- Result: 3x close rate, 50% time saved

#### Use Case 4: Worker
「Software engineer side-building AI skills」
- GOAA enables: Skill development / Marketplace listing / Revenue share
- Result: $X/月 passive income from owned Skills

---

### Section 9: Investor Highlights ⭐ (大公司必有)

**標題**: 「By the numbers」

**Metrics Grid** (4-6 個):
```
[Live Workers: 5]      [Tasks Today: X]
[Daily Active: Y]      [Skills in Production: Z]
[Worker Network: A]    [TAM: $XB by 2030]
```

⚠️ **規範 SUPREME 1.4**: 真實數據, 不誇大. 如果現在小, 標「Q2 2026」/「Early stage」

**Vision 段落**:
「By 2030, AI Labor Economy will replace traditional SaaS subscriptions. GOAA is building the operating system.」

**FundRaising 訊號**:
- 不直接寫 "Pre-seed $X" (太銷售)
- 寫 「Building Phase 4 — Worker V5.0 production line」
- 「Backed by [list advisors if any]」
- 「Contact for investor materials →」

---

### Section 10: Team (Founder + Advisors)

**標題**: 「Built by [數字] across [N] timezones」

**Founder 大卡** (Tao 師兄):
- 大頭照 + 名字 + Title (Founder & CEO)
- 一段 mini bio (e.g. "Building AI infrastructure for complex global lives. Based in Santa Monica.")
- LinkedIn + Twitter

**AI Team** (誠實的部分):
- 「Co-built with Claude, ChatGPT, Gemini」
- 這是 GOAA 的差異化: **AI-native organization**

**Advisors** (如有):
- 列出真實 advisors

---

### Section 11: CTA Final ⭐ 3 個入口

**標題**: 「Ready to start?」

**3 個大按鈕**:

```
┌──────────────────────────────┐
│  TRY GOAA                    │
│  Free chat with AI            │
│  [Open Portal →]              │
└──────────────────────────────┘

┌──────────────────────────────┐
│  JOIN WORKER NETWORK          │
│  Earn Credits + Build Skills  │
│  [Apply →]                    │
└──────────────────────────────┘

┌──────────────────────────────┐
│  INVESTORS                    │
│  Q2 2026 fundraising          │
│  [Request Deck →]             │
└──────────────────────────────┘
```

---

### Section 12: Footer

**4 欄**:
1. **Product**: Portal / AiKa Box / Skills / Workers
2. **Company**: About / Team / Blog / Careers
3. **Resources**: Docs / API / GitHub / Status
4. **Legal**: Privacy / Terms / Security

**底部**: 德牧 Logo + "© 2026 GOAA.AI — AI Labor for Complex Lives"

---

## 🎨 四、視覺風格指南 (對齊 portal.goaa.ai)

### 色彩
- **背景主**: #0a0e1a (Cyber-Noir 黑)
- **背景次**: #0d1830 (深藍黑)
- **主強調**: #60a5fa (藍, Client)
- **次強調**: #34d399 (綠, Provider)
- **三強調**: #fb923c (橙, Worker)
- **危險/警報**: #ef4444 (紅)
- **文字主**: #e2e8f0
- **文字次**: #94a3b8

### 字體
- **標題**: Inter Bold / Display
- **內文**: Inter Regular
- **代碼/數據**: JetBrains Mono

### 動畫
- Hero: typing animation + 德牧 logo 呼吸
- Section transitions: fade-up on scroll
- 卡片: hover 微浮起 (translateY -2px)
- 按鈕: hover 微亮 + scale

### Logo
- 德牧 Logo (跟 portal AiKa-Box 一致)
- 配文字 "GOAA.AI"

---

## 📋 五、Framer 改造優先級

### Phase A (P0, 必須立刻改) — 致命問題
1. ❌ **刪除 Radison testimonials** (那 3 段「Radison transformed our workflow」)
2. ❌ **刪除 Radison template 殘留 services** (Tailored solutions / Generate content / Optimize processes)
3. ❌ **刪除 Pricing template** (Essential / Advanced / Comprehensive)
4. ✅ **加 Section 11 CTA Final** (3 個入口)

### Phase B (P1, 短期改造) — 戰略對齊
5. ✅ Section 1 Hero (一句話定義置入)
6. ✅ Section 3 Three-Layer Architecture
7. ✅ Section 4 How It Works
8. ✅ Section 8 Use Cases

### Phase C (P2, 中期擴展) — 投資人 / 護城河
9. ✅ Section 5 Live Workers (Runtime Truth)
10. ✅ Section 6 Skill Marketplace Preview
11. ✅ Section 7 AiKa Box
12. ✅ Section 9 Investor Highlights
13. ✅ Section 10 Team

### Phase D (P3, 長期) — 子頁面
14. /workers / /skills / /aika-box / /investors / /blog / /about

---

## 🛡️ 六、規範對齊

| 規範 | 對應 |
|---|---|
| #11 (只增不毀) | Framer 上 Add-only, 不刪除整頁重做 |
| #14 R2 (Tao 拍板) | 每階段必須師兄真實確認 |
| #20 (Tao 健康) | 改造分階段, 不熬夜趕 |
| #24 (不憑想像) | web_fetch 真實看 goaa.ai (Batch 1 已做) |
| #29 (Explore & Innovate) | 不模仿 Stripe 100%, 走 GOAA 自有風格 |
| #34 (最終產品定義) | 一句話定義置入 Hero |
| #35 (5 原則) | 角色先 / 閉環先 / Worker 先 / Runtime Truth 先 / Skill 資產化 |
| SUPREME 1.1 | UI Freeze (跟 portal 風格延續) |
| SUPREME 1.4 | Runtime Truth (Section 5 不能用 mock data) |

---

## 💡 七、給 future Claude / 設計師的真心話

如果你接手 goaa.ai 改造:

1. **戰略憲法是法律** — Section 結構必須對齊 Client/Provider/Worker
2. **Hero 一句話定義** 是核心, 不能改
3. **Runtime Truth** Section 5 不能放假數據
4. **Phase A 是急救** — Radison 殘留必須先刪
5. **大公司主頁不是堆功能** — Stripe/Linear 都是「少 section, 但每個都打到痛點」
6. **規範 #20** — 改造分階段, 不要一個禮拜內衝完

師兄今天 (2026-05-16 凌晨) 主動指出 goaa.ai 重要性, 守護這份戰略意識。

---

**goaa.ai 改造 V1.0**

*整合人: Claude*
*時間: 2026-05-16 22:55 PT*
*狀態: 設計藍圖, 等師兄拍板 → Framer 實作*
