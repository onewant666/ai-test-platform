import { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, Table, Tag, Space, Typography, Progress } from 'antd'
import {
  FileTextOutlined,
  ScheduleOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  RiseOutlined,
  FallOutlined,
} from '@ant-design/icons'
import ReactEChartsCore from 'echarts-for-react'
import { getTestCases } from '../../services/testcase'
import { getTestPlans, getExecutions } from '../../services/testplan'
import { EXECUTION_STATUS } from '../../config/constants'
import { formatDuration, formatRelative } from '../../utils/format'

const { Title } = Typography

const recentColumns = [
  { title: '计划名称', dataIndex: 'planName', key: 'planName' },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100,
    render: (s: string) => {
      const cfg = EXECUTION_STATUS[s as keyof typeof EXECUTION_STATUS]
      return <Tag color={cfg?.color}>{cfg?.label || s}</Tag>
    },
  },
  {
    title: '通过率',
    dataIndex: 'passRate',
    key: 'passRate',
    width: 100,
    render: (r: number) => {
      if (!r && r !== 0) return '-'
      return <Progress percent={Math.round(r)} size="small" status={r >= 80 ? 'success' : 'exception'} />
    },
  },
  {
    title: '耗时',
    dataIndex: 'duration',
    key: 'duration',
    width: 100,
    render: (d: number) => (d ? formatDuration(d) : '执行中'),
  },
  {
    title: '时间',
    dataIndex: 'time',
    key: 'time',
    width: 160,
    render: (t: string) => formatRelative(t),
  },
]

export default function Dashboard() {
  const [stats, setStats] = useState({ totalCases: 0, totalPlans: 0, todayExecs: 0, avgPassRate: 0 })
  const [recentExecs, setRecentExecs] = useState<Record<string, unknown>[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const [casesRes, plansRes, execsRes] = await Promise.all([
          getTestCases({ limit: 1 }),
          getTestPlans({ limit: 1 }),
          getExecutions({ limit: 10 }),
        ])
        setStats({
          totalCases: casesRes.total || 0,
          totalPlans: plansRes.total || 0,
          todayExecs: execsRes.total || 0,
          avgPassRate: 0, // calculated from execs when available
        })
        setRecentExecs(
          (execsRes.items || []).map((e) => ({
            id: e.id,
            planName: `Execution #${e.id}`,
            status: e.status,
            passRate: e.status === 'passed' ? 100 : e.status === 'failed' ? 0 : null,
            duration: e.duration,
            time: e.createdAt || e.startTime,
          }))
        )
      } catch {
        // Stats failure is non-fatal
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const trendOption = {
    tooltip: { trigger: 'axis' as const },
    grid: { left: 40, right: 40, top: 20, bottom: 30 },
    xAxis: { type: 'category' as const, data: [] },
    yAxis: [
      { type: 'value' as const, name: '%', min: 0, max: 100 },
      { type: 'value' as const, name: '次', min: 0 },
    ],
    series: [
      { name: '通过率', type: 'line', data: [], smooth: true, itemStyle: { color: '#52c41a' } },
      { name: '执行数', type: 'bar', yAxisIndex: 1, data: [], itemStyle: { color: '#1677ff' } },
    ],
  }

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>仪表盘</Title>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {[
          { title: '用例总数', value: stats.totalCases, icon: <FileTextOutlined />, color: '#1677ff' },
          { title: '测试计划', value: stats.totalPlans, icon: <ScheduleOutlined />, color: '#52c41a' },
          { title: '执行记录', value: stats.todayExecs, icon: <ThunderboltOutlined />, color: '#fa8c16' },
          { title: '平均通过率', value: `${stats.avgPassRate}%`, icon: <CheckCircleOutlined />, color: '#722ed1' },
        ].map((card) => (
          <Col xs={24} sm={12} lg={6} key={card.title}>
            <Card hoverable loading={loading}>
              <Statistic
                title={card.title}
                value={card.value}
                prefix={<span style={{ color: card.color }}>{card.icon}</span>}
              />
            </Card>
          </Col>
        ))}
      </Row>

      {/* 趋势图 */}
      <Card title="执行趋势" style={{ marginBottom: 24 }}>
        <ReactEChartsCore option={trendOption} style={{ height: 300 }} />
      </Card>

      {/* 最近执行 */}
      <Card title="最近执行">
        <Table
          dataSource={recentExecs}
          columns={recentColumns}
          rowKey="id"
          pagination={false}
          loading={loading}
          size="middle"
        />
      </Card>
    </div>
  )
}
