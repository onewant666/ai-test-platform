"""测试计划相关 Schema"""

from pydantic import BaseModel
from datetime import datetime


class TestPlanCreate(BaseModel):
    project_id: int
    name: str
    description: str | None = None
    case_ids: list[int] = []
    cron_expr: str | None = None
    max_retries: int = 2
    timeout: int = 600


class TestPlanUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    case_ids: list[int] | None = None
    status: str | None = None
    cron_expr: str | None = None
    max_retries: int | None = None
    timeout: int | None = None


class TestPlanResponse(BaseModel):
    id: int
    project_id: int
    name: str
    description: str | None = None
    case_ids: list
    case_count: int = 0
    status: str
    cron_expr: str | None = None
    max_retries: int
    timeout: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
