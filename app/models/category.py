# -*- coding: utf-8 -*-
"""
商品分类模型
"""
from sqlalchemy import Column, DateTime, Integer, String, func

from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, comment="分类名称")
    icon = Column(String(255), default="", comment="分类图标 URL")
    sort_order = Column(Integer, default=0, comment="排序值（越小越靠前）")
    status = Column(Integer, default=1, comment="状态：1 上架 0 下架")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
