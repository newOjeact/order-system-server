# -*- coding: utf-8 -*-
"""
全局配置项
"""
import os
from datetime import timedelta

from dotenv import load_dotenv

# 项目根目录（server 目录）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载 server/.env（UTF-8 无 BOM），用于注入 WX_SECRET 等本地敏感配置
load_dotenv(os.path.join(BASE_DIR, ".env"), encoding="utf-8")

# SQLite 数据库文件路径（自动初始化）
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'order.db')}")

# JWT 配置
SECRET_KEY = os.getenv("SECRET_KEY", "order-system-mvp-secret-key-please-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 天

# 微信小程序配置（用于 MP-WEIXIN 端一键登录）
# WX_APPID 为项目小程序 appid；WX_SECRET 必须通过环境变量注入，严禁写死/编造
WX_APPID = os.getenv("WX_APPID", "wxee4014e517b8275b")
WX_SECRET = os.getenv("WX_SECRET", "")


def require_wx_secret() -> str:
    """返回微信小程序密钥；未配置时抛出明确错误提示（不在此处编造）"""
    if not WX_SECRET:
        raise RuntimeError(
            "未配置微信小程序密钥 WX_SECRET：请在启动服务前设置环境变量 "
            "WX_SECRET=你的小程序密钥（登录微信公众平台 mp.weixin.qq.com → "
            "开发管理 → 开发设置 → 小程序密钥 获取），严禁在代码中写死密钥。"
        )
    return WX_SECRET

# 是否自动初始化数据（分类/示例商品等）
AUTO_SEED_DATA = True

# 项目信息（用于 Swagger 文档）
PROJECT_NAME = "下单系统 MVP"
PROJECT_DESCRIPTION = "uni-app 小程序下单系统 MVP 后端：用户/商品/SKU/购物车/地址/订单/模拟支付"

# 模拟支付：支付成功后订单状态流转的延迟（秒），0 表示立即
MOCK_PAY_DELAY_SECONDS = 0
