"""
FastAPI应用主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.v1 import api_router
from app.core.database import engine
from app.models import *


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("🚀 应用启动中...")
    print(f"📊 环境: {settings.APP_ENVIRONMENT}")
    print(f"🔗 数据库: {settings.DATABASE_HOST}:{settings.DATABASE_PORT}")
    yield
    # 关闭时执行
    print("👋 应用关闭中...")
    engine.dispose()


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="雷达数据自动化采集、处理、管理和预测平台",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 健康检查端点
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "气象雷达数据管理与预测平台 API",
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "database": "connected"
    }


# 注册API路由
app.include_router(api_router, prefix="/api/v1")


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "内部服务器错误",
            "detail": str(exc) if settings.DEBUG else "请联系系统管理员"
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
