"""
气象雷达色标解析模块

将雷达图片的RGB值转换为dBZ反射率值
"""

import numpy as np
from PIL import Image
from typing import Dict, Tuple, List, Optional
import re


class ColorScaleParser:
    """
    雷达色标解析器

    支持中国气象局标准雷达色标方案
    """

    # 中国气象局组合反射率标准色标
    STANDARD_COLOR_SCALE = {
        'no_echo': {
            'rgb': (0, 0, 0),           # 黑色 - 无回波
            'dbz_range': (0, 5),
            'description': '无回波'
        },
        'very_weak': {
            'rgb': (0, 128, 0),         # 深绿色 - 极弱回波
            'dbz_range': (5, 10),
            'description': '极弱回波'
        },
        'weak': {
            'rgb': (0, 255, 0),         # 绿色 - 弱回波
            'dbz_range': (10, 15),
            'description': '弱回波'
        },
        'moderate_low': {
            'rgb': (128, 255, 0),       # 黄绿色 - 中低回波
            'dbz_range': (15, 20),
            'description': '中低回波'
        },
        'moderate': {
            'rgb': (255, 255, 0),       # 黄色 - 中等回波
            'dbz_range': (20, 25),
            'description': '中等回波'
        },
        'moderate_high': {
            'rgb': (255, 200, 0),       # 深黄色 - 中高回波
            'dbz_range': (25, 30),
            'description': '中高回波'
        },
        'strong': {
            'rgb': (255, 128, 0),       # 橙色 - 强回波
            'dbz_range': (30, 35),
            'description': '强回波'
        },
        'very_strong': {
            'rgb': (255, 0, 0),         # 红色 - 很强回波
            'dbz_range': (35, 40),
            'description': '很强回波'
        },
        'severe': {
            'rgb': (200, 0, 0),         # 深红色 - 严重回波
            'dbz_range': (40, 45),
            'description': '严重回波'
        },
        'extreme': {
            'rgb': (128, 0, 128),       # 紫色 - 极端回波
            'dbz_range': (45, 50),
            'description': '极端回波'
        },
        'intense': {
            'rgb': (255, 0, 255),       # 紫红色 - 剧烈回波
            'dbz_range': (50, 55),
            'description': '剧烈回波'
        },
        'maximum': {
            'rgb': (255, 255, 255),     # 白色 - 最大回波
            'dbz_range': (55, 75),
            'description': '最大回波'
        }
    }

    def __init__(self, custom_color_scale: Optional[Dict] = None):
        """
        初始化色标解析器

        Args:
            custom_color_scale: 自定义色标，如不提供则使用标准色标
        """
        self.color_scale = custom_color_scale or self.STANDARD_COLOR_SCALE
        self._build_color_lookup_table()

    def _build_color_lookup_table(self):
        """构建颜色查找表，加速RGB到dBZ的转换"""
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
            rgb: RGB元组 (R, G, B)

        Returns:
            dBZ值
        """
        # 方法1: 最近邻颜色匹配
        dbz_value = self._nearest_color_match(rgb)

        # 方法2: 如果需要更精确，可以使用加权插值
        # dbz_value = self._interpolate_dbz(rgb)

        return dbz_value

    def _nearest_color_match(self, rgb: Tuple[int, int, int]) -> float:
        """
        最近邻颜色匹配

        Args:
            rgb: RGB元组

        Returns:
            匹配的dBZ值
        """
        rgb_array = np.array(rgb)

        # 计算与每个标准颜色的欧氏距离
        distances = np.linalg.norm(self.color_array - rgb_array, axis=1)

        # 找到最近的颜色索引
        nearest_idx = np.argmin(distances)

        # 返回对应的dBZ范围的中值
        dbz_range = self.dbz_ranges[nearest_idx]
        return sum(dbz_range) / 2

    def _interpolate_dbz(self, rgb: Tuple[int, int, int]) -> float:
        """
        基于颜色插值计算dBZ值（更精确但更慢）

        Args:
            rgb: RGB元组

        Returns:
            插值后的dBZ值
        """
        rgb_array = np.array(rgb)

        # 计算与所有颜色的距离
        distances = np.linalg.norm(self.color_array - rgb_array, axis=1)

        # 找到最近的几个颜色（例如3个）
        k = 3
        nearest_indices = np.argpartition(distances, k)[:k]

        # 基于距离的加权平均
        weights = 1.0 / (distances[nearest_indices] + 1e-6)
        weights = weights / weights.sum()

        # 计算加权平均的dBZ值
        dbz_values = []
        for idx in nearest_indices:
            dbz_range = self.dbz_ranges[idx]
            dbz_values.append(sum(dbz_range) / 2)

        dbz_value = np.average(dbz_values, weights=weights)

        return dbz_value

    def dbz_to_category(self, dbz: float) -> str:
        """
        将dBZ值转换为强度等级分类

        Args:
            dbz: dBZ值

        Returns:
            强度等级字符串
        """
        if dbz < 15:
            return 'weak'  # 弱回波
        elif dbz < 35:
            return 'moderate'  # 中等回波
        elif dbz < 45:
            return 'strong'  # 强回波
        elif dbz < 55:
            return 'severe'  # 严重回波
        else:
            return 'extreme'  # 极端回波

    def get_cloud_impact_factor(self, dbz: float) -> float:
        """
        计算云影响因子（用于光伏预测）

        根据dBZ值计算云层对辐照度的影响因子

        Args:
            dbz: dBZ值

        Returns:
            影响因子 (0.0-1.0, 1.0表示无影响)
        """
        if dbz < 10:
            return 1.0  # 晴空或薄云，基本无影响
        elif dbz < 25:
            # 中等云层，线性下降
            return 1.0 - (dbz - 10) / 15 * 0.6  # 下降到0.4
        elif dbz < 35:
            # 厚云，继续下降
            return 0.4 - (dbz - 25) / 10 * 0.3  # 下降到0.1
        else:
            return 0.0  # 强对流云，完全遮挡


class LegendParser:
    """
    图例解析器

    从雷达图片中自动提取色标图例
    """

    def __init__(self, legend_image_path: str):
        """
        初始化图例解析器

        Args:
            legend_image_path: 色标图例图片路径
        """
        self.legend_image = Image.open(legend_image_path)
        self.pixels = np.array(self.legend_image)

    def extract_color_scale(self) -> Dict:
        """
        从图例图片中提取色标

        Returns:
            色标字典
        """
        # 假设图例是垂直排列的
        height, width = self.pixels.shape[:3]

        # 提取中间列的像素作为色标
        center_col = width // 2
        color_column = self.pixels[:, center_col, :]

        # 去除重复颜色
        unique_colors = np.unique(color_column, axis=0)

        # 这里需要实际的dBZ标注来建立映射
        # 简化版本：返回找到的颜色
        color_scale = {}

        for i, color in enumerate(unique_colors):
            dbz_min = i * 5  # 假设每5 dBZ一个等级
            dbz_max = (i + 1) * 5
            color_scale[f'level_{i}'] = {
                'rgb': tuple(color),
                'dbz_range': (dbz_min, dbz_max),
                'description': f'Level {i}'
            }

        return color_scale


def analyze_radar_image_colors(image_path: str, num_samples: int = 1000) -> Dict:
    """
    分析雷达图片中的颜色分布

    Args:
        image_path: 图片路径
        num_samples: 采样点数量

    Returns:
        颜色统计信息
    """
    image = Image.open(image_path)
    pixels = np.array(image)

    # 随机采样
    height, width = pixels.shape[:3]
    sample_indices = np.random.choice(height * width, num_samples, replace=False)

    sample_colors = pixels.reshape(-1, 3)[sample_indices]

    # 统计颜色分布
    unique_colors, counts = np.unique(sample_colors, axis=0, return_counts=True)

    # 按频率排序
    sorted_indices = np.argsort(-counts)
    top_colors = unique_colors[sorted_indices[:10]]
    top_counts = counts[sorted_indices[:10]]

    return {
        'total_pixels': height * width,
        'unique_colors': len(unique_colors),
        'top_colors': [tuple(c) for c in top_colors],
        'top_counts': top_counts.tolist()
    }


if __name__ == '__main__':
    # 示例用法
    print("雷达色标解析模块")

    # 创建色标解析器
    parser = ColorScaleParser()

    # 测试RGB转dBZ
    test_colors = [
        (0, 0, 0),      # 黑色 - 无回波
        (0, 255, 0),    # 绿色 - 弱回波
        (255, 255, 0),  # 黄色 - 中等回波
        (255, 0, 0),    # 红色 - 强回波
        (128, 0, 128),  # 紫色 - 极端回波
    ]

    for color in test_colors:
        dbz = parser.rgb_to_dbz(color)
        category = parser.dbz_to_category(dbz)
        impact = parser.get_cloud_impact_factor(dbz)
        print(f"RGB {color} -> dBZ: {dbz:.1f}, 类别: {category}, 影响因子: {impact:.2f}")
