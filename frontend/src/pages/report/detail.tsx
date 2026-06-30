import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Descriptions, Tag, Button, Space, Typography, Table, Progress, Row, Col, Statistic, Image, Empty, Spin, message } from 'antd'
import { ArrowLeftOutlined, CheckCircleOutlined, CloseCircleOutlined, MinusCircleOutlined } from '@ant-design/icons'
import ReactEChartsCore from 'echarts-for-react'
import { getReport } from '../../services/report'
import type { TestReport } from '../../types'
import { formatDate, formatDuration } from '../../utils/format'

const { Title, Text } = Typography

export default function ReportDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [report, setReport] = useState<TestReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    async function load() {
      if (!id) return
      setLoading(true)
      try {
        const data = await getReport(Number(id))
        setReport(data)
      } catch {
        message.error('获取报告详情失败')
        setNotFound(true)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />
  if (notFound || !report) {
    return (
      <Card>
        <Title level={4}>报告不存在</Title>
        <Button onClick={() => navigate('/reports')}>返回列表</Button>
      </Card>
    )
  }

  const trendOption = {
    tooltip: { trigger: 'axis' as const },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category' as const, data: report.trendData?.map((d) => d.date) || [] },
    yAxis: { type: 'value' as const, min: 0, max: 100 },
    series: [{
      type: 'line',
      data: report.trendData?.map((d) => d.passRate) || [],
      smooth: true,
      itemStyle: { color: '#52c41a' },
      areaStyle: { color: 'rgba(82, 196, 26, 0.1)' },
    }],
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/reports')}>返回列表</Button>
      </Space>

      <Title level={4}>{report.planName} — 测试报告</Title>

      {/* 结果统计 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={4}>
          <Card><Statistic title="总用例" value={report.totalCount} /></Card>
        </Col>
        <Col span={4}>
          <Card><Statistic title="通过" value={report.passedCount} valueStyle={{ color: '#52c41a' }} prefix={<CheckCircleOutlined />} /></Card>
        </Col>
        <Col span={4}>
          <Card><Statistic title="失败" value={report.failedCount} valueStyle={{ color: '#ff4d4f' }} prefix={<CloseCircleOutlined />} /></Card>
        </Col>
        <Col span={4}>
          <Card><Statistic title="跳过" value={report.skippedCount} valueStyle={{ color: '#faad14' }} prefix={<MinusCircleOutlined />} /></Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="通过率" value={report.passRate} suffix="%" valueStyle={{ color: report.passRate >= 80 ? '#52c41a' : '#ff4d4f' }} />
            <Progress percent={Math.round(report.passRate)} size="small" status={report.passRate >= 80 ? 'success' : 'exception'} />
          </Card>
        </Col>
        <Col span={4}>
          <Card><Statistic title="总耗时" value={formatDuration(report.duration)} /></Card>
        </Col>
      </Row>

      <Card style={{ marginBottom: 16 }}>
        <Descriptions column={4} size="small">
          <Descriptions.Item label="项目">{report.projectName}</Descriptions.Item>
          <Descriptions.Item label="开始时间">{formatDate(report.startTime)}</Descriptions.Item>
          <Descriptions.Item label="结束时间">{formatDate(report.endTime)}</Descriptions.Item>
          <Descriptions.Item label="耗时">{formatDuration(report.duration)}</Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 趋势图 */}
      {report.trendData && (
        <Card title="通过率趋势（近 7 天）" style={{ marginBottom: 16 }}>
          <ReactEChartsCore option={trendOption} style={{ height: 250 }} />
        </Card>
      )}

      {/* 用例结果明细 */}
      <Card title="用例结果明细">
        <Table
          dataSource={report.caseResults}
          rowKey="caseId"
          columns={[
            { title: '用例', dataIndex: 'caseTitle', key: 'caseTitle' },
            { title: '优先级', dataIndex: 'priority', key: 'priority', width: 80 },
            { title: '模块', dataIndex: 'module', key: 'module', width: 100 },
            {
              title: '结果', dataIndex: 'status', key: 'status', width: 80,
              render: (s: string) => {
                const map: Record<string, { color: string; label: string }> = {
                  passed: { color: 'success', label: '通过' },
                  failed: { color: 'error', label: '失败' },
                  skipped: { color: 'warning', label: '跳过' },
                  error: { color: 'error', label: '异常' },
                }
                return <Tag color={map[s]?.color}>{map[s]?.label || s}</Tag>
              },
            },
            { title: '耗时', dataIndex: 'duration', key: 'duration', width: 100, render: (d: number) => formatDuration(d) },
            {
              title: '错误信息', dataIndex: 'errorMessage', key: 'errorMessage', width: 200,
              render: (m: string) => m ? <Text type="danger" ellipsis={{ tooltip: m }}>{m}</Text> : '-',
            },
          ]}
          expandable={{
            expandedRowRender: (record) => (
              <div style={{ padding: '8px 48px' }}>
                <Text strong>截图:</Text>
                {record.screenshots.length > 0 ? (
                  <div style={{ marginTop: 8 }}>
                    {record.screenshots.map((s, i) => (
                      <div key={i} style={{ marginBottom: 8 }}>
                        <Text type="secondary">{s}</Text>
                        <div style={{
                          width: 320, height: 200, background: '#f0f0f0',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          borderRadius: 8, border: '1px dashed #d9d9d9',
                        }}>
                          <Empty description="截图预览（开发环境无实际文件）" />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <Text type="secondary">无截图</Text>
                )}
              </div>
            ),
          }}
        />
      </Card>
    </div>
  )
}
