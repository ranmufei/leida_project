"""
数据查询API端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.radar_data import SiteRadarData
from app.models.site import Site
from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("/query", response_model=ApiResponse)
async def query_radar_data(
    site_id: Optional[int] = Query(None, description="站点ID"),
    start_time: Optional[str] = Query(None, description="开始时间 (YYYY-MM-DD HH:MM:SS)"),
    end_time: Optional[str] = Query(None, description="结束时间 (YYYY-MM-DD HH:MM:SS)"),
    min_dbz: Optional[float] = Query(None, description="最小dBZ值"),
    max_dbz: Optional[float] = Query(None, description="最大dBZ值"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    查询雷达数据

    支持按站点、时间范围、dBZ值范围查询
    """
    query = db.query(SiteRadarData)

    # 按站点筛选
    if site_id:
        query = query.filter(SiteRadarData.site_id == site_id)

    # 按时间范围筛选
    if start_time:
        try:
            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            query = query.filter(SiteRadarData.observation_time >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="开始时间格式错误，请使用格式: YYYY-MM-DD HH:MM:SS")

    if end_time:
        try:
            end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            query = query.filter(SiteRadarData.observation_time <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="结束时间格式错误，请使用格式: YYYY-MM-DD HH:MM:SS")

    # 按dBZ值筛选
    if min_dbz is not None:
        query = query.filter(SiteRadarData.dbz_value >= min_dbz)

    if max_dbz is not None:
        query = query.filter(SiteRadarData.dbz_value <= max_dbz)

    # 计算总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    data_list = query.order_by(SiteRadarData.observation_time.desc()).offset(offset).limit(page_size).all()

    # 转换为字典，同时获取站点信息
    items = []
    for data in data_list:
        # 获取站点信息
        site = db.query(Site).filter(Site.id == data.site_id).first()

        items.append({
            "id": data.id,
            "site_id": data.site_id,
            "observation_time": data.observation_time.isoformat() if data.observation_time else None,
            "dbz_value": float(data.dbz_value) if data.dbz_value else None,
            "dbz_category": data.dbz_category,
            "rgb_value": data.rgb_value,
            "pixel_x": data.pixel_x,
            "pixel_y": data.pixel_y,
            "cloud_impact_factor": float(data.cloud_impact_factor) if data.cloud_impact_factor else None,
            "data_quality": data.data_quality,
            "data_source": data.data_source,
            "created_at": data.created_at.isoformat() if data.created_at else None,
            "longitude": float(site.longitude) if site else None,
            "latitude": float(site.latitude) if site else None
        })

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return ApiResponse(
        code=200,
        message="success",
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    )


@router.get("/statistics", response_model=ApiResponse)
async def get_data_statistics(
    site_id: Optional[int] = Query(None, description="站点ID"),
    days: int = Query(7, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db)
):
    """
    获取数据统计信息

    返回指定站点在指定天数内的统计数据
    """
    # 计算时间范围
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)

    query = db.query(SiteRadarData).filter(
        SiteRadarData.observation_time >= start_time,
        SiteRadarData.observation_time <= end_time
    )

    # 按站点筛选
    if site_id:
        query = query.filter(SiteRadarData.site_id == site_id)

    # 获取所有数据
    data_list = query.all()

    if not data_list:
        return ApiResponse(
            code=200,
            message="暂无数据",
            data={
                "total_records": 0,
                "site_id": site_id,
                "days": days,
                "statistics": {}
            }
        )

    # 计算统计信息
    dbz_values = [d.dbz_value for d in data_list if d.dbz_value is not None]

    # dBZ分类统计
    category_counts = {}
    for data in data_list:
        if data.dbz_category:
            category_counts[data.dbz_category] = category_counts.get(data.dbz_category, 0) + 1

    # 计算平均值
    avg_dbz = sum(dbz_values) / len(dbz_values) if dbz_values else 0
    max_dbz = max(dbz_values) if dbz_values else 0
    min_dbz = min(dbz_values) if dbz_values else 0

    # 按站点统计
    site_stats = {}
    for data in data_list:
        sid = data.site_id
        if sid not in site_stats:
            site_stats[sid] = {"count": 0, "avg_dbz": 0, "dbz_values": []}
        site_stats[sid]["count"] += 1
        if data.dbz_value is not None:
            site_stats[sid]["dbz_values"].append(data.dbz_value)

    # 计算每个站点的平均值
    for sid in site_stats:
        values = site_stats[sid]["dbz_values"]
        site_stats[sid]["avg_dbz"] = sum(values) / len(values) if values else 0
        del site_stats[sid]["dbz_values"]

    return ApiResponse(
        code=200,
        message="success",
        data={
            "total_records": len(data_list),
            "site_id": site_id,
            "days": days,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "statistics": {
                "avg_dbz": round(avg_dbz, 2),
                "max_dbz": round(max_dbz, 2),
                "min_dbz": round(min_dbz, 2),
                "category_distribution": category_counts,
                "by_site": site_stats
            }
        }
    )
