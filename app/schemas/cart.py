# -*- coding: utf-8 -*-
"""
购物车请求/响应模式
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CartAddRequest(BaseModel):
    """加入购物车"""
    sku_id: int = Field(..., description="SKU ID")
    quantity: int = Field(1, ge=1, description="数量")


class CartUpdateRequest(BaseModel):
    """更新购物车（数量 / 选中状态）"""
    quantity: Optional[int] = Field(None, ge=1, description="数量")
    selected: Optional[int] = Field(None, ge=0, le=1, description="是否选中")


class CartItemOut(BaseModel):
    """购物车条目（含商品/SKU 冗余信息）"""
    id: int
    sku_id: int
    quantity: int
    selected: int
    product_id: int
    product_name: str
    cover_url: str
    sku_name: str
    price: float
    stock: int
    subtotal: float
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CartOut(BaseModel):
    """购物车整体视图"""
    items: List[CartItemOut]
    selected_total: float
    selected_count: int
