import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Table, Button, Space, Tag, Typography, Progress, Row, Col, Statistic, message } from 'antd'
import { EyeOutlined, CheckCircleOutlined, CloseCircleOutlined, MinusCircleOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { getReports } from '../../services/report'
import type { TestReport } from '../../types'
import { formatDate, formatDuration, formatPassRate } from '../../utils/format'
import ReactEChartsCore from 'echarts-for-react'

const { Title } = Typography

export default function ReportList() {
  const navigate = useNavigate()
  const [data, setData] = useState<TestReport[]>([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ page: 1, limit: 20, total: 0 })

  const fetchData = useCallback(async (page = 1, limit = 20) => {
    setLoading(true)
    try {
      const res = await getReports({ page, limit })
      setData(res.items || [])
      setPagination({ page: res.page || 1, limit: res.limit || 20, total: res.total || 0 })
    } catch {
      message.error('获取报告列表失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  const columns: ColumnsType<TestReport> = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: '计划名称', dataIndex: 'planName', key: 'planName', width: 200,
      render: (t: string, r: TestReport) => <a onClick={() => navigate(`/reports/${r.id}`)}>{t}</a>,
    },
    { title: '项目', dataIndex: 'projectName', key: 'projectName', width: 120 },
    {
      title: '通过率', dataIndex: 'passRate', key: 'passRate', width: 150,
      render: (r: number) => (
        <Progress
          percent={Math.round(r)}
          size="small"
          status={r >= 80 ? 'success' : r >= 50 ? 'normal' : 'exception'}
        />
      ),
    },
    {
      title: '总计', dataIndex: 'totalCount', key: 'totalCount', width: 60,
    },
    {
      title: '通过/失败/跳过', key: 'summary', width: 160,
      render: (_: unknown, r: TestReport) => (
        <Space>
          <Tag color="success">{r.passedCount}</Tag>
          <Tag color="error">{r.failedCount}</Tag>
          <Tag color="warning">{r.skippedCount}</Tag>
        </Space>
      ),
    },
    {
      title: '耗时', dataIndex: 'duration', key: 'duration', width: 100,
      render: (d: number) => formatDuration(d),
    },
    {
      title: '执行时间', dataIndex: 'startTime', key: 'startTime', width: 160,
      render: (t: string) => formatDate(t),
    },
    {
      title: '操作', key: 'action', width: 80,
      render: (_: unknown, r: TestReport) => (
        <Button type="text" icon={<EyeOutlined />} onClick={() => navigate(`/reports/${r.id}`)}>查看</Button>
      ),
    },
  ]

  // 计算统计数据
  const totalPassed = data.reduce((sum, r) => sum + (r.passedCount || 0), 0)
  const totalFailed = data.reduce((sum, r) => sum + (r.failedCount || 0), 0)
  const avgPassRate = data.length > 0 ? data.reduce((sum, r) => sum + (r.passRate || 0), 0) / data.length : 0

  const trendOption = {
    tooltip: { trigger: 'axis' as const },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category' as const, data: data.map((r) => formatDate(r.startTime)).slice(-7) },
    yAxis: { type: 'value' as const, min: 0, max: 100 },
    series: [{
      type: 'line',
      data: data.map((r) => r.passRate).slice(-7),
      smooth: true,
      itemStyle: { color: '#1677ff' },
      areaStyle: { color: 'rgba(22, 119, 255, 0.1)' },
    }],
  }

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>报告中心</Title>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card><Statistic title="报告总数" value={pagination.total} prefix={<CheckCircleOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="平均通过率" value={avgPassRate.toFixed(1)} suffix="%" valueStyle={{ color: avgPassRate >= 80 ? '#52c41a' : '#ff4d4f' }} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="发现缺陷" value={totalFailed} valueStyle={{ color: '#ff4d4f' }} prefix={<CloseCircleOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="累计通过" value={totalPassed} suffix="个" /></Card>
        </Col>
      </Row>

      <Card title="通过率趋势" style={{ marginBottom: 16 }}>
        <ReactEChartsCore option={trendOption} style={{ height: 250 }} />
      </Card>

      <Card title="报告列表">
        <Table
          dataSource={data}
          columns={columns}
          rowKey="id"
          loading={loading}
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
