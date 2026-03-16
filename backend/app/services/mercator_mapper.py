"""
墨卡托投影坐标映射器

支持标准墨卡托投影的像素坐标与经纬度转换
"""
import numpy as np
from PIL import Image
from typing import Tuple, Dict, Optional
from pathlib import Path


class MercatorRadarMapper:
    """
    墨卡托投影雷达坐标映射器

    使用墨卡托投影公式进行像素坐标与经纬度的双向转换
    """

    def __init__(self, image_path: str, legend_height: int = None,
                 lon_min: float = None, lon_max: float = None,
                 lat_min: float = None, lat_max: float = None):
        """
        初始化墨卡托投影映射器

        Args:
            image_path: 雷达图片路径
            legend_height: 底部图例区域高度（像素）
            lon_min, lon_max: 经度范围（如果为None，自动计算）
            lat_min, lat_max: 纬度范围（如果为None，自动计算）
        """
        self.image_path = Path(image_path)
        self.image = Image.open(image_path)
        self.width, self.height = self.image.size

        # 图例区域高度（底部）
        self.legend_height = legend_height if legend_height is not None else 120
        self.map_height = self.height - self.legend_height

        # 墨卡托投影的纬度限制（约±85.05度，避免极点处的无穷大）
        self.MERCATOR_MAX_LAT = 85.05112878

        # 设置经纬度范围
        if lon_min is not None and lon_max is not None and lat_min is not None and lat_max is not None:
            self.lon_min = lon_min
            self.lon_max = lon_max
            self.lat_min = max(lat_min, -self.MERCATOR_MAX_LAT)
            self.lat_max = min(lat_max, self.MERCATOR_MAX_LAT)
        else:
            # 默认范围：基于9个地面控制点（含边缘城市）拟合的最优参数
            self.lon_min = 72.2
            self.lon_max = 133.5
            self.lat_min = 17.0
            self.lat_max = 51.8

        # 计算墨卡托投影的Y坐标范围
        self.y_min = self._lat_to_mercator_y(self.lat_min)
        self.y_max = self._lat_to_mercator_y(self.lat_max)

        print(f"🗺️  墨卡托投影映射器初始化:")
        print(f"   图片尺寸: {self.width}x{self.height}")
        print(f"   地图区域: {self.width}x{self.map_height}")
        print(f"   经度范围: [{self.lon_min:.2f}, {self.lon_max:.2f}]")
        print(f"   纬度范围: [{self.lat_min:.2f}, {self.lat_max:.2f}]")

    def _lat_to_mercator_y(self, lat: float) -> float:
        """
        将纬度转换为墨卡托投影的Y坐标

        公式: y = ln(tan(π/4 + φ/2))

        Args:
            lat: 纬度（度）

        Returns:
            墨卡托Y坐标
        """
        lat_rad = np.radians(lat)
        return np.log(np.tan(np.pi / 4 + lat_rad / 2))

    def _mercator_y_to_lat(self, mercator_y: float) -> float:
        """
        将墨卡托投影的Y坐标转换为纬度

        公式: φ = 2 * arctan(e^y) - π/2

        Args:
            mercator_y: 墨卡托Y坐标

        Returns:
            纬度（度）
        """
        lat_rad = 2 * np.arctan(np.exp(mercator_y)) - np.pi / 2
        return np.degrees(lat_rad)

    def pixel_to_geo(self, pixel_x: float, pixel_y: float) -> Tuple[float, float]:
        """
        像素坐标转经纬度（使用墨卡托投影）

        Args:
            pixel_x: 像素X坐标
            pixel_y: 像素Y坐标

        Returns:
            (经度, 纬度)
        """
        # 经度：线性映射
        lon = self.lon_min + (pixel_x / self.width) * (self.lon_max - self.lon_min)

        # 纬度：使用有效地图区域高度进行墨卡托投影映射
        # 首先将像素Y映射到墨卡托Y坐标
        mercator_y = self.y_max - (pixel_y / self.map_height) * (self.y_max - self.y_min)

        # 然后转换为纬度
        lat = self._mercator_y_to_lat(mercator_y)

        return lon, lat

    def geo_to_pixel(self, lon: float, lat: float) -> Tuple[int, int]:
        """
        经纬度转像素坐标（使用墨卡托投影）

        Args:
            lon: 经度
            lat: 纬度

        Returns:
            (像素X坐标, 像素Y坐标)
        """
        # 限制纬度范围
        lat = max(-self.MERCATOR_MAX_LAT, min(self.MERCATOR_MAX_LAT, lat))

        # 经度：线性映射
        x_ratio = (lon - self.lon_min) / (self.lon_max - self.lon_min)
        pixel_x = int(x_ratio * self.width)

        # 纬度：使用墨卡托投影
        mercator_y = self._lat_to_mercator_y(lat)
        y_ratio = (self.y_max - mercator_y) / (self.y_max - self.y_min)
        pixel_y = int(y_ratio * self.map_height)

        # 边界检查
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
            'projection': 'mercator',
            'lon_min': self.lon_min,
            'lon_max': self.lon_max,
            'lat_min': self.lat_min,
            'lat_max': self.lat_max,
            'lon_span': self.lon_max - self.lon_min,
            'lat_span': self.lat_max - self.lat_min,
            'image_size': (self.width, self.height),
            'map_height': self.map_height,
            'legend_height': self.legend_height
        }
