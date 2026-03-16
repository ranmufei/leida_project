"""
多项式坐标映射器

基于地面控制点数据拟合的最优多项式变换
不假设特定投影类型，直接使用数据拟合
"""
import numpy as np
from PIL import Image
from typing import Tuple, Dict, Optional
from pathlib import Path


class PolynomialRadarMapper:
    """
    多项式雷达坐标映射器

    使用多项式拟合进行像素坐标与经纬度的双向转换
    """

    # 基于10个地面控制点拟合的最优参数（三次多项式）
    # X: x = a0 + a1 * lon (线性)
    _X_A0 = -1600.17
    _X_A1 = 22.1290

    # Y: y = b0 + b1 * lat + b2 * lat² + b3 * lat³ (三次多项式)
    _Y_B0 = 1974.13
    _Y_B1 = -67.2142
    _Y_B2 = 1.254099
    _Y_B3 = -0.01346331

    # 参数的逆变换（用于 pixel_to_geo）
    # lon = (x - a0) / a1
    _LON_A0_INV = -_X_A0 / _X_A1  # 72.33
    _LON_A1_INV = 1.0 / _X_A1     # 0.0452

    def __init__(self, image_path: str, legend_height: int = None):
        """
        初始化多项式映射器

        Args:
            image_path: 雷达图片路径
            legend_height: 底部图例区域高度（像素）
        """
        self.image_path = Path(image_path)
        self.image = Image.open(image_path)
        self.width, self.height = self.image.size

        # 图例区域高度（底部）
        self.legend_height = legend_height if legend_height is not None else 120
        self.map_height = self.height - self.legend_height

        print(f"🗺️  多项式投影映射器初始化:")
        print(f"   图片尺寸: {self.width}x{self.height}")
        print(f"   地图区域: {self.width}x{self.map_height}")
        print(f"   变换公式:")
        print(f"     X: x = {self._X_A0:.2f} + {self._X_A1:.4f} * lon")
        print(f"     Y: y = {self._Y_B0:.2f} + {self._Y_B1:.4f}*lat + {self._Y_B2:.6f}*lat² + {self._Y_B3:.8f}*lat³")

    def geo_to_pixel(self, lon: float, lat: float) -> Tuple[int, int]:
        """
        经纬度转像素坐标

        Args:
            lon: 经度
            lat: 纬度

        Returns:
            (像素X坐标, 像素Y坐标)
        """
        # X方向：线性变换
        pixel_x = int(self._X_A0 + self._X_A1 * lon)

        # Y方向：三次多项式变换
        pixel_y = int(self._Y_B0 + self._Y_B1 * lat + self._Y_B2 * lat**2 + self._Y_B3 * lat**3)

        # 边界检查
        pixel_x = max(0, min(pixel_x, self.width - 1))
        pixel_y = max(0, min(pixel_y, self.map_height - 1))

        return pixel_x, pixel_y

    def pixel_to_geo(self, pixel_x: float, pixel_y: float) -> Tuple[float, float]:
        """
        像素坐标转经纬度

        Args:
            pixel_x: 像素X坐标
            pixel_y: 像素Y坐标

        Returns:
            (经度, 纬度)
        """
        # X方向：逆线性变换
        lon = self._LON_A0_INV + self._LON_A1_INV * pixel_x

        # Y方向：求解三次方程 y = b0 + b1*lat + b2*lat² + b3*lat³
        # 即: b3*lat³ + b2*lat² + b1*lat + (b0 - y) = 0
        # 使用数值方法求解

        # 牛顿迭代法求解三次方程
        def cubic_equation(lat):
            return self._Y_B3 * lat**3 + self._Y_B2 * lat**2 + self._Y_B1 * lat + self._Y_B0 - pixel_y

        def cubic_derivative(lat):
            return 3 * self._Y_B3 * lat**2 + 2 * self._Y_B2 * lat + self._Y_B1

        # 初始猜测值（使用线性近似）
        if self._Y_B1 != 0:
            lat_guess = (pixel_y - self._Y_B0) / self._Y_B1
        else:
            lat_guess = 30.0  # 默认 guesses

        # 限制在合理范围内
        lat_guess = max(10, min(60, lat_guess))

        # 牛顿迭代
        lat = lat_guess
        for _ in range(20):  # 最多20次迭代
            f_val = cubic_equation(lat)
            f_deriv = cubic_derivative(lat)

            if abs(f_deriv) < 1e-10:
                break

            lat_new = lat - f_val / f_deriv

            if abs(lat_new - lat) < 1e-6:
                break

            lat = lat_new

        # 确保结果在合理范围内
        lat = max(0, min(lat, 60))

        return lon, lat

    def is_valid_coordinate(self, lon: float, lat: float) -> bool:
        """
        检查经纬度是否在图片范围内

        Args:
            lon: 经度
            lat: 纬度

        Returns:
            是否有效
        """
        # 使用拟合的参数范围
        lon_min, lon_max = 70, 135
        lat_min, lat_max = 15, 55

        return (lon_min <= lon <= lon_max and
                lat_min <= lat <= lat_max)

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
            'projection': 'polynomial_cubic',
            'lon_min': 70.0,
            'lon_max': 135.0,
            'lat_min': 15.0,
            'lat_max': 55.0,
            'image_size': (self.width, self.height),
            'map_height': self.map_height,
            'legend_height': self.legend_height,
            'formula_x': f'x = {self._X_A0:.2f} + {self._X_A1:.4f} * lon',
            'formula_y': f'y = {self._Y_B0:.2f} + {self._Y_B1:.4f}*lat + {self._Y_B2:.6f}*lat² + {self._Y_B3:.8f}*lat³'
        }
