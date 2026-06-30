// AI 助手 API 服务
import request from './request'

export interface ChatReq {
  message: string
  conversation_id?: number
}

export interface ChatRes {
  reply: string
}

export interface GenerateStepsReq {
  description: string
}

export interface TestStep {
  seq: number
  action: string
  target: string
  value?: string
  expected: string
}

export interface GenerateStepsRes {
  steps: TestStep[]
}

export interface AnalyzePageReq {
  url: string
}

export interface AnalyzePageRes {
  analysis: string
}

// AI 对话
export function aiChat(data: ChatReq): Promise<ChatRes> {
  return request.post('/ai/chat', data)
}

// AI 生成测试步骤
export function generateSteps(data: GenerateStepsReq): Promise<GenerateStepsRes> {
  return request.post('/ai/generate-steps', data)
}

// AI 分析页面
export function analyzePage(data: AnalyzePageReq): Promise<AnalyzePageRes> {
  return request.post('/ai/analyze-page', data)
}
