# goaa.ai CTA Final + Email Capture V1.0 — 立刻可上線

**版本**: V1.0
**最後更新**: 2026-05-16 23:08 PT
**配套**: `docs/marketing/goaa_ai_homepage_revamp_V1.md` 第 11.11 章
**狀態**: 文案 + 操作教學, 等師兄拍板

---

## 📌 文件角色標籤

```text
本文角色: CTA Final Section 文案 + Google Form 收 email 教學
本文類型: Marketing Copy + Setup Guide
是否允許直接執行: 是 (師兄真實在 Google Forms / Framer 操作)
是否允許修改 Production: 是 (goaa.ai Framer + Google Forms)
是否需要 Tao 拍板: 是 (上線收 email 影響投資人 / 用戶接觸)
最高參考來源: GOAA_BUSINESS_MODEL_V1.md 第 11 章 (最終產品定義 多角色 8 視角)
```

---

## 🎯 為什麼今晚做 CTA + Email Capture

師兄, 急救版主頁刪掉 Radison 殘留後, **必須有個 CTA 收 lead**, 否則:
- 投資人看完不知道怎麼聯繫
- 早期用戶想試但沒入口
- Worker 想加入沒地方申請

**今晚做這個, 明天就有真實 lead 進來**。

---

## 📝 CTA Final Section 文案

### 標題

**主標題**:
```
Ready to start?
你準備好了嗎?
```

### Subtitle (可選)

```
Whether you're navigating life, growing a practice, or building AI workers — 
GOAA has a path for you.

無論你是在規劃人生、發展專業, 還是建構 AI Worker — 
GOAA 為你準備好一條路。
```

### 3 個 CTA 卡片 (橫排)

---

#### CTA 卡片 1: For Clients (用戶)

**Layout**:
```
┌──────────────────────────────────────┐
│  👤  TRY GOAA                          │
│                                       │
│  Free AI chat for complex life        │
│  questions — income, tax, housing,    │
│  family, risk.                        │
│                                       │
│  免費 AI 對話, 為複雜人生提供 答案 —   │
│  收入、稅務、房產、家庭、風險           │
│                                       │
│  [Open Portal →]                      │
└──────────────────────────────────────┘
```

**按鈕連結**: `https://portal.goaa.ai`
**邊框色**: 藍 (#60a5fa)
**圖示**: 👤 (或自定義 SVG)

---

#### CTA 卡片 2: For Workers (AI 數字勞動力)

**Layout**:
```
┌──────────────────────────────────────┐
│  🤖  JOIN WORKER NETWORK              │
│                                       │
│  Build AI Skills. Earn Credits.       │
│  Share platform revenue.              │
│                                       │
│  開發 AI Skill, 賺 Credits             │
│  共享平台分潤                          │
│                                       │
│  [Apply →]                            │
└──────────────────────────────────────┘
```

**按鈕連結**: Google Form (見下方教學)
**邊框色**: 橙 (#fb923c)
**圖示**: 🤖

---

#### CTA 卡片 3: For Investors (投資人)

**Layout**:
```
┌──────────────────────────────────────┐
│  📈  INVESTORS                         │
│                                       │
│  Building the AI Labor OS for         │
│  2030 economy. Q2 2026 round opening. │
│                                       │
│  打造 2030 年 AI 勞動力作業系統        │
│  Q2 2026 募資輪開放中                  │
│                                       │
│  [Request Deck →]                     │
└──────────────────────────────────────┘
```

**按鈕連結**: Google Form (見下方教學, 不同 form)
**邊框色**: 紫 (#a78bfa) 或灰 (#94a3b8)
**圖示**: 📈

---

### 底部小字 (Trust signal)

```
Built in public · Open governance · No VC pressure (yet)
公開建設 · 透明治理 · 暫無 VC 壓力
```

⚠️ **規範 SUPREME 1.4 Runtime Truth**: 「Q2 2026 round opening」如果還沒實際開, 改成「Building Phase 4 — Pre-seed inquiries welcome」更誠實。

---

## 📋 Google Form 收 email 完整教學

### 為什麼用 Google Form (不是 Mailchimp / ConvertKit)

| 工具 | 優點 | 缺點 | 適合 |
|---|---|---|---|
| **Google Form** ✅ | 免費 / 5 分鐘設定 / 直接寫入 Sheets | 樣式醜 (但內嵌可改) | **急救階段** |
| Mailchimp | 漂亮 / 有 newsletter | 需要設定 audience / SPF / 200 contact 才 worth | 中期 |
| ConvertKit | 創作者最愛 / API 好 | $9/月起 | 中期 |
| Typeform | 體驗最好 | $25/月起 | 後期 |

**今晚用 Google Form**, 後期再升級。

---

### Step 1: 建 Google Form (Worker Application)

#### 1.1 進 Google Forms
- 打開 [forms.google.com](https://forms.google.com)
- 用師兄 Google 帳號登入
- 點 **「+ Blank」** 建新 form

#### 1.2 設定 Form 標題 + 描述

**Title**:
```
GOAA Worker Network Application
```

**Description**:
```
Help us build the AI Labor Economy.

GOAA Worker Network is the production line for AI Skills that serve 
real users — Clients with complex lives and Providers running practices.

If you're a developer, AI engineer, or technical builder interested in 
creating Skills and sharing revenue, fill in below. We'll be in touch.

— Tao @ GOAA
```

#### 1.3 加問題 (建議 6 題)

**Q1**: Your name (Short answer, Required)

**Q2**: Email (Short answer, Required, 加 validation: Email)

**Q3**: Your background (Multiple choice):
- Software engineer
- AI / ML engineer
- Data scientist
- Designer
- Product manager
- Other (please specify)

**Q4**: What kind of Skill would you build? (Paragraph)
- 提示: e.g. Family mail manager / Tax document AI / Property valuation

**Q5**: GitHub / portfolio / LinkedIn URL (Short answer, Optional)

**Q6**: Timezone (Short answer, Optional)
- 提示: e.g. America/Los_Angeles, Asia/Taipei

#### 1.4 設定 Responses 寫入 Google Sheet

1. 點上方 **「Responses」**
2. 點 Google Sheets 圖示
3. 選「Create a new spreadsheet」
4. 命名: `GOAA Worker Applications`
5. 點 Create

→ **每個 submission 自動寫入 Sheet, 師兄可即時查**

#### 1.5 拿 Form 公開連結

1. 點右上 **「Send」**
2. 切換到 🔗 圖示 (link)
3. 勾選「Shorten URL」
4. Copy 短連結 (例: `https://forms.gle/AbCdEfGhI`)

→ **這個 URL 就是 CTA 卡片 2 的按鈕連結**

---

### Step 2: 建第二個 Google Form (Investor Inquiry)

重複 Step 1, 但:

**Title**: `GOAA Investor Inquiry`

**Description**:
```
GOAA.AI is building the AI Labor Operating System for complex global lives.

We're sharing early access to our investor materials with aligned investors 
who care about:
- AI infrastructure (not chatbots)
- Real labor economy (not subscription SaaS)
- Long-term technical moats

Drop your details and we'll share the deck within 48 hours.

— Tao @ GOAA
```

**Questions**:
- Q1: Name (Short, Required)
- Q2: Email (Short, Required, Email validation)
- Q3: Firm / Fund (Short, Required)
- Q4: Investment focus (Multiple choice):
  - Pre-seed / Seed
  - Series A
  - Strategic / Corporate
  - Angel
  - Other
- Q5: Check size range (Multiple choice):
  - $25K - $100K
  - $100K - $500K
  - $500K - $2M
  - $2M+
- Q6: Why GOAA? (Paragraph, Optional)
- Q7: LinkedIn URL (Short, Optional)

**Sheet 名**: `GOAA Investor Inquiries`

**這個 URL 是 CTA 卡片 3 的按鈕連結**

---

### Step 3: 在 Framer 設定 CTA 按鈕

#### 3.1 找 CTA Section (或新建)

如果 Phase A 已刪 Radison 殘留, 主頁可能太短, 加 CTA Final section:

1. Framer 編輯模式
2. 在 Hero 下方 (或主頁最底部, 在 Footer 之前) 新增 section
3. **Section 設定**:
   - 背景: 漸層 `#0a0e1a → #0d1830`
   - 高度: 600-800px
   - Padding: 80px 上下

#### 3.2 加 Section 標題

1. 加 Heading element
2. 內容: `Ready to start?`
3. 字體: 大 (48-60px), 粗 (Inter Bold)
4. 顏色: 純白 `#ffffff`
5. 對齊: 中央

加第二行中文標題:
1. 內容: `你準備好了嗎?`
2. 字體: 中 (32-40px)
3. 顏色: 灰 `#94a3b8`

#### 3.3 加 3 個 CTA 卡片 (橫排, 響應式)

1. 用 Framer **Grid** 或 **Flex** 容器
2. 3 欄, gap: 24px, 在手機改成 1 欄 (responsive)
3. 每個卡片:
   - 背景: 半透明黑 `rgba(255,255,255,0.03)` + 邊框
   - 邊框: 1px solid, 顏色按卡片區分 (藍 / 橙 / 紫)
   - 圓角: 12px
   - Padding: 32px
   - hover: 邊框變亮 + 微浮起 (translateY -4px)

#### 3.4 卡片內容 (按上方文案複製)

**卡片 1** (藍):
- 圖示: 👤
- 標題: TRY GOAA
- 副標題 EN: "Free AI chat for complex life questions..."
- 副標題 CN: "免費 AI 對話, 為複雜人生提供答案..."
- 按鈕: `[Open Portal →]` → `https://portal.goaa.ai`

**卡片 2** (橙):
- 圖示: 🤖
- 標題: JOIN WORKER NETWORK
- 副標題: 按上方文案
- 按鈕: `[Apply →]` → Step 1 Google Form URL

**卡片 3** (紫):
- 圖示: 📈
- 標題: INVESTORS
- 副標題: 按上方文案
- 按鈕: `[Request Deck →]` → Step 2 Google Form URL

#### 3.5 加底部 trust signal

1. 在 3 個卡片下方加 text
2. 內容:
   ```
   Built in public · Open governance · No VC pressure (yet)
   公開建設 · 透明治理 · 暫無 VC 壓力
   ```
3. 字體: 小 (12-14px), 灰 (#64748b)
4. 對齊: 中央
5. 上方間距: 48px

---

### Step 4: Publish

1. Framer 右上點 **「Publish」**
2. 等 1-2 分鐘
3. 隱身瀏覽器 visit `https://goaa.ai`
4. 真實確認:
   - [ ] CTA Section 顯示正確
   - [ ] 3 個按鈕都可點
   - [ ] Portal 按鈕跳到 portal.goaa.ai
   - [ ] Worker 按鈕跳到 Google Form 1
   - [ ] Investor 按鈕跳到 Google Form 2
5. **真實測試**: 用師兄朋友的 email 提交一次 Form, 確認 Sheet 真的收到

---

## 📧 Step 5: Email 通知設定 (可選但推薦)

### 為什麼要 email 通知

師兄不會每天打開 Google Sheets, 如果有人 submit, **真實第一時間知道**很重要 (投資人 lead 黃金時間 < 2 小時).

### 設定方式: Google Forms 內建 email 通知

1. 在 Form 編輯模式
2. 點右上 **3 個點** → **「Get email notifications for new responses」**
3. ✅ 勾選
4. 寄到師兄 Google Apps Script 設定的 email (預設是 form owner)

### 進階: 用 Google Apps Script 寫自動 email (10 min)

```javascript
// Google Apps Script
function onFormSubmit(e) {
  const responses = e.namedValues;
  const name = responses['Your name'] || responses['Name'][0];
  const email = responses['Email'][0];
  const background = responses['Your background']?.[0] || 'N/A';
  
  // 寄 email 通知師兄
  GmailApp.sendEmail(
    'tao@goaa.ai',  // 師兄真實 email
    `🚀 New GOAA Lead: ${name} (${background})`,
    `New submission:\n\nName: ${name}\nEmail: ${email}\nBackground: ${background}\n\nFull data: see Sheet`,
    {
      from: 'aika@goaa.ai',  // 用 GOAA 寄出 (如有 alias)
    }
  );
  
  // 自動回信給申請者
  GmailApp.sendEmail(
    email,
    'Thanks for joining GOAA Worker Network',
    `Hi ${name},\n\nThanks for applying! We'll review and be in touch within 48 hours.\n\n— Tao @ GOAA`
  );
}
```

設定 trigger:
1. Apps Script → 左側 Triggers
2. + Add Trigger
3. Function: `onFormSubmit`
4. Event source: From form
5. Event type: On form submit
6. Save

---

## 🛡️ 規範對齊

| 規範 | 對應 |
|---|---|
| #11 (只增不毀) | 加 CTA Section, 不刪好的內容 |
| #15 (24h Cooldown) | Publish 後等 24h 觀察 |
| #20 (Tao 健康) | 文案教學完整, 師兄按步操作即可 |
| #22 (密碼安全) | Google Form 不需在對話貼密碼 |
| #24 (不憑想像) | 真實設定 + 真實測試 |
| #28 (Silent Failure) | Email 通知失敗有 Apps Script log |
| #34 (最終產品定義) | 3 個 CTA 對應 3 觀眾 (Client/Worker/Investor) |
| SUPREME 1.1 | UI Freeze (新 section 風格延續) |
| SUPREME 1.4 | Runtime Truth (Worker Network 不誇大, 寫「Building」) |

---

## ⏰ 完整時間預估 (師兄真實操作)

| Step | 內容 | 時間 |
|---|---|---|
| 1 | Google Form 1 (Worker) | 5 min |
| 2 | Google Form 2 (Investor) | 5 min |
| 3 | Framer 加 CTA Section | 15 min |
| 4 | Publish + 驗證 | 5 min |
| 5 | Email 通知設定 | 5 min |
| **合計** | | **35 min** |

完成後 GOAA 主頁**可立刻收 lead**。

---

## 💡 給 future Claude / 師兄的真心話

師兄今晚 23:00 PT 主動指出 goaa.ai 是「**第一個入口**」, 不能繼續放 Radison template.

CTA + Google Form 設定後:
- **明天就會收到第一個 lead** (不論是 Worker / Investor / Client)
- 真實 traction 開始累積
- 投資人看到「**有人在 apply**」就是 social proof

這是規範 #29 創新精神 — **誠實展示「Early stage」**, 不假裝大公司, 反而比 Radison template 更可信。

---

**CTA Final + Email Capture V1.0**

*整合人: Claude*
*時間: 2026-05-16 23:10 PT*
*狀態: 文案 + 教學, 等師兄拍板 → Google Form + Framer 設定*
