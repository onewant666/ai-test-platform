"""报告 API"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.common import APIResponse, PaginatedRes
from app.api.deps import get_current_user
from app.models.user import User
from app.models.report import TestReport

router = APIRouter(prefix="/reports", tags=["报告"])


@router.get("")
def list_reports(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    获取测试报告列表。

    按创建时间倒序排列，支持分页。
    - **page**: 页码，从1开始
    - **limit**: 每页数量，最大100
    """
    query = db.query(TestReport)
    total = query.count()
    items = query.order_by(TestReport.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    def serialize(r: TestReport) -> dict:
        return {
            "id": r.id, "plan_id": r.plan_id, "plan_name": r.plan_name,
            "project_id": r.project_id, "project_name": r.project_name,
            "total_count": r.total_count, "passed_count": r.passed_count,
            "failed_count": r.failed_count, "skipped_count": r.skipped_count,
            "error_count": r.error_count, "pass_rate": r.pass_rate,
            "duration": r.duration,
            "start_time": r.start_time.isoformat() if r.start_time else "",
            "end_time": r.end_time.isoformat() if r.end_time else "",
        }

    return PaginatedRes(
        items=[serialize(r) for r in items],
        total=total, page=page, limit=limit,
        total_pages=max(1, (total + limit - 1) // limit),
    )


@router.get("/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    r = db.query(TestReport).filter(TestReport.id == report_id).first()
    if not r:
        raise HTTPException(404, "报告不存在")
    return APIResponse(data={
        "id": r.id, "plan_id": r.plan_id, "plan_name": r.plan_name,
        "project_id": r.project_id, "project_name": r.project_name,
        "total_count": r.total_count, "passed_count": r.passed_count,
        "failed_count": r.failed_count, "skipped_count": r.skipped_count,
        "error_count": r.error_count, "pass_rate": r.pass_rate,
        "duration": r.duration, "case_results": r.case_results or [],
        "trend_data": r.trend_data or [],
        "start_time": r.start_time.isoformat() if r.start_time else "",
        "end_time": r.end_time.isoformat() if r.end_time else "",
    })
