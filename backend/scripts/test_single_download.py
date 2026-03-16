#!/usr/bin/env python3
"""
测试单张图片下载 - 用于诊断下载问题（NMC直接URL方式）
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.download_service_nmc import NMCRadarImageDownloader


def main():
    print("=" * 60)
    print("🧪 测试单张图片下载功能（NMC直接URL）")
    print("=" * 60)

    # 初始化下载器
    downloader = NMCRadarImageDownloader()

    # 测试下载当前时间的一张图片
    test_time = datetime.now()

    print(f"\n📅 测试时间（北京时间）: {test_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 显示生成的URL
    utc_time = downloader.beijing_to_utc(test_time)
    url = downloader.build_url(utc_time)
    print(f"\n🌐 生成的URL: {url}")

    # 尝试下载
    print(f"\n🚀 开始下载测试...")
    success, message, file_path = downloader.download_image(test_time, force=True)

    print(f"\n📊 下载结果:")
    print(f"  成功: {success}")
    print(f"  消息: {message}")
    print(f"  路径: {file_path}")

    if success:
        print(f"\n✅ 下载测试成功！")
        print(f"\n💡 说明:")
        print(f"  - URL中的时间戳是UTC时间")
        print(f"  - 存储到数据库的时间是北京时间（UTC+8）")
        print(f"  - 图片每6分钟更新一次")
    else:
        print(f"\n❌ 下载测试失败")
        print(f"\n💡 可能的原因:")
        print(f"  1. 该时间点暂无图片数据")
        print(f"  2. 网络连接问题")
        print(f"  3. 图片URL格式已变更")


def test_time_conversion():
    """测试时间转换功能"""
    print("\n" + "=" * 60)
    print("🕐 测试时间转换功能")
    print("=" * 60)

    downloader = NMCRadarImageDownloader()

    # 测试用例
    test_cases = [
        ("2026-03-15 22:30:00", "2026-03-16 06:30:00"),
        ("2026-03-15 00:00:00", "2026-03-15 08:00:00"),
        ("2026-03-15 16:00:00", "2026-03-16 00:00:00"),
    ]

    print(f"\n{'UTC时间':<25} -> {'北京时间':<25}")
    print("-" * 51)

    for utc_str, expected_beijing_str in test_cases:
        utc_time = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S")
        beijing_time = downloader.utc_to_beijing(utc_time)
        actual_beijing_str = beijing_time.strftime("%Y-%m-%d %H:%M:%S")

        status = "✅" if actual_beijing_str == expected_beijing_str else "❌"
        print(f"{utc_str:<25} -> {actual_beijing_str:<25} {status}")


if __name__ == "__main__":
    main()
    test_time_conversion()
