// 用例 API
import request from './request'
import type { TestCase, TestCaseFilter, PaginatedReq, PaginatedRes } from '../types'

export function getTestCases(params: PaginatedReq & TestCaseFilter): Promise<PaginatedRes<TestCase>> {
  return request.get('/testcases', { params })
}

export function getTestCase(id: number): Promise<TestCase> {
  return request.get(`/testcases/${id}`)
}

export function createTestCase(data: Partial<TestCase>): Promise<TestCase> {
  return request.post('/testcases', data)
}

export function updateTestCase(id: number, data: Partial<TestCase>): Promise<TestCase> {
  return request.put(`/testcases/${id}`, data)
}

export function deleteTestCase(id: number): Promise<void> {
  return request.delete(`/testcases/${id}`)
}

export function aiGenerateSteps(description: string): Promise<{ steps: TestCase['steps'] }> {
  return request.post('/ai/generate-steps', { description })
}
