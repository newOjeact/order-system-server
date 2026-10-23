# -*- coding: utf-8 -*-
"""
商品与 SKU 响应模式
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class SkuOut(BaseModel):
    id: int
    product_id: int
    name: str
    price: float
    stock: int

    class Config:
        from_attributes = True


class ProductListItem(BaseModel):
    """商品列表项（不含完整描述）"""
    id: int
    category_id: int
    category_name: str
    name: str
    cover_url: str
    price: float
    stock: int
    sales: int
    status: int

    class Config:
        from_attributes = True


class ProductDetail(ProductListItem):
    """商品详情（含描述与 SKU 列表）"""
    description: str
    skus: List[SkuOut] = []
    created_at: Optional[datetime] = None
