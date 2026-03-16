"""
Celery启动脚本

用于启动Celery Worker和Beat
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.tasks.celery_app import celery_app


def start_worker():
    """启动Celery Worker"""
    celery_app.start(
        argv=[
            'worker',
            '--loglevel=info',
            '--concurrency=4'
        ]
    )


def start_beat():
    """启动Celery Beat（定时任务调度器）"""
    celery_app.start(
        argv=[
            'beat',
            '--loglevel=info'
        ]
    )


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Celery启动脚本')
    parser.add_argument('service', choices=['worker', 'beat'], help='服务类型')

    args = parser.parse_args()

    if args.service == 'worker':
        print("🚀 启动Celery Worker...")
        start_worker()
    elif args.service == 'beat':
        print("⏰ 启动Celery Beat...")
        start_beat()
