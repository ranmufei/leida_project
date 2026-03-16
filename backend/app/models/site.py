"""
站点信息模型
"""
from sqlalchemy import Column, Integer, String, DECIMAL, Text, Boolean, DateTime, Index
from sqlalchemy.sql import func
from app.core.database import Base


class Site(Base):
    """站点信息表"""
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="站点ID")
    name = Column(String(100), nullable=False, comment="站点名称")
    code = Column(String(50), unique=True, nullable=False, comment="站点编码")
    longitude = Column(DECIMAL(10, 6), nullable=False, comment="经度")
    latitude = Column(DECIMAL(10, 6), nullable=False, comment="纬度")
    altitude = Column(DECIMAL(8, 2), nullable=True, comment="海拔高度(米)")
    region = Column(String(100), nullable=True, comment="所属区域")
    description = Column(Text, nullable=True, comment="描述信息")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间(软删除)")

    # 索引
    __table_args__ = (
        Index('idx_region', 'region'),
        Index('idx_is_active', 'is_active'),
        Index('idx_code', 'code'),
        Index('idx_deleted_at', 'deleted_at'),
    )

    def __repr__(self):
        return f"<Site(id={self.id}, name={self.name}, code={self.code})>"
