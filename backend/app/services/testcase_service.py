"""用例服务"""

from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.testcase import TestCase
from app.schemas.testcase import TestCaseCreate, TestCaseUpdate
from app.schemas.common import PaginatedReq, PaginatedRes


def list_testcases(
    db: Session,
    pagination: PaginatedReq,
    project_id: int | None = None,
    status: str | None = None,
    priority: str | None = None,
    tags: list[str] | None = None,
) -> PaginatedRes:
    query = db.query(TestCase)

    if project_id:
        query = query.filter(TestCase.project_id == project_id)
    if status:
        query = query.filter(TestCase.status == status)
    if priority:
        query = query.filter(TestCase.priority == priority)
    if pagination.keyword:
        keyword = f"%{pagination.keyword}%"
        query = query.filter(
            or_(TestCase.title.like(keyword), TestCase.description.like(keyword))
        )

    total = query.count()
    total_pages = max(1, (total + pagination.limit - 1) // pagination.limit)

    order_col = getattr(TestCase, pagination.order_by or "updated_at", TestCase.updated_at)
    if pagination.order == "asc":
        query = query.order_by(order_col.asc())
    else:
        query = query.order_by(order_col.desc())

    items = query.offset((pagination.page - 1) * pagination.limit).limit(pagination.limit).all()

    return PaginatedRes(
        items=[_to_response(tc) for tc in items],
        total=total,
        page=pagination.page,
        limit=pagination.limit,
        total_pages=total_pages,
    )


def get_testcase(db: Session, testcase_id: int) -> TestCase:
    tc = db.query(TestCase).filter(TestCase.id == testcase_id).first()
    if not tc:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=404, detail="用例不存在")
    return tc


def create_testcase(db: Session, data: TestCaseCreate, user_id: int) -> TestCase:
    tc = TestCase(
        project_id=data.project_id,
        title=data.title,
        description=data.description,
        priority=data.priority,
        status=data.status,
        preconditions=data.preconditions,
        steps=[step.model_dump() for step in data.steps],
        tags=data.tags,
        module=data.module,
        zentao_id=data.zentao_id,
        zentao_case_id=data.zentao_case_id,
        created_by=user_id,
    )
    db.add(tc)
    db.commit()
    db.refresh(tc)
    return tc


def update_testcase(db: Session, tc: TestCase, data: TestCaseUpdate) -> TestCase:
    update_data = data.model_dump(exclude_unset=True)
    if "steps" in update_data and update_data["steps"]:
        update_data["steps"] = [s if isinstance(s, dict) else s.model_dump() for s in update_data["steps"]]
    for key, value in update_data.items():
        setattr(tc, key, value)
    db.commit()
    db.refresh(tc)
    return tc


def delete_testcase(db: Session, tc: TestCase) -> None:
    db.delete(tc)
    db.commit()


def _to_response(tc: TestCase) -> dict:
    return {
        "id": tc.id,
        "project_id": tc.project_id,
        "title": tc.title,
        "description": tc.description,
        "priority": tc.priority.value if hasattr(tc.priority, 'value') else tc.priority,
        "status": tc.status.value if hasattr(tc.status, 'value') else tc.status,
        "preconditions": tc.preconditions,
        "steps": tc.steps or [],
        "tags": tc.tags or [],
        "module": tc.module,
        "zentao_id": tc.zentao_id,
        "zentao_case_id": tc.zentao_case_id,
        "created_by": tc.created_by,
        "created_at": tc.created_at.isoformat() if tc.created_at else "",
        "updated_at": tc.updated_at.isoformat() if tc.updated_at else "",
    }
