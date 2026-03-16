"""
配置文件模块

定义系统常量、默认参数和配置选项
"""

import os
from typing import Dict, List, Tuple
from dataclasses import dataclass, field


@dataclass
class RadarConfig:
    """雷达图片配置"""

    # 中国气象局标准网格参数
    GRID_RESOLUTION: float = 0.01  # 度
    DEFAULT_LON_RANGE: float = 70.0  # 经度跨度
    DEFAULT_LAT_RANGE: float = 40.0  # 纬度跨度
    CENTER_LON: float = 105.0  # 中国中心经度
    CENTER_LAT: float = 35.0  # 中国中心纬度

    # 数据时间间隔
    RAW_INTERVAL: int = 6  # 原始数据间隔(分钟)
    TARGET_INTERVAL: str = '15T'  # 目标间隔(Pandas格式)

    # URL配置
    BASE_URL: str = "https://image.data.cma.cn/vis/RAD__B0_CR"

    # 图片格式
    IMAGE_FORMAT: str = 'png'
    IMAGE_QUALITY: int = 95


@dataclass
class ColorScaleConfig:
    """色标配置"""

    # dBZ分类阈值
    WEAK_THRESHOLD: float = 15.0
    MODERATE_THRESHOLD: float = 35.0
    STRONG_THRESHOLD: float = 45.0
    SEVERE_THRESHOLD: float = 55.0

    # 云影响因子参数
    CLOUD_FREE_THRESHOLD: float = 10.0
    THICK_CLOUD_THRESHOLD: float = 35.0
    MAX_IMPACT_FACTOR: float = 1.0
    MIN_IMPACT_FACTOR: float = 0.0


@dataclass
class FeatureConfig:
    """特征提取配置"""

    # 邻域分析
    DEFAULT_NEIGHBORHOOD_RADIUS: float = 20.0  # 公里
    NEIGHBORHOOD_PIXEL_RATIO: float = 20.0 / 111.0  # 像素比例

    # 时序特征
    TEMPORAL_WINDOW_SIZES: List[int] = field(default_factory=lambda: [2, 3, 6])

    # 数据质量
    DBZ_MIN_VALID: float = -30.0
    DBZ_MAX_VALID: float = 75.0
    MAX_MISSING_RATIO: float = 0.3  # 最大缺失值比例


@dataclass
class ProcessingConfig:
    """数据处理配置"""

    # 并行处理
    ENABLE_PARALLEL: bool = True
    MAX_WORKERS: int = 4

    # 批处理
    BATCH_SIZE: int = 10

    # 内存管理
    MAX_IMAGE_CACHE_SIZE: int = 100  # 最大缓存图片数
    CHUNK_SIZE: int = 1000  # 分块处理大小


@dataclass
class OutputConfig:
    """输出配置"""

    # CSV格式
    CSV_ENCODING: str = 'utf-8-sig'
    CSV_DATE_FORMAT: str = '%Y-%m-%d %H:%M:%S'

    # 输出字段
    PRIORITY_FIELDS: List[str] = field(default_factory=lambda: [
        'timestamp', 'location_name', 'longitude', 'latitude',
        'dbz_value', 'dbz_category', 'cloud_impact_factor',
        'dbz_change_rate', 'dbz_trend', 'dbz_max_past_3'
    ])

    # 文件命名
    OUTPUT_FILENAME_TEMPLATE: str = "radar_data_{start}_{end}.csv"


@dataclass
class PathConfig:
    """路径配置"""

    # 项目根目录
    PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # 数据目录
    DATA_DIR: str = None
    RAW_DATA_DIR: str = None
    PROCESSED_DATA_DIR: str = None

    # 日志目录
    LOG_DIR: str = None

    # 输出目录
    OUTPUT_DIR: str = None

    def __post_init__(self):
        """初始化路径"""
        if self.DATA_DIR is None:
            self.DATA_DIR = os.path.join(self.PROJECT_ROOT, 'data')
        if self.RAW_DATA_DIR is None:
            self.RAW_DATA_DIR = os.path.join(self.DATA_DIR, 'raw')
        if self.PROCESSED_DATA_DIR is None:
            self.PROCESSED_DATA_DIR = os.path.join(self.DATA_DIR, 'processed')
        if self.LOG_DIR is None:
            self.LOG_DIR = os.path.join(self.PROJECT_ROOT, 'logs')
        if self.OUTPUT_DIR is None:
            self.OUTPUT_DIR = os.path.join(self.PROJECT_ROOT, 'output')


# 默认配置实例
radar_config = RadarConfig()
color_scale_config = ColorScaleConfig()
feature_config = FeatureConfig()
processing_config = ProcessingConfig()
output_config = OutputConfig()
path_config = PathConfig()


def get_config() -> Dict:
    """
    获取所有配置

    Returns:
        配置字典
    """
    return {
        'radar': radar_config,
        'color_scale': color_scale_config,
        'feature': feature_config,
        'processing': processing_config,
        'output': output_config,
        'path': path_config
    }


def update_config(config_dict: Dict):
    """
    更新配置

    Args:
        config_dict: 配置字典
    """
    for key, value in config_dict.items():
        if hasattr(globals(), f'{key}_config'):
            config_obj = globals()[f'{key}_config']
            for attr, attr_value in value.items():
                if hasattr(config_obj, attr):
                    setattr(config_obj, attr, attr_value)


# 中国主要城市坐标
MAJOR_CITIES = {
    '北京': (116.4074, 39.9042),
    '上海': (121.4737, 31.2304),
    '广州': (113.2644, 23.1291),
    '深圳': (114.0579, 22.5431),
    '杭州': (120.1551, 30.2741),
    '南京': (118.7969, 32.0603),
    '武汉': (114.3054, 30.5931),
    '成都': (104.0668, 30.5728),
    '重庆': (106.5516, 29.5630),
    '西安': (108.9398, 34.3416),
    '天津': (117.2008, 39.0842),
    '苏州': (120.5853, 31.2989),
    '长沙': (112.9388, 28.2282),
    '郑州': (113.6253, 34.7466),
    '沈阳': (123.4315, 41.8057),
    '青岛': (120.3826, 36.0671),
    '大连': (121.6147, 38.9140),
    '厦门': (118.0894, 24.4798),
    '哈尔滨': (126.5340, 45.8038),
    '济南': (117.1205, 36.6510),
    '石家庄': (114.5149, 38.0423),
    '合肥': (117.2272, 31.8206),
    '太原': (112.5489, 37.8570),
    '呼和浩特': (111.7492, 40.8426),
    '长春': (125.3235, 43.8171),
    '昆明': (102.8329, 24.8801),
    '南宁': (108.3665, 22.8172),
    '贵阳': (106.6302, 26.6477),
    '兰州': (103.8343, 36.0611),
    '银川': (106.2309, 38.4872),
    '西宁': (101.7782, 36.6171),
    '乌鲁木齐': (87.6168, 43.8256),
    '拉萨': (91.1174, 29.6469),
    '海口': (110.1989, 20.0178),
    '三亚': (109.5119, 18.2524)
}


def get_city_coordinates(city_name: str) -> Tuple[float, float]:
    """
    获取城市坐标

    Args:
        city_name: 城市名称

    Returns:
        (经度, 纬度)

    Raises:
        ValueError: 如果城市不存在
    """
    if city_name not in MAJOR_CITIES:
        raise ValueError(f"城市 '{city_name}' 不在数据库中")
    return MAJOR_CITIES[city_name]


def get_all_cities() -> List[str]:
    """
    获取所有城市名称列表

    Returns:
        城市名称列表
    """
    return list(MAJOR_CITIES.keys())


if __name__ == '__main__':
    # 示例用法
    print("配置文件模块")

    # 显示所有配置
    config = get_config()
    for key, value in config.items():
        print(f"\n{key.upper()}配置:")
        if hasattr(value, '__dict__'):
            for attr, attr_value in value.__dict__.items():
                if not attr.startswith('_'):
                    print(f"  {attr}: {attr_value}")

    # 测试城市坐标
    print(f"\n北京坐标: {get_city_coordinates('北京')}")
    print(f"城市总数: {len(get_all_cities())}")
