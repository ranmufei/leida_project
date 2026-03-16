"""
坐标校准相关数据模型
"""
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime
from datetime import datetime
from app.core.database import Base


class ControlPoint(Base):
    """控制点表 - 存储人工标注的像素坐标与经纬度对应关系"""
    __tablename__ = 'control_points'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='控制点ID')
    pixel_x = Column(Integer, nullable=False, comment='像素X坐标')
    pixel_y = Column(Integer, nullable=False, comment='像素Y坐标')
    longitude = Column(Float, nullable=False, comment='经度')
    latitude = Column(Float, nullable=False, comment='纬度')
    name = Column(String(100), nullable=True, comment='控制点名称')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    def to_dict(self):
        return {
            'id': self.id,
            'pixel_x': self.pixel_x,
            'pixel_y': self.pixel_y,
            'longitude': self.longitude,
            'latitude': self.latitude,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CalibrationParams(Base):
    """校准参数表 - 存储仿射变换参数"""
    __tablename__ = 'calibration_params'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='参数ID')
    # 仿射变换参数: lon = a0 + a1*x + a2*y
    affine_lon_a0 = Column(Float, nullable=True, comment='经度仿射变换参数 a0')
    affine_lon_a1 = Column(Float, nullable=True, comment='经度仿射变换参数 a1')
    affine_lon_a2 = Column(Float, nullable=True, comment='经度仿射变换参数 a2')
    # 仿射变换参数: lat = b0 + b1*x + b2*y
    affine_lat_b0 = Column(Float, nullable=True, comment='纬度仿射变换参数 b0')
    affine_lat_b1 = Column(Float, nullable=True, comment='纬度仿射变换参数 b1')
    affine_lat_b2 = Column(Float, nullable=True, comment='纬度仿射变换参数 b2')
    is_active = Column(Boolean, default=False, comment='是否激活使用')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    def to_dict(self):
        return {
            'id': self.id,
            'affine_lon': [self.affine_lon_a0, self.affine_lon_a1, self.affine_lon_a2],
            'affine_lat': [self.affine_lat_b0, self.affine_lat_b1, self.affine_lat_b2],
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_params(cls, affine_lon, affine_lat, is_active=True):
        """从参数数组创建实例"""
        return cls(
            affine_lon_a0=affine_lon[0],
            affine_lon_a1=affine_lon[1],
            affine_lon_a2=affine_lon[2],
            affine_lat_b0=affine_lat[0],
            affine_lat_b1=affine_lat[1],
            affine_lat_b2=affine_lat[2],
            is_active=is_active
        )
