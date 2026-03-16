"""
气象雷达数据特征提取模块

从雷达图片中提取多维度的气象特征
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import os
import glob
import warnings

from ..preprocessing.mapper import ChinaRadarMapper, create_mapper_from_image
from ..preprocessing.color_scale import ColorScaleParser


class RadarFeatureExtractor:
    """
    雷达特征提取器

    从雷达图片中提取指定位置的多维度特征
    """

    def __init__(self, color_parser: Optional[ColorScaleParser] = None):
        """
        初始化特征提取器

        Args:
            color_parser: 色标解析器，如不提供则创建默认实例
        """
        self.color_parser = color_parser or ColorScaleParser()

    def extract_point_features(self,
                             image_path: str,
                             lon: float,
                             lat: float,
                             timestamp: Optional[datetime] = None) -> Dict:
        """
        提取指定经纬度点的特征

        Args:
            image_path: 雷达图片路径
            lon: 经度
            lat: 纬度
            timestamp: 时间戳

        Returns:
            特征字典
        """
        try:
            # 创建映射器
            mapper = ChinaRadarMapper(image_path)

            # 检查坐标是否有效
            if not mapper.is_valid_coordinate(lon, lat):
                warnings.warn(f"坐标 ({lon}, {lat}) 不在图片范围内")
                return self._get_invalid_features(lon, lat, timestamp)

            # 获取像素值
            rgb = mapper.get_pixel_value(lon, lat)

            # 转换为dBZ值
            dbz_value = self.color_parser.rgb_to_dbz(rgb)
            dbz_category = self.color_parser.dbz_to_category(dbz_value)
            cloud_impact = self.color_parser.get_cloud_impact_factor(dbz_value)

            # 构建特征字典
            features = {
                'timestamp': timestamp,
                'longitude': lon,
                'latitude': lat,
                'dbz_value': dbz_value,
                'dbz_category': dbz_category,
                'cloud_impact_factor': cloud_impact,
                'rgb_values': rgb,
                'data_quality': 'valid'
            }

            return features

        except Exception as e:
            warnings.warn(f"提取特征时出错: {e}")
            return self._get_invalid_features(lon, lat, timestamp, error=str(e))

    def _get_invalid_features(self, lon: float, lat: float,
                             timestamp: Optional[datetime],
                             error: Optional[str] = None) -> Dict:
        """返回无效特征字典"""
        return {
            'timestamp': timestamp,
            'longitude': lon,
            'latitude': lat,
            'dbz_value': np.nan,
            'dbz_category': 'no_data',
            'cloud_impact_factor': 1.0,  # 无数据时假设无影响
            'rgb_values': (0, 0, 0),
            'data_quality': f'invalid_{error}' if error else 'out_of_range'
        }

    def extract_neighborhood_features(self,
                                     image_path: str,
                                     lon: float,
                                     lat: float,
                                     radius_km: float = 20,
                                     timestamp: Optional[datetime] = None) -> Dict:
        """
        提取邻域统计特征

        Args:
            image_path: 雷达图片路径
            lon: 中心经度
            lat: 中心纬度
            radius_km: 半径(公里)
            timestamp: 时间戳

        Returns:
            邻域特征字典
        """
        try:
            mapper = ChinaRadarMapper(image_path)

            if not mapper.is_valid_coordinate(lon, lat):
                return self._get_invalid_neighborhood_features(lon, lat, timestamp)

            # 获取邻域像素
            neighborhood = mapper.get_neighborhood_pixels(lon, lat, radius_km)

            # 提取统计特征
            neighborhood_features = self._calculate_neighborhood_statistics(
                neighborhood, lon, lat, timestamp
            )

            return neighborhood_features

        except Exception as e:
            warnings.warn(f"提取邻域特征时出错: {e}")
            return self._get_invalid_neighborhood_features(lon, lat, timestamp, error=str(e))

    def _calculate_neighborhood_statistics(self,
                                         neighborhood: np.ndarray,
                                         lon: float,
                                         lat: float,
                                         timestamp: Optional[datetime]) -> Dict:
        """计算邻域统计特征"""
        # 将邻域像素转换为dBZ值
        dbz_values = []
        for row in neighborhood:
            for pixel in row:
                if len(pixel) >= 3:  # 确保是RGB像素
                    dbz = self.color_parser.rgb_to_dbz(tuple(pixel[:3]))
                    dbz_values.append(dbz)

        if not dbz_values:
            return self._get_invalid_neighborhood_features(lon, lat, timestamp)

        dbz_array = np.array(dbz_values)

        # 计算统计量
        features = {
            'timestamp': timestamp,
            'longitude': lon,
            'latitude': lat,
            'dbz_max': float(np.max(dbz_array)),
            'dbz_min': float(np.min(dbz_array)),
            'dbz_mean': float(np.mean(dbz_array)),
            'dbz_std': float(np.std(dbz_array)),
            'dbz_median': float(np.median(dbz_array)),
            'dbz_75th_percentile': float(np.percentile(dbz_array, 75)),
            'dbz_25th_percentile': float(np.percentile(dbz_array, 25)),
            'high_dbz_pixel_count': int(np.sum(dbz_array > 35)),  # 强回波像素数
            'data_quality': 'valid'
        }

        return features

    def _get_invalid_neighborhood_features(self, lon: float, lat: float,
                                          timestamp: Optional[datetime],
                                          error: Optional[str] = None) -> Dict:
        """返回无效邻域特征字典"""
        return {
            'timestamp': timestamp,
            'longitude': lon,
            'latitude': lat,
            'dbz_max': np.nan,
            'dbz_min': np.nan,
            'dbz_mean': np.nan,
            'dbz_std': np.nan,
            'dbz_median': np.nan,
            'dbz_75th_percentile': np.nan,
            'dbz_25th_percentile': np.nan,
            'high_dbz_pixel_count': 0,
            'data_quality': f'invalid_{error}' if error else 'out_of_range'
        }


class RadarDataExtractor:
    """
    雷达数据批量提取器

    批量处理雷达图片，提取时间序列特征
    """

    def __init__(self,
                 target_locations: List[Dict],
                 feature_extractor: Optional[RadarFeatureExtractor] = None):
        """
        初始化数据提取器

        Args:
            target_locations: 目标位置列表
                [{'name': '北京', 'lon': 116.4074, 'lat': 39.9042}, ...]
            feature_extractor: 特征提取器实例
        """
        self.locations = target_locations
        self.feature_extractor = feature_extractor or RadarFeatureExtractor()

    def extract_time_series(self,
                           start_time: datetime,
                           end_time: datetime,
                           image_dir: str,
                           image_pattern: str = '*.png',
                           extract_neighborhood: bool = False,
                           neighborhood_radius: float = 20) -> pd.DataFrame:
        """
        提取时间序列数据

        Args:
            start_time: 开始时间
            end_time: 结束时间
            image_dir: 雷达图片目录
            image_pattern: 图片文件名模式
            extract_neighborhood: 是否提取邻域特征
            neighborhood_radius: 邻域半径(公里)

        Returns:
            包含时间序列数据的DataFrame
        """
        # 获取图片文件列表
        image_files = self._get_image_files(image_dir, image_pattern)

        # 过滤时间范围内的图片
        image_files = self._filter_images_by_time(image_files, start_time, end_time)

        # 提取特征
        all_data = []

        for image_path in image_files:
            try:
                # 从文件名解析时间戳
                timestamp = self._parse_timestamp_from_filename(image_path)

                # 提取每个位置的特征
                for location in self.locations:
                    # 提取点特征
                    point_features = self.feature_extractor.extract_point_features(
                        image_path, location['lon'], location['lat'], timestamp
                    )
                    point_features['location_name'] = location['name']
                    all_data.append(point_features)

                    # 提取邻域特征
                    if extract_neighborhood:
                        neighborhood_features = self.feature_extractor.extract_neighborhood_features(
                            image_path, location['lon'], location['lat'],
                            neighborhood_radius, timestamp
                        )
                        # 重命名邻域特征以避免冲突
                        neighborhood_features = {
                            f'neighborhood_{k}': v for k, v in neighborhood_features.items()
                            if k not in ['timestamp', 'longitude', 'latitude']
                        }
                        neighborhood_features['location_name'] = location['name']
                        neighborhood_features['timestamp'] = timestamp
                        all_data.append(neighborhood_features)

            except Exception as e:
                warnings.warn(f"处理图片 {image_path} 时出错: {e}")

        # 创建DataFrame
        df = pd.DataFrame(all_data)

        if not df.empty:
            # 转换时间戳
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # 按位置和时间排序
            df = df.sort_values(['location_name', 'timestamp'])

            # 重置索引
            df = df.reset_index(drop=True)

        return df

    def _get_image_files(self, image_dir: str, pattern: str) -> List[str]:
        """获取图片文件列表"""
        search_pattern = os.path.join(image_dir, pattern)
        return glob.glob(search_pattern)

    def _filter_images_by_time(self,
                              image_files: List[str],
                              start_time: datetime,
                              end_time: datetime) -> List[str]:
        """根据时间范围过滤图片"""
        filtered_files = []

        for filepath in image_files:
            try:
                timestamp = self._parse_timestamp_from_filename(filepath)
                if start_time <= timestamp <= end_time:
                    filtered_files.append(filepath)
            except Exception:
                # 如果无法解析时间，保留文件
                filtered_files.append(filepath)

        return filtered_files

    def _parse_timestamp_from_filename(self, filepath: str) -> datetime:
        """
        从文件名解析时间戳

        支持多种文件名格式:
        - 20240310_160000.png
        - Z_RADA_C_BABJ_20240310160000_P_DOR_ACHN_CREF_20240310_160000.png
        """
        filename = os.path.basename(filepath)
        name_without_ext = os.path.splitext(filename)[0]

        # 尝试多种时间格式
        time_patterns = [
            r'(\d{8})_(\d{6})',  # 20240310_160000
            r'_(\d{14})_',       # _20240310160000_
            r'(\d{14})',         # 20240310160000
            r'(\d{8})',          # 20240310 (只有日期)
        ]

        for pattern in time_patterns:
            match = re.search(pattern, name_without_ext)
            if match:
                time_str = match.group(1)
                if len(time_str) == 14:
                    return datetime.strptime(time_str, '%Y%m%d%H%M%S')
                elif len(time_str) == 12:
                    return datetime.strptime(time_str, '%Y%m%d%H%M')
                elif len(time_str) == 8:
                    return datetime.strptime(time_str, '%Y%m%d')

        # 如果无法解析，返回文件修改时间
        return datetime.fromtimestamp(os.path.getmtime(filepath))


# 导入re模块
import re


if __name__ == '__main__':
    # 示例用法
    print("雷达特征提取模块")

    # 定义目标位置
    locations = [
        {'name': '北京', 'lon': 116.4074, 'lat': 39.9042},
        {'name': '上海', 'lon': 121.4737, 'lat': 31.2304}
    ]

    # 创建提取器
    extractor = RadarDataExtractor(locations)

    # 提取特征
    # start_time = datetime(2024, 3, 10, 0, 0)
    # end_time = datetime(2024, 3, 10, 23, 59)
    # df = extractor.extract_time_series(start_time, end_time, './data/raw')

    # print(f"提取了 {len(df)} 条记录")
    # print(df.head())
