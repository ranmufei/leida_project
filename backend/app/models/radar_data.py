"""
站点雷达数据模型
"""
from sqlalchemy import Column, BigInteger, Integer, DateTime, DECIMAL, String, Enum, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class SiteRadarData(Base):
    """站点雷达数据表"""
    __tablename__ = "site_radar_data"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="数据ID")
    site_id = Column(Integer, ForeignKey('sites.id', ondelete='CASCADE'), nullable=False, comment="站点ID")
    observation_time = Column(DateTime, nullable=False, comment="观测时间")
    dbz_value = Column(DECIMAL(6, 2), nullable=True, comment="dBZ值")
    dbz_category = Column(
        Enum('no_data', 'weak', 'moderate', 'strong', 'severe', 'extreme'),
        default='no_data',
        comment="dBZ等级"
    )
    cloud_impact_factor = Column(DECIMAL(4, 3), default=1.000, comment="云影响因子(0-1)")
    rgb_value = Column(String(20), nullable=True, comment="原始RGB值")
    pixel_x = Column(Integer, nullable=True, comment="雷达图片X坐标")
    pixel_y = Column(Integer, nullable=True, comment="雷达图片Y坐标")
    data_quality = Column(
        Enum('good', 'interpolated', 'outlier', 'missing'),
        default='good',
        comment="数据质量"
    )
    data_source = Column(
        Enum('actual', 'predicted'),
        default='actual',
        comment="数据来源"
    )
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    # 关系
    site = relationship("Site", backref="radar_data")

    # 索引
    __table_args__ = (
        Index('uk_site_time', 'site_id', 'observation_time', unique=True),
        Index('idx_observation_time', 'observation_time'),
        Index('idx_site_id', 'site_id'),
        Index('idx_data_source', 'data_source'),
        Index('idx_site_time_source', 'site_id', 'observation_time', 'data_source'),
    )

    def __repr__(self):
        return f"<SiteRadarData(id={self.id}, site_id={self.site_id}, observation_time={self.observation_time}, dbz_value={self.dbz_value})>"
