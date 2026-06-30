import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card, Form, Input, Select, Button, Space, Typography, Divider,
  Row, Col, message, Modal, Spin,
} from 'antd'
import { PlusOutlined, DeleteOutlined, ArrowLeftOutlined, RobotOutlined } from '@ant-design/icons'
import { getTestCase, createTestCase, updateTestCase } from '../../services/testcase'
import { generateSteps } from '../../services/ai'
import { CASE_PRIORITY, TEST_STEP_ACTIONS } from '../../config/constants'

const { Title } = Typography
const { TextArea } = Input

export default function TestCaseEditor() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isEdit = !!id

  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [aiLoading, setAiLoading] = useState(false)
  const [aiModalOpen, setAiModalOpen] = useState(false)
  const [aiDesc, setAiDesc] = useState('')

  // 编辑模式下加载用例数据
  useEffect(() => {
    if (isEdit && id) {
      setLoading(true)
      getTestCase(Number(id))
        .then((tc) => {
          form.setFieldsValue({
            title: tc.title,
            priority: tc.priority,
            status: tc.status,
            module: tc.module,
            tags: tc.tags || [],
            description: tc.description,
            preconditions: tc.preconditions,
            steps: tc.steps || [{ seq: 1, action: 'navigate', target: '', value: '', expected: '' }],
            projectId: tc.projectId,
          })
        })
        .catch(() => message.error('加载用例失败'))
        .finally(() => setLoading(false))
    }
  }, [id, isEdit, form])

  async function handleFinish(values: Record<string, unknown>) {
    setSubmitting(true)
    try {
      const payload: Record<string, unknown> = {
        project_id: values.projectId || 1,
        title: values.title,
        description: values.description || '',
        priority: values.priority,
        status: values.status || 'draft',
        preconditions: values.preconditions || '',
        steps: values.steps || [],
        tags: values.tags || [],
        module: values.module || '',
      }
      if (isEdit && id) {
        await updateTestCase(Number(id), payload)
        message.success('用例已更新')
      } else {
        await createTestCase(payload)
        message.success('用例已创建')
      }
      navigate('/testcases')
    } catch (err: unknown) {
      const errMsg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message || '操作失败'
      message.error(errMsg)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleAIGenerate() {
    if (!aiDesc.trim()) return
    setAiLoading(true)
    try {
      const res = await generateSteps({ description: aiDesc })
      if (res.steps && res.steps.length > 0) {
        form.setFieldValue('steps', res.steps)
        message.success('AI 已生成测试步骤')
      } else {
        message.warning('AI 未能生成步骤，请尝试更详细的描述')
      }
      setAiModalOpen(false)
      setAiDesc('')
    } catch {
      message.error('AI 生成步骤失败，请检查 LLM 配置')
    } finally {
      setAiLoading(false)
    }
  }

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/testcases')}>返回</Button>
      </Space>

      <Card
        title={<Title level={4} style={{ margin: 0 }}>{isEdit ? '编辑用例' : '新建用例'}</Title>}
        extra={
          <Button icon={<RobotOutlined />} onClick={() => setAiModalOpen(true)}>
            AI 生成步骤
          </Button>
        }
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleFinish}
          initialValues={{
            priority: 'P2',
            status: 'draft',
            projectId: 1,
            steps: [{ seq: 1, action: 'navigate', target: '', value: '', expected: '' }],
            tags: [],
          }}
        >
          <Row gutter={24}>
            <Col span={16}>
              <Form.Item name="title" label="用例名称" rules={[{ required: true, message: '请输入用例名称' }]}>
                <Input placeholder="例如：用户登录功能验证" />
              </Form.Item>
            </Col>
            <Col span={4}>
              <Form.Item name="priority" label="优先级" rules={[{ required: true }]}>
                <Select
                  options={Object.entries(CASE_PRIORITY).map(([k, v]) => ({ value: k, label: v.label }))}
                />
              </Form.Item>
            </Col>
            <Col span={4}>
              <Form.Item name="status" label="状态">
                <Select options={[
                  { value: 'draft', label: '草稿' },
                  { value: 'reviewing', label: '评审中' },
                  { value: 'approved', label: '已通过' },
                ]} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={24}>
            <Col span={12}>
              <Form.Item name="module" label="所属模块">
                <Input placeholder="例如：用户管理" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="tags" label="标签">
                <Select
                  mode="tags"
                  placeholder="输入标签后回车"
                  options={[
                    { value: 'smoke', label: 'smoke' },
                    { value: 'regression', label: 'regression' },
                    { value: 'login', label: 'login' },
                  ]}
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="description" label="用例描述">
            <TextArea rows={2} placeholder="描述用例的测试目标和场景" />
          </Form.Item>

          <Form.Item name="preconditions" label="前置条件">
            <TextArea rows={2} placeholder="执行前需满足的条件" />
          </Form.Item>

          {/* 隐藏的 project_id 字段 */}
          <Form.Item name="projectId" hidden>
            <Input />
          </Form.Item>

          <Divider orientation="left">测试步骤</Divider>

          <Form.List name="steps">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...rest }) => (
                  <Row
                    key={key}
                    gutter={12}
                    align="top"
                    style={{ marginBottom: 8, padding: 8, background: '#fafafa', borderRadius: 8 }}
                  >
                    <Col flex="40px">
                      <div style={{ textAlign: 'center', lineHeight: '32px', fontWeight: 600 }}>
                        {name + 1}
                      </div>
                    </Col>
                    <Col flex="140px">
                      <Form.Item {...rest} name={[name, 'action']} noStyle>
                        <Select options={TEST_STEP_ACTIONS} placeholder="操作" />
                      </Form.Item>
                    </Col>
                    <Col flex="auto">
                      <Form.Item {...rest} name={[name, 'target']} noStyle>
                        <Input placeholder="目标元素" />
                      </Form.Item>
                    </Col>
                    <Col flex="160px">
                      <Form.Item {...rest} name={[name, 'value']} noStyle>
                        <Input placeholder="输入值" />
                      </Form.Item>
                    </Col>
                    <Col flex="auto">
                      <Form.Item {...rest} name={[name, 'expected']} noStyle>
                        <Input placeholder="预期结果" />
                      </Form.Item>
                    </Col>
                    <Col flex="40px">
                      {fields.length > 1 && (
                        <Button
                          type="text"
                          danger
                          icon={<DeleteOutlined />}
                          onClick={() => remove(name)}
                        />
                      )}
                    </Col>
                  </Row>
                ))}
                <Button
                  type="dashed"
                  onClick={() => add({ seq: fields.length + 1, action: 'click', target: '', value: '', expected: '' })}
                  block
                  icon={<PlusOutlined />}
                >
                  添加步骤
                </Button>
              </>
            )}
          </Form.List>

          <Divider />

          <Space>
            <Button type="primary" htmlType="submit" loading={submitting}>
              {isEdit ? '保存修改' : '创建用例'}
            </Button>
            <Button onClick={() => navigate('/testcases')}>取消</Button>
          </Space>
        </Form>
      </Card>

      {/* AI 生成步骤弹窗 */}
      <Modal
        title="AI 智能生成测试步骤"
        open={aiModalOpen}
        onCancel={() => { setAiModalOpen(false); setAiDesc('') }}
        onOk={handleAIGenerate}
        confirmLoading={aiLoading}
        okText="生成"
        cancelText="取消"
      >
        <TextArea
          rows={4}
          value={aiDesc}
          onChange={(e) => setAiDesc(e.target.value)}
          placeholder="用自然语言描述测试场景，例如：打开登录页，输入用户名 admin 和密码 123456，点击登录按钮，验证跳转到首页并显示用户名"
        />
      </Modal>
    </div>
  )
}
