"""
数据库初始化脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine, Base
from app.models import *
from app.core.security import get_password_hash
from sqlalchemy.orm import sessionmaker


def init_database():
    """初始化数据库表"""
    print("🔧 开始初始化数据库...")

    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建成功")

    # 创建默认管理员用户
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # 检查是否已有管理员用户
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if not existing_admin:
            admin_user = User(
                username="admin",
                email="admin@example.com",
                full_name="系统管理员",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_superuser=True
            )
            db.add(admin_user)
            db.commit()
            print("✅ 默认管理员用户创建成功 (用户名: admin, 密码: admin123)")
        else:
            print("ℹ️  管理员用户已存在，跳过创建")

    except Exception as e:
        print(f"❌ 创建管理员用户失败: {e}")
        db.rollback()
    finally:
        db.close()

    # 插入示例站点数据
    try:
        sample_sites = [
            Site(
                name="北京站",
                code="BJ001",
                longitude=116.4074,
                latitude=39.9042,
                region="华北",
                description="北京气象观测站"
            ),
            Site(
                name="上海站",
                code="SH001",
                longitude=121.4737,
                latitude=31.2304,
                region="华东",
                description="上海气象观测站"
            ),
            Site(
                name="广州站",
                code="GZ001",
                longitude=113.2644,
                latitude=23.1291,
                region="华南",
                description="广州气象观测站"
            )
        ]

        for site in sample_sites:
            existing = db.query(Site).filter(Site.code == site.code).first()
            if not existing:
                db.add(site)

        db.commit()
        print("✅ 示例站点数据插入成功")

    except Exception as e:
        print(f"❌ 插入示例数据失败: {e}")
        db.rollback()
    finally:
        db.close()

    print("\n🎉 数据库初始化完成!")


if __name__ == "__main__":
    init_database()
