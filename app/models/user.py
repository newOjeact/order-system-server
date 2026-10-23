# -*- coding: utf-8 -*-
"""
用户模型
"""
from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    openid = Column(String(64), unique=True, nullable=True, index=True, comment="微信 openid（微信一键登录用户标识）")
    password_hash = Column(String(128), nullable=False, comment="密码哈希")
    nickname = Column(String(50), default="", comment="昵称")
    avatar = Column(String(255), default="", comment="头像 URL")
    phone = Column(String(20), default="", comment="手机号")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
