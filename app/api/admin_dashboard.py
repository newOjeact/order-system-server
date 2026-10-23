# -*- coding: utf-8 -*-
"""
管理后台：数据看板（汇总指标 + 销售趋势）
"""
from datetime import date, datetime, time, timedelta
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.admin import Admin
from app.models.order import Order
from app.models.product import Product, Sku
from app.models.user import User
from app.schemas.admin import (
    DashboardSummaryOut,
    DashboardTrendItem,
    LowStockItemOut,
)

router = APIRouter(prefix="/api/admin/dashboard", tags=["管理后台-数据看板"])

# 已支付订单状态：1 已付款 2 已发货 3 已完成
PAID_STATUS = (1, 2, 3)


@router.get("/summary", summary="数据看板汇总", response_model=DashboardSummaryOut)
def dashboard_summary(
    low_stock_threshold: int = Query(10, ge=0, description="低库存预警阈值"),
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """今日/累计销售额、订单数、用户数、商品数、低库存预警"""
    today_start = datetime.combine(date.today(), time.min)

    today_sales = db.query(func.coalesce(func.sum(Order.pay_amount), 0)).filter(
        Order.status.in_(PAID_STATUS), Order.paid_at >= today_start
    ).scalar() or 0
    total_sales = db.query(func.coalesce(func.sum(Order.pay_amount), 0)).filter(
        Order.status.in_(PAID_STATUS)
    ).scalar() or 0

    today_order_count = db.query(func.count(Order.id)).filter(
        Order.created_at >= today_start
    ).scalar() or 0
    total_order_count = db.query(func.count(Order.id)).scalar() or 0
    user_count = db.query(func.count(User.id)).scalar() or 0
    product_count = db.query(func.count(Product.id)).scalar() or 0

    low_stock_skus = (
        db.query(Sku)
        .filter(Sku.stock <= low_stock_threshold)
        .order_by(Sku.stock.asc(), Sku.id.asc())
        .all()
    )
    product_ids = {s.product_id for s in low_stock_skus}
    products = {
        p.id: p.name
        for p in db.query(Product).filter(Product.id.in_(product_ids)).all()
    } if product_ids else {}

    return DashboardSummaryOut(
        today_sales=float(today_sales),
        total_sales=float(total_sales),
        today_order_count=today_order_count,
        total_order_count=total_order_count,
        user_count=user_count,
        product_count=product_count,
        low_stock_count=len(low_stock_skus),
        low_stock_items=[
            LowStockItemOut(
                sku_id=s.id,
                product_id=s.product_id,
                product_name=products.get(s.product_id, ""),
                sku_name=s.name,
                stock=s.stock,
            )
            for s in low_stock_skus
        ],
    )


@router.get("/trend", summary="销售趋势（近7日/30日）", response_model=List[DashboardTrendItem])
def dashboard_trend(
    days: int = Query(7, ge=1, le=90, description="统计天数：7 或 30"),
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """按日返回已支付订单数与销售额（无订单日期补零）"""
    start_date = date.today() - timedelta(days=days - 1)
    start_dt = datetime.combine(start_date, time.min)

    rows = (
        db.query(
            func.date(Order.paid_at).label("day"),
            func.count(Order.id).label("order_count"),
            func.coalesce(func.sum(Order.pay_amount), 0).label("sales_amount"),
        )
        .filter(Order.status.in_(PAID_STATUS), Order.paid_at >= start_dt)
        .group_by(func.date(Order.paid_at))
        .all()
    )
    stat = {r.day: (r.order_count, float(r.sales_amount)) for r in rows}

    items = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        day_str = d.strftime("%Y-%m-%d")
        order_count, sales_amount = stat.get(day_str, (0, 0.0))
        items.append(DashboardTrendItem(
            date=day_str,
            order_count=order_count,
            sales_amount=sales_amount,
        ))
    return items
