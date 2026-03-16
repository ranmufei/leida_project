"""
高级使用示例

演示高级功能，包括批量下载、并行处理、自定义配置等
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from src import (
    RadarDataExtractor,
    CSVGenerator,
    ColorScaleParser,
    ChinaRadarMapper,
    download_radar_images,
    setup_logger,
    Timer
)


def example_batch_download():
    """批量下载雷达图片"""
    print("=" * 60)
    print("高级示例1: 批量下载雷达图片")
    print("=" * 60)

    # 设置日志
    logger = setup_logger('batch_download', 'logs/download.log')

    # 定义时间范围
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)

    print(f"\n下载时间范围:")
    print(f"  开始: {start_time}")
    print(f"  结束: {end_time}")
    print(f"  间隔: 6分钟")
    print(f"  预计文件数: {(end_time - start_time).seconds // 360 + 1}")

    # 下载文件
    output_dir = './data/raw'
    downloaded_files = download_radar_images(
        start_time=start_time,
        end_time=end_time,
        output_dir=output_dir,
        logger=logger
    )

    print(f"\n下载完成: {len(downloaded_files)} 个文件")


def example_custom_color_scale():
    """自定义色标方案"""
    print("\n" + "=" * 60)
    print("高级示例2: 自定义色标方案")
    print("=" * 60)

    # 定义自定义色标
    custom_color_scale = {
        'level_1': {
            'rgb': (0, 0, 0),
            'dbz_range': (0, 10),
            'description': '无回波'
        },
        'level_2': {
            'rgb': (0, 255, 0),
            'dbz_range': (10, 20),
            'description': '弱回波'
        },
        'level_3': {
            'rgb': (255, 255, 0),
            'dbz_range': (20, 30),
            'description': '中等回波'
        },
        'level_4': {
            'rgb': (255, 128, 0),
            'dbz_range': (30, 40),
            'description': '强回波'
        },
        'level_5': {
            'rgb': (255, 0, 0),
            'dbz_range': (40, 50),
            'description': '严重回波'
        },
        'level_6': {
            'rgb': (128, 0, 128),
            'dbz_range': (50, 75),
            'description': '极端回波'
        }
    }

    # 创建自定义色标解析器
    color_parser = ColorScaleParser(custom_color_scale=custom_color_scale)

    # 测试色标转换
    test_colors = [
        (0, 0, 0),      # 无回波
        (0, 255, 0),    # 弱回波
        (255, 255, 0),  # 中等回波
        (255, 0, 0),    # 严重回波
        (128, 0, 128),  # 极端回波
    ]

    print("\n自定义色标测试:")
    for color in test_colors:
        dbz = color_parser.rgb_to_dbz(color)
        category = color_parser.dbz_to_category(dbz)
        impact = color_parser.get_cloud_impact_factor(dbz)
        print(f"  RGB {color} -> dBZ: {dbz:.1f}, 类别: {category}, 影响: {impact:.2f}")


def example_coordinate_mapping():
    """坐标映射演示"""
    print("\n" + "=" * 60)
    print("高级示例3: 坐标映射")
    print("=" * 60)

    # 假设有一个雷达图片
    image_path = './data/raw/sample_radar.png'

    # 如果文件不存在，创建演示
    if not os.path.exists(image_path):
        print(f"\n注意: 示例图片 {image_path} 不存在")
        print("创建映射器需要真实的雷达图片文件")
        return

    # 创建映射器
    mapper = ChinaRadarMapper(image_path)

    # 获取覆盖信息
    info = mapper.get_coverage_info()
    print("\n图片覆盖范围:")
    print(f"  经度: {info['lon_min']:.2f}° ~ {info['lon_max']:.2f}°")
    print(f"  纬度: {info['lat_min']:.2f}° ~ {info['lat_max']:.2f}°")
    print(f"  分辨率: {info['resolution_lon']:.4f}° × {info['resolution_lat']:.4f}°")
    print(f"  图片尺寸: {info['image_size'][0]} × {info['image_size'][1]} 像素")

    # 测试坐标转换
    test_locations = [
        ('北京', 116.4074, 39.9042),
        ('上海', 121.4737, 31.2304),
        ('广州', 113.2644, 23.1291)
    ]

    print("\n坐标转换测试:")
    for name, lon, lat in test_locations:
        if mapper.is_valid_coordinate(lon, lat):
            pixel_x, pixel_y = mapper.geo_to_pixel(lon, lat)
            print(f"  {name}: ({lon:.2f}, {lat:.2f}) -> 像素({pixel_x}, {pixel_y})")
        else:
            print(f"  {name}: ({lon:.2f}, {lat:.2f}) -> 超出范围")


def example_data_quality_control():
    """数据质量控制示例"""
    print("\n" + "=" * 60)
    print("高级示例4: 数据质量控制")
    print("=" * 60)

    import pandas as pd
    import numpy as np

    # 创建包含异常值的数据
    dates = pd.date_range('2024-03-10', periods=100, freq='6T')
    data = {
        'timestamp': dates,
        'location_name': ['测试站'] * 100,
        'longitude': [116.4074] * 100,
        'latitude': [39.9042] * 100,
        'dbz_value': list(np.random.uniform(5, 50, 95)) + [999, -100, np.nan, np.nan, np.nan]
    }

    df = pd.DataFrame(data)

    print(f"\n原始数据统计:")
    print(f"  总记录数: {len(df)}")
    print(f"  dBZ范围: {df['dbz_value'].min():.1f} ~ {df['dbz_value'].max():.1f}")
    print(f"  缺失值: {df['dbz_value'].isna().sum()}")

    # 创建CSV生成器(包含质量控制)
    csv_generator = CSVGenerator(target_interval='15T')

    # 处理数据
    df_processed = csv_generator.generate_csv(
        df,
        output_path='./data/processed/quality_controlled.csv',
        add_temporal_features=True
    )

    print(f"\n处理后数据统计:")
    print(f"  总记录数: {len(df_processed)}")
    if 'dbz_value' in df_processed.columns:
        valid_data = df_processed['dbz_value'].dropna()
        if len(valid_data) > 0:
            print(f"  dBZ范围: {valid_data.min():.1f} ~ {valid_data.max():.1f}")
        print(f"  缺失值: {df_processed['dbz_value'].isna().sum()}")


def example_different_intervals():
    """不同时间间隔处理"""
    print("\n" + "=" * 60)
    print("高级示例5: 不同时间间隔处理")
    print("=" * 60)

    import pandas as pd
    import numpy as np

    # 创建6分钟间隔的原始数据
    dates = pd.date_range('2024-03-10 00:00:00', periods=240, freq='6T')
    data = {
        'timestamp': dates,
        'location_name': ['测试站'] * 240,
        'dbz_value': np.random.uniform(5, 50, 240)
    }

    df = pd.DataFrame(data)
    print(f"\n原始数据: {len(df)} 条记录 (6分钟间隔)")

    # 测试不同重采样间隔
    intervals = ['6T', '15T', '30T', '1H']

    for interval in intervals:
        generator = CSVGenerator(target_interval=interval)
        df_resampled = generator._resample_data(df.copy(), 'mean')
        print(f"  {interval} 间隔: {len(df_resampled)} 条记录")


def example_summary_statistics():
    """生成统计摘要"""
    print("\n" + "=" * 60)
    print("高级示例6: 统计摘要")
    print("=" * 60)

    import pandas as pd
    import numpy as np

    # 创建示例数据
    dates = pd.date_range('2024-03-10', periods=100, freq='15T')
    data = {
        'timestamp': dates,
        'location_name': ['北京'] * 50 + ['上海'] * 50,
        'dbz_value': np.random.uniform(5, 50, 100),
        'dbz_category': np.random.choice(['weak', 'moderate', 'strong'], 100),
        'data_quality': np.random.choice(['good', 'outlier'], 100, p=[0.95, 0.05])
    }

    df = pd.DataFrame(data)

    from src.features.csv_generator import create_summary_statistics

    # 生成统计摘要
    stats = create_summary_statistics(df, 'data/processed/statistics.json')

    print("\n数据统计摘要:")
    print(f"  总记录数: {stats['total_records']}")
    print(f"  时间范围: {stats['date_range']['start']} ~ {stats['date_range']['end']}")
    print(f"  位置数量: {stats['locations']}")

    if stats.get('dbz_statistics'):
        dbz_stats = stats['dbz_statistics']
        print(f"\n  dBZ统计:")
        print(f"    平均值: {dbz_stats['mean']:.2f}")
        print(f"    标准差: {dbz_stats['std']:.2f}")
        print(f"    最小值: {dbz_stats['min']:.2f}")
        print(f"    最大值: {dbz_stats['max']:.2f}")
        print(f"    中位数: {dbz_stats['median']:.2f}")

    if stats.get('category_distribution'):
        print(f"\n  类别分布:")
        for category, count in stats['category_distribution'].items():
            print(f"    {category}: {count}")


def example_error_handling():
    """错误处理示例"""
    print("\n" + "=" * 60)
    print("高级示例7: 错误处理")
    print("=" * 60)

    # 定义一个超出范围的位置
    invalid_locations = [
        {'name': '无效位置', 'lon': 200.0, 'lat': 100.0},  # 超出有效范围
        {'name': '北京', 'lon': 116.4074, 'lat': 39.9042}
    ]

    # 创建提取器
    extractor = RadarDataExtractor(invalid_locations)

    print("\n错误处理演示:")
    print("系统会自动处理:")
    print("  - 无效的地理坐标")
    print("  - 缺失的图片文件")
    print("  - 损坏的图片数据")
    print("  - 时间戳解析错误")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("气象雷达数据提取系统 - 高级使用示例")
    print("=" * 60)

    # 确保必要的目录存在
    os.makedirs('./data/raw', exist_ok=True)
    os.makedirs('./data/processed', exist_ok=True)
    os.makedirs('./logs', exist_ok=True)

    try:
        # 运行各个示例
        example_batch_download()
        example_custom_color_scale()
        example_coordinate_mapping()
        example_data_quality_control()
        example_different_intervals()
        example_summary_statistics()
        example_error_handling()

        print("\n" + "=" * 60)
        print("所有高级示例运行完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
