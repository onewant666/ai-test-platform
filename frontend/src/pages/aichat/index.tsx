import { useState, useRef, useEffect } from 'react'
import { Card, Input, Button, Space, Typography, Avatar, Tag, message } from 'antd'
import { SendOutlined, RobotOutlined, UserOutlined } from '@ant-design/icons'
import { aiChat } from '../../services/ai'

const { Title, Text } = Typography

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

const initialMessages: Message[] = [
  {
    id: 1, role: 'assistant',
    content: '你好！我是 AI 测试助手 🤖\n\n我可以帮你：\n- 📝 根据需求描述生成测试用例\n- 🔍 分析网页并生成测试步骤\n- 🐛 根据错误信息分析 Bug 原因\n- 📊 解读测试报告并给出建议\n\n请描述你的测试需求吧！',
    timestamp: '10:00',
  },
]

const suggestions = [
  '帮我生成一个电商登录功能的测试用例',
  '分析这个页面的可测试元素',
  '最近失败率上升的原因是什么',
  '生成 v2.0 版本的回归测试计划',
]

export default function AIChat() {
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend() {
    if (!input.trim()) return
    const userMsg: Message = {
      id: Date.now(),
      role: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    }
    setMessages((prev) => [...prev, userMsg])
    const userInput = input
    setInput('')
    setLoading(true)

    try {
      const res = await aiChat({ message: userInput })
      const aiMsg: Message = {
        id: Date.now() + 1,
        role: 'assistant',
        content: res.reply || 'AI 未返回内容，请稍后重试',
        timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      }
      setMessages((prev) => [...prev, aiMsg])
    } catch {
      message.error('AI 对话失败，请检查 LLM 配置')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Title level={4} style={{ marginBottom: 16 }}>AI 助手</Title>

      <Card
        style={{ marginBottom: 16 }}
        styles={{ body: { padding: 16, height: 500, overflow: 'auto' } }}
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              display: 'flex',
              gap: 12,
              marginBottom: 20,
              flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
            }}
          >
            <Avatar
              icon={msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
              style={{
                backgroundColor: msg.role === 'user' ? '#1677ff' : '#52c41a',
                flexShrink: 0,
              }}
            />
            <div
              style={{
                maxWidth: '75%',
                padding: '10px 16px',
                borderRadius: 12,
                backgroundColor: msg.role === 'user' ? '#e6f4ff' : '#f6ffed',
                border: `1px solid ${msg.role === 'user' ? '#91caff' : '#b7eb8f'}`,
              }}
            >
              <div style={{ whiteSpace: 'pre-wrap', fontSize: 14, lineHeight: 1.7 }}>
                {msg.content}
              </div>
              <div style={{ textAlign: 'right', marginTop: 4 }}>
                <Text type="secondary" style={{ fontSize: 11 }}>{msg.timestamp}</Text>
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', color: '#999', padding: 8 }}>
            <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#52c41a' }} />
            <span>AI 正在思考...</span>
          </div>
        )}

        <div ref={bottomRef} />
      </Card>

      {/* 快捷提示 */}
      <div style={{ marginBottom: 12 }}>
        <Space wrap>
          {suggestions.map((s) => (
            <Tag
              key={s}
              style={{ cursor: 'pointer', padding: '4px 10px' }}
              onClick={() => setInput(s)}
            >
              {s}
            </Tag>
          ))}
        </Space>
      </div>

      {/* 输入区 */}
      <Space.Compact style={{ width: '100%' }}>
        <Input.TextArea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onPressEnter={(e) => { if (!e.shiftKey) { e.preventDefault(); handleSend() } }}
          placeholder="输入测试需求..."
          autoSize={{ minRows: 1, maxRows: 4 }}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSend}
          loading={loading}
          style={{ height: 'auto' }}
        >
          发送
        </Button>
      </Space.Compact>
    </div>
  )
}
