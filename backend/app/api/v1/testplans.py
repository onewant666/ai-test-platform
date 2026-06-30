"""测试计划 & 执行 API"""

from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.testplan import TestPlanCreate, TestPlanUpdate
from app.schemas.common import APIResponse, PaginatedReq, PaginatedRes
from app.api.deps import get_current_user
from app.models.user import User
from app.models.testplan import TestPlan, PlanStatus
from app.models.execution import Execution, ExecutionStatus, TriggerType

router = APIRouter(tags=["测试计划"])


@router.get("/testplans")
def list_plans(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    project_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(TestPlan)
    if project_id:
        query = query.filter(TestPlan.project_id == project_id)
    total = query.count()
    items = query.order_by(TestPlan.updated_at.desc()).offset((page - 1) * limit).limit(limit).all()

    def serialize(plan: TestPlan) -> dict:
        return {
            "id": plan.id, "project_id": plan.project_id, "name": plan.name,
            "description": plan.description, "case_ids": plan.case_ids or [],
            "case_count": len(plan.case_ids or []),
            "status": plan.status.value if hasattr(plan.status, 'value') else plan.status,
            "cron_expr": plan.cron_expr, "max_retries": plan.max_retries,
            "timeout": plan.timeout, "created_by": plan.created_by,
            "created_at": plan.created_at.isoformat() if plan.created_at else "",
            "updated_at": plan.updated_at.isoformat() if plan.updated_at else "",
        }

    return PaginatedRes(
        items=[serialize(p) for p in items],
        total=total, page=page, limit=limit,
        total_pages=max(1, (total + limit - 1) // limit),
    )


@router.post("/testplans", status_code=201)
def create_plan(
    data: TestPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = TestPlan(
        project_id=data.project_id, name=data.name, description=data.description,
        case_ids=data.case_ids, cron_expr=data.cron_expr,
        max_retries=data.max_retries, timeout=data.timeout,
        created_by=current_user.id,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return APIResponse(data={"id": plan.id}, message="计划创建成功")


@router.get("/testplans/{plan_id}")
def get_plan(plan_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    plan = db.query(TestPlan).filter(TestPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(404, "计划不存在")
    return APIResponse(data={
        "id": plan.id, "project_id": plan.project_id, "name": plan.name,
        "description": plan.description, "case_ids": plan.case_ids or [],
        "case_count": len(plan.case_ids or []),
        "status": plan.status.value if hasattr(plan.status, 'value') else plan.status,
        "cron_expr": plan.cron_expr, "max_retries": plan.max_retries,
        "timeout": plan.timeout, "created_by": plan.created_by,
        "created_at": plan.created_at.isoformat() if plan.created_at else "",
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else "",
    })


@router.post("/testplans/{plan_id}/run")
def run_plan(plan_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """
    启动测试计划执行。

    为计划关联的每个用例创建一条 Execution 记录，通过 Celery 异步任务
    依次执行 AI 浏览器测试。执行进度可通过 WebSocket 订阅:
    `ws://host/ws/executions/{execution_id}`

    - **plan_id**: 测试计划 ID
    """
    plan = db.query(TestPlan).filter(TestPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(404, "计划不存在")

    if not plan.case_ids:
        raise HTTPException(400, "计划未关联任何用例")

    plan.status = PlanStatus.RUNNING
    db.commit()

    # 为每个关联用例创建执行记录
    executions = []
    for case_id in plan.case_ids:
        exec_record = Execution(
            plan_id=plan.id,
            case_id=case_id,
            status=ExecutionStatus.PENDING,
            trigger_type=TriggerType.MANUAL,
            steps=[],
            screenshots=[],
            log="",
            executed_by="manual",
        )
        db.add(exec_record)
        db.flush()
        executions.append(exec_record)

    db.commit()

    # 触发 Celery 异步任务执行每个用例
    from app.tasks.executor import run_testcase_execution
    for exec_record in executions:
        run_testcase_execution.delay(exec_record.id)

    return APIResponse(data={
        "plan_id": plan.id,
        "executions": [
            {
                "id": e.id,
                "plan_id": e.plan_id,
                "case_id": e.case_id,
                "status": e.status.value if hasattr(e.status, 'value') else e.status,
            }
            for e in executions
        ],
    }, message=f"执行已启动，共创建 {len(executions)} 条执行记录")


# ── 执行记录 ──

@router.get("/executions")
def list_executions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    plan_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Execution)
    if plan_id:
        query = query.filter(Execution.plan_id == plan_id)
    total = query.count()
    items = query.order_by(Execution.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    def serialize(e: Execution) -> dict:
        return {
            "id": e.id, "plan_id": e.plan_id, "case_id": e.case_id,
            "status": e.status.value if hasattr(e.status, 'value') else e.status,
            "trigger_type": e.trigger_type.value if hasattr(e.trigger_type, 'value') else e.trigger_type,
            "start_time": e.start_time.isoformat() if e.start_time else None,
            "end_time": e.end_time.isoformat() if e.end_time else None,
            "duration": e.duration, "error_message": e.error_message,
            "screenshots": e.screenshots or [], "log": e.log,
            "steps": e.steps or [], "zentao_bug_id": e.zentao_bug_id,
            "retry_count": e.retry_count, "executed_by": e.executed_by,
        }

    return PaginatedRes(
        items=[serialize(e) for e in items],
        total=total, page=page, limit=limit,
        total_pages=max(1, (total + limit - 1) // limit),
    )


@router.get("/executions/{execution_id}")
def get_execution(execution_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    e = db.query(Execution).filter(Execution.id == execution_id).first()
    if not e:
        raise HTTPException(404, "执行记录不存在")
    return APIResponse(data={
        "id": e.id, "plan_id": e.plan_id, "case_id": e.case_id,
        "status": e.status.value if hasattr(e.status, 'value') else e.status,
        "start_time": e.start_time.isoformat() if e.start_time else None,
        "end_time": e.end_time.isoformat() if e.end_time else None,
        "duration": e.duration, "error_message": e.error_message,
        "screenshots": e.screenshots or [], "log": e.log,
        "steps": e.steps or [], "zentao_bug_id": e.zentao_bug_id,
        "retry_count": e.retry_count, "executed_by": e.executed_by,
    })


@router.post("/executions/{execution_id}/stop")
def stop_execution(execution_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    e = db.query(Execution).filter(Execution.id == execution_id).first()
    if not e:
        raise HTTPException(404, "执行记录不存在")
    e.status = ExecutionStatus.FAILED
    e.error_message = "用户手动停止"
    e.end_time = datetime.utcnow()
    db.commit()
    return APIResponse(data={"id": e.id}, message="执行已停止")
