"""
下载管理API端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.radar_image import RadarImage
from app.schemas.common import ApiResponse, PaginatedResponse
from app.tasks.download_tasks import (
    download_latest_image,
    download_range_images,
    cleanup_old_records,
    retry_failed_downloads,
    download_history_data
)

router = APIRouter()


@router.get("/status", response_model=ApiResponse)
async def get_download_status(db: Session = Depends(get_db)):
    """
    获取下载状态
    """
    # 使用真实CMA API的下载服务
    from app.services.download_service_real import RealRadarImageDownloader

    downloader = RealRadarImageDownloader()
    stats = downloader.get_download_statistics()

    # 获取下次下载时间
    latest_time = stats.get('latest_download_time')
    if latest_time:
        next_download = latest_time + timedelta(minutes=6)
    else:
        next_download = datetime.now()

    return ApiResponse(
        code=200,
        message="success",
        data={
            "download_statistics": stats,
            "next_download_time": next_download,
            "download_interval_minutes": 6
        }
    )


@router.get("/history", response_model=ApiResponse[PaginatedResponse])
async def get_download_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="下载状态筛选"),
    db: Session = Depends(get_db)
):
    """
    获取下载历史记录
    """
    query = db.query(RadarImage)

    if status:
        query = query.filter(RadarImage.download_status == status)

    # 按观测时间倒序
    query = query.order_by(RadarImage.observation_time.desc())

    total = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    total_pages = (total + page_size - 1) // page_size

    return ApiResponse(
        code=200,
        message="success",
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )


@router.post("/trigger", response_model=ApiResponse)
async def trigger_download(
    background_tasks: BackgroundTasks,
    count: int = Query(None, description="下载图片数量，不传则下载全部")
):
    """
    手动触发下载任务

    使用真实CMA API下载最新的N张雷达图片（count=None表示下载全部）
    自动去重：已下载的图片不会重复保存
    """
    from app.services.download_service_real import RealRadarImageDownloader

    # 直接同步执行下载（不使用后台任务，确保用户立即看到结果）
    downloader = RealRadarImageDownloader()

    # 如果count为None或0，下载全部
    download_count = count if count and count > 0 else None

    stats = downloader.download_latest_from_api(count=download_count, force=False)

    success_count = stats.get('success', 0)
    failed_count = stats.get('failed', 0)
    skipped_count = stats.get('skipped', 0)

    if failed_count == 0:
        message = f"成功下载 {success_count} 张图片" + (f"，跳过 {skipped_count} 张已存在" if skipped_count > 0 else "")
    elif success_count > 0:
        message = f"部分成功: 下载 {success_count} 张, 跳过 {skipped_count} 张, 失败 {failed_count} 张"
    else:
        message = f"下载失败: {failed_count} 张图片下载失败"

    return ApiResponse(
        code=200,
        message=message,
        data={
            "task_type": "download_latest",
            "count": download_count if download_count else "全部",
            "statistics": stats
        }
    )


@router.post("/retry", response_model=ApiResponse)
async def retry_failed(
    background_tasks: BackgroundTasks,
    max_retry_count: int = Query(3, ge=1, le=10, description="最大重试次数")
):
    """
    重试失败的下载
    """
    background_tasks.add_task(retry_failed_downloads, max_retry_count)

    return ApiResponse(
        code=202,
        message="重试任务已创建",
        data={
            "task_type": "retry_failed",
            "max_retry_count": max_retry_count
        }
    )


@router.post("/cleanup", response_model=ApiResponse)
async def cleanup_old_data(
    background_tasks: BackgroundTasks,
    max_age_hours: int = Query(24, ge=1, le=720, description="最大保留时间(小时)")
):
    """
    清理旧的失败记录
    """
    background_tasks.add_task(cleanup_old_records, max_age_hours)

    return ApiResponse(
        code=202,
        message=f"清理任务已创建，将删除 {max_age_hours} 小时前的失败记录",
        data={
            "task_type": "cleanup",
            "max_age_hours": max_age_hours
        }
    )


@router.post("/history-download", response_model=ApiResponse)
async def download_history(
    background_tasks: BackgroundTasks,
    days: int = Query(7, ge=1, le=30, description="下载天数")
):
    """
    下载历史数据

    下载指定天数的历史雷达图片
    """
    background_tasks.add_task(download_history_data, days)

    return ApiResponse(
        code=202,
        message=f"历史数据下载任务已创建，将下载最近 {days} 天的数据",
        data={
            "task_type": "download_history",
            "days": days
        }
    )
