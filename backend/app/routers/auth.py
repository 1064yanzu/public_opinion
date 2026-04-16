import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)
from app.dependencies import (
    get_db, get_current_user, get_password_hash, 
    verify_password, create_access_token
)
from app.models.user import User
from app.schemas import (
    UserCreate, UserLogin, UserResponse, UserUpdate, UserPasswordUpdate, Token, MessageResponse
)
from app.config import settings

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED,
             summary="用户注册", description="创建新用户账号")
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    用户注册
    
    - **username**: 用户名（3-50字符，唯一）
    - **email**: 邮箱地址（唯一）
    - **password**: 密码（至少6字符）
    """
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    try:
        # 创建用户
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    except Exception as e:
        await db.rollback()
        logger.error(f"注册过程中出现意外错误: {e}")
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")


@router.post("/login", response_model=Token, summary="用户登录", description="用户登录并获取访问令牌")
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    用户登录
    
    - **username**: 用户名
    - **password**: 密码
    
    返回 JWT 访问令牌
    """
    # 查询用户
    result = await db.execute(select(User).where(User.username == user_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    
    # 创建访问令牌
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse, summary="获取当前用户", description="获取当前登录用户信息")
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户的信息"""
    return current_user


@router.put("/me", response_model=UserResponse, summary="更新用户信息", description="更新当前用户信息")
async def update_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新当前用户信息
    
    - **email**: 新邮箱地址（可选）
    """
    if user_data.email:
        # 检查邮箱是否被其他用户使用
        result = await db.execute(
            select(User).where(User.email == user_data.email, User.id != current_user.id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="邮箱已被其他用户使用")
        current_user.email = user_data.email
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.post("/logout", response_model=MessageResponse, summary="用户登出", description="用户登出（客户端需删除令牌）")
async def logout(current_user: User = Depends(get_current_user)):
    """
    用户登出
    
    注意：JWT 是无状态的，服务端不会使令牌失效。
    客户端需要自行删除存储的令牌。
    """
    return MessageResponse(message="登出成功", success=True)


@router.put("/password", response_model=MessageResponse, summary="修改密码", description="修改当前用户密码")
async def update_password(
    payload: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """修改当前用户密码。"""
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="当前密码不正确")

    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=400, detail="新密码不能与当前密码相同")

    current_user.hashed_password = get_password_hash(payload.new_password)
    await db.commit()
    return MessageResponse(message="密码更新成功", success=True)
