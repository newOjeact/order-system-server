# -*- coding: utf-8 -*-
"""
商品与 SKU 模型
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True, comment="所属分类 ID")
    name = Column(String(100), nullable=False, comment="商品名称")
    cover_url = Column(String(255), default="", comment="封面图 URL")
    description = Column(Text, default="", comment="商品描述")
    price = Column(Numeric(10, 2), nullable=False, default=0, comment="默认价格")
    stock = Column(Integer, default=0, comment="总库存")
    sales = Column(Integer, default=0, comment="销量")
    status = Column(Integer, default=1, comment="状态：1 上架 0 下架")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    category = relationship("Category", lazy="joined")
    skus = relationship("Sku", back_populates="product", cascade="all, delete-orphan", lazy="selectin")


class Sku(Base):
    __tablename__ = "skus"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True, comment="所属商品 ID")
    name = Column(String(50), nullable=False, comment="规格名称（如：黑色 / 标准版）")
    price = Column(Numeric(10, 2), nullable=False, default=0, comment="规格价格")
    stock = Column(Integer, default=0, comment="规格库存")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    product = relationship("Product", back_populates="skus")
