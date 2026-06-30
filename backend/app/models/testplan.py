"""测试计划模型"""

from datetime import datetime
from sqlalchemy import String, Integer, Text, JSON, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class PlanStatus(str, enum.Enum):
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TestPlan(Base):
    __tablename__ = "testplans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    case_ids: Mapped[list] = mapped_column(JSON, default=list, comment="关联用例 ID 列表")
    status: Mapped[PlanStatus] = mapped_column(Enum(PlanStatus), default=PlanStatus.DRAFT)
    cron_expr: Mapped[str] = mapped_column(String(64), nullable=True)
    max_retries: Mapped[int] = mapped_column(Integer, default=2)
    timeout: Mapped[int] = mapped_column(Integer, default=600)
    created_by: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关联
    project = relationship("Project", back_populates="testplans")
    executions = relationship("Execution", back_populates="testplan", lazy="dynamic")
