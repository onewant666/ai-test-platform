// 禅道相关类型

export interface ZentaoConfig {
  id: number
  name: string
  baseUrl: string        // 禅道地址
  account: string
  token?: string
  defaultProductId?: number
  defaultProjectId?: number
  autoSyncCases: boolean // 自动同步用例
  autoReportBug: boolean // 失败时自动上报 Bug
  syncInterval: number   // 同步间隔（分钟）
  enabled: boolean
}

export interface ZentaoProduct {
  id: number
  name: string
  code: string
  description: string
}

export interface ZentaoProject {
  id: number
  name: string
  productId?: number
  hasProduct: boolean
}

export interface ZentaoTestCase {
  id: number
  productId: number
  title: string
  steps: string
  lastRunResult?: string
  status: string
}

export interface ZentaoBugReq {
  product: number
  module?: number
  project?: number
  title: string
  severity: 1 | 2 | 3 | 4  // 1-严重 2-较重 3-一般 4-建议
  priority?: 1 | 2 | 3 | 4
  steps: string
  openedBuild?: string
  assignedTo?: string
}

export interface SyncLog {
  id: number
  type: 'cases_import' | 'bug_export' | 'result_writeback'
  direction: 'pull' | 'push'
  status: 'success' | 'failed' | 'partial'
  detail: string
  recordsAffected: number
  createdAt: string
}
