# -*- coding: utf-8 -*-
"""
订单模型：订单主表 + 订单明细表
订单状态流转：待付款(0) -> 已付款(1) -> 已发货(2) -> 已完成(3)；已取消(4)
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(32), unique=True, nullable=False, index=True, comment="订单号")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="下单用户 ID")
    address_id = Column(Integer, ForeignKey("addresses.id"), nullable=True, comment="收货地址 ID")
    receiver = Column(String(50), default="", comment="收货人（下单时快照）")
    phone = Column(String(20), default="", comment="联系电话（快照）")
    address_text = Column(String(255), default="", comment="收货地址（快照）")
    total_amount = Column(Numeric(10, 2), nullable=False, default=0, comment="订单总额")
    pay_amount = Column(Numeric(10, 2), nullable=False, default=0, comment="实付金额（MVP 与总额一致）")
    status = Column(Integer, default=0, comment="状态：0 待付款 1 已付款 2 已发货 3 已完成 4 已取消")
    remark = Column(String(255), default="", comment="订单备注")
    paid_at = Column(DateTime, nullable=True, comment="支付时间")
    shipped_at = Column(DateTime, nullable=True, comment="发货时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="selectin")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True, comment="所属订单 ID")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, comment="商品 ID")
    product_name = Column(String(100), default="", comment="商品名称（快照）")
    sku_id = Column(Integer, ForeignKey("skus.id"), nullable=True, comment="SKU ID")
    sku_name = Column(String(50), default="", comment="规格名称（快照）")
    cover_url = Column(String(255), default="", comment="商品封面（快照）")
    price = Column(Numeric(10, 2), nullable=False, default=0, comment="成交单价")
    quantity = Column(Integer, default=1, comment="购买数量")

    order = relationship("Order", back_populates="items")
