# -*- coding: utf-8 -*-
"""
模型注册：显式导入全部模型，确保 Base.metadata.create_all 建表完整
"""
from app.models.admin import Admin  # noqa: F401
from app.models.address import Address  # noqa: F401
from app.models.cart import CartItem  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.order import Order, OrderItem  # noqa: F401
from app.models.product import Product, Sku  # noqa: F401
from app.models.user import User  # noqa: F401