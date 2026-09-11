'use client'

// Conversation-driven professional handoff card (P4.4B).
// Rendered INSIDE the AI conversation when the AI has gathered enough
// structured information to reasonably understand the customer's need.
//
// Financial boundary (kept strict):
//   $39.90 = GOAA Connection / Matching Fee
//   30 days · one-time · non-renewing
//   NOT a professional service fee, NOT settlement, NOT invoiceable.
// The card never promises unlimited professionals; during the 30-day access
// GOAA can also help connect the customer with other appropriate licensed
// professionals for additional eligible needs.

const FACT_LABEL_EN: Record<string, string> = {
  child_age: 'Child Age', monthly_budget: 'Monthly Budget', current_savings: 'Current Savings',
  college_start_age: 'College Start Age', college_type: 'School Type', location: 'Region',
  risk_preference: 'Risk Preference', target_amount: 'Target Amount', insured_person: 'Insured Person',
  coverage_goal: 'Coverage Goal', age: 'Age', benefit_type: 'Benefit Type',
  existing_coverage: 'Existing Coverage', coverage_amount: 'Coverage Amount', time_horizon: 'Time Horizon',
  health_status: 'Health Status', who: 'Who Needs Help', budget: 'Budget', objective: 'Objective',
  preferences: 'Preferences', family: 'Family Situation', dependents: 'Dependents', goals: 'Goals',
  income: 'Income', region: 'Region', timeline: 'Timeline', financing: 'Financing',
}

const FACT_LABEL_ZH: Record<string, string> = {
  child_age: '孩子年龄', monthly_budget: '每月预算', current_savings: '现有储蓄',
  college_start_age: '开始上大学年龄', college_type: '学校类型', location: '所在地区',
  risk_preference: '风险偏好', target_amount: '目标金额', insured_person: '保障对象',
  coverage_goal: '保障目标', age: '年龄', benefit_type: '保障类型',
  existing_coverage: '已有保障', coverage_amount: '保障额度', time_horizon: '时间跨度',
  health_status: '健康状况', who: '需要帮助的人', budget: '预算', objective: '目标',
  preferences: '偏好', family: '家庭情况', dependents: '赡养人口', goals: '目标',
  income: '收入', region: '所在地区', timeline: '时间安排', financing: '贷款需求',
}

type HandoffProps = {
  lang: 'zh' | 'en'
  facts: Record<string, unknown>
  onConnect: () => void
  onContinue: () => void
}

const COPY = {
  en: {
    label: 'Professional Handoff',
    title: 'Professional Handoff',
    summary: 'Here&apos;s what GOAA understood about your needs:',
    question: 'Would you like me to connect you with a licensed professional who can review actual options and help you move forward?',
    primary: 'Connect with a Licensed Professional · $39.90',
    secondary: 'Continue with AI',
    support: 'GOAA platform connection fee: $39.90 USD · One-time · 30-day access · No automatic renewal. Professional service fees are separate and require your agreement. During your 30-day access, GOAA can also help connect you with other appropriate licensed professionals for additional eligible professional needs. Nothing is charged by this conversation; review and confirm in checkout.',
  },
  zh: {
    label: '专业交接',
    title: '专业交接',
    summary: 'GOAA 已梳理您的需求要点：',
    question: '请问您是否希望我为您连接一位持证专业人士，帮您审阅实际可选方案，并推进下一步？',
    primary: '连接持证专业人士 · $39.90',
    secondary: '继续使用 AI 规划',
    support: 'GOAA 平台一次性连接费 $39.90 美元 · 30 天有效 · 不自动续费。不包含报税等专业办理费用；专业人士的服务费另行说明，并经您确认。有效期内，其他符合条件的专业需求也可以申请匹配。对话不会扣款，请在结账页面核对并确认购买。',
  },
}

export default function ProfessionalHandoffCard({ lang, facts, onConnect, onContinue }: HandoffProps) {
  const c = COPY[lang]
  const labels = lang === 'zh' ? FACT_LABEL_ZH : FACT_LABEL_EN
  const entries = Object.entries(facts).filter(([, v]) => v !== undefined && v !== null && String(v).trim() !== '').slice(0, 6)

  return (
    <div className="handoff-card" role="region" aria-label={c.label}>
      <div className="handoff-card-head">
        <span className="handoff-badge" aria-hidden="true">◆</span>
        <strong>{c.title}</strong>
      </div>
      {entries.length > 0 && (
        <div className="handoff-summary">
          <p>{c.summary}</p>
          <ul>
            {entries.map(([key, value]) => (
              <li key={key}>
                <small>{labels[key] || key}</small>
                <strong>{String(value)}</strong>
              </li>
            ))}
          </ul>
        </div>
      )}
      <p className="handoff-question">{c.question}</p>
      <button type="button" className="handoff-primary" onClick={onConnect}>{c.primary}</button>
      <button type="button" className="handoff-secondary" onClick={onContinue}>{c.secondary}</button>
      <p className="handoff-support">{c.support}</p>
    </div>
  )
}
