"""
预测数据模型
"""
from sqlalchemy import Column, BigInteger, Integer, DateTime, DECIMAL, String, Enum, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class SitePrediction(Base):
    """预测数据表"""
    __tablename__ = "site_predictions"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="预测ID")
    site_id = Column(Integer, ForeignKey('sites.id', ondelete='CASCADE'), nullable=False, comment="站点ID")
    prediction_time = Column(DateTime, nullable=False, comment="预测时间点")
    predicted_dbz = Column(DECIMAL(6, 2), nullable=False, comment="预测的dBZ值")
    confidence_lower = Column(DECIMAL(6, 2), nullable=True, comment="置信区间下限")
    confidence_upper = Column(DECIMAL(6, 2), nullable=True, comment="置信区间上限")
    model_type = Column(
        Enum('optical_flow', 'prophet', 'ensemble'),
        nullable=False,
        comment="模型类型"
    )
    model_version = Column(String(50), nullable=True, comment="模型版本")
    prediction_horizon = Column(Integer, nullable=False, comment="预测时长(分钟)")
    prediction_accuracy = Column(DECIMAL(5, 4), nullable=True, comment="预测准确度(0-1)")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    # 关系
    site = relationship("Site", backref="predictions")

    # 索引
    __table_args__ = (
        Index('idx_site_prediction_time', 'site_id', 'prediction_time'),
        Index('idx_model_type', 'model_type'),
        Index('idx_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<SitePrediction(id={self.id}, site_id={self.site_id}, prediction_time={self.prediction_time}, predicted_dbz={self.predicted_dbz})>"
