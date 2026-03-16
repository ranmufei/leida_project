"""
检查数据库连接
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine, SessionLocal
from app.models import Site, User


def check_database():
    """检查数据库连接和数据"""
    print("🔍 检查数据库连接...")

    try:
        # 测试连接
        with engine.connect() as conn:
            print("✅ 数据库连接成功")

        # 检查表
        db = SessionLocal()

        # 检查站点数据
        site_count = db.query(Site).count()
        print(f"📍 站点数量: {site_count}")

        if site_count > 0:
            sites = db.query(Site).limit(5).all()
            print("前5个站点:")
            for site in sites:
                print(f"  - {site.name} ({site.code}): ({site.longitude}, {site.latitude})")

        # 检查用户数据
        user_count = db.query(User).count()
        print(f"\n👤 用户数量: {user_count}")

        if user_count > 0:
            users = db.query(User).all()
            print("用户列表:")
            for user in users:
                print(f"  - {user.username} ({user.email}) - {'管理员' if user.is_superuser else '普通用户'}")

        db.close()

        print("\n✅ 数据库检查完成")

    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")


if __name__ == "__main__":
    check_database()
