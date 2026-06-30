"""禅道同步日志模型"""

from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
import enum


class SyncType(str, enum.Enum):
    CASES_IMPORT = "cases_import"
    BUG_EXPORT = "bug_export"
    RESULT_WRITEBACK = "result_writeback"


class SyncDirection(str, enum.Enum):
    PULL = "pull"
    PUSH = "push"


class SyncStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class ZentaoSyncLog(Base):
    __tablename__ = "zentao_sync_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[SyncType] = mapped_column(Enum(SyncType), nullable=False)
    direction: Mapped[SyncDirection] = mapped_column(Enum(SyncDirection), nullable=False)
    status: Mapped[SyncStatus] = mapped_column(Enum(SyncStatus), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=True)
    records_affected: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
