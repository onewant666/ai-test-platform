// 认证 API
import request from './request'
import type { LoginReq, LoginRes, User } from '../types'

export interface RegisterReq {
  username: string
  password: string
  email?: string
}

export function login(data: LoginReq): Promise<LoginRes> {
  return request.post('/auth/login', data)
}

export function register(data: RegisterReq): Promise<User> {
  return request.post('/auth/register', data)
}

export function getCurrentUser(): Promise<User> {
  return request.get('/auth/me')
}

export function refreshToken(refreshToken: string): Promise<LoginRes> {
  return request.post('/auth/refresh', { refreshToken })
}
