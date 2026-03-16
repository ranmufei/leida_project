"""
认证API端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserInDB
from app.schemas.token import Token
from app.schemas.common import ApiResponse

router = APIRouter()


@router.post("/login", response_model=ApiResponse[Token])
async def login(
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    """
    用户登录

    返回JWT访问令牌
    """
    # 查找用户
    user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")

    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )

    # 更新最后登录时间
    from datetime import datetime
    user.last_login = datetime.now()
    db.commit()

    return ApiResponse(
        code=200,
        message="登录成功",
        data=Token(
            access_token=access_token,
            refresh_token=access_token,  # 简化版本，使用同一个token
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    )


@router.post("/register", response_model=ApiResponse[UserInDB])
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    用户注册
    """
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    # 创建用户
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return ApiResponse(
        code=201,
        message="注册成功",
        data=new_user
    )


@router.post("/logout", response_model=ApiResponse)
async def logout():
    """
    用户登出

    由于使用JWT无状态认证，登出主要在客户端处理（删除token）
    服务端可以添加token到黑名单（如果实现的话）
    """
    return ApiResponse(
        code=200,
        message="登出成功",
        data={
            "message": "请在客户端删除存储的token"
        }
    )
