import { useState, useEffect, useCallback } from 'react'
import { Card, Table, Button, Space, Tag, Typography, Modal, Form, Input, message } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, LinkOutlined } from '@ant-design/icons'
import { getProjects, createProject, updateProject, deleteProject, type ProjectItem } from '../../services/project'
import { formatDate } from '../../utils/format'

const { Title } = Typography

export default function ProjectList() {
  const [projects, setProjects] = useState<ProjectItem[]>([])
  const [loading, setLoading] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [form] = Form.useForm()
  const [editingId, setEditingId] = useState<number | null>(null)

  const fetchProjects = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getProjects({ limit: 100 })
      setProjects(res.items || [])
    } catch {
      message.error('获取项目列表失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  function handleCreate() {
    setEditingId(null)
    form.resetFields()
    setIsModalOpen(true)
  }

  function handleEdit(record: ProjectItem) {
    setEditingId(record.id)
    form.setFieldsValue({
      name: record.name,
      description: record.description,
      zentaoProductId: record.zentaoProductId,
    })
    setIsModalOpen(true)
  }

  async function handleDelete(id: number) {
    Modal.confirm({
      title: '确认删除',
      content: '删除项目将同时删除关联的用例和计划，确定继续？',
      okType: 'danger',
      onOk: async () => {
        try {
          await deleteProject(id)
          message.success('项目已删除')
          fetchProjects()
        } catch {
          message.error('删除失败')
        }
      },
    })
  }

  async function handleSubmit() {
    try {
      const values = await form.validateFields()
      setSubmitting(true)
      const payload = {
        name: values.name,
        description: values.description,
        zentao_product_id: values.zentaoProductId ? Number(values.zentaoProductId) : undefined,
      }
      if (editingId) {
        await updateProject(editingId, payload)
        message.success('项目已更新')
      } else {
        await createProject(payload)
        message.success('项目已创建')
      }
      setIsModalOpen(false)
      fetchProjects()
    } catch (err: unknown) {
      const errMsg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message
      if (errMsg) message.error(errMsg)
    } finally {
      setSubmitting(false)
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '项目名称', dataIndex: 'name', key: 'name', width: 180 },
    { title: '描述', dataIndex: 'description', key: 'description' },
    {
      title: '禅道关联', dataIndex: 'zentaoProductId', key: 'zentaoProductId', width: 120,
      render: (id: number) => id ? <Tag icon={<LinkOutlined />} color="blue">产品 #{id}</Tag> : <Tag>未关联</Tag>,
    },
    { title: '用例数', dataIndex: 'caseCount', key: 'caseCount', width: 80 },
    {
      title: '创建日期', dataIndex: 'createdAt', key: 'createdAt', width: 120,
      render: (t: string) => formatDate(t, 'YYYY-MM-DD'),
    },
    {
      title: '操作', key: 'action', width: 140,
      render: (_: unknown, r: ProjectItem) => (
        <Space>
          <Button type="text" size="small" icon={<EditOutlined />} onClick={() => handleEdit(r)} />
          <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(r.id)} />
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>项目管理</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>新建项目</Button>
      </div>

      <Card>
        <Table
          dataSource={projects}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      </Card>

      <Modal
        title={editingId ? '编辑项目' : '新建项目'}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={handleSubmit}
        confirmLoading={submitting}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }]}>
            <Input placeholder="项目名称" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="项目描述" />
          </Form.Item>
          <Form.Item name="zentaoProductId" label="禅道产品 ID">
            <Input type="number" placeholder="关联禅道产品" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
