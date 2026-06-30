"""用例 API"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.testcase import TestCaseCreate, TestCaseUpdate, TestCaseResponse
from app.schemas.common import APIResponse, PaginatedRes
from app.services.testcase_service import list_testcases, get_testcase, create_testcase, update_testcase, delete_testcase
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/testcases", tags=["用例管理"])


@router.get("")
def get_list(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    keyword: str | None = None,
    project_id: int | None = None,
    status: str | None = None,
    priority: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from app.schemas.common import PaginatedReq
    pagination = PaginatedReq(page=page, limit=limit, keyword=keyword)
    result = list_testcases(db, pagination, project_id, status, priority)
    return result


@router.get("/{testcase_id}")
def get_one(
    testcase_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    tc = get_testcase(db, testcase_id)
    from app.services.testcase_service import _to_response
    return APIResponse(data=_to_response(tc))


@router.post("", status_code=201)
def create(
    data: TestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tc = create_testcase(db, data, current_user.id)
    from app.services.testcase_service import _to_response
    return APIResponse(data=_to_response(tc), message="用例创建成功")


@router.put("/{testcase_id}")
def update(
    testcase_id: int,
    data: TestCaseUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    tc = get_testcase(db, testcase_id)
    tc = update_testcase(db, tc, data)
    from app.services.testcase_service import _to_response
    return APIResponse(data=_to_response(tc), message="用例更新成功")


@router.delete("/{testcase_id}")
def delete(
    testcase_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    tc = get_testcase(db, testcase_id)
    delete_testcase(db, tc)
    return APIResponse(data=None, message="用例已删除")
