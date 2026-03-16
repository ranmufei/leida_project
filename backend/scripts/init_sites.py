#!/usr/bin/env python3
"""
初始化站点数据

创建中国主要城市的气象监测站点
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.site import Site
from datetime import datetime


# 中国主要城市站点数据
CHINA_SITES = [
    {
        "name": "北京",
        "code": "BJ001",
        "longitude": 116.4074,
        "latitude": 39.9042,
        "altitude": 43.5,
        "region": "华北",
        "description": "中国首都，位于华北平原北部"
    },
    {
        "name": "上海",
        "code": "SH001",
        "longitude": 121.4737,
        "latitude": 31.2304,
        "altitude": 4.0,
        "region": "华东",
        "description": "中国最大城市，位于长江入海口"
    },
    {
        "name": "广州",
        "code": "GZ001",
        "longitude": 113.2644,
        "latitude": 23.1291,
        "altitude": 21.0,
        "region": "华南",
        "description": "广东省省会，华南地区中心城市"
    },
    {
        "name": "深圳",
        "code": "SZ001",
        "longitude": 114.0579,
        "latitude": 22.5431,
        "altitude": 8.0,
        "region": "华南",
        "description": "中国改革开放前沿城市"
    },
    {
        "name": "成都",
        "code": "CD001",
        "longitude": 104.0668,
        "latitude": 30.5728,
        "altitude": 505.0,
        "region": "西南",
        "description": "四川省省会，西南地区科技、商贸中心"
    },
    {
        "name": "武汉",
        "code": "WH001",
        "longitude": 114.3055,
        "latitude": 30.5928,
        "altitude": 23.0,
        "region": "华中",
        "description": "湖北省省会，九省通衢"
    },
    {
        "name": "西安",
        "code": "XA001",
        "longitude": 108.9398,
        "latitude": 34.3416,
        "altitude": 400.0,
        "region": "西北",
        "description": "陕西省省会，古都长安"
    },
    {
        "name": "杭州",
        "code": "HZ001",
        "longitude": 120.1551,
        "latitude": 30.2741,
        "altitude": 8.0,
        "region": "华东",
        "description": "浙江省省会，人间天堂"
    },
    {
        "name": "南京",
        "code": "NJ001",
        "longitude": 118.7969,
        "latitude": 32.0603,
        "altitude": 15.0,
        "region": "华东",
        "description": "江苏省省会，六朝古都"
    },
    {
        "name": "重庆",
        "code": "CQ001",
        "longitude": 106.5516,
        "latitude": 29.5630,
        "altitude": 259.0,
        "region": "西南",
        "description": "直辖市，山城"
    }
]


def init_sites():
    """初始化站点数据"""
    print("=" * 70)
    print("🌍 开始初始化中国主要城市站点数据")
    print("=" * 70)

    db = SessionLocal()

    try:
        # 检查是否已存在站点
        existing_count = db.query(Site).count()
        if existing_count > 0:
            print(f"\n⚠️  数据库中已存在 {existing_count} 个站点")
            choice = input("是否清空并重新初始化？(y/N): ").strip().lower()
            if choice == 'y':
                db.query(Site).delete()
                db.commit()
                print("✅ 已清空现有站点数据")
            else:
                print("❌ 取消初始化")
                return

        # 插入站点数据
        print(f"\n📝 准备插入 {len(CHINA_SITES)} 个站点...\n")

        for i, site_data in enumerate(CHINA_SITES, 1):
            # 检查站点编码是否已存在
            existing = db.query(Site).filter(Site.code == site_data['code']).first()
            if existing:
                print(f"⏭️  [{i}/{len(CHINA_SITES)}] {site_data['name']} ({site_data['code']}) - 已存在，跳过")
                continue

            # 创建新站点
            site = Site(
                name=site_data['name'],
                code=site_data['code'],
                longitude=site_data['longitude'],
                latitude=site_data['latitude'],
                altitude=site_data['altitude'],
                region=site_data['region'],
                description=site_data['description'],
                is_active=True
            )

            db.add(site)

            print(f"✅ [{i}/{len(CHINA_SITES)}] {site_data['name']} ({site_data['code']}) - "
                  f"经度: {site_data['longitude']}, 纬度: {site_data['latitude']}")

        # 提交事务
        db.commit()

        print(f"\n{'=' * 70}")
        print(f"🎉 站点初始化完成！")
        print(f"{'=' * 70}")

        # 统计信息
        total_sites = db.query(Site).count()
        active_sites = db.query(Site).filter(Site.is_active == True).count()

        print(f"\n📊 统计信息:")
        print(f"  总站点数: {total_sites}")
        print(f"  启用站点: {active_sites}")
        print(f"  禁用站点: {total_sites - active_sites}")

        # 按区域统计
        print(f"\n📍 站点分布:")
        sites = db.query(Site).order_by(Site.region).all()
        current_region = None
        for site in sites:
            if site.region != current_region:
                current_region = site.region
                print(f"\n  {current_region}:")
            print(f"    - {site.name} ({site.code})")

    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        db.rollback()
        raise

    finally:
        db.close()


def show_sites():
    """显示所有站点信息"""
    print("\n" + "=" * 70)
    print("📋 当前站点列表")
    print("=" * 70)

    db = SessionLocal()
    try:
        sites = db.query(Site).order_by(Site.id).all()

        if not sites:
            print("\n⚠️  数据库中暂无站点数据")
            print("   请运行: python3 scripts/init_sites.py")
            return

        print(f"\n共 {len(sites)} 个站点:\n")

        for site in sites:
            status = "✅ 启用" if site.is_active else "❌ 禁用"
            print(f"ID: {site.id}")
            print(f"  名称: {site.name} ({site.code})")
            print(f"  位置: ({site.longitude}, {site.latitude}), 海拔: {site.altitude}m")
            print(f"  区域: {site.region}")
            print(f"  状态: {status}")
            print(f"  描述: {site.description}")
            print(f"  创建时间: {site.created_at}")
            print()

    except Exception as e:
        print(f"\n❌ 查询失败: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='站点数据管理')
    parser.add_argument('action', choices=['init', 'list', 'cleanup'],
                       help='操作类型: init(初始化), list(查看列表), cleanup(清空)')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='自动确认所有提示')

    args = parser.parse_args()

    if args.action == 'init':
        if args.yes:
            # 自动确认模式：模拟用户输入'y'
            import io
            sys.stdin = io.StringIO('y\n')
        init_sites()

    elif args.action == 'list':
        show_sites()

    elif args.action == 'cleanup':
        print("⚠️  警告：此操作将删除所有站点数据！")
        if args.yes or input("确认删除？(y/N): ").strip().lower() == 'y':
            db = SessionLocal()
            try:
                count = db.query(Site).delete()
                db.commit()
                print(f"✅ 已删除 {count} 个站点")
            except Exception as e:
                print(f"❌ 删除失败: {e}")
                db.rollback()
            finally:
                db.close()
        else:
            print("❌ 取消删除")
