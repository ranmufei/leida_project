"""
预测服务模块

整合光流法和Prophet的预测服务
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from app.services.optical_flow_service import OpticalFlowService, OpticalFlowPredictor
from app.services.prophet_service import ProphetService, ProphetPredictor, PROPHET_AVAILABLE

from app.core.database import SessionLocal
from app.models.radar_data import SiteRadarData
from app.models.site import Site


class PredictionService:
    """
    统一的预测服务

    提供多种预测方法的统一接口
    """

    def __init__(self):
        """初始化预测服务"""
        self.optical_flow_service = OpticalFlowService()
        self.prophet_service = ProphetService() if PROPHET_AVAILABLE else None

    def predict_with_optical_flow(
        self,
        site_id: int,
        image_paths: List[str],
        longitude: float,
        latitude: float,
        prediction_horizon_minutes: int = 360
    ) -> Dict:
        """
        使用光流法预测

        Args:
            site_id: 站点ID
            image_paths: 雷达图片路径列表
            longitude: 经度
            latitude: 纬度
            prediction_horizon_minutes: 预测时长

        Returns:
            预测结果
        """
        # 使用坐标映射器获取像素坐标（简化版）
        # 实际应用中需要调用CoordinateMapper
        pixel_x, pixel_y = 100, 100  # 占位符

        predictor = OpticalFlowPredictor()
        images = predictor.load_images(image_paths)

        result = predictor.predict_site_future(
            site_id=site_id,
            longitude=longitude,
            latitude=latitude,
            pixel_x=pixel_x,
            pixel_y=pixel_y,
            image_sequence=images,
            prediction_horizon_minutes=prediction_horizon_minutes
        )

        return result

    def predict_with_prophet(
        self,
        site_id: int,
        prediction_horizon_minutes: int = 360,
        training_days: int = 30
    ) -> Dict:
        """
        使用Prophet预测

        Args:
            site_id: 站点ID
            prediction_horizon_minutes: 预测时长
            training_days: 训练数据天数

        Returns:
            预测结果
        """
        if not PROPHET_AVAILABLE:
            return {
                'site_id': site_id,
                'status': 'error',
                'error': 'Prophet未安装'
            }

        # 获取历史数据
        db = SessionLocal()
        try:
            # 查询最近N天的数据
            start_time = datetime.now() - timedelta(days=training_days)
            data_records = db.query(SiteRadarData).filter(
                SiteRadarData.site_id == site_id,
                SiteRadarData.observation_time >= start_time,
                SiteRadarData.data_source == 'actual'
            ).order_by(SiteRadarData.observation_time).all()

            if len(data_records) < 168:  # 至少7天数据
                return {
                    'site_id': site_id,
                    'status': 'error',
                    'error': f'数据不足，需要至少168个数据点，当前只有{len(data_records)}个'
                }

            # 转换为字典格式
            time_series_data = []
            for record in data_records:
                time_series_data.append({
                    'site_id': record.site_id,
                    'observation_time': record.observation_time,
                    'dbz_value': float(record.dbz_value) if record.dbz_value else 0.0
                })

            # 使用Prophet预测
            result = self.prophet_service.predictor.predict_site(
                time_series_data,
                site_id,
                prediction_horizon_minutes
            )

            return result

        finally:
            db.close()

    def predict_ensemble(
        self,
        site_id: int,
        image_paths: List[str],
        longitude: float,
        latitude: float,
        prediction_horizon_minutes: int = 360,
        optical_flow_weight: float = 0.5,
        prophet_weight: float = 0.5
    ) -> Dict:
        """
        集成预测（光流法 + Prophet）

        Args:
            site_id: 站点ID
            image_paths: 图片路径列表
            longitude: 经度
            latitude: 纬度
            prediction_horizon_minutes: 预测时长
            optical_flow_weight: 光流法权重
            prophet_weight: Prophet权重

        Returns:
            集成预测结果
        """
        results = {}

        # 光流法预测
        if len(image_paths) >= 2:
            optical_flow_result = self.predict_with_optical_flow(
                site_id, image_paths, longitude, latitude, prediction_horizon_minutes
            )
            results['optical_flow'] = optical_flow_result

        # Prophet预测
        if PROPHET_AVAILABLE:
            prophet_result = self.predict_with_prophet(
                site_id, prediction_horizon_minutes
            )
            results['prophet'] = prophet_result

        # 集成结果
        if 'optical_flow' in results and 'prophet' in results:
            if results['optical_flow']['status'] == 'success' and results['prophet']['status'] == 'success':
                # 加权平均
                of_preds = results['optical_flow']['predictions']
                prophet_preds = results['prophet']['predictions']

                ensemble_predictions = []
                min_length = min(len(of_preds), len(prophet_preds))

                for i in range(min_length):
                    ensemble_dbz = (
                        of_preds[i]['predicted_dbz'] * optical_flow_weight +
                        prophet_preds[i]['predicted_dbz'] * prophet_weight
                    )

                    ensemble_predictions.append({
                        'prediction_time': of_preds[i]['prediction_time'],
                        'predicted_dbz': round(ensemble_dbz, 2),
                        'confidence_lower': prophet_preds[i]['confidence_lower'],
                        'confidence_upper': prophet_preds[i]['confidence_upper'],
                        'method': 'ensemble'
                    })

                results['ensemble'] = {
                    'site_id': site_id,
                    'status': 'success',
                    'method': 'ensemble',
                    'predictions': ensemble_predictions,
                    'weights': {'optical_flow': optical_flow_weight, 'prophet': prophet_weight}
                }

        return results

    def batch_predict_sites(
        self,
        sites: List[Dict],
        prediction_method: str = 'prophet',
        prediction_horizon_minutes: int = 360
    ) -> List[Dict]:
        """
        批量预测多个站点

        Args:
            sites: 站点列表
            prediction_method: 预测方法 ('optical_flow', 'prophet', 'ensemble')
            prediction_horizon_minutes: 预测时长

        Returns:
            预测结果列表
        """
        results = []

        for site in sites:
            if prediction_method == 'optical_flow':
                # 需要提供图片路径
                result = {
                    'site_id': site['site_id'],
                    'status': 'error',
                    'error': '光流法需要图片路径'
                }
            elif prediction_method == 'prophet':
                result = self.predict_with_prophet(
                    site_id=site['site_id'],
                    prediction_horizon_minutes=prediction_horizon_minutes
                )
            else:  # ensemble
                result = {
                    'site_id': site['site_id'],
                    'status': 'error',
                    'error': '集成预测需要图片路径'
                }

            results.append(result)

        return results
