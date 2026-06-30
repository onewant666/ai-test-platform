import { createBrowserRouter, Navigate } from 'react-router-dom'
import BasicLayout from '../layouts/basic-layout'
import Login from '../pages/login'
import Register from '../pages/register'
import Dashboard from '../pages/dashboard'
import TestCaseList from '../pages/testcase'
import TestCaseDetail from '../pages/testcase/detail'
import TestCaseEditor from '../pages/testcase/editor'
import TestPlanList from '../pages/testplan'
import TestPlanDetail from '../pages/testplan/detail'
import ExecuteMonitor from '../pages/testplan/execute'
import ReportList from '../pages/report'
import ReportDetail from '../pages/report/detail'
import ZentaoConfig from '../pages/zentao'
import ZentaoSync from '../pages/zentao/sync'
import AIChat from '../pages/aichat'
import ProjectList from '../pages/project'
import Settings from '../pages/settings'
import Profile from '../pages/profile'

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/register',
    element: <Register />,
  },
  {
    path: '/',
    element: <BasicLayout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <Dashboard /> },

      // 用例管理
      { path: 'testcases', element: <TestCaseList /> },
      { path: 'testcases/new', element: <TestCaseEditor /> },
      { path: 'testcases/:id', element: <TestCaseDetail /> },
      { path: 'testcases/:id/edit', element: <TestCaseEditor /> },

      // 测试计划
      { path: 'testplans', element: <TestPlanList /> },
      { path: 'testplans/:id', element: <TestPlanDetail /> },
      { path: 'testplans/:id/execute', element: <ExecuteMonitor /> },

      // 报告
      { path: 'reports', element: <ReportList /> },
      { path: 'reports/:id', element: <ReportDetail /> },

      // 禅道
      { path: 'zentao', element: <ZentaoConfig /> },
      { path: 'zentao/sync', element: <ZentaoSync /> },

      // AI 助手
      { path: 'ai-chat', element: <AIChat /> },

      // 项目 & 设置
      { path: 'projects', element: <ProjectList /> },
      { path: 'profile', element: <Profile /> },
      { path: 'settings', element: <Settings /> },
    ],
  },
])
