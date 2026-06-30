// API 通用类型定义

export interface PaginatedReq {
  page?: number
  limit?: number
  keyword?: string
  orderBy?: string
  order?: 'asc' | 'desc'
}

export interface PaginatedRes<T> {
  items: T[]
  total: number
  page: number
  limit: number
  totalPages: number
}

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface LoginReq {
  username: string
  password: string
}

export interface LoginRes {
  token: string
  refreshToken: string
  expiresIn: number
}

export interface User {
  id: number
  username: string
  email: string
  avatar?: string
  role: 'admin' | 'tester' | 'viewer'
  zentaoAccount?: string
  createdAt: string
}
