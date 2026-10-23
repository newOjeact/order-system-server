# -*- coding: utf-8 -*-
"""
管理员模型
角色：super_admin 超级管理员（可管理管理员账号），admin 普通管理员（仅管业务数据）
状态：1 启用 0 禁用
"""
from sqlalchemy import Column, DateTime, Integer, String, func

from app.core.database import Base


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment="管理员用户名")
    password_hash = Column(String(128), nullable=False, comment="密码哈希")
    role = Column(String(20), default="admin", comment="角色：super_admin / admin")
    status = Column(Integer, default=1, comment="状态：1 启用 0 禁用")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
