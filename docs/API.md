# 气象雷达数据管理与预测平台 - API接口文档

## 📋 文档说明

### 基础信息
- **API版本**: v1
- **基础URL**: `http://localhost:8000/api/v1`
- **数据格式**: JSON
- **字符编码**: UTF-8
- **认证方式**: JWT Bearer Token

### 通用响应格式

#### 成功响应
```json
{
    "code": 200,
    "message": "success",
    "data": {},
    "timestamp": "2024-03-10T16:00:00Z"
}
```

#### 错误响应
```json
{
    "code": 400,
    "message": "Bad Request",
    "detail": "参数验证失败",
    "timestamp": "2024-03-10T16:00:00Z"
}
```

### 状态码说明
| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 422 | 验证错误 |
| 500 | 服务器内部错误 |

---

## 🔐 认证接口

### 1. 用户登录
```
POST /auth/login
```

**请求参数**
```json
{
    "username": "admin",
    "password": "admin123"
}
```

**响应示例**
```json
{
    "code": 200,
    "message": "登录成功",
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 3600,
        "user": {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "full_name": "系统管理员",
            "is_superuser": true
        }
    },
    "timestamp": "2024-03-10T16:00:00Z"
}
```

### 2. 刷新令牌
```
POST /auth/refresh
```

**请求参数**
```json
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 3. 用户登出
```
POST /auth/logout
```

**请求头**
```
Authorization: Bearer {access_token}
```

---

## 📍 站点管理接口

### 1. 获取站点列表
```
GET /sites
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| name | str | 否 | 站点名称（模糊搜索） |
| code | str | 否 | 站点编码 |
| region | str | 否 | 区域筛选 |
| is_active | bool | 否 | 是否启用 |

**响应示例**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "items": [
            {
                "id": 1,
                "name": "北京站",
                "code": "BJ001",
                "longitude": 116.4074,
                "latitude": 39.9042,
                "altitude": 50.0,
                "region": "华北",
                "description": "北京气象观测站",
                "is_active": true,
                "created_at": "2024-03-10T00:00:00Z",
                "updated_at": "2024-03-10T00:00:00Z"
            }
        ],
        "total": 100,
        "page": 1,
        "page_size": 20,
        "total_pages": 5
    },
    "timestamp": "2024-03-10T16:00:00Z"
}
```

### 2. 获取单个站点详情
```
GET /sites/{site_id}
```

**路径参数**
- `site_id`: 站点ID

**响应示例**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "name": "北京站",
        "code": "BJ001",
        "longitude": 116.4074,
        "latitude": 39.9042,
        "altitude": 50.0,
        "region": "华北",
        "description": "北京气象观测站",
        "is_active": true,
        "created_at": "2024-03-10T00:00:00Z",
        "updated_at": "2024-03-10T00:00:00Z",
        "statistics": {
            "total_records": 24000,
            "latest_observation": "2024-03-10T16:00:00Z",
            "avg_dbz": 28.5
        }
    },
    "timestamp": "2024-03-10T16:00:00Z"
}
```

### 3. 创建站点
```
POST /sites
```

**请求参数**
```json
{
    "name": "北京站",
    "code": "BJ001",
    "longitude": 116.4074,
    "latitude": 39.9042,
    "altitude": 50.0,
    "region": "华北",
    "description": "北京气象观测站"
}
```

**参数验证规则**
- `name`: 必填，长度1-100字符
- `code`: 必填，长度1-50字符，唯一
- `longitude`: 必填，范围-180到180
- `latitude`: 必填，范围-90到90
- `altitude`: 可选，单位米
- `region`: 可选，长度1-100字符
- `description`: 可选

**响应示例**
```json
{
    "code": 201,
    "message": "站点创建成功",
    "data": {
        "id": 1,
        "name": "北京站",
        "code": "BJ001",
        ...
    },
    "timestamp": "2024-03-10T16:00:00Z"
}
```

### 4. 更新站点
```
PUT /sites/{site_id}
```

**请求参数**
```json
{
    "name": "北京站(更新)",
    "description": "更新后的描述",
    "is_active": true
}
```

**响应示例**
```json
{
    "code": 200,
    "message": "站点更新成功",
    "data": {
        "id": 1,
        "name": "北京站(更新)",
        ...
    },
    "timestamp": "2024-03-10T16:00:00Z"
}
```

### 5. 删除站点 (软删除)
```
DELETE /sites/{site_id}
```

**响应示例**
```json
{
    "code": 200,
    "message": "站点删除成功",
    "data": null,
    "timestamp": "2024-03-10T16:00:00Z"
}
```

### 6. 批量导入站点
```
POST /sites/import
```

**请求参数**
- Content-Type: `multipart/form-data`
- `file`: CSV或Excel文件

**CSV格式示例**
```csv
name,code,longitude,latitude,altitude,region,description
北京站,BJ001,116.4074,39.9042,50,华北,北京气象观测站
上海站,SH001,121.4737,31.2304,10,华东,上海气象观测站
```

**响应示例**
```json
{
    "code": 200,
    "message": "批量导入完成",
    "data": {
        "total": 10,
        "success": 8,
        "failed": 2,
        "errors": [
            {
                "row": 3,
                "error": "站点编码已存在"
            },
            {
                "row": 7,
                "error": "经纬度格式错误"
            }
        ]
    },
    "timestamp": "2024-03-10T16:00:00Z"
}
```

---

## 📊 数据查询接口

### 1. 查询站点雷达数据
```
GET /sites/{site_id}/data
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_time | datetime | 是 | 开始时间 (ISO 8601格式) |
| end_time | datetime | 是 | 结束时间 (ISO 8601格式) |
| data_source | str | 否 | 数据来源: 'actual', 'predicted', 'all' |
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |

**请求示例**
```
GET /sites/1/data?start_time=2024-03-10T00:00:00Z&end_time=2024-03-10T23:59:59Z&data_source=actual&page=1&page_size=20
```

**响应示例**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "site_info": {
            "id": 1,
            "name": "北京站",
            "code": "BJ001",
            "longitude": 116.4074,
            "latitude": 39.9042,
            "region": "华北"
        },
        "time_range": {
            "start": "2024-03-10T00:00:00Z",
            "end": "2024-03-10T23:59:59Z"
        },
        "statistics": {
            "count": 240,
            "max_dbz": 55.2,
            "min_dbz": 5.1,
            "avg_dbz": 28.3,
            "std_dbz": 12.5,
            "data_quality": {
                "good": 220,
                "interpolated": 15,
                "outlier": 3,
                "missing": 2
            }
        },
        "items": [
            {
                "id": 123456,
                "observation_time": "2024-03-10T00:00:00Z",
                "dbz_value": 25.3,
                "dbz_category": "moderate",
                "cloud_impact_factor": 0.6,
                "rgb_value": "255,255,0",
                "data_quality": "good",
                "data_source": "actual"
            },
            ...
        ],
        "total": 240,
        "page": 1,
        "page_size": 20,
        "total_pages": 12
    },
    "timestamp": "2024-03-10T16:00:00Z"
}
```

### 2. 导出数据为CSV
```
GET /sites/{site_id}/data/export
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_time | datetime | 是 | 开始时间 |
| end_time | datetime | 是 | 结束时间 |
| data_source | str | 否 | 数据来源 |
| include_columns | str | 否 | 包含的列（逗号分隔） |

**响应**
- Content-Type: `text/csv`
- Content-Disposition: `attachment; filename="site_{site_id}_data_{timestamp}.csv"`

**CSV格式示例**
```csv
observation_time,dbz_value,dbz_category,cloud_impact_factor,data_quality,data_source
2024-03-10 00:00:00,25.3,moderate,0.600,good,actual
2024-03-10 00:06:00,28.7,moderate,0.500,good,actual
```

### 3. 获取站点数据统计
```
GET /sites/{site_id}/statistics
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_time | datetime | 是 | 开始时间 |
| end_time | datetime | 是 | 结束时间 |

**响应示例**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "site_info": {
            "id": 1,
            "name": "北京站"
        },
        "time_range": {
            "start": "2024-03-10T00:00:00Z",
            "end": "2024-03-10T23:59:59Z"
        },
        "basic_statistics": {
            "count": 240,
            "max_dbz": 55.2,
            "min_dbz": 5.1,
            "avg_dbz": 28.3,
            "median_dbz": 26.5,
            "std_dbz": 12.5,
            "percentile_25": 18.2,
            "percentile_75": 38.6
        },
        "category_distribution": {
            "no_data": 10,
            "weak": 50,
            "moderate": 120,
            "strong": 45,
            "severe": 12,
            "extreme": 3
        },
        "temporal_distribution": {
            "hourly_avg": [
                {"hour": 0, "avg_dbz": 22.5},
                {"hour": 1, "avg_dbz": 24.3},
                ...
            ]
        },
        "data_quality": {
            "good": 220,
            "interpolated": 15,
            "outlier": 3,
            "missing": 2
        }
    },
    "timestamp": "2024-03-10T16:00:00Z"
}
```

---

## 🔮 预测接口

### 1. 获取站点预测数据
```
GET /sites/{site_id}/predictions
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_time | datetime | 是 | 开始时间 |
| end_time | datetime | 是 | 结束时间 |
| model_type | str | 否 | 模型类型: 'optical_flow', 'prophet', 'all' |

**响应示例**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "site_info": {
            "id": 1,
            "name": "北京站"
        },
        "predictions": [
            {
                "id": 10001,
                "prediction_time": "2024-03-10T17:00:00Z",
                "predicted_dbz": 30.5,
                "confidence_lower": 25.2,
                "confidence_upper": 35.8,
                "model_type": "prophet",
                "model_version": "v1.0.0",
                "prediction_horizon": 60,
                "prediction_accuracy": 0.85,
                "created_at": "2024-03-10T16:00:00Z"
            },
            ...
        ],
        "total": 24
    },
    "timestamp": "2024-03-10T16:00:00Z"
}
```

### 2. 触发预测任务
```
POST /sites/{site_id}/predict
```

**请求参数**
```json
{
    "model_type": "prophet",
    "prediction_horizon": 360,
    "confidence_interval": 0.8
}
```

**参数说明**
- `model_type`: 模型类型 ('optical_flow', 'prophet', 'ensemble')
- `prediction_horizon`: 预测时长（分钟），默认360分钟（6小时）
- `confidence_interval`: 置信区间 (0-1)，默认0.8

**响应示例**
```json
{
    "code": 202,
    "message": "预测任务已创建",
    "data": {
        "task_id": "pred_task_123456",
        "status": "pending",
        "estimated_completion": "2024-03-10T16:05:00Z",
        "model_type": "prophet",
        "prediction_horizon": 360
    },
    "timestamp": "2024-03-10T16:00:00Z"
}
```

### 3. 获取预测任务状态
```
GET /predictions/tasks/{task_id}
```

**响应示例**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "task_id": "pred_task_123456",
        "status": "completed",
        "progress": 100.0,
        "started_at": "2024-03-10T16:00:00Z",
        "completed_at": "2024-03-10T16:04:32Z",
        "result": {
            "predictions_count": 24,
            "model_version": "v1.0.0",
            "accuracy_score": 0.85
        }
    },
    "timestamp": "2024-03-10T16:05:00Z"
}
```

### 4. 对比实际数据与预测数据
```
GET /sites/{site_id}/predictions/comparison
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_time | datetime | 是 | 开始时间 |
| end_time | datetime | 是 | 结束时间 |
| model_type | str | 否 | 模型类型 |

**响应示例**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "site_info": {
            "id": 1,
            "name": "北京站"
        },
        "comparison": [
            {
                "time": "2024-03-10T17:00:00Z",
                "actual_dbz": 28.5,
                "predicted_dbz": 30.2,
                "error": -1.7,
                "absolute_error": 1.7,
                "percentage_error": 5.96
            },
            ...
        ],
        "accuracy_metrics": {
            "mae": 2.5,
            "rmse": 3.2,
            "mape": 8.5,
            "r_squared": 0.85
        }
    },
    "timestamp": "2024-03-10T16:00:00Z"
}
```

---

## ⚙️ 系统监控接口

### 1. 获取系统状态
```
GET /system/status
```

**响应示例**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "system_info": {
            "version": "1.0.0",
            "environment": "production",
            "uptime": 86400,
            "server_time": "2024-03-10T16:00:00Z"
        },
        "download_status": {
            "last_download_time": "2024-03-10T16:00:00Z",
            "next_download_time": "2024-03-10T16:06:00Z",
            "pending_tasks": 0,
            "failed_tasks": 0,
            "success_rate": 0.98
        },
        "processing_status": {
            "last_processing_time": "2024-03-10T16:00:30Z",
            "pending_images": 0,
            "processing_queue_size": 0,
            "avg_processing_time": 2.5
        },
        "database_status": {
            "connection_pool_size": 20,
            "active_connections": 5,
            "idle_connections": 15,
            "status": "healthy"
        },
        "system_resources": {
            "cpu_usage": 25.5,
            "memory_usage": 45.2,
            "disk_usage": 60.8,
            "network_io": {
                "bytes_sent": 1024000,
                "bytes_recv": 2048000
            }
        }
    },
    "timestamp": "2024-03-10T16:00:00Z"
}
```

### 2. 获取系统日志
```
GET /system/logs
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| log_type | str | 否 | 日志类型: 'download', 'processing', 'prediction', 'system', 'all' |
| log_level | str | 否 | 日志级别: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL' |
| start_time | datetime | 否 | 开始时间 |
| end_time | datetime | 否 | 结束时间 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应示例**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "items": [
            {
                "id": 10001,
                "log_type": "download",
                "log_level": "INFO",
                "message": "雷达图片下载成功",
                "details": {
                    "filename": "Z_RADA_C_BABJ_20240310160000.png",
                    "file_size": 524288,
                    "download_time": 2.5
                },
                "created_at": "2024-03-10T16:00:00Z"
            },
            ...
        ],
        "total": 1000,
        "page": 1,
        "page_size": 20
    },
    "timestamp": "2024-03-10T16:00:00Z"
}
```

### 3. 获取任务队列状态
```
GET /system/tasks/queue
```

**响应示例**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "download_queue": {
            "pending": 0,
            "running": 1,
            "failed": 0
        },
        "processing_queue": {
            "pending": 0,
            "running": 0,
            "failed": 0
        },
        "prediction_queue": {
            "pending": 2,
            "running": 1,
            "failed": 0
        }
    },
    "timestamp": "2024-03-10T16:00:00Z"
}
```

### 4. 清理系统日志
```
POST /system/logs/cleanup
```

**请求参数**
```json
{
    "days_to_keep": 30
}
```

**响应示例**
```json
{
    "code": 200,
    "message": "日志清理完成",
    "data": {
        "deleted_rows": 1500
    },
    "timestamp": "2024-03-10T16:00:00Z"
}
```

---

## 📥 数据处理接口

### 1. 创建数据处理任务
```
POST /processing/tasks
```

**请求参数**
```json
{
    "task_name": "批量处理北京站数据",
    "task_type": "batch_process",
    "site_ids": [1, 2, 3],
    "start_time": "2024-03-10T00:00:00Z",
    "end_time": "2024-03-10T23:59:59Z"
}
```

**响应示例**
```json
{
    "code": 201,
    "message": "处理任务已创建",
    "data": {
        "task_id": "proc_task_123456",
        "status": "pending",
        "estimated_completion": "2024-03-10T16:10:00Z"
    },
    "timestamp": "2024-03-10T16:00:00Z"
}
```

### 2. 获取处理任务状态
```
GET /processing/tasks/{task_id}
```

**响应示例**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "task_id": "proc_task_123456",
        "task_name": "批量处理北京站数据",
        "status": "running",
        "progress": 45.5,
        "total_items": 1000,
        "processed_items": 455,
        "failed_items": 2,
        "started_at": "2024-03-10T16:00:00Z",
        "estimated_completion": "2024-03-10T16:05:00Z"
    },
    "timestamp": "2024-03-10T16:02:30Z"
}
```

### 3. 取消处理任务
```
POST /processing/tasks/{task_id}/cancel
```

**响应示例**
```json
{
    "code": 200,
    "message": "任务已取消",
    "data": {
        "task_id": "proc_task_123456",
        "status": "cancelled"
    },
    "timestamp": "2024-03-10T16:00:00Z"
}
```

---

## 🔧 配置管理接口

### 1. 获取系统配置
```
GET /system/config
```

**响应示例**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "download_config": {
            "interval_minutes": 6,
            "max_retries": 3,
            "timeout": 30,
            "enable_resume": true
        },
        "processing_config": {
            "batch_size": 10,
            "max_workers": 4
        },
        "prediction_config": {
            "optical_flow": {
                "enabled": true,
                "history_frames": 6
            },
            "prophet": {
                "enabled": true,
                "retrain_interval": "daily"
            }
        }
    },
    "timestamp": "2024-03-10T16:00:00Z"
}
```

### 2. 更新系统配置
```
PUT /system/config
```

**请求参数**
```json
{
    "download_config": {
        "interval_minutes": 6,
        "max_retries": 3
    },
    "processing_config": {
        "batch_size": 20
    }
}
```

**响应示例**
```json
{
    "code": 200,
    "message": "配置更新成功",
    "data": {
        "updated_at": "2024-03-10T16:00:00Z"
    },
    "timestamp": "2024-03-10T16:00:00Z"
}
```

---

## 📈 统计分析接口

### 1. 获取系统统计概览
```
GET /statistics/overview
```

**响应示例**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "sites": {
            "total": 10,
            "active": 8,
            "inactive": 2
        },
        "data": {
            "total_records": 2400000,
            "date_range": {
                "earliest": "2024-01-01T00:00:00Z",
                "latest": "2024-03-10T16:00:00Z"
            }
        },
        "predictions": {
            "total_predictions": 12000,
            "avg_accuracy": 0.85
        },
        "storage": {
            "radar_images_size": "5.2 GB",
            "database_size": "2.8 GB"
        }
    },
    "timestamp": "2024-03-10T16:00:00Z"
}
```

### 2. 获取下载统计
```
GET /statistics/downloads
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | date | 否 | 开始日期 |
| end_date | date | 否 | 结束日期 |

**响应示例**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "period": {
            "start": "2024-03-01",
            "end": "2024-03-10"
        },
        "summary": {
            "total_downloads": 240,
            "successful": 235,
            "failed": 5,
            "success_rate": 0.979
        },
        "daily_statistics": [
            {
                "date": "2024-03-10",
                "total": 24,
                "success": 24,
                "failed": 0,
                "avg_file_size": 524288
            },
            ...
        ]
    },
    "timestamp": "2024-03-10T16:00:00Z"
}
```

---

## 🚨 错误处理

### 错误响应格式
```json
{
    "code": 400,
    "message": "Bad Request",
    "detail": "参数验证失败",
    "errors": [
        {
            "field": "longitude",
            "message": "经度必须在-180到180之间"
        },
        {
            "field": "latitude",
            "message": "纬度必须在-90到90之间"
        }
    ],
    "timestamp": "2024-03-10T16:00:00Z"
}
```

### 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 400 | 请求参数错误 | 检查请求参数格式 |
| 401 | 未授权 | 检查Token是否有效 |
| 403 | 禁止访问 | 检查用户权限 |
| 404 | 资源不存在 | 检查URL路径 |
| 422 | 验证错误 | 检查请求体数据 |
| 500 | 服务器错误 | 联系系统管理员 |

---

## 📝 使用示例

### Python示例
```python
import requests
import pandas as pd

# 配置
BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "your-jwt-token-here"

# 请求头
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 1. 获取站点列表
response = requests.get(f"{BASE_URL}/sites", headers=headers)
sites = response.json()["data"]["items"]

# 2. 查询站点数据
site_id = 1
params = {
    "start_time": "2024-03-10T00:00:00Z",
    "end_time": "2024-03-10T23:59:59Z",
    "data_source": "actual"
}
response = requests.get(
    f"{BASE_URL}/sites/{site_id}/data",
    headers=headers,
    params=params
)
data = response.json()["data"]["items"]

# 3. 转换为DataFrame
df = pd.DataFrame(data)
print(df.head())
```

### JavaScript示例
```javascript
// 配置
const BASE_URL = "http://localhost:8000/api/v1";
const TOKEN = "your-jwt-token-here";

// 请求头
const headers = {
    "Authorization": `Bearer ${TOKEN}`,
    "Content-Type": "application/json"
};

// 1. 获取站点列表
async function getSites() {
    const response = await fetch(`${BASE_URL}/sites`, { headers });
    const data = await response.json();
    return data.data.items;
}

// 2. 查询站点数据
async function getSiteData(siteId, startTime, endTime) {
    const params = new URLSearchParams({
        start_time: startTime,
        end_time: endTime,
        data_source: "actual"
    });
    const response = await fetch(
        `${BASE_URL}/sites/${siteId}/data?${params}`,
        { headers }
    );
    const data = await response.json();
    return data.data.items;
}

// 使用示例
getSites().then(sites => {
    console.log("站点列表:", sites);
});
```

---

## 📚 附录

### A. 数据模型定义

#### Site (站点)
```python
class Site(BaseModel):
    id: int
    name: str
    code: str
    longitude: float
    latitude: float
    altitude: float | None
    region: str | None
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

#### RadarData (雷达数据)
```python
class RadarData(BaseModel):
    id: int
    site_id: int
    observation_time: datetime
    dbz_value: float | None
    dbz_category: str
    cloud_impact_factor: float
    data_quality: str
    data_source: str
```

#### Prediction (预测数据)
```python
class Prediction(BaseModel):
    id: int
    site_id: int
    prediction_time: datetime
    predicted_dbz: float
    confidence_lower: float | None
    confidence_upper: float | None
    model_type: str
    model_version: str | None
    prediction_horizon: int
```

### B. WebSocket接口 (实时更新)

#### 连接WebSocket
```
ws://localhost:8000/api/v1/ws?token={jwt_token}
```

#### 订阅站点数据更新
```json
{
    "action": "subscribe",
    "channel": "site_data",
    "site_id": 1
}
```

#### 实时数据推送
```json
{
    "type": "site_data_update",
    "data": {
        "site_id": 1,
        "observation_time": "2024-03-10T16:06:00Z",
        "dbz_value": 28.5,
        "dbz_category": "moderate"
    },
    "timestamp": "2024-03-10T16:06:00Z"
}
```

---

**文档版本**: v1.0.0
**最后更新**: 2024-03-10
**作者**: 气象雷达数据平台团队
