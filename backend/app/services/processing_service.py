"""
雷达数据处理服务

实现坐标映射、色标解析、dBZ转换等功能
"""
import numpy as np
from PIL import Image
from typing import Tuple, Dict, Optional, List
from pathlib import Path
import cv2
import sys
import os

from app.core.config import settings
from sqlalchemy.orm import Session

# 导入三次样条插值映射器（高精度：±1px）
from app.services.spline_mapper import SplineCoordinateMapper

# 添加 src 目录到路径以导入 mapper
# 从 backend/app/services/processing_service.py 到 src/preprocessing
# 需要向上3级到项目根目录，然后进入 src/preprocessing
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_current_dir, '../../../'))
_src_dir = os.path.join(_project_root, 'src/preprocessing')
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

try:
    from mapper import CalibratedRadarMapper
    print(f"✅ 成功导入 CalibratedRadarMapper 从: {_src_dir}")
except ImportError as e:
    print(f"❌ 导入 CalibratedRadarMapper 失败: {e}")
    print(f"   _src_dir = {_src_dir}")
    print(f"   sys.path = {sys.path[:3]}")
    CalibratedRadarMapper = None


class CoordinateMapper:
    """坐标映射器 - 经纬度与像素坐标转换"""

    def __init__(self, image_path: str, legend_height: int = None):
        """
        初始化映射器

        Args:
            image_path: 雷达图片路径
            legend_height: 底部图例区域高度（像素），默认从配置读取
        """
        self.image_path = Path(image_path)
        self.image = Image.open(image_path)
        self.width, self.height = self.image.size

        # 图例区域高度（底部）- 从配置读取或使用默认值
        self.legend_height = legend_height if legend_height is not None else getattr(settings, 'RADAR_IMAGE_LEGEND_HEIGHT', 120)

        # 有效地图区域高度（排除底部图例）
        self.map_height = self.height - self.legend_height

        # 中国气象局标准网格参数
        self.grid_resolution = 0.01  # 度
        self.default_lon_range = 70.0  # 经度跨度
        self.default_lat_range = 40.0  # 纬度跨度
        self.center_lon = 105.0  # 中国中心经度
        self.center_lat = 35.0  # 中国中心纬度

        # 计算边界
        self._calculate_bounds()

    def _calculate_bounds(self):
        """计算地理边界"""
        aspect_ratio = self.width / self.height

        if aspect_ratio > 1.5:  # 横向图片
            self.lon_span = self.default_lon_range
            self.lat_span = self.lon_span / aspect_ratio
        else:  # 纵向图片或接近方形
            self.lat_span = self.default_lat_range
            self.lon_span = self.lat_span * aspect_ratio

        self.lon_min = self.center_lon - self.lon_span / 2
        self.lon_max = self.center_lon + self.lon_span / 2
        self.lat_min = self.center_lat - self.lat_span / 2
        self.lat_max = self.center_lat + self.lat_span / 2

        self.lon_span_total = self.lon_max - self.lon_min
        self.lat_span_total = self.lat_max - self.lat_min

    def pixel_to_geo(self, pixel_x: float, pixel_y: float) -> Tuple[float, float]:
        """
        像素坐标转经纬度

        Args:
            pixel_x: 像素X坐标
            pixel_y: 像素Y坐标

        Returns:
            (经度, 纬度)
        """
        lon = self.lon_min + (pixel_x / self.width) * self.lon_span_total
        # 使用有效地图区域高度进行计算（排除底部图例）
        lat = self.lat_max - (pixel_y / self.map_height) * self.lat_span_total
        return lon, lat

    def geo_to_pixel(self, lon: float, lat: float) -> Tuple[int, int]:
        """
        经纬度转像素坐标

        Args:
            lon: 经度
            lat: 纬度

        Returns:
            (像素X坐标, 像素Y坐标)
        """
        x_ratio = (lon - self.lon_min) / self.lon_span_total
        y_ratio = (self.lat_max - lat) / self.lat_span_total

        # 使用有效地图区域高度进行计算（排除底部图例）
        pixel_x = int(x_ratio * self.width)
        pixel_y = int(y_ratio * self.map_height)

        # 边界检查（Y坐标不超过有效地图区域）
        pixel_x = max(0, min(pixel_x, self.width - 1))
        pixel_y = max(0, min(pixel_y, self.map_height - 1))

        return pixel_x, pixel_y

    def is_valid_coordinate(self, lon: float, lat: float) -> bool:
        """
        检查经纬度是否在图片范围内

        Args:
            lon: 经度
            lat: 纬度

        Returns:
            是否有效
        """
        return (self.lon_min <= lon <= self.lon_max and
                self.lat_min <= lat <= self.lat_max)

    def get_pixel_value(self, lon: float, lat: float) -> Optional[Tuple[int, int, int]]:
        """
        获取指定经纬度的像素RGB值

        Args:
            lon: 经度
            lat: 纬度

        Returns:
            (R, G, B) 值，超出范围返回None
        """
        if not self.is_valid_coordinate(lon, lat):
            return None

        pixel_x, pixel_y = self.geo_to_pixel(lon, lat)
        pixel = self.image.getpixel((pixel_x, pixel_y))

        # 处理RGBA或RGB格式
        if isinstance(pixel, (tuple, list)):
            if len(pixel) == 4:  # RGBA格式
                return (pixel[0], pixel[1], pixel[2])
            elif len(pixel) == 3:  # RGB格式
                return pixel
            else:
                # 处理其他格式，只取前3个值
                return tuple(pixel[:3]) if len(pixel) >= 3 else (255, 255, 255)
        else:
            # 单通道图像
            return (pixel, pixel, pixel) if isinstance(pixel, int) else (255, 255, 255)

    def get_coverage_info(self) -> Dict:
        """
        获取覆盖范围信息

        Returns:
            覆盖信息字典
        """
        return {
            'lon_min': self.lon_min,
            'lon_max': self.lon_max,
            'lat_min': self.lat_min,
            'lat_max': self.lat_max,
            'lon_span': self.lon_span_total,
            'lat_span': self.lat_span_total,
            'resolution_lon': self.lon_span_total / self.width,
            'resolution_lat': self.lat_span_total / self.map_height,
            'image_size': (self.width, self.height),
            'map_height': self.map_height,
            'legend_height': self.legend_height
        }


class ColorScaleParser:
    """色标解析器 - RGB值转dBZ值"""

    # 中国气象局组合反射率标准色标（基于实际图片色块）
    STANDARD_COLOR_SCALE = {
        'dbz_05_10': {'rgb': (78, 156, 240), 'dbz_range': (5, 10), 'hex': '#4E9CF0', 'description': '5-10'},
        'dbz_10_15': {'rgb': (100, 230, 234), 'dbz_range': (10, 15), 'hex': '#64E6EA', 'description': '10-15'},
        'dbz_15_20': {'rgb': (109, 251, 61), 'dbz_range': (15, 20), 'hex': '#6DFB3D', 'description': '15-20'},
        'dbz_20_25': {'rgb': (78, 216, 0), 'dbz_range': (20, 25), 'hex': '#4ED800', 'description': '20-25'},
        'dbz_25_30': {'rgb': (49, 145, 0), 'dbz_range': (25, 30), 'hex': '#319100', 'description': '25-30'},
        'dbz_30_35': {'rgb': (250, 255, 0), 'dbz_range': (30, 35), 'hex': '#FAFF00', 'description': '30-35'},
        'dbz_35_40': {'rgb': (231, 204, 2), 'dbz_range': (35, 40), 'hex': '#E7C002', 'description': '35-40'},
        'dbz_40_45': {'rgb': (241, 143, 5), 'dbz_range': (40, 45), 'hex': '#F18F05', 'description': '40-45'},
        'dbz_45_50': {'rgb': (237, 0, 5), 'dbz_range': (45, 50), 'hex': '#ED0005', 'description': '45-50'},
        'dbz_50_55': {'rgb': (214, 0, 0), 'dbz_range': (50, 55), 'hex': '#D60000', 'description': '50-55'},
        'dbz_55_60': {'rgb': (192, 0, 0), 'dbz_range': (55, 60), 'hex': '#C00000', 'description': '55-60'},
        'dbz_60_65': {'rgb': (242, 2, 240), 'dbz_range': (60, 65), 'hex': '#F202F0', 'description': '60-65'},
        'dbz_65_70': {'rgb': (150, 0, 181), 'dbz_range': (65, 70), 'hex': '#9600B5', 'description': '65-70'},
        'dbz_70_plus': {'rgb': (173, 145, 240), 'dbz_range': (70, 75), 'hex': '#AD91F0', 'description': '70+'},
        # 无回波区域（灰色背景）
        'no_echo': {'rgb': (0, 0, 0), 'dbz_range': (0, 5), 'hex': '#000000', 'description': '无回波'},
    }

    def __init__(self, custom_color_scale: Optional[Dict] = None):
        """
        初始化色标解析器

        Args:
            custom_color_scale: 自定义色标
        """
        self.color_scale = custom_color_scale or self.STANDARD_COLOR_SCALE
        self._build_color_lookup_table()

    def _build_color_lookup_table(self):
        """构建颜色查找表"""
        self.color_list = []
        self.dbz_ranges = []

        for level, data in self.color_scale.items():
            self.color_list.append(data['rgb'])
            self.dbz_ranges.append(data['dbz_range'])

        self.color_array = np.array(self.color_list)

    def rgb_to_dbz(self, rgb: Tuple[int, int, int]) -> float:
        """
        将RGB值转换为dBZ值

        Args:
            rgb: RGB元组

        Returns:
            dBZ值
        """
        r, g, b = rgb

        # 检查是否为无回波区域（灰色背景）
        rgb_std = np.std([r, g, b])
        rgb_mean = np.mean([r, g, b])
        rgb_range = max(r, g, b) - min(r, g, b)

        # 无回波判断：RGB标准差小于15（颜色单一，接近灰色）
        # 且RGB范围小于30（确保是灰色而不是彩色）
        if rgb_std < 15 and rgb_range < 30:
            return 2.5  # 无回波，返回0-5范围的中间值

        # 使用最近邻颜色匹配
        return self._nearest_color_match(rgb)

    def _nearest_color_match(self, rgb: Tuple[int, int, int]) -> float:
        """
        最近邻颜色匹配

        Args:
            rgb: RGB元组

        Returns:
            匹配的dBZ值
        """
        rgb_array = np.array(rgb)
        distances = np.linalg.norm(self.color_array - rgb_array, axis=1)
        nearest_idx = np.argmin(distances)
        dbz_range = self.dbz_ranges[nearest_idx]
        return sum(dbz_range) / 2

    def dbz_to_category(self, dbz: float) -> str:
        """
        将dBZ值转换为强度等级分类

        Args:
            dbz: dBZ值

        Returns:
            强度等级 (匹配数据库枚举: 'no_data', 'weak', 'moderate', 'strong', 'severe', 'extreme')
        """
        if dbz < 5 or dbz == 2.5:
            return 'no_data'      # 无回波/极弱 (0-5)
        elif dbz < 20:
            return 'weak'         # 弱回波 (5-20)
        elif dbz < 35:
            return 'moderate'     # 中等回波 (20-35)
        elif dbz < 45:
            return 'strong'       # 强回波 (35-45)
        elif dbz < 55:
            return 'severe'       # 严重回波 (45-55)
        else:
            return 'extreme'      # 极端回波 (55+)

    def get_cloud_impact_factor(self, dbz: float) -> float:
        """
        计算云影响因子（用于光伏预测）

        Args:
            dbz: dBZ值

        Returns:
            影响因子 (0.0-1.0)
        """
        # 基于新的dBZ范围计算更精确的影响因子
        if dbz < 5:
            return 1.0
        elif dbz < 10:
            return 1.0
        elif dbz < 15:
            return 0.95 - (dbz - 10) / 5 * 0.10  # 0.95-0.85
        elif dbz < 20:
            return 0.85 - (dbz - 15) / 5 * 0.20  # 0.85-0.65
        elif dbz < 25:
            return 0.65 - (dbz - 20) / 5 * 0.30  # 0.65-0.35
        elif dbz < 30:
            return 0.35 - (dbz - 25) / 5 * 0.25  # 0.35-0.10
        elif dbz < 35:
            return 0.10 - (dbz - 30) / 5 * 0.08  # 0.10-0.02
        elif dbz < 40:
            return 0.02 - (dbz - 35) / 5 * 0.02  # 0.02-0.00
        else:
            return 0.0  # dBZ >= 40，完全阻挡


class RadarDataProcessor:
    """雷达数据处理器"""

    def __init__(self, use_calibration: bool = True, db: Session = None):
        """
        初始化处理器

        Args:
            use_calibration: 是否使用校准参数
            db: 数据库会话（用于加载校准参数）
        """
        self.color_parser = ColorScaleParser()
        self.use_calibration = use_calibration
        self.db = db
        self._affine_params = None

        # 如果启用校准，加载校准参数
        if use_calibration and db:
            self._load_calibration_params()

    def _load_calibration_params(self):
        """从数据库加载激活的校准参数"""
        try:
            from app.models.calibration import CalibrationParams
            from sqlalchemy import desc

            calibration = self.db.query(CalibrationParams).filter(
                CalibrationParams.is_active == True
            ).order_by(desc(CalibrationParams.created_at)).first()

            if calibration:
                self._affine_params = {
                    'lon': [calibration.affine_lon_a0, calibration.affine_lon_a1, calibration.affine_lon_a2],
                    'lat': [calibration.affine_lat_b0, calibration.affine_lat_b1, calibration.affine_lat_b2]
                }
                print(f"✅ 已加载校准参数: ID={calibration.id}")
            else:
                print("⚠️  未找到激活的校准参数，使用默认映射器")
        except Exception as e:
            print(f"⚠️  加载校准参数失败: {e}")

    def _create_mapper(self, image_path: str) -> CoordinateMapper:
        """
        创建坐标映射器

        Args:
            image_path: 雷达图片路径

        Returns:
            坐标映射器实例
        """
        # 使用三次样条插值映射器（高精度：±1px）
        return SplineCoordinateMapper(image_path)

    def process_site_data(
        self,
        image_path: str,
        site_id: int,
        longitude: float,
        latitude: float,
        observation_time,
        sample_window: int = 3
    ) -> Dict:
        """
        处理单个站点的雷达数据

        Args:
            image_path: 雷达图片路径
            site_id: 站点ID
            longitude: 经度
            latitude: 纬度
            observation_time: 观测时间
            sample_window: 采样窗口大小 (3=3x3, 5=5x5)

        Returns:
            处理结果
        """
        # 创建坐标映射器（支持校准）
        mapper = self._create_mapper(image_path)

        # 检查坐标是否有效
        if not mapper.is_valid_coordinate(longitude, latitude):
            return {
                'site_id': site_id,
                'status': 'out_of_range',
                'error': '坐标超出图片范围'
            }

        # 获取像素坐标
        pixel_x, pixel_y = mapper.geo_to_pixel(longitude, latitude)

        # 使用区域平均采样获取像素值
        rgb_value = self._get_averaged_pixel_value(mapper, pixel_x, pixel_y, sample_window)
        if rgb_value is None:
            return {
                'site_id': site_id,
                'status': 'error',
                'error': '无法获取像素值'
            }

        # 转换为dBZ
        dbz_value = self.color_parser.rgb_to_dbz(rgb_value)
        dbz_category = self.color_parser.dbz_to_category(dbz_value)
        cloud_impact = self.color_parser.get_cloud_impact_factor(dbz_value)

        return {
            'site_id': site_id,
            'status': 'success',
            'observation_time': observation_time,
            'longitude': longitude,
            'latitude': latitude,
            'pixel_x': pixel_x,
            'pixel_y': pixel_y,
            'dbz_value': round(dbz_value, 2),
            'dbz_category': dbz_category,
            'cloud_impact_factor': round(cloud_impact, 3),
            'rgb_value': f"{rgb_value[0]},{rgb_value[1]},{rgb_value[2]}",
            'data_quality': 'good',
            'data_source': 'actual'
        }

    def _get_averaged_pixel_value(self, mapper, center_x: int, center_y: int, window_size: int = 3) -> Optional[Tuple[int, int, int]]:
        """
        获取区域平均的RGB值

        使用窗口区域内的平均颜色，避免单点采样的偶然性

        Args:
            mapper: 坐标映射器
            center_x: 中心X坐标
            center_y: 中心Y坐标
            window_size: 窗口大小 (3=3x3, 5=5x5)

        Returns:
            平均RGB值
        """
        if window_size not in [1, 3, 5]:
            window_size = 3

        if window_size == 1:
            return mapper.get_pixel_value(center_x, center_y)

        # 计算窗口边界
        half = window_size // 2
        x_start = max(0, center_x - half)
        x_end = min(mapper.width, center_x + half + 1)
        y_start = max(0, center_y - half)
        y_end = min(mapper.map_height, center_y + half + 1)

        # 收集窗口内所有有效像素
        rgb_values = []
        for y in range(y_start, y_end):
            for x in range(x_start, x_end):
                pixel = mapper.image.getpixel((x, y))
                if isinstance(pixel, (tuple, list)) and len(pixel) >= 3:
                    rgb_values.append((pixel[0], pixel[1], pixel[2]))

        if not rgb_values:
            return None

        # 计算平均RGB
        avg_r = int(np.mean([r for r, g, b in rgb_values]))
        avg_g = int(np.mean([g for r, g, b in rgb_values]))
        avg_b = int(np.mean([b for r, g, b in rgb_values]))

        return (avg_r, avg_g, avg_b)

    def batch_process_sites(
        self,
        image_path: str,
        sites: List[Dict],
        observation_time
    ) -> List[Dict]:
        """
        批量处理多个站点

        Args:
            image_path: 雷达图片路径
            sites: 站点列表 [{'site_id': 1, 'longitude': 116.4, 'latitude': 39.9}, ...]
            observation_time: 观测时间

        Returns:
            处理结果列表
        """
        results = []
        mapper = CoordinateMapper(image_path)

        for site in sites:
            result = self.process_site_data(
                image_path=image_path,
                site_id=site['site_id'],
                longitude=site['longitude'],
                latitude=site['latitude'],
                observation_time=observation_time
            )
            results.append(result)

        return results
