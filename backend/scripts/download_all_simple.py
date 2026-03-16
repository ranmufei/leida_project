#!/usr/bin/env python3
"""
下载雷达图片（简化版 - NMC直接URL方式）

这个脚本会：
1. 下载指定时间范围的雷达图片（每6分钟一张）
2. 自动跳过已下载的图片（去重）
3. 自动处理UTC到北京时间转换

使用方法:
python3 download_all_simple.py
"""

import sys
import os
from datetime import datetime, timedelta

# 确保可以导入app模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.services.download_service_nmc import NMCRadarImageDownloader
    print("✅ 模块导入成功")
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    print("\n请尝试:")
    print("1. cd /data/weather3.0/leida_project/backend")
    print("2. python3 -m scripts.download_all_simple")
    sys.exit(1)


def main():
    """主函数"""
    print("=" * 80)
    print("🌤️  下载雷达图片（NMC直接URL方式）".center(80))
    print("=" * 80)
    print()

    # 创建下载器
    print("⚙️  初始化下载器...")
    try:
        downloader = NMCRadarImageDownloader()
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)

    # 设置下载时间范围（默认最近24小时）
    hours = 24
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)

    print(f"\n📅 下载时间范围: 最近 {hours} 小时")
    print(f"   开始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   结束: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏰ 图片间隔: 6 分钟")
    print(f"💾 保存位置: ../data/raw")
    print()

    # 下载指定时间范围的图片（自动去重）
    # force=False 表示跳过已下载的（去重）
    stats = downloader.download_range(start_time, end_time, force=False)

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
        print("  2. 该时间点暂无图片数据")

    if stats['success'] > 0:
        print(f"\n🎉 成功下载了 {stats['success']} 张新图片！")


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
