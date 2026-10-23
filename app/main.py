# -*- coding: utf-8 -*-
"""
FastAPI 应用入口
- 挂载各业务路由
- 自动初始化 SQLite 数据库（含种子数据）
- 提供 Swagger 文档：http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    addresses,
    admin_auth,
    admin_dashboard,
    admin_orders,
    admin_products,
    auth,
    cart,
    categories,
    orders,
    pay,
    products,
)
from app.core.config import PROJECT_DESCRIPTION, PROJECT_NAME
from app.core.database import init_db

app = FastAPI(
    title=PROJECT_NAME,
    description=PROJECT_DESCRIPTION,
    version="0.1.0",
)

# 允许跨域（本地开发小程序/H5 调试用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(addresses.router)
app.include_router(orders.router)
app.include_router(pay.router)
# 管理后台路由
app.include_router(admin_auth.router)
app.include_router(admin_products.router)
app.include_router(admin_orders.router)
app.include_router(admin_dashboard.router)


@app.on_event("startup")
def on_startup():
    """启动时自动建表并初始化种子数据"""
    init_db()


@app.get("/", tags=["健康检查"])
def root():
    return {"message": "下单系统 MVP 后端运行中", "docs": "/docs"}
