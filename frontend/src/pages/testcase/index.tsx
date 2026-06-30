import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card, Table, Button, Input, Select, Space, Tag, Typography, Dropdown, Modal, message, Tooltip,
} from 'antd'
import {
  PlusOutlined, SearchOutlined, DeleteOutlined, ExportOutlined,
  EditOutlined, PlayCircleOutlined, EyeOutlined, MoreOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { getTestCases } from '../../services/testcase'
import { CASE_PRIORITY, CASE_STATUS } from '../../config/constants'
import type { TestCase } from '../../types'
import { formatRelative } from '../../utils/format'

const { Title } = Typography

export default function TestCaseList() {
  const navigate = useNavigate()
  const [keyword, setKeyword] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [priorityFilter, setPriorityFilter] = useState<string>('')
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [data, setData] = useState<TestCase[]>([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ page: 1, limit: 20, total: 0 })

  const fetchData = useCallback(async (page = 1, limit = 20) => {
    setLoading(true)
    try {
      const res = await getTestCases({
        page,
        limit,
        keyword: keyword || undefined,
        status: (statusFilter || undefined) as TestCase['status'] | undefined,
        priority: (priorityFilter || undefined) as TestCase['priority'] | undefined,
      })
      setData(res.items || [])
      setPagination({ page: res.page || 1, limit: res.limit || 20, total: res.total || 0 })
    } catch {
      message.error('获取用例列表失败')
    } finally {
      setLoading(false)
    }
  }, [keyword, statusFilter, priorityFilter])

  useEffect(() => {
    fetchData(1, pagination.limit)
  }, [keyword, statusFilter, priorityFilter, fetchData, pagination.limit])

  const columns: ColumnsType<TestCase> = [
    {
      title: 'ID', dataIndex: 'id', key: 'id', width: 60,
    },
    {
      title: '用例名称', dataIndex: 'title', key: 'title', width: 280,
      render: (t: string, r) => (
        <a onClick={() => navigate(`/testcases/${r.id}`)}>{t}</a>
      ),
    },
    {
      title: '优先级', dataIndex: 'priority', key: 'priority', width: 90,
      render: (p: string) => {
        const cfg = CASE_PRIORITY[p as keyof typeof CASE_PRIORITY]
        return <Tag color={cfg?.color}>{cfg?.label || p}</Tag>
      },
    },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 90,
      render: (s: string) => {
        const cfg = CASE_STATUS[s as keyof typeof CASE_STATUS]
        return <Tag color={cfg?.color}>{cfg?.label || s}</Tag>
      },
    },
    {
      title: '模块', dataIndex: 'module', key: 'module', width: 100,
    },
    {
      title: '标签', dataIndex: 'tags', key: 'tags', width: 160,
      render: (tags: string[]) => (
        <Space size={4} wrap>
          {tags?.map((t) => <Tag key={t}>{t}</Tag>)}
        </Space>
      ),
    },
    {
      title: '上次执行', dataIndex: 'lastRunStatus', key: 'lastRunStatus', width: 90,
      render: (s: string) => {
        if (!s) return <Tag>未执行</Tag>
        const color = s === 'passed' ? 'success' : 'error'
        const label = s === 'passed' ? '通过' : '失败'
        return <Tag color={color}>{label}</Tag>
      },
    },
    {
      title: '更新时间', dataIndex: 'updatedAt', key: 'updatedAt', width: 140,
      render: (t: string) => formatRelative(t),
    },
    {
      title: '操作', key: 'action', width: 120, fixed: 'right',
      render: (_: unknown, r: TestCase) => (
        <Space>
          <Tooltip title="查看">
            <Button type="text" size="small" icon={<EyeOutlined />} onClick={() => navigate(`/testcases/${r.id}`)} />
          </Tooltip>
          <Tooltip title="编辑">
            <Button type="text" size="small" icon={<EditOutlined />} onClick={() => navigate(`/testcases/${r.id}/edit`)} />
          </Tooltip>
          <Tooltip title="执行">
            <Button type="text" size="small" icon={<PlayCircleOutlined />} />
          </Tooltip>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>用例管理</Title>
        <Space>
          <Button icon={<ExportOutlined />}>导出</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/testcases/new')}>
            新建用例
          </Button>
        </Space>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Input
            placeholder="搜索用例名称或描述"
            prefix={<SearchOutlined />}
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            style={{ width: 280 }}
            allowClear
          />
          <Select
            placeholder="优先级"
            value={priorityFilter || undefined}
            onChange={(v) => setPriorityFilter(v || '')}
            allowClear
            style={{ width: 120 }}
            options={Object.entries(CASE_PRIORITY).map(([k, v]) => ({ value: k, label: v.label }))}
          />
          <Select
            placeholder="状态"
            value={statusFilter || undefined}
            onChange={(v) => setStatusFilter(v || '')}
            allowClear
            style={{ width: 120 }}
            options={Object.entries(CASE_STATUS).map(([k, v]) => ({ value: k, label: v.label }))}
          />
        </Space>
      </Card>

      <Card>
        {selectedRowKeys.length > 0 && (
          <div style={{ marginBottom: 12 }}>
            <Space>
              <span>已选 {selectedRowKeys.length} 项</span>
              <Button size="small">批量执行</Button>
              <Button size="small" danger icon={<DeleteOutlined />}>批量删除</Button>
            </Space>
          </div>
        )}
        <Table
          dataSource={data}
          columns={columns}
          rowKey="id"
          loading={loading}
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys,
          }}
          scroll={{ x: 1100 }}
          pagination={{
            current: pagination.page,
            pageSize: pagination.limit,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, limit) => fetchData(page, limit),
          }}
        />
      </Card>
    </div>
  )
}
