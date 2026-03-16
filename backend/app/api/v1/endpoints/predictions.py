"""
预测API端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.site import Site
from app.models.prediction import SitePrediction
from app.schemas.common import ApiResponse

router = APIRouter()


# 支持的预测方法
PREDICTION_METHODS = {
    "prophet": {
        "name": "Prophet时间序列预测",
        "description": "基于Facebook Prophet的时间序列预测算法，适合长期趋势预测",
        "parameters": {
            "hours": {"type": "integer", "default": 24, "min": 1, "max": 168, "description": "预测小时数"}
        }
    },
    "optical_flow": {
        "name": "光流法预测",
        "description": "基于OpenCV Farneback光流算法，通过云层移动轨迹进行短期预测",
        "parameters": {
            "hours": {"type": "integer", "default": 6, "min": 1, "max": 24, "description": "预测小时数"}
        }
    },
    "ensemble": {
        "name": "集成预测",
        "description": "组合多种预测方法，提高预测准确度",
        "parameters": {
            "hours": {"type": "integer", "default": 24, "min": 1, "max": 168, "description": "预测小时数"}
        }
    }
}


@router.get("/methods", response_model=ApiResponse)
async def get_prediction_methods():
    """
    获取支持的预测方法列表

    返回所有可用的预测算法及其参数说明
    """
    methods = []
    for method_id, method_info in PREDICTION_METHODS.items():
        methods.append({
            "id": method_id,
            "name": method_info["name"],
            "description": method_info["description"],
            "parameters": method_info["parameters"]
        })

    return ApiResponse(
        code=200,
        message="success",
        data={
            "methods": methods,
            "total": len(methods)
        }
    )


@router.post("/predict", response_model=ApiResponse)
async def create_prediction(
    site_id: int,
    model_type: str = "prophet",
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """
    创建预测任务

    为指定站点创建预测任务，使用指定的预测方法
    """
    # 验证站点是否存在
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail=f"站点 {site_id} 不存在")

    # 验证预测方法（映射到model_type）
    method_mapping = {
        "prophet": "prophet",
        "optical_flow": "optical_flow",
        "ensemble": "ensemble"
    }

    if model_type not in method_mapping:
        available = ", ".join(method_mapping.keys())
        raise HTTPException(
            status_code=400,
            detail=f"不支持的预测方法: {model_type}。可用方法: {available}"
        )

    # 验证参数
    if hours < 1 or hours > 168:
        raise HTTPException(
            status_code=400,
            detail=f"预测小时数必须在 1 到 168 之间"
        )

    # 检查是否已有最近的预测
    existing_prediction = db.query(SitePrediction).filter(
        SitePrediction.site_id == site_id,
        SitePrediction.model_type == model_type,
        SitePrediction.created_at >= datetime.now() - timedelta(hours=6)
    ).first()

    if existing_prediction:
        return ApiResponse(
            code=200,
            message="已存在最近的预测结果",
            data={
                "prediction_id": existing_prediction.id,
                "site_id": existing_prediction.site_id,
                "model_type": existing_prediction.model_type,
                "prediction_time": existing_prediction.prediction_time.isoformat() if existing_prediction.prediction_time else None,
                "created_at": existing_prediction.created_at.isoformat() if existing_prediction.created_at else None,
                "is_cached": True
            }
        )

    # 创建新的预测记录（模拟）
    try:
        # 这里应该调用实际的预测服务
        # 为了演示，我们创建一个模拟预测结果

        prediction_time = datetime.now() + timedelta(hours=1)

        new_prediction = SitePrediction(
            site_id=site_id,
            prediction_time=prediction_time,
            predicted_dbz=30.5,  # 模拟预测值
            confidence_lower=25.0,  # 模拟置信区间
            confidence_upper=35.0,
            model_type=model_type,
            model_version="1.0.0",
            prediction_horizon=hours * 60,  # 转换为分钟
            prediction_accuracy=0.85  # 模拟准确度
        )

        db.add(new_prediction)
        db.commit()
        db.refresh(new_prediction)

        return ApiResponse(
            code=201,
            message="预测任务创建成功",
            data={
                "prediction_id": new_prediction.id,
                "site_id": new_prediction.site_id,
                "model_type": new_prediction.model_type,
                "prediction_time": new_prediction.prediction_time.isoformat() if new_prediction.prediction_time else None,
                "predicted_dbz": float(new_prediction.predicted_dbz) if new_prediction.predicted_dbz else None,
                "confidence_lower": float(new_prediction.confidence_lower) if new_prediction.confidence_lower else None,
                "confidence_upper": float(new_prediction.confidence_upper) if new_prediction.confidence_upper else None,
                "prediction_horizon": new_prediction.prediction_horizon,
                "prediction_accuracy": float(new_prediction.prediction_accuracy) if new_prediction.prediction_accuracy else None,
                "created_at": new_prediction.created_at.isoformat() if new_prediction.created_at else None,
                "is_cached": False
            }
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建预测失败: {str(e)}")


@router.get("/site/{site_id}/latest", response_model=ApiResponse)
async def get_latest_prediction(
    site_id: int,
    model_type: str = None,
    db: Session = Depends(get_db)
):
    """
    获取站点的最新预测结果

    返回指定站点的最新预测数据
    """
    # 验证站点是否存在
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail=f"站点 {site_id} 不存在")

    # 构建查询
    query = db.query(SitePrediction).filter(SitePrediction.site_id == site_id)

    if model_type:
        query = query.filter(SitePrediction.model_type == model_type)

    # 获取最新的预测
    prediction = query.order_by(SitePrediction.created_at.desc()).first()

    if not prediction:
        return ApiResponse(
            code=404,
            message="未找到预测结果",
            data={
                "site_id": site_id,
                "model_type": model_type,
                "message": "该站点暂无预测数据，请先创建预测任务"
            }
        )

    return ApiResponse(
        code=200,
        message="success",
        data={
            "prediction_id": prediction.id,
            "site_id": prediction.site_id,
            "model_type": prediction.model_type,
            "prediction_time": prediction.prediction_time.isoformat() if prediction.prediction_time else None,
            "predicted_dbz": float(prediction.predicted_dbz) if prediction.predicted_dbz else None,
            "confidence_lower": float(prediction.confidence_lower) if prediction.confidence_lower else None,
            "confidence_upper": float(prediction.confidence_upper) if prediction.confidence_upper else None,
            "model_version": prediction.model_version,
            "prediction_horizon": prediction.prediction_horizon,
            "prediction_accuracy": float(prediction.prediction_accuracy) if prediction.prediction_accuracy else None,
            "created_at": prediction.created_at.isoformat() if prediction.created_at else None
        }
    )
