#!/usr/bin/env python3
"""
测试CMA Cookie认证配置

使用方法:
1. 登录 https://data.cma.cn/
2. 获取Cookie（参考 docs/CMA_AUTHENTICATION_GUIDE.md）
3. 在下面填写Cookie
4. 运行此脚本: python3 test_cookie_auth.py
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.download_service_real import RealRadarImageDownloader


def test_with_cookie(cookie_string: str):
    """
    使用指定的Cookie测试下载

    Args:
        cookie_string: Cookie字符串，格式: "key1=value1; key2=value2"
    """
    print("=" * 70)
    print("🧪 CMA Cookie认证测试")
    print("=" * 70)

    # 临时设置Cookie
    from app.core.config import settings
    original_cookie = settings.CMA_COOKIE
    settings.CMA_COOKIE = cookie_string

    try:
        # 创建下载器
        print(f"\n📝 配置的Cookie:")
        print(f"   {cookie_string[:50]}..." if len(cookie_string) > 50 else f"   {cookie_string}")
        print(f"\n")

        downloader = RealRadarImageDownloader()

        # 测试获取图片列表
        print("\n" + "=" * 70)
        print("步骤1: 测试API访问（获取图片列表）")
        print("=" * 70)

        images = downloader.fetch_available_images(limit=1)

        if not images:
            print("❌ 失败: 无法获取图片列表")
            print("   可能原因:")
            print("   1. 网络连接问题")
            print("   2. API地址错误")
            return False

        print(f"✅ 成功获取到 {len(images)} 张图片信息")

        # 测试下载第一张图片
        print("\n" + "=" * 70)
        print("步骤2: 测试图片下载")
        print("=" * 70)

        image_info = images[0]
        success, message, file_path = downloader.download_from_api(image_info, force=True)

        print("\n" + "=" * 70)
        print("📊 测试结果")
        print("=" * 70)

        if success:
            print(f"✅ 测试成功!")
            print(f"   消息: {message}")
            print(f"   文件: {file_path}")

            if file_path and os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"   大小: {file_size} bytes ({file_size/1024:.2f} KB)")

            print("\n🎉 Cookie认证配置正确！")
            print("\n下一步:")
            print("1. 将此Cookie配置到 backend/.env 文件:")
            print(f"   CMA_COOKIE={cookie_string}")
            print("2. 或者配置到 backend/app/core/config.py")
            print("3. 重启后端服务")
            return True

        else:
            print(f"❌ 测试失败!")
            print(f"   消息: {message}")
            print("\n可能的原因:")
            print("1. Cookie格式错误（检查是否有多余的空格或引号）")
            print("2. Cookie已过期（重新登录获取）")
            print("3. Cookie不完整（可能需要更多的Cookie字段）")
            print("4. IP地址限制（CMA可能绑定Cookie到特定IP）")
            return False

    except Exception as e:
        print(f"\n❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 恢复原始配置
        settings.CMA_COOKIE = original_cookie


def main():
    """主函数"""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                   CMA Cookie认证配置测试工具                        ║
╚════════════════════════════════════════════════════════════════════╝

此工具用于测试从浏览器获取的Cookie是否能成功下载CMA雷达图片。

准备工作:
1. 在浏览器中登录 https://data.cma.cn/
2. 打开开发者工具（F12）
3. 查看Application → Cookies → https://data.cma.cn
4. 复制关键Cookie（JSESSIONID, auth_token等）

参考文档: docs/CMA_AUTHENTICATION_GUIDE.md
""")

    # 从用户输入获取Cookie
    print("\n请粘贴您的Cookie字符串:")
    print("(格式示例: JSESSIONID=abc123; auth_token=xyz789)")
    print("输入 'quit' 退出\n")

    cookie_input = input("Cookie: ").strip()

    if cookie_input.lower() == 'quit':
        print("退出测试")
        return

    if not cookie_input:
        print("❌ Cookie不能为空")
        return

    # 运行测试
    print("\n")
    success = test_with_cookie(cookie_input)

    print("\n" + "=" * 70)
    if success:
        print("✅ 测试完成 - Cookie可用")
    else:
        print("❌ 测试失败 - Cookie不可用")
        print("\n建议:")
        print("1. 检查Cookie是否正确复制")
        print("2. 尝试使用不同的Cookie（如JSESSIONID）")
        print("3. 重新登录CMA网站获取新的Cookie")
    print("=" * 70)


if __name__ == "__main__":
    main()
