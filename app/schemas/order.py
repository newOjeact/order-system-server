# -*- coding: utf-8 -*-
"""
订单请求/响应模式
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class OrderCreateRequest(BaseModel):
    """创建订单：支持从购物车结算或直接购买"""
    address_id: int = Field(..., description="收货地址 ID")
    source: str = Field("cart", description="订单来源：cart 购物车结算 / buy 立即购买")
    sku_id: Optional[int] = Field(None, description="立即购买时的 SKU ID")
    quantity: Optional[int] = Field(None, ge=1, description="立即购买时的数量")
    cart_item_ids: Optional[List[int]] = Field(None, description="结算的购物车条目 ID 列表（空表示全部选中项）")
    remark: str = Field("", max_length=255, description="订单备注")


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    sku_id: Optional[int] = None
    sku_name: str
    cover_url: str
    price: float
    quantity: int

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    order_no: str
    receiver: str
    phone: str
    address_text: str
    total_amount: float
    pay_amount: float
    status: int
    status_text: str
    remark: str
    paid_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    items: List[OrderItemOut] = []

    class Config:
        from_attributes = True


class PayRequest(BaseModel):
    """模拟支付请求"""
    order_id: int = Field(..., description="订单 ID")
    pay_channel: str = Field("wechat", description="支付渠道（MVP 仅 wechat 模拟）")


class PayOut(BaseModel):
    """模拟支付结果"""
    success: bool
    message: str
    mock: bool = True
    order_id: Optional[int] = None
