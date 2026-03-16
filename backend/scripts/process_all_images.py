#!/usr/bin/env python3
"""
批量处理雷达图片，生成站点数据

将已下载的雷达图片转换为各站点的雷达数据（dBZ值等）
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
from app.services.processing_service import RadarDataProcessor


def process_all_images(
    limit: int = None,
    force: bool = False,
    verbose: bool = True
):
    """
    批量处理所有雷达图片

    Args:
        limit: 限制处理数量，None表示处理全部
        force: 是否强制重新处理（忽略已存在的数据）
        verbose: 是否显示详细信息
    """
    print("=" * 80)
    print("🚀 开始批量处理雷达图片")
    print("=" * 80)

    db = SessionLocal()

    try:
        # 获取所有站点
        sites = db.query(WeatherStation).filter(WeatherStation.status == 'active').all()
        if not sites:
            print("❌ 未找到启用的站点，请先运行: python3 scripts/init_sites.py init")
            return

        print(f"\n📍 找到 {len(sites)} 个启用站点")
        for site in sites:
            print(f"  - {site.station_name} ({site.station_id}): ({site.longitude}, {site.latitude})")

        # 获取雷达图片
        query = db.query(RadarImage).filter(
            RadarImage.download_status == 'success'
        ).order_by(RadarImage.observation_time.desc())

        if limit:
            query = query.limit(limit)

        radar_images = query.all()

        if not radar_images:
            print("\n⚠️  未找到已下载的雷达图片")
            print("   请先运行: python3 scripts/download_all_fixed.py")
            return

        print(f"\n📸 找到 {len(radar_images)} 张雷达图片")

        # 初始化处理器（传递数据库会话以支持校准）
        processor = RadarDataProcessor(use_calibration=True, db=db)

        # 统计信息
        stats = {
            'total_images': len(radar_images),
            'total_sites': len(sites),
            'total_expected': len(radar_images) * len(sites),
            'processed': 0,
            'skipped': 0,
            'out_of_range': 0,
            'errors': 0,
            'start_time': datetime.now()
        }

        print(f"\n📊 预计生成 {stats['total_expected']} 条站点数据")
        print(f"⏱️  预计耗时: {stats['total_expected'] / 100:.1f} 秒")
        print("\n" + "=" * 80)

        # 处理每张图片
        for img_idx, radar_image in enumerate(radar_images, 1):
            if verbose:
                print(f"\n🖼️  [{img_idx}/{len(radar_images)}] 处理图片: {radar_image.filename}")
                print(f"   观测时间: {radar_image.observation_time}")

            # 检查文件是否存在
            image_path = Path(radar_image.file_path)
            if not image_path.exists():
                print(f"   ⚠️  文件不存在，跳过")
                stats['errors'] += 1
                continue

            # 处理该图片的所有站点
            for site_idx, site in enumerate(sites, 1):
                try:
                    # 检查是否已存在数据
                    if not force:
                        existing = db.query(SiteRadarData).filter(
                            SiteRadarData.site_id == site.id,
                            SiteRadarData.observation_time == radar_image.observation_time
                        ).first()

                        if existing:
                            if verbose and site_idx == 1:
                                print(f"   ⏭️  数据已存在，跳过（使用 --force 强制重新处理）")
                            stats['skipped'] += 1
                            continue

                    # 处理站点数据
                    result = processor.process_site_data(
                        image_path=str(image_path),
                        site_id=site.id,
                        longitude=float(site.longitude),
                        latitude=float(site.latitude),
                        observation_time=radar_image.observation_time
                    )

                    # 处理结果
                    if result['status'] == 'success':
                        # 保存到数据库
                        radar_data = SiteRadarData(
                            site_id=site.id,
                            observation_time=radar_image.observation_time,
                            dbz_value=result['dbz_value'],
                            dbz_category=result['dbz_category'],
                            cloud_impact_factor=result['cloud_impact_factor'],
                            rgb_value=result['rgb_value'],
                            pixel_x=result.get('pixel_x'),
                            pixel_y=result.get('pixel_y'),
                            data_quality=result['data_quality'],
                            data_source=result['data_source']
                        )

                        db.add(radar_data)
                        stats['processed'] += 1

                        if verbose:
                            print(f"   ✅ [{site_idx}/{len(sites)}] {site.station_name}: "
                                  f"dBZ={result['dbz_value']}, {result['dbz_category']}")

                    elif result['status'] == 'out_of_range':
                        stats['out_of_range'] += 1
                        if verbose and site_idx == 1:
                            print(f"   ⚠️  [{site_idx}/{len(sites)}] {site.station_name}: 坐标超出范围")

                    else:
                        stats['errors'] += 1
                        if verbose:
                            print(f"   ❌ [{site_idx}/{len(sites)}] {site.station_name}: {result.get('error', '未知错误')}")

                except Exception as e:
                    stats['errors'] += 1
                    if verbose:
                        print(f"   ❌ [{site_idx}/{len(sites)}] {site.station_name}: 处理异常 - {e}")

            # 每处理完一张图片提交一次
            db.commit()

            # 显示进度
            progress = (img_idx / len(radar_images)) * 100
            print(f"   进度: {progress:.1f}% ({img_idx}/{len(radar_images)})")

        # 完成统计
        stats['end_time'] = datetime.now()
        stats['duration'] = (stats['end_time'] - stats['start_time']).total_seconds()

        print("\n" + "=" * 80)
        print("📊 处理完成统计")
        print("=" * 80)
        print(f"  处理图片: {stats['total_images']} 张")
        print(f"  站点数量: {stats['total_sites']} 个")
        print(f"  预期数据: {stats['total_expected']} 条")
        print(f"  " + "-" * 60)
        print(f"  ✅ 成功处理: {stats['processed']} 条")
        print(f"  ⏭️  跳过（已存在）: {stats['skipped']} 条")
        print(f"  ⚠️  超出范围: {stats['out_of_range']} 条")
        print(f"  ❌ 错误: {stats['errors']} 条")
        print(f"  " + "-" * 60)
        print(f"  ⏱️  总耗时: {stats['duration']:.1f} 秒")
        print(f"  ⚡ 平均速度: {stats['total_expected'] / stats['duration']:.1f} 条/秒")
        print("=" * 80)

        # 数据库统计
        total_records = db.query(SiteRadarData).count()
        print(f"\n📈 数据库总记录数: {total_records} 条")

    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        db.rollback()
        raise

    finally:
        db.close()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='批量处理雷达图片生成站点数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 处理所有图片
  python3 scripts/process_all_images.py

  # 处理最新的10张图片
  python3 scripts/process_all_images.py --limit 10

  # 强制重新处理（覆盖已存在数据）
  python3 scripts/process_all_images.py --force

  # 静默模式（不显示详细信息）
  python3 scripts/process_all_images.py --quiet
        """
    )

    parser.add_argument('--limit', '-l', type=int, default=None,
                       help='限制处理数量（默认处理全部）')
    parser.add_argument('--force', '-f', action='store_true',
                       help='强制重新处理，覆盖已存在的数据')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='静默模式，不显示详细信息')

    args = parser.parse_args()

    process_all_images(
        limit=args.limit,
        force=args.force,
        verbose=not args.quiet
    )


if __name__ == "__main__":
    main()
