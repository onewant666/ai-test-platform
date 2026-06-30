"""认证 API"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import LoginReq, RegisterReq, LoginRes, UserInfo
from app.schemas.common import APIResponse
from app.services.auth_service import authenticate, register_user, get_user_info
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=APIResponse[UserInfo], status_code=201)
def register(req: RegisterReq, db: Session = Depends(get_db)):
    """
    用户注册。

    注册成功后直接返回用户信息，默认角色为 tester。
    - **username**: 用户名，3-64 字符，不可重复
    - **password**: 密码，6-64 字符
    - **email**: 邮箱（可选），不可重复
    """
    user_info = register_user(db, req)
    return APIResponse(data=user_info, message="注册成功")


@router.post("/login", response_model=APIResponse[LoginRes])
def login(req: LoginReq, db: Session = Depends(get_db)):
    """
    用户登录。

    使用用户名和密码获取 JWT Token。
    - Token 有效期 24 小时
    - Refresh Token 有效期 7 天
    """
    result = authenticate(db, req)
    return APIResponse(data=result)


@router.get("/me", response_model=APIResponse[UserInfo])
def me(current_user: User = Depends(get_current_user)):
    return APIResponse(data=get_user_info(current_user))


@router.post("/refresh", response_model=APIResponse[LoginRes])
def refresh(refresh_token: str, db: Session = Depends(get_db)):
    """刷新 Token（简化实现）"""
    from app.utils.security import decode_token, create_token
    try:
        payload = decode_token(refresh_token)
        user_id = int(payload["sub"])
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            raise Exception("用户不存在")
        token = create_token(user.id)
        return APIResponse(data=LoginRes(token=token, refresh_token=refresh_token, expires_in=86400))
    except Exception:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的 Refresh Token")
