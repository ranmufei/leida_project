"""
Celery预测任务
"""
from celery import shared_task
from datetime import datetime, timedelta
from typing import Dict, List

from app.services.prediction_service import PredictionService


@shared_task(name="tasks.run_single_prediction")
def run_single_prediction(
    site_id: int,
    model_type: str = 'prophet',
    prediction_horizon: int = 360
):
    """
    运行单个站点的预测任务

    Args:
        site_id: 站点ID
        model_type: 模型类型
        prediction_horizon: 预测时长(分钟)

    Returns:
        预测结果
    """
    print(f"\n{'='*60}")
    print(f"🔮 预测任务触发: {datetime.now()}")
    print(f"站点ID: {site_id}")
    print(f"模型类型: {model_type}")
    print(f"预测时长: {prediction_horizon}分钟")
    print(f"{'='*60}")

    try:
        service = PredictionService()

        if model_type == 'prophet':
            result = service.predict_with_prophet(
                site_id=site_id,
                prediction_horizon_minutes=prediction_horizon
            )
        elif model_type == 'optical_flow':
            # 光流法需要图片路径，这里暂时返回错误
            result = {
                'site_id': site_id,
                'status': 'error',
                'error': '光流法需要图片路径，请使用批量预测接口'
            }
        else:  # ensemble
            result = {
                'site_id': site_id,
                'status': 'error',
                'error': '集成预测需要图片路径'
            }

        # 如果成功，保存到数据库
        if result.get('status') == 'success':
            save_predictions_to_database(result)

        return {
            'task': 'run_single_prediction',
            'site_id': site_id,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        print(f"❌ 预测任务失败: {e}")
        return {
            'task': 'run_single_prediction',
            'site_id': site_id,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


@shared_task(name="tasks.batch_predict_sites")
def batch_predict_sites(
    sites: List[Dict],
    prediction_method: str = 'prophet',
    prediction_horizon: int = 360
):
    """
    批量预测多个站点

    Args:
        sites: 站点列表
        prediction_method: 预测方法
        prediction_horizon: 预测时长

    Returns:
        批量预测结果
    """
    print(f"\n{'='*60}")
    print(f"🔮 批量预测任务触发: {datetime.now()}")
    print(f"站点数量: {len(sites)}")
    print(f"预测方法: {prediction_method}")
    print(f"{'='*60}")

    try:
        service = PredictionService()
        results = service.batch_predict_sites(
            sites=sites,
            prediction_method=prediction_method,
            prediction_horizon_minutes=prediction_horizon
        )

        # 保存成功的预测
        for result in results:
            if result.get('status') == 'success':
                save_predictions_to_database(result)

        successful_count = sum(1 for r in results if r.get('status') == 'success')
        failed_count = len(results) - successful_count

        return {
            'task': 'batch_predict_sites',
            'total': len(sites),
            'success': successful_count,
            'failed': failed_count,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        print(f"❌ 批量预测失败: {e}")
        return {
            'task': 'batch_predict_sites',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


@shared_task(name="tasks.retrain_prophet_models")
def retrain_prophet_models(site_ids: List[int] = None):
    """
    重新训练Prophet模型

    Args:
        site_ids: 站点ID列表，None表示训练所有站点

    Returns:
        训练结果
    """
    print(f"\n{'='*60}")
    print(f"🔄 Prophet模型重训练任务: {datetime.now()}")
    print(f"{'='*60}")

    try:
        from app.core.database import SessionLocal
        from app.models.site import Site

        db = SessionLocal()

        # 获取需要训练的站点
        if site_ids:
            sites = db.query(Site).filter(Site.id.in_(site_ids)).all()
        else:
            # 获取所有有足够数据的站点
            sites = db.query(Site).filter(Site.is_active == True).all()

        db.close()

        results = []
        for site in sites:
            try:
                # 训练模型
                result = train_prophet_for_site(site.id)
                results.append(result)
            except Exception as e:
                print(f"❌ 站点 {site.id} 训练失败: {e}")
                results.append({
                    'site_id': site.id,
                    'status': 'error',
                    'error': str(e)
                })

        return {
            'task': 'retrain_prophet_models',
            'total': len(sites),
            'success': sum(1 for r in results if r.get('status') == 'success'),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {
            'task': 'retrain_prophet_models',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def train_prophet_for_site(site_id: int) -> Dict:
    """
    为单个站点训练Prophet模型

    Args:
        site_id: 站点ID

    Returns:
        训练结果
    """
    from app.services.prophet_service import ProphetService

    prophet_service = ProphetService()

    # 保存模型
    model_save_path = f"./data/models/site_{site_id}_prophet.pkl"

    # 获取训练数据
    from app.core.database import SessionLocal
    from app.models.radar_data import SiteRadarData

    db = SessionLocal()
    try:
        # 查询最近30天的数据
        start_time = datetime.now() - timedelta(days=30)
        data_records = db.query(SiteRadarData).filter(
            SiteRadarData.site_id == site_id,
            SiteRadarData.observation_time >= start_time,
            SiteRadarData.data_source == 'actual'
        ).order_by(SiteRadarData.observation_time).all()

        if len(data_records) < 168:
            return {
                'site_id': site_id,
                'status': 'error',
                'error': f'数据不足，只有{len(data_records)}个数据点'
            }

        # 转换数据格式
        time_series_data = []
        for record in data_records:
            time_series_data.append({
                'site_id': record.site_id,
                'observation_time': record.observation_time,
                'dbz_value': float(record.dbz_value) if record.dbz_value else 0.0
            })

        # 训练并保存模型
        result = prophet_service.train_and_save_model(
            time_series_data,
            site_id,
            model_save_path
        )

        return result

    finally:
        db.close()


def save_predictions_to_database(prediction_result: Dict):
    """
    保存预测结果到数据库

    Args:
        prediction_result: 预测结果
    """
    from app.core.database import SessionLocal
    from app.models.prediction import SitePrediction

    db = SessionLocal()
    try:
        site_id = prediction_result['site_id']
        model_type = prediction_result.get('method', prediction_result.get('model_type', 'unknown'))

        for pred in prediction_result.get('predictions', []):
            site_pred = SitePrediction(
                site_id=site_id,
                prediction_time=pred['prediction_time'],
                predicted_dbz=pred['predicted_dbz'],
                confidence_lower=pred.get('confidence_lower'),
                confidence_upper=pred.get('confidence_upper'),
                model_type=model_type,
                model_version='v1.0.0',
                prediction_horizon=prediction_result.get('prediction_horizon_minutes', 0)
            )

            db.add(site_pred)

        db.commit()
        print(f"✅ 保存了 {len(prediction_result.get('predictions', []))} 条预测记录")

    except Exception as e:
        print(f"❌ 保存预测数据失败: {e}")
        db.rollback()
    finally:
        db.close()
