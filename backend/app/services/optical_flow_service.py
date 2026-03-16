"""
光流法预测模块

使用OpenCV的Farneback光流法追踪云团运动，预测未来雷达回波
"""
import numpy as np
import cv2
from typing import List, Tuple, Dict, Optional
from pathlib import Path
from datetime import datetime, timedelta
import warnings

from app.core.config import settings


class OpticalFlowPredictor:
    """
    光流法预测器

    基于连续雷达图片计算光流场，预测云团移动趋势
    """

    def __init__(self):
        """初始化光流法预测器"""
        # 光流法参数
        self.pyr_scale = getattr(settings, 'OPTICAL_FLOW_PYRAMED_SCALE', 0.5)
        self.levels = getattr(settings, 'OPTICAL_FLOW_LEVELS', 3)
        self.winsize = getattr(settings, 'OPTICAL_FLOW_WINSIZE', 15)
        self.iterations = getattr(settings, 'OPTICAL_FLOW_ITERATIONS', 3)
        self.poly_n = getattr(settings, 'OPTICAL_FLOW_POLY_N', 5)
        self.poly_sigma = getattr(settings, 'OPTICAL_FLOW_POLY_SIGMA', 1.2)

        # 历史帧数
        self.history_frames = getattr(settings, 'OPTICAL_FLOW_HISTORY_FRAMES', 6)

        # 图片缓存
        self.image_cache: List[np.ndarray] = []

    def load_images(self, image_paths: List[str]) -> List[np.ndarray]:
        """
        加载雷达图片

        Args:
            image_paths: 图片路径列表（按时间排序）

        Returns:
            图片数组列表
        """
        images = []
        for path in image_paths:
            try:
                # 读取图片
                img = cv2.imread(path)
                if img is None:
                    warnings.warn(f"无法读取图片: {path}")
                    continue

                # 转换为灰度图
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                # 调整大小（可选）
                # gray = cv2.resize(gray, (0, 0), fx=0.5, fy=0.5)

                images.append(gray)
            except Exception as e:
                warnings.warn(f"处理图片失败 {path}: {e}")

        return images

    def calculate_optical_flow(self, prev_img: np.ndarray, curr_img: np.ndarray) -> np.ndarray:
        """
        计算两帧之间的光流

        Args:
            prev_img: 上一帧图片
            curr_img: 当前帧图片

        Returns:
            光流场 (height, width, 2)
        """
        # 使用Farneback算法计算稠密光流
        flow = cv2.calcOpticalFlowFarneback(
            prev_img,
            curr_img,
            None,
            pyr_scale=self.pyr_scale,
            levels=self.levels,
            winsize=self.winsize,
            iterations=self.iterations,
            poly_n=self.poly_n,
            poly_sigma=self.poly_sigma,
            flags=0
        )

        return flow

    def predict_future_position(
        self,
        lon: float,
        lat: float,
        pixel_x: int,
        pixel_y: int,
        flow: np.ndarray,
        time_steps: int = 10
    ) -> List[Tuple[int, int, float, float]]:
        """
        预测未来位置的轨迹

        Args:
            lon: 当前经度
            lat: 当前纬度
            pixel_x: 当前像素X坐标
            pixel_y: 当前像素Y坐标
            flow: 光流场
            time_steps: 预测时间步数

        Returns:
            预测轨迹列表 [(pixel_x, pixel_y, lon, lat), ...]
        """
        height, width = flow.shape[:2]
        trajectory = []

        curr_x, curr_y = float(pixel_x), float(pixel_y)

        for step in range(1, time_steps + 1):
            # 边界检查
            if (curr_x < 0 or curr_x >= width or
                curr_y < 0 or curr_y >= height):
                break

            # 获取当前像素的光流矢量
            x_idx = int(np.clip(curr_x, 0, width - 1))
            y_idx = int(np.clip(curr_y, 0, height - 1))

            flow_x = flow[y_idx, x_idx, 0]
            flow_y = flow[y_idx, x_idx, 1]

            # 更新位置
            curr_x += flow_x
            curr_y += flow_y

            # 转换为经纬度（需要坐标映射器）
            # 这里简化处理，实际需要调用CoordinateMapper
            next_lon = lon + flow_x * 0.01  # 粗略估算
            next_lat = lat - flow_y * 0.01

            trajectory.append((int(curr_x), int(curr_y), next_lon, next_lat))

        return trajectory

    def predict_site_future(
        self,
        site_id: int,
        longitude: float,
        latitude: float,
        pixel_x: int,
        pixel_y: int,
        image_sequence: List[np.ndarray],
        prediction_horizon_minutes: int = 360
    ) -> Dict:
        """
        预测站点未来的雷达数据

        Args:
            site_id: 站点ID
            longitude: 经度
            latitude: 纬度
            pixel_x: 像素X坐标
            pixel_y: 像素Y坐标
            image_sequence: 图片序列（按时间排序）
            prediction_horizon_minutes: 预测时长（分钟）

        Returns:
            预测结果
        """
        if len(image_sequence) < 2:
            return {
                'site_id': site_id,
                'status': 'error',
                'error': '需要至少2张图片进行光流计算'
            }

        try:
            # 计算最近两帧的光流
            prev_img = image_sequence[-2]
            curr_img = image_sequence[-1]

            flow = self.calculate_optical_flow(prev_img, curr_img)

            # 计算预测时间步数
            time_steps = prediction_horizon_minutes // 6  # 每6分钟一个时间步

            # 预测轨迹
            trajectory = self.predict_future_position(
                longitude, latitude, pixel_x, pixel_y, flow, time_steps
            )

            # 提取预测值（简化版，实际需要从轨迹位置提取dBZ值）
            predictions = []
            for i, (px, py, lon, lat) in enumerate(trajectory):
                # 从当前位置提取dBZ值（简化为当前位置的值）
                # 实际应用中，这里需要根据新的像素位置重新提取RGB并转换为dBZ
                predicted_dbz = self._extract_dbz_at_position(curr_img, px, py)

                predictions.append({
                    'time_step': i + 1,
                    'prediction_time': datetime.now() + timedelta(minutes=6 * (i + 1)),
                    'pixel_x': px,
                    'pixel_y': py,
                    'longitude': lon,
                    'latitude': lat,
                    'predicted_dbz': predicted_dbz,
                    'confidence': self._calculate_confidence(flow, pixel_x, pixel_y)
                })

            return {
                'site_id': site_id,
                'status': 'success',
                'method': 'optical_flow',
                'prediction_horizon_minutes': prediction_horizon_minutes,
                'predictions': predictions,
                'flow_magnitude': np.linalg.norm(flow[pixel_y, pixel_x])
            }

        except Exception as e:
            return {
                'site_id': site_id,
                'status': 'error',
                'error': str(e)
            }

    def _extract_dbz_at_position(self, image: np.ndarray, x: int, y: int) -> float:
        """
        从图片指定位置提取dBZ值（简化版）

        Args:
            image: 灰度图片
            x: X坐标
            y: Y坐标

        Returns:
            dBZ值
        """
        # 简化版本：基于灰度值估算dBZ
        # 实际应用中应该使用ColorScaleParser处理彩色图片
        height, width = image.shape[:2]

        if x < 0 or x >= width or y < 0 or y >= height:
            return 0.0

        gray_value = image[y, x]

        # 灰度值转dBZ的简化映射
        # 0-255 映射到 0-75 dBZ
        dbz = (gray_value / 255.0) * 75.0

        return round(dbz, 2)

    def _calculate_confidence(self, flow: np.ndarray, x: int, y: int) -> float:
        """
        计算预测置信度

        基于光流幅度和一致性

        Args:
            flow: 光流场
            x: X坐标
            y: Y坐标

        Returns:
            置信度 (0-1)
        """
        height, width = flow.shape[:2]

        if x < 0 or x >= width or y < 0 or y >= height:
            return 0.0

        # 获取局部区域的光流
        window_size = 5
        x_start = max(0, x - window_size)
        x_end = min(width, x + window_size + 1)
        y_start = max(0, y - window_size)
        y_end = min(height, y + window_size + 1)

        local_flow = flow[y_start:y_end, x_start:x_end]

        # 计算标准差（一致性）
        std_flow = np.std(local_flow)

        # 光流幅度
        flow_magnitude = np.linalg.norm(flow[y, x])

        # 置信度计算
        # 低标准差、中等幅度 = 高置信度
        if std_flow < 1.0 and 0.5 < flow_magnitude < 5.0:
            return 0.8
        elif std_flow < 2.0 and 0.3 < flow_magnitude < 10.0:
            return 0.6
        else:
            return 0.4

    def analyze_motion_field(self, flow: np.ndarray) -> Dict:
        """
        分析运动场特征

        Args:
            flow: 光流场

        Returns:
            运动场统计信息
        """
        # 计算光流幅度
        magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)

        # 计算平均运动方向和速度
        mean_flow_x = np.mean(flow[..., 0])
        mean_flow_y = np.mean(flow[..., 1])

        # 平均速度
        mean_speed = np.mean(magnitude)

        # 主导方向（角度）
        mean_direction = np.arctan2(mean_flow_y, mean_flow_x) * 180 / np.pi

        return {
            'mean_speed': float(mean_speed),
            'mean_direction': float(mean_direction),
            'max_speed': float(np.max(magnitude)),
            'min_speed': float(np.min(magnitude)),
            'std_speed': float(np.std(magnitude)),
            'flow_coverage': float(np.count_nonzero(magnitude > 0.1) / magnitude.size)
        }


class OpticalFlowService:
    """
    光流法预测服务

    提供光流法预测的高级接口
    """

    def __init__(self):
        """初始化服务"""
        self.predictor = OpticalFlowPredictor()

    def predict_site_batch(
        self,
        sites: List[Dict],
        image_paths: List[str],
        prediction_horizon_minutes: int = 360
    ) -> List[Dict]:
        """
        批量预测多个站点

        Args:
            sites: 站点列表 [{'site_id': 1, 'longitude': 116.4, 'latitude': 39.9}, ...]
            image_paths: 图片路径列表
            prediction_horizon_minutes: 预测时长

        Returns:
            预测结果列表
        """
        # 加载图片
        images = self.predictor.load_images(image_paths)

        if len(images) < 2:
            raise ValueError("需要至少2张图片进行光流计算")

        # 为每个站点生成预测
        results = []
        for site in sites:
            # 这里需要坐标映射器获取像素坐标
            # 简化处理：假设已有像素坐标
            result = self.predictor.predict_site_future(
                site_id=site['site_id'],
                longitude=site['longitude'],
                latitude=site['latitude'],
                pixel_x=0,  # 需要从坐标映射器获取
                pixel_y=0,  # 需要从坐标映射器获取
                image_sequence=images,
                prediction_horizon_minutes=prediction_horizon_minutes
            )
            results.append(result)

        return results

    def get_motion_statistics(self, image_paths: List[str]) -> Dict:
        """
        获取运动场统计信息

        Args:
            image_paths: 图片路径列表

        Returns:
            统计信息
        """
        images = self.predictor.load_images(image_paths)

        if len(images) < 2:
            return {'error': '需要至少2张图片'}

        # 计算光流
        flow = self.predictor.calculate_optical_flow(images[-2], images[-1])

        # 分析运动场
        return self.predictor.analyze_motion_field(flow)
