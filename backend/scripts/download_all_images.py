#!/usr/bin/env python3
"""
下载全部CMA雷达图片

使用方法:
python3 download_all_images.py
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.download_service_real import RealRadarImageDownloader


def main():
    """下载全部图片"""
    print("=" * 80)
    print("🌤️  下载全部CMA雷达图片".center(80))
    print("=" * 80)
    print()

    # 创建下载器
    print("⚙️  初始化下载器...")
    downloader = RealRadarImageDownloader()

    # 下载全部图片
    print("\n开始下载全部图片...")
    stats = downloader.download_latest_from_api(count=None, force=False)

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
