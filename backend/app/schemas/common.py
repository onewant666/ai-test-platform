"""通用 Schema"""

from typing import TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedReq(BaseModel):
    page: int = 1
    limit: int = 20
    keyword: str | None = None
    order_by: str | None = None
    order: str = "desc"


class PaginatedRes(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    limit: int
    total_pages: int


class APIResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: T
