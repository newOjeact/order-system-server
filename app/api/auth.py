# -*- coding: utf-8 -*-
"""
用户模块：注册 / 登录 / 微信一键登录 / 获取个人信息（JWT 鉴权）
"""
import secrets

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import WX_APPID, WX_SECRET
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import LoginRequest, RegisterRequest, TokenOut, UserOut, WxLoginRequest

router = APIRouter(prefix="/api/user", tags=["用户"])


@router.post("/register", summary="注册", response_model=TokenOut)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """注册新用户，成功后直接返回登录令牌"""
    exists = db.query(User).filter(User.username == body.username).first()
    if exists:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        nickname=body.nickname or body.username,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", summary="登录", response_model=TokenOut)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """用户名密码登录，返回 JWT 令牌"""
    user = db.query(User).filter(User.username == body.username).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="账号已被禁用")
    token = create_access_token(user.id)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", summary="获取当前用户信息", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


@router.post("/wx-login", summary="微信一键登录", response_model=TokenOut)
def wx_login(body: WxLoginRequest, db: Session = Depends(get_db)):
    """小程序端微信一键登录：前端传入 code，调用微信 jscode2session 换取 openid，
    按 openid 查找用户，不存在则自动创建，签发与账号密码登录一致的 JWT。"""
    if not WX_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务端未配置微信小程序密钥 WX_SECRET，请在环境变量中设置后重启服务",
        )

    # 1. 用 code 向微信服务器换取 openid
    try:
        resp = httpx.get(
            "https://api.weixin.qq.com/sns/jscode2session",
            params={
                "appid": WX_APPID,
                "secret": WX_SECRET,
                "js_code": body.code,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        data = resp.json()
    except Exception:
        raise HTTPException(status_code=502, detail="微信登录服务暂不可用，请稍后重试")

    if data.get("errcode"):
        raise HTTPException(
            status_code=400,
            detail=f"微信登录失败：{data.get('errmsg', 'code 无效或已过期')}",
        )
    openid = data.get("openid")
    if not openid:
        raise HTTPException(status_code=400, detail="微信登录失败：未获取到 openid")

    # 2. 按 openid 查询用户；不存在则自动创建（保留账号密码登录体系不变）
    user = db.query(User).filter(User.openid == openid).first()
    if user is None:
        username = "wx_" + openid
        # 极端情况：用户名被占用时追加序号，避免唯一约束冲突
        base = username[:40]
        suffix = 1
        while db.query(User).filter(User.username == username).first():
            username = f"{base}_{suffix}"
            suffix += 1
        user = User(
            username=username,
            password_hash=hash_password(secrets.token_urlsafe(24)),
            nickname="微信用户",
            openid=openid,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=400, detail="账号已被禁用")

    # 3. 签发 JWT，返回与注册/登录一致的结构
    token = create_access_token(user.id)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))
