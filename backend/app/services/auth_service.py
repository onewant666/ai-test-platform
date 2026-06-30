"""认证服务"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, UserRole
from app.utils.security import hash_password, verify_password, create_token
from app.schemas.auth import LoginReq, LoginRes, RegisterReq, UserInfo
from app.config import get_settings

settings = get_settings()


def authenticate(db: Session, req: LoginReq) -> LoginRes:
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")

    token = create_token(user.id)
    refresh_token = create_token(user.id, expires_minutes=settings.jwt_expire_minutes * 7)

    return LoginRes(
        token=token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_expire_minutes * 60,
    )


def get_user_info(user: User) -> UserInfo:
    return UserInfo(
        id=user.id,
        username=user.username,
        email=user.email,
        avatar=user.avatar,
        role=user.role.value,
        zentao_account=user.zentao_account,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else "",
    )


def register_user(db: Session, req: RegisterReq) -> UserInfo:
    """注册新用户"""
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已被占用")

    # 检查邮箱是否已存在
    if req.email:
        existing_email = db.query(User).filter(User.email == req.email).first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="邮箱已被占用")

    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        email=req.email,
        role=UserRole.TESTER,  # 新注册用户默认为 tester
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return get_user_info(user)


def create_initial_admin(db: Session):
    """初始化超级管理员（如果不存在）"""
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            password_hash=hash_password("123456"),
            email="admin@example.com",
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
