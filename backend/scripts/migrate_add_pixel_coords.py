#!/usr/bin/env python3
"""
数据库迁移脚本：添加像素坐标字段

为site_radar_data表添加pixel_x和pixel_y字段
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine
from sqlalchemy import text

def migrate():
    """执行数据库迁移"""
    print("=" * 80)
    print("🔄 数据库迁移：添加像素坐标字段")
    print("=" * 80)

    with engine.connect() as conn:
        # 检查字段是否已存在
        result = conn.execute(text("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'site_radar_data'
            AND COLUMN_NAME IN ('pixel_x', 'pixel_y')
        """))

        existing_columns = [row[0] for row in result]

        if 'pixel_x' in existing_columns and 'pixel_y' in existing_columns:
            print("\n✅ 字段已存在，无需迁移")
            return

        print(f"\n📋 当前已有字段: {existing_columns}")

        # 添加字段
        if 'pixel_x' not in existing_columns:
            print("\n➕ 添加 pixel_x 字段...")
            conn.execute(text("""
                ALTER TABLE site_radar_data
                ADD COLUMN pixel_x INT NULL COMMENT '雷达图片X坐标'
                AFTER rgb_value
            """))
            print("✅ pixel_x 字段添加成功")

        if 'pixel_y' not in existing_columns:
            print("\n➕ 添加 pixel_y 字段...")
            conn.execute(text("""
                ALTER TABLE site_radar_data
                ADD COLUMN pixel_y INT NULL COMMENT '雷达图片Y坐标'
                AFTER pixel_x
            """))
            print("✅ pixel_y 字段添加成功")

        # 提交事务
        conn.commit()

        print("\n" + "=" * 80)
        print("🎉 数据库迁移完成！")
        print("=" * 80)

        # 显示新字段
        result = conn.execute(text("""
            SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'site_radar_data'
            AND COLUMN_NAME IN ('pixel_x', 'pixel_y')
        """))

        print("\n📋 新字段信息:")
        for row in result:
            print(f"  - {row[0]}: {row[1]}, NULL={row[2]}, 备注={row[3]}")

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
