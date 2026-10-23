# -*- coding: utf-8 -*-
"""
管理后台：商品管理（列表/详情/创建/更新/删除，含上下架状态与 SKU 编辑）
全部接口走管理员鉴权
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.admin import Admin
from app.models.category import Category
from app.models.order import OrderItem
from app.models.product import Product, Sku
from app.schemas.admin_product import (
    AdminProductCreateRequest,
    AdminProductListOut,
    AdminProductOut,
    AdminProductUpdateRequest,
    AdminSkuOut,
)

router = APIRouter(prefix="/api/admin/products", tags=["管理后台-商品"])


def _sku_out(s: Sku) -> AdminSkuOut:
    return AdminSkuOut(
        id=s.id,
        product_id=s.product_id,
        name=s.name,
        price=float(s.price),
        stock=s.stock,
    )


def _product_out(p: Product) -> AdminProductOut:
    return AdminProductOut(
        id=p.id,
        category_id=p.category_id,
        category_name=p.category.name if p.category else "",
        name=p.name,
        cover_url=p.cover_url,
        description=p.description,
        price=float(p.price),
        stock=p.stock,
        sales=p.sales,
        status=p.status,
        created_at=p.created_at,
        skus=[_sku_out(s) for s in p.skus],
    )


def _get_product(db: Session, product_id: int) -> Product:
    product = (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.skus))
        .filter(Product.id == product_id)
        .first()
    )
    if product is None:
        raise HTTPException(status_code=404, detail="商品不存在")
    return product


@router.get("", summary="商品列表（分页/状态/关键词筛选）", response_model=AdminProductListOut)
def list_products(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    status: Optional[int] = Query(None, description="状态：1 上架 0 下架，不传返回全部"),
    keyword: Optional[str] = Query(None, description="关键词（模糊匹配商品名）"),
    category_id: Optional[int] = Query(None, description="分类 ID"),
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """管理端商品列表：包含上下架全部商品，按创建时间倒序"""
    query = db.query(Product).options(joinedload(Product.category))
    if status is not None:
        query = query.filter(Product.status == status)
    if keyword:
        query = query.filter(Product.name.like(f"%{keyword}%"))
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    total = query.count()
    products = (
        query.options(joinedload(Product.skus))
        .order_by(Product.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return AdminProductListOut(
        total=total,
        page=page,
        page_size=page_size,
        items=[_product_out(p) for p in products],
    )


@router.get("/{product_id}", summary="商品详情（含 SKU）", response_model=AdminProductOut)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    return _product_out(_get_product(db, product_id))


@router.post("", summary="创建商品", response_model=AdminProductOut)
def create_product(
    body: AdminProductCreateRequest,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """创建商品；传 skus 时商品库存=SKU 库存之和，价格取第一个 SKU 价格"""
    category = db.query(Category).filter(Category.id == body.category_id).first()
    if category is None:
        raise HTTPException(status_code=400, detail="分类不存在")

    stock = body.stock
    price = body.price
    skus = []
    if body.skus:
        skus = [Sku(name=s.name, price=s.price, stock=s.stock) for s in body.skus]
        stock = sum(s.stock for s in skus)
        price = float(skus[0].price)

    product = Product(
        category_id=body.category_id,
        name=body.name,
        cover_url=body.cover_url,
        description=body.description,
        price=price,
        stock=stock,
        status=body.status,
    )
    product.skus = skus
    db.add(product)
    db.commit()
    db.refresh(product)
    product = _get_product(db, product.id)
    return _product_out(product)


@router.put("/{product_id}", summary="更新商品（含 SKU 全量同步）", response_model=AdminProductOut)
def update_product(
    product_id: int,
    body: AdminProductUpdateRequest,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """更新商品字段；skus 传入时按列表全量同步（无 id 新增、有 id 更新、缺失删除）"""
    product = _get_product(db, product_id)

    if body.category_id is not None:
        category = db.query(Category).filter(Category.id == body.category_id).first()
        if category is None:
            raise HTTPException(status_code=400, detail="分类不存在")
        product.category_id = body.category_id
    if body.name is not None:
        product.name = body.name
    if body.cover_url is not None:
        product.cover_url = body.cover_url
    if body.description is not None:
        product.description = body.description
    if body.price is not None:
        product.price = body.price
    if body.status is not None:
        if body.status not in (0, 1):
            raise HTTPException(status_code=400, detail="状态仅支持 1 上架 0 下架")
        product.status = body.status

    # SKU 全量同步
    if body.skus is not None:
        existing = {s.id: s for s in product.skus if s.id is not None}
        seen_ids = set()
        for item in body.skus:
            if item.id is not None and item.id in existing:
                sku = existing[item.id]
                sku.name = item.name
                sku.price = item.price
                sku.stock = item.stock
                seen_ids.add(item.id)
            else:
                db.add(Sku(
                    product_id=product.id,
                    name=item.name,
                    price=item.price,
                    stock=item.stock,
                ))
        for sid, sku in existing.items():
            if sid not in seen_ids:
                db.delete(sku)
        db.flush()
        product.stock = sum(s.stock for s in db.query(Sku).filter(Sku.product_id == product.id).all())
    elif body.stock is not None:
        product.stock = body.stock

    db.commit()
    db.refresh(product)
    product = _get_product(db, product.id)
    return _product_out(product)


@router.delete("/{product_id}", summary="删除商品", response_model=dict)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """删除商品（含 SKU）；存在订单记录时拒绝删除，建议改为下架"""
    product = _get_product(db, product_id)
    has_order = db.query(OrderItem).filter(OrderItem.product_id == product_id).first()
    if has_order:
        raise HTTPException(status_code=400, detail="该商品存在订单记录，无法删除，请改为下架")
    db.delete(product)
    db.commit()
    return {"message": "商品已删除", "id": product_id}
