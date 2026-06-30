// Axios 请求封装
import axios from 'axios'
import type { AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { message } from 'antd'
import { APP_CONFIG } from '../config'
import { storage } from '../utils/storage'

const request = axios.create({
  baseURL: APP_CONFIG.apiBaseUrl,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 — 自动附加 Token
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = storage.get<string>(APP_CONFIG.tokenKey)
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: AxiosError) => Promise.reject(error)
)

// ── 工具函数：snake_case → camelCase ──
function toCamelCase(str: string): string {
  return str.replace(/_([a-z])/g, (_, c) => c.toUpperCase())
}

function transformKeys(obj: unknown): unknown {
  if (Array.isArray(obj)) return obj.map(transformKeys)
  if (obj !== null && typeof obj === 'object') {
    const result: Record<string, unknown> = {}
    for (const [key, value] of Object.entries(obj as Record<string, unknown>)) {
      result[toCamelCase(key)] = transformKeys(value)
    }
    return result
  }
  return obj
}

// 响应拦截器 — 统一解包 + 驼峰转换 + 错误处理
request.interceptors.response.use(
  (response: AxiosResponse) => {
    let data = response.data
    // 如果后端用 APIResponse 包装（{code, message, data}），自动解包
    if (data && typeof data === 'object' && 'code' in data && 'data' in data) {
      data = (data as Record<string, unknown>).data
    }
    // snake_case 转 camelCase
    return transformKeys(data)
  },
  (error: AxiosError<{ message?: string }>) => {
    const status = error.response?.status
    const msg = error.response?.data?.message || error.message

    switch (status) {
      case 401:
        // Token 过期，清除并跳转登录
        storage.remove(APP_CONFIG.tokenKey)
        storage.remove(APP_CONFIG.refreshTokenKey)
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
        message.error('登录已过期，请重新登录')
        break
      case 403:
        message.error('没有权限执行此操作')
        break
      case 404:
        message.error('请求的资源不存在')
        break
      case 500:
        message.error('服务器内部错误')
        break
      default:
        message.error(msg || '网络请求失败')
    }

    return Promise.reject(error)
  }
)

export default request
