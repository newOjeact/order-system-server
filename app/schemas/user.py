# -*- coding: utf-8 -*-
"""
用户相关请求/响应模式
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    nickname: Optional[str] = Field("", description="昵称")


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class WxLoginRequest(BaseModel):
    """微信一键登录请求"""
    code: str = Field(..., min_length=1, description="微信登录凭证 code（uni.login 获取）")


class UserOut(BaseModel):
    """用户信息（脱敏）"""
    id: int
    username: str
    nickname: str
    avatar: str
    phone: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    """登录成功返回的令牌"""
    access_token: str
    token_type: str = "bearer"
    user: UserOut
