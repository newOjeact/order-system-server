# -*- coding: utf-8 -*-
"""
收货地址请求/响应模式
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AddressCreate(BaseModel):
    receiver: str = Field(..., max_length=50, description="收货人姓名")
    phone: str = Field(..., max_length=20, description="联系电话")
    province: str = Field("", max_length=50, description="省")
    city: str = Field("", max_length=50, description="市")
    district: str = Field("", max_length=50, description="区/县")
    detail: str = Field(..., max_length=255, description="详细地址")
    is_default: int = Field(0, ge=0, le=1, description="是否默认地址")


class AddressUpdate(BaseModel):
    receiver: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    province: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=50)
    district: Optional[str] = Field(None, max_length=50)
    detail: Optional[str] = Field(None, max_length=255)
    is_default: Optional[int] = Field(None, ge=0, le=1)


class AddressOut(BaseModel):
    id: int
    receiver: str
    phone: str
    province: str
    city: str
    district: str
    detail: str
    is_default: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
