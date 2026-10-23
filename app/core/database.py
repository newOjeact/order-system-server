# -*- coding: utf-8 -*-
"""
数据库连接与会话管理
- 使用 SQLAlchemy 2.x 风格
- SQLite 数据库文件自动创建
- 首次启动自动建表并写入种子数据（分类/商品/SKU）
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import DATABASE_URL

# SQLite 需要 check_same_thread=False 以支持多线程访问
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI 依赖：请求级数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """建表并初始化种子数据"""
    from app import models  # noqa: F401  确保模型已注册
    Base.metadata.create_all(bind=engine)

    # 种子数据仅在空库时写入
    with SessionLocal() as db:
        from app.models.category import Category
        from app.models.product import Product, Sku
        if db.query(Category).count() == 0:
            _seed_data(db)

        # 管理员账号仅在 admins 表为空时写入
        from app.models.admin import Admin
        if db.query(Admin).count() == 0:
            _seed_admins(db)


def _seed_admins(db):
    """写入演示用管理员账号：super_admin / admin，初始密码均为 admin123456"""
    from app.core.security import hash_password
    from app.models.admin import Admin

    db.add_all([
        Admin(
            username="super_admin",
            password_hash=hash_password("admin123456"),
            role="super_admin",
            status=1,
        ),
        Admin(
            username="admin",
            password_hash=hash_password("admin123456"),
            role="admin",
            status=1,
        ),
    ])
    db.commit()


def _seed_data(db):
    """写入演示用的分类、商品与 SKU"""
    from app.models.category import Category
    from app.models.product import Product, Sku

    # 分类
    c1 = Category(name="手机数码", sort_order=1)
    c2 = Category(name="家用电器", sort_order=2)
    c3 = Category(name="服饰鞋包", sort_order=3)
    c4 = Category(name="食品生鲜", sort_order=4)
    db.add_all([c1, c2, c3, c4])
    db.flush()

    # 商品 1：无线耳机（含 2 个 SKU 规格）
    p1 = Product(
        category_id=c1.id,
        name="无线蓝牙耳机 Pro",
        cover_url="https://dummyimage.com/600x600/1e90ff/ffffff&text=Headphone",
        description="主动降噪、30 小时续航、蓝牙 5.3，支持快速充电。",
        price=299.00,
        stock=100,
        status=1,
    )
    db.add(p1)
    db.flush()
    db.add_all([
        Sku(product_id=p1.id, name="黑色", price=299.00, stock=60),
        Sku(product_id=p1.id, name="白色", price=319.00, stock=40),
    ])

    # 商品 2：智能手表
    p2 = Product(
        category_id=c1.id,
        name="智能运动手表",
        cover_url="https://dummyimage.com/600x600/32cd32/ffffff&text=Watch",
        description="心率监测、血氧检测、50 米防水，支持 100+ 运动模式。",
        price=599.00,
        stock=50,
        status=1,
    )
    db.add(p2)
    db.flush()
    db.add_all([
        Sku(product_id=p2.id, name="标准版", price=599.00, stock=30),
        Sku(product_id=p2.id, name="尊享版(含表带)", price=699.00, stock=20),
    ])

    # 商品 3：电热水壶
    p3 = Product(
        category_id=c2.id,
        name="智能恒温电热水壶",
        cover_url="https://dummyimage.com/600x600/ffa500/ffffff&text=Kettle",
        description="1.7L 大容量，304 不锈钢内胆，60 秒速热，恒温 24 小时。",
        price=129.00,
        stock=80,
        status=1,
    )
    db.add(p3)
    db.flush()
    db.add_all([
        Sku(product_id=p3.id, name="白色", price=129.00, stock=50),
        Sku(product_id=p3.id, name="蓝色", price=139.00, stock=30),
    ])

    # 商品 4：T 恤
    p4 = Product(
        category_id=c3.id,
        name="纯棉圆领 T 恤",
        cover_url="https://dummyimage.com/600x600/ff69b4/ffffff&text=TShirt",
        description="100% 新疆长绒棉，透气亲肤，多种颜色可选。",
        price=59.00,
        stock=200,
        status=1,
    )
    db.add(p4)
    db.flush()
    db.add_all([
        Sku(product_id=p4.id, name="白色 M", price=59.00, stock=80),
        Sku(product_id=p4.id, name="黑色 L", price=59.00, stock=70),
        Sku(product_id=p4.id, name="粉色 S", price=59.00, stock=50),
    ])

    db.commit()
