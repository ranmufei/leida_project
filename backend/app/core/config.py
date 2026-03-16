"""
应用配置模块
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """应用配置类"""

    # 应用基本信息
    APP_NAME: str = "气象雷达数据管理与预测平台"
    APP_VERSION: str = "1.0.0"
    APP_ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"

    # 数据库配置
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 3308
    DATABASE_USER: str = "admin"
    DATABASE_PASSWORD: str = "cqsyyxydxsyc6z"
    DATABASE_NAME: str = "gfs_weather"
    DATABASE_CHARSET: str = "utf8mb4"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40

    @property
    def DATABASE_URL(self) -> str:
        """构建数据库连接URL"""
        return f"mysql+pymysql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}?charset={self.DATABASE_CHARSET}"

    # JWT配置
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # 数据目录配置
    DATA_DIR: str = "../data"
    RAW_DATA_DIR: str = "../data/raw"
    PROCESSED_DATA_DIR: str = "../data/processed"
    MODEL_DIR: str = "../data/models"
    LOG_DIR: str = "../logs"

    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ]

    # 下载配置
    DOWNLOAD_BASE_URL: str = "https://image.data.cma.cn/vis/RAD__B0_CR"
    DOWNLOAD_INTERVAL_MINUTES: int = 6
    DOWNLOAD_MAX_RETRIES: int = 3
    DOWNLOAD_TIMEOUT: int = 30

    # CMA API认证配置
    CMA_API_URL: str = "https://data.cma.cn/weatherGis/web/bmd/VisDataDef/getVisData?datacode=RAD__B0_CR"
    CMA_BASE_URL: str = "https://data.cma.cn"
    # CMA认证Cookie（从浏览器获取）
    CMA_COOKIE: str = ""  # 格式: "key1=value1; key2=value2"
    # 或者使用认证Token
    CMA_AUTH_TOKEN: str = ""  # JWT Token或其他认证token

    # 处理配置
    PROCESSING_BATCH_SIZE: int = 10
    PROCESSING_MAX_WORKERS: int = 4

    # 雷达图片配置
    RADAR_IMAGE_LEGEND_HEIGHT: int = 120  # 底部图例区域高度（像素）

    # 预测配置
    OPTICAL_FLOW_ENABLED: bool = True
    PROPHET_ENABLED: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建配置实例
settings = Settings()
