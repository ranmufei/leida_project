"""
图片管理API端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from pathlib import Path
import os

from app.core.database import get_db
from app.models.radar_image import RadarImage
from app.schemas.common import ApiResponse
from app.schemas.radar_image import RadarImageSchema, RadarImageListSchema

router = APIRouter()


@router.get("/list", response_model=ApiResponse)
async def list_images(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=500, description="每页数量"),
    sort_by: Optional[str] = Query("observation_time", description="排序字段: observation_time, download_time, file_size"),
    sort_order: Optional[str] = Query("desc", description="排序方向: asc, desc"),
    status: Optional[str] = Query(None, description="下载状态筛选"),
    db: Session = Depends(get_db)
):
    """
    获取图片列表（支持排序和筛选）
    """
    query = db.query(RadarImage)

    # 状态筛选
    if status:
        query = query.filter(RadarImage.download_status == status)

    # 排序
    sort_column = getattr(RadarImage, sort_by, RadarImage.observation_time)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # 分页
    total = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    total_pages = (total + page_size - 1) // page_size

    # 转换为Schema
    items_schema = [RadarImageSchema.model_validate(item) for item in items]

    return ApiResponse(
        code=200,
        message="success",
        data=RadarImageListSchema(
            items=items_schema,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )


@router.get("/{image_id}", response_model=ApiResponse)
async def get_image_detail(
    image_id: int,
    db: Session = Depends(get_db)
):
    """
    获取图片详细信息
    """
    image = db.query(RadarImage).filter(RadarImage.id == image_id).first()

    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    return ApiResponse(
        code=200,
        message="success",
        data=image
    )


@router.get("/{image_id}/preview", response_class=FileResponse)
async def preview_image(
    image_id: int,
    db: Session = Depends(get_db)
):
    """
    预览图片（返回图片文件）
    """
    image = db.query(RadarImage).filter(RadarImage.id == image_id).first()

    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    if not image.download_status == 'success':
        raise HTTPException(status_code=400, detail="图片下载未成功")

    file_path = Path(image.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="图片文件不存在")

    return FileResponse(
        path=str(file_path),
        media_type="image/png",
        filename=image.original_filename
    )


@router.get("/stats/summary", response_model=ApiResponse)
async def get_image_statistics(
    db: Session = Depends(get_db)
):
    """
    获取图片统计信息
    """
    total = db.query(RadarImage).count()
    success = db.query(RadarImage).filter(RadarImage.download_status == 'success').count()
    failed = db.query(RadarImage).filter(RadarImage.download_status == 'failed').count()
    pending = db.query(RadarImage).filter(RadarImage.download_status == 'pending').count()

    # 计算总文件大小
    total_size = db.query(RadarImage).filter(
        RadarImage.download_status == 'success'
    ).all()
    size_bytes = sum([img.file_size or 0 for img in total_size])

    # 获取最新和最早的图片时间
    latest = db.query(RadarImage).filter(
        RadarImage.download_status == 'success'
    ).order_by(RadarImage.observation_time.desc()).first()

    earliest = db.query(RadarImage).filter(
        RadarImage.download_status == 'success'
    ).order_by(RadarImage.observation_time.asc()).first()

    return ApiResponse(
        code=200,
        message="success",
        data={
            "total_images": total,
            "success_count": success,
            "failed_count": failed,
            "pending_count": pending,
            "success_rate": success / total if total > 0 else 0,
            "total_size_bytes": size_bytes,
            "total_size_mb": round(size_bytes / (1024 * 1024), 2),
            "latest_observation_time": latest.observation_time if latest else None,
            "earliest_observation_time": earliest.observation_time if earliest else None
        }
    )


@router.delete("/{image_id}", response_model=ApiResponse)
async def delete_image(
    image_id: int,
    db: Session = Depends(get_db)
):
    """
    删除图片记录和文件
    """
    image = db.query(RadarImage).filter(RadarImage.id == image_id).first()

    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    # 删除文件
    file_path = Path(image.file_path)
    if file_path.exists():
        try:
            os.remove(file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")

    # 删除数据库记录
    db.delete(image)
    db.commit()

    return ApiResponse(
        code=200,
        message="删除成功",
        data={"deleted_id": image_id}
    )
