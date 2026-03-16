#!/usr/bin/env python3
"""
处理单张雷达图片（测试用）

用于测试图片处理功能，查看详细的处理过程和结果
"""
import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.weather_station import WeatherStation
from app.models.radar_image import RadarImage
from app.models.radar_data import SiteRadarData
from app.services.processing_service import RadarDataProcessor, CoordinateMapper, ColorScaleParser


def process_single_image(image_id: int = None, filename: str = None, force: bool = False):
    """
    处理单张雷达图片

    Args:
        image_id: 雷达图片ID
        filename: 雷达图片文件名
        force: 是否强制重新处理
    """
    print("=" * 80)
    print("🔍 单张图片处理测试")
    print("=" * 80)

    db = SessionLocal()

    try:
        # 查找雷达图片
        query = db.query(RadarImage).filter(RadarImage.download_status == 'success')

        if image_id:
            radar_image = query.filter(RadarImage.id == image_id).first()
        elif filename:
            radar_image = query.filter(RadarImage.filename == filename).first()
        else:
            # 获取最新的一张
            radar_image = query.order_by(RadarImage.observation_time.desc()).first()

        if not radar_image:
            print("❌ 未找到指定的雷达图片")
            print("\n提示:")
            print("  - 使用 --id <图片ID> 指定ID")
            print("  - 使用 --filename <文件名> 指定文件名")
            print("  - 不带参数则处理最新的一张")
            return

        # 显示图片信息
        print(f"\n📸 图片信息:")
        print(f"  ID: {radar_image.id}")
        print(f"  文件名: {radar_image.filename}")
        print(f"  观测时间: {radar_image.observation_time}")
        print(f"  文件路径: {radar_image.file_path}")
        print(f"  文件大小: {radar_image.file_size} bytes")

        # 检查文件
        image_path = Path(radar_image.file_path)
        if not image_path.exists():
            print(f"\n❌ 文件不存在: {image_path}")
            return

        # 显示坐标映射信息
        print(f"\n🗺️  坐标映射信息:")
        mapper = CoordinateMapper(str(image_path))
        coverage = mapper.get_coverage_info()
        print(f"  经度范围: {coverage['lon_min']:.2f}° ~ {coverage['lon_max']:.2f}°")
        print(f"  纬度范围: {coverage['lat_min']:.2f}° ~ {coverage['lat_max']:.2f}°")
        print(f"  分辨率: {coverage['resolution_lon']:.4f}° × {coverage['resolution_lat']:.4f}°")
        print(f"  图片尺寸: {coverage['image_size'][0]} × {coverage['image_size'][1]} 像素")

        # 获取所有站点
        sites = db.query(WeatherStation).filter(WeatherStation.is_active == True).all()
        if not sites:
            print("\n❌ 未找到启用的站点")
            return

        print(f"\n📍 找到 {len(sites)} 个站点")

        # 初始化处理器
        processor = RadarDataProcessor()

        # 处理每个站点
        print(f"\n{'=' * 80}")
        print("开始处理站点数据")
        print("=" * 80)

        results = []

        for idx, site in enumerate(sites, 1):
            print(f"\n[{idx}/{len(sites)}] 处理站点: {site.name} ({site.code})")
            print(f"  经纬度: ({site.longitude}, {site.latitude})")

            # 检查是否已存在
            existing = db.query(SiteRadarData).filter(
                SiteRadarData.site_id == site.id,
                SiteRadarData.observation_time == radar_image.observation_time
            ).first()

            if existing and not force:
                print(f"  ⏭️  已存在数据，跳过（使用 --force 强制重新处理）")
                results.append({
                    'site': site,
                    'status': 'skipped',
                    'data': existing
                })
                continue

            # 检查坐标是否在范围内
            if not mapper.is_valid_coordinate(float(site.longitude), float(site.latitude)):
                print(f"  ⚠️  坐标超出图片范围")
                results.append({
                    'site': site,
                    'status': 'out_of_range'
                })
                continue

            # 获取像素坐标
            pixel_x, pixel_y = mapper.geo_to_pixel(
                float(site.longitude),
                float(site.latitude)
            )
            print(f"  像素坐标: ({pixel_x}, {pixel_y})")

            # 获取RGB值
            rgb = mapper.get_pixel_value(float(site.longitude), float(site.latitude))
            print(f"  RGB值: ({rgb[0]}, {rgb[1]}, {rgb[2]})")

            # 转换为dBZ
            dbz_value = processor.color_parser.rgb_to_dbz(rgb)
            dbz_category = processor.color_parser.dbz_to_category(dbz_value)
            cloud_impact = processor.color_parser.get_cloud_impact_factor(dbz_value)

            print(f"  dBZ值: {dbz_value:.2f}")
            print(f"  强度等级: {dbz_category}")
            print(f"  云影响因子: {cloud_impact:.3f}")

            # 保存到数据库
            if force and existing:
                # 更新现有记录
                existing.dbz_value = dbz_value
                existing.dbz_category = dbz_category
                existing.cloud_impact_factor = cloud_impact
                existing.rgb_value = f"{rgb[0]},{rgb[1]},{rgb[2]}"
                existing.pixel_x = pixel_x
                existing.pixel_y = pixel_y
                existing.data_quality = 'good'
                print(f"  ✅ 已更新数据库记录")
            else:
                # 创建新记录
                radar_data = SiteRadarData(
                    site_id=site.id,
                    observation_time=radar_image.observation_time,
                    dbz_value=dbz_value,
                    dbz_category=dbz_category,
                    cloud_impact_factor=cloud_impact,
                    rgb_value=f"{rgb[0]},{rgb[1]},{rgb[2]}",
                    pixel_x=pixel_x,
                    pixel_y=pixel_y,
                    data_quality='good',
                    data_source='actual'
                )
                db.add(radar_data)
                print(f"  ✅ 已保存到数据库")

            results.append({
                'site': site,
                'status': 'success',
                'dbz_value': dbz_value,
                'dbz_category': dbz_category,
                'cloud_impact': cloud_impact
            })

        # 提交事务
        db.commit()

        # 显示统计
        print(f"\n{'=' * 80}")
        print("📊 处理结果统计")
        print("=" * 80)

        success_count = sum(1 for r in results if r['status'] == 'success')
        skipped_count = sum(1 for r in results if r['status'] == 'skipped')
        out_of_range_count = sum(1 for r in results if r['status'] == 'out_of_range')

        print(f"  总站点数: {len(sites)}")
        print(f"  ✅ 成功处理: {success_count}")
        print(f"  ⏭️  跳过（已存在）: {skipped_count}")
        print(f"  ⚠️  超出范围: {out_of_range_count}")

        # 显示结果表格
        print(f"\n详细结果:")
        print(f"{'站点名称':<10} {'状态':<15} {'dBZ值':<10} {'强度等级':<10}")
        print("-" * 80)

        for result in results:
            site = result['site']
            status = result['status']

            if status == 'success':
                print(f"{site.name:<10} {'成功':<15} {result['dbz_value']:<10.2f} {result['dbz_category']:<10}")
            elif status == 'skipped':
                print(f"{site.name:<10} {'跳过':<15} {'-':<10} {'-':<10}")
            elif status == 'out_of_range':
                print(f"{site.name:<10} {'超出范围':<15} {'-':<10} {'-':<10}")

        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise

    finally:
        db.close()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='处理单张雷达图片（测试用）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 处理最新的一张图片
  python3 scripts/process_single_image.py

  # 处理指定ID的图片
  python3 scripts/process_single_image.py --id 1

  # 处理指定文件名的图片
  python3 scripts/process_single_image.py --filename radar_20260311000000.png

  # 强制重新处理（覆盖已存在数据）
  python3 scripts/process_single_image.py --force
        """
    )

    parser.add_argument('--id', type=int, default=None,
                       help='雷达图片ID')
    parser.add_argument('--filename', type=str, default=None,
                       help='雷达图片文件名')
    parser.add_argument('--force', '-f', action='store_true',
                       help='强制重新处理，覆盖已存在的数据')

    args = parser.parse_args()

    process_single_image(
        image_id=args.id,
        filename=args.filename,
        force=args.force
    )


if __name__ == "__main__":
    main()
