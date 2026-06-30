import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Form, Input, Button, Card, Typography, message, Space } from 'antd'
import { UserOutlined, LockOutlined, RobotOutlined } from '@ant-design/icons'
import { useAuthStore } from '../../stores/auth-store'
import { usernameRules, passwordRules } from '../../utils/validators'
import { login, getCurrentUser } from '../../services/auth'

const { Title, Text } = Typography

export default function Login() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { setTokens, setUser } = useAuthStore()

  async function handleSubmit(values: { username: string; password: string }) {
    setLoading(true)
    try {
      const res = await login(values)
      setTokens(res.token, res.refreshToken)

      // 获取当前用户信息
      try {
        const user = await getCurrentUser()
        // 后端角色大写转小写
        setUser({ ...user, role: (user.role as string).toLowerCase() } as typeof user)
      } catch {
        // 用户信息获取失败不影响登录流程
      }

      message.success('登录成功！')
      navigate('/dashboard')
    } catch {
      message.error('用户名或密码错误（试试 admin / 123456）')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Card
        style={{ width: 420, boxShadow: '0 8px 24px rgba(0,0,0,0.15)' }}
        styles={{ body: { padding: '40px 32px' } }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <RobotOutlined style={{ fontSize: 48, color: '#667eea', marginBottom: 8 }} />
          <Title level={3} style={{ margin: 0 }}>
            AI 智能测试平台
          </Title>
          <Text type="secondary">Web 用例自动执行 & 禅道集成</Text>
        </div>

        <Form
          name="login"
          size="large"
          onFinish={handleSubmit}
          autoComplete="off"
          initialValues={{ username: 'admin', password: '123456' }}
        >
          <Form.Item name="username" rules={usernameRules}>
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>

          <Form.Item name="password" rules={passwordRules}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              登 录
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center' }}>
          <Text type="secondary" style={{ fontSize: 13 }}>
            还没有账号？ <a href="/register">立即注册</a>
          </Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>
            测试账号: admin / 123456
          </Text>
        </div>
      </Card>
    </div>
  )
}
