"""执行记录模型"""

from datetime import datetime
from sqlalchemy import String, Integer, Text, JSON, DateTime, ForeignKey, Enum, Float, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class ExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TriggerType(str, enum.Enum):
    MANUAL = "manual"
    CRON = "cron"
    WEBHOOK = "zentao_webhook"
    API = "api"


class Execution(Base):
    __tablename__ = "executions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("testplans.id"), nullable=False, index=True)
    case_id: Mapped[int] = mapped_column(Integer, ForeignKey("testcases.id"), nullable=False)
    status: Mapped[ExecutionStatus] = mapped_column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING)
    trigger_type: Mapped[TriggerType] = mapped_column(Enum(TriggerType), default=TriggerType.MANUAL)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    duration: Mapped[float] = mapped_column(Float, nullable=True)  # 执行耗时（ms）
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    screenshots: Mapped[list] = mapped_column(JSON, default=list)
    dom_snapshot: Mapped[str] = mapped_column(Text, nullable=True)
    log: Mapped[str] = mapped_column(Text, nullable=True)
    steps: Mapped[list] = mapped_column(JSON, default=list)  # 每步执行结果
    zentao_bug_id: Mapped[int] = mapped_column(Integer, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    executed_by: Mapped[str] = mapped_column(String(32), default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 关联
    testplan = relationship("TestPlan", back_populates="executions")
    testcase = relationship("TestCase", back_populates="executions")


class ExecutionStep(Base):
    """已废弃 — 执行步骤直接以 JSON 存储在 executions.steps 中"""
    __tablename__ = "execution_steps"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    execution_id: Mapped[int] = mapped_column(Integer, ForeignKey("executions.id"), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    screenshot: Mapped[str] = mapped_column(String(512), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    duration: Mapped[float] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
