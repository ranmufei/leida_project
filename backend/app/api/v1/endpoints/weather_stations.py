"""
气象站点管理API端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.weather_station import WeatherStation
from app.schemas.weather_station import WeatherStationCreate, WeatherStationUpdate, WeatherStationInDB
from app.schemas.common import ApiResponse, PaginatedResponse

router = APIRouter()


@router.get("/", response_model=ApiResponse[PaginatedResponse[WeatherStationInDB]])
async def get_weather_stations(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    station_name: Optional[str] = Query(None, description="站点名称(模糊搜索)"),
    region: Optional[str] = Query(None, description="区域"),
    status: Optional[str] = Query(None, description="状态"),
    db: Session = Depends(get_db)
):
    """
    获取气象站点列表

    支持分页、搜索和筛选
    """
    # 构建查询
    query = db.query(WeatherStation)

    # 添加筛选条件
    if station_name:
        query = query.filter(WeatherStation.station_name.like(f"%{station_name}%"))
    if region:
        query = query.filter(WeatherStation.region == region)
    if status:
        query = query.filter(WeatherStation.status == status)

    # 计算总数
    total = query.count()

    # 分页查询
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    # 计算总页数
    total_pages = (total + page_size - 1) // page_size

    return ApiResponse(
        code=0,
        message="success",
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )


@router.get("/{station_id}", response_model=ApiResponse[WeatherStationInDB])
async def get_weather_station(
    station_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个气象站点详情
    """
    station = db.query(WeatherStation).filter(
        WeatherStation.id == station_id
    ).first()

    if not station:
        raise HTTPException(status_code=404, detail="站点不存在")

    return ApiResponse(
        code=0,
        message="success",
        data=station
    )


@router.post("/", response_model=ApiResponse[WeatherStationInDB])
async def create_weather_station(
    station_data: WeatherStationCreate,
    db: Session = Depends(get_db)
):
    """
    创建新气象站点
    """
    # 检查站点编码是否已存在
    existing_station = db.query(WeatherStation).filter(
        WeatherStation.station_id == station_data.station_id
    ).first()
    if existing_station:
        raise HTTPException(status_code=400, detail="站点编码已存在")

    # 创建站点
    new_station = WeatherStation(**station_data.model_dump())
    db.add(new_station)
    db.commit()
    db.refresh(new_station)

    return ApiResponse(
        code=0,
        message="站点创建成功",
        data=new_station
    )


@router.put("/{station_id}", response_model=ApiResponse[WeatherStationInDB])
async def update_weather_station(
    station_id: int,
    station_data: WeatherStationUpdate,
    db: Session = Depends(get_db)
):
    """
    更新气象站点信息
    """
    station = db.query(WeatherStation).filter(
        WeatherStation.id == station_id
    ).first()

    if not station:
        raise HTTPException(status_code=404, detail="站点不存在")

    # 更新站点信息
    update_data = station_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(station, field, value)

    db.commit()
    db.refresh(station)

    return ApiResponse(
        code=0,
        message="站点更新成功",
        data=station
    )


@router.delete("/{station_id}", response_model=ApiResponse)
async def delete_weather_station(
    station_id: int,
    db: Session = Depends(get_db)
):
    """
    删除气象站点
    """
    station = db.query(WeatherStation).filter(
        WeatherStation.id == station_id
    ).first()

    if not station:
        raise HTTPException(status_code=404, detail="站点不存在")

    # 删除站点
    db.delete(station)
    db.commit()

    return ApiResponse(
        code=0,
        message="站点删除成功",
        data=None
    )
