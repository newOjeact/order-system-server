# -*- coding: utf-8 -*-
"""
管理后台：商品管理请求/响应模式
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SkuEditRequest(BaseModel):
    """SKU 编辑项：有 id 表示更新已有 SKU，无 id 表示新增"""
    id: Optional[int] = Field(None, description="SKU ID（新增时为空）")
    name: str = Field(..., description="规格名称")
    price: float = Field(..., description="规格价格")
    stock: int = Field(..., ge=0, description="规格库存")


class AdminSkuOut(BaseModel):
    id: int
    product_id: int
    name: str
    price: float
    stock: int

    class Config:
        from_attributes = True


class AdminProductCreateRequest(BaseModel):
    """创建商品"""
    category_id: int = Field(..., description="所属分类 ID")
    name: str = Field(..., max_length=100, description="商品名称")
    cover_url: str = Field("", description="封面图 URL")
    description: str = Field("", description="商品描述")
    price: float = Field(..., ge=0, description="默认价格")
    stock: int = Field(0, ge=0, description="总库存（未传 SKU 时生效）")
    status: int = Field(1, description="状态：1 上架 0 下架")
    skus: List[SkuEditRequest] = Field([], description="SKU 列表（可选）")


class AdminProductUpdateRequest(BaseModel):
    """更新商品：仅传入的字段生效；skus 传入时全量同步 SKU"""
    category_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=100)
    cover_url: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)
    status: Optional[int] = Field(None, description="状态：1 上架 0 下架")
    skus: Optional[List[SkuEditRequest]] = Field(None, description="全量 SKU 列表（新增/更新/删除）")


class AdminProductOut(BaseModel):
    """管理端商品详情（含 SKU）"""
    id: int
    category_id: int
    category_name: str
    name: str
    cover_url: str
    description: str
    price: float
    stock: int
    sales: int
    status: int
    created_at: Optional[datetime] = None
    skus: List[AdminSkuOut] = []


class AdminProductListOut(BaseModel):
    """管理端商品分页列表"""
    total: int
    page: int
    page_size: int
    items: List[AdminProductOut] = []
