"""
系统监控API端点
"""
from fastapi import APIRouter
from app.schemas.common import ApiResponse
import platform
import psutil
from datetime import datetime

router = APIRouter()


@router.get("/info", response_model=ApiResponse)
async def get_system_info():
    """
    获取系统信息

    返回服务器和应用的详细信息
    """
    # 获取系统信息
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    return ApiResponse(
        code=200,
        message="success",
        data={
            "system": {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "hostname": platform.node()
            },
            "python": {
                "version": platform.python_version(),
                "implementation": platform.python_implementation()
            },
            "app": {
                "name": "气象雷达数据管理与预测平台",
                "version": "1.0.0",
                "environment": "development"
            },
            "resources": {
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    )


@router.get("/status", response_model=ApiResponse)
async def get_system_status():
    """
    获取系统状态
    """
    return ApiResponse(
        code=200,
        message="success",
        data={
            "system_info": {
                "version": "1.0.0",
                "environment": "development",
                "status": "running"
            },
            "services": {
                "database": "connected",
                "redis": "connected",
                "celery": "running"
            }
        }
    )


@router.get("/health", response_model=ApiResponse)
async def health_check():
    """
    健康检查
    """
    return ApiResponse(
        code=200,
        message="healthy",
        data={"status": "ok"}
    )
