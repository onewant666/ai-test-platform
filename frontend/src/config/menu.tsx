import {
  DashboardOutlined,
  FileTextOutlined,
  ScheduleOutlined,
  BarChartOutlined,
  LinkOutlined,
  RobotOutlined,
  ProjectOutlined,
  SettingOutlined,
} from '@ant-design/icons'

export interface MenuItem {
  key: string
  label: string
  icon?: React.ReactNode
  path?: string
  children?: MenuItem[]
}

export const menuConfig: MenuItem[] = [
  {
    key: 'dashboard',
    label: '仪表盘',
    icon: <DashboardOutlined />,
    path: '/dashboard',
  },
  {
    key: 'testcase',
    label: '用例管理',
    icon: <FileTextOutlined />,
    path: '/testcases',
  },
  {
    key: 'testplan',
    label: '测试计划',
    icon: <ScheduleOutlined />,
    path: '/testplans',
  },
  {
    key: 'report',
    label: '报告中心',
    icon: <BarChartOutlined />,
    path: '/reports',
  },
  {
    key: 'zentao',
    label: '禅道集成',
    icon: <LinkOutlined />,
    path: '/zentao',
  },
  {
    key: 'aichat',
    label: 'AI 助手',
    icon: <RobotOutlined />,
    path: '/ai-chat',
  },
  {
    key: 'project',
    label: '项目管理',
    icon: <ProjectOutlined />,
    path: '/projects',
  },
  {
    key: 'settings',
    label: '系统设置',
    icon: <SettingOutlined />,
    path: '/settings',
  },
]
