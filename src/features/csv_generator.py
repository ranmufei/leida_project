"""
CSV数据生成模块

将提取的雷达数据转换为标准化的CSV格式，支持时间重采样和特征增强
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import warnings


class CSVGenerator:
    """
    CSV生成器

    将雷达数据转换为标准CSV格式，支持时间重采样和特征增强
    """

    def __init__(self, target_interval: str = '15T'):
        """
        初始化CSV生成器

        Args:
            target_interval: 目标时间间隔 (Pandas时间偏移字符串)
                '6T' = 6分钟 (原始数据)
                '15T' = 15分钟 (默认，适合光伏预测)
                '30T' = 30分钟
                '1H' = 1小时
        """
        self.target_interval = target_interval

    def generate_csv(self,
                    df: pd.DataFrame,
                    output_path: str,
                    add_temporal_features: bool = True,
                    aggregation_method: str = 'mean') -> pd.DataFrame:
        """
        生成CSV文件

        Args:
            df: 输入数据DataFrame
            output_path: 输出文件路径
            add_temporal_features: 是否添加时序特征
            aggregation_method: 聚合方法 ('mean', 'max', 'min', 'median')

        Returns:
            处理后的DataFrame
        """
        # 数据预处理
        df_processed = self._preprocess_data(df)

        # 时间重采样
        if self.target_interval != '0T':
            df_resampled = self._resample_data(df_processed, aggregation_method)
        else:
            df_resampled = df_processed

        # 添加时序特征
        if add_temporal_features:
            df_resampled = self._add_temporal_features(df_resampled)

        # 数据质量检查
        df_resampled = self._quality_check(df_resampled)

        # 保存CSV
        self._save_csv(df_resampled, output_path)

        return df_resampled

    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        数据预处理

        Args:
            df: 原始数据

        Returns:
            预处理后的数据
        """
        # 创建副本避免修改原始数据
        df_processed = df.copy()

        # 确保时间戳是datetime类型
        if 'timestamp' in df_processed.columns:
            df_processed['timestamp'] = pd.to_datetime(df_processed['timestamp'])

        # 确保有位置标识
        if 'location_name' not in df_processed.columns and 'longitude' in df_processed.columns:
            df_processed['location_name'] = df_processed.apply(
                lambda row: f"{row['longitude']:.2f}_{row['latitude']:.2f}",
                axis=1
            )

        # 设置多级索引
        index_cols = ['location_name']
        if 'timestamp' in df_processed.columns:
            index_cols.append('timestamp')

        # 处理重复数据
        if len(df_processed) > 0:
            df_processed = df_processed.drop_duplicates(
                subset=index_cols,
                keep='first'
            )

        return df_processed

    def _resample_data(self,
                      df: pd.DataFrame,
                      aggregation_method: str = 'mean') -> pd.DataFrame:
        """
        时间重采样

        将6分钟间隔的数据重采样到目标间隔(如15分钟)

        Args:
            df: 输入数据
            aggregation_method: 聚合方法

        Returns:
            重采样后的数据
        """
        if df.empty:
            return df

        # 确保有时间戳列
        if 'timestamp' not in df.columns:
            warnings.warn("数据中没有timestamp列，跳过重采样")
            return df

        # 设置时间戳为索引
        df_resampled = df.set_index('timestamp')

        # 按位置分组并重采样
        if 'location_name' in df.columns:
            # 分组重采样
            grouped = df_resampled.groupby('location_name')

            resampled_groups = []
            for name, group in grouped:
                # 数值列使用指定方法聚合
                numeric_cols = group.select_dtypes(include=[np.number]).columns

                # 对数值列进行聚合
                resampled = group[numeric_cols].resample(self.target_interval)

                if aggregation_method == 'mean':
                    resampled = resampled.mean()
                elif aggregation_method == 'max':
                    resampled = resampled.max()
                elif aggregation_method == 'min':
                    resampled = resampled.min()
                elif aggregation_method == 'median':
                    resampled = resampled.median()
                else:
                    resampled = resampled.mean()

                # 恢复location_name
                resampled['location_name'] = name
                resampled_groups.append(resampled)

            # 合并所有组
            df_final = pd.concat(resampled_groups)
            df_final = df_final.reset_index()
        else:
            # 不分组，直接重采样
            numeric_cols = df_resampled.select_dtypes(include=[np.number]).columns
            df_final = df_resampled[numeric_cols].resample(self.target_interval).mean()
            df_final = df_final.reset_index()

        return df_final

    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        添加时序特征

        计算dBZ值的时间趋势、变化率等特征

        Args:
            df: 输入数据

        Returns:
            添加了时序特征的数据
        """
        if df.empty or 'timestamp' not in df.columns:
            return df

        df_enhanced = df.copy()

        # 按位置分组
        if 'location_name' in df.columns:
            grouped = df_enhanced.groupby('location_name')

            # 计算时序特征
            for name, group in grouped:
                if 'dbz_value' in group.columns and len(group) > 1:
                    # 排序确保时间顺序
                    group = group.sort_values('timestamp')

                    # 计算时间间隔(分钟)
                    group['time_diff'] = group['timestamp'].diff().dt.total_seconds() / 60

                    # 计算dBZ变化
                    group['dbz_diff'] = group['dbz_value'].diff()

                    # 计算变化率 (dBZ/小时)
                    group['dbz_change_rate'] = group['dbz_diff'] / group['time_diff'] * 60

                    # 计算移动平均
                    group['dbz_ma_2'] = group['dbz_value'].rolling(window=2, min_periods=1).mean()
                    group['dbz_ma_3'] = group['dbz_value'].rolling(window=3, min_periods=1).mean()

                    # 计算趋势 (线性回归斜率的简化版本)
                    group['dbz_trend'] = group['dbz_value'].diff().rolling(window=3).mean()

                    # 计算过去N时间步的最大值
                    group['dbz_max_past_3'] = group['dbz_value'].rolling(window=3, min_periods=1).max()
                    group['dbz_max_past_6'] = group['dbz_value'].rolling(window=6, min_periods=1).max()

                    # 更新DataFrame
                    mask = df_enhanced['location_name'] == name
                    for col in ['time_diff', 'dbz_diff', 'dbz_change_rate',
                               'dbz_ma_2', 'dbz_ma_3', 'dbz_trend',
                               'dbz_max_past_3', 'dbz_max_past_6']:
                        if col in group.columns:
                            df_enhanced.loc[mask, col] = group[col].values

        return df_enhanced

    def _quality_check(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        数据质量检查

        检测和处理异常值、缺失值

        Args:
            df: 输入数据

        Returns:
            质量检查后的数据
        """
        if df.empty:
            return df

        df_qc = df.copy()

        # 标记异常值
        if 'dbz_value' in df_qc.columns:
            # dBZ值通常在 -30 到 75 之间
            df_qc['dbz_outlier'] = (
                (df_qc['dbz_value'] < -30) | (df_qc['dbz_value'] > 75)
            )

            # 将异常值设为NaN
            df_qc.loc[df_qc['dbz_outlier'], 'dbz_value'] = np.nan

        # 处理缺失值
        if 'dbz_value' in df_qc.columns:
            # 线性插值填充缺失值
            if 'location_name' in df_qc.columns:
                # 按位置分组插值
                for name in df_qc['location_name'].unique():
                    mask = df_qc['location_name'] == name
                    df_qc.loc[mask, 'dbz_value'] = df_qc.loc[mask, 'dbz_value'].interpolate(
                        method='linear', limit_direction='both'
                    )

        # 添加数据质量标志
        if 'data_quality' not in df_qc.columns:
            df_qc['data_quality'] = 'good'
        else:
            df_qc.loc[df_qc.get('dbz_outlier', False), 'data_quality'] = 'outlier'

        return df_qc

    def _save_csv(self, df: pd.DataFrame, output_path: str):
        """
        保存CSV文件

        Args:
            df: 要保存的数据
            output_path: 输出文件路径
        """
        # 选择重要的列
        priority_cols = [
            'timestamp', 'location_name', 'longitude', 'latitude',
            'dbz_value', 'dbz_category', 'cloud_impact_factor',
            'dbz_change_rate', 'dbz_trend', 'dbz_max_past_3', 'data_quality'
        ]

        # 筛选存在的列
        output_cols = [col for col in priority_cols if col in df.columns]

        # 添加其他数值列
        other_cols = [col for col in df.columns
                     if col not in output_cols and col not in ['rgb_values', 'dbz_outlier']]
        output_cols.extend(other_cols)

        # 保存
        df_output = df[output_cols]
        df_output.to_csv(output_path, index=False, encoding='utf-8-sig')

        print(f"CSV文件已保存到: {output_path}")
        print(f"共 {len(df_output)} 条记录，{len(output_cols)} 个字段")


def create_summary_statistics(df: pd.DataFrame, output_path: Optional[str] = None) -> Dict:
    """
    创建数据摘要统计

    Args:
        df: 输入数据
        output_path: 输出文件路径(可选)

    Returns:
        统计信息字典
    """
    if df.empty:
        return {}

    stats = {
        'total_records': len(df),
        'date_range': {
            'start': str(df['timestamp'].min()) if 'timestamp' in df.columns else None,
            'end': str(df['timestamp'].max()) if 'timestamp' in df.columns else None
        },
        'locations': df['location_name'].nunique() if 'location_name' in df.columns else 0,
        'dbz_statistics': {}
    }

    # dBZ统计
    if 'dbz_value' in df.columns:
        dbz_data = df['dbz_value'].dropna()
        if len(dbz_data) > 0:
            stats['dbz_statistics'] = {
                'mean': float(dbz_data.mean()),
                'std': float(dbz_data.std()),
                'min': float(dbz_data.min()),
                'max': float(dbz_data.max()),
                'median': float(dbz_data.median())
            }

    # 类别分布
    if 'dbz_category' in df.columns:
        stats['category_distribution'] = df['dbz_category'].value_counts().to_dict()

    # 数据质量
    if 'data_quality' in df.columns:
        stats['data_quality'] = df['data_quality'].value_counts().to_dict()

    # 保存到文件
    if output_path:
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

    return stats


if __name__ == '__main__':
    # 示例用法
    print("CSV生成模块")

    # 创建示例数据
    dates = pd.date_range('2024-03-10 00:00:00', periods=24, freq='6T')
    data = {
        'timestamp': dates,
        'location_name': ['北京'] * 24,
        'longitude': [116.4074] * 24,
        'latitude': [39.9042] * 24,
        'dbz_value': np.random.uniform(5, 50, 24),
        'dbz_category': np.random.choice(['weak', 'moderate', 'strong'], 24)
    }

    df = pd.DataFrame(data)

    # 创建CSV生成器
    generator = CSVGenerator(target_interval='15T')

    # 生成CSV
    df_output = generator.generate_csv(
        df,
        output_path='./output_test.csv',
        add_temporal_features=True
    )

    print(f"\n输入数据: {len(df)} 条")
    print(f"输出数据: {len(df_output)} 条")
    print(f"压缩比: {len(df_output) / len(df):.1%}")

    # 生成统计摘要
    stats = create_summary_statistics(df_output)
    print(f"\n统计信息: {stats}")
