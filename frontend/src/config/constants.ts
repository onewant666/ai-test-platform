// 常量定义

export const CASE_PRIORITY = {
  P0: { label: 'P0-最高', color: 'red' },
  P1: { label: 'P1-高', color: 'orange' },
  P2: { label: 'P2-中', color: 'blue' },
  P3: { label: 'P3-低', color: 'default' },
} as const

export const CASE_STATUS = {
  draft: { label: '草稿', color: 'default' },
  reviewing: { label: '评审中', color: 'processing' },
  approved: { label: '已通过', color: 'success' },
  deprecated: { label: '已废弃', color: 'error' },
} as const

export const EXECUTION_STATUS = {
  pending: { label: '等待中', color: 'default' },
  running: { label: '执行中', color: 'processing' },
  passed: { label: '通过', color: 'success' },
  failed: { label: '失败', color: 'error' },
  skipped: { label: '跳过', color: 'warning' },
  error: { label: '异常', color: 'error' },
} as const

export const PLAN_STATUS = {
  draft: { label: '草稿', color: 'default' },
  ready: { label: '就绪', color: 'processing' },
  running: { label: '执行中', color: 'processing' },
  completed: { label: '已完成', color: 'success' },
  cancelled: { label: '已取消', color: 'error' },
} as const

export const TEST_STEP_ACTIONS = [
  { value: 'navigate', label: '导航' },
  { value: 'click', label: '点击' },
  { value: 'input', label: '输入' },
  { value: 'select', label: '选择' },
  { value: 'hover', label: '悬停' },
  { value: 'scroll', label: '滚动' },
  { value: 'wait', label: '等待' },
  { value: 'assert', label: '断言' },
  { value: 'screenshot', label: '截图' },
  { value: 'ai_action', label: 'AI 智能操作' },
]
