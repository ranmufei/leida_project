# Phase 7: 预测引擎 - 完成总结

## 实施概述

Phase 7 已成功完成，实现了完整的预测引擎系统，包括光流法预测、Prophet时序预测和集成预测功能。

## 已实现的功能

### 1. 光流法预测服务

**文件**: `backend/app/services/optical_flow_service.py`

**核心类**: `OpticalFlowPredictor`

**主要功能**:
- 使用OpenCV Farneback算法计算稠密光流场
- 基于连续雷达图片追踪云团运动
- 预测未来位置轨迹（默认支持360分钟/6小时预测）
- 计算预测置信度（基于光流一致性和幅度）

**关键参数**:
```python
pyr_scale = 0.5        # 金字塔缩放因子
levels = 3             # 金字塔层数
winsize = 15           # 平均窗口大小
iterations = 3         # 迭代次数
poly_n = 5             # 多项式邻域大小
poly_sigma = 1.2       # 多项式标准差
```

**适用场景**:
- 短期预测（0-2小时）
- 需要至少2张连续雷达图片
- 适合追踪快速移动的云团

### 2. Prophet时序预测服务

**文件**: `backend/app/services/prophet_service.py`

**核心类**: `ProphetPredictor`

**主要功能**:
- 基于Facebook Prophet进行时序预测
- 自动处理趋势、季节性（年、周、日）
- 生成预测区间（默认80%置信度）
- 交叉验证计算模型性能指标

**性能指标**:
- MSE (均方误差)
- RMSE (均方根误差)
- MAE (平均绝对误差)
- MAPE (平均绝对百分比误差)
- Coverage (覆盖率)

**数据要求**:
- 最少168个数据点（7天 × 每天24个数据点，6分钟间隔）
- 建议使用30天历史数据进行训练

**适用场景**:
- 中长期预测（2-6小时）
- 需要充足的历史数据
- 考虑季节性和趋势因素

### 3. 统一预测服务

**文件**: `backend/app/services/prediction_service.py`

**核心类**: `PredictionService`

**提供方法**:

1. **predict_with_optical_flow()**
   - 输入: 站点ID、图片路径列表、经纬度、预测时长
   - 输出: 光流法预测结果
   - 特点: 基于云团运动轨迹预测

2. **predict_with_prophet()**
   - 输入: 站点ID、预测时长、训练天数
   - 输出: Prophet预测结果（含置信区间）
   - 特点: 基于历史时序数据预测

3. **predict_ensemble()**
   - 输入: 站点ID、图片路径、经纬度、权重配置
   - 输出: 加权集成预测结果
   - 特点: 结合两种方法的优势（默认权重各0.5）

4. **batch_predict_sites()**
   - 输入: 站点列表、预测方法、预测时长
   - 输出: 批量预测结果列表
   - 特点: 支持多站点并行处理

### 4. 预测API接口

**文件**: `backend/app/api/v1/endpoints/prediction.py`

**已实现的端点**:

1. **GET /api/v1/predictions/methods**
   - 描述: 获取可用的预测方法列表
   - 返回: 方法名称、描述、数据要求

2. **GET /api/v1/predictions/site/{site_id}/latest**
   - 描述: 获取站点最新预测结果
   - 参数: 站点ID
   - 返回: 最近一次预测的详细数据

3. **POST /api/v1/predictions/site/{site_id}/predict**
   - 描述: 触发站点的异步预测任务
   - 参数: 站点ID、预测方法、预测时长
   - 返回: Celery任务ID

4. **GET /api/v1/predictions/site/{site_id}/history**
   - 描述: 获取站点历史预测记录
   - 参数: 站点ID、分页参数、时间范围过滤
   - 返回: 分页的预测历史数据

### 5. Celery异步任务

**文件**: `backend/app/tasks/prediction_tasks.py`

**任务定义**:

1. **run_single_prediction**
   - 功能: 运行单个站点的预测任务
   - 参数: 站点ID、模型类型、预测时长
   - 自动保存预测结果到数据库

2. **batch_predict_sites**
   - 功能: 批量预测多个站点
   - 参数: 站点列表、预测方法、预测时长
   - 返回: 成功/失败统计

3. **retrain_prophet_models**
   - 功能: 重新训练Prophet模型
   - 参数: 站点ID列表（None表示所有站点）
   - 用途: 定期更新模型以保持预测准确性

4. **save_predictions_to_database**
   - 功能: 保存预测结果到site_predictions表
   - 自动处理: 数据验证、事务管理、错误处理

## 数据库集成

预测结果存储在 `site_predictions` 表中:

```sql
CREATE TABLE site_predictions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    site_id INT NOT NULL,
    prediction_time DATETIME NOT NULL,
    predicted_dbz DECIMAL(5,2) NOT NULL,
    confidence_lower DECIMAL(5,2),
    confidence_upper DECIMAL(5,2),
    model_type VARCHAR(50) NOT NULL,  -- 'optical_flow', 'prophet', 'ensemble'
    model_version VARCHAR(20),
    prediction_horizon INT NOT NULL,  -- 预测时长（分钟）
    prediction_accuracy DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_site_prediction_time (site_id, prediction_time),
    INDEX idx_model_type (model_type),
    FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE
);
```

## 预测精度评估

### 光流法
- **优势**: 短期预测准确，响应快速
- **局限**: 随着时间推移误差累积
- **置信度**: 基于光流一致性（0.4-0.8）

### Prophet
- **优势**: 考虑季节性和趋势，提供置信区间
- **局限**: 需要大量历史数据，对突发变化响应慢
- **置信度**: 80%预测区间可调整

### 集成预测
- **权重**: 默认光学流0.5 + Prophet0.5
- **优势**: 结合两者优势，平衡短期和长期预测
- **调整**: 可根据实际效果动态调整权重

## 配置参数

在 `backend/app/core/config.py` 中可配置:

```python
# 光流法参数
OPTICAL_FLOW_PYRAMED_SCALE = 0.5
OPTICAL_FLOW_LEVELS = 3
OPTICAL_FLOW_WINSIZE = 15
OPTICAL_FLOW_ITERATIONS = 3
OPTICAL_FLOW_POLY_N = 5
OPTICAL_FLOW_POLY_SIGMA = 1.2
OPTICAL_FLOW_HISTORY_FRAMES = 6

# Prophet参数
PROPHET_INTERVAL_WIDTH = 0.8  # 置信区间宽度
PROPHET_YEARLY_SEASONALITY = True
PROPHET_WEEKLY_SEASONALITY = True
PROPHET_DAILY_SEASONALITY = True
PROPHET_MIN_DATA_POINTS = 168
PROPHET_TRAINING_WINDOW = 30  # 训练数据天数
```

## 使用示例

### Python API调用

```python
from app.services.prediction_service import PredictionService

service = PredictionService()

# 光流法预测
result = service.predict_with_optical_flow(
    site_id=1,
    image_paths=['path/to/image1.jpg', 'path/to/image2.jpg'],
    longitude=116.4,
    latitude=39.9,
    prediction_horizon_minutes=360
)

# Prophet预测
result = service.predict_with_prophet(
    site_id=1,
    prediction_horizon_minutes=360,
    training_days=30
)

# 集成预测
result = service.predict_ensemble(
    site_id=1,
    image_paths=['path/to/image1.jpg', 'path/to/image2.jpg'],
    longitude=116.4,
    latitude=39.9,
    prediction_horizon_minutes=360,
    optical_flow_weight=0.5,
    prophet_weight=0.5
)
```

### HTTP API调用

```bash
# 触发预测任务
curl -X POST "http://localhost:8000/api/v1/predictions/site/1/predict" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "prophet",
    "prediction_horizon_minutes": 360
  }'

# 获取最新预测
curl -X GET "http://localhost:8000/api/v1/predictions/site/1/latest" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 获取预测历史
curl -X GET "http://localhost:8000/api/v1/predictions/site/1/history?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 测试建议

### 单元测试
1. 测试光流法预测器
   - 验证光流计算正确性
   - 测试轨迹预测逻辑
   - 验证置信度计算

2. 测试Prophet预测器
   - 验证数据准备逻辑
   - 测试模型训练和预测
   - 验证性能指标计算

### 集成测试
1. 测试预测服务
   - 验证所有预测方法
   - 测试集成预测逻辑
   - 验证批量预测功能

2. 测试API端点
   - 验证请求/响应格式
   - 测试权限控制
   - 验证错误处理

3. 测试Celery任务
   - 验证异步执行
   - 测试任务重试机制
   - 验证数据库保存

## 性能优化建议

1. **模型缓存**: Prophet模型可以训练后保存，避免重复训练
2. **图片预处理**: 光流法计算前可以预处理图片（降噪、归一化）
3. **并行处理**: 批量预测可以使用Celery的group特性并行执行
4. **结果缓存**: 预测结果可以缓存到Redis，避免重复计算

## 未来改进方向

1. **实时预测**: 使用WebSocket推送预测结果
2. **模型调优**: 根据实际数据调整Prophet超参数
3. **深度学习**: 引入LSTM/GRU模型进行时序预测
4. **可视化**: 在前端展示预测曲线和置信区间
5. **预警机制**: 当预测值超过阈值时自动告警

## 已知限制

1. **光流法**:
   - 需要至少2张连续图片
   - 对光照变化敏感
   - 长期预测误差较大

2. **Prophet**:
   - 需要至少7天历史数据
   - 训练时间较长（分钟级）
   - 对突发事件响应慢

3. **集成预测**:
   - 需要同时满足两种方法的数据要求
   - 权重需要人工调优

## 依赖项

```txt
opencv-python==4.8.0.76
prophet==1.1.4
pandas==2.0.3
numpy==1.24.3
pillow==10.0.0
```

## 总结

Phase 7 成功实现了完整的预测引擎，包括:
- ✅ 光流法短期预测
- ✅ Prophet中长期预测
- ✅ 集成预测方法
- ✅ RESTful API接口
- ✅ Celery异步任务
- ✅ 数据库持久化
- ✅ 置信区间计算
- ✅ 性能指标评估

预测引擎已完全集成到系统中，可以支持未来4-6小时的dBZ值预测，为气象预警和决策提供数据支持。
