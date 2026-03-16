#!/usr/bin/env python3
"""
NMC雷达图片批量下载脚本（使用NMC直接URL方式）

功能:
- 从NMC批量下载雷达图片（每6分钟一张）
- 支持指定下载数量或时间范围
- 自动去重（断点续传）
- 完整的进度显示
- 自动处理UTC到北京时间转换

使用方法:
python3 batch_download_radar.py --count 50
python3 batch_download_radar.py --hours 24
python3 batch_download_radar.py --start "2026-03-15 00:00:00" --end "2026-03-16 00:00:00"
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.download_service_nmc import NMCRadarImageDownloader
from app.core.database import SessionLocal
from app.models.radar_image import RadarImage


def print_banner():
    """打印横幅"""
    print("=" * 80)
    print("🌤️  NMC雷达图片批量下载工具".center(80))
    print("=" * 80)
    print()


def print_statistics(stats):
    """打印统计信息"""
    print("\n" + "=" * 80)
    print("📊 下载统计".center(80))
    print("=" * 80)

    total = stats.get('total', 0)
    success = stats.get('success', 0)
    failed = stats.get('failed', 0)
    skipped = stats.get('skipped', 0)

    print(f"总计任务: {total}")
    print(f"✅ 成功: {success}")
    print(f"⏭️  跳过: {skipped}")
    print(f"❌ 失败: {failed}")

    if total > 0:
        success_rate = (success / total) * 100
        print(f"\n成功率: {success_rate:.2f}%")

    print("=" * 80)


def generate_report(stats, start_time, end_time):
    """生成详细报告"""
    report = {
        "download_session": {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": (end_time - start_time).total_seconds()
        },
        "statistics": stats
    }

    # 获取数据库中的统计
    db = SessionLocal()
    try:
        total_records = db.query(RadarImage).count()
        success_records = db.query(RadarImage).filter(
            RadarImage.download_status == 'success'
        ).count()
        failed_records = db.query(RadarImage).filter(
            RadarImage.download_status == 'failed'
        ).count()

        report["database"] = {
            "total_records": total_records,
            "success_records": success_records,
            "failed_records": failed_records,
            "success_rate": success_records / total_records if total_records > 0 else 0
        }

        # 获取最新的下载记录
        latest = db.query(RadarImage).filter(
            RadarImage.download_status == 'success'
        ).order_by(RadarImage.observation_time.desc()).limit(5).all()

        report["latest_downloads"] = [
            {
                "observation_time": img.observation_time.isoformat(),
                "file_path": img.file_path,
                "download_url": img.download_url
            }
            for img in latest
        ]

    finally:
        db.close()

    return report


def batch_download_by_count(count: int = 50, force: bool = False):
    """
    按数量批量下载雷达图片

    Args:
        count: 下载数量
        force: 是否强制重新下载
    """
    print_banner()

    # 计算时间范围（每6分钟一张）
    downloader = NMCRadarImageDownloader()
    hours = (count * downloader.INTERVAL_MINUTES) // 60 + 1

    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)

    # 显示配置
    print(f"📋 下载配置:")
    print(f"   目标数量: {count} 张（约 {hours} 小时数据）")
    print(f"   强制下载: {'是' if force else '否（跳过已下载）'}")
    print(f"   时间范围: {start_time.strftime('%Y-%m-%d %H:%M')} ~ {end_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"   数据目录: ../data/raw")
    print()

    # 开始下载
    start = datetime.now()
    print(f"\n🚀 开始下载: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    stats = downloader.download_range(start_time, end_time, force=force)
    end = datetime.now()

    # 打印最终统计
    print_statistics(stats)

    # 生成报告
    print("\n📝 生成报告...")
    report = generate_report(stats, start, end)

    # 保存报告
    report_file = Path("../logs/download_report.json")
    report_file.parent.mkdir(exist_ok=True)

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n📄 报告已保存: {report_file.absolute()}")

    # 总结
    duration = (end - start).total_seconds()
    print("=" * 80)
    print(f"✅ 下载完成!".center(80))
    print(f"总耗时: {duration:.2f} 秒")
    print(f"平均速度: {duration/max(stats['success'], 1):.2f} 秒/张")
    print("=" * 80)

    return stats


def batch_download_by_range(
    start_time: datetime,
    end_time: datetime,
    force: bool = False
):
    """
    按时间范围批量下载雷达图片

    Args:
        start_time: 开始时间
        end_time: 结束时间
        force: 是否强制重新下载
    """
    print_banner()

    # 计算预计数量
    downloader = NMCRadarImageDownloader()
    total_minutes = int((end_time - start_time).total_seconds() // 60)
    estimated_count = total_minutes // downloader.INTERVAL_MINUTES

    # 显示配置
    print(f"📋 下载配置:")
    print(f"   开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   预计数量: 约 {estimated_count} 张")
    print(f"   强制下载: {'是' if force else '否（跳过已下载）'}")
    print()

    # 开始下载
    start = datetime.now()
    print(f"\n🚀 开始下载: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    stats = downloader.download_range(start_time, end_time, force=force)
    end = datetime.now()

    # 打印最终统计
    print_statistics(stats)

    # 总结
    duration = (end - start).total_seconds()
    print("=" * 80)
    print(f"✅ 下载完成!".center(80))
    print(f"总耗时: {duration:.2f} 秒")
    print("=" * 80)

    return stats


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='NMC雷达图片批量下载工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 下载最近50张图片（约5小时数据）
  python3 batch_download_radar.py --count 50

  # 下载最近24小时的数据
  python3 batch_download_radar.py --hours 24

  # 下载指定时间范围的数据
  python3 batch_download_radar.py --start "2026-03-15 00:00:00" --end "2026-03-16 00:00:00"

  # 强制重新下载
  python3 batch_download_radar.py --count 50 --force
        '''
    )

    parser.add_argument(
        '--count',
        type=int,
        default=0,
        help='下载数量（每6分钟一张）'
    )

    parser.add_argument(
        '--hours',
        type=float,
        default=0,
        help='下载最近N小时的数据'
    )

    parser.add_argument(
        '--start',
        type=str,
        default=None,
        help='开始时间 (格式: YYYY-MM-DD HH:MM:SS)'
    )

    parser.add_argument(
        '--end',
        type=str,
        default=None,
        help='结束时间 (格式: YYYY-MM-DD HH:MM:SS)'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='强制重新下载（覆盖已存在的文件）'
    )

    args = parser.parse_args()

    # 解析参数
    if args.start and args.end:
        # 按时间范围下载
        start_time = datetime.strptime(args.start, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(args.end, "%Y-%m-%d %H:%M:%S")
        batch_download_by_range(start_time, end_time, args.force)
    elif args.hours > 0:
        # 按小时数下载
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=args.hours)
        batch_download_by_range(start_time, end_time, args.force)
    elif args.count > 0:
        # 按数量下载
        batch_download_by_count(count=args.count, force=args.force)
    else:
        # 默认下载最近24小时
        parser.print_help()
        print("\n使用默认配置：下载最近24小时的数据")
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        batch_download_by_range(start_time, end_time, False)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断下载")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 下载失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
