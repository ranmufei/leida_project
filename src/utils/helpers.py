"""
工具函数模块

提供各种辅助功能，如文件下载、数据处理、日志记录等
"""

import os
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import hashlib


def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件路径
        level: 日志级别

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 清除现有的处理器
    logger.handlers.clear()

    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def download_file(url: str, output_path: str, timeout: int = 30) -> bool:
    """
    下载文件

    Args:
        url: 文件URL
        output_path: 输出文件路径
        timeout: 超时时间(秒)

    Returns:
        是否成功下载
    """
    try:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 下载文件
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()

        # 保存文件
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return True

    except Exception as e:
        print(f"下载文件失败: {e}")
        return False


def download_radar_images(start_time: datetime,
                         end_time: datetime,
                         output_dir: str,
                         base_url: str = "https://image.data.cma.cn/vis/RAD__B0_CR",
                         interval_minutes: int = 6,
                         logger: Optional[logging.Logger] = None) -> List[str]:
    """
    批量下载雷达图片

    Args:
        start_time: 开始时间
        end_time: 结束时间
        output_dir: 输出目录
        base_url: 基础URL
        interval_minutes: 时间间隔(分钟)
        logger: 日志记录器

    Returns:
        下载成功的文件路径列表
    """
    if logger is None:
        logger = setup_logger('radar_downloader')

    downloaded_files = []
    current_time = start_time

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    while current_time <= end_time:
        try:
            # 构建文件名(根据实际URL格式调整)
            date_str = current_time.strftime('%Y%m%d')
            time_str = current_time.strftime('%Y%m%d%H%M%S')

            filename = f"Z_RADA_C_BABJ_{time_str}_P_DOR_ACHN_CREF_{date_str}_{current_time.strftime('%H%M%S')}.png"
            url = f"{base_url}/{date_str}/{filename}"
            output_path = os.path.join(output_dir, filename)

            # 检查文件是否已存在
            if os.path.exists(output_path):
                logger.info(f"文件已存在，跳过: {filename}")
                downloaded_files.append(output_path)
                current_time += timedelta(minutes=interval_minutes)
                continue

            # 下载文件
            logger.info(f"正在下载: {filename}")
            if download_file(url, output_path):
                downloaded_files.append(output_path)
                logger.info(f"下载成功: {filename}")
            else:
                logger.warning(f"下载失败: {filename}")

        except Exception as e:
            logger.error(f"处理时间 {current_time} 时出错: {e}")

        current_time += timedelta(minutes=interval_minutes)

    logger.info(f"下载完成，共获取 {len(downloaded_files)} 个文件")
    return downloaded_files


def ensure_directory(directory: str) -> Path:
    """
    确保目录存在，如不存在则创建

    Args:
        directory: 目录路径

    Returns:
        Path对象
    """
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def calculate_file_hash(file_path: str, algorithm: str = 'md5') -> str:
    """
    计算文件哈希值

    Args:
        file_path: 文件路径
        algorithm: 哈希算法 ('md5', 'sha1', 'sha256')

    Returns:
        文件哈希值
    """
    hash_func = hashlib.new(algorithm)

    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def batch_process(items: List,
                 process_func,
                 batch_size: int = 10,
                 desc: str = "Processing") -> List:
    """
    批量处理数据

    Args:
        items: 要处理的项目列表
        process_func: 处理函数
        batch_size: 批次大小
        desc: 描述信息

    Returns:
        处理结果列表
    """
    results = []
    total = len(items)

    for i in range(0, total, batch_size):
        batch = items[i:i + batch_size]
        batch_results = [process_func(item) for item in batch]
        results.extend(batch_results)

        print(f"{desc}: {min(i + batch_size, total)}/{total} ({min(i + batch_size, total) / total * 100:.1f}%)")

    return results


def validate_coordinates(lon: float, lat: float) -> Tuple[bool, str]:
    """
    验证经纬度坐标是否有效

    Args:
        lon: 经度
        lat: 纬度

    Returns:
        (是否有效, 错误信息)
    """
    if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
        return False, "经纬度必须是数字"

    if not (-180 <= lon <= 180):
        return False, f"经度必须在-180到180之间，当前值: {lon}"

    if not (-90 <= lat <= 90):
        return False, f"纬度必须在-90到90之间，当前值: {lat}"

    return True, ""


def format_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 字节数

    Returns:
        格式化后的大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_file_info(file_path: str) -> Dict:
    """
    获取文件信息

    Args:
        file_path: 文件路径

    Returns:
        文件信息字典
    """
    if not os.path.exists(file_path):
        return {'exists': False}

    stat_info = os.stat(file_path)

    return {
        'exists': True,
        'size': stat_info.st_size,
        'size_formatted': format_size(stat_info.st_size),
        'modified_time': datetime.fromtimestamp(stat_info.st_mtime),
        'created_time': datetime.fromtimestamp(stat_info.st_ctime),
        'hash_md5': calculate_file_hash(file_path, 'md5')
    }


def create_progress_bar(current: int, total: int, width: int = 50) -> str:
    """
    创建进度条

    Args:
        current: 当前进度
        total: 总数
        width: 进度条宽度

    Returns:
        进度条字符串
    """
    if total == 0:
        return "[" + "=" * width + "]"

    filled = int(width * current / total)
    bar = "=" * filled + "-" * (width - filled)
    percentage = current / total * 100

    return f"[{bar}] {percentage:.1f}% ({current}/{total})"


class Timer:
    """计时器类"""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        """开始计时"""
        self.start_time = datetime.now()
        return self

    def stop(self):
        """停止计时"""
        self.end_time = datetime.now()
        return self

    def elapsed(self) -> timedelta:
        """获取已用时间"""
        if self.start_time is None:
            return timedelta(0)

        end = self.end_time or datetime.now()
        return end - self.start_time

    def elapsed_seconds(self) -> float:
        """获取已用秒数"""
        return self.elapsed().total_seconds()

    def __str__(self) -> str:
        """字符串表示"""
        return str(self.elapsed())

    def __enter__(self):
        """上下文管理器入口"""
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()


if __name__ == '__main__':
    # 示例用法
    print("工具函数模块")

    # 测试日志记录器
    logger = setup_logger('test', 'test.log')
    logger.info("这是一条测试日志")

    # 测试计时器
    with Timer() as timer:
        import time
        time.sleep(1)
    print(f"耗时: {timer.elapsed_seconds():.2f}秒")

    # 测试坐标验证
    valid, msg = validate_coordinates(116.4074, 39.9042)
    print(f"坐标验证: {valid}, {msg}")

    # 测试文件信息
    if os.path.exists('test.log'):
        info = get_file_info('test.log')
        print(f"文件信息: {info}")

    # 测试进度条
    for i in range(101):
        print(f"\r{create_progress_bar(i, 100)}", end='')
        import time
        time.sleep(0.02)
    print()
