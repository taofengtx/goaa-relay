# goaa.ai Footer + Legal Pages V1.0

**版本**: V1.0
**最後更新**: 2026-05-16 23:13 PT
**配套**: `docs/marketing/goaa_ai_homepage_revamp_V1.md` 第 11.12 章
**狀態**: 文案 + 結構, 等師兄拍板 → Framer 實作

---

## 📌 文件角色標籤

```text
本文角色: Footer Section + 3 個 Legal Pages 草稿
本文類型: Marketing Footer + Legal Templates
是否允許直接執行: 是 (師兄貼到 Framer)
是否允許修改 Production: 是
是否需要 Tao 拍板: 是 (Legal 影響合規)
最高參考來源: GOAA_BUSINESS_MODEL_V1.md (戰略源) + 美國加州法律 (Tao 在 Santa Monica)
```

⚠️ **重要免責**: 本文 Legal Templates **不是法律建議**, 上線前必須**真實律師審查**。

---

## 🎨 Footer 結構

### Layout (4 欄, Desktop)

```
┌────────────────────────────────────────────────────────────────┐
│  [Logo 區]      [Product]         [Company]      [Resources]   │
│  德牧 + GOAA.AI  · Portal          · About        · Docs       │
│  Tagline        · AiKa Box         · Team         · API        │
│  Social icons   · Skills           · Blog         · GitHub     │
│  Email subscribe · Workers         · Careers      · Status     │
│                 · Pricing          · Investors    · Changelog  │
│                                                                │
│  ─────────────────────────────────────────────────────────────│
│                                                                │
│  © 2026 GOAA.AI  |  Privacy | Terms | Security                │
│  Built with ❤️ in Santa Monica · 加州監管 · 全球服務           │
└────────────────────────────────────────────────────────────────┘
```

### 響應式
- Desktop: 4 欄
- Tablet: 2 欄 (上下兩排)
- Mobile: 1 欄 (Accordion 折疊)

---

## 📝 Footer 內容 (4 欄)

### 欄 1: Brand (品牌)

**Logo**: 德牧 + GOAA.AI 文字

**Tagline (中英)**:
```
The AI Labor Platform for Complex Lives
AI 勞動力平台, 為複雜人生而生
```

**Social Icons** (Lucide icons or simple SVG):
- Twitter / X → `https://x.com/goaa_ai` (需師兄申請)
- LinkedIn → `https://linkedin.com/company/goaa-ai` (需師兄申請)
- GitHub → `https://github.com/taofengtx`
- YouTube → (暫無, 可不放)
- Email → `mailto:tao@goaa.ai`

**Email Subscribe (簡單版)**:
```
Get monthly updates on GOAA development:
[Email input] [Subscribe →]
```
連結到 Google Form 或 Mailchimp embed。

---

### 欄 2: Product (產品)

```
Product
─────────
· Portal              → portal.goaa.ai
· AiKa Box            → /aika-box (Coming Soon)
· Skill Marketplace   → /skills (Coming Q3 2026)
· Worker Network      → /workers (Coming Q2 2026)
· Pricing             → /pricing (Coming)
· API                 → /api (Coming Q3 2026)
```

⚠️ **Runtime Truth**: 還沒做的標 "Coming", 不要假連結。

---

### 欄 3: Company (公司)

```
Company
─────────
· About                → /about
· Team                 → /team
· Blog                 → /blog (Coming)
· Careers              → /careers (Coming, hiring soon)
· Investors            → /investors (Private, contact for access)
· Press                → /press (Coming)
· Contact              → mailto:tao@goaa.ai
```

---

### 欄 4: Resources (資源)

```
Resources
─────────
· Documentation        → /docs (Coming Q2 2026)
· API Reference        → /docs/api (Coming Q3 2026)
· GitHub               → github.com/taofengtx
· Status Page          → status.goaa.ai (Coming)
· Changelog            → /changelog (Coming)
· Brand Assets         → /brand
· Help Center          → /help (Coming)
```

---

### 底部 Bar (Bottom Bar)

```
─────────────────────────────────────────────────────────
© 2026 GOAA.AI. All rights reserved.

[Privacy Policy] | [Terms of Service] | [Security] | [Cookie Settings]

Built with ❤️ in Santa Monica, California
加州監管 · 全球服務 · Worker Network across timezones
```

---

## 🎨 Framer 視覺指南

### 色彩
- 背景: 純黑 `#000000` (比主頁 `#0a0e1a` 更深, 區隔)
- 主文字: `#94a3b8` (灰)
- 標題: `#cbd5e1` (淡灰)
- Hover: `#60a5fa` (藍)
- 邊框: `#1e293b`

### 字體
- 標題: Inter Semi-Bold 14px
- 內容: Inter Regular 14px
- 底部 Bar: 12px

### Spacing
- Section padding: 80px 上下
- 欄距: 48px
- 行距: 12px

---

## 📋 3 個 Legal Pages 草稿

⚠️ **再次警告**: 以下是**起草模板**, 上線前必須律師審查。

---

### Page 1: Privacy Policy

```markdown
# Privacy Policy

**Last Updated**: 2026-05-16
**Effective Date**: TBD (after legal review)

## 1. Who We Are

GOAA.AI ("GOAA", "we", "us") is operated by [GOAA.AI LLC / Tao Feng], 
based in Santa Monica, California, USA.

Contact: tao@goaa.ai

## 2. What Data We Collect

### 2.1 Information you provide:
- Name, email (when you sign up or contact us)
- Profile data (when you create Client/Provider/Worker account)
- Content (chat messages, uploaded files, task data)
- Payment data (handled by Stripe, we don't store card numbers)

### 2.2 Information we collect automatically:
- Usage data (which Skills, how often, performance metrics)
- Device data (browser, OS, IP — for security)
- Cookies (essential + optional)

### 2.3 Information from third parties:
- OAuth providers (Google, Apple — if you sign in via them)
- Licensed Provider verification data (e.g., bar admission lookup)

## 3. How We Use Data

- Provide GOAA services
- Connect you with Providers / Workers
- Improve AI models (with consent)
- Send service notifications
- Marketing (with opt-in)
- Legal compliance (US, EU, California)

## 4. Sharing of Data

We share data with:
- Licensed Providers (when you explicitly connect to them)
- Workers in the Network (only task-relevant data, anonymized when possible)
- Service providers (Stripe, AWS, OpenAI, Anthropic — for infrastructure)
- Legal authorities (only when legally required)

**We do NOT sell your data.**

## 5. AI and Machine Learning

GOAA uses AI to:
- Understand your needs
- Match you with Providers / Workers
- Generate executable life paths

You can:
- Opt out of model training on your data
- Request human review of AI decisions
- Delete data used in training (subject to legal retention)

## 6. Your Rights

Depending on your location:
- **California (CCPA)**: Right to know, delete, opt-out of sale, non-discrimination
- **EU (GDPR)**: Right to access, rectify, erase, port, object, restrict
- **All users**: Right to update your data anytime

Email tao@goaa.ai to exercise rights.

## 7. Data Retention

- Active account data: While account is open
- Inactive: 12 months after last login
- Legal retention: 7 years (US tax law)
- Backups: 90 days after deletion

## 8. Security

- TLS encryption in transit
- AES-256 encryption at rest
- Regular security audits
- Bug bounty program (Coming Q3 2026)

## 9. Children

GOAA is not intended for users under 18. If we discover such data, we delete.

## 10. Changes

We'll notify you of material changes via email and in-product banner.

## 11. Contact

Privacy questions: privacy@goaa.ai (or tao@goaa.ai)
```

---

### Page 2: Terms of Service

```markdown
# Terms of Service

**Last Updated**: 2026-05-16
**Effective Date**: TBD (after legal review)

## 1. Acceptance

By using GOAA.AI, you agree to these Terms. If you don't agree, don't use.

## 2. Who Can Use

- 18 years or older
- Legal capacity in your jurisdiction
- Not on US sanctions lists

## 3. Services

### 3.1 What GOAA provides:
- AI-powered life and asset analysis
- Connection to licensed Providers
- AI Worker Network for task execution
- Skill Marketplace for AI capabilities

### 3.2 What GOAA does NOT provide:
- Direct legal, financial, or medical advice (only through Providers)
- Guaranteed outcomes (AI predictions are estimates)
- Insurance or guarantees on Provider performance

## 4. Your Responsibilities

- Provide accurate information
- Don't impersonate others
- Don't reverse-engineer our AI
- Don't use GOAA for illegal purposes
- Pay for services you subscribe to

## 5. Provider Marketplace

When you connect with a Provider:
- Provider is independent (not employee of GOAA)
- GOAA verifies basic credentials but is not liable for service quality
- Provider sets their own fees, terms (within GOAA guidelines)
- Disputes between you and Provider: GOAA may mediate but is not a party

## 6. Worker Network

Workers who join GOAA:
- Are independent contractors / partners
- Earn 50% of Skill revenue (default, may vary)
- Are responsible for their own taxes
- Must follow Worker Conduct guidelines

## 7. Skill Marketplace

When you subscribe to a Skill:
- Monthly auto-renewal unless cancelled
- Cancel anytime (no refund on past months unless Skill is broken)
- Skills may update, be deprecated, or removed
- GOAA refunds if a Skill is fraudulent / breaks promise

## 8. Payment

- Pricing in USD (currency conversion fees not included)
- Payment via Stripe (we don't see your card)
- Auto-renewal subscriptions
- Refunds: case-by-case (contact us)

## 9. Intellectual Property

- GOAA owns the platform, AI models, brand
- You own your content (chat, files)
- Providers / Workers own their Skills (license to GOAA for distribution)
- You grant GOAA license to use your content for service provision

## 10. Limitation of Liability

GOAA is provided "AS IS". To the maximum extent allowed by law:
- We're not liable for indirect damages
- Total liability capped at fees you paid in past 12 months
- AI predictions are estimates, not guarantees

## 11. Termination

We may suspend or terminate accounts for:
- Violation of Terms
- Fraud
- Legal requirement
- Long inactivity (12+ months)

You may delete your account anytime.

## 12. Disputes

- Governing law: California, USA
- Arbitration (JAMS, Santa Monica)
- Class action waiver

## 13. Changes

Material changes require 30-day notice. Continued use = acceptance.

## 14. Contact

Terms questions: legal@goaa.ai (or tao@goaa.ai)
```

---

### Page 3: Security (簡單版)

```markdown
# Security

**Last Updated**: 2026-05-16

## Our Commitment

GOAA.AI handles sensitive life and financial data. We take security seriously.

## How We Protect Your Data

### Encryption
- **In transit**: TLS 1.3
- **At rest**: AES-256
- **Database**: Encrypted column-level for PII

### Infrastructure
- **Cloud**: DigitalOcean (production), Cloudflare (edge)
- **Region**: US-East (primary), with disaster recovery
- **Backups**: Daily, encrypted, 90-day retention

### Access Control
- Tao Feng (Founder) + named team members
- All access logged
- 2FA required for production access
- Quarterly access reviews

### Code Security
- Open governance on GitHub (taofengtx/goaa-ai-frontend)
- Code review for all merges
- Automated dependency scanning
- No production deploys without sign-off

## What You Can Do

- Use strong, unique password (we recommend 1Password)
- Enable 2FA when available
- Don't share account credentials
- Report security issues to: security@goaa.ai (or tao@goaa.ai)

## Bug Bounty (Coming Q3 2026)

We're planning a bug bounty program. Email security@goaa.ai if you find issues now.

## Audits

- **External audit**: Planned Q4 2026 (SOC 2 Type I path)
- **Penetration testing**: Annual
- **Compliance**: California (CCPA), planning EU (GDPR)

## Incident Response

If we have a security breach affecting your data:
1. Detection: Within 24 hours
2. Notification: Within 72 hours (legally required, EU GDPR)
3. Remediation: Public post-mortem within 30 days
```

---

## 🛡️ 規範對齊

| 規範 | 對應 |
|---|---|
| #11 (只增不毀) | Footer + Legal 新加, 不刪其他 |
| #15 (24h Cooldown) | Legal Page Publish 後 24h 觀察 |
| #20 (Tao 健康) | 草案完整, 律師審查可獨立進行 |
| #22 (Privacy) | Privacy Policy 對齊 CCPA + GDPR |
| #24 (不憑想像) | 真實對齊加州 + 國際法規 |
| #28 (Silent Failure) | Security Incident Response 完整 |
| SUPREME 1.1 | Footer 風格延續 Cyber-Noir |
| SUPREME 1.4 | Runtime Truth (Coming Soon 不假裝) |

---

## ⚠️ Legal 上線前 checklist

師兄, Legal pages 上線前**必須**:

- [ ] **真實律師審查** (加州律師 + 國際隱私律師)
- [ ] CCPA 合規驗證
- [ ] GDPR 合規 (如果服務歐盟用戶)
- [ ] 加州 SB 1001 (AI 透明度法)
- [ ] HIPAA (如果服務醫療場景)
- [ ] FINRA (如果服務金融場景)

**律師費**: $2,000-$5,000 一次性 (推薦)

---

## 💡 給 future Claude / 設計師的真心話

如果你接手 Footer + Legal:

1. **Footer 不是垃圾桶** — 大公司 Footer 很重要 (SEO + 信任)
2. **Coming Soon 標誠實** — 沒做的不要做假連結
3. **Legal 必須律師審** — 草案是起點, 不是終點
4. **Privacy Policy 是 trust signal** — 投資人會看
5. **Security 主動展示** — 不要等被問

師兄今天 22:30 PT 強調主頁要做「**大公司一樣**」, Footer + Legal 完整度就是區分早期專案跟大公司的細節。

---

**Footer + Legal V1.0**

*整合人: Claude*
*時間: 2026-05-16 23:13 PT*
*狀態: 草案, 等師兄拍板 → 律師審查 → Framer 實作*
