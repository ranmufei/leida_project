"""
服务模块
"""
# 使用新的NMC直接URL下载服务
from app.services.download_service_nmc import NMCRadarImageDownloader as RadarImageDownloader
from app.services.processing_service import (
    CoordinateMapper,
    ColorScaleParser,
    RadarDataProcessor
)

__all__ = [
    "RadarImageDownloader",
    "CoordinateMapper",
    "ColorScaleParser",
    "RadarDataProcessor"
]
