#!/usr/bin/env python3
"""
生成测试雷达图片数据

用于演示下载功能，生成模拟的雷达图片文件
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def create_test_images(count=10):
    """
    创建测试雷达图片

    Args:
        count: 生成图片数量
    """
    from PIL import Image, ImageDraw, ImageFont

    # 数据目录
    raw_dir = Path("/Users/ranmufei/2026/leida_project/data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    print(f"📁 数据目录: {raw_dir}")
    print(f"🎨 开始生成 {count} 张测试雷达图片...\n")

    for i in range(count):
        # 计算时间（每6分钟一张）
        observation_time = datetime.now() - timedelta(minutes=i*6)
        timestamp = observation_time.strftime('%Y%m%d%H%M%S')
        filename = f"radar_{timestamp}.png"
        filepath = raw_dir / filename

        # 创建图片
        img = Image.new('RGB', (800, 600), color='#f0f0f0')
        draw = ImageDraw.Draw(img)

        # 绘制模拟雷达图
        # 1. 绘制圆形背景
        for j in range(5, 0, -1):
            radius = 50 * j
            color = f"#{j*40:02x}{j*40:02x}ff"  # 蓝色渐变
            draw.ellipse([400-radius, 300-radius, 400+radius, 300+radius],
                        outline=color, width=2)

        # 2. 绘制中心点
        draw.ellipse([395, 295, 405, 305], fill='red')

        # 3. 添加文本
        title = f"雷达回波图 - 测试数据 {i+1}"
        time_text = observation_time.strftime('%Y-%m-%d %H:%M:%S')
        location = "站点: 北京 (BJ001)"

        # 尝试使用系统字体
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
            font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()

        draw.text((400, 50), title, fill='black', anchor='mm', font=font_large)
        draw.text((400, 100), time_text, fill='#333', anchor='mm', font=font_medium)
        draw.text((400, 130), location, fill='#666', anchor='mm', font=font_medium)

        # 4. 添加模拟dBZ值
        dbz_value = 30 + i * 2
        dbz_text = f"模拟dBZ值: {dbz_value} dBZ"
        draw.text((400, 550), dbz_text, fill='blue', anchor='mm', font=font_medium)

        # 保存图片
        img.save(filepath)

        # 保存到数据库
        try:
            from app.core.database import SessionLocal
            from app.models.radar_image import RadarImage

            db = SessionLocal()
            radar_image = RadarImage(
                filename=filename,
                file_path=str(filepath),
                file_size=filepath.stat().st_size,
                observation_time=observation_time,
                download_time=datetime.now(),
                download_status='success',
                md5_hash=f"test_md5_{timestamp}"
            )
            db.add(radar_image)
            db.commit()
            db.close()

            print(f"✅ [{i+1}/{count}] {filename} ({filepath.stat().st_size} bytes)")
        except Exception as e:
            print(f"⚠️  [{i+1}/{count}] {filename} - 保存数据库失败: {e}")

    print(f"\n🎉 测试数据生成完成！")
    print(f"📊 目录: {raw_dir}")
    print(f"📈 共生成 {count} 张雷达图片")

    # 列出文件
    print(f"\n📁 文件列表:")
    files = sorted(raw_dir.glob("*.png"), reverse=True)
    for f in files[:5]:  # 显示最新的5个
        print(f"  - {f.name} ({f.stat().st_size} bytes)")
    if len(files) > 5:
        print(f"  ... 还有 {len(files)-5} 个文件")

def cleanup_test_images():
    """清理测试数据"""
    raw_dir = Path("/Users/ranmufei/2026/leida_project/data/raw")

    print(f"🧹 清理测试数据...")

    # 删除文件
    count = 0
    for f in raw_dir.glob("radar_*.png"):
        f.unlink()
        count += 1

    print(f"✅ 已删除 {count} 个测试文件")

    # 清理数据库
    try:
        from app.core.database import SessionLocal
        from app.models.radar_image import RadarImage

        db = SessionLocal()
        deleted = db.query(RadarImage).filter(
            RadarImage.filename.like('radar_%')
        ).delete()
        db.commit()
        db.close()

        print(f"✅ 已删除数据库中 {deleted} 条记录")
    except Exception as e:
        print(f"⚠️  清理数据库失败: {e}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='生成测试雷达图片数据')
    parser.add_argument('action', choices=['generate', 'cleanup'],
                       help='操作类型: generate(生成) 或 cleanup(清理)')
    parser.add_argument('--count', type=int, default=10,
                       help='生成图片数量 (默认: 10)')

    args = parser.parse_args()

    if args.action == 'generate':
        create_test_images(args.count)
    elif args.action == 'cleanup':
        cleanup_test_images()
