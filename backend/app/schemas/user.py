"""
用户相关 Pydantic Schemas
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")


class UserCreate(UserBase):
    """创建用户请求"""
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserUpdate(BaseModel):
    """更新用户信息"""
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    is_active: Optional[bool] = Field(None, description="是否激活")


class UserPasswordUpdate(BaseModel):
    """修改密码请求"""
    current_password: str = Field(..., min_length=6, max_length=100, description="当前密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


class UserResponse(UserBase):
    """用户响应"""
    id: int = Field(..., description="用户ID")
    is_active: bool = Field(..., description="是否激活")
    is_superuser: bool = Field(..., description="是否是超级用户")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token 响应"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    user: UserResponse = Field(..., description="用户信息")


class TokenData(BaseModel):
    """Token 数据"""
    username: Optional[str] = None
