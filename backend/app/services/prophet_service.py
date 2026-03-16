"""
Prophet时序预测模型模块

基于Facebook Prophet的时序预测
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import warnings

try:
    from prophet import Prophet
    import prophet.forecaster as prophet_forecaster
    PROPHET_AVAILABLE = True
except ImportError:
    Prophet = None
    PROPHET_AVAILABLE = False
    warnings.warn("Prophet未安装，预测功能将不可用")


class ProphetPredictor:
    """
    Prophet时序预测器

    使用Prophet模型预测未来dBZ值
    """

    def __init__(self):
        """初始化预测器"""
        if not PROPHET_AVAILABLE:
            raise RuntimeError("Prophet未安装，请运行: pip install prophet")

        # Prophet配置
        self.interval_width = getattr(settings, 'PROPHET_INTERVAL_WIDTH', 0.8)
        self.yearly_seasonality = getattr(settings, 'PROPHET_YEARLY_SEASONALITY', True)
        self.weekly_seasonality = getattr(settings, 'PROPHET_WEEKLY_SEASONALITY', True)
        self.daily_seasonality = getattr(settings, 'PROPHET_DAILY_SEASONALITY', True)

        # 训练参数
        self.min_data_points = getattr(settings, 'PROPHET_MIN_DATA_POINTS', 168)
        self.training_window = getattr(settings, 'PROPHET_TRAINING_WINDOW', 30)

    def prepare_training_data(
        self,
        time_series_data: List[Dict],
        site_id: int
    ) -> pd.DataFrame:
        """
        准备训练数据

        Args:
            time_series_data: 时序数据列表
            site_id: 站点ID

        Returns:
            Prophet格式的DataFrame
        """
        # 提取有效数据
        valid_data = [
            {
                'ds': pd.to_datetime(item['observation_time']),
                'y': float(item['dbz_value']) if item['dbz_value'] is not None else 0.0
            }
            for item in time_series_data
            if item['site_id'] == site_id and item['dbz_value'] is not None
        ]

        if len(valid_data) < self.min_data_points:
            raise ValueError(f"数据不足，需要至少{self.min_data_points}个数据点，当前只有{len(valid_data)}个")

        # 创建DataFrame
        df = pd.DataFrame(valid_data)
        df = df.sort_values('ds')

        return df

    def train_model(self, df: pd.DataFrame) -> Prophet:
        """
        训练Prophet模型

        Args:
            df: 训练数据

        Returns:
            训练好的模型
        """
        # 创建Prophet模型
        model = Prophet(
            interval_width=self.interval_width,
            yearly_seasonality=self.yearly_seasonality,
            weekly_seasonality=self.weekly_seasonality,
            daily_seasonality=self.daily_seasonality
        )

        # 训练模型
        model.fit(df)

        return model

    def predict_future(
        self,
        model: Prophet,
        periods: int = 24,
        freq: str = '6T'
    ) -> pd.DataFrame:
        """
        预测未来数据

        Args:
            model: 训练好的模型
            periods: 预测时间步数
            freq: 时间频率

        Returns:
            预测结果
        """
        # 创建未来时间戳
        future = model.make_future_dataframe(periods=periods, freq=freq)

        # 预测
        forecast = model.predict(future)

        return forecast

    def predict_site(
        self,
        time_series_data: List[Dict],
        site_id: int,
        prediction_horizon_minutes: int = 360
    ) -> Dict:
        """
        预测单个站点的未来数据

        Args:
            time_series_data: 时序数据
            site_id: 站点ID
            prediction_horizon_minutes: 预测时长（分钟）

        Returns:
            预测结果
        """
        try:
            # 准备数据
            df = self.prepare_training_data(time_series_data, site_id)

            # 训练模型
            model = self.train_model(df)

            # 计算预测步数
            periods = prediction_horizon_minutes // 6  # 每6分钟一个时间步

            # 预测
            forecast = self.predict_future(model, periods=periods, freq='6T')

            # 提取预测结果
            predictions = []
            for i, row in forecast.tail(periods).iterrows():
                predictions.append({
                    'prediction_time': row['ds'],
                    'predicted_dbz': round(row['yhat'], 2),
                    'confidence_lower': round(row['yhat_lower'], 2),
                    'confidence_upper': round(row['yhat_upper'], 2),
                    'confidence_interval_width': row['yhat_upper'] - row['yhat_lower']
                })

            # 计算模型性能指标
            performance = self._calculate_performance(model, df)

            return {
                'site_id': site_id,
                'status': 'success',
                'model_type': 'prophet',
                'prediction_horizon_minutes': prediction_horizon_minutes,
                'predictions': predictions,
                'performance': performance
            }

        except Exception as e:
            return {
                'site_id': site_id,
                'status': 'error',
                'error': str(e)
            }

    def _calculate_performance(self, model: Prophet, df: pd.DataFrame) -> Dict:
        """
        计算模型性能指标

        Args:
            model: 训练好的模型
            df: 训练数据

        Returns:
            性能指标
        """
        # 交叉验证
        df_cv = prophet_forecaster.cross_validation(model, horizon='6H', initial='720H', period='180H')

        # 计算指标
        performance = {
            'mse': float(df_cv['mse'].mean()),
            'rmse': float(np.sqrt(df_cv['mse']).mean()),
            'mae': float(df_cv['mae'].mean()),
            'mape': float(df_cv['mape'].mean()),
            'coverage': float(df_cv['coverage'].mean())
        }

        return performance


class ProphetService:
    """
    Prophet预测服务

    提供Prophet模型训练和预测的高级接口
    """

    def __init__(self):
        """初始化服务"""
        if not PROPHET_AVAILABLE:
            warnings.warn("Prophet未安装，部分功能将不可用")
        self.predictor = None

    def predict_batch(
        self,
        time_series_data: List[Dict],
        sites: List[int],
        prediction_horizon_minutes: int = 360
    ) -> List[Dict]:
        """
        批量预测多个站点

        Args:
            time_series_data: 时序数据
            sites: 站点ID列表
            prediction_horizon_minutes: 预测时长

        Returns:
            预测结果列表
        """
        if not PROPHET_AVAILABLE:
            raise RuntimeError("Prophet未安装")

        results = []
        for site_id in sites:
            result = self.predictor.predict_site(
                time_series_data,
                site_id,
                prediction_horizon_minutes
            )
            results.append(result)

        return results

    def train_and_save_model(
        self,
        time_series_data: List[Dict],
        site_id: int,
        model_save_path: str
    ) -> Dict:
        """
        训练模型并保存

        Args:
            time_series_data: 时序数据
            site_id: 站点ID
            model_save_path: 模型保存路径

        Returns:
            训练结果
        """
        if not PROPHET_AVAILABLE:
            raise RuntimeError("Prophet未安装")

        try:
            # 准备数据
            df = self.predictor.prepare_training_data(time_series_data, site_id)

            # 训练模型
            model = self.predictor.train_model(df)

            # 保存模型
            import pickle
            with open(model_save_path, 'wb') as f:
                pickle.dump(model, f)

            return {
                'site_id': site_id,
                'status': 'success',
                'model_path': model_save_path,
                'training_samples': len(df)
            }

        except Exception as e:
            return {
                'site_id': site_id,
                'status': 'error',
                'error': str(e)
            }

    def load_model_and_predict(
        self,
        model_path: str,
        prediction_horizon_minutes: int = 360
    ) -> Dict:
        """
        加载模型并预测

        Args:
            model_path: 模型文件路径
            prediction_horizon_minutes: 预测时长

        Returns:
            预测结果
        """
        if not PROPHET_AVAILABLE:
            raise RuntimeError("Prophet未安装")

        try:
            import pickle

            # 加载模型
            with open(model_path, 'rb') as f:
                model = pickle.load(f)

            # 预测
            periods = prediction_horizon_minutes // 6
            forecast = self.predictor.predict_future(model, periods=periods, freq='6T')

            # 提取结果
            predictions = []
            for i, row in forecast.tail(periods).iterrows():
                predictions.append({
                    'prediction_time': row['ds'],
                    'predicted_dbz': round(row['yhat'], 2),
                    'confidence_lower': round(row['yhat_lower'], 2),
                    'confidence_upper': round(row['yhat_upper'], 2)
                })

            return {
                'status': 'success',
                'model_path': model_path,
                'predictions': predictions
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
