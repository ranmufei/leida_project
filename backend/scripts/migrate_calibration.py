#!/usr/bin/env python3
"""数据库迁移脚本：创建校准相关表"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine
from sqlalchemy import text


def migrate():
    """创建校准相关表"""
    with engine.connect() as conn:
        # 检查表是否已存在
        result = conn.execute(text("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME IN ('control_points', 'calibration_params')
        """))

        existing_tables = [row[0] for row in result]

        # 创建 control_points 表
        if 'control_points' not in existing_tables:
            conn.execute(text("""
                CREATE TABLE control_points (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '控制点ID',
                    pixel_x INT NOT NULL COMMENT '像素X坐标',
                    pixel_y INT NOT NULL COMMENT '像素Y坐标',
                    longitude FLOAT NOT NULL COMMENT '经度',
                    latitude FLOAT NOT NULL COMMENT '纬度',
                    name VARCHAR(100) COMMENT '控制点名称',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='坐标校准控制点表'
            """))
            print("✅ 已创建 control_points 表")
        else:
            print("⏭️  control_points 表已存在")

        # 创建 calibration_params 表
        if 'calibration_params' not in existing_tables:
            conn.execute(text("""
                CREATE TABLE calibration_params (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '参数ID',
                    affine_lon_a0 FLOAT COMMENT '经度仿射变换参数 a0',
                    affine_lon_a1 FLOAT COMMENT '经度仿射变换参数 a1',
                    affine_lon_a2 FLOAT COMMENT '经度仿射变换参数 a2',
                    affine_lat_b0 FLOAT COMMENT '纬度仿射变换参数 b0',
                    affine_lat_b1 FLOAT COMMENT '纬度仿射变换参数 b1',
                    affine_lat_b2 FLOAT COMMENT '纬度仿射变换参数 b2',
                    is_active BOOLEAN DEFAULT FALSE COMMENT '是否激活使用',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    INDEX idx_is_active (is_active)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='坐标校准参数表'
            """))
            print("✅ 已创建 calibration_params 表")
        else:
            print("⏭️  calibration_params 表已存在")

        conn.commit()
        print("\n🎉 数据库迁移完成！")


if __name__ == '__main__':
    migrate()
