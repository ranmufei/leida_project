"""
雷达图片下载服务 - 使用NMC直接URL方式

URL格式: https://image.nmc.cn/product/YYYY/MM/DD/RDCP/SEVP_AOC_RDCP_SLDAS3_ECREF_ACHN_L88_PI_YYYYMMDDHHmmssSSS.PNG

注意：URL中的时间戳是UTC时间，需要转换为北京时间（UTC+8）存储
图片更新间隔：6分钟
"""
import os
import requests
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.radar_image import RadarImage
from app.core.database import SessionLocal


class NMCRadarImageDownloader:
    """基于NMC直接URL的雷达图片下载器"""

    # URL固定部分
    BASE_URL = "https://image.nmc.cn/product"
    PRODUCT_DIR = "RDCP"
    FILENAME_PREFIX = "SEVP_AOC_RDCP_SLDAS3_ECREF_ACHN_L88_PI_"

    # 图片更新间隔（分钟）
    INTERVAL_MINUTES = 6

    def __init__(self):
        """初始化下载器"""
        self.max_retries = settings.DOWNLOAD_MAX_RETRIES
        self.timeout = settings.DOWNLOAD_TIMEOUT
        self.save_dir = Path(settings.RAW_DATA_DIR)
        self.save_dir.mkdir(parents=True, exist_ok=True)

        print(f"✅ 初始化NMC雷达下载服务")
        print(f"📡 基础URL: {self.BASE_URL}")
        print(f"💾 保存目录: {self.save_dir}")
        print(f"⏰ 更新间隔: {self.INTERVAL_MINUTES} 分钟")

    def build_url(self, utc_time: datetime) -> str:
        """
        根据UTC时间构建图片URL

        Args:
            utc_time: UTC时间

        Returns:
            完整的图片URL
        """
        # URL中的日期路径: YYYY/MM/DD
        date_path = utc_time.strftime("%Y/%m/%d")

        # URL中的时间戳: YYYYMMDDHHmmssSSS (17位数字)
        # 格式: 20260315223000000 (YYYYMMDDHHmmssSSS)
        timestamp = utc_time.strftime("%Y%m%d%H%M%S") + "000"

        # 构建完整URL
        url = f"{self.BASE_URL}/{date_path}/{self.PRODUCT_DIR}/{self.FILENAME_PREFIX}{timestamp}.PNG"

        return url

    def utc_to_beijing(self, utc_time: datetime) -> datetime:
        """
        将UTC时间转换为北京时间

        Args:
            utc_time: UTC时间

        Returns:
            北京时间
        """
        return utc_time + timedelta(hours=8)

    def beijing_to_utc(self, beijing_time: datetime) -> datetime:
        """
        将北京时间转换为UTC时间

        Args:
            beijing_time: 北京时间

        Returns:
            UTC时间
        """
        return beijing_time - timedelta(hours=8)

    def generate_time_points(
        self,
        start_time: datetime,
        end_time: datetime,
        use_beijing_time: bool = True
    ) -> List[datetime]:
        """
        生成指定时间范围内的时间点列表（6分钟间隔）

        Args:
            start_time: 开始时间
            end_time: 结束时间
            use_beijing_time: 输入时间是否为北京时间（默认True）

        Returns:
            时间点列表（北京时间）
        """
        # 如果输入是北京时间，转换为UTC来计算
        if use_beijing_time:
            start_utc = self.beijing_to_utc(start_time)
            end_utc = self.beijing_to_utc(end_time)
        else:
            start_utc = start_time
            end_utc = end_time

        # 生成UTC时间点
        time_points = []
        current = start_utc
        while current <= end_utc:
            # 转换回北京时间存储
            beijing_time = self.utc_to_beijing(current)
            time_points.append(beijing_time)
            current += timedelta(minutes=self.INTERVAL_MINUTES)

        return time_points

    def is_file_downloaded(self, beijing_time: datetime) -> bool:
        """
        检查指定时间的图片是否已下载

        Args:
            beijing_time: 北京时间

        Returns:
            是否已下载
        """
        db = SessionLocal()
        try:
            existing = db.query(RadarImage).filter(
                RadarImage.observation_time == beijing_time,
                RadarImage.download_status == 'success'
            ).first()
            return existing is not None
        finally:
            db.close()

    def download_image(
        self,
        beijing_time: datetime,
        force: bool = False
    ) -> Tuple[bool, str, Optional[str]]:
        """
        下载指定时间的雷达图片

        Args:
            beijing_time: 北京时间
            force: 是否强制重新下载

        Returns:
            (是否成功, 消息, 文件路径)
        """
        # 转换为UTC时间构造URL
        utc_time = self.beijing_to_utc(beijing_time)
        url = self.build_url(utc_time)

        # 检查是否已下载
        if not force and self.is_file_downloaded(beijing_time):
            return True, "图片已存在", None

        # 构造本地文件路径
        filename = beijing_time.strftime("radar_%Y%m%d_%H%M%S.png")
        local_path = self.save_dir / filename

        print(f"⬇️  下载中: {beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
        print(f"🌐 URL: {url}")

        # 尝试下载
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    timeout=self.timeout,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                    }
                )
                response.raise_for_status()

                # 保存文件
                with open(local_path, 'wb') as f:
                    f.write(response.content)

                # 保存到数据库
                self._save_to_db(
                    beijing_time=beijing_time,
                    url=url,
                    file_path=str(local_path),
                    status='success'
                )

                print(f"✅ 下载成功: {filename}")
                return True, "下载成功", str(local_path)

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    print(f"⚠️  下载失败，重试中 ({attempt + 1}/{self.max_retries}): {e}")
                    continue
                else:
                    print(f"❌ 下载失败: {e}")

                    # 保存失败记录
                    self._save_to_db(
                        beijing_time=beijing_time,
                        url=url,
                        file_path=None,
                        status='failed',
                        error_message=str(e)
                    )

                    return False, f"下载失败: {e}", None

    def _save_to_db(
        self,
        beijing_time: datetime,
        url: str,
        file_path: Optional[str],
        status: str,
        error_message: str = None
    ):
        """保存下载记录到数据库"""
        db = SessionLocal()
        try:
            # 查找是否已存在
            existing = db.query(RadarImage).filter(
                RadarImage.observation_time == beijing_time
            ).first()

            if existing:
                # 更新现有记录
                existing.download_url = url
                existing.file_path = file_path
                existing.download_time = datetime.now() if status == 'success' else None
                existing.download_status = status
                existing.error_message = error_message
            else:
                # 创建新记录
                radar_image = RadarImage(
                    observation_time=beijing_time,
                    download_url=url,
                    file_path=file_path,
                    download_time=datetime.now() if status == 'success' else None,
                    download_status=status,
                    error_message=error_message
                )
                db.add(radar_image)

            db.commit()
        except Exception as e:
            db.rollback()
            print(f"⚠️  数据库保存失败: {e}")
        finally:
            db.close()

    def download_range(
        self,
        start_time: datetime,
        end_time: datetime,
        force: bool = False,
        use_beijing_time: bool = True
    ) -> Dict[str, int]:
        """
        下载指定时间范围的雷达图片

        Args:
            start_time: 开始时间
            end_time: 结束时间
            force: 是否强制重新下载
            use_beijing_time: 输入时间是否为北京时间（默认True）

        Returns:
            下载统计信息
        """
        # 生成时间点
        time_points = self.generate_time_points(start_time, end_time, use_beijing_time)

        print(f"📅 时间范围: {start_time} ~ {end_time}")
        print(f"📊 共 {len(time_points)} 个时间点")

        stats = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}

        for beijing_time in time_points:
            stats['total'] += 1

            success, message, _ = self.download_image(beijing_time, force)

            if success:
                if message == "图片已存在":
                    stats['skipped'] += 1
                else:
                    stats['success'] += 1
            else:
                stats['failed'] += 1

        print(f"\n📊 下载完成:")
        print(f"   总计: {stats['total']}")
        print(f"   成功: {stats['success']}")
        print(f"   跳过: {stats['skipped']}")
        print(f"   失败: {stats['failed']}")

        return stats

    def download_latest(self, count: int = 1, force: bool = False) -> Dict[str, int]:
        """
        下载最新的N张雷达图片

        Args:
            count: 下载数量
            force: 是否强制重新下载

        Returns:
            下载统计信息
        """
        # 从当前时间往前推
        now = datetime.now()

        # 计算起始时间
        start_time = now - timedelta(minutes=count * self.INTERVAL_MINUTES)

        return self.download_range(start_time, now, force, use_beijing_time=True)

    def download_latest_from_api(self, count: int = None, force: bool = False) -> Dict[str, int]:
        """
        兼容接口：下载最新图片

        Args:
            count: 下载数量，None表示只下载最新一张
            force: 是否强制重新下载

        Returns:
            下载统计信息
        """
        if count is None:
            count = 1
        return self.download_latest(count, force)

    def get_download_statistics(self) -> Dict:
        """
        获取下载统计信息

        Returns:
            统计信息字典
        """
        db = SessionLocal()
        try:
            total = db.query(RadarImage).count()
            success = db.query(RadarImage).filter(RadarImage.download_status == 'success').count()
            failed = db.query(RadarImage).filter(RadarImage.download_status == 'failed').count()
            pending = db.query(RadarImage).filter(RadarImage.download_status == 'pending').count()

            # 获取最新成功下载的图片
            latest = db.query(RadarImage).filter(
                RadarImage.download_status == 'success'
            ).order_by(RadarImage.observation_time.desc()).first()

            return {
                'total': total,
                'success': success,
                'failed': failed,
                'pending': pending,
                'latest_download_time': latest.observation_time if latest else None
            }
        finally:
            db.close()


# 导出别名，保持与旧接口兼容
RadarImageDownloader = NMCRadarImageDownloader
