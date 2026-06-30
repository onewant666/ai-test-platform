import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Table, Button, Space, Tag, Typography, Progress, Tooltip, message } from 'antd'
import { PlusOutlined, PlayCircleOutlined, EyeOutlined, EditOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { getTestPlans } from '../../services/testplan'
import { PLAN_STATUS } from '../../config/constants'
import type { TestPlan } from '../../types'
import { formatDate, formatRelative } from '../../utils/format'

const { Title } = Typography

export default function TestPlanList() {
  const navigate = useNavigate()
  const [data, setData] = useState<TestPlan[]>([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ page: 1, limit: 20, total: 0 })

  const fetchData = useCallback(async (page = 1, limit = 20) => {
    setLoading(true)
    try {
      const res = await getTestPlans({ page, limit })
      setData(res.items || [])
      setPagination({ page: res.page || 1, limit: res.limit || 20, total: res.total || 0 })
    } catch {
      message.error('获取测试计划列表失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  const columns: ColumnsType<TestPlan> = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: '计划名称', dataIndex: 'name', key: 'name', width: 220,
      render: (t: string, r) => <a onClick={() => navigate(`/testplans/${r.id}`)}>{t}</a>,
    },
  {
    title: '状态', dataIndex: 'status', key: 'status', width: 90,
    render: (s: string) => {
      const cfg = PLAN_STATUS[s as keyof typeof PLAN_STATUS]
      return <Tag color={cfg?.color}>{cfg?.label || s}</Tag>
    },
  },
  {
    title: '用例数', dataIndex: 'caseIds', key: 'caseCount', width: 80,
    render: (ids: number[]) => ids?.length ?? 0,
  },
  {
    title: '定时执行', dataIndex: 'cronExpr', key: 'cronExpr', width: 130,
    render: (c: string) => c ? <Tag color="blue">{c}</Tag> : <Tag>手动</Tag>,
  },
  {
    title: '创建人', dataIndex: 'createdBy', key: 'createdBy', width: 90,
  },
  {
    title: '创建时间', dataIndex: 'createdAt', key: 'createdAt', width: 140,
    render: (t: string) => formatDate(t),
  },
  {
    title: '操作', key: 'action', width: 160, fixed: 'right' as const,
    render: (_: unknown, r: TestPlan) => (
      <Space>
        <Tooltip title="查看"><Button type="text" size="small" icon={<EyeOutlined />} onClick={() => navigate(`/testplans/${r.id}`)} /></Tooltip>
        <Tooltip title="编辑"><Button type="text" size="small" icon={<EditOutlined />} /></Tooltip>
        <Tooltip title="执行"><Button type="text" size="small" icon={<PlayCircleOutlined />} onClick={() => navigate(`/testplans/${r.id}/execute`)} /></Tooltip>
      </Space>
    ),
  },
]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>测试计划</Title>
        <Button type="primary" icon={<PlusOutlined />}>新建计划</Button>
      </div>
      <Card>
        <Table
          dataSource={data}
          columns={columns}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1000 }}
          pagination={{
            current: pagination.page,
            pageSize: pagination.limit,
            total: pagination.total,
            showTotal: (t) => `共 ${t} 条`,
            onChange: (page, limit) => fetchData(page, limit),
          }}
        />
      </Card>
    </div>
  )
}
