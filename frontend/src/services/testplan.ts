// 测试计划 API
import request from './request'
import type { TestPlan, Execution, PaginatedReq, PaginatedRes } from '../types'

export function getTestPlans(params: PaginatedReq): Promise<PaginatedRes<TestPlan>> {
  return request.get('/testplans', { params })
}

export function getTestPlan(id: number): Promise<TestPlan> {
  return request.get(`/testplans/${id}`)
}

export function createTestPlan(data: Partial<TestPlan>): Promise<TestPlan> {
  return request.post('/testplans', data)
}

export function updateTestPlan(id: number, data: Partial<TestPlan>): Promise<TestPlan> {
  return request.put(`/testplans/${id}`, data)
}

export interface RunPlanResult {
  planId: number
  executions: Array<{
    id: number
    planId: number
    caseId: number
    status: string
  }>
}

export function runTestPlan(id: number): Promise<RunPlanResult> {
  return request.post(`/testplans/${id}/run`)
}

export function stopExecution(executionId: number): Promise<void> {
  return request.post(`/executions/${executionId}/stop`)
}

export function getExecutions(params: PaginatedReq & { planId?: number }): Promise<PaginatedRes<Execution>> {
  return request.get('/executions', { params })
}

export function getExecution(id: number): Promise<Execution> {
  return request.get(`/executions/${id}`)
}
