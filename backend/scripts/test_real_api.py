#!/usr/bin/env python3
"""
测试真实的中国气象局雷达数据API

根据API.md文档实现
"""
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.download_service_real import RealRadarImageDownloader


def test_real_api():
    """测试真实API"""
    print("=" * 60)
    print("🧪 测试中国气象局真实雷达数据API")
    print("=" * 60)

    downloader = RealRadarImageDownloader()

    # 测试1: 获取图片列表
    print("\n📡 测试1: 获取图片列表")
    print("-" * 40)
    images = downloader.fetch_available_images(limit=3)

    if images:
        print(f"✅ 成功获取 {len(images)} 张图片信息:")
        for i, img in enumerate(images[:3], 1):
            print(f"\n  图片 {i}:")
            print(f"    文件名: {img.get('c_FNAME')}")
            print(f"    观测时间: {img.get('v_SHIJIAN')}")
            print(f"    创建时间: {img.get('c_IYMDHMS')}")
            print(f"    文件URL: {img.get('fileURL')}")
    else:
        print("❌ 获取图片列表失败")
        return

    # 测试2: 下载1张图片
    print(f"\n📥 测试2: 下载最新图片")
    print("-" * 40)

    stats = downloader.download_latest_from_api(count=1, force=True)

    print(f"\n📊 下载统计:")
    print(f"  总计: {stats['total']}")
    print(f"  成功: {stats['success']}")
    print(f"  失败: {stats['failed']}")
    print(f"  跳过: {stats['skipped']}")

    # 测试3: 查看下载统计
    print(f"\n📊 测试3: 数据库统计")
    print("-" * 40)
    stats = downloader.get_download_statistics()
    print(f"总记录数: {stats['total']}")
    print(f"成功: {stats['success']}")
    print(f"失败: {stats['failed']}")
    print(f"成功率: {stats['success_rate']:.2%}")
    print(f"最新下载: {stats['latest_download_time']}")

    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_real_api()
