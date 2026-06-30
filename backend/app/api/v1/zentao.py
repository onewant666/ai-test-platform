"""禅道集成 API"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.schemas.common import APIResponse, PaginatedReq, PaginatedRes
from app.api.deps import get_current_user
from app.models.user import User
from app.models.zentao import ZentaoSyncLog
from app.adapters.zentao.client import ZentaoClient
from app.adapters.zentao.sync import sync_cases_from_zentao

router = APIRouter(prefix="/zentao", tags=["禅道集成"])


class ZentaoConfigReq(BaseModel):
    base_url: str
    account: str
    password: str


class SyncCasesReq(BaseModel):
    product_id: int
    project_id: int


class ReportBugReq(BaseModel):
    execution_id: int
    product_id: int


@router.post("/test-connection")
def test_connection(config: ZentaoConfigReq):
    client = ZentaoClient(base_url=config.base_url, account=config.account, password=config.password)
    ok = client.test_connection()
    if ok:
        return APIResponse(data={"connected": True}, message="禅道连接成功")
    else:
        raise HTTPException(400, "禅道连接失败，请检查配置")


@router.get("/products")
def get_products(config_base_url: str, config_account: str, config_password: str):
    client = ZentaoClient(base_url=config_base_url, account=config_account, password=config_password)
    try:
        products = client.get_products()
        return APIResponse(data=products)
    except Exception as e:
        raise HTTPException(400, f"获取产品列表失败: {str(e)}")


@router.post("/sync/cases")
def sync_cases(
    req: SyncCasesReq,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = ZentaoClient()
    log = sync_cases_from_zentao(db, client, req.product_id, req.project_id, current_user.id)
    return APIResponse(data={
        "log_id": log.id,
        "status": log.status.value,
        "detail": log.detail,
        "records_affected": log.records_affected,
    }, message="同步完成")


@router.post("/report-bug")
def report_bug(
    req: ReportBugReq,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from app.adapters.zentao.sync import report_bug_to_zentao
    from app.models.execution import Execution

    execution = db.query(Execution).filter(Execution.id == req.execution_id).first()
    if not execution:
        raise HTTPException(404, "执行记录不存在")

    client = ZentaoClient()
    log = report_bug_to_zentao(db, client, execution, req.product_id)
    return APIResponse(data={"log_id": log.id, "status": log.status.value, "detail": log.detail})


@router.post("/write-result")
def write_result(
    execution_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from app.adapters.zentao.sync import write_result_to_zentao
    from app.models.execution import Execution

    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    if not execution:
        raise HTTPException(404, "执行记录不存在")

    client = ZentaoClient()
    log = write_result_to_zentao(db, client, execution)
    return APIResponse(data={"log_id": log.id, "status": log.status.value, "detail": log.detail})


@router.get("/sync-logs")
def get_sync_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取禅道同步日志列表"""
    query = db.query(ZentaoSyncLog).order_by(ZentaoSyncLog.created_at.desc())
    total = query.count()
    total_pages = max(1, (total + limit - 1) // limit)
    items = query.offset((page - 1) * limit).limit(limit).all()

    return PaginatedRes(
        items=[_sync_log_to_response(log) for log in items],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


def _sync_log_to_response(log: ZentaoSyncLog) -> dict:
    return {
        "id": log.id,
        "type": log.type.value if hasattr(log.type, 'value') else log.type,
        "direction": log.direction.value if hasattr(log.direction, 'value') else log.direction,
        "status": log.status.value if hasattr(log.status, 'value') else log.status,
        "detail": log.detail,
        "records_affected": log.records_affected,
        "created_at": log.created_at.isoformat() if log.created_at else "",
    }
