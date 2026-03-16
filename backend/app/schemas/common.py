"""
通用响应Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, Generic, TypeVar
from datetime import datetime

DataT = TypeVar('DataT')


class ApiResponse(BaseModel, Generic[DataT]):
    """通用API响应"""
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="消息")
    data: Optional[DataT] = Field(None, description="数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class PaginatedResponse(BaseModel, Generic[DataT]):
    """分页响应"""
    items: list[DataT] = Field([], description="数据列表")
    total: int = Field(0, description="总数")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(20, description="每页数量")
    total_pages: int = Field(0, description="总页数")
