#!/usr/bin/env python3
"""
数据库表初始化脚本
"""
from app.core.database import engine
from app.models.user import User
from app.models.site import Site
from app.models.radar_image import RadarImage
from app.models.radar_data import SiteRadarData
from app.models.prediction import SitePrediction
from sqlalchemy import text

from app.core.database import Base

print("创建数据库表...")
Base.metadata.create_all(bind=engine)

with engine.connect() as conn:
    result = conn.execute(text('SHOW TABLES'))
    tables = [row[0] for row in result]
    print(f'已创建的表: {tables}')

    # 检查用户表
    if 'users' in tables:
        result = conn.execute(text('SELECT COUNT(*) FROM users'))
        count = result.scalar()
        print(f'用户数量: {count}')

print("\n数据库初始化完成！")
