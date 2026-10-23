# -*- coding: utf-8 -*-
"""
支付模块：微信支付留桩接口（模拟支付成功）
MVP 阶段不接真实微信支付，直接返回成功并更新订单状态。
后期接入真实支付时，在此替换为统一下单/支付回调逻辑。
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.order import Order
from app.models.user import User
from app.schemas.order import PayOut, PayRequest

router = APIRouter(prefix="/api/pay", tags=["支付"])


@router.post("/wechat/mock", summary="模拟微信支付（桩接口）", response_model=PayOut)
def mock_wechat_pay(
    body: PayRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """模拟支付：
    - 仅待付款订单可支付
    - 支付成功后订单状态 0 -> 1（已付款）
    - 真实微信支付接入点：统一下单 / 支付回调
    """
    order = db.query(Order).filter(Order.id == body.order_id, Order.user_id == user.id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != 0:
        raise HTTPException(status_code=400, detail="订单状态异常，无法支付")
    order.status = 1
    order.paid_at = datetime.now()
    db.commit()
    return PayOut(
        success=True,
        message=f"模拟支付成功，订单 {order.order_no} 已付款",
        mock=True,
        order_id=order.id,
    )
