#!/usr/bin/env python3
"""
下载雷达图片（使用NMC直接URL方式）

每6分钟一张图片，自动处理UTC到北京时间转换
"""
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.download_service_nmc import NMCRadarImageDownloader


def main():
    print("=" * 60)
    print("🚀 开始下载雷达图片（NMC直接URL方式）")
    print("=" * 60)

    # 初始化下载器
    downloader = NMCRadarImageDownloader()

    # 默认下载最近24小时的图片
    # 可根据需要修改时间范围
    hours = 24
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)

    print(f"\n📅 时间范围: 最近 {hours} 小时")
    print(f"   开始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   结束: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏰ 间隔: 6 分钟/张")

    # 下载指定时间范围的图片
    stats = downloader.download_range(start_time, end_time, force=False)

    print(f"\n" + "=" * 60)
    print(f"📊 下载任务完成")
    print(f"=" * 60)
    print(f"总计: {stats['total']} 张")
    print(f"✅ 成功: {stats['success']} 张")
    print(f"⏭️  跳过: {stats['skipped']} 张")
    print(f"❌ 失败: {stats['failed']} 张")
    print(f"=" * 60)

    if stats['failed'] > 0:
        print(f"\n💡 提示: 有 {stats['failed']} 张图片下载失败")
        print(f"可能原因:")
        print(f"  1. 网络连接不稳定")
        print(f"  2. 该时间点暂无图片")


def download_custom(start_time_str: str, end_time_str: str):
    """
    下载自定义时间范围的图片

    Args:
        start_time_str: 开始时间字符串 (格式: YYYY-MM-DD HH:MM:SS)
        end_time_str: 结束时间字符串 (格式: YYYY-MM-DD HH:MM:SS)
    """
    print("=" * 60)
    print("🚀 自定义时间范围下载")
    print("=" * 60)

    downloader = NMCRadarImageDownloader()

    # 解析时间
    start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")

    print(f"\n📅 时间范围:")
    print(f"   开始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   结束: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

    stats = downloader.download_range(start_time, end_time, force=False)

    print(f"\n" + "=" * 60)
    print(f"📊 下载任务完成")
    print(f"=" * 60)
    print(f"总计: {stats['total']} 张")
    print(f"✅ 成功: {stats['success']} 张")
    print(f"⏭️  跳过: {stats['skipped']} 张")
    print(f"❌ 失败: {stats['failed']} 张")
    print(f"=" * 60)


if __name__ == "__main__":
    main()
