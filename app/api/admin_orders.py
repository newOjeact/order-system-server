# -*- coding: utf-8 -*-
"""
管理后台：订单管理（分页列表/详情/状态流转）
状态：0 待付款 1 已付款 2 已发货 3 已完成 4 已取消
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_admin
from app.api.orders import STATUS_TEXT, _order_out
from app.core.database import get_db
from app.models.admin import Admin
from app.models.order import Order
from app.models.product import Product, Sku
from app.schemas.admin import AdminOrderStatusRequest
from app.schemas.order import OrderOut

router = APIRouter(prefix="/api/admin/orders", tags=["管理后台-订单"])


class OrderListOut(BaseModel):
    """管理端订单分页列表"""
    total: int
    page: int
    page_size: int
    items: list[OrderOut] = []


# 状态流转规则：{当前状态: 允许的目标状态集合}
ALLOWED_TRANSITIONS = {
    0: {1, 4},   # 待付款 -> 已付款(确认收款) / 已取消
    1: {2, 4},   # 已付款 -> 已发货 / 已取消
    2: {3, 4},   # 已发货 -> 已完成 / 已取消
    3: set(),    # 已完成：终态
    4: set(),    # 已取消：终态
}


def _get_order(db: Session, order_id: int) -> Order:
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id)
        .first()
    )
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order


@router.get("", summary="订单列表（分页/状态筛选）", response_model=OrderListOut)
def list_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    status: Optional[int] = Query(None, description="状态：0 待付款 1 已付款 2 已发货 3 已完成 4 已取消"),
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """管理端订单列表：全部用户订单，按创建时间倒序"""
    query = db.query(Order)
    if status is not None:
        query = query.filter(Order.status == status)
    total = query.count()
    orders = (
        query.options(joinedload(Order.items))
        .order_by(Order.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return OrderListOut(
        total=total,
        page=page,
        page_size=page_size,
        items=[_order_out(o) for o in orders],
    )


@router.get("/{order_id}", summary="订单详情", response_model=OrderOut)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    return _order_out(_get_order(db, order_id))


@router.put("/{order_id}/status", summary="修改订单状态", response_model=OrderOut)
def update_order_status(
    order_id: int,
    body: AdminOrderStatusRequest,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """按状态流转规则修改订单状态；流转到已付款/已发货/已完成时写入对应时间戳，取消时回补库存"""
    order = _get_order(db, order_id)
    target = body.status
    if target not in (0, 1, 2, 3, 4):
        raise HTTPException(status_code=400, detail="状态仅支持 0-4")
    if target not in ALLOWED_TRANSITIONS.get(order.status, set()):
        current_text = STATUS_TEXT.get(order.status, "未知")
        target_text = STATUS_TEXT.get(target, "未知")
        raise HTTPException(
            status_code=400,
            detail=f"不允许从「{current_text}」流转到「{target_text}」",
        )

    now = datetime.now()
    if target == 1:
        order.paid_at = order.paid_at or now
    elif target == 2:
        order.shipped_at = order.shipped_at or now
    elif target == 3:
        order.completed_at = order.completed_at or now
    elif target == 4:
        # 取消订单：回补库存、扣回销量
        for item in order.items:
            if item.sku_id:
                sku = db.query(Sku).filter(Sku.id == item.sku_id).first()
                if sku:
                    sku.stock += item.quantity
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product.stock += item.quantity
                product.sales = max(0, product.sales - item.quantity)

    order.status = target
    db.commit()
    db.refresh(order)
    return _order_out(_get_order(db, order.id))
