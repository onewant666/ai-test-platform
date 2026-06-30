import { useState, useEffect, useCallback } from 'react'
import { Card, Button, Space, Typography, Table, Tag, Badge, message, Row, Col, Statistic } from 'antd'
import { SyncOutlined, BugOutlined, FileTextOutlined, CheckCircleOutlined } from '@ant-design/icons'
import type { SyncLog } from '../../types'
import { getSyncLogs, syncZentaoCases, writeResultToZentao } from '../../services/zentao'
import { formatDate } from '../../utils/format'

const { Title } = Typography

const columns = [
  {
    title: '类型', dataIndex: 'type', key: 'type', width: 120,
    render: (t: string) => {
      const map: Record<string, { label: string; color: string }> = {
        cases_import: { label: '用例导入', color: 'blue' },
        bug_export: { label: 'Bug 上报', color: 'red' },
        result_writeback: { label: '结果回写', color: 'green' },
      }
      return <Tag color={map[t]?.color}>{map[t]?.label || t}</Tag>
    },
  },
  {
    title: '方向', dataIndex: 'direction', key: 'direction', width: 70,
    render: (d: string) => d === 'pull' ? <Tag>拉取</Tag> : <Tag>推送</Tag>,
  },
  {
    title: '状态', dataIndex: 'status', key: 'status', width: 80,
    render: (s: string) => {
      const map: Record<string, { status: 'success' | 'error' | 'warning'; label: string }> = {
        success: { status: 'success', label: '成功' },
        failed: { status: 'error', label: '失败' },
        partial: { status: 'warning', label: '部分成功' },
      }
      return <Badge status={map[s]?.status || 'default'} text={map[s]?.label || s} />
    },
  },
  { title: '详情', dataIndex: 'detail', key: 'detail' },
  { title: '影响记录', dataIndex: 'recordsAffected', key: 'recordsAffected', width: 80 },
  { title: '时间', dataIndex: 'createdAt', key: 'createdAt', width: 160, render: (t: string) => formatDate(t) },
]

export default function ZentaoSync() {
  const [logs, setLogs] = useState<SyncLog[]>([])
  const [loading, setLoading] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [total, setTotal] = useState(0)

  const fetchLogs = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getSyncLogs({ page: 1, limit: 20 })
      setLogs(res.items || [])
      setTotal(res.total || 0)
    } catch {
      // 后端可能还没有数据，静默处理
      setLogs([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchLogs()
  }, [fetchLogs])

  async function handleSyncCases() {
    setSyncing(true)
    try {
      // 从 localStorage 读取配置
      const raw = localStorage.getItem('zentao_config')
      const config = raw ? JSON.parse(raw) : null
      if (!config || !config.defaultProductId) {
        message.warning('请先在禅道配置页面完成配置并设置默认产品 ID')
        setSyncing(false)
        return
      }
      await syncZentaoCases({ product_id: config.defaultProductId, project_id: 1 })
      message.success('用例同步成功！')
      fetchLogs()
    } catch (err: unknown) {
      const errMsg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message || '同步失败'
      message.error(errMsg)
    } finally {
      setSyncing(false)
    }
  }

  async function handleWriteResult() {
    try {
      // 获取最近的 execution id — 简化：让用户输入或使用默认
      message.info('请从执行记录中选择需要回写结果的执行项')
    } catch {
      message.error('回写失败')
    }
  }

  // 统计数据
  const successCount = logs.filter(l => l.status === 'success').length
  const bugCount = logs.filter(l => l.type === 'bug_export').length
  const writebackCount = logs.filter(l => l.type === 'result_writeback').length

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>禅道同步管理</Title>
        <Space>
          <Button icon={<SyncOutlined />} onClick={handleSyncCases} loading={syncing}>
            同步用例
          </Button>
          <Button icon={<FileTextOutlined />} onClick={handleWriteResult}>
            回写结果
          </Button>
        </Space>
      </div>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card><Statistic title="同步日志总数" value={total} prefix={<FileTextOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="成功次数" value={successCount} prefix={<CheckCircleOutlined />} valueStyle={{ color: '#52c41a' }} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="Bug 上报" value={bugCount} prefix={<BugOutlined />} valueStyle={{ color: '#ff4d4f' }} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="结果回写" value={writebackCount} suffix="次" prefix={<SyncOutlined />} /></Card>
        </Col>
      </Row>

      <Card title="同步日志">
        <Table
          dataSource={logs}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ showTotal: (t) => `共 ${t} 条` }}
        />
      </Card>
    </div>
  )
}
