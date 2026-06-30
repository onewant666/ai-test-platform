// 用例相关类型定义

export type TestCaseStatus = 'draft' | 'reviewing' | 'approved' | 'deprecated'
export type TestCasePriority = 'P0' | 'P1' | 'P2' | 'P3'
export type TestStepAction = 'navigate' | 'click' | 'input' | 'select' | 'hover' | 'scroll' | 'wait' | 'assert' | 'screenshot' | 'ai_action'

export interface TestStep {
  seq: number
  action: TestStepAction
  target: string        // 目标元素描述（自然语言）或 CSS/XPath
  value?: string        // 输入值
  expected: string      // 预期结果
  timeout?: number      // 超时（ms）
}

export interface TestCase {
  id: number
  projectId: number
  title: string
  description: string
  priority: TestCasePriority
  status: TestCaseStatus
  preconditions?: string
  steps: TestStep[]
  tags: string[]
  module?: string       // 所属模块
  zentaoId?: number     // 关联禅道用例 ID
  zentaoCaseId?: string // 禅道用例编号
  createdBy: number
  creatorName?: string
  createdAt: string
  updatedAt: string
  lastRunAt?: string
  lastRunStatus?: 'passed' | 'failed' | 'skipped'
}

export interface TestCaseFilter {
  projectId?: number
  status?: TestCaseStatus
  priority?: TestCasePriority
  keyword?: string
  tags?: string[]
  module?: string
}
