# 气象雷达数据管理与预测平台 - 完整使用手册

<div align="center">

**版本：v1.0.0**
**更新日期：2026-03-11**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green)](https://fastapi.tiangolo.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.3%2B-brightgreen)](https://vuejs.org/)

</div>

---

## 📋 目录

- [1. 项目概述](#1-项目概述)
- [2. 快速开始](#2-快速开始)
- [3. 系统配置](#3-系统配置)
- [4. 数据下载功能](#4-数据下载功能)
- [5. 站点管理](#5-站点管理)
- [6. 数据处理与生成](#6-数据处理与生成)
- [7. 数据查询与分析](#7-数据查询与分析)
- [8. Web界面使用](#8-web界面使用)
- [9. API接口文档](#9-api接口文档)
- [10. 常见问题FAQ](#10-常见问题faq)
- [11. 维护与监控](#11-维护与监控)
- [12. 故障排查](#12-故障排查)

---

## 1. 项目概述

### 1.1 系统简介

本平台是一个企业级的气象雷达数据全流程自动化管理系统，实现了从数据自动采集、智能处理、Web管理到AI预测的完整闭环。

### 1.2 核心功能

✅ **自动数据下载**：每6分钟自动从中国气象局下载最新雷达图片
✅ **智能数据处理**：基于坐标映射和色标解析的自动化处理
✅ **站点数据生成**：将雷达图片转换为各站点的dBZ反射率数据
✅ **Web管理界面**：现代化的Vue.js 3前端界面
✅ **数据查询分析**：多维度数据查询和可视化
✅ **AI预测引擎**：光流法 + Prophet时序预测

### 1.3 技术栈

**后端**：
- FastAPI 0.100+ - 高性能异步Web框架
- SQLAlchemy 2.0+ - Python ORM
- MySQL 8.0+ - 关系型数据库
- Celery + Redis - 分布式任务队列
- OpenCV + NumPy - 图像处理

**前端**：
- Vue.js 3.3+ - 渐进式JavaScript框架
- Vite 4.3+ - 前端构建工具
- Element Plus 2.3+ - UI组件库
- ECharts 5.4+ - 数据可视化
- Pinia 2.1+ - 状态管理

---

## 2. 快速开始

### 2.1 环境要求

- **Python**: 3.9+
- **Node.js**: 16+
- **MySQL**: 8.0+
- **Redis**: 6.0+ (可选，用于异步任务)

### 2.2 安装步骤

#### 步骤1：克隆项目

```bash
git clone <repository-url>
cd leida_project
```

#### 步骤2：数据库配置

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE gfs_weather CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 配置数据库连接
cd backend
cp .env.example .env
# 编辑 .env 文件，配置数据库连接信息
```

#### 步骤3：后端安装

```bash
cd backend

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python3 scripts/init_db.py
```

#### 步骤4：前端安装

```bash
cd frontend/frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env.local
# 编辑 .env.local 文件
```

### 2.3 启动服务

#### 方式1：命令行启动（推荐开发环境）

```bash
# 终端1：启动后端
cd /Users/ranmufei/2026/leida_project/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 终端2：启动前端
cd /Users/ranmufei/2026/leida_project/frontend/frontend
npm run dev
```

#### 方式2：使用启动脚本

```bash
# 启动所有服务
cd backend
./scripts/start.sh all

# 查看服务状态
./scripts/start.sh status

# 停止所有服务
./scripts/stop.sh
```

### 2.4 访问系统

- **前端界面**: http://localhost:5173
- **API文档**: http://localhost:8000/docs
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 3. 系统配置

### 3.1 后端配置 (.env)

```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=3308
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=gfs_weather

# CMA API配置
CMA_API_URL=https://data.cma.cn/weatherGis/web/bmd/VisDataDef/getVisData?datacode=RAD__B0_CR
CMA_COOKIE=your_cookie_here
CMA_AUTH_TOKEN=

# 文件存储路径
RAW_DATA_DIR=../data/raw

# 下载配置
DOWNLOAD_TIMEOUT=30
DOWNLOAD_MAX_RETRIES=3
```

### 3.2 前端配置 (.env.local)

```bash
# API基础URL
VITE_API_BASE_URL=http://localhost:8000

# 应用配置
VITE_APP_TITLE=气象雷达数据管理平台
```

### 3.3 Cookie配置指南

#### 为什么需要Cookie？

中国气象局API需要登录认证才能下载图片。Cookie用于维持登录状态。

#### 如何获取Cookie？

1. 访问 https://data.cma.cn/ 并登录
2. 打开浏览器开发者工具 (F12)
3. 切换到 "Network" (网络) 标签
4. 刷新页面
5. 点击任意请求
6. 查看 "Request Headers" (请求头)
7. 找到 "Cookie" 字段，复制其值

#### 更新Cookie配置

编辑 `backend/.env` 文件：

```bash
CMA_COOKIE=JSESSIONID=xxx; _pk_id.6.dd70=xxx; _pk_ses.6.dd70=1
```

**重要提示**：
- Cookie会过期，如果下载失败请重新获取
- 不要分享Cookie，它包含你的登录信息
- 格式：`key1=value1; key2=value2; key3=value3`

---

## 4. 数据下载功能

### 4.1 命令行下载

#### 测试单张图片下载（推荐先测试）

```bash
cd /Users/ranmufei/2026/leida_project/backend
python3 scripts/test_single_download.py
```

#### 下载全部图片

```bash
cd /Users/ranmufei/2026/leida_project/backend
python3 scripts/download_all_fixed.py
```

**说明**：
- 自动下载全部168张雷达图片
- 每张图片间隔1秒（避免API限流）
- 自动去重，不重复下载已存在的图片
- 使用原始文件名（包含时间信息）

### 4.2 Web界面下载

#### 步骤：

1. 启动后端和前端服务
2. 访问 http://localhost:5173
3. 点击"图片管理"菜单
4. 点击"立即下载"按钮

#### 功能特性：

- ✅ 自动下载全部图片
- ✅ 实时显示下载进度
- ✅ 自动去重
- ✅ 下载统计（成功/失败/跳过）
- ✅ 错误重试机制

### 4.3 下载配置

#### 修改下载间隔

编辑 `backend/app/services/download_service_real.py`：

```python
# 第418行
time.sleep(1)  # 改为其他值，如 time.sleep(0.5) 表示0.5秒间隔
```

#### 修改下载数量

```python
# backend/app/api/v1/endpoints/download.py
@router.post("/trigger")
async def trigger_download(
    background_tasks: BackgroundTasks,
    count: int = Query(None, description="下载图片数量")  # None=全部，10=前10张
):
```

### 4.4 下载目录结构

```
backend/data/raw/
├── Z_RADA_C_BABJ_20260311084854_P_DOR_ACHN_CREF_20260311_084200.png
├── Z_RADA_C_BABJ_20260311084255_P_DOR_ACHN_CREF_20260311_083600.png
└── ... (共168张图片)
```

### 4.5 下载问题排查

#### 问题1：下载失败

**可能原因**：
- Cookie已过期
- 网络连接问题
- API地址变更

**解决方案**：
1. 重新登录 https://data.cma.cn/ 获取Cookie
2. 更新 `backend/.env` 中的 `CMA_COOKIE`
3. 检查网络连接

#### 问题2：下载速度慢

**解决方案**：
- 修改下载间隔时间（见4.3节）
- 检查网络带宽
- 考虑使用代理

---

## 5. 站点管理

### 5.1 站点初始化

#### 初始化默认站点

```bash
cd /Users/ranmufei/2026/leida_project/backend
python3 scripts/init_sites.py init --yes
```

**默认站点列表**：

| 站点名称 | 编码 | 经度 | 纬度 | 区域 |
|---------|------|------|------|------|
| 北京 | BJ001 | 116.4074 | 39.9042 | 华北 |
| 上海 | SH001 | 121.4737 | 31.2304 | 华东 |
| 广州 | GZ001 | 113.2644 | 23.1291 | 华南 |
| 深圳 | SZ001 | 114.0579 | 22.5431 | 华南 |
| 成都 | CD001 | 104.0668 | 30.5728 | 西南 |
| 武汉 | WH001 | 114.3055 | 30.5928 | 华中 |
| 西安 | XA001 | 108.9398 | 34.3416 | 西北 |
| 杭州 | HZ001 | 120.1551 | 30.2741 | 华东 |
| 南京 | NJ001 | 118.7969 | 32.0603 | 华东 |
| 重庆 | CQ001 | 106.5516 | 29.5630 | 西南 |

#### 查看站点列表

```bash
python3 scripts/init_sites.py list
```

#### 清空站点

```bash
python3 scripts/init_sites.py cleanup --yes
```

### 5.2 添加自定义站点

#### 方式1：直接操作数据库

```sql
INSERT INTO sites (name, code, longitude, latitude, altitude, region, description, is_active)
VALUES ('站点名称', 'CODE001', 120.0, 30.0, 10.0, '华东', '描述信息', 1);
```

#### 方式2：使用Python脚本

创建 `scripts/add_site.py`：

```python
from app.core.database import SessionLocal
from app.models.site import Site

db = SessionLocal()
site = Site(
    name="站点名称",
    code="CODE001",
    longitude=120.0,
    latitude=30.0,
    altitude=10.0,
    region="华东",
    description="描述信息",
    is_active=True
)
db.add(site)
db.commit()
db.close()
```

### 5.3 站点坐标要求

#### 经纬度范围

- **经度**：70.0° ~ 135.0°（中国范围）
- **纬度**：15.0° ~ 55.0°（中国范围）

#### 坐标精度

- 推荐精度：小数点后4位（约10米）
- 最低精度：小数点后2位（约1公里）

---

## 6. 数据处理与生成

### 6.1 数据处理流程

```
雷达图片 → 坐标映射 → RGB提取 → dBZ转换 → 数据库存储
```

#### 步骤1：坐标映射

- 将站点经纬度转换为图片像素坐标
- 精度：0.01°（约1公里）

#### 步骤2：RGB提取

- 获取像素坐标处的RGB颜色值
- 支持RGBA和RGB格式

#### 步骤3：dBZ转换

- 基于中国气象局12级标准色标
- RGB值匹配最近邻色标
- 返回dBZ反射率值

#### 步骤4：数据存储

- 保存到 `site_radar_data` 表
- 包含dBZ值、强度等级、云影响因子等

### 6.2 批量处理数据

#### 处理全部图片

```bash
cd /Users/ranmufei/2026/leida_project/backend
python3 scripts/process_all_images.py
```

**输出示例**：
```
📊 预计生成 1680 条站点数据
⏱️  预计耗时: 16.8 秒

✅ 成功处理: 1680 条
⏭️  跳过（已存在）: 0 条
⚠️  超出范围: 0 条
❌ 错误: 0 条

⏱️  总耗时: 40.1 秒
⚡ 平均速度: 41.9 条/秒
```

#### 处理指定数量图片

```bash
# 处理最新的10张图片
python3 scripts/process_all_images.py --limit 10

# 处理最新的50张图片
python3 scripts/process_all_images.py --limit 50
```

#### 强制重新处理

```bash
# 覆盖已存在的数据
python3 scripts/process_all_images.py --force
```

#### 静默模式

```bash
# 不显示详细信息
python3 scripts/process_all_images.py --quiet
```

### 6.3 单张图片处理（测试用）

```bash
# 处理最新的一张图片
python3 scripts/process_single_image.py

# 处理指定ID的图片
python3 scripts/process_single_image.py --id 1

# 处理指定文件名的图片
python3 scripts/process_single_image.py --filename Z_RADA_C_BABJ_20260311084854_P_DOR_ACHN_CREF_20260311_084200.png

# 强制重新处理
python3 scripts/process_single_image.py --force
```

**输出示例**：
```
📸 图片信息:
  ID: 173
  文件名: Z_RADA_C_BABJ_20260311084854_P_DOR_ACHN_CREF_20260311_084200.png
  观测时间: 2026-03-11 16:42:00

🗺️  坐标映射信息:
  经度范围: 82.67° ~ 127.33°
  纬度范围: 15.00° ~ 55.00°
  分辨率: 0.0331° × 0.0331°
  图片尺寸: 1349 × 1208 像素

[1/10] 处理站点: 北京 (BJ001)
  经纬度: (116.407400, 39.904200)
  像素坐标: (1019, 455)
  RGB值: (250, 250, 250)
  dBZ值: 65.00
  强度等级: extreme
  云影响因子: 0.000
  ✅ 已保存到数据库
```

### 6.4 数据统计查看

```bash
# 查看总体统计
python3 scripts/show_processing_stats.py

# 查看特定站点详情
python3 scripts/show_processing_stats.py --site BJ001

# 列出所有站点
python3 scripts/show_processing_stats.py --list-sites
```

**统计输出示例**：
```
📈 基础统计
  总站点数: 10
  启用站点: 10
  雷达图片: 168
  数据记录: 1680
  完成度: 100.0%

🌩️  dBZ强度分布
  极端回波: 1668 条 (99.3%)
  中等回波: 7 条 (0.4%)
  弱回波: 3 条 (0.2%)
  强回波: 2 条 (0.1%)

📍 各站点数据统计
  站点名称    编码    数据量    平均dBZ    最新时间
  北京        BJ001   168       65.00     2026-03-11 16:42
  上海        SH001   168       65.00     2026-03-11 16:42
  ...
```

### 6.5 数据质量说明

#### 数据质量等级

- **good**：良好 - 直接从雷达图片提取的原始数据
- **interpolated**：插值 - 通过插值计算得到的数据
- **outlier**：异常值 - 被标记为异常的数据
- **missing**：缺失 - 数据缺失

#### 数据来源

- **actual**：实际观测 - 从雷达图片提取的真实数据
- **predicted**：预测数据 - 通过AI模型预测的数据

#### dBZ强度等级

| 等级 | dBZ范围 | 描述 |
|------|---------|------|
| no_data | - | 无数据 |
| weak | 0-15 | 弱回波 |
| moderate | 15-35 | 中等回波 |
| strong | 35-45 | 强回波 |
| severe | 45-55 | 严重回波 |
| extreme | 55+ | 极端回波 |

---

## 7. 数据查询与分析

### 7.1 API查询

#### 基础查询

```bash
# 查询所有数据
curl "http://localhost:8000/api/v1/data/query?page=1&page_size=20"

# 查询特定站点
curl "http://localhost:8000/api/v1/data/query?site_id=8&page=1&page_size=20"

# 查询特定时间范围
curl "http://localhost:8000/api/v1/data/query?start_time=2026-03-10+00:00:00&end_time=2026-03-11+23:59:59"

# 查询特定dBZ范围
curl "http://localhost:8000/api/v1/data/query?min_dbz=30&max_dbz=50"

# 组合查询
curl "http://localhost:8000/api/v1/data/query?site_id=8&start_time=2026-03-10+00:00:00&min_dbz=30&page=1&page_size=10"
```

#### API响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "site_id": 8,
        "observation_time": "2026-03-11T16:42:00",
        "dbz_value": 65.0,
        "dbz_category": "extreme",
        "rgb_value": "250,250,250",
        "cloud_impact_factor": 0.000,
        "data_quality": "good",
        "data_source": "actual",
        "created_at": "2026-03-11T17:40:37"
      }
    ],
    "total": 168,
    "page": 1,
    "page_size": 20,
    "total_pages": 9
  }
}
```

### 7.2 Web界面查询

#### 访问数据查询页面

1. 启动前后端服务
2. 访问 http://localhost:5173
3. 点击"数据查询"菜单

#### 查询功能

- **站点选择**：下拉选择要查询的站点
- **时间范围**：选择开始时间和结束时间
- **dBZ范围**：设置最小/最大dBZ值
- **数据源筛选**：选择实际数据或预测数据
- **分页浏览**：支持翻页查看

#### 数据导出

- 点击"导出CSV"按钮
- 自动下载当前查询结果为CSV文件
- 文件名格式：`radar_data_YYYYMMDD_HHMMSS.csv`

### 7.3 数据可视化

#### ECharts图表展示

- **折线图**：显示dBZ值随时间变化
- **置信区间**：显示预测数据的置信区间
- **多站点对比**：同时显示多个站点的数据

#### 图表交互

- 鼠标悬停显示详细数值
- 点击图例显示/隐藏数据系列
- 缩放和平移功能

---

## 8. Web界面使用

### 8.1 界面布局

```
┌─────────────────────────────────────────────────────┐
│  侧边栏菜单          主内容区域                      │
│  ├─ 首页                                              │
│  ├─ 站点管理                                          │
│  ├─ 数据查询                                          │
│  ├─ 预测展示                                          │
│  ├─ 下载管理                                          │
│  └─ 系统监控                                          │
└─────────────────────────────────────────────────────┘
```

### 8.2 各功能模块

#### 8.2.1 首页

显示系统概览信息：
- 系统状态
- 数据统计
- 最近活动
- 快速操作入口

#### 8.2.2 站点管理

**功能**：
- 查看所有站点列表
- 添加新站点
- 编辑站点信息
- 启用/禁用站点
- 查看站点数据统计

**操作**：
1. 点击"站点管理"菜单
2. 查看站点表格
3. 点击"添加站点"按钮添加新站点
4. 点击操作列的"编辑"按钮修改站点
5. 点击"启用/禁用"开关切换状态

#### 8.2.3 数据查询

**功能**：
- 多维度数据查询
- 数据可视化图表
- CSV数据导出

**操作步骤**：
1. 点击"数据查询"菜单
2. 设置查询条件：
   - 选择站点
   - 设置时间范围
   - 设置dBZ范围
   - 选择数据源
3. 点击"查询"按钮
4. 查看结果表格和图表
5. 点击"导出CSV"下载数据

#### 8.2.4 预测展示

**功能**：
- AI预测模型配置
- 预测结果展示
- 预测精度评估

**操作步骤**：
1. 点击"预测展示"菜单
2. 选择预测方法：
   - 光流法（短期0-2小时）
   - Prophet（中期2-6小时）
   - 集成预测（0-6小时）
3. 设置预测时长
4. 点击"开始预测"按钮
5. 查看预测结果图表

#### 8.2.5 下载管理

**功能**：
- 手动触发下载
- 查看下载状态
- 下载统计图表

**操作步骤**：
1. 点击"下载管理"菜单
2. 查看当前下载状态
3. 点击"立即下载"按钮触发下载
4. 查看下载统计：
   - 总计图片数
   - 成功下载数
   - 失败下载数
   - 下载成功率

#### 8.2.6 图片管理

**功能**：
- 查看已下载的雷达图片
- 图片预览（缩略图）
- 图片详情查看
- 删除图片文件

**操作步骤**：
1. 点击"图片管理"菜单
2. 查看图片列表表格
3. 点击缩略图预览大图
4. 点击"删除"按钮删除图片

**表格功能**：
- 排序：点击列标题排序
- 筛选：按状态、时间筛选
- 分页：翻页浏览

#### 8.2.7 系统监控

**功能**：
- CPU使用率
- 内存使用率
- 任务队列状态
- 数据库连接池
- Redis状态
- 系统日志查看

**操作步骤**：
1. 点击"系统监控"菜单
2. 查看各项监控指标
3. 实时数据自动刷新
4. 点击"刷新"按钮手动刷新

### 8.3 用户界面特性

#### 响应式设计

- 支持桌面、平板、手机访问
- 自适应屏幕尺寸
- 移动端友好

#### 主题切换

- 浅色主题（默认）
- 深色主题
- 跟随系统

#### 多语言支持

- 中文（默认）
- 英文
- 可扩展其他语言

---

## 9. API接口文档

### 9.1 API基础信息

**Base URL**: `http://localhost:8000`

**认证方式**: JWT Token（部分接口需要）

**响应格式**: JSON

**通用响应格式**:

```json
{
  "code": 200,
  "message": "success",
  "data": {},
  "timestamp": "2026-03-11T17:42:09.813600"
}
```

### 9.2 核心API接口

#### 9.2.1 站点管理

**获取站点列表**

```http
GET /api/v1/sites/?page=1&page_size=20
```

**获取站点详情**

```http
GET /api/v1/sites/{site_id}
```

**创建站点**

```http
POST /api/v1/sites/
Content-Type: application/json

{
  "name": "站点名称",
  "code": "CODE001",
  "longitude": 120.0,
  "latitude": 30.0,
  "altitude": 10.0,
  "region": "华东",
  "description": "描述信息"
}
```

**更新站点**

```http
PUT /api/v1/sites/{site_id}
Content-Type: application/json

{
  "name": "站点名称",
  "altitude": 15.0
}
```

**删除站点**

```http
DELETE /api/v1/sites/{site_id}
```

#### 9.2.2 数据查询

**查询雷达数据**

```http
GET /api/v1/data/query?site_id=8&start_time=2026-03-10+00:00:00&end_time=2026-03-11+23:59:59&page=1&page_size=20
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| site_id | int | 否 | 站点ID |
| start_time | string | 否 | 开始时间 (YYYY-MM-DD HH:MM:SS) |
| end_time | string | 否 | 结束时间 (YYYY-MM-DD HH:MM:SS) |
| min_dbz | float | 否 | 最小dBZ值 |
| max_dbz | float | 否 | 最大dBZ值 |
| page | int | 否 | 页码（默认1） |
| page_size | int | 否 | 每页数量（默认20，最大100） |

**获取数据统计**

```http
GET /api/v1/data/statistics
```

#### 9.2.3 下载管理

**触发下载**

```http
POST /api/v1/downloads/trigger?count=None
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| count | int | 否 | 下载数量，None=全部 |

**获取下载状态**

```http
GET /api/v1/downloads/status
```

**获取下载历史**

```http
GET /api/v1/downloads/history?page=1&page_size=20
```

#### 9.2.4 图片管理

**获取图片列表**

```http
GET /api/v1/images/list?page=1&page_size=20&sort_by=observation_time&sort_order=desc
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码（默认1） |
| page_size | int | 否 | 每页数量（默认20） |
| sort_by | string | 否 | 排序字段（默认observation_time） |
| sort_order | string | 否 | 排序方向（asc/desc，默认desc） |
| status | string | 否 | 状态筛选（success/failed/pending） |

**获取图片详情**

```http
GET /api/v1/images/{image_id}
```

**预览图片**

```http
GET /api/v1/images/{image_id}/preview
```

**获取图片统计**

```http
GET /api/v1/images/stats/summary
```

**删除图片**

```http
DELETE /api/v1/images/{image_id}
```

#### 9.2.5 系统监控

**获取系统信息**

```http
GET /api/v1/system/info
```

**获取任务队列状态**

```http
GET /api/v1/system/tasks
```

**获取数据库状态**

```http
GET /api/v1/system/database
```

**获取系统日志**

```http
GET /api/v1/system/logs?level=INFO&page=1&page_size=50
```

### 9.3 API错误码

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

**错误响应示例**：

```json
{
  "code": 400,
  "message": "参数验证失败",
  "detail": "start_time格式错误，请使用格式: YYYY-MM-DD HH:MM:SS"
}
```

### 9.4 API调用示例

#### Python示例

```python
import requests

# 配置
BASE_URL = "http://localhost:8000"

# 查询站点8的雷达数据
response = requests.get(
    f"{BASE_URL}/api/v1/data/query",
    params={
        "site_id": 8,
        "start_time": "2026-03-10 00:00:00",
        "end_time": "2026-03-11 23:59:59",
        "page": 1,
        "page_size": 20
    }
)

data = response.json()
print(f"状态码: {data['code']}")
print(f"消息: {data['message']}")
print(f"数据量: {len(data['data']['items'])}")
```

#### JavaScript示例

```javascript
// 查询站点数据
const BASE_URL = 'http://localhost:8000';

async function querySiteData(siteId) {
  const response = await fetch(
    `${BASE_URL}/api/v1/data/query?site_id=${siteId}&page=1&page_size=20`
  );
  const data = await response.json();

  console.log('状态码:', data.code);
  console.log('消息:', data.message);
  console.log('数据量:', data.data.items.length);

  return data.data.items;
}

// 使用
querySiteData(8).then(items => {
  items.forEach(item => {
    console.log(`时间: ${item.observation_time}, dBZ: ${item.dbz_value}`);
  });
});
```

---

## 10. 常见问题FAQ

### 10.1 安装与配置

#### Q1: Python版本不兼容怎么办？

**A**: 确保使用Python 3.9或更高版本：
```bash
python3 --version
# 如果版本过低，请升级Python
```

#### Q2: npm install失败？

**A**: 尝试以下解决方案：
```bash
# 清除缓存
npm cache clean --force

# 使用淘宝镜像
npm install --registry=https://registry.npmmirror.com

# 或者使用cnpm
npm install -g cnpm --registry=https://registry.npmmirror.com
cnpm install
```

#### Q3: 数据库连接失败？

**A**: 检查以下几点：
1. MySQL服务是否启动
2. .env文件中的数据库配置是否正确
3. 数据库用户权限是否足够
4. 防火墙是否允许连接

```bash
# 测试数据库连接
mysql -h localhost -P 3308 -u root -p
```

### 10.2 数据下载

#### Q4: Cookie如何获取？

**A**: 详细步骤见3.3节"Cookie配置指南"

简述：
1. 登录 https://data.cma.cn/
2. F12打开开发者工具
3. Network标签
4. 查看请求头中的Cookie字段
5. 复制到 .env 文件

#### Q5: 下载失败怎么办？

**A**: 按以下步骤排查：
1. 检查Cookie是否过期
2. 运行测试脚本：`python3 scripts/test_single_download.py`
3. 查看错误日志
4. 重新获取Cookie
5. 检查网络连接

#### Q6: 下载速度慢？

**A**: 解决方案：
1. 修改下载间隔（见4.3节）
2. 检查网络带宽
3. 考虑在非高峰时段下载

### 10.3 数据处理

#### Q7: 站点超出范围怎么办？

**A**: 检查：
1. 站点经纬度是否在中国范围内（经度70-135，纬度15-55）
2. 雷达图片的覆盖范围
3. 使用 `show_processing_stats.py` 查看超出范围的站点数量

#### Q8: 数据处理失败？

**A**: 排查步骤：
1. 确认雷达图片文件存在
2. 检查图片文件是否损坏
3. 确认站点坐标正确
4. 查看错误日志

#### Q9: 如何重新处理数据？

**A**: 使用 `--force` 参数：
```bash
# 重新处理所有图片
python3 scripts/process_all_images.py --force

# 重新处理单张图片
python3 scripts/process_single_image.py --force
```

### 10.4 Web界面

#### Q10: 前端无法访问后端API？

**A**: 检查：
1. 后端服务是否启动（http://localhost:8000/docs）
2. 前端API配置是否正确（.env.local）
3. 浏览器控制台是否有CORS错误
4. 防火墙设置

#### Q11: 图表不显示？

**A**: 解决方案：
1. 检查ECharts是否正确加载
2. 查看浏览器控制台错误
3. 确认数据格式正确
4. 尝试刷新页面

#### Q12: 数据导出失败？

**A**: 检查：
1. 浏览器是否允许下载
2. 数据量是否过大
3. 网络连接是否稳定

### 10.5 性能优化

#### Q13: 系统运行缓慢？

**A**: 优化建议：
1. 增加数据库连接池大小
2. 启用Redis缓存
3. 优化SQL查询
4. 增加服务器资源

#### Q14: 数据库占用空间过大？

**A**: 清理方案：
```sql
-- 删除旧数据
DELETE FROM site_radar_data WHERE observation_time < '2026-01-01';

-- 优化表
OPTIMIZE TABLE site_radar_data;

-- 清空表
TRUNCATE TABLE site_radar_data;
```

### 10.6 其他问题

#### Q15: 如何备份数据？

**A**:
```bash
# 备份数据库
mysqldump -u root -p gfs_weather > backup_$(date +%Y%m%d).sql

# 备份图片文件
tar -czf images_backup_$(date +%Y%m%d).tar.gz backend/data/raw/
```

#### Q16: 如何恢复数据？

**A**:
```bash
# 恢复数据库
mysql -u root -p gfs_weather < backup_20260311.sql

# 恢复图片文件
tar -xzf images_backup_20260311.tar.gz
```

#### Q17: 如何更新系统？

**A**:
```bash
# 拉取最新代码
git pull origin main

# 更新后端依赖
cd backend
pip install -r requirements.txt

# 更新前端依赖
cd frontend/frontend
npm install

# 重启服务
```

---

## 11. 维护与监控

### 11.1 日常维护

#### 每日检查

- [ ] 检查后端服务状态
- [ ] 检查前端服务状态
- [ ] 检查数据下载是否正常
- [ ] 查看系统日志

#### 每周维护

- [ ] 清理过期数据
- [ ] 备份数据库
- [ ] 检查磁盘空间
- [ ] 性能监控分析

#### 每月维护

- [ ] 更新系统依赖
- [ ] 安全补丁更新
- [ ] 数据库优化
- [ ] 日志归档

### 11.2 监控指标

#### 系统指标

- CPU使用率 < 80%
- 内存使用率 < 80%
- 磁盘使用率 < 90%
- 网络流量正常

#### 应用指标

- API响应时间 < 1秒
- 下载成功率 > 95%
- 数据处理成功率 > 99%
- 数据库连接池使用率 < 80%

#### 业务指标

- 每日下载数据量
- 站点数据完整性
- 预测准确率
- 用户活跃度

### 11.3 日志管理

#### 日志位置

- **后端日志**: `backend/logs/`
- **前端日志**: 浏览器控制台
- **系统日志**: `/var/log/`

#### 日志级别

- **DEBUG**: 调试信息
- **INFO**: 一般信息
- **WARNING**: 警告信息
- **ERROR**: 错误信息
- **CRITICAL**: 严重错误

#### 日志查看

```bash
# 查看后端日志
tail -f backend/logs/app.log

# 查看错误日志
grep ERROR backend/logs/app.log

# 查看最近100行
tail -n 100 backend/logs/app.log
```

### 11.4 数据备份

#### 自动备份脚本

创建 `scripts/backup.sh`：

```bash
#!/bin/bash

# 备份目录
BACKUP_DIR="/path/to/backup"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份数据库
mysqldump -u root -p gfs_weather > $BACKUP_DIR/db_$DATE.sql

# 备份图片
tar -czf $BACKUP_DIR/images_$DATE.tar.gz backend/data/raw/

# 删除30天前的备份
find $BACKUP_DIR -name "db_*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "images_*.tar.gz" -mtime +30 -delete

echo "备份完成: $DATE"
```

#### 定时备份

```bash
# 编辑crontab
crontab -e

# 每天凌晨2点备份
0 2 * * * /path/to/backup.sh
```

---

## 12. 故障排查

### 12.1 常见错误及解决方案

#### 错误1: ModuleNotFoundError

**错误信息**:
```
ModuleNotFoundError: No module named 'requests'
```

**解决方案**:
```bash
# 激活虚拟环境
source venv/bin/activate

# 安装缺失的模块
pip install requests

# 或安装全部依赖
pip install -r requirements.txt
```

#### 错误2: 数据库连接失败

**错误信息**:
```
sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError) (2003, "Can't connect to MySQL server")
```

**解决方案**:
1. 检查MySQL服务是否启动
2. 检查.env中的数据库配置
3. 检查防火墙设置
4. 检查数据库用户权限

#### 错误3: Cookie认证失败

**错误信息**:
```
❌ 下载失败: 403 Forbidden
```

**解决方案**:
1. 重新登录 https://data.cma.cn/
2. 获取新的Cookie
3. 更新 .env 文件
4. 重启服务

#### 错误4: 图片文件损坏

**错误信息**:
```
PIL.UnidentifiedImageError: cannot identify image file
```

**解决方案**:
1. 删除损坏的图片文件
2. 重新下载图片
3. 检查磁盘空间

#### 错误5: 内存不足

**错误信息**:
```
MemoryError: Unable to allocate array
```

**解决方案**:
1. 减少批处理数量
2. 增加服务器内存
3. 使用分批处理

### 12.2 诊断工具

#### 系统状态检查

```bash
# 检查Python版本
python3 --version

# 检查Node版本
node --version

# 检查MySQL状态
systemctl status mysql

# 检查Redis状态
systemctl status redis

# 检查磁盘空间
df -h

# 检查内存使用
free -h

# 检查CPU使用
top
```

#### 数据库诊断

```sql
-- 检查连接数
SHOW PROCESSLIST;

-- 检查表大小
SELECT
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS "Size (MB)"
FROM information_schema.TABLES
WHERE table_schema = "gfs_weather"
ORDER BY (data_length + index_length) DESC;

-- 检查慢查询
SHOW VARIABLES LIKE 'slow_query_log';

-- 优化表
OPTIMIZE TABLE site_radar_data;
```

### 12.3 性能优化

#### 数据库优化

```sql
-- 添加索引
CREATE INDEX idx_observation_time ON site_radar_data(observation_time);
CREATE INDEX idx_site_time ON site_radar_data(site_id, observation_time);

-- 分析查询
EXPLAIN SELECT * FROM site_radar_data WHERE site_id = 8;
```

#### 应用优化

```python
# 使用连接池
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_MAX_OVERFLOW = 10

# 启用查询缓存
SQLALCHEMY_ECHO = False

# 批量插入
Session.bulk_save_objects(objects)
```

#### 系统优化

```bash
# 增加文件描述符限制
ulimit -n 4096

# 优化TCP参数
sysctl -w net.core.somaxconn=1024

# 增加共享内存
sysctl -w kernel.shmmax=2147483648
```

### 12.4 紧急恢复

#### 服务崩溃恢复

```bash
# 1. 检查服务状态
ps aux | grep uvicorn

# 2. 重启后端服务
pkill -f uvicorn
cd /Users/ranmufei/2026/leida_project/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# 3. 重启前端服务
cd /Users/ranmufei/2026/leida_project/frontend/frontend
npm run dev &
```

#### 数据损坏恢复

```bash
# 1. 停止应用
pkill -f uvicorn

# 2. 备份当前数据
cp gfs_weather.sql gfs_weather_backup.sql

# 3. 恢复最近的备份
mysql -u root -p gfs_weather < backup_20260311.sql

# 4. 重启服务
```

---

## 📞 技术支持

### 联系方式

- **Issues**: https://github.com/your-repo/issues
- **Email**: support@example.com
- **文档**: https://docs.example.com

### 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

---

## 📝 更新日志

### v1.0.0 (2026-03-11)

**新功能**：
- ✅ 完整的数据下载功能
- ✅ 站点管理系统
- ✅ 数据处理引擎
- ✅ Web管理界面
- ✅ API接口
- ✅ 数据查询与分析
- ✅ 系统监控

**修复**：
- 🐛 修复RGBA格式图片兼容性问题
- 🐛 修复API字段映射错误
- 🐛 优化下载速率控制

**优化**：
- ⚡ 提升数据处理速度（41.9条/秒）
- ⚡ 优化数据库查询性能
- ⚡ 改进错误处理机制

---

<div align="center">

**感谢使用气象雷达数据管理与预测平台！**

Made with ❤️ by AI Assistant

</div>
