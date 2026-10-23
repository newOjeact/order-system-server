# -*- coding: utf-8 -*-
"""
商品模块：商品列表（支持分类筛选）/ 商品详情（含 SKU）
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.product import Product
from app.schemas.product import ProductDetail, ProductListItem

router = APIRouter(prefix="/api/products", tags=["商品"])


def _to_list_item(p: Product) -> ProductListItem:
    return ProductListItem(
        id=p.id,
        category_id=p.category_id,
        category_name=p.category.name if p.category else "",
        name=p.name,
        cover_url=p.cover_url,
        price=float(p.price),
        stock=p.stock,
        sales=p.sales,
        status=p.status,
    )


@router.get("", summary="商品列表（可按分类/关键词筛选）", response_model=List[ProductListItem])
def list_products(
    category_id: Optional[int] = Query(None, description="分类 ID，不传返回全部"),
    keyword: Optional[str] = Query(None, description="关键词（模糊匹配商品名）"),
    db: Session = Depends(get_db),
):
    """MVP 商品列表：仅返回上架商品，按销量降序"""
    query = db.query(Product).options(joinedload(Product.category)).filter(Product.status == 1)
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if keyword:
        query = query.filter(Product.name.like(f"%{keyword}%"))
    products = query.order_by(Product.sales.desc(), Product.id.desc()).all()
    return [_to_list_item(p) for p in products]


@router.get("/{product_id}", summary="商品详情（含 SKU 列表）", response_model=ProductDetail)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """返回商品详情、描述与全部 SKU 规格"""
    product = (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.skus))
        .filter(Product.id == product_id)
        .first()
    )
    if product is None:
        raise HTTPException(status_code=404, detail="商品不存在")
    if product.status != 1:
        raise HTTPException(status_code=404, detail="商品已下架")
    base = _to_list_item(product)
    return ProductDetail(
        **base.model_dump(),
        description=product.description,
        skus=[s for s in product.skus],
    )
