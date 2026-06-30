"""用例相关 Schema"""

from pydantic import BaseModel, Field
from datetime import datetime


class TestStepSchema(BaseModel):
    seq: int
    action: str
    target: str
    value: str | None = None
    expected: str
    timeout: int | None = 30000


class TestCaseCreate(BaseModel):
    project_id: int
    title: str = Field(..., min_length=1, max_length=256)
    description: str | None = None
    priority: str = "P2"
    status: str = "draft"
    preconditions: str | None = None
    steps: list[TestStepSchema] = []
    tags: list[str] = []
    module: str | None = None
    zentao_id: int | None = None
    zentao_case_id: str | None = None


class TestCaseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    preconditions: str | None = None
    steps: list[TestStepSchema] | None = None
    tags: list[str] | None = None
    module: str | None = None
    zentao_id: int | None = None
    zentao_case_id: str | None = None


class TestCaseResponse(BaseModel):
    id: int
    project_id: int
    title: str
    description: str | None = None
    priority: str
    status: str
    preconditions: str | None = None
    steps: list
    tags: list
    module: str | None = None
    zentao_id: int | None = None
    zentao_case_id: str | None = None
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AIGenerateStepsReq(BaseModel):
    description: str = Field(..., min_length=10, description="自然语言描述的测试场景")


class AIGenerateStepsRes(BaseModel):
    steps: list[TestStepSchema]
