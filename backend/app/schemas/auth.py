"""认证相关 Schema"""

from pydantic import BaseModel, Field


class LoginReq(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=64)


class RegisterReq(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, description="用户名（3-64字符）")
    password: str = Field(..., min_length=6, max_length=64, description="密码（6-64字符）")
    email: str | None = Field(None, max_length=128, description="邮箱（可选）")


class LoginRes(BaseModel):
    token: str
    refresh_token: str
    expires_in: int


class TokenPayload(BaseModel):
    sub: str   # user id
    exp: int   # expire timestamp


class UserInfo(BaseModel):
    id: int
    username: str
    email: str | None = None
    avatar: str | None = None
    role: str
    zentao_account: str | None = None
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True
