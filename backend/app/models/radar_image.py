"""
雷达图片模型
"""
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Enum, Boolean, Index
from sqlalchemy.sql import func
from app.core.database import Base


class RadarImage(Base):
    """雷达图片元数据表"""
    __tablename__ = "radar_images"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="图片ID")
    filename = Column(String(255), nullable=False, comment="本地文件名")
    original_filename = Column(String(255), nullable=True, comment="原始文件名")
    original_time_str = Column(String(20), nullable=True, comment="原始时间字符串(从API获取)")
    file_path = Column(String(500), nullable=False, comment="文件路径")
    download_url = Column(String(500), nullable=True, comment="下载URL")
    file_size = Column(BigInteger, nullable=True, comment="文件大小(字节)")
    observation_time = Column(DateTime, nullable=False, comment="观测时间")
    download_time = Column(DateTime, nullable=True, comment="下载完成时间")
    download_status = Column(
        Enum('pending', 'success', 'failed', 'retrying'),
        default='pending',
        comment="下载状态"
    )
    retry_count = Column(Integer, default=0, comment="重试次数")
    md5_hash = Column(String(32), nullable=True, comment="文件MD5值")
    error_message = Column(String(1000), nullable=True, comment="错误信息")
    is_processed = Column(Boolean, default=False, comment="是否已处理")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    # 索引
    __table_args__ = (
        Index('uk_observation_time', 'observation_time', unique=True),
        Index('idx_download_status', 'download_status'),
        Index('idx_is_processed', 'is_processed'),
        Index('idx_observation_time', 'observation_time'),
    )

    def __repr__(self):
        return f"<RadarImage(id={self.id}, filename={self.filename}, observation_time={self.observation_time})>"
