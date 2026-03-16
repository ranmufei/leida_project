"""
Celery下载任务
"""
from celery import shared_task
from datetime import datetime, timedelta
from typing import Dict

from app.services.download_service import RadarImageDownloader


@shared_task(name="tasks.download_latest_image")
def download_latest_image():
    """
    下载最新的雷达图片

    每6分钟执行一次
    """
    print(f"\n{'='*60}")
    print(f"⏰ 定时任务触发: {datetime.now()}")
    print(f"{'='*60}")

    downloader = RadarImageDownloader()
    stats = downloader.download_latest(count=1)

    return {
        'task': 'download_latest_image',
        'timestamp': datetime.now().isoformat(),
        'statistics': stats
    }


@shared_task(name="tasks.download_range")
def download_range_images(
    start_time: str,
    end_time: str,
    interval_minutes: int = 6,
    force: bool = False
):
    """
    下载指定时间范围的图片

    Args:
        start_time: 开始时间 (ISO格式)
        end_time: 结束时间 (ISO格式)
        interval_minutes: 时间间隔
        force: 是否强制重新下载
    """
    start = datetime.fromisoformat(start_time)
    end = datetime.fromisoformat(end_time)

    downloader = RadarImageDownloader()
    stats = downloader.download_range(start, end, interval_minutes, force)

    return {
        'task': 'download_range_images',
        'timestamp': datetime.now().isoformat(),
        'start_time': start_time,
        'end_time': end_time,
        'statistics': stats
    }


@shared_task(name="tasks.cleanup_old_records")
def cleanup_old_records(max_age_hours: int = 24):
    """
    清理旧的失败记录

    Args:
        max_age_hours: 最大保留时间（小时）
    """
    downloader = RadarImageDownloader()
    downloader.cleanup_failed_downloads(max_age_hours)

    return {
        'task': 'cleanup_old_records',
        'timestamp': datetime.now().isoformat(),
        'max_age_hours': max_age_hours
    }


@shared_task(name="tasks.download_history")
def download_history_data(days: int = 7):
    """
    下载历史数据

    Args:
        days: 天数
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)

    downloader = RadarImageDownloader()
    stats = downloader.download_range(start_time, end_time, force=False)

    return {
        'task': 'download_history_data',
        'timestamp': datetime.now().isoformat(),
        'days': days,
        'statistics': stats
    }


@shared_task(name="tasks.retry_failed_downloads")
def retry_failed_downloads(max_retry_count: int = 3):
    """
    重试失败的下载

    Args:
        max_retry_count: 最大重试次数
    """
    from app.core.database import SessionLocal
    from app.models.radar_image import RadarImage

    db = SessionLocal()
    try:
        # 查询失败的下载记录
        failed_downloads = db.query(RadarImage).filter(
            RadarImage.download_status == 'failed',
            RadarImage.retry_count < max_retry_count
        ).limit(100).all()

        print(f"🔄 找到 {len(failed_downloads)} 条失败记录，准备重试")

        downloader = RadarImageDownloader()
        retry_count = 0
        success_count = 0

        for record in failed_downloads:
            retry_count += 1
            success, message, _ = downloader.download_image(
                record.observation_time,
                force=True
            )

            if success:
                success_count += 1

        db.close()

        return {
            'task': 'retry_failed_downloads',
            'timestamp': datetime.now().isoformat(),
            'total': len(failed_downloads),
            'retry_count': retry_count,
            'success_count': success_count
        }

    except Exception as e:
        print(f"❌ 重试任务失败: {e}")
        return {
            'task': 'retry_failed_downloads',
            'error': str(e)
        }
