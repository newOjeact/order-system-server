# -*- coding: utf-8 -*-
"""
商品分类响应模式
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CategoryOut(BaseModel):
    id: int
    name: str
    icon: str
    sort_order: int
    status: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
