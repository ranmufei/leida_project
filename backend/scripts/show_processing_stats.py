#!/usr/bin/env python3
"""
显示站点雷达数据统计信息

展示数据库中已处理的雷达数据统计情况
"""
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.site import Site
from app.models.radar_image import RadarImage
from app.models.radar_data import SiteRadarData
from sqlalchemy import func


def show_statistics():
    """显示统计数据"""
    print("=" * 80)
    print("📊 站点雷达数据统计")
    print("=" * 80)

    db = SessionLocal()

    try:
        # 1. 基础统计
        print(f"\n📈 基础统计")
        print("-" * 80)

        total_sites = db.query(Site).count()
        active_sites = db.query(Site).filter(Site.is_active == True).count()
        total_images = db.query(RadarImage).filter(RadarImage.download_status == 'success').count()
        total_records = db.query(SiteRadarData).count()

        print(f"  总站点数: {total_sites}")
        print(f"  启用站点: {active_sites}")
        print(f"  雷达图片: {total_images}")
        print(f"  数据记录: {total_records}")
        print(f"  预期记录: {total_images * active_sites} (图片数 × 站点数)")
        print(f"  完成度: {total_records / (total_images * active_sites) * 100:.1f}%" if total_images * active_sites > 0 else "  完成度: N/A")

        # 2. 数据来源统计
        print(f"\n📥 数据来源")
        print("-" * 80)

        source_stats = db.query(
            SiteRadarData.data_source,
            func.count(SiteRadarData.id).label('count')
        ).group_by(SiteRadarData.data_source).all()

        for source, count in source_stats:
            source_name = {
                'actual': '实际观测',
                'predicted': '预测数据'
            }.get(source, source)
            percentage = count / total_records * 100 if total_records > 0 else 0
            print(f"  {source_name}: {count} 条 ({percentage:.1f}%)")

        # 3. 数据质量统计
        print(f"\n✅ 数据质量")
        print("-" * 80)

        quality_stats = db.query(
            SiteRadarData.data_quality,
            func.count(SiteRadarData.id).label('count')
        ).group_by(SiteRadarData.data_quality).all()

        for quality, count in quality_stats:
            quality_name = {
                'good': '良好',
                'interpolated': '插值',
                'outlier': '异常值',
                'missing': '缺失'
            }.get(quality, quality)
            percentage = count / total_records * 100 if total_records > 0 else 0
            print(f"  {quality_name}: {count} 条 ({percentage:.1f}%)")

        # 4. dBZ强度分布
        print(f"\n🌩️  dBZ强度分布")
        print("-" * 80)

        dbz_stats = db.query(
            SiteRadarData.dbz_category,
            func.count(SiteRadarData.id).label('count')
        ).group_by(SiteRadarData.dbz_category).all()

        category_names = {
            'no_data': '无数据',
            'weak': '弱回波',
            'moderate': '中等回波',
            'strong': '强回波',
            'severe': '严重回波',
            'extreme': '极端回波'
        }

        for category, count in sorted(dbz_stats, key=lambda x: x[1] or 0, reverse=True):
            category_name = category_names.get(category, category)
            percentage = count / total_records * 100 if total_records > 0 else 0
            bar_length = int(percentage / 2)
            bar = "█" * bar_length
            print(f"  {category_name:<12}: {bar} {count} 条 ({percentage:.1f}%)")

        # 5. 各站点统计
        print(f"\n📍 各站点数据统计")
        print("-" * 80)
        print(f"  {'站点名称':<12} {'编码':<8} {'数据量':<10} {'平均dBZ':<10} {'最新时间':<20}")
        print("-" * 80)

        sites = db.query(Site).filter(Site.is_active == True).all()

        for site in sites:
            record_count = db.query(SiteRadarData).filter(
                SiteRadarData.site_id == site.id
            ).count()

            avg_dbz = db.query(
                func.avg(SiteRadarData.dbz_value)
            ).filter(SiteRadarData.site_id == site.id).scalar()

            latest_record = db.query(SiteRadarData).filter(
                SiteRadarData.site_id == site.id
            ).order_by(SiteRadarData.observation_time.desc()).first()

            latest_time = latest_record.observation_time.strftime("%Y-%m-%d %H:%M") if latest_record else "N/A"
            avg_dbz_str = f"{avg_dbz:.2f}" if avg_dbz else "N/A"

            print(f"  {site.name:<12} {site.code:<8} {record_count:<10} {avg_dbz_str:<10} {latest_time:<20}")

        # 6. 时间范围
        print(f"\n⏰ 时间范围")
        print("-" * 80)

        earliest = db.query(func.min(SiteRadarData.observation_time)).scalar()
        latest = db.query(func.max(SiteRadarData.observation_time)).scalar()

        if earliest and latest:
            time_span = latest - earliest
            print(f"  最早记录: {earliest.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  最新记录: {latest.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  时间跨度: {time_span.days} 天 {time_span.seconds // 3600} 小时")
        else:
            print("  暂无数据")

        # 7. 最近24小时统计
        print(f"\n📅 最近24小时")
        print("-" * 80)

        yesterday = datetime.now() - timedelta(hours=24)
        recent_count = db.query(SiteRadarData).filter(
            SiteRadarData.observation_time >= yesterday
        ).count()

        print(f"  数据量: {recent_count} 条")

        # 按站点统计
        recent_by_site = db.query(
            Site.name,
            func.count(SiteRadarData.id).label('count')
        ).join(SiteRadarData, Site.id == SiteRadarData.site_id).filter(
            SiteRadarData.observation_time >= yesterday
        ).group_by(Site.id, Site.name).order_by(
            func.count(SiteRadarData.id).desc()
        ).limit(5).all()

        if recent_by_site:
            print(f"  最活跃站点:")
            for site_name, count in recent_by_site:
                print(f"    - {site_name}: {count} 条")

        # 8. 数据完整性检查
        print(f"\n🔍 数据完整性")
        print("-" * 80)

        missing_count = 0
        for site in sites:
            site_images = db.query(RadarImage.observation_time).filter(
                RadarImage.download_status == 'success'
            ).all()

            for (obs_time,) in site_images:
                exists = db.query(SiteRadarData).filter(
                    SiteRadarData.site_id == site.id,
                    SiteRadarData.observation_time == obs_time
                ).first()

                if not exists:
                    missing_count += 1

        print(f"  缺失数据: {missing_count} 条")
        print(f"  完整性: {100 - missing_count / (total_images * active_sites) * 100:.1f}%" if total_images * active_sites > 0 else "  完整性: N/A")

        print("\n" + "=" * 80)

    except Exception as e:
        print(f"\n❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


def show_site_details(site_code: str = None):
    """显示站点详情"""
    if not site_code:
        return

    print("\n" + "=" * 80)
    print(f"📍 站点详情: {site_code}")
    print("=" * 80)

    db = SessionLocal()

    try:
        site = db.query(Site).filter(Site.code == site_code).first()
        if not site:
            print(f"❌ 未找到站点: {site_code}")
            return

        print(f"\n站点信息:")
        print(f"  名称: {site.name}")
        print(f"  编码: {site.code}")
        print(f"  位置: ({site.longitude}, {site.latitude})")
        print(f"  海拔: {site.altitude} m")
        print(f"  区域: {site.region}")

        # 数据统计
        total_records = db.query(SiteRadarData).filter(
            SiteRadarData.site_id == site.id
        ).count()

        print(f"\n数据统计:")
        print(f"  总记录数: {total_records}")

        # 最近10条记录
        print(f"\n最近10条记录:")
        print(f"  {'观测时间':<20} {'dBZ值':<10} {'强度等级':<12} {'云影响':<10}")
        print("-" * 80)

        recent_records = db.query(SiteRadarData).filter(
            SiteRadarData.site_id == site.id
        ).order_by(SiteRadarData.observation_time.desc()).limit(10).all()

        for record in recent_records:
            obs_time = record.observation_time.strftime('%Y-%m-%d %H:%M:%S')
            dbz_str = f"{record.dbz_value:.2f}" if record.dbz_value else "N/A"
            impact_str = f"{record.cloud_impact_factor:.3f}" if record.cloud_impact_factor else "N/A"
            print(f"  {obs_time:<20} {dbz_str:<10} {record.dbz_category:<12} {impact_str:<10}")

    except Exception as e:
        print(f"\n❌ 查询失败: {e}")

    finally:
        db.close()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='显示站点雷达数据统计信息',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 显示总体统计
  python3 scripts/show_processing_stats.py

  # 显示特定站点详情
  python3 scripts/show_processing_stats.py --site BJ001

  # 列出所有站点
  python3 scripts/show_processing_stats.py --list-sites
        """
    )

    parser.add_argument('--site', '-s', type=str, default=None,
                       help='显示特定站点的详细信息（站点编码）')
    parser.add_argument('--list-sites', '-l', action='store_true',
                       help='列出所有站点及其编码')

    args = parser.parse_args()

    if args.list_sites:
        db = SessionLocal()
        try:
            sites = db.query(Site).all()
            print(f"\n共有 {len(sites)} 个站点:\n")
            for site in sites:
                status = "✅" if site.is_active else "❌"
                print(f"  {status} {site.name} ({site.code}) - {site.region}")
        finally:
            db.close()
    elif args.site:
        show_site_details(args.site)
    else:
        show_statistics()


if __name__ == "__main__":
    main()
