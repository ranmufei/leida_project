"""
雷达图片Schema
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RadarImageSchema(BaseModel):
    """雷达图片Schema"""
    id: int
    filename: str
    original_filename: Optional[str] = None
    original_time_str: Optional[str] = None
    file_path: str
    download_url: Optional[str] = None
    file_size: Optional[int] = None
    observation_time: datetime
    download_time: Optional[datetime] = None
    download_status: str
    retry_count: int = 0
    md5_hash: Optional[str] = None
    error_message: Optional[str] = None
    is_processed: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class RadarImageListSchema(BaseModel):
    """雷达图片列表Schema"""
    items: list[RadarImageSchema]
    total: int
    page: int
    page_size: int
    total_pages: int
