// 测试计划相关类型

export type PlanStatus = 'draft' | 'ready' | 'running' | 'completed' | 'cancelled'
export type ExecutionStatus = 'pending' | 'running' | 'passed' | 'failed' | 'skipped' | 'error'
export type TriggerType = 'manual' | 'cron' | 'zentao_webhook' | 'api'

export interface TestPlan {
  id: number
  projectId: number
  name: string
  description: string
  caseIds: number[]
  caseCount: number
  status: PlanStatus
  cronExpr?: string      // 定时执行 cron 表达式
  maxRetries: number     // 失败重试次数
  timeout: number        // 整体超时（秒）
  createdBy: number
  creatorName?: string
  createdAt: string
  updatedAt: string
  lastRunAt?: string
}

export interface Execution {
  id: number
  planId: number
  planName?: string
  caseId: number
  caseTitle?: string
  status: ExecutionStatus
  triggerType: TriggerType
  startTime?: string
  endTime?: string
  duration?: number      // 执行耗时（ms）
  errorMessage?: string
  screenshots: string[]  // 截图路径
  domSnapshot?: string   // 失败时 DOM 快照
  log: string            // 执行日志
  steps: ExecutionStep[]
  zentaoBugId?: number   // 上报禅道的 Bug ID
  retryCount: number
  executedBy: string     // manual / cron / webhook
}

export interface ExecutionStep {
  seq: number
  action: string
  status: 'passed' | 'failed' | 'skipped'
  screenshot?: string
  errorMessage?: string
  duration?: number
  timestamp: string
}
