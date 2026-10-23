# -*- coding: utf-8 -*-
"""
收货地址模型
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from app.core.database import Base


class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="所属用户 ID")
    receiver = Column(String(50), nullable=False, comment="收货人姓名")
    phone = Column(String(20), nullable=False, comment="联系电话")
    province = Column(String(50), default="", comment="省")
    city = Column(String(50), default="", comment="市")
    district = Column(String(50), default="", comment="区/县")
    detail = Column(String(255), nullable=False, comment="详细地址")
    is_default = Column(Integer, default=0, comment="是否默认：1 默认 0 非默认")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
