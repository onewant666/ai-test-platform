// 系统设置 API 服务
import request from './request'

export interface LLMConfig {
  provider: string
  apiKey?: string
  apiBase: string
  model: string
  temperature: number
  maxTokens: number
  openaiBaseUrl?: string
  anthropicApiKey?: string
  googleApiKey?: string
  ollamaBaseUrl?: string
}

export interface ExecutorConfig {
  browser: string
  headless: boolean
  viewportWidth: number
  viewportHeight: number
  browserTimeout: number
  retryCount: number
  maxConcurrency: number
}

export interface NotificationConfig {
  emailEnabled: boolean
  emailRecipients: string[]
  dingtalkEnabled: boolean
  dingtalkWebhook: string
  feishuEnabled: boolean
  feishuWebhook: string
  notifyOnFailure: boolean
  notifyOnComplete: boolean
}

export interface AllSettings {
  llm: LLMConfig
  executor: ExecutorConfig
  notification: NotificationConfig
}

// 获取所有设置
export function getSettings(): Promise<AllSettings> {
  return request.get('/settings')
}

// 更新 LLM 配置
export function updateLLMConfig(config: LLMConfig): Promise<void> {
  return request.put('/settings/llm', config)
}

// 更新执行器配置
export function updateExecutorConfig(config: ExecutorConfig): Promise<void> {
  return request.put('/settings/executor', config)
}

// 更新通知配置
export function updateNotificationConfig(config: NotificationConfig): Promise<void> {
  return request.put('/settings/notification', config)
}
