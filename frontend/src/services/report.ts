// 报告 API
import request from './request'
import type { TestReport, PaginatedReq, PaginatedRes } from '../types'

export function getReports(params: PaginatedReq): Promise<PaginatedRes<TestReport>> {
  return request.get('/reports', { params })
}

export function getReport(id: number): Promise<TestReport> {
  return request.get(`/reports/${id}`)
}
