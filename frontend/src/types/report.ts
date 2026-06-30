// 报告相关类型

export interface TestReport {
  id: number
  planId: number
  planName: string
  projectName: string
  totalCount: number
  passedCount: number
  failedCount: number
  skippedCount: number
  errorCount: number
  passRate: number    // 0-100
  duration: number    // 总耗时（ms）
  startTime: string
  endTime: string
  caseResults: CaseResult[]
  trendData?: TrendDataPoint[]
}

export interface CaseResult {
  caseId: number
  caseTitle: string
  priority: string
  module: string
  status: 'passed' | 'failed' | 'skipped' | 'error'
  duration: number
  errorMessage?: string
  screenshots: string[]
  steps: ExecutionStepBrief[]
}

export interface ExecutionStepBrief {
  seq: number
  action: string
  target: string
  expected: string
  actual: string
  status: 'passed' | 'failed'
  screenshot?: string
}

export interface TrendDataPoint {
  date: string
  passRate: number
  totalCount: number
  failedCount: number
}
