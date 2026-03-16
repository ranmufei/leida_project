# 气象雷达数据管理与预测平台

<div align="center">

**一个完整的气象雷达数据自动化采集、处理、管理和预测系统**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green)](https://fastapi.tiangolo.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.3%2B-brightgreen)](https://vuejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📋 项目简介

本平台是一个企业级的气象雷达数据全流程自动化管理系统，实现了从数据自动采集、智能处理、Web管理到AI预测的完整闭环。

### ✨ 核心特性

- 🌍 **自动数据下载**：每6分钟自动从中国气象局下载最新雷达图片
- 🔄 **断点续传**：支持断点续传和自动重试（最多3次）
- 🎯 **智能坐标映射**：基于0.01°网格精度的经纬度到像素坐标转换
- 🎨 **RGB转dBZ**：12级标准气象色标，自动将RGB值转换为dBZ反射率
- 🤖 **AI预测引擎**：光流法 + Prophet时序预测 + 集成预测
- 📊 **数据可视化**：ECharts图表展示，支持置信区间显示
- 💻 **Web管理界面**：Vue.js 3 + Element Plus现代化UI
- 📈 **系统监控**：实时监控CPU、内存、任务队列、数据库连接池

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端展示层                            │
│  Vue.js 3 + Element Plus + ECharts + Pinia                  │
│  - 站点管理  - 数据查询  - 预测展示  - 系统监控              │
└─────────────────────────────────────────────────────────────┘
                              ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                       API网关层                              │
│  FastAPI + CORS + JWT认证 + 请求限流                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      业务逻辑层                              │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │
│  │数据处理引擎│ │预测引擎   │ │任务调度器 │ │API服务    │   │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      数据持久层                              │
│  MySQL 8.0 (业务数据 + 时序数据 + 文件存储)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.9+
- **Node.js**: 16+
- **MySQL**: 8.0+
- **Redis**: 6.0+

### 1. 克隆项目

```bash
git clone <repository-url>
cd leida_project
```

### 2. 配置数据库

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE gfs_weather CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 导入数据库结构
mysql -u root -p gfs_weather < docs/database.sql
```

### 3. 后端配置

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等

# 初始化数据库
python scripts/init_db.py
```

### 4. 前端配置

```bash
cd frontend

# 安装依赖
npm install

# 开发模式运行
npm run dev

# 生产环境构建
npm run build
```

### 5. 启动服务

使用提供的启动脚本：

```bash
# 启动所有服务
./backend/scripts/start.sh all

# 查看服务状态
./backend/scripts/start.sh status

# 停止所有服务
./backend/scripts/stop.sh
```

或手动启动：

```bash
# 1. 启动Redis
redis-server --daemonize yes

# 2. 启动Celery Worker
cd backend
celery -A app.tasks worker --loglevel=info --concurrency=4

# 3. 启动Celery Beat
celery -A app.tasks beat --loglevel=info

# 4. 启动后端API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 5. 启动前端
cd frontend
npm run dev
```

### 6. 访问系统

- **前端界面**: http://localhost:5173
- **API文档**: http://localhost:8000/docs
- **默认账号**: admin / admin123

---

## 📖 功能模块

### 1. 数据下载模块

- ✅ 自动每6分钟下载最新雷达图片
- ✅ 断点续传（检查数据库避免重复下载）
- ✅ 失败自动重试（最多3次）
- ✅ MD5校验确保文件完整性
- ✅ 下载日志和状态监控

### 2. 数据处理模块

- ✅ **坐标映射器**：经纬度 ↔ 像素坐标（0.01°精度）
- ✅ **颜色标尺解析器**：RGB → dBZ值（12级色标）
- ✅ **批量处理器**：多站点并行处理
- ✅ **数据质量验证**：质量评级（excellent/good/fair/poor）

### 3. 预测引擎

| 方法 | 适用场景 | 数据要求 | 预测时长 | 特点 |
|------|----------|----------|----------|------|
| **光流法** | 短期追踪 | 2张连续图片 | 0-2小时 | 基于云团运动轨迹 |
| **Prophet** | 时序预测 | 7天历史数据 | 2-6小时 | 考虑季节性趋势 |
| **集成预测** | 综合预测 | 满足两者 | 0-6小时 | 加权融合两者优势 |

### 4. Web管理平台

#### 数据查询
- 多维度筛选（站点、时间、数据源、dBZ范围）
- 实时统计（总数、平均值、最大/最小值）
- ECharts可视化（折线图、置信区间）
- CSV数据导出

#### 预测展示
- 预测控制面板（方法、时长配置）
- 预测结果展示（图表、表格）
- 置信区间可视化
- 历史预测记录

#### 下载管理
- 手动触发下载
- 任务状态监控
- 失败任务重试
- 下载统计图表

#### 系统监控
- 系统状态（CPU、内存、运行时间）
- Celery任务队列（活跃、等待、完成、失败）
- 数据库连接池（活跃、空闲连接）
- 磁盘空间（总容量、使用率）
- Redis状态（内存、键数、命中率）
- 系统日志查看

---

## 📁 项目结构

```
leida_project/
├── backend/                    # 后端项目
│   ├── app/
│   │   ├── api/               # API接口
│   │   │   └── v1/
│   │   │       └── endpoints/ # 各功能模块端点
│   │   ├── core/              # 核心配置
│   │   │   ├── config.py      # 配置管理
│   │   │   ├── database.py    # 数据库连接
│   │   │   └── security.py    # JWT认证
│   │   ├── models/            # SQLAlchemy模型
│   │   ├── schemas/           # Pydantic模式
│   │   ├── services/          # 业务逻辑
│   │   │   ├── download_service.py      # 下载服务
│   │   │   ├── processing_service.py    # 处理服务
│   │   │   ├── optical_flow_service.py  # 光流法
│   │   │   ├── prophet_service.py       # Prophet
│   │   │   └── prediction_service.py    # 预测服务
│   │   └── tasks/             # Celery任务
│   │       ├── download_tasks.py        # 下载任务
│   │       └── prediction_tasks.py      # 预测任务
│   ├── scripts/               # 工具脚本
│   │   ├── init_db.py         # 数据库初始化
│   │   ├── start.sh           # 启动脚本
│   │   └── stop.sh            # 停止脚本
│   ├── tests/                 # 测试文件
│   ├── requirements.txt       # Python依赖
│   └── .env.example           # 环境变量模板
├── frontend/                   # 前端项目
│   ├── src/
│   │   ├── api/               # API客户端
│   │   ├── components/        # 组件
│   │   │   └── charts/        # 图表组件
│   │   ├── layouts/           # 布局
│   │   ├── router/            # 路由
│   │   ├── stores/            # 状态管理
│   │   ├── types/             # 类型定义
│   │   └── views/             # 页面
│   │       ├── Data/          # 数据查询
│   │       ├── Prediction/    # 预测展示
│   │       ├── Download/      # 下载管理
│   │       └── System/        # 系统监控
│   ├── package.json           # Node依赖
│   └── vite.config.ts         # Vite配置
├── docs/                      # 文档
│   ├── database.sql           # 数据库结构
│   ├── API.md                 # API文档
│   ├── DEPLOYMENT.md          # 部署指南
│   ├── USER_GUIDE.md          # 用户手册
│   ├── PROGRESS.md            # 开发进度
│   └── PHASE_*.md             # 各阶段总结
└── README.md                  # 项目说明
```

---

## 🔧 技术栈

### 后端
- **FastAPI** 0.100+ - 高性能异步Web框架
- **SQLAlchemy** 2.0+ - Python ORM
- **Celery** 5.3+ - 分布式任务队列
- **Redis** - 消息代理和缓存
- **OpenCV** 4.8+ - 计算机视觉（光流法）
- **Prophet** 1.1+ - 时序预测
- **MySQL** 8.0+ - 关系型数据库

### 前端
- **Vue.js** 3.3+ - 渐进式JavaScript框架
- **Vite** 4.3+ - 下一代前端构建工具
- **TypeScript** 5.0+ - 类型安全
- **Element Plus** 2.3+ - 企业级UI组件库
- **ECharts** 5.4+ - 数据可视化
- **Pinia** 2.1+ - Vue 3状态管理

---

## 📊 数据库设计

### 核心表

| 表名 | 说明 | 主要字段 |
|------|------|----------|
| `users` | 用户表 | id, username, email, hashed_password |
| `sites` | 站点表 | id, name, code, longitude, latitude, region |
| `radar_images` | 雷达图片表 | id, observation_time, file_path, file_size |
| `site_radar_data` | 站点雷达数据 | site_id, observation_time, dbz_value, data_source |
| `site_predictions` | 预测结果表 | site_id, prediction_time, predicted_dbz, model_type |
| `download_logs` | 下载日志表 | id, observation_time, status, retry_count |

详细数据库设计见 [docs/database.sql](docs/database.sql)

---

## 🧪 测试

```bash
# 后端测试
cd backend
pytest tests/ -v

# 前端测试
cd frontend
npm run test
```

## 下载接口全部数据

cd /Users/ranmufei/2026/leida_project/backend
python3 scripts/download_all_fixed.py 


---

## 📚 文档

- [部署指南](docs/DEPLOYMENT.md) - 详细的部署步骤
- [用户手册](docs/USER_GUIDE.md) - 功能使用说明
- [API文档](docs/API.md) - RESTful API接口文档
- [开发进度](docs/PROGRESS.md) - 项目实施进度

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

---

## 📝 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👥 作者

- 开发团队 - AI Assistant

---

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [Vue.js](https://vuejs.org/) - 渐进式JavaScript框架
- [Element Plus](https://element-plus.org/) - 优秀的Vue 3组件库
- [ECharts](https://echarts.apache.org/) - 强大的数据可视化库
- [Prophet](https://facebook.github.io/prophet/) - Facebook时序预测工具

---

## 📮 联系方式

如有问题或建议，请通过以下方式联系：

- 提交Issue
- 发送邮件至项目维护者

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个Star支持一下！ ⭐**

Made with ❤️ by AI Assistant

</div>
