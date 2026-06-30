// 禅道集成 API 服务
import request from './request'
import type { SyncLog, ZentaoProduct } from '../types'

export interface ZentaoConfigReq {
  base_url: string
  account: string
  password: string
}

export interface SyncCasesReq {
  product_id: number
  project_id: number
}

export interface ReportBugReq {
  execution_id: number
  product_id: number
}

export interface ZentaoConnectionResult {
  connected: boolean
}

export interface SyncResult {
  log_id: number
  status: string
  detail: string
  records_affected: number
}

// 测试禅道连接
export function testZentaoConnection(config: ZentaoConfigReq): Promise<ZentaoConnectionResult> {
  return request.post('/zentao/test-connection', config)
}

// 获取禅道产品列表
export function getZentaoProducts(params: {
  config_base_url: string
  config_account: string
  config_password: string
}): Promise<ZentaoProduct[]> {
  return request.get('/zentao/products', { params })
}

// 同步用例
export function syncZentaoCases(data: SyncCasesReq): Promise<SyncResult> {
  return request.post('/zentao/sync/cases', data)
}

// 上报 Bug
export function reportBugToZentao(data: ReportBugReq): Promise<{ log_id: number; status: string; detail: string }> {
  return request.post('/zentao/report-bug', data)
}

// 回写测试结果
export function writeResultToZentao(execution_id: number): Promise<{ log_id: number; status: string; detail: string }> {
  return request.post('/zentao/write-result', null, { params: { execution_id } })
}

// 获取同步日志列表
export function getSyncLogs(params?: { page?: number; limit?: number }): Promise<{ items: SyncLog[]; total: number; page: number; limit: number; totalPages: number }> {
  return request.get('/zentao/sync-logs', { params })
}
