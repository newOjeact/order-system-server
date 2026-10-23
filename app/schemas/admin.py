# -*- coding: utf-8 -*-
"""
管理后台：管理员账号 / 登录 / 订单管理 / 数据看板 响应模式
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    """管理员登录请求"""
    username: str = Field(..., description="管理员用户名")
    password: str = Field(..., description="密码")


class AdminOut(BaseModel):
    """管理员信息"""
    id: int
    username: str
    role: str
    status: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminTokenOut(BaseModel):
    """管理员登录成功返回的令牌"""
    access_token: str
    token_type: str = "bearer"
    admin: AdminOut


class AdminCreateRequest(BaseModel):
    """创建管理员（super_admin 权限）"""
    username: str = Field(..., min_length=3, max_length=50, description="管理员用户名")
    password: str = Field(..., min_length=6, max_length=50, description="初始密码")
    role: str = Field("admin", description="角色：super_admin / admin")


class AdminUpdateRequest(BaseModel):
    """更新管理员：角色 / 状态 / 重置密码（super_admin 权限）"""
    role: Optional[str] = Field(None, description="角色：super_admin / admin")
    status: Optional[int] = Field(None, description="状态：1 启用 0 禁用")
    password: Optional[str] = Field(None, min_length=6, max_length=50, description="重置密码")


class AdminOrderStatusRequest(BaseModel):
    """管理端修改订单状态"""
    status: int = Field(..., description="目标状态：0 待付款 1 已付款 2 已发货 3 已完成 4 已取消")


class DashboardSummaryOut(BaseModel):
    """数据看板汇总"""
    today_sales: float
    total_sales: float
    today_order_count: int
    total_order_count: int
    user_count: int
    product_count: int
    low_stock_count: int
    low_stock_items: List["LowStockItemOut"] = []


class LowStockItemOut(BaseModel):
    """低库存 SKU 预警项"""
    sku_id: int
    product_id: int
    product_name: str
    sku_name: str
    stock: int


class DashboardTrendItem(BaseModel):
    """销售趋势单日数据"""
    date: str
    order_count: int
    sales_amount: float


DashboardSummaryOut.model_rebuild()
