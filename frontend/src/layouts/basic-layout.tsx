import { Layout, theme } from 'antd'
import { Outlet } from 'react-router-dom'
import Sidebar from './sidebar'
import Header from './header'
import { useAppStore } from '../stores/app-store'

const { Content } = Layout

export default function BasicLayout() {
  const siderCollapsed = useAppStore((s) => s.sidebarCollapsed)
  const { token } = theme.useToken()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sidebar />
      <Layout
        style={{
          marginLeft: siderCollapsed ? 80 : 220,
          transition: 'margin-left 0.2s',
        }}
      >
        <Header />
        <Content
          style={{
            margin: 16,
            padding: 24,
            background: token.colorBgContainer,
            borderRadius: token.borderRadiusLG,
            minHeight: 280,
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
