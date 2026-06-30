import { Card, Descriptions, Avatar, Typography, Tag, Space, Divider } from 'antd'
import { UserOutlined, MailOutlined, ClockCircleOutlined, SafetyOutlined } from '@ant-design/icons'
import { useAuthStore } from '../../stores/auth-store'

const { Title } = Typography

export default function Profile() {
  const { user } = useAuthStore()

  const roleColorMap: Record<string, string> = {
    admin: 'red',
    tester: 'blue',
    viewer: 'green',
  }

  return (
    <div style={{ maxWidth: 600 }}>
      <Title level={4} style={{ marginBottom: 24 }}>个人中心</Title>

      <Card>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Avatar size={80} icon={<UserOutlined />} style={{ backgroundColor: '#667eea' }} />
          <Title level={3} style={{ marginTop: 16, marginBottom: 4 }}>
            {user?.username || '未知用户'}
          </Title>
          <Tag color={roleColorMap[user?.role || ''] || 'default'}>
            {user?.role?.toUpperCase() || '-'}
          </Tag>
        </div>

        <Divider />

        <Descriptions column={1} size="middle">
          <Descriptions.Item
            label={<Space><UserOutlined /> 用户名</Space>}
          >
            {user?.username || '-'}
          </Descriptions.Item>
          <Descriptions.Item
            label={<Space><MailOutlined /> 邮箱</Space>}
          >
            {user?.email || '未设置'}
          </Descriptions.Item>
          <Descriptions.Item
            label={<Space><SafetyOutlined /> 角色</Space>}
          >
            <Tag color={roleColorMap[user?.role || '']}>
              {user?.role === 'admin' ? '管理员' :
               user?.role === 'tester' ? '测试工程师' :
               user?.role === 'viewer' ? '观察者' : user?.role}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item
            label={<Space><ClockCircleOutlined /> 注册时间</Space>}
          >
            {user?.createdAt || '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  )
}
