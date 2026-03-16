"""
站点Schema
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class SiteBase(BaseModel):
    """站点基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="站点名称")
    code: str = Field(..., min_length=1, max_length=50, description="站点编码")
    longitude: float = Field(..., ge=-180, le=180, description="经度")
    latitude: float = Field(..., ge=-90, le=90, description="纬度")
    altitude: Optional[float] = Field(None, description="海拔高度(米)")
    region: Optional[str] = Field(None, max_length=100, description="所属区域")
    description: Optional[str] = Field(None, description="描述信息")


class SiteCreate(SiteBase):
    """创建站点Schema"""
    pass


class SiteUpdate(BaseModel):
    """更新站点Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    altitude: Optional[float] = None
    region: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SiteInDB(SiteBase):
    """站点完整信息Schema"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
