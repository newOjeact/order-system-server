# -*- coding: utf-8 -*-
"""
订单模块：创建订单（金额计算/库存扣减）、订单列表/详情、状态流转、模拟支付
状态：0 待付款 1 已付款 2 已发货 3 已完成 4 已取消
"""
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.address import Address
from app.models.cart import CartItem
from app.models.order import Order, OrderItem
from app.models.product import Product, Sku
from app.models.user import User
from app.schemas.order import OrderCreateRequest, OrderItemOut, OrderOut

router = APIRouter(prefix="/api/orders", tags=["订单"])

STATUS_TEXT = {
    0: "待付款",
    1: "已付款",
    2: "已发货",
    3: "已完成",
    4: "已取消",
}


def _gen_order_no() -> str:
    """生成订单号：时间戳 + 随机串"""
    return datetime.now().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:8].upper()


def _order_out(order: Order) -> OrderOut:
    return OrderOut(
        id=order.id,
        order_no=order.order_no,
        receiver=order.receiver,
        phone=order.phone,
        address_text=order.address_text,
        total_amount=float(order.total_amount),
        pay_amount=float(order.pay_amount),
        status=order.status,
        status_text=STATUS_TEXT.get(order.status, "未知"),
        remark=order.remark,
        paid_at=order.paid_at,
        shipped_at=order.shipped_at,
        completed_at=order.completed_at,
        created_at=order.created_at,
        items=[
            OrderItemOut(
                id=i.id,
                product_id=i.product_id,
                product_name=i.product_name,
                sku_id=i.sku_id,
                sku_name=i.sku_name,
                cover_url=i.cover_url,
                price=float(i.price),
                quantity=i.quantity,
            )
            for i in order.items
        ],
    )


@router.post("", summary="创建订单", response_model=OrderOut)
def create_order(
    body: OrderCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """创建订单：
    - source=cart：结算购物车中选中的条目（可指定 cart_item_ids）
    - source=buy：立即购买指定 SKU
    创建成功后扣减库存、清空对应购物车条目。
    """
    address = db.query(Address).filter(Address.id == body.address_id, Address.user_id == user.id).first()
    if address is None:
        raise HTTPException(status_code=404, detail="收货地址不存在")

    # 组装待下单条目：(sku, quantity, cart_item)
    pending: list = []
    if body.source == "buy":
        if body.sku_id is None or body.quantity is None:
            raise HTTPException(status_code=400, detail="立即购买需要提供 sku_id 和 quantity")
        sku = db.query(Sku).filter(Sku.id == body.sku_id).first()
        if sku is None:
            raise HTTPException(status_code=404, detail="SKU 不存在")
        pending.append((sku, body.quantity, None))
    else:
        cart_query = db.query(CartItem).filter(CartItem.user_id == user.id, CartItem.selected == 1)
        if body.cart_item_ids:
            cart_query = cart_query.filter(CartItem.id.in_(body.cart_item_ids))
        cart_items = cart_query.all()
        if not cart_items:
            raise HTTPException(status_code=400, detail="请先选择要结算的购物车商品")
        for item in cart_items:
            sku = db.query(Sku).filter(Sku.id == item.sku_id).first()
            if sku is None:
                raise HTTPException(status_code=400, detail="购物车中存在已失效商品，请重新选购")
            pending.append((sku, item.quantity, item))

    # 校验库存并计算金额
    total = 0.0
    for sku, quantity, _ in pending:
        if quantity > sku.stock:
            raise HTTPException(status_code=400, detail=f"商品规格「{sku.name}」库存不足，仅剩 {sku.stock} 件")
        total += float(sku.price) * quantity

    # 创建订单与明细（快照商品名称/价格/地址）
    order = Order(
        order_no=_gen_order_no(),
        user_id=user.id,
        address_id=address.id,
        receiver=address.receiver,
        phone=address.phone,
        address_text=f"{address.province}{address.city}{address.district}{address.detail}",
        total_amount=round(total, 2),
        pay_amount=round(total, 2),
        status=0,
        remark=body.remark,
    )
    db.add(order)
    db.flush()

    for sku, quantity, _ in pending:
        product = db.query(Product).filter(Product.id == sku.product_id).first()
        db.add(OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            sku_id=sku.id,
            sku_name=sku.name,
            cover_url=product.cover_url,
            price=sku.price,
            quantity=quantity,
        ))
        # 扣减库存、累加销量
        sku.stock -= quantity
        product.stock -= quantity
        product.sales += quantity

    # 清空已结算的购物车条目
    for _, _, cart_item in pending:
        if cart_item is not None:
            db.delete(cart_item)

    db.commit()
    db.refresh(order)
    order = db.query(Order).options(joinedload(Order.items)).filter(Order.id == order.id).first()
    return _order_out(order)


@router.get("", summary="订单列表", response_model=List[OrderOut])
def list_orders(
    status: Optional[int] = Query(None, description="按状态过滤：0 待付款 1 已付款 2 已发货 3 已完成 4 已取消"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """当前用户订单列表，按创建时间倒序"""
    query = db.query(Order).options(joinedload(Order.items)).filter(Order.user_id == user.id)
    if status is not None:
        query = query.filter(Order.status == status)
    orders = query.order_by(Order.id.desc()).all()
    return [_order_out(o) for o in orders]


@router.get("/{order_id}", summary="订单详情", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id, Order.user_id == user.id)
        .first()
    )
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    return _order_out(order)


@router.post("/{order_id}/cancel", summary="取消订单", response_model=OrderOut)
def cancel_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """仅待付款订单可取消；取消后回补库存并扣回销量"""
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id, Order.user_id == user.id)
        .first()
    )
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != 0:
        raise HTTPException(status_code=400, detail="当前状态不可取消")
    for item in order.items:
        if item.sku_id:
            sku = db.query(Sku).filter(Sku.id == item.sku_id).first()
            if sku:
                sku.stock += item.quantity
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock += item.quantity
            product.sales = max(0, product.sales - item.quantity)
    order.status = 4
    db.commit()
    db.refresh(order)
    return _order_out(order)


@router.post("/{order_id}/confirm", summary="确认收货（完成订单）", response_model=OrderOut)
def confirm_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """已发货订单可确认收货，状态流转为已完成"""
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id, Order.user_id == user.id)
        .first()
    )
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != 2:
        raise HTTPException(status_code=400, detail="仅已发货订单可确认收货")
    order.status = 3
    order.completed_at = datetime.now()
    db.commit()
    db.refresh(order)
    return _order_out(order)
