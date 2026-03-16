"""
API v1 路由模块
"""
from fastapi import APIRouter

from app.api.v1.endpoints import sites, weather_stations, auth, system, download, data, predictions, images, calibration

api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(sites.router, prefix="/sites", tags=["站点管理"])
api_router.include_router(weather_stations.router, prefix="/weather-stations", tags=["气象站点管理"])
api_router.include_router(download.router, prefix="/downloads", tags=["下载管理"])
api_router.include_router(system.router, prefix="/system", tags=["系统监控"])
api_router.include_router(data.router, prefix="/data", tags=["数据查询"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["预测管理"])
api_router.include_router(images.router, prefix="/images", tags=["图片管理"])
api_router.include_router(calibration.router, tags=["坐标校准"])
