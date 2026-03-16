"""
预测API端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.services.prediction_service import PredictionService
from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("/methods", response_model=ApiResponse)
async def get_prediction_methods():
    """
    获取可用的预测方法
    """
    from app.services.prophet_service import PROPHET_AVAILABLE

    methods = [
        {
            'method': 'optical_flow',
            'name': '光流法',
            'description': '基于云团运动轨迹的外推预测',
            'enabled': True,
            'requirements': '需要连续的雷达图片序列'
        },
        {
            'method': 'prophet',
            'name': 'Prophet时序模型',
            'description': '基于历史时序数据的统计预测',
            'enabled': PROPHET_AVAILABLE,
            'requirements': '需要至少7天(168个数据点)的历史数据'
        },
        {
            'method': 'ensemble',
            'name': '集成预测',
            'description': '光流法和Prophet的加权组合',
            'enabled': PROPHET_AVAILABLE,
            'requirements': '需要图片序列和历史数据'
        }
    ]

    return ApiResponse(
        code=200,
        message="success",
        data={'methods': methods}
    )


@router.get("/site/{site_id}/latest", response_model=ApiResponse)
async def get_latest_prediction(
    site_id: int,
    db: Session = Depends(get_db)
):
    """
    获取站点的最新预测数据

    Args:
        site_id: 站点ID

    Returns:
        最新预测结果
    """
    from app.models.prediction import SitePrediction

    # 查询最新的预测数据
    latest_prediction = db.query(SitePrediction).filter(
        SitePrediction.site_id == site_id,
        SitePrediction.prediction_time >= datetime.now()
    ).order_by(SitePrediction.prediction_time.asc()).limit(60).all()

    predictions = []
    for pred in latest_prediction:
        predictions.append({
            'id': pred.id,
            'prediction_time': pred.prediction_time,
            'predicted_dbz': float(pred.predicted_dbz),
            'confidence_lower': float(pred.confidence_lower) if pred.confidence_lower else None,
            'confidence_upper': float(pred.confidence_upper) if pred.confidence_upper else None,
            'model_type': pred.model_type,
            'model_version': pred.model_version,
            'prediction_horizon': pred.prediction_horizon,
            'prediction_accuracy': float(pred.prediction_accuracy) if pred.prediction_accuracy else None
        })

    return ApiResponse(
        code=200,
        message="success",
        data={
            'site_id': site_id,
            'predictions': predictions
        }
    )


@router.post("/site/{site_id}/predict", response_model=ApiResponse)
async def create_prediction_task(
    site_id: int,
    background_tasks: BackgroundTasks,
    model_type: str = Query('prophet', description="预测模型类型"),
    prediction_horizon: int = Query(360, ge=60, le=720, description="预测时长(分钟)"),
    db: Session = Depends(get_db)
):
    """
    创建预测任务

    Args:
        site_id: 站点ID
        model_type: 模型类型 ('optical_flow', 'prophet', 'ensemble')
        prediction_horizon: 预测时长

    Returns:
        任务创建确认
    """
    from app.tasks.prediction_tasks import run_prediction_task

    # 验证站点是否存在
    from app.models.site import Site
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="站点不存在")

    # 添加后台任务
    background_tasks.add_task(
        run_prediction_task(
            site_id=site_id,
            model_type=model_type,
            prediction_horizon=prediction_horizon
        )
    )

    return ApiResponse(
        code=202,
        message="预测任务已创建",
        data={
            'task_type': 'prediction',
            'site_id': site_id,
            'model_type': model_type,
            'prediction_horizon': prediction_horizon
        }
    )


@router.get("/site/{site_id}/history", response_model=ApiResponse)
async def get_prediction_history(
    site_id: int,
    start_time: Optional[str] = Query(None, description="开始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
    model_type: Optional[str] = Query(None, description="模型类型筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    获取站点的预测历史记录

    Args:
        site_id: 站点ID
        start_time: 开始时间
        end_time: 结束时间
        model_type: 模型类型
        page: 页码
        page_size: 每页数量

    Returns:
        预测历史记录
    """
    from app.models.prediction import SitePrediction
    from datetime import datetime

    query = db.query(SitePrediction).filter(SitePrediction.site_id == site_id)

    # 时间筛选
    if start_time:
        query = query.filter(SitePrediction.prediction_time >= datetime.fromisoformat(start_time))
    if end_time:
        query = query.filter(SitePrediction.prediction_time <= datetime.fromisoformat(end_time))

    # 模型类型筛选
    if model_type:
        query = query.filter(SitePrediction.model_type == model_type)

    # 排序和分页
    query = query.order_by(SitePrediction.prediction_time.desc())
    total = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    predictions = []
    for pred in items:
        predictions.append({
            'id': pred.id,
            'prediction_time': pred.prediction_time,
            'predicted_dbz': float(pred.predicted_dbz),
            'confidence_lower': float(pred.confidence_lower) if pred.confidence_lower else None,
            'confidence_upper': float(pred.confidence_upper) if pred.confidence_upper else None,
            'model_type': pred.model_type,
            'model_version': pred.model_version,
            'prediction_horizon': pred.prediction_horizon,
            'prediction_accuracy': float(pred.prediction_accuracy) if pred.prediction_accuracy else None,
            'created_at': pred.created_at
        })

    return ApiResponse(
        code=200,
        message="success",
        data={
            'site_id': site_id,
            'total': total,
            'page': page,
            'page_size': page_size,
            'predictions': predictions
        }
    )
