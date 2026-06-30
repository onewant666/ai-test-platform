"""用例模型"""

from datetime import datetime
from sqlalchemy import String, Integer, Text, JSON, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class TestCaseStatus(str, enum.Enum):
    DRAFT = "draft"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    DEPRECATED = "deprecated"


class TestCasePriority(str, enum.Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class TestCase(Base):
    __tablename__ = "testcases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    priority: Mapped[TestCasePriority] = mapped_column(Enum(TestCasePriority), default=TestCasePriority.P2)
    status: Mapped[TestCaseStatus] = mapped_column(Enum(TestCaseStatus), default=TestCaseStatus.DRAFT)
    preconditions: Mapped[str] = mapped_column(Text, nullable=True)
    steps: Mapped[list] = mapped_column(JSON, default=list, comment="测试步骤 JSON 数组")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    module: Mapped[str] = mapped_column(String(128), nullable=True)
    zentao_id: Mapped[str] = mapped_column(String(64), nullable=True, comment="ZenTao case ID (e.g. 'case_1')")
    zentao_case_id: Mapped[int] = mapped_column(Integer, nullable=True, comment="Numeric ZenTao case ID")
    created_by: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关联
    project = relationship("Project", back_populates="testcases")
    executions = relationship("Execution", back_populates="testcase", lazy="dynamic")


class TestCaseStep(Base):
    """已废弃 — 步骤直接以 JSON 存储在 testcases.steps 中"""
    __tablename__ = "testcase_steps"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    testcase_id: Mapped[int] = mapped_column(Integer, ForeignKey("testcases.id"), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target: Mapped[str] = mapped_column(String(512), nullable=False)
    value: Mapped[str] = mapped_column(String(1024), nullable=True)
    expected: Mapped[str] = mapped_column(String(1024), nullable=True)
    timeout: Mapped[int] = mapped_column(Integer, default=30000)
