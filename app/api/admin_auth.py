# -*- coding: utf-8 -*-
"""
管理后台：管理员登录（POST /api/admin/login）+ 管理员账号管理（super_admin）
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, require_super_admin
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.admin import Admin
from app.schemas.admin import (
    AdminCreateRequest,
    AdminLoginRequest,
    AdminOut,
    AdminTokenOut,
    AdminUpdateRequest,
)

router = APIRouter(prefix="/api/admin", tags=["管理后台-管理员"])


@router.post("/login", summary="管理员登录", response_model=AdminTokenOut)
def admin_login(body: AdminLoginRequest, db: Session = Depends(get_db)):
    """管理员用户名密码登录，返回 JWT 令牌（type=admin）"""
    admin = db.query(Admin).filter(Admin.username == body.username).first()
    if admin is None or not verify_password(body.password, admin.password_hash):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    if admin.status != 1:
        raise HTTPException(status_code=400, detail="账号已被禁用")
    token = create_access_token(admin.id, token_type="admin")
    return AdminTokenOut(access_token=token, admin=AdminOut.model_validate(admin))


@router.get("/admins", summary="管理员列表", response_model=List[AdminOut])
def list_admins(
    db: Session = Depends(get_db),
    _: Admin = Depends(require_super_admin),
):
    """仅超级管理员可查看全部管理员账号"""
    return db.query(Admin).order_by(Admin.id.asc()).all()


@router.post("/admins", summary="创建管理员", response_model=AdminOut)
def create_admin(
    body: AdminCreateRequest,
    db: Session = Depends(get_db),
    _: Admin = Depends(require_super_admin),
):
    """仅超级管理员可创建管理员账号"""
    if body.role not in ("super_admin", "admin"):
        raise HTTPException(status_code=400, detail="角色仅支持 super_admin / admin")
    exists = db.query(Admin).filter(Admin.username == body.username).first()
    if exists:
        raise HTTPException(status_code=400, detail="用户名已存在")
    admin = Admin(
        username=body.username,
        password_hash=hash_password(body.password),
        role=body.role,
        status=1,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return AdminOut.model_validate(admin)


@router.put("/admins/{admin_id}", summary="更新管理员（角色/状态/重置密码）", response_model=AdminOut)
def update_admin(
    admin_id: int,
    body: AdminUpdateRequest,
    db: Session = Depends(get_db),
    current: Admin = Depends(require_super_admin),
):
    """仅超级管理员可更新管理员；禁止禁用自身"""
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if admin is None:
        raise HTTPException(status_code=404, detail="管理员不存在")
    if body.role is not None:
        if body.role not in ("super_admin", "admin"):
            raise HTTPException(status_code=400, detail="角色仅支持 super_admin / admin")
        admin.role = body.role
    if body.status is not None:
        if body.status not in (0, 1):
            raise HTTPException(status_code=400, detail="状态仅支持 1 启用 0 禁用")
        if admin.id == current.id and body.status == 0:
            raise HTTPException(status_code=400, detail="不能禁用当前登录账号")
        admin.status = body.status
    if body.password is not None:
        admin.password_hash = hash_password(body.password)
    db.commit()
    db.refresh(admin)
    return AdminOut.model_validate(admin)
