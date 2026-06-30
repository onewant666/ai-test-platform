import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Descriptions, Tag, Button, Space, Typography, Table, Progress, Spin, message } from 'antd'
import { ArrowLeftOutlined, PlayCircleOutlined } from '@ant-design/icons'
import { getTestPlan, getExecutions } from '../../services/testplan'
import { getTestCases } from '../../services/testcase'
import { PLAN_STATUS, EXECUTION_STATUS } from '../../config/constants'
import { formatDate, formatDuration } from '../../utils/format'
import type { Execution, TestCase } from '../../types'

const { Title } = Typography

const execColumns = [
  {
    title: '用例', dataIndex: 'caseTitle', key: 'caseTitle',
    render: (t: string) => t || '-',
  },
  {
    title: '状态', dataIndex: 'status', key: 'status', width: 100,
    render: (s: string) => {
      const cfg = EXECUTION_STATUS[s as keyof typeof EXECUTION_STATUS]
      return <Tag color={cfg?.color}>{cfg?.label || s}</Tag>
    },
  },
  {
    title: '耗时', dataIndex: 'duration', key: 'duration', width: 100,
    render: (d: number) => d ? formatDuration(d) : '-',
  },
  {
    title: '重试', dataIndex: 'retryCount', key: 'retryCount', width: 60,
  },
  {
    title: '执行时间', dataIndex: 'startTime', key: 'startTime', width: 160,
    render: (t: string) => t ? formatDate(t) : '-',
  },
]

export default function TestPlanDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [plan, setPlan] = useState<TestPlan | null>(null)
  const [executions, setExecutions] = useState<Execution[]>([])
  const [relatedCases, setRelatedCases] = useState<TestCase[]>([])
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    async function load() {
      if (!id) return
      setLoading(true)
      try {
        const planData = await getTestPlan(Number(id))
        setPlan(planData)

        // Fetch executions for this plan
        const execRes = await getExecutions({ planId: Number(id), limit: 100 })
        setExecutions(execRes.items || [])

        // Fetch related test cases
        if (planData.caseIds?.length) {
          const casesRes = await getTestCases({ limit: 100 })
          const matched = (casesRes.items || []).filter((c) =>
            (planData.caseIds as number[]).includes(c.id)
          )
          setRelatedCases(matched)
        }
      } catch {
        message.error('获取计划详情失败')
        setNotFound(true)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />
  if (notFound || !plan) {
    return (
      <Card>
        <Title level={4}>计划不存在</Title>
        <Button onClick={() => navigate('/testplans')}>返回列表</Button>
      </Card>
    )
  }

  const passedCount = executions.filter((e) => e.status === 'passed').length
  const passRate = executions.length > 0 ? Math.round((passedCount / executions.length) * 100) : 0

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/testplans')}>返回</Button>
        <Button type="primary" icon={<PlayCircleOutlined />} onClick={() => navigate(`/testplans/${id}/execute`)}>
          立即执行
        </Button>
      </Space>

      <Card title={<Title level={4} style={{ margin: 0 }}>{plan.name}</Title>} style={{ marginBottom: 16 }}>
        <Descriptions column={3} bordered size="small">
          <Descriptions.Item label="状态">
            <Tag color={PLAN_STATUS[plan.status]?.color}>{PLAN_STATUS[plan.status]?.label}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="关联用例">{plan.caseIds?.length || 0}</Descriptions.Item>
          <Descriptions.Item label="失败重试">{plan.maxRetries} 次</Descriptions.Item>
          <Descriptions.Item label="超时设置">{plan.timeout}s</Descriptions.Item>
          <Descriptions.Item label="定时表达式">{plan.cronExpr || '无'}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{plan.createdAt ? formatDate(plan.createdAt) : '-'}</Descriptions.Item>
          <Descriptions.Item label="上次执行">-</Descriptions.Item>
          <Descriptions.Item label="描述" span={3}>{plan.description || '无'}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title={`关联用例 (${relatedCases.length})`} style={{ marginBottom: 16 }}>
        <Table
          dataSource={relatedCases}
          rowKey="id"
          columns={[
            { title: 'ID', dataIndex: 'id', width: 60 },
            { title: '用例名称', dataIndex: 'title' },
            { title: '优先级', dataIndex: 'priority', width: 80 },
            { title: '模块', dataIndex: 'module', width: 100 },
          ]}
          pagination={false}
          size="small"
        />
      </Card>

      <Card
        title={`执行记录 (${executions.length})`}
        extra={<Progress percent={passRate} size="small" style={{ width: 150 }} status={passRate >= 80 ? 'success' : 'exception'} />}
      >
        <Table
          dataSource={executions}
          columns={execColumns}
          rowKey="id"
          size="small"
          pagination={false}
        />
      </Card>
    </div>
  )
}
