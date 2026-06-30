"""项目管理 API"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.common import APIResponse, PaginatedReq
from app.services.project_service import (
    list_projects, get_project, create_project, update_project, delete_project,
    ProjectCreate, ProjectUpdate,
)
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/projects", tags=["项目管理"])


@router.get("")
def get_list(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    keyword: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    pagination = PaginatedReq(page=page, limit=limit, keyword=keyword)
    result = list_projects(db, pagination)
    return result


@router.get("/{project_id}")
def get_one(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = get_project(db, project_id)
    return APIResponse(data=_to_detail(db, p))


@router.post("", status_code=201)
def create(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    p = create_project(db, data, current_user.id)
    return APIResponse(data=_to_detail(db, p), message="项目创建成功")


@router.put("/{project_id}")
def update(
    project_id: int,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = get_project(db, project_id)
    p = update_project(db, p, data)
    return APIResponse(data=_to_detail(db, p), message="项目更新成功")


@router.delete("/{project_id}")
def delete(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = get_project(db, project_id)
    delete_project(db, p)
    return APIResponse(data=None, message="项目已删除")


def _to_detail(db: Session, p) -> dict:
    """返回含统计信息的项目详情"""
    from app.models.testcase import TestCase
    from app.models.testplan import TestPlan

    case_count = db.query(TestCase).filter(TestCase.project_id == p.id).count()
    plan_count = db.query(TestPlan).filter(TestPlan.project_id == p.id).count()

    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "status": p.status,
        "zentao_product_id": p.zentao_product_id,
        "created_by": p.created_by,
        "case_count": case_count,
        "plan_count": plan_count,
        "created_at": p.created_at.isoformat() if p.created_at else "",
        "updated_at": p.updated_at.isoformat() if p.updated_at else "",
    }
