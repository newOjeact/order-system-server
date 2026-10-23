# -*- coding: utf-8 -*-
"""
收货地址模块：增删改查、设置默认（需登录）
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.address import Address
from app.models.user import User
from app.schemas.address import AddressCreate, AddressOut, AddressUpdate

router = APIRouter(prefix="/api/addresses", tags=["收货地址"])


@router.get("", summary="地址列表", response_model=List[AddressOut])
def list_addresses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """按创建时间倒序，默认地址置顶"""
    return (
        db.query(Address)
        .filter(Address.user_id == user.id)
        .order_by(Address.is_default.desc(), Address.id.desc())
        .all()
    )


@router.post("", summary="新增地址", response_model=AddressOut)
def create_address(body: AddressCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.is_default == 1:
        db.query(Address).filter(Address.user_id == user.id).update({"is_default": 0})
    address = Address(user_id=user.id, **body.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


@router.put("/{address_id}", summary="修改地址", response_model=AddressOut)
def update_address(
    address_id: int,
    body: AddressUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == user.id).first()
    if address is None:
        raise HTTPException(status_code=404, detail="地址不存在")
    data = body.model_dump(exclude_unset=True)
    if data.get("is_default") == 1:
        db.query(Address).filter(Address.user_id == user.id, Address.id != address_id).update({"is_default": 0})
    for key, value in data.items():
        setattr(address, key, value)
    db.commit()
    db.refresh(address)
    return address


@router.delete("/{address_id}", summary="删除地址")
def delete_address(address_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == user.id).first()
    if address is None:
        raise HTTPException(status_code=404, detail="地址不存在")
    db.delete(address)
    db.commit()
    return {"message": "删除成功"}
