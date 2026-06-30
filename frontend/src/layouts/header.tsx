import { Layout, Button, Dropdown, Space, Badge, theme, Switch } from 'antd'
import {
  BellOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  SunOutlined,
  MoonOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/auth-store'
import { useAppStore } from '../stores/app-store'

const { Header: AntHeader } = Layout

export default function Header() {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const { theme: appTheme, toggleTheme, sidebarCollapsed, toggleSidebar } = useAppStore()
  const { token } = theme.useToken()

  const userMenuItems = {
    items: [
      {
        key: 'profile',
        icon: <UserOutlined />,
        label: '个人中心',
        onClick: () => navigate('/profile'),
      },
      {
        key: 'settings',
        icon: <SettingOutlined />,
        label: '系统设置',
        onClick: () => navigate('/settings'),
      },
      { type: 'divider' as const },
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: '退出登录',
        danger: true,
        onClick: () => {
          logout()
          navigate('/login')
        },
      },
    ],
  }

  return (
    <AntHeader
      style={{
        background: token.colorBgContainer,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
        position: 'sticky',
        top: 0,
        zIndex: 99,
      }}
    >
      <Space>
        <Button
          type="text"
          icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={toggleSidebar}
        />
        <span style={{ fontSize: 16, fontWeight: 500 }}>AI 智能测试平台</span>
      </Space>

      <Space size="middle">
        <Switch
          checkedChildren={<MoonOutlined />}
          unCheckedChildren={<SunOutlined />}
          checked={appTheme === 'dark'}
          onChange={toggleTheme}
        />

        <Badge count={3} size="small">
          <Button type="text" icon={<BellOutlined style={{ fontSize: 18 }} />} />
        </Badge>

        <Dropdown menu={userMenuItems} placement="bottomRight">
          <Space style={{ cursor: 'pointer' }}>
            <Button type="text" icon={<UserOutlined />}>
              {user?.username || '未登录'}
            </Button>
          </Space>
        </Dropdown>
      </Space>
    </AntHeader>
  )
}
