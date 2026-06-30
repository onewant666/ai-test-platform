import { useLocation, useNavigate } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import { menuConfig } from '../config/menu'
import { useAppStore } from '../stores/app-store'
import type { MenuProps } from 'antd'

const { Sider } = Layout

function buildMenuItems(): MenuProps['items'] {
  return menuConfig.map((item) => ({
    key: item.path || item.key,
    icon: item.icon,
    label: item.label,
  }))
}

export default function Sidebar() {
  const location = useLocation()
  const navigate = useNavigate()
  const collapsed = useAppStore((s) => s.sidebarCollapsed)

  const selectedKeys = [location.pathname]
  const openKeys = menuConfig
    .filter((m) => m.children?.some((c) => location.pathname.startsWith(c.path || '')))
    .map((m) => m.key)

  function handleClick(info: { key: string }) {
    navigate(info.key)
  }

  return (
    <Sider
      collapsible
      collapsed={collapsed}
      onCollapse={(v) => useAppStore.setState({ sidebarCollapsed: v })}
      width={220}
      style={{
        overflow: 'auto',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        zIndex: 100,
      }}
    >
      <div
        style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: collapsed ? 16 : 18,
          fontWeight: 700,
          whiteSpace: 'nowrap',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        {collapsed ? '🧠' : '🧠 AI 测试平台'}
      </div>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={selectedKeys}
        defaultOpenKeys={openKeys}
        items={buildMenuItems()}
        onClick={handleClick}
      />
    </Sider>
  )
}
