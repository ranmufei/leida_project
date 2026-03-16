"""
气象站点信息模型
"""
from sqlalchemy import Column, Integer, String, DECIMAL, Text, DateTime, Enum, Index, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base


class WeatherStation(Base):
    """气象站点信息表"""
    __tablename__ = "weather_stations"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="站点ID")
    station_id = Column(String(50), unique=True, nullable=False, comment="站点编码")
    station_name = Column(String(200), nullable=False, comment="站点名称")
    latitude = Column(DECIMAL(10, 6), nullable=False, comment="纬度")
    longitude = Column(DECIMAL(10, 6), nullable=False, comment="经度")
    address = Column(String(500), nullable=True, comment="地址")
    region = Column(String(100), nullable=True, comment="所属区域")
    station_type = Column(String(50), nullable=True, comment="站点类型")
    retry_count = Column(Integer, nullable=True, default=0, comment="重试次数")
    max_retries = Column(Integer, nullable=True, default=3, comment="最大重试次数")
    status = Column(
        Enum('active', 'disabled', 'error'),
        nullable=True,
        default='active',
        comment="状态"
    )
    last_sync_time = Column(DateTime, nullable=True, comment="最后同步时间")
    last_sync_status = Column(
        Enum('success', 'failed', 'pending'),
        nullable=True,
        comment="最后同步状态"
    )
    last_error_message = Column(Text, nullable=True, comment="最后错误信息")
    created_at = Column(TIMESTAMP, nullable=True, default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, nullable=True, default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    remark = Column(Text, nullable=True, comment="备注")

    # 索引
    __table_args__ = (
        Index('idx_station_id', 'station_id'),
        Index('idx_region', 'region'),
        Index('idx_status', 'status'),
        Index('idx_latitude', 'latitude'),
        Index('idx_longitude', 'longitude'),
    )

    def __repr__(self):
        return f"<WeatherStation(id={self.id}, station_id={self.station_id}, station_name={self.station_name})>"
