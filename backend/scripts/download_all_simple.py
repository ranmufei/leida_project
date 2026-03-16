#!/usr/bin/env python3
"""
下载全部CMA雷达图片（简化版）

这个脚本会：
1. 从CMA API获取全部152张图片信息
2. 自动跳过已下载的图片（去重）
3. 下载所有未下载的图片

使用方法:
python3 download_all_simple.py
"""

import sys
import os

# 确保可以导入app模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.services.download_service_real import RealRadarImageDownloader
    print("✅ 模块导入成功")
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    print("\n请尝试:")
    print("1. cd /Users/ranmufei/2026/leida_project/backend")
    print("2. python3 -m scripts.download_all_simple")
    sys.exit(1)


def main():
    """主函数"""
    print("=" * 80)
    print("🌤️  下载全部CMA雷达图片".center(80))
    print("=" * 80)
    print()

    # 创建下载器
    print("⚙️  初始化下载器...")
    try:
        downloader = RealRadarImageDownloader()
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)

    # 下载全部图片（自动去重）
    print("\n开始下载全部图片（自动跳过已下载的）...")
    print("💾 保存位置: ../data/raw")
    print()

    # count=None 表示下载全部
    # force=False 表示跳过已下载的（去重）
    stats = downloader.download_latest_from_api(count=None, force=False)

    # 显示结果
    print("\n" + "=" * 80)
    print("✅ 下载完成！".center(80))
    print("=" * 80)
    print(f"总计处理: {stats['total']} 张")
    print(f"✅ 成功下载: {stats['success']} 张")
    print(f"⏭️  跳过（已存在）: {stats['skipped']} 张")
    print(f"❌ 失败: {stats['failed']} 张")
    print("=" * 80)

    if stats['failed'] > 0:
        print("\n⚠️  部分图片下载失败，可能原因:")
        print("  1. 网络连接问题")
        print("  2. Cookie认证过期（需要重新登录获取）")
        print("  3. CMA服务器限制")

    if stats['success'] > 0:
        print(f"\n🎉 成功下载了 {stats['success']} 张新图片！")
        print("查看图片: http://localhost:5173/images")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断下载")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 下载失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
