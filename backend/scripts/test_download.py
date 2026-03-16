"""
测试下载功能
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.download_service import RadarImageDownloader
from datetime import datetime, timedelta


def test_latest_download():
    """测试下载最新图片"""
    print("=" * 60)
    print("测试1: 下载最新图片")
    print("=" * 60)

    downloader = RadarImageDownloader()

    # 下载最新的1张图片
    stats = downloader.download_latest(count=1)

    print(f"\n下载统计:")
    print(f"  总计: {stats['total']}")
    print(f"  成功: {stats['success']}")
    print(f"  跳过: {stats['skipped']}")
    print(f"  失败: {stats['failed']}")


def test_range_download():
    """测试批量下载"""
    print("\n" + "=" * 60)
    print("测试2: 批量下载指定时间范围")
    print("=" * 60)

    downloader = RadarImageDownloader()

    # 下载最近1小时的数据（10张图片）
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=1)

    stats = downloader.download_range(start_time, end_time, interval_minutes=6)

    print(f"\n下载统计:")
    print(f"  总计: {stats['total']}")
    print(f"  成功: {stats['success']}")
    print(f"  跳过: {stats['skipped']}")
    print(f"  失败: {stats['failed']}")


def test_statistics():
    """测试统计功能"""
    print("\n" + "=" * 60)
    print("测试3: 获取下载统计")
    print("=" * 60)

    downloader = RadarImageDownloader()
    stats = downloader.get_download_statistics()

    print(f"\n统计信息:")
    print(f"  总记录数: {stats['total']}")
    print(f"  成功: {stats['success']}")
    print(f"  失败: {stats['failed']}")
    print(f"  待处理: {stats['pending']}")
    print(f"  成功率: {stats['success_rate']:.2%}")
    print(f"  最新下载时间: {stats['latest_download_time']}")


def test_url_building():
    """测试URL构建"""
    print("\n" + "=" * 60)
    print("测试4: URL构建")
    print("=" * 60)

    downloader = RadarImageDownloader()
    test_time = datetime(2024, 3, 10, 16, 0, 0)

    url = downloader.build_download_url(test_time)
    filename = downloader.build_filename(test_time)

    print(f"\n测试时间: {test_time}")
    print(f"下载URL: {url}")
    print(f"文件名: {filename}")


def test_cleanup():
    """测试清理功能"""
    print("\n" + "=" * 60)
    print("测试5: 清理失败记录")
    print("=" * 60)

    downloader = RadarImageDownloader()
    downloader.cleanup_failed_downloads(max_age_hours=24)


if __name__ == "__main__":
    print("🧪 雷达图片下载功能测试")
    print("=" * 60)

    try:
        # 运行测试
        test_url_building()
        test_latest_download()
        test_range_download()
        test_statistics()
        test_cleanup()

        print("\n" + "=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
