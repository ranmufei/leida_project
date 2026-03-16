#!/usr/bin/env python3
"""
测试单张图片下载 - 用于诊断下载问题
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.download_service_real import RealRadarImageDownloader
from app.core.config import settings

def main():
    print("=" * 60)
    print("🧪 测试单张图片下载功能")
    print("=" * 60)

    # 显示配置
    print(f"\n📋 当前配置:")
    print(f"  API地址: {settings.CMA_API_URL}")
    print(f"  Cookie配置: {'✅ 已配置' if settings.CMA_COOKIE else '❌ 未配置'}")
    print(f"  Token配置: {'✅ 已配置' if settings.CMA_AUTH_TOKEN else '❌ 未配置'}")
    print(f"  Cookie内容: {settings.CMA_COOKIE[:100]}..." if settings.CMA_COOKIE else "  Cookie内容: (空)")

    # 初始化下载器
    downloader = RealRadarImageDownloader()

    # 获取一张图片信息
    print(f"\n📡 获取图片列表...")
    images = downloader.fetch_available_images(limit=1)

    if not images:
        print("❌ 无法获取图片列表")
        return

    print(f"✅ 成功获取图片列表，共 {len(images)} 张")

    # 显示第一张图片信息
    first_image = images[0]
    print(f"\n📸 第一张图片信息:")
    print(f"  文件名: {first_image.get('c_FNAME')}")
    print(f"  时间: {first_image.get('v_SHIJIAN')}")
    print(f"  URL: {first_image.get('fileURL')}")

    # 尝试下载
    print(f"\n🚀 开始下载测试...")
    success, message, file_path = downloader.download_from_api(first_image, force=True)

    print(f"\n📊 下载结果:")
    print(f"  成功: {success}")
    print(f"  消息: {message}")
    print(f"  路径: {file_path}")

    if success:
        print(f"\n✅ 下载测试成功！")
    else:
        print(f"\n❌ 下载测试失败")
        print(f"\n💡 可能的原因:")
        print(f"  1. Cookie已过期，需要重新登录 https://data.cma.cn/")
        print(f"  2. 网络连接问题")
        print(f"  3. API地址变更")
        print(f"\n🔧 建议操作:")
        print(f"  1. 访问 https://data.cma.cn/ 并登录")
        print(f"  2. 打开浏览器开发者工具 (F12)")
        print(f"  3. 刷新页面，找到 Network 标签")
        print(f"  4. 点击任意请求，查看 Request Headers")
        print(f"  5. 复制 Cookie 字段的值")
        print(f"  6. 更新 backend/.env 文件中的 CMA_COOKIE")

if __name__ == "__main__":
    main()
