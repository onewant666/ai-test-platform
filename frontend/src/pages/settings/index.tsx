import { useState, useEffect, useCallback } from 'react'
import { Card, Form, Input, Select, InputNumber, Switch, Button, Space, Typography, message, Tabs, Spin } from 'antd'
import { SaveOutlined, RobotOutlined, SettingOutlined, BellOutlined } from '@ant-design/icons'
import {
  getSettings, updateLLMConfig, updateExecutorConfig, updateNotificationConfig,
  type LLMConfig, type ExecutorConfig, type NotificationConfig,
} from '../../services/settings'

const { Title } = Typography

export default function Settings() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<string | null>(null)
  const [llmForm] = Form.useForm()
  const [executorForm] = Form.useForm()
  const [notifForm] = Form.useForm()

  // Watch provider to conditionally show fields
  const selectedProvider = Form.useWatch('provider', llmForm)

  useEffect(() => {
    loadSettings()
  }, [])

  async function loadSettings() {
    setLoading(true)
    try {
      const data = await getSettings()
      if (data.llm) llmForm.setFieldsValue({
        provider: data.llm.provider,
        apiBase: data.llm.apiBase,
        model: data.llm.model,
        temperature: data.llm.temperature,
        maxTokens: data.llm.maxTokens,
        openaiBaseUrl: data.llm.openaiBaseUrl || 'https://api.openai.com/v1',
        anthropicApiKey: data.llm.anthropicApiKeySet ? '••••••••' : '',
        googleApiKey: data.llm.googleApiKeySet ? '••••••••' : '',
        ollamaBaseUrl: data.llm.ollamaBaseUrl || 'http://localhost:11434/v1',
      })
      if (data.executor) executorForm.setFieldsValue({
        browser: data.executor.browser,
        headless: data.executor.headless,
        viewportWidth: data.executor.viewportWidth,
        viewportHeight: data.executor.viewportHeight,
        browserTimeout: data.executor.browserTimeout,
        retryCount: data.executor.retryCount,
        maxConcurrency: data.executor.maxConcurrency,
      })
      if (data.notification) notifForm.setFieldsValue({
        emailEnabled: data.notification.emailEnabled,
        emailRecipients: data.notification.emailRecipients,
        dingtalkEnabled: data.notification.dingtalkEnabled,
        dingtalkWebhook: data.notification.dingtalkWebhook,
        feishuEnabled: data.notification.feishuEnabled,
        feishuWebhook: data.notification.feishuWebhook,
        notifyOnFailure: data.notification.notifyOnFailure,
        notifyOnComplete: data.notification.notifyOnComplete,
      })
    } catch {
      // 使用默认值
    } finally {
      setLoading(false)
    }
  }

  async function handleSaveLLM(values: LLMConfig) {
    setSaving('llm')
    try {
      // 如果 API Key 是掩码值（未修改），则发送空字符串表示不更新
      const payload = { ...values }
      if (payload.anthropicApiKey === '••••••••') {
        payload.anthropicApiKey = ''
      }
      if (payload.googleApiKey === '••••••••') {
        payload.googleApiKey = ''
      }
      await updateLLMConfig(payload)
      message.success('LLM 配置已保存')
    } catch {
      message.error('保存失败')
    } finally {
      setSaving(null)
    }
  }

  async function handleSaveExecutor(values: ExecutorConfig) {
    setSaving('executor')
    try {
      await updateExecutorConfig(values)
      message.success('执行器配置已保存')
    } catch {
      message.error('保存失败')
    } finally {
      setSaving(null)
    }
  }

  async function handleSaveNotification(values: NotificationConfig) {
    setSaving('notif')
    try {
      await updateNotificationConfig(values)
      message.success('通知配置已保存')
    } catch {
      message.error('保存失败')
    } finally {
      setSaving(null)
    }
  }

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>
  }

  const llmTab = (
    <Form form={llmForm} layout="vertical" onFinish={handleSaveLLM} initialValues={{
      provider: 'deepseek',
      model: 'deepseek-chat',
      temperature: 0.7,
      maxTokens: 4096,
    }}>
      <Form.Item name="provider" label="LLM 提供商" rules={[{ required: true }]}>
        <Select options={[
          { value: 'deepseek', label: 'DeepSeek (推荐)' },
          { value: 'openai', label: 'OpenAI' },
          { value: 'ollama', label: 'Ollama (本地)' },
          { value: 'anthropic', label: 'Anthropic Claude' },
          { value: 'gemini', label: 'Google Gemini' },
        ]} />
      </Form.Item>
      <Form.Item name="apiKey" label={selectedProvider === 'ollama' ? 'API Key (可留空)' : 'API Key'}>
        <Input.Password placeholder={
          selectedProvider === 'ollama' ? '本地 Ollama 不需要 API Key' :
          selectedProvider === 'anthropic' ? 'sk-ant-...' :
          selectedProvider === 'gemini' ? 'AIza...' :
          'sk-...（留空不修改）'
        } />
      </Form.Item>
      {/* 通用 OpenAI 兼容供应商的 API Base URL */}
      {(selectedProvider === 'deepseek' || selectedProvider === 'openai' || selectedProvider === 'ollama' || !selectedProvider) && (
        <Form.Item name="apiBase" label="API Base URL">
          <Input placeholder={
            selectedProvider === 'openai' ? 'https://api.openai.com/v1' :
            selectedProvider === 'ollama' ? 'http://localhost:11434/v1' :
            'https://api.deepseek.com'
          } />
        </Form.Item>
      )}
      <Form.Item name="model" label="模型" rules={[{ required: true }]}>
        <Input placeholder={
          selectedProvider === 'anthropic' ? 'claude-sonnet-4-20250514' :
          selectedProvider === 'gemini' ? 'gemini-2.5-flash' :
          selectedProvider === 'ollama' ? 'qwen2.5:7b' :
          'deepseek-chat'
        } />
      </Form.Item>
      <Form.Item name="temperature" label="Temperature">
        <InputNumber min={0} max={2} step={0.1} style={{ width: 200 }} />
      </Form.Item>
      <Form.Item name="maxTokens" label="最大 Token 数">
        <InputNumber min={256} max={128000} step={256} style={{ width: 200 }} />
      </Form.Item>

      {/* ── 供应商专属字段 ── */}
      {selectedProvider === 'openai' && (
        <Form.Item name="openaiBaseUrl" label="OpenAI Base URL">
          <Input placeholder="https://api.openai.com/v1" />
        </Form.Item>
      )}
      {selectedProvider === 'anthropic' && (
        <Form.Item name="anthropicApiKey" label="Anthropic API Key（独立配置）">
          <Input.Password placeholder="sk-ant-...（将覆盖通用 API Key）" />
        </Form.Item>
      )}
      {selectedProvider === 'gemini' && (
        <Form.Item name="googleApiKey" label="Google API Key（独立配置）">
          <Input.Password placeholder="AIza...（将覆盖通用 API Key）" />
        </Form.Item>
      )}
      {selectedProvider === 'ollama' && (
        <Form.Item name="ollamaBaseUrl" label="Ollama 服务地址">
          <Input placeholder="http://localhost:11434/v1" />
        </Form.Item>
      )}
      <Form.Item>
        <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={saving === 'llm'}>保存 LLM 配置</Button>
      </Form.Item>
    </Form>
  )

  const executorTab = (
    <Form form={executorForm} layout="vertical" onFinish={handleSaveExecutor} initialValues={{
      browser: 'chromium',
      headless: true,
      viewportWidth: 1920,
      viewportHeight: 1080,
      browserTimeout: 30,
      retryCount: 2,
      maxConcurrency: 4,
    }}>
      <Form.Item name="browser" label="浏览器引擎">
        <Select options={[
          { value: 'chromium', label: 'Chromium' },
          { value: 'firefox', label: 'Firefox' },
          { value: 'webkit', label: 'WebKit' },
        ]} />
      </Form.Item>
      <Form.Item name="headless" label="无头模式" valuePropName="checked">
        <Switch />
      </Form.Item>
      <Form.Item name="viewportWidth" label="视窗宽度">
        <InputNumber style={{ width: 200 }} min={320} max={3840} />
      </Form.Item>
      <Form.Item name="viewportHeight" label="视窗高度">
        <InputNumber style={{ width: 200 }} min={240} max={2160} />
      </Form.Item>
      <Form.Item name="browserTimeout" label="浏览器超时（秒）">
        <InputNumber style={{ width: 200 }} min={5} max={300} />
      </Form.Item>
      <Form.Item name="retryCount" label="失败重试次数">
        <InputNumber style={{ width: 200 }} min={0} max={10} />
      </Form.Item>
      <Form.Item name="maxConcurrency" label="最大并发数">
        <InputNumber style={{ width: 200 }} min={1} max={20} />
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={saving === 'executor'}>保存执行器配置</Button>
      </Form.Item>
    </Form>
  )

  const notifTab = (
    <Form form={notifForm} layout="vertical" onFinish={handleSaveNotification} initialValues={{
      notifyOnFailure: true,
      notifyOnComplete: true,
      dingtalkEnabled: false,
      feishuEnabled: false,
      emailEnabled: true,
    }}>
      <Form.Item name="emailEnabled" label="邮件通知" valuePropName="checked">
        <Switch />
      </Form.Item>
      <Form.Item name="emailRecipients" label="接收邮箱">
        <Select mode="tags" placeholder="输入邮箱地址后回车" />
      </Form.Item>
      <Form.Item name="dingtalkEnabled" label="钉钉通知" valuePropName="checked">
        <Switch />
      </Form.Item>
      <Form.Item name="dingtalkWebhook" label="钉钉 Webhook">
        <Input placeholder="https://oapi.dingtalk.com/robot/send..." />
      </Form.Item>
      <Form.Item name="feishuEnabled" label="飞书通知" valuePropName="checked">
        <Switch />
      </Form.Item>
      <Form.Item name="feishuWebhook" label="飞书 Webhook">
        <Input placeholder="https://open.feishu.cn/open-apis/bot/..." />
      </Form.Item>
      <Form.Item name="notifyOnFailure" label="失败时通知" valuePropName="checked">
        <Switch />
      </Form.Item>
      <Form.Item name="notifyOnComplete" label="完成时通知" valuePropName="checked">
        <Switch />
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={saving === 'notif'}>保存通知配置</Button>
      </Form.Item>
    </Form>
  )

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>系统设置</Title>
      <Tabs
        defaultActiveKey="llm"
        items={[
          { key: 'llm', label: <span><RobotOutlined /> LLM 配置</span>, children: <Card>{llmTab}</Card> },
          { key: 'executor', label: <span><SettingOutlined /> 执行器配置</span>, children: <Card>{executorTab}</Card> },
          { key: 'notification', label: <span><BellOutlined /> 通知配置</span>, children: <Card>{notifTab}</Card> },
        ]}
      />
    </div>
  )
}
