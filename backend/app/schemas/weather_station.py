"""
气象站点Schema
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime


class WeatherStationBase(BaseModel):
    """气象站点基础Schema"""
    station_id: str = Field(..., min_length=1, max_length=50, description="站点编码")
    station_name: str = Field(..., min_length=1, max_length=200, description="站点名称")
    longitude: float = Field(..., ge=-180, le=180, description="经度")
    latitude: float = Field(..., ge=-90, le=90, description="纬度")
    address: Optional[str] = Field(None, max_length=500, description="地址")
    region: Optional[str] = Field(None, max_length=100, description="所属区域")
    station_type: Optional[str] = Field(None, max_length=50, description="站点类型")
    max_retries: Optional[int] = Field(3, description="最大重试次数")
    remark: Optional[str] = Field(None, description="备注")


class WeatherStationCreate(WeatherStationBase):
    """创建气象站点Schema"""
    status: Optional[Literal['active', 'disabled', 'error']] = Field('active', description="状态")


class WeatherStationUpdate(BaseModel):
    """更新气象站点Schema"""
    station_name: Optional[str] = Field(None, min_length=1, max_length=200)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    address: Optional[str] = Field(None, max_length=500)
    region: Optional[str] = Field(None, max_length=100)
    station_type: Optional[str] = Field(None, max_length=50)
    max_retries: Optional[int] = None
    status: Optional[Literal['active', 'disabled', 'error']] = None
    remark: Optional[str] = None


class WeatherStationInDB(WeatherStationBase):
    """气象站点完整信息Schema"""
    id: int
    retry_count: int
    max_retries: int
    status: Optional[Literal['active', 'disabled', 'error']]
    last_sync_time: Optional[datetime]
    last_sync_status: Optional[Literal['success', 'failed', 'pending']]
    last_error_message: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
