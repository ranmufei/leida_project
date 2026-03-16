#!/usr/bin/env python3
"""
CMA雷达图片批量下载脚本

功能:
- 从CMA API批量下载雷达图片
- 支持指定下载数量
- 自动去重（断点续传）
- 完整的进度显示
- 生成详细报告

使用方法:
python3 batch_download_radar.py --count 50
python3 batch_download_radar.py --count 100 --force
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.download_service_real import RealRadarImageDownloader
from app.core.database import SessionLocal
from app.models.radar_image import RadarImage


def print_banner():
    """打印横幅"""
    print("=" * 80)
    print("🌤️  CMA雷达图片批量下载工具".center(80))
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
                "filename": img.filename,
                "original_filename": img.original_filename,
                "observation_time": img.observation_time.isoformat(),
                "file_size": img.file_size,
                "download_url": img.download_url
            }
            for img in latest
        ]

    finally:
        db.close()

    return report


def batch_download(count: int = 50, force: bool = False):
    """
    批量下载雷达图片

    Args:
        count: 下载数量
        force: 是否强制重新下载
    """
    print_banner()

    # 显示配置
    print(f"📋 下载配置:")
    print(f"   下载数量: {count} 张")
    print(f"   强制下载: {'是' if force else '否（跳过已下载）'}")
    print(f"   数据目录: ../data/raw")
    print()

    # 创建下载器
    print("⚙️  初始化下载器...")
    downloader = RealRadarImageDownloader()

    # 开始下载
    start_time = datetime.now()
    print(f"\n🚀 开始下载: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 分批下载（每批10张）
    batch_size = 10
    downloaded = 0
    total_stats = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'skipped': 0
    }

    while downloaded < count:
        current_batch = min(batch_size, count - downloaded)

        print(f"\n📦 批次 {downloaded // batch_size + 1}: 下载 {current_batch} 张")
        print("-" * 80)

        stats = downloader.download_latest_from_api(
            count=current_batch,
            force=force
        )

        # 更新统计
        for key in total_stats:
            total_stats[key] += stats.get(key, 0)

        downloaded += current_batch

        print(f"\n批次完成: 成功 {stats.get('success', 0)}, 跳过 {stats.get('skipped', 0)}, 失败 {stats.get('failed', 0)}")

        # 如果全部失败，停止下载
        if stats.get('failed', 0) == current_batch:
            print("\n⚠️  连续失败，停止下载")
            break

        # 短暂延迟，避免请求过快
        if downloaded < count:
            print("⏳ 等待 2 秒...")
            time.sleep(2)

    end_time = datetime.now()

    # 打印最终统计
    print_statistics(total_stats)

    # 生成报告
    print("\n📝 生成报告...")
    report = generate_report(total_stats, start_time, end_time)

    # 保存报告
    report_file = Path("../logs/download_report.json")
    report_file.parent.mkdir(exist_ok=True)

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n📄 报告已保存: {report_file.absolute()}")

    # 显示文件信息
    print("\n💾 下载的文件:")
    print("-" * 80)

    db = SessionLocal()
    try:
        latest = db.query(RadarImage).filter(
            RadarImage.download_status == 'success'
        ).order_by(RadarImage.download_time.desc()).limit(10).all()

        for img in latest:
            size_mb = img.file_size / (1024 * 1024) if img.file_size else 0
            print(f"  {img.filename}")
            print(f"    时间: {img.observation_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    大小: {size_mb:.2f} MB")
            print(f"    原文件: {img.original_filename}")
            print()

    finally:
        db.close()

    # 总结
    duration = (end_time - start_time).total_seconds()
    print("=" * 80)
    print(f"✅ 下载完成!".center(80))
    print(f"总耗时: {duration:.2f} 秒")
    print(f"平均速度: {duration/max(total_stats['success'], 1):.2f} 秒/张")
    print("=" * 80)

    return total_stats


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='CMA雷达图片批量下载工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 下载50张图片
  python3 batch_download_radar.py --count 50

  # 强制重新下载100张（覆盖已存在的）
  python3 batch_download_radar.py --count 100 --force

  # 下载最近20张图片
  python3 batch_download_radar.py --count 20
        '''
    )

    parser.add_argument(
        '--count',
        type=int,
        default=50,
        help='下载数量（默认: 50）'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='强制重新下载（覆盖已存在的文件）'
    )

    args = parser.parse_args()

    try:
        batch_download(count=args.count, force=args.force)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断下载")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 下载失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
