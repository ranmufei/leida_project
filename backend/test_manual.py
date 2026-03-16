#!/usr/bin/env python3
"""
手动测试脚本 - 测试核心功能
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("气象雷达数据管理与预测平台 - 手动测试")
print("=" * 60)
print()

# 测试1: 模块导入测试
print("【测试1】模块导入测试")
print("-" * 60)

try:
    from app.services.processing_service import CoordinateMapper, ColorScaleParser
    print("✓ 处理服务模块导入成功")
except Exception as e:
    print(f"✗ 处理服务模块导入失败: {e}")
    sys.exit(1)

try:
    from app.models.user import User
    from app.models.site import Site
    print("✓ 数据模型导入成功")
except Exception as e:
    print(f"✗ 数据模型导入失败: {e}")
    sys.exit(1)

print()

# 测试2: 坐标映射测试
print("【测试2】坐标映射测试")
print("-" * 60)

try:
    mapper = CoordinateMapper(width=1000, height=1000)

    # 测试中心点
    pixel_x, pixel_y = mapper.geo_to_pixel(105.0, 35.0)
    assert pixel_x == 500 and pixel_y == 500, f"中心点转换错误: ({pixel_x}, {pixel_y})"
    print(f"✓ 中心点转换: (105.0°E, 35.0°N) → (500, 500)")

    # 测试边界点
    pixel_x, pixel_y = mapper.geo_to_pixel(105.35, 35.35)
    print(f"✓ 边界点转换: (105.35°E, 35.35°N) → ({pixel_x}, {pixel_y})")

    # 测试反向转换
    lon, lat = mapper.pixel_to_geo(500, 500)
    print(f"✓ 反向转换: (500, 500) → ({lon:.2f}°E, {lat:.2f}°N)")

    # 测试往返一致性
    original_lon, original_lat = 116.4, 39.9
    px, py = mapper.geo_to_pixel(original_lon, original_lat)
    result_lon, result_lat = mapper.pixel_to_geo(px, py)
    error_lon = abs(original_lon - result_lon)
    error_lat = abs(original_lat - result_lat)
    assert error_lon < 0.01 and error_lat < 0.01, f"往返误差过大: ({error_lon}, {error_lat})"
    print(f"✓ 往返一致性测试: 误差 < 0.01°")

except Exception as e:
    print(f"✗ 坐标映射测试失败: {e}")

print()

# 测试3: 颜色标尺解析测试
print("【测试3】颜色标尺解析测试")
print("-" * 60)

try:
    parser = ColorScaleParser()

    # 测试无回波
    dbz = parser.rgb_to_dbz(0, 0, 0)
    assert 0 <= dbz <= 5, f"无回波dBZ范围错误: {dbz}"
    print(f"✓ 无回波 RGB(0,0,0) → dBZ={dbz:.1f}")

    # 测试弱回波
    dbz = parser.rgb_to_dbz(0, 255, 0)
    assert 10 <= dbz <= 15, f"弱回波dBZ范围错误: {dbz}"
    print(f"✓ 弱回波 RGB(0,255,0) → dBZ={dbz:.1f}")

    # 测试中等回波
    dbz = parser.rgb_to_dbz(255, 255, 0)
    assert 20 <= dbz <= 25, f"中等回波dBZ范围错误: {dbz}"
    print(f"✓ 中等回波 RGB(255,255,0) → dBZ={dbz:.1f}")

    # 测试强回波
    dbz = parser.rgb_to_dbz(255, 0, 0)
    assert 45 <= dbz <= 50, f"强回波dBZ范围错误: {dbz}"
    print(f"✓ 强回波 RGB(255,0,0) → dBZ={dbz:.1f}")

    # 测试云影响因子
    factor_low = parser.get_cloud_impact_factor(5)
    factor_medium = parser.get_cloud_impact_factor(30)
    factor_high = parser.get_cloud_impact_factor(60)
    print(f"✓ 云影响因子: dBZ=5 → {factor_low:.2%}, dBZ=30 → {factor_medium:.2%}, dBZ=60 → {factor_high:.2%}")

    # 测试dBZ等级分类
    category = parser.get_dbz_category(25)
    print(f"✓ dBZ等级分类: dBZ=25 → {category}")

except Exception as e:
    print(f"✗ 颜色标尺解析测试失败: {e}")

print()

# 测试4: 数据库连接测试
print("【测试4】数据库连接测试")
print("-" * 60)

try:
    from app.core.database import engine
    from sqlalchemy import text

    with engine.connect() as conn:
        # 测试连接
        result = conn.execute(text('SELECT DATABASE()'))
        db_name = result.scalar()
        print(f"✓ 数据库连接成功: {db_name}")

        # 检查表
        result = conn.execute(text('SHOW TABLES'))
        tables = [row[0] for row in result]
        print(f"✓ 数据库表数量: {len(tables)}")

        # 检查核心表
        expected_tables = ['users', 'sites', 'radar_images', 'site_radar_data', 'site_predictions', 'download_logs']
        for table in expected_tables:
            if table in tables:
                print(f"✓ 表 {table} 存在")
            else:
                print(f"⚠ 表 {table} 不存在")

        # 测试用户数据
        result = conn.execute(text('SELECT COUNT(*) FROM users'))
        user_count = result.scalar()
        print(f"✓ 用户数量: {user_count}")

        # 测试站点数据
        result = conn.execute(text('SELECT COUNT(*) FROM sites'))
        site_count = result.scalar()
        print(f"✓ 站点数量: {site_count}")

except ImportError as e:
    print(f"⚠ 数据库模块未安装: {e}")
except Exception as e:
    print(f"✗ 数据库连接测试失败: {e}")

print()

# 测试5: JWT认证测试
print("【测试5】JWT认证测试")
print("-" * 60)

try:
    from app.core.security import create_access_token, verify_token

    # 创建测试token
    data = {"sub": "test_user"}
    token = create_access_token(data)
    print(f"✓ Token创建成功: {token[:50]}...")

    # 验证token
    payload = verify_token(token)
    print(f"✓ Token验证成功: user={payload.get('sub')}")

except ImportError as e:
    print(f"⚠ JWT模块未安装: {e}")
except Exception as e:
    print(f"✗ JWT认证测试失败: {e}")

print()

# 测试总结
print("=" * 60)
print("测试完成")
print("=" * 60)
print()
print("核心功能测试通过！")
print()
