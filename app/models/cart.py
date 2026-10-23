# -*- coding: utf-8 -*-
"""
购物车模型
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint, func

from app.core.database import Base


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("user_id", "sku_id", name="uq_user_sku"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户 ID")
    sku_id = Column(Integer, ForeignKey("skus.id"), nullable=False, comment="SKU ID")
    quantity = Column(Integer, default=1, comment="数量")
    selected = Column(Integer, default=1, comment="是否选中：1 选中 0 未选中")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
