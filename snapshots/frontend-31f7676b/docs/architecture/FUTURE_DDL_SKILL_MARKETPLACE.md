# Skill Marketplace DDL 儲備 (V4.2+, 不立即執行)

**版本**: V1.0
**最後更新**: 2026-05-16
**狀態**: ⚠️ **儲備 DDL, 不得立即執行** (規範 #11 + #15)
**配套**: `docs/business/GOAA_BUSINESS_MODEL_V1.md` (戰略憲法主檔 第 8-9 章)

## 📌 文件角色標籤 (規範 SUPREME 治理)

```text
本文角色: V4.2+ 架構儲備 DDL
本文類型: Future DDL Archive
是否允許直接執行: 否 (規範 #11 + #15 嚴守)
是否允許修改 Production: 否 (絕對禁止)
是否需要 Tao 拍板: 是 (執行前必須 Tao + Claude + ChatGPT 三方審查)
最高參考來源: GOAA_BUSINESS_MODEL_V1.md 第 9 章
```

---

## ⚠️ 重要警告 (規範 #11 + #15)

**本文 DDL 是 V4.2+ 架構儲備, 不得立即執行。**

如果未來需要執行 migration, 必須:
1. Tao 明確批准
2. Claude 復核
3. ChatGPT 架構審查
4. Schema snapshot (PG 當前狀態完整備份)
5. Backup (Docker volume + pg_dump)
6. Rollback plan
7. 24h Cooldown (規範 #15)

**禁止直接 ALTER 生產 PG**, 規範 #35 嚴守。

---

## 📊 一、核心表 schema

### 1.1 `skill_marketplace` (技能市場主表)

```sql
CREATE TABLE skill_marketplace (
    skill_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(120) UNIQUE,  -- SUPREME 項 7.1: Marketplace URL slug
    version VARCHAR(20) DEFAULT 'v1.0.0',
    category VARCHAR(50) NOT NULL,  -- Client / Provider / Office / Real Estate / Insurance
    target_user VARCHAR(30) NOT NULL,  -- Client / Provider / Both
    description TEXT,
    status VARCHAR(20) DEFAULT 'draft',
        -- draft / testing / review / published / paused / archived
    visibility VARCHAR(20) DEFAULT 'private',  -- SUPREME 項 7.1: private / public / provider_only / client_only
    
    -- 商業層
    billing_model VARCHAR(20) DEFAULT 'subscription',  -- SUPREME 項 7.1: subscription / one_time / usage_based
    trial_days INTEGER DEFAULT 0,  -- SUPREME 項 7.1: 試用期
    price_monthly DECIMAL(10, 2) DEFAULT 0.00,
    active_subscribers INTEGER DEFAULT 0,
    monthly_revenue DECIMAL(12, 2) DEFAULT 0.00,
    
    -- 分潤
    platform_share DECIMAL(5, 2) DEFAULT 50.00,  -- 平台分成 %
    worker_share DECIMAL(5, 2) DEFAULT 50.00,    -- Worker 分成 %
    
    -- 成本與淨利
    runtime_cost DECIMAL(12, 2) DEFAULT 0.00,
    net_profit DECIMAL(12, 2) GENERATED ALWAYS AS (monthly_revenue - runtime_cost) STORED,
    
    -- 質量指標
    rating FLOAT DEFAULT 5.0,
    feedback_count INTEGER DEFAULT 0,
    
    -- 開發者
    created_by VARCHAR(50) NOT NULL,        -- 開發 Worker ID
    maintained_by VARCHAR(50) NOT NULL,      -- 維護 Worker ID
    
    -- 時間
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    published_at TIMESTAMPTZ
);

CREATE INDEX idx_skill_status ON skill_marketplace(status);
CREATE INDEX idx_skill_target ON skill_marketplace(target_user);
CREATE INDEX idx_skill_category ON skill_marketplace(category);
CREATE INDEX idx_skill_visibility ON skill_marketplace(visibility);
CREATE INDEX idx_skill_slug ON skill_marketplace(slug);
```

### 1.2 `skill_subscriptions` (訂閱流水帳)

```sql
CREATE TABLE skill_subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 訂閱者 (二選一)
    client_id UUID REFERENCES clients(client_id),
    provider_id UUID REFERENCES providers(provider_id),
    
    -- Skill
    skill_id UUID NOT NULL REFERENCES skill_marketplace(skill_id),
    
    -- 狀態
    status VARCHAR(20) DEFAULT 'active',
        -- active / paused / cancelled / expired / trial
    
    -- 計費
    billing_cycle VARCHAR(20) DEFAULT 'monthly',  -- monthly / annual
    next_billing_at TIMESTAMPTZ,
    
    -- 時間
    activated_at TIMESTAMPTZ DEFAULT NOW(),
    terminated_at TIMESTAMPTZ,
    
    CONSTRAINT chk_subscriber CHECK (
        (client_id IS NOT NULL AND provider_id IS NULL) OR
        (client_id IS NULL AND provider_id IS NOT NULL)
    )
);

CREATE INDEX idx_subscription_client ON skill_subscriptions(client_id);
CREATE INDEX idx_subscription_provider ON skill_subscriptions(provider_id);
CREATE INDEX idx_subscription_skill ON skill_subscriptions(skill_id);
CREATE INDEX idx_subscription_status ON skill_subscriptions(status);
```

### 1.3 `skill_billing_ledger` (計費流水帳, SUPREME 項 7.2 新增)

> ⚠️ **重要設計原則**: `skill_subscriptions` 是**狀態表**, 不應承擔財務流水
> 所有收益 / 分潤 / 成本 / 淨利必須進入 ledger 表

```sql
CREATE TABLE skill_billing_ledger (
    ledger_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 關聯
    subscription_id UUID REFERENCES skill_subscriptions(subscription_id),
    skill_id UUID REFERENCES skill_marketplace(skill_id),
    
    -- 付款者
    payer_type VARCHAR(20) NOT NULL,  -- 'client' / 'provider'
    payer_id UUID NOT NULL,           -- client_id 或 provider_id
    
    -- 金額
    amount DECIMAL(12, 2) NOT NULL,                     -- 總收費
    platform_share_amount DECIMAL(12, 2) DEFAULT 0.00,  -- 平台分潤金額
    worker_share_amount DECIMAL(12, 2) DEFAULT 0.00,    -- Worker 分潤金額
    runtime_cost DECIMAL(12, 2) DEFAULT 0.00,           -- Runtime 成本
    net_profit DECIMAL(12, 2) DEFAULT 0.00,             -- 淨利潤
    
    -- 期間
    billing_period_start TIMESTAMPTZ,
    billing_period_end TIMESTAMPTZ,
    
    -- 狀態
    status VARCHAR(20) DEFAULT 'pending',
        -- pending / paid / failed / refunded / disputed
    
    -- 時間
    created_at TIMESTAMPTZ DEFAULT NOW(),
    paid_at TIMESTAMPTZ
);

CREATE INDEX idx_ledger_subscription ON skill_billing_ledger(subscription_id);
CREATE INDEX idx_ledger_skill ON skill_billing_ledger(skill_id);
CREATE INDEX idx_ledger_payer ON skill_billing_ledger(payer_type, payer_id);
CREATE INDEX idx_ledger_status ON skill_billing_ledger(status);
CREATE INDEX idx_ledger_period ON skill_billing_ledger(billing_period_start, billing_period_end);
```

### 1.4 `skill_versions` (版本管理 + Rollback)

```sql
CREATE TABLE skill_versions (
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id UUID NOT NULL REFERENCES skill_marketplace(skill_id),
    version VARCHAR(20) NOT NULL,  -- v1.0.0, v1.1.0, v2.0.0
    
    -- 變更
    changelog TEXT,
    breaking_changes BOOLEAN DEFAULT FALSE,
    
    -- 開發
    developed_by_worker VARCHAR(50),
    runtime_cost_change DECIMAL(10, 4),  -- 跟前版差異
    
    -- 質量
    rating_at_release FLOAT,
    rollback_count INTEGER DEFAULT 0,
    
    -- SUPREME 項 7.3 新增字段
    artifact_hash VARCHAR(128),         -- Skill package 可驗證 hash
    runtime_config_hash VARCHAR(128),   -- Runtime 配置可驗證 hash
    rollback_from_version VARCHAR(20),  -- 回滾來源版本
    is_stable BOOLEAN DEFAULT FALSE,    -- 穩定版本標記
    
    -- 時間
    released_at TIMESTAMPTZ DEFAULT NOW(),
    deprecated_at TIMESTAMPTZ,
    
    UNIQUE(skill_id, version)
);

CREATE INDEX idx_version_skill ON skill_versions(skill_id);
CREATE INDEX idx_version_stable ON skill_versions(skill_id, is_stable);
```

### 1.5 `skill_feedback` (用戶反饋 → Worker Task)

```sql
CREATE TABLE skill_feedback (
    feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id UUID NOT NULL REFERENCES skill_marketplace(skill_id),
    
    -- 反饋者
    client_id UUID REFERENCES clients(client_id),
    provider_id UUID REFERENCES providers(provider_id),
    
    -- 內容 (SUPREME 項 7.5: VARCHAR + CHECK, V5.0 後升 ENUM)
    feedback_type VARCHAR(30) NOT NULL CHECK (feedback_type IN (
        'bug', 'ux', 'slow', 'feature_request', 'wrong_output',
        'too_expensive', 'security_issue', 'billing_issue'
    )),
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    content TEXT,
    
    -- 自動派發 (SUPREME 項 7.4 — 8 種完整映射)
    generated_task_id UUID,
    generated_task_type VARCHAR(50),
    
    -- SUPREME 項 7.4 新增字段
    dispatch_plan_id UUID,              -- 關聯到 dispatch plan (FK 等 dispatch_plans 建表後加)
    severity VARCHAR(20) DEFAULT 'P2',  -- P0 緊急 / P1 高 / P2 中 / P3 低
    sla_due_at TIMESTAMPTZ,             -- SLA 截止
    
    status VARCHAR(20) DEFAULT 'open',  -- open / in_progress / resolved / dismissed
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX idx_feedback_skill ON skill_feedback(skill_id);
CREATE INDEX idx_feedback_status ON skill_feedback(status);
CREATE INDEX idx_feedback_severity ON skill_feedback(severity, status);
CREATE INDEX idx_feedback_sla ON skill_feedback(sla_due_at) WHERE status != 'resolved';
```

### Feedback → Worker Task 映射 (SUPREME 項 7.4 — 8 種完整)

| feedback_type | generated_task_type | severity 預設 |
|---|---|---|
| `bug` | `patch_task` | P1 |
| `ux` | `ux_improvement_task` | P2 |
| `slow` | `optimization_task` | P2 |
| `feature_request` | `feature_task` | P3 |
| `wrong_output` | `prompt_fix_task` | P1 |
| `too_expensive` | `cost_optimization_task` | P2 |
| `security_issue` | `security_fix_task` | **P0 緊急** |
| `billing_issue` | `billing_review_task` | P1 |

### feedback_type 類型策略 (SUPREME 項 7.5)

> ⚠️ **暫時不要急著用 ENUM**

V4.2 初期建議: **VARCHAR + CHECK constraint** (上方 schema 已用)

原因:
- ENUM 修改需要 ALTER TYPE, 影響生產
- 新類型增加頻繁時, VARCHAR 更靈活

V5.0 類型穩定後, 再考慮升級為 ENUM。

### 1.5 `dispatch_plans` (任務拆解規劃, V4.2 預留)

```sql
CREATE TABLE dispatch_plans (
    plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 來源
    user_session_id UUID,
    triggered_by_message_id UUID,  -- 用戶哪個訊息觸發
    
    -- 規劃內容
    user_intent TEXT,  -- LLM 理解的意圖
    decomposed_steps JSONB,  -- LLM 拆解的步驟列表
    estimated_total_cost DECIMAL(10, 4),
    estimated_duration_seconds INTEGER,
    
    -- 執行
    status VARCHAR(20) DEFAULT 'planning',
        -- planning / executing / completed / failed / cancelled
    
    -- 時間
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_plan_session ON dispatch_plans(user_session_id);
CREATE INDEX idx_plan_status ON dispatch_plans(status);
```

### 1.6 `worker_events` (Runtime 事件流, V4.2 預留)

```sql
CREATE TABLE worker_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 上下文
    worker_id VARCHAR(50) NOT NULL,
    task_id UUID,
    dispatch_plan_id UUID REFERENCES dispatch_plans(plan_id),
    
    -- 事件
    event_type VARCHAR(50) NOT NULL,
        -- task_received / task_started / step_progress / task_completed / task_failed
        -- heartbeat / capability_update / error
    payload JSONB,
    
    -- 時間
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_event_worker ON worker_events(worker_id);
CREATE INDEX idx_event_task ON worker_events(task_id);
CREATE INDEX idx_event_plan ON worker_events(dispatch_plan_id);
CREATE INDEX idx_event_type ON worker_events(event_type);
CREATE INDEX idx_event_created ON worker_events(created_at DESC);
```

---

## 🌐 二、未來 API 規劃 (不立即接入)

### 2.1 成果市場 Metrics API

```text
GET /api/v1/achievements/metrics
```

返回:
```json
{
  "total_skills": 47,
  "published_skills": 32,
  "review_skills": 8,
  "mrr": 28450.00,
  "arr": 341400.00,
  "worker_share_total": 14225.00,
  "platform_share_total": 14225.00,
  "active_subscribers": 9450,
  "dau": 3200,
  "retention_rate": 0.87
}
```

### 2.2 質量 API

```text
GET /api/v1/achievements/quality
```

返回:
```json
{
  "average_rating": 4.6,
  "rollback_count": 3,
  "pending_bugs": 12,
  "average_response_time_ms": 1850,
  "failed_runs": 0.02,
  "patch_tasks_open": 5,
  "upgrade_tasks_open": 8
}
```

---

## 📋 三、執行檢查清單 (未來 migration 用)

當 Tao 拍板執行 migration 時, 必須:

### 階段 0: 前置確認
- [ ] Tao 明確批准
- [ ] Claude 復核 DDL
- [ ] ChatGPT 架構審查
- [ ] 24h Cooldown 開始計時

### 階段 1: 備份
- [ ] PG schema snapshot: `pg_dump --schema-only > backup_$(date +%Y%m%d).sql`
- [ ] PG data snapshot: `pg_dump --data-only > data_$(date +%Y%m%d).sql`
- [ ] Docker volume backup
- [ ] 確認 backup MD5 + 大小

### 階段 2: 執行 (low-traffic 窗口)
- [ ] CREATE TABLE 順序: skill_marketplace → skill_versions → skill_subscriptions → skill_feedback → dispatch_plans → worker_events
- [ ] 種子資料 (測試用 1-2 個 Skill)
- [ ] 驗證 schema: `\d skill_marketplace` 等

### 階段 3: 驗證
- [ ] INSERT 測試資料 (不影響線上)
- [ ] FK constraint 測試
- [ ] CHECK constraint 測試 (skill_subscriptions 互斥)
- [ ] GENERATED column 計算測試 (net_profit)

### 階段 4: 24h Cooldown 監控
- [ ] 每小時檢查 PG 健康度
- [ ] 檢查既有功能不受影響
- [ ] 24h 後拍板「正式採用」或回滾

---

## 🛡️ 四、規範對齊

| 規範 | 對應本文 |
|---|---|
| #11 (只增不毀) | 新表全部 CREATE, 不 ALTER 既有 |
| #14 R2 | Tao 明確批准才能執行 |
| #15 (24h Cooldown) | migration 後 24h 觀察 |
| #24 (不憑想像) | 執行前 pg_dump 看真實 schema |
| #25 (跨層型別) | UUID / DECIMAL / JSONB / INET 嚴格 |
| #34 (最終產品定義) | Skill 服務人類, 不偏離 |
| #35 (不走偏 5 原則) | 「技能必須資產化」(原則 5) |

---

## 💡 給 future Claude / DBA 的真心話

如果你執行本 DDL:

1. **不要立即執行** — 等師兄拍板, 等戰略憲法 V1.0 真實採用
2. **執行前先 snapshot** — pg_dump 保命
3. **執行順序很重要** — FK constraint 從父表到子表
4. **GENERATED column** (net_profit) — 是 STORED, 改 monthly_revenue/runtime_cost 會自動算
5. **migration 後 24h** — 規範 #15, 別跳過
6. **回滾準備** — DROP TABLE 順序反過來 (子表先 DROP)

---

**Skill Marketplace DDL 儲備 V1.0**

*整合人: Claude*
*時間: 2026-05-16 11:25 AM PT*
*狀態: 儲備, 不執行 (規範 #11 + #15)*
