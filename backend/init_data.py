#!/usr/bin/env python3
"""
初始化示例数据
"""
from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal
from app.models.user import User
from app.models.site import Site
from app.core.security import get_password_hash
from datetime import datetime

def init_sample_data():
    """初始化示例数据"""

    db = SessionLocal()

    try:
        # 创建默认管理员用户
        print("检查默认用户...")

        admin_user = db.query(User).filter(User.username == "admin").first()

        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@radar-system.com",
                hashed_password=get_password_hash("admin123"),
                full_name="系统管理员",
                is_active=True,
                is_superuser=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f"✓ 创建默认管理员: admin / admin123")
        else:
            print(f"✓ 管理员用户已存在: {admin_user.username}")

        # 创建示例站点
        print("\n检查示例站点...")

        sample_sites = [
            {
                "name": "北京站",
                "code": "BJ001",
                "longitude": 116.4074,
                "latitude": 39.9042,
                "altitude": 50,
                "region": "华北",
                "description": "北京市气象观测站点"
            },
            {
                "name": "上海站",
                "code": "SH001",
                "longitude": 121.4737,
                "latitude": 31.2304,
                "altitude": 10,
                "region": "华东",
                "description": "上海市气象观测站点"
            },
            {
                "name": "广州站",
                "code": "GZ001",
                "longitude": 113.2644,
                "latitude": 23.1291,
                "altitude": 20,
                "region": "华南",
                "description": "广州市气象观测站点"
            }
        ]

        for site_data in sample_sites:
            existing_site = db.query(Site).filter(Site.code == site_data["code"]).first()

            if not existing_site:
                site = Site(**site_data, is_active=True)
                db.add(site)
                db.commit()
                db.refresh(site)
                print(f"✓ 创建站点: {site.name} ({site.code})")
            else:
                print(f"✓ 站点已存在: {existing_site.name}")

        # 统计数据
        user_count = db.query(User).count()
        site_count = db.query(Site).count()

        print(f"\n数据初始化完成！")
        print(f"用户数量: {user_count}")
        print(f"站点数量: {site_count}")

    except Exception as e:
        print(f"错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_sample_data()
