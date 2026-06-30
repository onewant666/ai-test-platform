import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Form, Input, Button, Card, Typography, message } from 'antd'
import { UserOutlined, LockOutlined, MailOutlined, RobotOutlined } from '@ant-design/icons'
import { register } from '../../services/auth'
import { usernameRules, passwordRules } from '../../utils/validators'

const { Title, Text } = Typography

export default function Register() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(values: { username: string; password: string; email?: string }) {
    setLoading(true)
    try {
      await register(values)
      message.success('注册成功！请登录')
      navigate('/login')
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      message.error(detail || '注册失败，请重试')
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
            创建账号
          </Title>
          <Text type="secondary">AI 智能测试平台</Text>
        </div>

        <Form
          name="register"
          size="large"
          onFinish={handleSubmit}
          autoComplete="off"
        >
          <Form.Item name="username" rules={usernameRules}>
            <Input prefix={<UserOutlined />} placeholder="用户名（3-64字符）" />
          </Form.Item>

          <Form.Item name="email" rules={[{ type: 'email', message: '请输入有效的邮箱地址' }]}>
            <Input prefix={<MailOutlined />} placeholder="邮箱（可选）" />
          </Form.Item>

          <Form.Item name="password" rules={passwordRules}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码（6-64字符）" />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'))
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="确认密码" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              注 册
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center' }}>
          <Text type="secondary" style={{ fontSize: 13 }}>
            已有账号？ <Link to="/login">返回登录</Link>
          </Text>
        </div>
      </Card>
    </div>
  )
}
