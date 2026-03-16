"""
基础使用示例

演示如何使用雷达数据提取系统提取指定经纬度的气象数据
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from src import RadarDataExtractor, CSVGenerator, get_city_coordinates, Timer


def example_basic_extraction():
    """基础数据提取示例"""
    print("=" * 60)
    print("示例1: 基础数据提取")
    print("=" * 60)

    # 定义目标位置
    locations = [
        {'name': '北京', 'lon': 116.4074, 'lat': 39.9042},
        {'name': '上海', 'lon': 121.4737, 'lat': 31.2304},
        {'name': '广州', 'lon': 113.2644, 'lat': 23.1291}
    ]

    # 创建数据提取器
    extractor = RadarDataExtractor(locations)

    # 模拟数据提取(假设你有雷达图片)
    print(f"\n目标位置: {[loc['name'] for loc in locations]}")
    print(f"数据时间范围: 2024-03-10 00:00:00 到 2024-03-10 23:59:59")
    print(f"原始数据间隔: 6分钟")
    print(f"输出数据间隔: 15分钟")

    # 实际使用时，你需要提供真实的雷达图片路径
    # df = extractor.extract_time_series(
    #     start_time=datetime(2024, 3, 10, 0, 0),
    #     end_time=datetime(2024, 3, 10, 23, 59),
    #     image_dir='./data/raw'
    # )

    # 这里创建一个示例数据
    import pandas as pd
    import numpy as np

    dates = pd.date_range('2024-03-10 00:00:00', periods=240, freq='6T')
    data = []
    for location in locations:
        for date in dates:
            data.append({
                'timestamp': date,
                'location_name': location['name'],
                'longitude': location['lon'],
                'latitude': location['lat'],
                'dbz_value': np.random.uniform(5, 50),
                'dbz_category': np.random.choice(['weak', 'moderate', 'strong']),
                'cloud_impact_factor': np.random.uniform(0, 1)
            })

    df = pd.DataFrame(data)
    print(f"\n模拟数据: {len(df)} 条记录")

    # 创建CSV生成器
    csv_generator = CSVGenerator(target_interval='15T')

    # 生成CSV文件
    output_path = './data/processed/example_output.csv'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    df_output = csv_generator.generate_csv(
        df,
        output_path=output_path,
        add_temporal_features=True
    )

    print(f"\n输出数据: {len(df_output)} 条记录")
    print(f"压缩比: {len(df_output) / len(df):.1%}")
    print(f"输出文件: {output_path}")

    # 显示前几条记录
    print("\n前5条记录:")
    print(df_output[['timestamp', 'location_name', 'dbz_value', 'dbz_category']].head())


def example_city_extraction():
    """使用城市名称提取数据"""
    print("\n" + "=" * 60)
    print("示例2: 使用城市名称提取数据")
    print("=" * 60)

    # 使用配置文件中的城市坐标
    cities = ['北京', '上海', '深圳', '成都', '西安']

    locations = []
    for city in cities:
        lon, lat = get_city_coordinates(city)
        locations.append({'name': city, 'lon': lon, 'lat': lat})

    print(f"\n选择的城市: {cities}")
    for loc in locations:
        print(f"  {loc['name']}: ({loc['lon']:.2f}, {loc['lat']:.2f})")

    # 创建提取器
    extractor = RadarDataExtractor(locations)
    print(f"\n数据提取器已创建，包含 {len(locations)} 个位置")


def example_neighborhood_analysis():
    """邻域分析示例"""
    print("\n" + "=" * 60)
    print("示例3: 邻域分析")
    print("=" * 60)

    # 提取邻域特征
    print("\n邻域分析功能:")
    print("  - 提取指定半径内的统计特征")
    print("  - 计算最大值、最小值、平均值、标准差等")
    print("  - 识别强回波区域")
    print("  - 支持自定义邻域半径(公里)")

    # 示例参数
    radius_km = 20
    print(f"\n示例参数:")
    print(f"  邻域半径: {radius_km} 公里")
    print(f"  约等于: {radius_km / 111:.3f} 度")

    # 实际使用时:
    # df = extractor.extract_time_series(
    #     start_time=datetime(2024, 3, 10, 0, 0),
    #     end_time=datetime(2024, 3, 10, 23, 59),
    #     image_dir='./data/raw',
    #     extract_neighborhood=True,
    #     neighborhood_radius=20
    # )


def example_temporal_features():
    """时序特征示例"""
    print("\n" + "=" * 60)
    print("示例4: 时序特征分析")
    print("=" * 60)

    print("\n时序特征包括:")
    print("  - dbz_change_rate: dBZ变化率 (dBZ/小时)")
    print("  - dbz_trend: dBZ趋势 (线性回归斜率)")
    print("  - dbz_ma_2: 2时间步移动平均")
    print("  - dbz_ma_3: 3时间步移动平均")
    print("  - dbz_max_past_3: 过去3时间步最大值")
    print("  - dbz_max_past_6: 过去6时间步最大值")

    print("\n这些特征有助于:")
    print("  - 预测云团发展趋势")
    print("  - 提前预警强对流天气")
    print("  - 提高光伏功率预测准确性")


def example_performance_measurement():
    """性能测量示例"""
    print("\n" + "=" * 60)
    print("示例5: 性能测量")
    print("=" * 60)

    from src.utils import Timer

    print("\n使用计时器测量处理时间:")

    with Timer() as timer:
        # 模拟数据处理
        import time
        time.sleep(1)

    print(f"处理耗时: {timer.elapsed_seconds():.2f} 秒")


def example_custom_locations():
    """自定义位置示例"""
    print("\n" + "=" * 60)
    print("示例6: 自定义位置")
    print("=" * 60)

    # 定义自定义位置(例如光伏电站位置)
    pv_stations = [
        {'name': '光伏电站A', 'lon': 116.1234, 'lat': 39.5678},
        {'name': '光伏电站B', 'lon': 120.3456, 'lat': 30.7890},
        {'name': '风电场C', 'lon': 115.2345, 'lat': 38.6789}
    ]

    print("\n自定义位置:")
    for station in pv_stations:
        print(f"  {station['name']}: ({station['lon']:.2f}, {station['lat']:.2f})")

    # 创建提取器
    extractor = RadarDataExtractor(pv_stations)
    print(f"\n数据提取器已创建，包含 {len(pv_stations)} 个自定义位置")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("气象雷达数据提取系统 - 使用示例")
    print("=" * 60)

    try:
        # 运行各个示例
        example_basic_extraction()
        example_city_extraction()
        example_neighborhood_analysis()
        example_temporal_features()
        example_performance_measurement()
        example_custom_locations()

        print("\n" + "=" * 60)
        print("所有示例运行完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
