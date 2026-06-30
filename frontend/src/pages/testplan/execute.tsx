import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Button, Space, Typography, Tag, Progress, Steps, Statistic, Row, Col, message } from 'antd'
import {
  ArrowLeftOutlined, PauseCircleOutlined, ReloadOutlined,
  CheckCircleOutlined, CloseCircleOutlined, LoadingOutlined, WifiOutlined,
} from '@ant-design/icons'
import ReactEChartsCore from 'echarts-for-react'
import { formatDuration } from '../../utils/format'
import { runTestPlan, getExecutions, getExecution, stopExecution } from '../../services/testplan'
import { APP_CONFIG } from '../../config'
import type { Execution } from '../../types'

const { Title, Text } = Typography

// WebSocket 状态更新数据类型
interface WSUpdate {
  event: string
  execution_id: number
  case_id: number
  case_title: string
  status: string
  message: string
  duration?: number
}

export default function ExecuteMonitor() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [executions, setExecutions] = useState<Execution[]>([])
  const [running, setRunning] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const [wsConnected, setWsConnected] = useState(false)
  const timerRef = useRef<ReturnType<typeof setInterval>>()
  const wsRef = useRef<WebSocket>()
  const wsConnectedRef = useRef(false)

  const planId = Number(id)

  // ── WebSocket 连接 ──
  function connectWebSocket(executionIds: number[]) {
    // 关闭旧连接
    if (wsRef.current) {
      wsRef.current.close()
    }

    // 为第一个执行 ID 建立 WebSocket（后端按 execution_id 推送）
    const mainExecId = executionIds[0]
    if (!mainExecId) return

    const wsUrl = `${APP_CONFIG.wsBaseUrl}/executions/${mainExecId}`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      setWsConnected(true)
      wsConnectedRef.current = true
      console.log(`[WS] Connected to ${wsUrl}`)
    }

    ws.onmessage = (event) => {
      try {
        const data: WSUpdate = JSON.parse(event.data)
        console.log('[WS] Received:', data)

        // 更新对应执行记录的状态
        setExecutions(prev =>
          prev.map(e =>
            e.id === data.execution_id
              ? { ...e, status: data.status as Execution['status'] }
              : e
          )
        )

        // 检查是否全部完成
        if (data.status === 'passed' || data.status === 'failed') {
          // 延迟检查，等所有更新到达
          setTimeout(() => {
            setExecutions(prev => {
              const pending = prev.filter(e =>
                e.status === 'pending' || e.status === 'running'
              )
              if (pending.length === 0 && prev.length > 0) {
                setRunning(false)
                const passed = prev.filter(e => e.status === 'passed').length
                message.info(`执行完成: ${passed}/${prev.length} 通过`)
              }
              return prev
            })
          }, 500)
        }
      } catch {
        // 忽略解析错误
      }
    }

    ws.onclose = () => {
      setWsConnected(false)
      wsConnectedRef.current = false
      console.log('[WS] Disconnected')
    }

    ws.onerror = () => {
      console.log('[WS] Connection error — falling back to polling')
    }

    wsRef.current = ws
  }

  // ── 启动执行 ──
  async function handleStart() {
    try {
      setRunning(true)
      const result = await runTestPlan(planId)
      const execIds = result.executions?.map(e => e.id) || []
      message.success(`执行已启动，共创建 ${execIds.length} 条执行记录`)

      // 加载所有执行记录
      if (execIds.length > 0) {
        const execList: Execution[] = []
        for (const eid of execIds) {
          try {
            const detail = await getExecution(eid)
            execList.push(detail)
          } catch {
            execList.push({
              id: eid, planId, caseId: 0,
              status: 'pending' as const, triggerType: 'manual' as const,
              screenshots: [], log: '', steps: [], retryCount: 0, executedBy: 'manual',
            })
          }
        }
        setExecutions(execList)
        // 建立 WebSocket 连接
        connectWebSocket(execIds)
      }
    } catch (err: unknown) {
      const errMsg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message || '启动执行失败'
      message.error(errMsg)
      setRunning(false)
    }
  }

  // ── 停止执行 ──
  async function handleStop() {
    try {
      for (const exec of executions) {
        if (exec.status === 'pending' || exec.status === 'running') {
          await stopExecution(exec.id)
        }
      }
      setRunning(false)
      message.info('执行已停止')
    } catch {
      message.error('停止执行失败')
    }
  }

  // ── HTTP 轮询（WebSocket 不可用时的后备方案） ──
  const pollStatus = useCallback(async () => {
    if (wsConnectedRef.current) return // WebSocket 已连接，不需要轮询
    const updated: Execution[] = []
    let allDone = true
    for (const exec of executions) {
      try {
        const fresh = await getExecution(exec.id)
        updated.push(fresh)
        if (fresh.status === 'pending' || fresh.status === 'running') {
          allDone = false
        }
      } catch {
        updated.push(exec)
      }
    }
    setExecutions(updated)
    if (allDone && updated.length > 0) {
      setRunning(false)
      const passed = updated.filter(e => e.status === 'passed').length
      message.info(`执行完成: ${passed}/${updated.length} 通过`)
    }
  }, [executions])

  // ── 加载历史执行记录 ──
  useEffect(() => {
    if (planId) {
      getExecutions({ planId, limit: 20 }).then(res => {
        if (res.items?.length > 0) {
          setExecutions(res.items)
        }
      }).catch(() => {})
    }
  }, [planId])

  // ── 定时器 & 轮询 ──
  useEffect(() => {
    if (running) {
      timerRef.current = setInterval(() => setElapsed((p) => p + 100), 100)
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [running])

  useEffect(() => {
    if (running && executions.length > 0) {
      const interval = setInterval(pollStatus, 5000)
      return () => clearInterval(interval)
    }
  }, [running, executions.length, pollStatus])

  // ── 清理 WebSocket ──
  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close()
    }
  }, [])

  // ── 统计数据 ──
  const totalCases = executions.length
  const passedCases = executions.filter(e => e.status === 'passed').length
  const failedCases = executions.filter(e => e.status === 'failed').length
  const runningCount = executions.filter(e => e.status === 'running').length
  const pendingCount = executions.filter(e => e.status === 'pending').length
  const hasFinished = !running && executions.length > 0

  const gaugeOption = {
    series: [{
      type: 'gauge',
      startAngle: 210, endAngle: -30,
      center: ['50%', '60%'], radius: '90%',
      min: 0, max: 100,
      data: [{ value: totalCases > 0 ? Math.round((passedCases / totalCases) * 100) : 0, name: '通过率' }],
      axisLine: { lineStyle: { width: 20, color: [[0.3, '#52c41a'], [0.7, '#faad14'], [1, '#ff4d4f']] } },
      detail: { fontSize: 32, offsetCenter: [0, 50] },
    }],
  }

  // 汇总所有步骤
  const allSteps = executions.flatMap(exec =>
    (exec.steps || []).map(step => ({
      ...step,
      caseTitle: exec.caseTitle || `用例 #${exec.caseId}`,
    }))
  )

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(`/testplans/${id}`)}>返回计划</Button>
        {!running && executions.length === 0 && (
          <Button icon={<ReloadOutlined />} type="primary" onClick={handleStart} loading={running}>
            启动执行
          </Button>
        )}
        {running && (
          <Button icon={<PauseCircleOutlined />} danger onClick={handleStop}>停止执行</Button>
        )}
        {hasFinished && (
          <Button icon={<ReloadOutlined />} type="primary" onClick={handleStart}>
            重新执行
          </Button>
        )}
        {running && (
          <Tag icon={wsConnected ? <WifiOutlined style={{ color: '#52c41a' }} /> : <WifiOutlined />}
               color={wsConnected ? 'success' : 'default'}>
            {wsConnected ? 'WebSocket' : '轮询'}
          </Tag>
        )}
      </Space>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          执行监控
          {running && <Tag color="processing" style={{ marginLeft: 8 }}>执行中</Tag>}
          {hasFinished && (
            <Tag color={failedCases > 0 ? 'error' : 'success'} style={{ marginLeft: 8 }}>
              {failedCases > 0 ? `${failedCases} 失败` : '全部通过'}
            </Tag>
          )}
        </Title>
        <Text type="secondary">已运行: {formatDuration(elapsed)}</Text>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card><Statistic title="总用例" value={totalCases} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="已通过" value={passedCases} valueStyle={{ color: '#52c41a' }} prefix={<CheckCircleOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="失败" value={failedCases} valueStyle={{ color: failedCases > 0 ? '#ff4d4f' : undefined }} prefix={<CloseCircleOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="执行中/等待" value={runningCount + pendingCount} prefix={<LoadingOutlined />} /></Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={8}>
          <Card title="执行进度">
            <ReactEChartsCore option={gaugeOption} style={{ height: 220 }} />
            <Progress
              percent={totalCases > 0 ? Math.round(((passedCases + failedCases) / totalCases) * 100) : 0}
              status={running ? 'active' : failedCases > 0 ? 'exception' : 'normal'}
            />
          </Card>
        </Col>

        <Col span={16}>
          <Card title="执行步骤" extra={
            running ? <Tag icon={<LoadingOutlined />} color="processing">执行中...</Tag> : null
          }>
            {allSteps.length > 0 ? (
              <Steps
                direction="vertical"
                current={allSteps.filter(s => s.status === 'passed' || s.status === 'failed').length}
                items={allSteps.map((step) => ({
                  title: (
                    <Space>
                      <Tag color="blue">{step.caseTitle}</Tag>
                      <span>{step.seq}. {step.action}</span>
                      {step.status === 'passed' && <CheckCircleOutlined style={{ color: '#52c41a' }} />}
                      {step.status === 'failed' && <CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
                      {step.status === 'running' && <LoadingOutlined style={{ color: '#1677ff' }} />}
                      {step.status === 'skipped' && <span style={{ color: '#bbb' }}>跳过</span>}
                    </Space>
                  ),
                  description: step.timestamp ? (
                    <Text type="secondary">
                      时间: {step.timestamp}
                      {step.duration ? ` | 耗时: ${formatDuration(step.duration)}` : ''}
                      {step.errorMessage ? <span style={{ color: '#ff4d4f' }}> | {step.errorMessage}</span> : null}
                    </Text>
                  ) : undefined,
                }))}
              />
            ) : (
              <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
                {executions.length > 0 ? '暂无步骤详情' : '点击「启动执行」开始测试'}
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* 执行日志 */}
      <Card title="执行日志" style={{ marginTop: 16 }}>
        <div style={{
          background: '#1e1e1e', color: '#d4d4d4', padding: 16,
          borderRadius: 8, fontFamily: 'monospace', fontSize: 13,
          maxHeight: 300, overflow: 'auto', whiteSpace: 'pre-wrap',
        }}>
          {executions.length > 0 ? (
            executions.map(exec => (
              <div key={exec.id} style={{ marginBottom: 8 }}>
                <span style={{ color: '#6a9955' }}>[用例 #{exec.caseId}]</span>{' '}
                <span style={{
                  color: exec.status === 'passed' ? '#4ec9b0' :
                         exec.status === 'failed' ? '#f44747' :
                         exec.status === 'running' ? '#dcdcaa' : '#888'
                }}>
                  {exec.status?.toUpperCase()}
                </span>
                {exec.errorMessage && <span style={{ color: '#f44747' }}> — {exec.errorMessage}</span>}
              </div>
            ))
          ) : (
            <span style={{ color: '#888' }}>点击「启动执行」开始测试</span>
          )}
        </div>
      </Card>
    </div>
  )
}
