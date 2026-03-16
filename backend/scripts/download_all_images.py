#!/usr/bin/env python3
"""
下载NMC雷达图片（使用NMC直接URL方式）

使用方法:
python3 download_all_images.py
"""

import os
import sys
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.download_service_nmc import NMCRadarImageDownloader


def main():
    """下载指定时间范围的图片"""
    print("=" * 80)
    print("🌤️  下载NMC雷达图片".center(80))
    print("=" * 80)
    print()

    # 创建下载器
    print("⚙️  初始化下载器...")
    downloader = NMCRadarImageDownloader()

    # 默认下载最近24小时的数据
    hours = 24
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)

    print(f"\n📅 时间范围: 最近 {hours} 小时")
    print(f"   开始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   结束: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 下载指定时间范围的图片
    print("\n开始下载...")
    stats = downloader.download_range(start_time, end_time, force=False)

    # 显示结果
    print("\n" + "=" * 80)
    print("✅ 下载完成！".center(80))
    print("=" * 80)
    print(f"总计: {stats['total']}")
    print(f"成功: {stats['success']}")
    print(f"跳过: {stats['skipped']}")
    print(f"失败: {stats['failed']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
