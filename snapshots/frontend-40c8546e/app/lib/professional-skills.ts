export type SkillField = {
  key: string
  label: string
  required_for_ready: boolean
  ask_priority: number
  type: "text" | "number" | "money" | "enum" | "boolean" | "location"
  options?: string[]
  notes?: string
}

export type ProfessionalSkill = {
  id: string
  version: string
  name: string
  domain: string
  description: string
  fields: SkillField[]
  connection_triggers: string[]
  stop_rules: string[]
  capability_rules: string[]
  readiness: {
    minimum_required_fields: number
    allow_missing_on_connection: boolean
    missing_fields_go_to_agent: boolean
  }
  knowledge_layers: string[]
}

export const LIFE_INSURANCE_SKILL_V1: ProfessionalSkill = {
  id: "life-insurance-v1",
  version: "1.0.0",
  name: "Life Insurance Planning",
  domain: "insurance.life",
  description: "Identifies life insurance needs, collects the minimum required information, and connects a licensed life insurance broker at the right time. AI does not replace formal product advice, illustrations, or underwriting decisions.",
  fields: [
    { key: "insured_person", label: "Insured Person", required_for_ready: true, ask_priority: 1, type: "enum", options: ["自己", "配偶", "孩子", "父母", "其他"] },
    { key: "age", label: "Age", required_for_ready: true, ask_priority: 2, type: "number" },
    { key: "location", label: "State / Region", required_for_ready: false, ask_priority: 8, type: "location", notes: "If the customer already asked to connect, do not block the handoff for a missing state." },
    { key: "coverage_goal", label: "Coverage Goal", required_for_ready: true, ask_priority: 3, type: "enum", options: ["身故保障", "收入替代", "债务/房贷", "教育责任", "父母赡养", "传承", "综合家庭责任"] },
    { key: "budget_amount", label: "Budget Amount", required_for_ready: true, ask_priority: 4, type: "money" },
    { key: "budget_period", label: "Budget Period", required_for_ready: true, ask_priority: 5, type: "enum", options: ["每月", "每年", "一次性"] },
    { key: "currency", label: "Budget Currency", required_for_ready: false, ask_priority: 9, type: "enum", options: ["USD", "CNY", "其他", "unknown"], notes: "Never assume the currency based on language." },
    { key: "responsibility_period", label: "Responsibility Period", required_for_ready: false, ask_priority: 6, type: "text" },
    { key: "target_coverage", label: "Target Coverage", required_for_ready: false, ask_priority: 7, type: "money" },
    { key: "existing_coverage", label: "Existing Coverage", required_for_ready: false, ask_priority: 10, type: "text" },
    { key: "smoking_status", label: "Smoking / Nicotine", required_for_ready: false, ask_priority: 11, type: "enum", options: ["是", "否", "待确认"] },
    { key: "health_status", label: "Important Health Disclosure", required_for_ready: false, ask_priority: 12, type: "text", notes: "AI only does high-level confirmation and does not dig into medical records." },
    { key: "product_preference", label: "Product Preference", required_for_ready: false, ask_priority: 13, type: "text", notes: "Only records preferences the customer volunteers, e.g. IUL / Term / Whole Life." },
  ],
  connection_triggers: [
    "我要买",
    "我要办理",
    "与持证经纪人连接",
    "连接经纪人",
    "找经纪人",
    "找专业人士",
    "帮我处理",
    "我要执行",
  ],
  stop_rules: [
    "known_facts 中已有字段禁止再次询问",
    "进入 CONNECTION_READY 后禁止返回 CLARIFY",
    "客户明确要求真人连接时，缺失字段交由真人继续补充",
    "READY 后 AI 可继续回答用户问题，但不得主动开启新的 Fact Finding 循环",
  ],
  capability_rules: [
    "没有对应 Tool 时禁止承诺生成 PDF、发送、预约、提交或支付",
    "不得承诺具体核保结果",
    "不得把 Agent 偏好描述为客观最佳产品",
    "具体 Carrier 产品建议、Illustration 与核保结论由持证专业人士确认",
  ],
  readiness: {
    minimum_required_fields: 4,
    allow_missing_on_connection: true,
    missing_fields_go_to_agent: true,
  },
  knowledge_layers: [
    "Platform Skill Rules",
    "Platform Knowledge Base",
    "Agent Private Knowledge Base",
    "Agent Preferences",
    "General Model Fallback",
  ],
}

export const PROFESSIONAL_SKILLS: ProfessionalSkill[] = [LIFE_INSURANCE_SKILL_V1]

export function getSkillById(id: string) {
  return PROFESSIONAL_SKILLS.find((skill) => skill.id === id) || null
}

export function getRequiredFieldKeys(skill: ProfessionalSkill) {
  return skill.fields.filter((field) => field.required_for_ready).map((field) => field.key)
}

export function getMissingRequiredFields(skill: ProfessionalSkill, facts: Record<string, unknown>) {
  return getRequiredFieldKeys(skill).filter((key) => facts[key] === undefined || facts[key] === null || facts[key] === "")
}

export function isConnectionTrigger(skill: ProfessionalSkill, text: string) {
  const normalized = text.trim().toLowerCase()
  return skill.connection_triggers.some((trigger) => normalized.includes(trigger.toLowerCase()))
}
