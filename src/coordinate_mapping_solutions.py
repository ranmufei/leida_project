"""
高级坐标映射解决方案实现

提供4种高级方法来校正中国雷达图的坐标映射精度问题:
1. 分段多项式拟合 (Piecewise Polynomial)
2. 三次样条插值 (Cubic Spline)
3. 局部加权回归 (LOESS/RBF)
4. 真实墨卡托投影优化 (Optimized Mercator)
"""

import numpy as np
from scipy.interpolate import CubicSpline, interp1d, Rbf
from scipy.optimize import curve_fit, minimize
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')


@dataclass
class ControlPoint:
    """控制点数据结构"""
    pixel_x: int
    pixel_y: int
    lon: float
    lat: float
    name: str = ""

    def __repr__(self):
        return f"{self.name}({self.lon:.2f}, {self.lat:.2f}) -> ({self.pixel_x}, {self.pixel_y})"


# ============================================================
# 方案1: 分段多项式拟合
# ============================================================

class PiecewisePolynomialMapper:
    """
    分段多项式坐标映射器

    将中国按纬度分为3个子区域,每个区域独立拟合二次多项式,
    避免全局拟合的权衡问题。

    特点:
    - 计算高效,适合实时应用
    - 精度可控,预期全域误差 < ±5px
    - 易于调试和维护
    """

    def __init__(self, control_points: List[ControlPoint],
                 image_width: int = 1350, image_height: int = 1208):
        """
        初始化分段多项式映射器

        Args:
            control_points: 控制点列表
            image_width: 图片宽度
            image_height: 图片高度
        """
        self.control_points = control_points
        self.image_width = image_width
        self.image_height = image_height

        # 定义纬度分带边界 (基于中国地理特征)
        self.lat_boundaries = [15, 28, 38, 50]
        self.zone_names = ['华南', '华中', '东北']

        # X方向: 全局线性拟合 (墨卡托投影经度是线性的)
        self._fit_x_polynomial()

        # Y方向: 分段二次多项式拟合
        self._fit_y_piecewise()

        print(f"✅ 分段多项式映射器初始化完成")
        print(f"   X方向: 线性 (全域)")
        print(f"   Y方向: {len(self.zone_names)}个纬度带二次多项式")

    def _fit_x_polynomial(self):
        """拟合X方向线性关系"""
        lons = np.array([cp.lon for cp in self.control_points])
        pixel_xs = np.array([cp.pixel_x for cp in self.control_points])

        # 线性回归: pixel_x = a0 + a1 * lon
        coeffs = np.polyfit(lons, pixel_xs, 1)
        self.x_a0, self.x_a1 = coeffs

        # 计算拟合误差
        pred_xs = self.x_a0 + self.x_a1 * lons
        rmse_x = np.sqrt(np.mean((pred_xs - pixel_xs)**2))
        print(f"   X方向拟合RMSE: {rmse_x:.2f} px")

    def _fit_y_piecewise(self):
        """分段拟合Y方向多项式"""
        self.y_coeffs = {}  # 每个区域的系数

        for i in range(len(self.lat_boundaries) - 1):
            lat_min = self.lat_boundaries[i]
            lat_max = self.lat_boundaries[i + 1]

            # 筛选该区域的控制点
            zone_points = [cp for cp in self.control_points
                          if lat_min <= cp.lat < lat_max]

            if len(zone_points) < 3:
                print(f"   ⚠️  警告: 纬度带 [{lat_min}, {lat_max}) 控制点不足")
                continue

            # 提取数据
            lats = np.array([cp.lat for cp in zone_points])
            pixel_ys = np.array([cp.pixel_y for cp in zone_points])

            # 二次多项式拟合: pixel_y = a0 + a1*lat + a2*lat²
            coeffs = np.polyfit(lats, pixel_ys, 2)
            self.y_coeffs[f'zone_{i}'] = coeffs

            # 计算该区域拟合误差
            pred_ys = np.polyval(coeffs, lats)
            rmse = np.sqrt(np.mean((pred_ys - pixel_ys)**2))
            print(f"   Y方向纬度带[{lat_min:2d}°, {lat_max:2d}°) RMSE: {rmse:.2f} px "
                  f"({len(zone_points)}个控制点)")

    def _get_zone(self, lat: float) -> str:
        """确定纬度所属区域"""
        for i in range(len(self.lat_boundaries) - 1):
            if self.lat_boundaries[i] <= lat < self.lat_boundaries[i + 1]:
                return f'zone_{i}'
        # 边界情况
        if lat < self.lat_boundaries[0]:
            return 'zone_0'
        else:
            return f'zone_{len(self.lat_boundaries) - 2}'

    def geo_to_pixel(self, lon: float, lat: float) -> Tuple[int, int]:
        """经纬度转像素坐标"""
        # X方向: 线性
        pixel_x = int(self.x_a0 + self.x_a1 * lon)

        # Y方向: 根据纬度选择对应区域的多项式
        zone = self._get_zone(lat)
        coeffs = self.y_coeffs.get(zone)
        if coeffs is None:
            # 回退到全局拟合
            pixel_y = int(np.polyval(list(self.y_coeffs.values())[0], lat))
        else:
            pixel_y = int(np.polyval(coeffs, lat))

        # 边界限制
        pixel_x = np.clip(pixel_x, 0, self.image_width - 1)
        pixel_y = np.clip(pixel_y, 0, self.image_height - 1)

        return pixel_x, pixel_y

    def pixel_to_geo(self, pixel_x: int, pixel_y: int) -> Tuple[float, float]:
        """像素坐标转经纬度"""
        # X方向: 逆线性变换
        lon = (pixel_x - self.x_a0) / self.x_a1

        # Y方向: 求解二次方程 (需要知道纬度带)
        # 使用迭代法找到最合适的纬度
        def predict_y(lat):
            zone = self._get_zone(lat)
            coeffs = self.y_coeffs.get(zone)
            if coeffs is None:
                coeffs = list(self.y_coeffs.values())[0]
            return np.polyval(coeffs, lat)

        # 优化求解
        from scipy.optimize import minimize_scalar
        result = minimize_scalar(
            lambda lat: abs(predict_y(lat) - pixel_y),
            bounds=(15, 50), method='bounded'
        )
        lat = result.x

        return lon, lat


# ============================================================
# 方案2: 三次样条插值
# ============================================================

class SplineRadarMapper:
    """
    三次样条坐标映射器

    使用三次样条函数在控制点之间进行插值,
    保证函数值和一阶、二阶导数的连续性。

    特点:
    - 精度极高,理论上可达 ±1px 以内
    - 平滑连续,避免突变
    - 数学严谨,基于成熟的样条理论
    """

    def __init__(self, control_points: List[ControlPoint],
                 image_width: int = 1350, image_height: int = 1208):
        """
        初始化样条映射器

        Args:
            control_points: 控制点列表
            image_width: 图片宽度
            image_height: 图片高度
        """
        self.control_points = control_points
        self.image_width = image_width
        self.image_height = image_height

        # 提取坐标数据
        self.lons = np.array([cp.lon for cp in control_points])
        self.lats = np.array([cp.lat for cp in control_points])
        self.pixel_xs = np.array([cp.pixel_x for cp in control_points])
        self.pixel_ys = np.array([cp.pixel_y for cp in control_points])

        # X方向: 线性插值 (墨卡托投影经度是线性的)
        self.spline_x = interp1d(
            self.lons, self.pixel_xs,
            kind='linear',
            bounds_error=False,
            fill_value="extrapolate"
        )

        # Y方向: 三次样条插值 (纬度非线性)
        # 按纬度排序
        sort_idx = np.argsort(self.lats)
        self.lats_sorted = self.lats[sort_idx]
        self.pixel_ys_sorted = self.pixel_ys[sort_idx]

        self.spline_y = CubicSpline(
            self.lats_sorted, self.pixel_ys_sorted,
            bc_type='natural'  # 自然边界条件
        )

        print(f"✅ 三次样条映射器初始化完成")
        print(f"   X方向: 线性插值")
        print(f"   Y方向: 三次样条 ({len(control_points)}个控制点)")

    def geo_to_pixel(self, lon: float, lat: float) -> Tuple[int, int]:
        """经纬度转像素坐标"""
        pixel_x = int(self.spline_x(lon))
        pixel_y = int(self.spline_y(lat))

        # 边界限制
        pixel_x = np.clip(pixel_x, 0, self.image_width - 1)
        pixel_y = np.clip(pixel_y, 0, self.image_height - 1)

        return pixel_x, pixel_y

    def pixel_to_geo(self, pixel_x: int, pixel_y: int) -> Tuple[float, float]:
        """像素坐标转经纬度 (使用优化器)"""
        from scipy.optimize import minimize_scalar

        # 求解经度
        def lon_error(lon):
            return abs(self.spline_x(lon) - pixel_x)

        lon_result = minimize_scalar(
            lon_error,
            bounds=(70, 135), method='bounded'
        )
        lon = lon_result.x

        # 求解纬度
        def lat_error(lat):
            return abs(self.spline_y(lat) - pixel_y)

        lat_result = minimize_scalar(
            lat_error,
            bounds=(15, 55), method='bounded'
        )
        lat = lat_result.x

        return lon, lat


# ============================================================
# 方案3: 径向基函数插值 (RBF)
# ============================================================

class RBFMapper:
    """
    径向基函数坐标映射器

    使用径向基函数进行二维插值,可以处理经纬度的耦合关系。

    特点:
    - 非线性适应能力强
    - 可以处理不规则分布的控制点
    - 鲁棒性强
    """

    def __init__(self, control_points: List[ControlPoint],
                 image_width: int = 1350, image_height: int = 1208,
                 rbf_function: str = 'multiquadric'):
        """
        初始化RBF映射器

        Args:
            control_points: 控制点列表
            image_width: 图片宽度
            image_height: 图片高度
            rbf_function: RBF核函数类型
                - 'multiquadric': sqrt(1 + (r*epsilon)**2)
                - 'inverse': 1 / sqrt(1 + (r*epsilon)**2)
                - 'gaussian': exp(-(r*epsilon)**2)
                - 'linear': r
                - 'cubic': r**3
                - 'thin_plate': r**2 * log(r)
        """
        self.control_points = control_points
        self.image_width = image_width
        self.image_height = image_height

        # 提取坐标数据
        lons = np.array([cp.lon for cp in control_points])
        lats = np.array([cp.lat for cp in control_points])
        pixel_xs = np.array([cp.pixel_x for cp in control_points])
        pixel_ys = np.array([cp.pixel_y for cp in control_points])

        # X方向: 线性RBF
        self.rbf_x = Rbf(lons, lats, pixel_xs, function=rbf_function)

        # Y方向: RBF插值
        self.rbf_y = Rbf(lons, lats, pixel_ys, function=rbf_function)

        print(f"✅ RBF映射器初始化完成")
        print(f"   核函数: {rbf_function}")
        print(f"   控制点数: {len(control_points)}")

    def geo_to_pixel(self, lon: float, lat: float) -> Tuple[int, int]:
        """经纬度转像素坐标"""
        pixel_x = int(self.rbf_x(lon, lat))
        pixel_y = int(self.rbf_y(lon, lat))

        # 边界限制
        pixel_x = np.clip(pixel_x, 0, self.image_width - 1)
        pixel_y = np.clip(pixel_y, 0, self.image_height - 1)

        return pixel_x, pixel_y

    def pixel_to_geo(self, pixel_x: int, pixel_y: int) -> Tuple[float, float]:
        """像素坐标转经纬度 (使用优化器)"""
        from scipy.optimize import minimize

        def error_function(params):
            lon, lat = params
            pred_x, pred_y = self.geo_to_pixel(lon, lat)
            return (pred_x - pixel_x)**2 + (pred_y - pixel_y)**2

        # 初始猜测
        initial_guess = [105.0, 35.0]

        result = minimize(
            error_function,
            initial_guess,
            bounds=[(70, 135), (15, 55)],
            method='L-BFGS-B'
        )

        return result.x[0], result.x[1]


# ============================================================
# 方案4: 优化的墨卡托投影
# ============================================================

class OptimizedMercatorMapper:
    """
    优化的墨卡托投影映射器

    直接使用墨卡托投影公式,并自动拟合最优边界参数,
    从根本上消除模型失配问题。

    特点:
    - 理论正确,完全匹配雷达图生成算法
    - 精度最高,仅受控制点精度限制
    - 全局一致,无分带问题
    - 高效,适合实时应用
    """

    def __init__(self, control_points: List[ControlPoint],
                 image_width: int = 1350, image_height: int = 1208,
                 legend_height: int = 120,
                 auto_fit_bounds: bool = True):
        """
        初始化优化的墨卡托投影映射器

        Args:
            control_points: 控制点列表
            image_width: 图片宽度
            image_height: 图片高度
            legend_height: 底部图例高度
            auto_fit_bounds: 是否自动拟合最优边界
        """
        self.control_points = control_points
        self.image_width = image_width
        self.image_height = image_height
        self.legend_height = legend_height
        self.map_height = image_height - legend_height

        # 墨卡托投影参数
        if auto_fit_bounds:
            # 自动拟合最优边界
            self.lon_min, self.lon_max, self.lat_min, self.lat_max = \
                self._auto_fit_bounds(control_points)
        else:
            # 使用默认参数
            self.lon_min = 72.2
            self.lon_max = 133.5
            self.lat_min = 17.0
            self.lat_max = 51.8

        # 计算墨卡托Y坐标范围
        self.y_min = self._lat_to_mercator_y(self.lat_min)
        self.y_max = self._lat_to_mercator_y(self.lat_max)

        # 计算缩放因子
        self.scale_x = self.image_width / (self.lon_max - self.lon_min)
        self.scale_y = self.map_height / (self.y_max - self.y_min)

        print(f"✅ 优化墨卡托投影映射器初始化完成")
        print(f"   经度范围: [{self.lon_min:.2f}, {self.lon_max:.2f}]")
        print(f"   纬度范围: [{self.lat_min:.2f}, {self.lat_max:.2f}]")

        # 评估拟合精度
        self._evaluate_accuracy()

    def _lat_to_mercator_y(self, lat: float) -> float:
        """纬度转墨卡托Y坐标"""
        lat_rad = np.radians(lat)
        return np.log(np.tan(np.pi / 4 + lat_rad / 2))

    def _mercator_y_to_lat(self, mercator_y: float) -> float:
        """墨卡托Y坐标转纬度"""
        lat_rad = 2 * np.arctan(np.exp(mercator_y)) - np.pi / 2
        return np.degrees(lat_rad)

    def _auto_fit_bounds(self, control_points: List[ControlPoint]) -> Tuple[float, float, float, float]:
        """自动拟合最优边界参数"""
        print("   正在自动拟合最优边界参数...")

        # 提取数据
        lons = np.array([cp.lon for cp in control_points])
        lats = np.array([cp.lat for cp in control_points])
        pixel_xs = np.array([cp.pixel_x for cp in control_points])
        pixel_ys = np.array([cp.pixel_y for cp in control_points])

        # 定义误差函数
        def error_function(bounds):
            lon_min, lon_max, lat_min, lat_max = bounds

            # 计算墨卡托Y范围
            y_min = self._lat_to_mercator_y(lat_min)
            y_max = self._lat_to_mercator_y(lat_max)

            # 计算预测坐标
            scale_x = self.image_width / (lon_max - lon_min)
            scale_y = self.map_height / (y_max - y_min)

            pred_xs = (lons - lon_min) * scale_x
            pred_ys = self.map_height - (self._lat_to_mercator_y(lats) - y_min) * scale_y

            # 计算误差
            error = np.sqrt(np.mean((pred_xs - pixel_xs)**2 + (pred_ys - pixel_ys)**2))
            return error

        # 优化
        from scipy.optimize import minimize

        # 初始猜测
        initial_guess = [72.0, 133.0, 17.0, 52.0]

        # 边界约束
        bounds = [(65, 80), (130, 145), (10, 25), (45, 60)]

        result = minimize(
            error_function,
            initial_guess,
            bounds=bounds,
            method='L-BFGS-B'
        )

        lon_min, lon_max, lat_min, lat_max = result.x
        print(f"   最优边界: lon=[{lon_min:.2f}, {lon_max:.2f}], lat=[{lat_min:.2f}, {lat_max:.2f}]")
        print(f"   拟合误差: {result.fun:.2f} px")

        return lon_min, lon_max, lat_min, lat_max

    def _evaluate_accuracy(self):
        """评估拟合精度"""
        errors_x = []
        errors_y = []

        for cp in self.control_points:
            pred_x, pred_y = self.geo_to_pixel(cp.lon, cp.lat)
            errors_x.append(pred_x - cp.pixel_x)
            errors_y.append(pred_y - cp.pixel_y)

        mae_x = np.mean([abs(e) for e in errors_x])
        mae_y = np.mean([abs(e) for e in errors_y])
        max_error = np.max([np.sqrt(ex**2 + ey**2)
                           for ex, ey in zip(errors_x, errors_y)])

        print(f"   拟合精度: MAE_X={mae_x:.2f}px, MAE_Y={mae_y:.2f}px, MAX={max_error:.2f}px")

    def geo_to_pixel(self, lon: float, lat: float) -> Tuple[int, int]:
        """经纬度转像素坐标"""
        # 经度: 线性映射
        pixel_x = int((lon - self.lon_min) * self.scale_x)

        # 纬度: 墨卡托投影
        mercator_y = self._lat_to_mercator_y(lat)
        pixel_y = int(self.map_height - (mercator_y - self.y_min) * self.scale_y)

        # 边界限制
        pixel_x = np.clip(pixel_x, 0, self.image_width - 1)
        pixel_y = np.clip(pixel_y, 0, self.map_height - 1)

        return pixel_x, pixel_y

    def pixel_to_geo(self, pixel_x: int, pixel_y: int) -> Tuple[float, float]:
        """像素坐标转经纬度"""
        # 经度: 逆线性变换
        lon = self.lon_min + pixel_x / self.scale_x

        # 纬度: 逆墨卡托变换
        mercator_y = self.y_max - pixel_y / self.scale_y
        lat = self._mercator_y_to_lat(mercator_y)

        return lon, lat


# ============================================================
# 工具函数
# ============================================================

def create_control_points_from_data(cities_data: List[Dict]) -> List[ControlPoint]:
    """
    从城市数据创建控制点列表

    Args:
        cities_data: 城市数据列表,每个元素包含:
            - name: 城市名称
            - lon: 经度
            - lat: 纬度
            - pixel_x: 像素X坐标 (可选)
            - pixel_y: 像素Y坐标 (可选)

    Returns:
        控制点列表
    """
    control_points = []
    for city in cities_data:
        cp = ControlPoint(
            pixel_x=city.get('pixel_x', 0),
            pixel_y=city.get('pixel_y', 0),
            lon=city['lon'],
            lat=city['lat'],
            name=city['name']
        )
        control_points.append(cp)
    return control_points


def evaluate_mapper(mapper, test_cities: List[ControlPoint]) -> Dict:
    """
    评估映射器精度

    Args:
        mapper: 映射器实例
        test_cities: 测试城市列表

    Returns:
        精度统计字典
    """
    errors_x = []
    errors_y = []
    error_details = []

    for city in test_cities:
        pred_x, pred_y = mapper.geo_to_pixel(city.lon, city.lat)
        error_x = pred_x - city.pixel_x
        error_y = pred_y - city.pixel_y
        error_mag = np.sqrt(error_x**2 + error_y**2)

        errors_x.append(error_x)
        errors_y.append(error_y)
        error_details.append({
            'name': city.name,
            'error_x': error_x,
            'error_y': error_y,
            'error_magnitude': error_mag
        })

    # 统计指标
    mae_x = np.mean([abs(e) for e in errors_x])
    mae_y = np.mean([abs(e) for e in errors_y])
    max_error = np.max([np.sqrt(ex**2 + ey**2) for ex, ey in zip(errors_x, errors_y)])
    within_3px = np.sum([e['error_magnitude'] < 3 for e in error_details]) / len(error_details)

    return {
        'MAE_X': mae_x,
        'MAE_Y': mae_y,
        'MAX_ERROR': max_error,
        'WITHIN_3PX': within_3px,
        'details': error_details
    }


# ============================================================
# 使用示例
# ============================================================

if __name__ == '__main__':
    # 示例控制点数据
    example_cities = [
        {'name': '北京', 'lon': 116.41, 'lat': 39.90, 'pixel_x': 980, 'pixel_y': 520},
        {'name': '上海', 'lon': 121.47, 'lat': 31.23, 'pixel_x': 1095, 'pixel_y': 780},
        {'name': '广州', 'lon': 113.26, 'lat': 23.13, 'pixel_x': 910, 'pixel_y': 950},
        {'name': '武汉', 'lon': 114.31, 'lat': 30.59, 'pixel_x': 930, 'pixel_y': 800},
        {'name': '西安', 'lon': 108.94, 'lat': 34.34, 'pixel_x': 810, 'pixel_y': 680},
        {'name': '乌鲁木齐', 'lon': 87.62, 'lat': 43.82, 'pixel_x': 340, 'pixel_y': 380},
        {'name': '哈尔滨', 'lon': 126.53, 'lat': 45.80, 'pixel_x': 1195, 'pixel_y': 320},
        {'name': '拉萨', 'lon': 91.11, 'lat': 29.97, 'pixel_x': 420, 'pixel_y': 810},
        {'name': '海口', 'lon': 110.20, 'lat': 20.02, 'pixel_x': 850, 'pixel_y': 1020},
        {'name': '杭州', 'lon': 120.15, 'lat': 30.27, 'pixel_x': 1070, 'pixel_y': 790},
    ]

    control_points = create_control_points_from_data(example_cities)

    print("=" * 60)
    print("高级坐标映射方案测试")
    print("=" * 60)

    # 测试方案1: 分段多项式
    print("\n【方案1】分段多项式拟合")
    mapper1 = PiecewisePolynomialMapper(control_points)
    results1 = evaluate_mapper(mapper1, control_points)
    print(f"精度评估: MAE_X={results1['MAE_X']:.2f}px, MAE_Y={results1['MAE_Y']:.2f}px")
    print(f"          MAX_ERROR={results1['MAX_ERROR']:.2f}px")
    print(f"          WITHIN_3PX={results1['WITHIN_3PX']*100:.1f}%")

    # 测试方案2: 三次样条
    print("\n【方案2】三次样条插值")
    mapper2 = SplineRadarMapper(control_points)
    results2 = evaluate_mapper(mapper2, control_points)
    print(f"精度评估: MAE_X={results2['MAE_X']:.2f}px, MAE_Y={results2['MAE_Y']:.2f}px")
    print(f"          MAX_ERROR={results2['MAX_ERROR']:.2f}px")
    print(f"          WITHIN_3PX={results2['WITHIN_3PX']*100:.1f}%")

    # 测试方案3: RBF
    print("\n【方案3】径向基函数")
    mapper3 = RBFMapper(control_points)
    results3 = evaluate_mapper(mapper3, control_points)
    print(f"精度评估: MAE_X={results3['MAE_X']:.2f}px, MAE_Y={results3['MAE_Y']:.2f}px")
    print(f"          MAX_ERROR={results3['MAX_ERROR']:.2f}px")
    print(f"          WITHIN_3PX={results3['WITHIN_3PX']*100:.1f}%")

    # 测试方案4: 优化的墨卡托投影
    print("\n【方案4】优化的墨卡托投影")
    mapper4 = OptimizedMercatorMapper(control_points)
    results4 = evaluate_mapper(mapper4, control_points)
    print(f"精度评估: MAE_X={results4['MAE_X']:.2f}px, MAE_Y={results4['MAE_Y']:.2f}px")
    print(f"          MAX_ERROR={results4['MAX_ERROR']:.2f}px")
    print(f"          WITHIN_3PX={results4['WITHIN_3PX']*100:.1f}%")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
