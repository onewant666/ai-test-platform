import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Descriptions, Tag, Button, Space, Steps, Typography, Divider, Spin, message } from 'antd'
import { EditOutlined, PlayCircleOutlined, ArrowLeftOutlined } from '@ant-design/icons'
import { getTestCase } from '../../services/testcase'
import { CASE_PRIORITY, CASE_STATUS } from '../../config/constants'
import type { TestCase } from '../../types'
import { formatDate } from '../../utils/format'

const { Title, Text } = Typography

export default function TestCaseDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [testCase, setTestCase] = useState<TestCase | null>(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    async function load() {
      if (!id) return
      setLoading(true)
      try {
        const data = await getTestCase(Number(id))
        setTestCase(data)
      } catch {
        message.error('获取用例详情失败')
        setNotFound(true)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />
  if (notFound || !testCase) {
    return (
      <Card>
        <Title level={4}>用例不存在</Title>
        <Button onClick={() => navigate('/testcases')}>返回列表</Button>
      </Card>
    )
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/testcases')}>
          返回列表
        </Button>
      </Space>

      <Card
        title={
          <Space>
            <Title level={4} style={{ margin: 0 }}>{testCase.title}</Title>
            <Tag color={CASE_PRIORITY[testCase.priority]?.color}>
              {CASE_PRIORITY[testCase.priority]?.label}
            </Tag>
            <Tag color={CASE_STATUS[testCase.status]?.color}>
              {CASE_STATUS[testCase.status]?.label}
            </Tag>
          </Space>
        }
        extra={
          <Space>
            <Button icon={<PlayCircleOutlined />}>立即执行</Button>
            <Button type="primary" icon={<EditOutlined />} onClick={() => navigate(`/testcases/${id}/edit`)}>
              编辑
            </Button>
          </Space>
        }
      >
        <Descriptions column={2} bordered size="small" style={{ marginBottom: 24 }}>
          <Descriptions.Item label="ID">{testCase.id}</Descriptions.Item>
          <Descriptions.Item label="模块">{testCase.module || '-'}</Descriptions.Item>
          <Descriptions.Item label="创建人">{testCase.creatorName}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{formatDate(testCase.createdAt)}</Descriptions.Item>
          <Descriptions.Item label="前置条件">{testCase.preconditions || '-'}</Descriptions.Item>
          <Descriptions.Item label="禅道关联">{testCase.zentaoId ? `#${testCase.zentaoId}` : '未关联'}</Descriptions.Item>
          <Descriptions.Item label="标签" span={2}>
            <Space>
              {testCase.tags.map((t) => <Tag key={t}>{t}</Tag>)}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="描述" span={2}>{testCase.description}</Descriptions.Item>
        </Descriptions>

        <Divider orientation="left">测试步骤</Divider>
        <Steps
          direction="vertical"
          current={-1}
          items={testCase.steps.map((step) => ({
            title: (
              <Space>
                <Tag color="blue">{step.action}</Tag>
                <Text strong>{step.target}</Text>
              </Space>
            ),
            description: (
              <div>
                {step.value && <Text type="secondary">输入值: {step.value}</Text>}
                <br />
                <Text type="success">预期: {step.expected}</Text>
              </div>
            ),
          }))}
        />
      </Card>
    </div>
  )
}
