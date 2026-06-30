// 项目管理 API 服务
import request from './request'

export interface ProjectItem {
  id: number
  name: string
  description: string
  status: string
  zentaoProductId?: number
  createdBy: number
  caseCount: number
  planCount: number
  createdAt: string
  updatedAt: string
}

export interface ProjectCreateReq {
  name: string
  description?: string
  status?: string
  zentao_product_id?: number
}

export interface ProjectUpdateReq {
  name?: string
  description?: string
  status?: string
  zentao_product_id?: number
}

// 获取项目列表
export function getProjects(params?: {
  page?: number
  limit?: number
  keyword?: string
}): Promise<{ items: ProjectItem[]; total: number; page: number; limit: number; totalPages: number }> {
  return request.get('/projects', { params })
}

// 获取项目详情
export function getProject(id: number): Promise<ProjectItem> {
  return request.get(`/projects/${id}`)
}

// 创建项目
export function createProject(data: ProjectCreateReq): Promise<ProjectItem> {
  return request.post('/projects', data)
}

// 更新项目
export function updateProject(id: number, data: ProjectUpdateReq): Promise<ProjectItem> {
  return request.put(`/projects/${id}`, data)
}

// 删除项目
export function deleteProject(id: number): Promise<void> {
  return request.delete(`/projects/${id}`)
}
