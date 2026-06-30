import { useState } from 'react'
import { Card, Form, Input, InputNumber, Switch, Button, Space, Typography, message, Alert, Descriptions, Tag } from 'antd'
import { LinkOutlined, ApiOutlined } from '@ant-design/icons'
import { testZentaoConnection } from '../../services/zentao'

const { Title } = Typography

export default function ZentaoConfig() {
  const [form] = Form.useForm()
  const [testing, setTesting] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<{ connected: boolean; message: string } | null>(null)

  async function handleTestConnection() {
    try {
      const values = await form.validateFields()
      setTesting(true)
      const result = await testZentaoConnection({
        base_url: values.baseUrl,
        account: values.account,
        password: values.password,
      })
      setConnectionStatus({ connected: true, message: '禅道连接测试成功！' })
      message.success('禅道连接测试成功！')
    } catch (err: unknown) {
      const errMsg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message || '连接测试失败'
      setConnectionStatus({ connected: false, message: errMsg })
      message.error(errMsg)
    } finally {
      setTesting(false)
    }
  }

  function handleSave(values: Record<string, unknown>) {
    // 保存配置到 localStorage（实际项目中应调用后端保存）
    localStorage.setItem('zentao_config', JSON.stringify(values))
    message.success('禅道配置已保存到本地')
  }

  // 尝试从 localStorage 恢复配置
  const savedConfig = (() => {
    try {
      const raw = localStorage.getItem('zentao_config')
      return raw ? JSON.parse(raw) : null
    } catch { return null }
  })()

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>禅道集成配置</Title>

      <Alert
        message="禅道集成说明"
        description="本平台通过禅道 REST API (v1) 进行集成，支持用例同步、Bug 上报和测试结果回写。请确保禅道版本为 16.5 或更高。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        action={
          <Button type="link" href="https://www.zentao.net/book/api/1397.html" target="_blank">
            查看禅道 API 文档 <LinkOutlined />
          </Button>
        }
      />

      <Card title="连接配置">
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          initialValues={savedConfig || {
            baseUrl: 'http://localhost:80',
            account: 'admin',
            autoSyncCases: true,
            autoReportBug: true,
            syncInterval: 30,
            enabled: true,
          }}
        >
          <Form.Item name="name" label="配置名称" rules={[{ required: true }]}>
            <Input placeholder="例如：本地禅道服务器" />
          </Form.Item>

          <Form.Item
            name="baseUrl"
            label="禅道地址"
            rules={[{ required: true, message: '请输入禅道地址' }, { type: 'url', message: '请输入有效 URL' }]}
          >
            <Input placeholder="例如：http://localhost:80" />
          </Form.Item>

          <Form.Item name="account" label="API 账号" rules={[{ required: true }]}>
            <Input placeholder="禅道登录账号" />
          </Form.Item>

          <Form.Item name="password" label="API 密码">
            <Input.Password placeholder="禅道登录密码（用于获取 Token）" />
          </Form.Item>

          <Form.Item name="defaultProductId" label="默认产品 ID">
            <InputNumber style={{ width: 200 }} placeholder="禅道产品 ID" />
          </Form.Item>

          <Form.Item name="syncInterval" label="自动同步间隔（分钟）">
            <InputNumber style={{ width: 200 }} min={5} max={1440} />
          </Form.Item>

          <Form.Item name="autoSyncCases" label="自动同步用例" valuePropName="checked">
            <Switch />
          </Form.Item>

          <Form.Item name="autoReportBug" label="失败时自动上报 Bug" valuePropName="checked">
            <Switch />
          </Form.Item>

          <Form.Item name="enabled" label="启用" valuePropName="checked">
            <Switch />
          </Form.Item>

          <Space>
            <Button type="primary" htmlType="submit">保存配置</Button>
            <Button icon={<ApiOutlined />} onClick={handleTestConnection} loading={testing}>测试连接</Button>
          </Space>
        </Form>
      </Card>

      {/* 连接状态 */}
      {connectionStatus && (
        <Card title="连接状态" style={{ marginTop: 16 }}>
          <Descriptions column={2}>
            <Descriptions.Item label="最近测试结果">
              <Tag color={connectionStatus.connected ? 'success' : 'error'}>
                {connectionStatus.connected ? '连接成功' : '连接失败'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="详情">{connectionStatus.message}</Descriptions.Item>
          </Descriptions>
        </Card>
      )}

      {!connectionStatus && (
        <Card title="连接状态" style={{ marginTop: 16 }}>
          <Descriptions column={1}>
            <Descriptions.Item label="状态">
              <Tag>未测试 — 请先配置并点击"测试连接"</Tag>
            </Descriptions.Item>
          </Descriptions>
        </Card>
      )}
    </div>
  )
}
