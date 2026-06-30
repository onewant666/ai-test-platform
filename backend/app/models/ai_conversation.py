"""AI 对话记录模型"""

from datetime import datetime
from sqlalchemy import Integer, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AIConversation(Base):
    __tablename__ = "ai_conversations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    messages: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
