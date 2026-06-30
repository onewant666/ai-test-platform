// 应用全局配置

const env = import.meta.env

export const APP_CONFIG = {
  name: 'AI 智能测试平台',
  version: '0.1.0',
  apiBaseUrl: env.VITE_API_BASE_URL || '/api/v1',
  wsBaseUrl: env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws',
  tokenKey: 'ai_test_token',
  refreshTokenKey: 'ai_test_refresh_token',
  tokenExpireKey: 'ai_test_token_expire',
}

export const PAGINATION = {
  defaultPage: 1,
  defaultLimit: 20,
  pageSizeOptions: [10, 20, 50, 100],
}
