"""
雷达图片下载服务

实现自动下载、断点续传、失败重试等功能
"""
import os
import requests
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.radar_image import RadarImage
from app.core.database import SessionLocal


class RadarImageDownloader:
    """雷达图片下载器"""

    def __init__(self):
        """初始化下载器"""
        self.base_url = settings.DOWNLOAD_BASE_URL
        self.max_retries = settings.DOWNLOAD_MAX_RETRIES
        self.timeout = settings.DOWNLOAD_TIMEOUT
        self.save_dir = Path(settings.RAW_DATA_DIR)
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def build_download_url(self, observation_time: datetime) -> str:
        """
        构建下载URL

        Args:
            observation_time: 观测时间

        Returns:
            下载URL
        """
        # 格式: https://image.data.cma.cn/vis/RAD__B0_CR/20260310/Z_RADA_C_BABJ_20260310160658_P_DOR_ACHN_CREF_20260310_160000.png
        date_str = observation_time.strftime('%Y%m%d')
        time_str = observation_time.strftime('%Y%m%d%H%M%S')
        filename = f"Z_RADA_C_BABJ_{time_str}_P_DOR_ACHN_CREF_{date_str}_{observation_time.strftime('%H%M%S')}.png"

        return f"{self.base_url}/{date_str}/{filename}"

    def build_filename(self, observation_time: datetime) -> str:
        """
        构建保存文件名

        Args:
            observation_time: 观测时间

        Returns:
            文件名
        """
        time_str = observation_time.strftime('%Y%m%d%H%M%S')
        return f"radar_{time_str}.png"

    def is_file_downloaded(self, observation_time: datetime) -> bool:
        """
        检查文件是否已下载

        Args:
            observation_time: 观测时间

        Returns:
            是否已下载
        """
        db = SessionLocal()
        try:
            existing = db.query(RadarImage).filter(
                RadarImage.observation_time == observation_time,
                RadarImage.download_status == 'success'
            ).first()
            return existing is not None
        finally:
            db.close()

    def download_image(
        self,
        observation_time: datetime,
        force: bool = False
    ) -> Tuple[bool, str, Optional[str]]:
        """
        下载单张雷达图片

        Args:
            observation_time: 观测时间
            force: 是否强制重新下载

        Returns:
            (是否成功, 消息, 文件路径)
        """
        # 断点续传：检查是否已下载
        if not force and self.is_file_downloaded(observation_time):
            return True, "文件已存在（断点续传）", None

        # 构建URL和文件路径
        url = self.build_download_url(observation_time)
        filename = self.build_filename(observation_time)
        file_path = self.save_dir / filename

        # 尝试下载（支持重试）
        for attempt in range(self.max_retries):
            try:
                print(f"📥 正在下载: {filename} (尝试 {attempt + 1}/{self.max_retries})")

                # 发送HTTP请求
                response = requests.get(url, stream=True, timeout=self.timeout)
                response.raise_for_status()

                # 保存文件
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                # 计算MD5
                md5_hash = self.calculate_md5(file_path)

                # 保存到数据库
                self.save_to_database(
                    filename=str(filename),
                    file_path=str(file_path),
                    observation_time=observation_time,
                    file_size=file_path.stat().st_size,
                    md5_hash=md5_hash,
                    download_status='success'
                )

                print(f"✅ 下载成功: {filename}")
                return True, "下载成功", str(file_path)

            except requests.exceptions.RequestException as e:
                print(f"❌ 下载失败 (尝试 {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    # 最后一次尝试失败，记录到数据库
                    self.save_to_database(
                        filename=str(filename),
                        file_path=str(file_path),
                        observation_time=observation_time,
                        download_status='failed',
                        error_message=str(e)
                    )
                    return False, f"下载失败: {str(e)}", None
                continue

            except Exception as e:
                print(f"❌ 未知错误: {e}")
                return False, f"未知错误: {str(e)}", None

        return False, "超过最大重试次数", None

    def calculate_md5(self, file_path: Path) -> str:
        """
        计算文件MD5值

        Args:
            file_path: 文件路径

        Returns:
            MD5哈希值
        """
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5.update(chunk)
        return md5.hexdigest()

    def save_to_database(
        self,
        filename: str,
        file_path: str,
        observation_time: datetime,
        file_size: Optional[int] = None,
        md5_hash: Optional[str] = None,
        download_status: str = 'pending',
        error_message: Optional[str] = None
    ):
        """
        保存下载记录到数据库

        Args:
            filename: 文件名
            file_path: 文件路径
            observation_time: 观测时间
            file_size: 文件大小
            md5_hash: MD5值
            download_status: 下载状态
            error_message: 错误信息
        """
        db = SessionLocal()
        try:
            # 检查是否已存在
            existing = db.query(RadarImage).filter(
                RadarImage.observation_time == observation_time
            ).first()

            if existing:
                # 更新现有记录
                existing.file_path = file_path
                existing.file_size = file_size
                existing.download_time = datetime.now()
                existing.download_status = download_status
                existing.retry_count += 1
                existing.md5_hash = md5_hash
            else:
                # 创建新记录
                radar_image = RadarImage(
                    filename=filename,
                    file_path=file_path,
                    file_size=file_size,
                    observation_time=observation_time,
                    download_time=datetime.now() if download_status == 'success' else None,
                    download_status=download_status,
                    md5_hash=md5_hash
                )
                db.add(radar_image)

            db.commit()

        except Exception as e:
            print(f"❌ 保存数据库失败: {e}")
            db.rollback()
        finally:
            db.close()

    def download_range(
        self,
        start_time: datetime,
        end_time: datetime,
        interval_minutes: int = 6,
        force: bool = False
    ) -> Dict[str, int]:
        """
        批量下载指定时间范围的图片

        Args:
            start_time: 开始时间
            end_time: 结束时间
            interval_minutes: 时间间隔（分钟）
            force: 是否强制重新下载

        Returns:
            下载统计
        """
        print(f"\n🚀 开始批量下载")
        print(f"📅 时间范围: {start_time} ~ {end_time}")
        print(f"⏱️  时间间隔: {interval_minutes}分钟")

        stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }

        current_time = start_time
        while current_time <= end_time:
            stats['total'] += 1

            success, message, _ = self.download_image(current_time, force)

            if success:
                if "已存在" in message:
                    stats['skipped'] += 1
                else:
                    stats['success'] += 1
            else:
                stats['failed'] += 1

            # 移动到下一个时间点
            current_time += timedelta(minutes=interval_minutes)

        # 打印统计
        print(f"\n📊 下载完成统计:")
        print(f"  总计: {stats['total']}")
        print(f"  ✅ 成功: {stats['success']}")
        print(f"  ⏭️  跳过: {stats['skipped']}")
        print(f"  ❌ 失败: {stats['failed']}")

        return stats

    def download_latest(self, count: int = 1, force: bool = False) -> Dict[str, int]:
        """
        下载最新的N张图片

        Args:
            count: 数量
            force: 是否强制重新下载

        Returns:
            下载统计
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=count * 6)

        return self.download_range(start_time, end_time, force=force)

    def cleanup_failed_downloads(self, max_age_hours: int = 24):
        """
        清理失败的下载记录

        Args:
            max_age_hours: 最大保留时间（小时）
        """
        db = SessionLocal()
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

            deleted = db.query(RadarImage).filter(
                RadarImage.download_status == 'failed',
                RadarImage.created_at < cutoff_time
            ).delete()

            db.commit()
            print(f"🧹 清理了 {deleted} 条失败的下载记录")

        except Exception as e:
            print(f"❌ 清理失败: {e}")
            db.rollback()
        finally:
            db.close()

    def get_download_statistics(self) -> Dict:
        """
        获取下载统计信息

        Returns:
            统计信息
        """
        db = SessionLocal()
        try:
            total = db.query(RadarImage).count()
            success = db.query(RadarImage).filter(RadarImage.download_status == 'success').count()
            failed = db.query(RadarImage).filter(RadarImage.download_status == 'failed').count()
            pending = db.query(RadarImage).filter(RadarImage.download_status == 'pending').count()

            # 获取最新下载时间
            latest = db.query(RadarImage).filter(
                RadarImage.download_status == 'success'
            ).order_by(RadarImage.observation_time.desc()).first()

            return {
                'total': total,
                'success': success,
                'failed': failed,
                'pending': pending,
                'success_rate': success / total if total > 0 else 0,
                'latest_download_time': latest.observation_time if latest else None
            }

        finally:
            db.close()
