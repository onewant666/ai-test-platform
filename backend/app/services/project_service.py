"""项目服务"""

from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from app.models.project import Project
from app.schemas.common import PaginatedReq, PaginatedRes


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    status: str = "active"
    zentao_product_id: int | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    zentao_product_id: int | None = None


def list_projects(
    db: Session,
    pagination: PaginatedReq,
) -> PaginatedRes:
    query = db.query(Project)

    if pagination.keyword:
        keyword = f"%{pagination.keyword}%"
        query = query.filter(
            or_(Project.name.like(keyword), Project.description.like(keyword))
        )

    total = query.count()
    total_pages = max(1, (total + pagination.limit - 1) // pagination.limit)

    order_col = getattr(Project, pagination.order_by or "updated_at", Project.updated_at)
    if pagination.order == "asc":
        query = query.order_by(order_col.asc())
    else:
        query = query.order_by(order_col.desc())

    items = query.offset((pagination.page - 1) * pagination.limit).limit(pagination.limit).all()

    return PaginatedRes(
        items=[_to_response(p) for p in items],
        total=total,
        page=pagination.page,
        limit=pagination.limit,
        total_pages=total_pages,
    )


def get_project(db: Session, project_id: int) -> Project:
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="项目不存在")
    return p


def create_project(db: Session, data: ProjectCreate, user_id: int) -> Project:
    p = Project(
        name=data.name,
        description=data.description,
        status=data.status,
        zentao_product_id=data.zentao_product_id,
        created_by=user_id,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def update_project(db: Session, p: Project, data: ProjectUpdate) -> Project:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(p, key, value)
    db.commit()
    db.refresh(p)
    return p


def delete_project(db: Session, p: Project) -> None:
    db.delete(p)
    db.commit()


def _to_response(p: Project) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "status": p.status,
        "zentao_product_id": p.zentao_product_id,
        "created_by": p.created_by,
        "created_at": p.created_at.isoformat() if p.created_at else "",
        "updated_at": p.updated_at.isoformat() if p.updated_at else "",
    }
