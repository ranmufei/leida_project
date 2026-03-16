#!/usr/bin/env python3
"""
下载所有雷达图片（简化版）
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.download_service_real import RealRadarImageDownloader

def main():
    print("=" * 60)
    print("🚀 开始下载全部雷达图片")
    print("=" * 60)

    # 初始化下载器
    downloader = RealRadarImageDownloader()

    # 下载全部图片（count=None表示下载全部）
    print(f"\n📥 下载模式: 全部下载（每张图片间隔1秒）")
    stats = downloader.download_latest_from_api(count=None, force=False)

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
        print(f"  1. Cookie已过期")
        print(f"  2. 网络连接不稳定")
        print(f"  3. 图片文件已被删除")

if __name__ == "__main__":
    main()
