"""
气象雷达数据提取系统

主要功能:
- 坐标映射: 经纬度与像素坐标转换
- 色标解析: RGB值转dBZ值
- 特征提取: 点特征、邻域特征、时序特征
- CSV生成: 15分钟粒度时间序列数据
"""

__version__ = '1.0.0'
__author__ = '雷达数据处理团队'

from .preprocessing.mapper import ChinaRadarMapper, CalibratedRadarMapper, create_mapper_from_image
from .preprocessing.color_scale import ColorScaleParser, LegendParser
from .features.extractor import RadarFeatureExtractor, RadarDataExtractor
from .features.csv_generator import CSVGenerator, create_summary_statistics
from .utils.helpers import setup_logger, download_radar_images, Timer
from .config.config import get_config, MAJOR_CITIES, get_city_coordinates

__all__ = [
    'ChinaRadarMapper',
    'CalibratedRadarMapper',
    'create_mapper_from_image',
    'ColorScaleParser',
    'LegendParser',
    'RadarFeatureExtractor',
    'RadarDataExtractor',
    'CSVGenerator',
    'create_summary_statistics',
    'setup_logger',
    'download_radar_images',
    'Timer',
    'get_config',
    'MAJOR_CITIES',
    'get_city_coordinates'
]
