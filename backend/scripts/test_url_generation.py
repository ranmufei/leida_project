#!/usr/bin/env python3
"""
测试URL生成逻辑
"""
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.download_service_nmc import NMCRadarImageDownloader


def test_url_generation():
    """测试URL生成"""
    print("=" * 80)
    print("测试URL生成逻辑")
    print("=" * 80)

    downloader = NMCRadarImageDownloader()

    # 测试用例：北京时间 -> UTC时间 -> URL
    test_cases = [
        ("2026-03-15 16:42:00", "2026-03-15 08:42:00", "20260315084200000"),
        ("2026-03-15 18:42:00", "2026-03-15 10:42:00", "20260315104200000"),
        ("2026-03-15 00:00:00", "2026-03-14 16:00:00", "20260314160000000"),
        ("2026-03-15 16:45:00", "2026-03-15 08:42:00", "20260315084200000"),  # 应该对齐到 08:42
    ]

    print(f"\n{'北京时间':<25} -> {'UTC时间':<25} -> {'时间戳':<20}")
    print("-" * 80)

    for bj_str, expected_utc_str, expected_timestamp in test_cases:
        bj_time = datetime.strptime(bj_str, "%Y-%m-%d %H:%M:%S")

        # 转换为UTC
        utc_time = downloader.beijing_to_utc(bj_time)

        # 对齐到6分钟边界
        utc_aligned = downloader.align_to_6_minutes(utc_time)

        # 生成URL
        url = downloader.build_url(utc_aligned)

        # 提取时间戳
        timestamp = url.split("_")[-1].split(".")[0]

        actual_utc_str = utc_aligned.strftime("%Y-%m-%d %H:%M:%S")
        status = "✅" if timestamp == expected_timestamp else "❌"

        print(f"{bj_str:<25} -> {actual_utc_str:<25} -> {timestamp:<20} {status}")

        if timestamp != expected_timestamp:
            print(f"   预期: {expected_timestamp}")


def test_time_alignment():
    """测试时间对齐"""
    print("\n" + "=" * 80)
    print("测试时间对齐到6分钟边界")
    print("=" * 80)

    downloader = NMCRadarImageDownloader()

    test_cases = [
        "2026-03-15 08:00:00",
        "2026-03-15 08:01:00",
        "2026-03-15 08:02:00",
        "2026-03-15 08:03:00",
        "2026-03-15 08:04:00",
        "2026-03-15 08:05:00",
        "2026-03-15 08:06:00",
        "2026-03-15 08:07:00",
        "2026-03-15 08:42:00",
        "2026-03-15 08:45:00",
        "2026-03-15 08:48:00",
        "2026-03-15 08:54:00",
        "2026-03-15 09:00:00",
    ]

    print(f"\n{'输入时间':<25} -> {'对齐后时间':<25} -> {'分钟是否为6的倍数'}")
    print("-" * 80)

    for time_str in test_cases:
        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        aligned = downloader.align_to_6_minutes(dt)
        aligned_str = aligned.strftime("%Y-%m-%d %H:%M:%S")
        is_valid = aligned.minute % 6 == 0
        status = "✅" if is_valid else "❌"
        print(f"{time_str:<25} -> {aligned_str:<25} {status}")


def test_generate_time_points():
    """测试生成时间点"""
    print("\n" + "=" * 80)
    print("测试生成时间点（6分钟间隔）")
    print("=" * 80)

    downloader = NMCRadarImageDownloader()

    # 测试：生成1小时内的所有时间点
    start = datetime.strptime("2026-03-15 00:00:00", "%Y-%m-%d %H:%M:%S")
    end = datetime.strptime("2026-03-15 01:00:00", "%Y-%m-%d %H:%M:%S")

    time_points = downloader.generate_time_points(start, end, use_beijing_time=True)

    print(f"\n时间范围: {start} ~ {end}")
    print(f"生成 {len(time_points)} 个时间点")
    print()

    print(f"{'序号':<5} {'北京时间':<25} {'UTC时间':<25} {'时间戳':<20}")
    print("-" * 80)

    for i, bj_time in enumerate(time_points[:20], 1):  # 只显示前20个
        utc_time = downloader.beijing_to_utc(bj_time)
        url = downloader.build_url(utc_time)
        timestamp = url.split("_")[-1].split(".")[0]

        print(f"{i:<5} {bj_time.strftime('%Y-%m-%d %H:%M:%S'):<25} {utc_time.strftime('%Y-%m-%d %H:%M:%S'):<25} {timestamp:<20}")


def test_actual_url():
    """测试实际可访问的URL"""
    print("\n" + "=" * 80)
    print("测试实际URL")
    print("=" * 80)

    downloader = NMCRadarImageDownloader()

    # 使用用户提供的实际时间
    bj_time = datetime.strptime("2026-03-15 18:42:00", "%Y-%m-%d %H:%M:%S")
    utc_time = downloader.beijing_to_utc(bj_time)
    utc_aligned = downloader.align_to_6_minutes(utc_time)

    url = downloader.build_url(utc_aligned)

    print(f"\n北京时间: {bj_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"UTC时间: {utc_aligned.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n生成的URL:")
    print(f"{url}")

    # 预期的URL
    expected_url = "https://image.nmc.cn/product/2026/03/15/RDCP/SEVP_AOC_RDCP_SLDAS3_ECREF_ACHN_L88_PI_20260315104200000.PNG"
    print(f"\n预期的URL:")
    print(f"{expected_url}")

    if url == expected_url:
        print(f"\n✅ URL匹配！")
    else:
        print(f"\n❌ URL不匹配")
        print(f"\n差异:")
        print(f"生成的: {url}")
        print(f"预期:   {expected_url}")


if __name__ == "__main__":
    test_url_generation()
    test_time_alignment()
    test_generate_time_points()
    test_actual_url()
