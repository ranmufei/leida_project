"""
站点管理API端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.site import Site
from app.schemas.site import SiteCreate, SiteUpdate, SiteInDB
from app.schemas.common import ApiResponse, PaginatedResponse

router = APIRouter()


@router.get("/", response_model=ApiResponse[PaginatedResponse[SiteInDB]])
async def get_sites(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="站点名称(模糊搜索)"),
    region: Optional[str] = Query(None, description="区域"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    db: Session = Depends(get_db)
):
    """
    获取站点列表

    支持分页、搜索和筛选
    """
    # 构建查询
    query = db.query(Site).filter(Site.deleted_at.is_(None))

    # 添加筛选条件
    if name:
        query = query.filter(Site.name.like(f"%{name}%"))
    if region:
        query = query.filter(Site.region == region)
    if is_active is not None:
        query = query.filter(Site.is_active == is_active)

    # 计算总数
    total = query.count()

    # 分页查询
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    # 计算总页数
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


@router.get("/{site_id}", response_model=ApiResponse[SiteInDB])
async def get_site(
    site_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个站点详情
    """
    site = db.query(Site).filter(
        Site.id == site_id,
        Site.deleted_at.is_(None)
    ).first()

    if not site:
        raise HTTPException(status_code=404, detail="站点不存在")

    return ApiResponse(
        code=200,
        message="success",
        data=site
    )


@router.post("/", response_model=ApiResponse[SiteInDB])
async def create_site(
    site_data: SiteCreate,
    db: Session = Depends(get_db)
):
    """
    创建新站点
    """
    # 检查编码是否已存在
    existing_site = db.query(Site).filter(Site.code == site_data.code).first()
    if existing_site:
        raise HTTPException(status_code=400, detail="站点编码已存在")

    # 创建站点
    new_site = Site(**site_data.dict())
    db.add(new_site)
    db.commit()
    db.refresh(new_site)

    return ApiResponse(
        code=201,
        message="站点创建成功",
        data=new_site
    )


@router.put("/{site_id}", response_model=ApiResponse[SiteInDB])
async def update_site(
    site_id: int,
    site_data: SiteUpdate,
    db: Session = Depends(get_db)
):
    """
    更新站点信息
    """
    site = db.query(Site).filter(
        Site.id == site_id,
        Site.deleted_at.is_(None)
    ).first()

    if not site:
        raise HTTPException(status_code=404, detail="站点不存在")

    # 更新站点信息
    update_data = site_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(site, field, value)

    db.commit()
    db.refresh(site)

    return ApiResponse(
        code=200,
        message="站点更新成功",
        data=site
    )


@router.delete("/{site_id}", response_model=ApiResponse)
async def delete_site(
    site_id: int,
    db: Session = Depends(get_db)
):
    """
    删除站点(软删除)
    """
    site = db.query(Site).filter(
        Site.id == site_id,
        Site.deleted_at.is_(None)
    ).first()

    if not site:
        raise HTTPException(status_code=404, detail="站点不存在")

    # 软删除
    from datetime import datetime
    site.deleted_at = datetime.now()
    db.commit()

    return ApiResponse(
        code=200,
        message="站点删除成功",
        data=None
    )
