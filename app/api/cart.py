# -*- coding: utf-8 -*-
"""
购物车模块：加入 / 列表 / 修改 / 删除（需登录）
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.cart import CartItem
from app.models.product import Product, Sku
from app.models.user import User
from app.schemas.cart import CartAddRequest, CartItemOut, CartOut, CartUpdateRequest

router = APIRouter(prefix="/api/cart", tags=["购物车"])


def _item_out(item: CartItem, sku: Sku, product: Product) -> CartItemOut:
    return CartItemOut(
        id=item.id,
        sku_id=item.sku_id,
        quantity=item.quantity,
        selected=item.selected,
        product_id=product.id,
        product_name=product.name,
        cover_url=product.cover_url,
        sku_name=sku.name,
        price=float(sku.price),
        stock=sku.stock,
        subtotal=float(sku.price) * item.quantity,
    )


@router.post("/add", summary="加入购物车", response_model=CartItemOut)
def add_to_cart(body: CartAddRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """加入购物车；同一 SKU 已存在则累加数量"""
    sku = db.query(Sku).filter(Sku.id == body.sku_id).first()
    if sku is None:
        raise HTTPException(status_code=404, detail="SKU 不存在")
    product = db.query(Product).filter(Product.id == sku.product_id).first()
    if product is None or product.status != 1:
        raise HTTPException(status_code=400, detail="商品不存在或已下架")

    item = db.query(CartItem).filter(CartItem.user_id == user.id, CartItem.sku_id == body.sku_id).first()
    if item:
        item.quantity += body.quantity
        if item.quantity > sku.stock:
            raise HTTPException(status_code=400, detail=f"库存不足，当前仅剩 {sku.stock} 件")
        item.selected = 1
    else:
        if body.quantity > sku.stock:
            raise HTTPException(status_code=400, detail=f"库存不足，当前仅剩 {sku.stock} 件")
        item = CartItem(user_id=user.id, sku_id=body.sku_id, quantity=body.quantity, selected=1)
        db.add(item)
    db.commit()
    db.refresh(item)
    return _item_out(item, sku, product)


@router.get("/list", summary="购物车列表", response_model=CartOut)
def list_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """返回购物车全部条目与选中项合计金额"""
    items = db.query(CartItem).filter(CartItem.user_id == user.id).order_by(CartItem.id.desc()).all()
    result_items = []
    total = 0.0
    count = 0
    for item in items:
        sku = db.query(Sku).filter(Sku.id == item.sku_id).first()
        if sku is None:
            continue
        product = db.query(Product).filter(Product.id == sku.product_id).first()
        if product is None:
            continue
        out = _item_out(item, sku, product)
        result_items.append(out)
        if item.selected == 1:
            total += out.subtotal
            count += item.quantity
    return CartOut(items=result_items, selected_total=round(total, 2), selected_count=count)


@router.put("/update/{item_id}", summary="更新购物车条目", response_model=CartItemOut)
def update_cart_item(
    item_id: int,
    body: CartUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """更新数量或选中状态"""
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user.id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="购物车条目不存在")
    sku = db.query(Sku).filter(Sku.id == item.sku_id).first()
    if sku is None:
        raise HTTPException(status_code=404, detail="SKU 不存在")
    if body.quantity is not None:
        if body.quantity > sku.stock:
            raise HTTPException(status_code=400, detail=f"库存不足，当前仅剩 {sku.stock} 件")
        item.quantity = body.quantity
    if body.selected is not None:
        item.selected = body.selected
    db.commit()
    db.refresh(item)
    product = db.query(Product).filter(Product.id == sku.product_id).first()
    return _item_out(item, sku, product)


@router.delete("/remove/{item_id}", summary="删除购物车条目")
def remove_cart_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user.id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="购物车条目不存在")
    db.delete(item)
    db.commit()
    return {"message": "删除成功"}


@router.delete("/clear", summary="清空购物车")
def clear_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.query(CartItem).filter(CartItem.user_id == user.id).delete()
    db.commit()
    return {"message": "购物车已清空"}
