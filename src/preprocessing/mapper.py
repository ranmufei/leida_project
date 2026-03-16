"""
气象雷达图片坐标映射模块

实现经纬度与像素坐标之间的双向转换，基于中国气象局标准网格参数。
"""

import numpy as np
from PIL import Image
from typing import Tuple, Dict, Optional


class ChinaRadarMapper:
    """
    中国气象局雷达图片坐标映射器

    基于规则经纬度网格建立像素-经纬度映射关系
    网格分辨率：0.01° × 0.01°
    """

    # 中国气象局雷达拼图标准参数
    GRID_RESOLUTION = 0.01  # 度
    DEFAULT_LON_RANGE = 70.0  # 经度跨度
    DEFAULT_LAT_RANGE = 40.0  # 纬度跨度
    CENTER_LON = 105.0  # 中国中心经度
    CENTER_LAT = 35.0   # 中国中心纬度

    def __init__(self, image_path: str, custom_bounds: Optional[Dict] = None, legend_height: int = 120):
        """
        初始化映射器

        Args:
            image_path: 雷达图片路径
            custom_bounds: 自定义边界 {'lon_min': float, 'lon_max': float,
                                        'lat_min': float, 'lat_max': float}
            legend_height: 底部图例区域高度（像素）
        """
        self.image_path = image_path
        self.image = Image.open(image_path)
        self.width, self.height = self.image.size

        # 图例区域高度（底部）
        self.legend_height = legend_height

        # 有效地图区域高度（排除底部图例）
        self.map_height = self.height - legend_height

        # 设置坐标范围
        if custom_bounds:
            self.lon_min = custom_bounds['lon_min']
            self.lon_max = custom_bounds['lon_max']
            self.lat_min = custom_bounds['lat_min']
            self.lat_max = custom_bounds['lat_max']
        else:
            # 根据图片尺寸和标准参数推算边界
            self._calculate_bounds()

        # 计算经纬度跨度
        self.lon_span = self.lon_max - self.lon_min
        self.lat_span = self.lat_max - self.lat_min

    def _calculate_bounds(self):
        """根据图片尺寸计算地理边界"""
        aspect_ratio = self.width / self.height

        # 根据宽高比确定覆盖范围
        if aspect_ratio > 1.5:  # 横向图片
            self.lon_span = self.DEFAULT_LON_RANGE
            self.lat_span = self.lon_span / aspect_ratio
        else:  # 纵向图片或接近方形
            self.lat_span = self.DEFAULT_LAT_RANGE
            self.lon_span = self.lat_span * aspect_ratio

        # 计算边界
        self.lon_min = self.CENTER_LON - self.lon_span / 2
        self.lon_max = self.CENTER_LON + self.lon_span / 2
        self.lat_min = self.CENTER_LAT - self.lat_span / 2
        self.lat_max = self.CENTER_LAT + self.lat_span / 2

    def pixel_to_geo(self, pixel_x: float, pixel_y: float) -> Tuple[float, float]:
        """
        像素坐标转经纬度

        Args:
            pixel_x: 像素X坐标
            pixel_y: 像素Y坐标

        Returns:
            (经度, 纬度)
        """
        lon = self.lon_min + (pixel_x / self.width) * self.lon_span
        # 使用有效地图区域高度进行计算（排除底部图例）
        lat = self.lat_max - (pixel_y / self.map_height) * self.lat_span
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
        # 计算相对位置
        x_ratio = (lon - self.lon_min) / self.lon_span
        y_ratio = (self.lat_max - lat) / self.lat_span

        # 转换为像素坐标（使用有效地图区域高度）
        pixel_x = int(x_ratio * self.width)
        pixel_y = int(y_ratio * self.map_height)

        # 边界检查（Y坐标不超过有效地图区域）
        pixel_x = max(0, min(pixel_x, self.width - 1))
        pixel_y = max(0, min(pixel_y, self.map_height - 1))

        return pixel_x, pixel_y

    def get_pixel_value(self, lon: float, lat: float) -> Tuple[int, int, int]:
        """
        获取指定经纬度的像素RGB值

        Args:
            lon: 经度
            lat: 纬度

        Returns:
            (R, G, B) 值
        """
        pixel_x, pixel_y = self.geo_to_pixel(lon, lat)
        return self.image.getpixel((pixel_x, pixel_y))

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

    def get_coverage_info(self) -> Dict:
        """
        获取覆盖范围信息

        Returns:
            包含边界、分辨率等信息的字典
        """
        return {
            'lon_min': self.lon_min,
            'lon_max': self.lon_max,
            'lat_min': self.lat_min,
            'lat_max': self.lat_max,
            'lon_span': self.lon_span,
            'lat_span': self.lat_span,
            'resolution_lon': self.lon_span / self.width,
            'resolution_lat': self.lat_span / self.map_height,
            'image_size': (self.width, self.height),
            'map_height': self.map_height,
            'legend_height': self.legend_height
        }

    def get_neighborhood_pixels(self, lon: float, lat: float,
                               radius_km: float = 20) -> np.ndarray:
        """
        获取指定经纬度周边邻域的像素值

        Args:
            lon: 中心经度
            lat: 中心纬度
            radius_km: 半径(公里)

        Returns:
            邻域像素值数组
        """
        # 将公里转换为度数 (粗略估算: 1度 ≈ 111km)
        radius_deg = radius_km / 111.0

        # 计算邻域边界
        pixel_x, pixel_y = self.geo_to_pixel(lon, lat)

        # 计算像素半径
        pixel_radius = int(radius_deg / self.lon_span * self.width)

        # 提取邻域
        x_min = max(0, pixel_x - pixel_radius)
        x_max = min(self.width, pixel_x + pixel_radius + 1)
        y_min = max(0, pixel_y - pixel_radius)
        y_max = min(self.height, pixel_y + pixel_radius + 1)

        # 提取像素数组
        neighborhood = np.array(self.image.crop((x_min, y_min, x_max, y_max)))

        return neighborhood


class CalibratedRadarMapper(ChinaRadarMapper):
    """
    可校准的雷达图片映射器

    支持通过控制点进行精确校准
    使用仿射变换: lon = a0 + a1*x + a2*y, lat = b0 + b1*x + b2*y
    """

    def __init__(self, image_path: str, affine_params: dict = None):
        """
        初始化可校准映射器

        Args:
            image_path: 雷达图片路径
            affine_params: 预设的仿射变换参数 {'lon': [a0, a1, a2], 'lat': [b0, b1, b2]}
        """
        super().__init__(image_path)
        self.control_points = []  # 控制点列表 [(pixel_x, pixel_y, lon, lat), ...]
        self.calibrated = False
        self.affine_params = affine_params  # {'lon': [a0, a1, a2], 'lat': [b0, b1, b2]}
        if affine_params:
            self.calibrated = True

    def add_control_point(self, pixel_x: int, pixel_y: int, lon: float, lat: float):
        """
        添加控制点

        Args:
            pixel_x: 像素X坐标
            pixel_y: 像素Y坐标
            lon: 对应经度
            lat: 对应纬度
        """
        self.control_points.append((pixel_x, pixel_y, lon, lat))
        self.calibrated = False  # 新增控制点后需要重新校准

    def calibrate(self):
        """
        基于控制点校准坐标映射

        使用最小二乘法拟合仿射变换参数:
        lon = a0 + a1*x + a2*y
        lat = b0 + b1*x + b2*y
        """
        if len(self.control_points) < 3:
            raise ValueError("至少需要3个控制点进行校准")

        # 提取坐标数据，构建设计矩阵 [1, x, y]
        pixel_coords = np.array([[cp[0], cp[1], 1] for cp in self.control_points])
        lons = np.array([cp[2] for cp in self.control_points])
        lats = np.array([cp[3] for cp in self.control_points])

        # 最小二乘拟合: lon = [a0, a1, a2] · [1, x, y]^T
        affine_lon, _, _, _ = np.linalg.lstsq(pixel_coords, lons, rcond=None)

        # 最小二乘拟合: lat = [b0, b1, b2] · [1, x, y]^T
        affine_lat, _, _, _ = np.linalg.lstsq(pixel_coords, lats, rcond=None)

        self.affine_params = {
            'lon': affine_lon,  # [a0, a1, a2]
            'lat': affine_lat   # [b0, b1, b2]
        }
        self.calibrated = True

        # 打印拟合误差（用于验证）
        residuals = []
        for cp in self.control_points:
            pred_lon, pred_lat = self.pixel_to_geo(cp[0], cp[1])
            error_lon = abs(pred_lon - cp[2])
            error_lat = abs(pred_lat - cp[3])
            residuals.append((error_lon, error_lat))

        avg_error_lon = sum(r[0] for r in residuals) / len(residuals)
        avg_error_lat = sum(r[1] for r in residuals) / len(residuals)
        print(f"校准完成 - 平均误差: lon={avg_error_lon:.6f}°, lat={avg_error_lat:.6f}°")

    def pixel_to_geo(self, pixel_x: float, pixel_y: float) -> Tuple[float, float]:
        """
        像素坐标转经纬度（使用仿射变换校正）

        Args:
            pixel_x: 像素X坐标
            pixel_y: 像素Y坐标

        Returns:
            (经度, 纬度)
        """
        if not self.calibrated or not self.affine_params:
            # 未校准时使用父类方法
            return super().pixel_to_geo(pixel_x, pixel_y)

        # 使用仿射变换: lon = a0 + a1*x + a2*y
        a = self.affine_params['lon']
        b = self.affine_params['lat']

        lon = a[0] + a[1] * pixel_x + a[2] * pixel_y
        lat = b[0] + b[1] * pixel_x + b[2] * pixel_y

        return lon, lat

    def geo_to_pixel(self, lon: float, lat: float) -> Tuple[int, int]:
        """
        经纬度转像素坐标（使用仿射变换逆变换）

        Args:
            lon: 经度
            lat: 纬度

        Returns:
            (像素X坐标, 像素Y坐标)
        """
        if not self.calibrated or not self.affine_params:
            # 未校准时使用父类方法
            return super().geo_to_pixel(lon, lat)

        # 求解逆变换: 从 lon, lat 求 x, y
        # lon = a0 + a1*x + a2*y
        # lat = b0 + b1*x + b2*y
        #
        # 写成矩阵形式:
        # [lon - a0]   [a1  a2] [x]
        # [lat - b0] = [b1  b2] [y]
        #
        # 逆变换:
        # [x]   [a1  a2]^-1 [lon - a0]
        # [y] = [b1  b2]    [lat - b0]

        a = self.affine_params['lon']
        b = self.affine_params['lat']

        # 计算变换矩阵的行列式
        det = a[1] * b[2] - a[2] * b[1]

        if abs(det) < 1e-10:
            # 矩阵奇异，回退到父类方法
            return super().geo_to_pixel(lon, lat)

        # 逆矩阵求解
        inv_det = 1.0 / det

        x = inv_det * ((b[2]) * (lon - a[0]) - a[2] * (lat - b[0]))
        y = inv_det * (-b[1] * (lon - a[0]) + a[1] * (lat - b[0]))

        # 边界检查
        pixel_x = int(round(x))
        pixel_y = int(round(y))
        pixel_x = max(0, min(pixel_x, self.width - 1))
        pixel_y = max(0, min(pixel_y, self.map_height - 1))

        return pixel_x, pixel_y

    def get_affine_params(self) -> dict:
        """获取仿射变换参数"""
        return self.affine_params


def create_mapper_from_image(image_path: str,
                            method: str = 'standard',
                            **kwargs) -> ChinaRadarMapper:
    """
    工厂函数：创建映射器实例

    Args:
        image_path: 图片路径
        method: 映射方法 ('standard' 或 'calibrated')
        **kwargs: 其他参数

    Returns:
        映射器实例
    """
    if method == 'calibrated':
        mapper = CalibratedRadarMapper(image_path)
        # 如果提供了控制点，自动校准
        if 'control_points' in kwargs:
            for cp in kwargs['control_points']:
                mapper.add_control_point(*cp)
            mapper.calibrate()
        return mapper
    else:
        return ChinaRadarMapper(image_path, custom_bounds=kwargs.get('custom_bounds'))


if __name__ == '__main__':
    # 示例用法
    print("雷达坐标映射模块")

    # 示例：创建映射器
    # mapper = ChinaRadarMapper('path/to/radar_image.png')

    # 测试坐标转换
    # lon, lat = mapper.pixel_to_geo(100, 100)
    # print(f"像素 (100, 100) -> 经纬度: {lon}, {lat}")

    # pixel_x, pixel_y = mapper.geo_to_pixel(116.4074, 39.9042)
    # print(f"经纬度 (116.4074, 39.9042) -> 像素: ({pixel_x}, {pixel_y})")

    # 获取覆盖信息
    # info = mapper.get_coverage_info()
    # print(f"覆盖范围: {info}")
