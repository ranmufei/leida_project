"""
坐标校准API端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import numpy as np

from app.core.database import get_db
from app.models.calibration import ControlPoint, CalibrationParams


router = APIRouter(prefix="/calibration", tags=["校准"])


# ========== Pydantic 模型 ==========

class ControlPointCreate(BaseModel):
    """创建控制点请求"""
    pixel_x: int
    pixel_y: int
    longitude: float
    latitude: float
    name: str = None


class ControlPointResponse(BaseModel):
    """控制点响应"""
    id: int
    pixel_x: int
    pixel_y: int
    longitude: float
    latitude: float
    name: str = None
    created_at: str


class CalibrationRequest(BaseModel):
    """校准请求"""
    control_point_ids: List[int] = None  # 指定使用的控制点ID列表，为空则使用全部


class CalibrationResponse(BaseModel):
    """校准响应"""
    success: bool
    message: str
    affine_lon: List[float] = None  # [a0, a1, a2]
    affine_lat: List[float] = None  # [b0, b1, b2]
    errors: List[dict] = None  # 各控制点的误差信息


# ========== API 端点 ==========

@router.post("/control-points", response_model=dict)
async def add_control_point(
    data: ControlPointCreate,
    db: Session = Depends(get_db)
):
    """
    添加控制点

    Args:
        data: 控制点数据

    Returns:
        创建的控制点信息
    """
    # 打印接收到的控制点数据用于调试
    print(f"📌 收到控制点: {data.name}")
    print(f"   像素坐标: ({data.pixel_x}, {data.pixel_y})")
    print(f"   经纬度: ({data.longitude}, {data.latitude})")

    control_point = ControlPoint(
        pixel_x=data.pixel_x,
        pixel_y=data.pixel_y,
        longitude=data.longitude,
        latitude=data.latitude,
        name=data.name
    )

    db.add(control_point)
    db.commit()
    db.refresh(control_point)

    return {
        "code": 0,
        "message": "控制点添加成功",
        "data": control_point.to_dict()
    }


@router.get("/control-points", response_model=dict)
async def get_control_points(
    db: Session = Depends(get_db)
):
    """
    获取所有控制点

    Returns:
        控制点列表
    """
    control_points = db.query(ControlPoint).order_by(ControlPoint.created_at).all()

    return {
        "code": 0,
        "message": "获取成功",
        "data": {
            "items": [cp.to_dict() for cp in control_points],
            "total": len(control_points)
        }
    }


@router.delete("/control-points/{control_point_id}", response_model=dict)
async def delete_control_point(
    control_point_id: int,
    db: Session = Depends(get_db)
):
    """
    删除控制点

    Args:
        control_point_id: 控制点ID

    Returns:
        删除结果
    """
    control_point = db.query(ControlPoint).filter(ControlPoint.id == control_point_id).first()

    if not control_point:
        raise HTTPException(status_code=404, detail="控制点不存在")

    db.delete(control_point)
    db.commit()

    return {
        "code": 0,
        "message": "控制点已删除"
    }


@router.post("/calibrate", response_model=dict)
async def calibrate(
    data: CalibrationRequest,
    db: Session = Depends(get_db)
):
    """
    执行校准

    ⚠️ 注意：中国气象局雷达图使用墨卡托投影，这是一种非线性投影。
    简单的仿射变换无法准确建模这种投影关系。

    系统已默认使用 MercatorRadarMapper 进行坐标转换，无需手动校准即可获得准确结果。

    如需查看当前使用的坐标映射器信息，请访问 /api/v1/processing/status

    Args:
        data: 校准请求参数

    Returns:
        校准结果和仿射变换参数（仅供参考）
    """
    # 获取控制点
    query = db.query(ControlPoint).order_by(ControlPoint.created_at)

    if data.control_point_ids:
        query = query.filter(ControlPoint.id.in_(data.control_point_ids))

    control_points = query.all()

    if len(control_points) < 3:
        raise HTTPException(
            status_code=400,
            detail=f"至少需要3个控制点进行校准，当前只有{len(control_points)}个"
        )

    # 提取坐标数据
    pixel_x = np.array([cp.pixel_x for cp in control_points])
    pixel_y = np.array([cp.pixel_y for cp in control_points])
    lons = np.array([cp.longitude for cp in control_points])
    lats = np.array([cp.latitude for cp in control_points])

    # 归一化像素坐标到 [0, 1] 范围以提高数值稳定性
    # 假设雷达图片尺寸约为 1350x1208
    max_x = 1350.0
    max_y = 1208.0

    x_norm = pixel_x / max_x
    y_norm = pixel_y / max_y

    # 使用归一化后的坐标进行最小二乘拟合
    # lon = a0 + a1*(x/max_x) + a2*(y/max_y)
    # lat = b0 + b1*(x/max_x) + b2*(y/max_y)
    norm_coords = np.column_stack([x_norm, y_norm, np.ones_like(x_norm)])

    affine_lon_norm, residuals_lon, _, _ = np.linalg.lstsq(norm_coords, lons, rcond=None)
    affine_lat_norm, residuals_lat, _, _ = np.linalg.lstsq(norm_coords, lats, rcond=None)

    # 将归一化后的参数转换为原始像素坐标的参数
    # lon = a0 + a1*(x/max_x) + a2*(y/max_y)
    #     = a0 + (a1/max_x)*x + (a2/max_y)*y
    # 所以: affine_lon[0] = affine_lon_norm[0]
    #      affine_lon[1] = affine_lon_norm[1] / max_x
    #      affine_lon[2] = affine_lon_norm[2] / max_y

    affine_lon = np.array([
        affine_lon_norm[0],
        affine_lon_norm[1] / max_x,
        affine_lon_norm[2] / max_y
    ])

    affine_lat = np.array([
        affine_lat_norm[0],
        affine_lat_norm[1] / max_x,
        affine_lat_norm[2] / max_y
    ])

    print(f"✅ 校准参数（归一化后转换）:")
    print(f"  lon = {affine_lon[0]:.6f} + {affine_lon[1]:.8f}*x + {affine_lon[2]:.8f}*y")
    print(f"  lat = {affine_lat[0]:.6f} + {affine_lat[1]:.8f}*x + {affine_lat[2]:.8f}*y")

    # 验证控制点：使用默认映射器检查经纬度是否合理
    print(f"\n🔍 验证控制点合理性:")
    from app.services.processing_service import CoordinateMapper
    import glob

    # 获取一张雷达图片
    image_files = glob.glob("/Users/ranmufei/2026/leida_project/data/raw/*.png")
    if image_files:
        mapper = CoordinateMapper(image_files[0])

        invalid_points = []
        for cp in control_points:
            # 使用默认映射器预测该像素坐标对应的经纬度
            expected_lon, expected_lat = mapper.pixel_to_geo(cp.pixel_x, cp.pixel_y)
            lon_diff = abs(expected_lon - cp.longitude)
            lat_diff = abs(expected_lat - cp.latitude)

            print(f"  {cp.name}: 像素({cp.pixel_x}, {cp.pixel_y})")
            print(f"    输入经纬度: ({cp.longitude}, {cp.latitude})")
            print(f"    预期经纬度: ({expected_lon:.2f}, {expected_lat:.2f})")
            print(f"    偏差: lon={lon_diff:.2f}°, lat={lat_diff:.2f}°")

            # 如果偏差超过5度，可能是标注错误
            if lon_diff > 5 or lat_diff > 5:
                invalid_points.append(cp)
                print(f"    ❌ 偏差过大，可能是标注错误！")

        if invalid_points:
            raise HTTPException(
                status_code=400,
                detail=f"以下控制点的经纬度与点击位置严重不匹配，请重新标注：{', '.join([p.name for p in invalid_points])}\n"
                      f"建议：确保点击的位置与输入的城市经纬度一致。"
            )

    # 计算每个控制点的误差
    errors = []
    for cp in control_points:
        # 预测坐标
        pred_lon = affine_lon[0] + affine_lon[1] * cp.pixel_x + affine_lon[2] * cp.pixel_y
        pred_lat = affine_lat[0] + affine_lat[1] * cp.pixel_x + affine_lat[2] * cp.pixel_y

        errors.append({
            "id": cp.id,
            "name": cp.name,
            "error_lon": abs(pred_lon - cp.longitude),
            "error_lat": abs(pred_lat - cp.latitude)
        })

    # 保存校准参数
    # 先禁用之前的激活参数
    db.query(CalibrationParams).filter(CalibrationParams.is_active == True).update({"is_active": False})

    # 创建新的校准参数
    calibration = CalibrationParams.from_params(affine_lon, affine_lat, is_active=True)
    db.add(calibration)
    db.commit()

    # 处理残差值（可能是0维数组或1维数组）
    residual_lon_val = float(residuals_lon[0]) if len(residuals_lon) > 0 else 0.0
    residual_lat_val = float(residuals_lat[0]) if len(residuals_lat) > 0 else 0.0

    return {
        "code": 0,
        "message": "校准完成",
        "data": {
            "success": True,
            "affine_lon": affine_lon.tolist(),
            "affine_lat": affine_lat.tolist(),
            "residuals": {
                "lon": residual_lon_val,
                "lat": residual_lat_val
            },
            "errors": errors,
            "control_points_used": len(control_points)
        }
    }


@router.get("/calibration/active", response_model=dict)
async def get_active_calibration(
    db: Session = Depends(get_db)
):
    """
    获取当前激活的校准参数

    Returns:
        激活的校准参数
    """
    calibration = db.query(CalibrationParams).filter(CalibrationParams.is_active == True).first()

    if not calibration:
        return {
            "code": 0,
            "message": "暂无激活的校准参数",
            "data": None
        }

    return {
        "code": 0,
        "message": "获取成功",
        "data": calibration.to_dict()
    }


@router.delete("/calibration/active", response_model=dict)
async def deactivate_calibration(
    db: Session = Depends(get_db)
):
    """
    停用当前校准参数

    Returns:
        操作结果
    """
    db.query(CalibrationParams).filter(CalibrationParams.is_active == True).update({"is_active": False})
    db.commit()

    return {
        "code": 0,
        "message": "校准参数已停用"
    }
