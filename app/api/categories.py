# -*- coding: utf-8 -*-
"""
商品分类模块
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.category import Category
from app.schemas.category import CategoryOut

router = APIRouter(prefix="/api/categories", tags=["商品分类"])


@router.get("", summary="获取启用状态的分类列表", response_model=List[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    """小程序首页/分类页使用的分类列表（仅返回上架分类，按 sort_order 升序）"""
    categories = (
        db.query(Category)
        .filter(Category.status == 1)
        .order_by(Category.sort_order.asc(), Category.id.asc())
        .all()
    )
    return categories
