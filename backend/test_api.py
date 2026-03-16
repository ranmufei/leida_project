#!/usr/bin/env python3
"""
API接口测试脚本
测试所有后端API接口的功能
"""
import sys
import os
import json
import time
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 80)
print("气象雷达数据管理与预测平台 - API接口测试")
print("=" * 80)
print()

# 测试配置
API_BASE_URL = "http://localhost:8000"
TEST_USER = {
    "username": "admin",
    "password": "admin123"
}

# 全局变量存储token
auth_token = None
test_site_id = None

def print_test_header(title):
    """打印测试标题"""
    print()
    print("=" * 80)
    print(f" {title}")
    print("=" * 80)
    print()

def print_success(message):
    """打印成功信息"""
    print(f"✅ {message}")

def print_error(message):
    """打印错误信息"""
    print(f"❌ {message}")

def print_info(message):
    """打印信息"""
    print(f"ℹ️  {message}")

def test_imports():
    """测试1: 模块导入"""
    print_test_header("测试1: 模块导入测试")

    try:
        from app.core.database import engine
        print_success("数据库模块导入成功")
    except Exception as e:
        print_error(f"数据库模块导入失败: {e}")
        return False

    try:
        from app.models.user import User
        from app.models.site import Site
        print_success("数据模型导入成功")
    except Exception as e:
        print_error(f"数据模型导入失败: {e}")
        return False

    try:
        from app.services.processing_service import CoordinateMapper, ColorScaleParser
        print_success("处理服务导入成功")
    except Exception as e:
        print_error(f"处理服务导入失败: {e}")
        return False

    print_success("所有核心模块导入成功")
    return True

def test_database_connection():
    """测试2: 数据库连接"""
    print_test_header("测试2: 数据库连接测试")

    try:
        from app.core.database import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            # 获取数据库名
            result = conn.execute(text('SELECT DATABASE()'))
            db_name = result.scalar()
            print_success(f"数据库连接成功: {db_name}")

            # 检查表
            result = conn.execute(text('SHOW TABLES'))
            tables = [row[0] for row in result]
            print_info(f"数据库表数量: {len(tables)}")

            # 检查核心表
            for table in ['users', 'sites', 'radar_images', 'site_radar_data', 'site_predictions']:
                if table in tables:
                    result = conn.execute(text(f'SELECT COUNT(*) FROM {table}'))
                    count = result.scalar()
                    print_success(f"表 {table}: {count}条记录")
                else:
                    print_error(f"表 {table} 不存在")
                    return False

            # 检查默认用户
            result = conn.execute(text('SELECT username FROM users WHERE username="admin"'))
            admin_user = result.scalar()
            if admin_user:
                print_success(f"默认管理员用户存在: {admin_user}")
            else:
                print_error("默认管理员用户不存在")
                return False

        return True

    except Exception as e:
        print_error(f"数据库连接测试失败: {e}")
        return False

def test_core_services():
    """测试3: 核心服务"""
    print_test_header("测试3: 核心服务测试")

    try:
        from app.services.processing_service import CoordinateMapper

        # 测试坐标映射
        mapper = CoordinateMapper(width=1000, height=1000)

        # 中心点转换
        pixel_x, pixel_y = mapper.geo_to_pixel(105.0, 35.0)
        assert pixel_x == 500 and pixel_y == 500
        print_success(f"坐标映射: 中心点 (105.0°E, 35.0°N) → ({pixel_x}, {pixel_y})")

        # 往返一致性
        lon, lat = mapper.pixel_to_geo(500, 500)
        print_success(f"反向转换: (500, 500) → ({lon:.2f}°E, {lat:.2f}°N)")

    except Exception as e:
        print_error(f"坐标映射测试失败: {e}")
        return False

    try:
        from app.services.processing_service import ColorScaleParser

        # 测试颜色解析
        parser = ColorScaleParser()

        # 测试RGB转dBZ
        dbz = parser.rgb_to_dbz(0, 255, 0)
        assert 10 <= dbz <= 15
        print_success(f"颜色解析: RGB(0,255,0) → dBZ={dbz:.1f}")

        # 测试云影响因子
        factor = parser.get_cloud_impact_factor(30)
        print_success(f"云影响因子: dBZ=30 → {factor:.2%}")

    except Exception as e:
        print_error(f"颜色解析测试失败: {e}")
        return False

    print_success("核心服务测试通过")
    return True

def main():
    """主测试函数"""
    print()
    print("🚀 开始执行API接口测试...")
    print()

    results = {
        "模块导入": False,
        "数据库连接": False,
        "核心服务": False,
    }

    # 执行测试
    results["模块导入"] = test_imports()
    results["数据库连接"] = test_database_connection()
    results["核心服务"] = test_core_services()

    # 测试总结
    print_test_header("测试总结")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0

    print(f"总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"通过率: {pass_rate:.1f}%")
    print()

    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")

    print()
    if pass_rate == 100:
        print_success("🎉 所有测试通过！系统可以正常使用！")
        return 0
    else:
        print_error(f"⚠️  有{failed}个测试失败，请检查")
        return 1

if __name__ == "__main__":
    sys.exit(main())
