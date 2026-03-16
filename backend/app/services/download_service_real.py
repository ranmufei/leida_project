"""
雷达图片下载服务 - 使用真实的中国气象局API

基于API.md文档实现的真实数据下载
"""
import os
import requests
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.radar_image import RadarImage
from app.core.database import SessionLocal


class RealRadarImageDownloader:
    """基于真实API的雷达图片下载器"""

    def __init__(self):
        """初始化下载器"""
        # 真实的API地址
        self.api_url = settings.CMA_API_URL

        self.max_retries = settings.DOWNLOAD_MAX_RETRIES
        self.timeout = settings.DOWNLOAD_TIMEOUT
        self.save_dir = Path(settings.RAW_DATA_DIR)
        self.save_dir.mkdir(parents=True, exist_ok=True)

        # CMA认证信息
        self.cookie = settings.CMA_COOKIE
        self.auth_token = settings.CMA_AUTH_TOKEN

        print(f"✅ 初始化真实雷达下载服务")
        print(f"📡 API地址: {self.api_url}")
        print(f"💾 保存目录: {self.save_dir}")
        print(f"🔐 认证状态: {'✅ 已配置' if (self.cookie or self.auth_token) else '⚠️ 未配置'}")

    def _get_auth_headers(self) -> Dict[str, str]:
        """
        构建带认证信息的请求头

        Returns:
            请求头字典
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://data.cma.cn/',
        }

        # 添加认证Token
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
            print(f"🔑 使用Authorization Token认证")

        return headers

    def _get_cookies(self) -> Dict[str, str]:
        """
        解析Cookie字符串为字典

        Returns:
            Cookie字典
        """
        if not self.cookie:
            return {}

        # 解析 "key1=value1; key2=value2" 格式
        cookies = {}
        for item in self.cookie.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                cookies[key.strip()] = value.strip()

        if cookies:
            print(f"🍪 使用Cookie认证，包含 {len(cookies)} 个Cookie")

        return cookies

    def fetch_available_images(self, limit: int = None) -> List[Dict]:
        """
        从API获取可用的雷达图片列表

        Args:
            limit: 获取数量限制，None表示获取全部

        Returns:
            图片信息列表
        """
        try:
            print(f"📡 正在获取雷达图片列表...")

            # 使用认证信息
            headers = self._get_auth_headers()
            cookies = self._get_cookies()

            response = requests.get(
                self.api_url,
                timeout=self.timeout,
                headers=headers,
                cookies=cookies
            )
            response.raise_for_status()

            data = response.json()

            if 'data' in data:
                images = data['data']
                total_count = len(images)

                # 如果没有limit或者limit大于总数，返回全部
                if limit is None or limit >= total_count:
                    print(f"✅ 获取到全部 {total_count} 张图片信息")
                    return images
                else:
                    print(f"✅ 获取到 {limit}/{total_count} 张图片信息")
                    return images[:limit]
            else:
                print(f"⚠️ API响应格式异常: {data.keys()}")
                return []

        except requests.exceptions.RequestException as e:
            print(f"❌ 获取图片列表失败: {e}")
            return []
        except Exception as e:
            print(f"❌ 解析响应失败: {e}")
            return []

    def parse_observation_time(self, time_str: str) -> datetime:
        """
        解析观测时间

        API返回的时间格式: "20260311000000" -> YYYYMMDDHHmmss
        """
        try:
            # 格式: 20260311000000
            # 解析为: 2026-03-11 00:00:00
            year = int(time_str[0:4])
            month = int(time_str[4:6])
            day = int(time_str[6:8])
            hour = int(time_str[8:10])
            minute = int(time_str[10:12])
            second = int(time_str[12:14])

            return datetime(year, month, day, hour, minute, second)
        except Exception as e:
            print(f"⚠️ 时间解析失败: {time_str} - {e}")
            return datetime.now()

    def download_from_api(
        self,
        image_info: Dict,
        force: bool = False
    ) -> Tuple[bool, str, Optional[str]]:
        """
        从API下载单张雷达图片

        Args:
            image_info: API返回的图片信息
            force: 是否强制重新下载

        Returns:
            (是否成功, 消息, 文件路径)
        """
        # 提取信息
        original_filename = image_info.get('c_FNAME', '')
        original_url = image_info.get('fileURL', '')
        observation_time_str = image_info.get('v_SHIJIAN', '')

        if not original_filename or not original_url:
            return False, "图片信息不完整", None

        # 解析观测时间
        observation_time = self.parse_observation_time(observation_time_str)

        # 断点续传：检查是否已下载
        if not force and self.is_file_downloaded(observation_time):
            return True, "文件已存在（断点续传）", None

        # 修改URL为HTTPS（按API文档要求）
        download_url = original_url.replace('http://', 'https://')

        # 使用原始文件名保存
        local_filename = original_filename
        file_path = self.save_dir / local_filename

        # 尝试下载
        for attempt in range(self.max_retries):
            try:
                print(f"📥 正在下载: {local_filename} (尝试 {attempt + 1}/{self.max_retries})")
                print(f"🌐 URL: {download_url}")

                # 准备认证信息
                headers = self._get_auth_headers()
                cookies = self._get_cookies()

                # 发送HTTP请求（携带认证信息）
                response = requests.get(
                    download_url,
                    stream=True,
                    timeout=self.timeout,
                    headers=headers,
                    cookies=cookies
                )
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
                    filename=local_filename,
                    original_filename=original_filename,
                    original_time_str=observation_time_str,
                    file_path=str(file_path),
                    observation_time=observation_time,
                    file_size=file_path.stat().st_size,
                    md5_hash=md5_hash,
                    download_url=download_url,
                    download_status='success'
                )

                print(f"✅ 下载成功: {local_filename} ({file_path.stat().st_size} bytes)")
                return True, "下载成功", str(file_path)

            except requests.exceptions.RequestException as e:
                print(f"❌ 下载失败 (尝试 {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    # 最后一次尝试失败，记录到数据库
                    self.save_to_database(
                        filename=local_filename,
                        original_filename=original_filename,
                        original_time_str=observation_time_str,
                        file_path=str(file_path),
                        observation_time=observation_time,
                        download_url=download_url,
                        download_status='failed',
                        error_message=str(e)
                    )
                    return False, f"下载失败: {str(e)}", None
                continue

            except Exception as e:
                print(f"❌ 未知错误: {e}")
                return False, f"未知错误: {str(e)}", None

        return False, "超过最大重试次数", None

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
        original_filename: str,
        file_path: str,
        observation_time: datetime,
        original_time_str: Optional[str] = None,
        file_size: Optional[int] = None,
        md5_hash: Optional[str] = None,
        download_url: Optional[str] = None,
        download_status: str = 'pending',
        error_message: Optional[str] = None
    ):
        """
        保存下载记录到数据库

        Args:
            filename: 本地文件名
            original_filename: 原始文件名
            file_path: 文件路径
            observation_time: 观测时间
            original_time_str: 原始时间字符串
            file_size: 文件大小
            md5_hash: MD5值
            download_url: 下载URL
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
                existing.filename = filename
                existing.original_filename = original_filename
                existing.original_time_str = original_time_str
                existing.file_path = file_path
                existing.file_size = file_size
                existing.download_url = download_url
                existing.download_time = datetime.now() if download_status == 'success' else None
                existing.download_status = download_status
                existing.retry_count += 1
                existing.md5_hash = md5_hash
                existing.error_message = error_message
            else:
                # 创建新记录
                radar_image = RadarImage(
                    filename=filename,
                    original_filename=original_filename,
                    original_time_str=original_time_str,
                    file_path=file_path,
                    file_size=file_size,
                    observation_time=observation_time,
                    download_url=download_url,
                    download_time=datetime.now() if download_status == 'success' else None,
                    download_status=download_status,
                    md5_hash=md5_hash,
                    error_message=error_message
                )
                db.add(radar_image)

            db.commit()

        except Exception as e:
            print(f"❌ 保存数据库失败: {e}")
            db.rollback()
        finally:
            db.close()

    def download_latest_from_api(self, count: int = None, force: bool = False) -> Dict[str, int]:
        """
        从真实API下载最新的N张图片（count=None表示下载全部）

        Args:
            count: 数量，None表示下载全部
            force: 是否强制重新下载

        Returns:
            下载统计
        """
        print(f"\n🚀 开始从真实API下载最新图片")
        if count is None:
            print(f"📅 下载模式: 全部下载")
        else:
            print(f"📅 下载数量: {count}")

        # 获取可用图片列表（如果count为None，获取全部）
        images = self.fetch_available_images(limit=count)

        if not images:
            print("❌ 未获取到图片列表")
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'skipped': 0
            }

        stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }

        # 下载图片（如果count指定，则限制数量）
        download_list = images if count is None else images[:count]

        # 下载图片
        for image_info in download_list:
            stats['total'] += 1

            success, message, _ = self.download_from_api(image_info, force)

            # 每2张图片之间间隔1秒，避免下载频率过快
            if stats['total'] < len(download_list):
                time.sleep(1)

            if success:
                if "已存在" in message:
                    stats['skipped'] += 1
                else:
                    stats['success'] += 1
            else:
                stats['failed'] += 1

        # 打印统计
        print(f"\n📊 下载完成统计:")
        print(f"  总计: {stats['total']}")
        print(f"  ✅ 成功: {stats['success']}")
        print(f"  ⏭️  跳过: {stats['skipped']}")
        print(f"  ❌ 失败: {stats['failed']}")

        return stats

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


# 导出类（保持向后兼容）
RadarImageDownloader = RealRadarImageDownloader
