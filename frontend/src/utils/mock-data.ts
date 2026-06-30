// Mock 数据（开发阶段使用，后端就绪后移除）
import type { TestCase, TestPlan, Execution, TestReport, User } from '../types'

export const mockUser: User = {
  id: 1,
  username: 'admin',
  email: 'admin@example.com',
  avatar: '',
  role: 'admin',
  zentaoAccount: 'admin',
  createdAt: '2025-12-01T00:00:00Z',
}

export const mockTestCases: TestCase[] = [
  {
    id: 1, projectId: 1, title: '用户登录功能验证', description: '验证使用正确的用户名和密码可以成功登录系统',
    priority: 'P0', status: 'approved', preconditions: '已有测试账号 admin/123456',
    steps: [
      { seq: 1, action: 'navigate', target: 'https://example.com/login', expected: '页面跳转到登录页' },
      { seq: 2, action: 'input', target: '用户名输入框', value: 'admin', expected: '用户名输入成功' },
      { seq: 3, action: 'input', target: '密码输入框', value: '123456', expected: '密码输入成功' },
      { seq: 4, action: 'click', target: '登录按钮', expected: '系统跳转到首页，显示用户名' },
    ],
    tags: ['smoke', 'login'], module: '用户管理', createdBy: 1, creatorName: 'admin',
    createdAt: '2026-06-01T10:00:00Z', updatedAt: '2026-06-15T14:00:00Z',
    lastRunAt: '2026-06-28T09:00:00Z', lastRunStatus: 'passed',
  },
  {
    id: 2, projectId: 1, title: '登录失败 - 错误密码', description: '使用错误密码登录时应提示错误信息',
    priority: 'P1', status: 'approved', preconditions: '已有测试账号 admin/123456',
    steps: [
      { seq: 1, action: 'navigate', target: 'https://example.com/login', expected: '页面跳转到登录页' },
      { seq: 2, action: 'input', target: '用户名输入框', value: 'admin', expected: '用户名输入成功' },
      { seq: 3, action: 'input', target: '密码输入框', value: 'wrong_password', expected: '密码输入成功' },
      { seq: 4, action: 'click', target: '登录按钮', expected: '显示"用户名或密码错误"提示' },
    ],
    tags: ['login', 'negative'], module: '用户管理', createdBy: 1, creatorName: 'admin',
    createdAt: '2026-06-02T10:00:00Z', updatedAt: '2026-06-10T11:00:00Z',
    lastRunAt: '2026-06-28T09:01:00Z', lastRunStatus: 'passed',
  },
  {
    id: 3, projectId: 1, title: '新增商品到购物车', description: '从商品列表添加商品到购物车并验证数量',
    priority: 'P0', status: 'approved', preconditions: '用户已登录',
    steps: [
      { seq: 1, action: 'navigate', target: 'https://example.com/products', expected: '显示商品列表' },
      { seq: 2, action: 'click', target: '第一个商品的"加入购物车"按钮', expected: '提示添加成功' },
      { seq: 3, action: 'click', target: '顶部购物车图标', expected: '跳转到购物车页面' },
      { seq: 4, action: 'assert', target: '购物车商品数量', value: '1', expected: '购物车中有 1 件商品' },
    ],
    tags: ['smoke', 'cart'], module: '购物车', createdBy: 1, creatorName: 'admin',
    createdAt: '2026-06-03T10:00:00Z', updatedAt: '2026-06-12T09:00:00Z',
    lastRunAt: '2026-06-28T10:00:00Z', lastRunStatus: 'failed',
  },
  {
    id: 4, projectId: 1, title: '搜索功能 - 精确搜索', description: '通过搜索框输入关键词查找商品',
    priority: 'P1', status: 'approved',
    steps: [
      { seq: 1, action: 'navigate', target: 'https://example.com', expected: '显示首页' },
      { seq: 2, action: 'click', target: '搜索框', expected: '搜索框获得焦点' },
      { seq: 3, action: 'input', target: '搜索框', value: 'iPhone 15', expected: '输入成功' },
      { seq: 4, action: 'click', target: '搜索按钮', expected: '显示搜索结果列表' },
      { seq: 5, action: 'assert', target: '搜索结果列表', expected: '至少显示 1 条结果' },
    ],
    tags: ['search'], module: '搜索', createdBy: 1, creatorName: 'admin',
    createdAt: '2026-06-05T10:00:00Z', updatedAt: '2026-06-14T16:00:00Z',
    lastRunAt: '2026-06-27T15:00:00Z', lastRunStatus: 'passed',
  },
  {
    id: 5, projectId: 1, title: '用户注册流程', description: '新用户通过注册表单完成账号注册',
    priority: 'P0', status: 'reviewing', preconditions: '邮箱未被注册',
    steps: [
      { seq: 1, action: 'navigate', target: 'https://example.com/register', expected: '显示注册页面' },
      { seq: 2, action: 'input', target: '邮箱输入框', value: 'test@example.com', expected: '输入成功' },
      { seq: 3, action: 'input', target: '用户名输入框', value: 'newuser', expected: '输入成功' },
      { seq: 4, action: 'input', target: '密码输入框', value: 'Test123456!', expected: '输入成功' },
      { seq: 5, action: 'click', target: '注册按钮', expected: '提示注册成功，跳转登录页' },
    ],
    tags: ['smoke', 'register'], module: '用户管理', createdBy: 1, creatorName: 'admin',
    createdAt: '2026-06-20T10:00:00Z', updatedAt: '2026-06-28T08:00:00Z',
  },
  {
    id: 6, projectId: 1, title: '订单提交 - 完整流程', description: '从购物车到下单的完整流程验证',
    priority: 'P0', status: 'draft', preconditions: '用户已登录且购物车有商品',
    steps: [
      { seq: 1, action: 'navigate', target: 'https://example.com/cart', expected: '显示购物车' },
      { seq: 2, action: 'click', target: '结算按钮', expected: '跳转到订单确认页' },
      { seq: 3, action: 'input', target: '收货地址', value: '北京市朝阳区xx路xx号', expected: '地址输入成功' },
      { seq: 4, action: 'click', target: '提交订单按钮', expected: '跳转到支付页面' },
    ],
    tags: ['smoke', 'order'], module: '订单', createdBy: 1, creatorName: 'admin',
    createdAt: '2026-06-25T10:00:00Z', updatedAt: '2026-06-28T18:00:00Z',
  },
]

export const mockTestPlans: TestPlan[] = [
  {
    id: 1, projectId: 1, name: 'v2.0 冒烟测试', description: '发布前的核心流程冒烟测试',
    caseIds: [1, 3, 5], caseCount: 3, status: 'completed',
    maxRetries: 2, timeout: 600, createdBy: 1, creatorName: 'admin',
    createdAt: '2026-06-20T10:00:00Z', updatedAt: '2026-06-28T09:30:00Z',
    lastRunAt: '2026-06-28T09:00:00Z',
  },
  {
    id: 2, projectId: 1, name: '回归测试 - 每日自动', description: '每日凌晨自动执行的全量回归',
    caseIds: [1, 2, 3, 4, 5], caseCount: 5, status: 'ready',
    cronExpr: '0 2 * * *', maxRetries: 1, timeout: 1200,
    createdBy: 1, creatorName: 'admin',
    createdAt: '2026-06-15T10:00:00Z', updatedAt: '2026-06-28T08:00:00Z',
  },
]

export const mockExecutions: Execution[] = [
  {
    id: 1, planId: 1, planName: 'v2.0 冒烟测试', caseId: 1, caseTitle: '用户登录功能验证',
    status: 'passed', triggerType: 'manual',
    startTime: '2026-06-28T09:00:00Z', endTime: '2026-06-28T09:00:15Z', duration: 15200,
    screenshots: [], log: '步骤1: 导航成功\n步骤2: 用户名输入成功\n步骤3: 密码输入成功\n步骤4: 登录成功',
    steps: [
      { seq: 1, action: '导航到登录页', status: 'passed', timestamp: '2026-06-28T09:00:01Z', duration: 3200 },
      { seq: 2, action: '输入用户名', status: 'passed', timestamp: '2026-06-28T09:00:05Z', duration: 1800 },
      { seq: 3, action: '输入密码', status: 'passed', timestamp: '2026-06-28T09:00:08Z', duration: 1500 },
      { seq: 4, action: '点击登录按钮', status: 'passed', timestamp: '2026-06-28T09:00:12Z', duration: 3500 },
    ],
    retryCount: 0, executedBy: 'manual',
  },
  {
    id: 2, planId: 1, planName: 'v2.0 冒烟测试', caseId: 3, caseTitle: '新增商品到购物车',
    status: 'failed', triggerType: 'manual',
    startTime: '2026-06-28T09:00:20Z', endTime: '2026-06-28T09:00:45Z', duration: 25000,
    errorMessage: '元素 "第一个商品的加入购物车按钮" 未找到 (页面结构可能已变化)',
    screenshots: ['/screenshots/exec_2_step_2_fail.png'],
    log: '步骤1: 导航成功\n步骤2: 失败 - 元素未找到\n尝试 AI 重定位: 失败',
    steps: [
      { seq: 1, action: '导航到商品列表', status: 'passed', timestamp: '2026-06-28T09:00:21Z', duration: 2800 },
      { seq: 2, action: '点击加入购物车', status: 'failed', timestamp: '2026-06-28T09:00:40Z', duration: 18000, errorMessage: '元素未找到' },
    ],
    retryCount: 0, executedBy: 'manual',
  },
  {
    id: 3, planId: 1, planName: 'v2.0 冒烟测试', caseId: 5, caseTitle: '用户注册流程',
    status: 'passed', triggerType: 'manual',
    startTime: '2026-06-28T09:00:50Z', endTime: '2026-06-28T09:01:10Z', duration: 20000,
    screenshots: [], log: '全部步骤执行通过',
    steps: [
      { seq: 1, action: '导航到注册页', status: 'passed', timestamp: '2026-06-28T09:00:51Z', duration: 2000 },
      { seq: 2, action: '输入邮箱', status: 'passed', timestamp: '2026-06-28T09:00:54Z', duration: 1500 },
      { seq: 3, action: '输入用户名', status: 'passed', timestamp: '2026-06-28T09:00:57Z', duration: 1200 },
      { seq: 4, action: '输入密码', status: 'passed', timestamp: '2026-06-28T09:00:59Z', duration: 1300 },
      { seq: 5, action: '点击注册按钮', status: 'passed', timestamp: '2026-06-28T09:01:06Z', duration: 7000 },
    ],
    retryCount: 0, executedBy: 'manual',
  },
]

export const mockReports: TestReport[] = [
  {
    id: 1, planId: 1, planName: 'v2.0 冒烟测试', projectName: '电商平台',
    totalCount: 3, passedCount: 2, failedCount: 1, skippedCount: 0, errorCount: 0,
    passRate: 66.7, duration: 60200,
    startTime: '2026-06-28T09:00:00Z', endTime: '2026-06-28T09:01:10Z',
    caseResults: [
      { caseId: 1, caseTitle: '用户登录功能验证', priority: 'P0', module: '用户管理', status: 'passed', duration: 15200, screenshots: [], steps: [] },
      { caseId: 3, caseTitle: '新增商品到购物车', priority: 'P0', module: '购物车', status: 'failed', duration: 25000, errorMessage: '元素未找到', screenshots: ['/screenshots/fail1.png'], steps: [] },
      { caseId: 5, caseTitle: '用户注册流程', priority: 'P0', module: '用户管理', status: 'passed', duration: 20000, screenshots: [], steps: [] },
    ],
    trendData: [
      { date: '2026-06-22', passRate: 60, totalCount: 5, failedCount: 2 },
      { date: '2026-06-23', passRate: 75, totalCount: 4, failedCount: 1 },
      { date: '2026-06-24', passRate: 80, totalCount: 5, failedCount: 1 },
      { date: '2026-06-25', passRate: 100, totalCount: 3, failedCount: 0 },
      { date: '2026-06-26', passRate: 66.7, totalCount: 3, failedCount: 1 },
      { date: '2026-06-27', passRate: 80, totalCount: 5, failedCount: 1 },
      { date: '2026-06-28', passRate: 66.7, totalCount: 3, failedCount: 1 },
    ],
  },
]

// 仪表盘统计数据
export const mockDashboardStats = {
  totalCases: 156,
  totalPlans: 23,
  todayExecutions: 47,
  avgPassRate: 87.5,
  recentExecutions: [
    { id: 1, planName: 'v2.0 冒烟测试', status: 'completed', passRate: 66.7, duration: 60200, time: '2026-06-28T09:00:00Z' },
    { id: 2, planName: '登录模块回归', status: 'completed', passRate: 100, duration: 35000, time: '2026-06-28T08:00:00Z' },
    { id: 3, planName: '购物车功能测试', status: 'running', passRate: 75, duration: 0, time: '2026-06-28T10:00:00Z' },
    { id: 4, planName: '支付流程验证', status: 'completed', passRate: 80, duration: 120000, time: '2026-06-27T18:00:00Z' },
    { id: 5, planName: '搜索功能测试', status: 'completed', passRate: 100, duration: 28000, time: '2026-06-27T16:00:00Z' },
  ],
  passRateTrend: [
    { date: '06-22', value: 82 },
    { date: '06-23', value: 85 },
    { date: '06-24', value: 79 },
    { date: '06-25', value: 91 },
    { date: '06-26', value: 88 },
    { date: '06-27', value: 93 },
    { date: '06-28', value: 87.5 },
  ],
  executionTrend: [
    { date: '06-22', count: 30 },
    { date: '06-23', count: 45 },
    { date: '06-24', count: 35 },
    { date: '06-25', count: 50 },
    { date: '06-26', count: 42 },
    { date: '06-27', count: 55 },
    { date: '06-28', count: 47 },
  ],
}
