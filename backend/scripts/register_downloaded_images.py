#!/usr/bin/env python3
"""
将已下载的雷达图片注册到数据库

如果图片文件已存在但数据库中没有记录，使用此脚本注册
"""
import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.radar_image import RadarImage


def register_downloaded_images():
    """扫描下载目录并将未注册的图片添加到数据库"""
    print("=" * 80)
    print("📝 注册已下载的雷达图片到数据库")
    print("=" * 80)

    # 获取数据目录
    from app.core.config import settings
    raw_dir = Path(settings.RAW_DATA_DIR)

    if not raw_dir.exists():
        print(f"❌ 数据目录不存在: {raw_dir}")
        return

    print(f"\n📁 扫描目录: {raw_dir}")

    # 查找所有 radar_*.png 文件
    image_files = list(raw_dir.glob("radar_*.png"))
    print(f"📊 找到 {len(image_files)} 个图片文件")

    db = SessionLocal()

    try:
        registered = 0
        skipped = 0
        errors = 0

        for image_file in image_files:
            try:
                # 从文件名解析时间: radar_YYYYMMDD_HHMMSS.png
                filename = image_file.name
                time_part = filename.replace("radar_", "").replace(".png", "")

                # 解析时间: YYYYMMDD_HHMMSS -> YYYY-MM-DD HH:MM:SS
                try:
                    observation_time = datetime.strptime(time_part, "%Y%m%d_%H%M%S")
                except ValueError:
                    print(f"   ⚠️  无法解析文件名: {filename}")
                    errors += 1
                    continue

                # 检查数据库中是否已存在
                existing = db.query(RadarImage).filter(
                    RadarImage.observation_time == observation_time
                ).first()

                if existing:
                    skipped += 1
                    continue

                # 创建新记录
                radar_image = RadarImage(
                    filename=filename,
                    file_path=str(image_file),
                    observation_time=observation_time,
                    download_time=datetime.fromtimestamp(image_file.stat().st_mtime),
                    download_status='success'
                )

                db.add(radar_image)
                registered += 1

                if registered <= 10:  # 只显示前10个
                    print(f"   ✅ 注册: {filename} -> {observation_time}")

            except Exception as e:
                print(f"   ❌ 处理失败 {image_file.name}: {e}")
                errors += 1

        # 提交更改
        db.commit()

        print("\n" + "=" * 80)
        print("📊 注册完成统计")
        print("=" * 80)
        print(f"  扫描文件: {len(image_files)} 个")
        print(f"  ✅ 新注册: {registered} 个")
        print(f"  ⏭️  已存在: {skipped} 个")
        print(f"  ❌ 错误: {errors} 个")
        print("=" * 80)

        # 数据库统计
        total_records = db.query(RadarImage).count()
        success_records = db.query(RadarImage).filter(
            RadarImage.download_status == 'success'
        ).count()

        print(f"\n📈 数据库总记录: {total_records} 条")
        print(f"📈 成功下载记录: {success_records} 条")

    except Exception as e:
        db.rollback()
        print(f"\n❌ 注册失败: {e}")
        raise
    finally:
        db.close()


def show_database_status():
    """显示数据库状态"""
    print("\n" + "=" * 80)
    print("📊 数据库状态")
    print("=" * 80)

    db = SessionLocal()
    try:
        total = db.query(RadarImage).count()
        success = db.query(RadarImage).filter(
            RadarImage.download_status == 'success'
        ).count()
        failed = db.query(RadarImage).filter(
            RadarImage.download_status == 'failed'
        ).count()
        pending = db.query(RadarImage).filter(
            RadarImage.download_status == 'pending'
        ).count()

        print(f"  总记录: {total}")
        print(f"  成功: {success}")
        print(f"  失败: {failed}")
        print(f"  等待: {pending}")

        # 显示最新的5条记录
        latest = db.query(RadarImage).order_by(
            RadarImage.observation_time.desc()
        ).limit(5).all()

        print(f"\n📅 最新的5条记录:")
        for img in latest:
            status_icon = {
                'success': '✅',
                'failed': '❌',
                'pending': '⏳'
            }.get(img.download_status, '❓')

            print(f"  {status_icon} {img.observation_time} - {img.download_status} - {img.filename}")

    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='将已下载的雷达图片注册到数据库'
    )
    parser.add_argument('--status', '-s', action='store_true',
                       help='只显示数据库状态，不注册新图片')

    args = parser.parse_args()

    if args.status:
        show_database_status()
    else:
        register_downloaded_images()
        show_database_status()
