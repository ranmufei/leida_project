# 气象雷达数据管理与预测平台 - 后端

基于 FastAPI + SQLAlchemy + MySQL 的气象雷达数据管理与预测平台后端服务。

## 📋 功能特性

- ✅ 用户认证与授权 (JWT)
- ✅ 站点管理 (CRUD)
- ✅ 雷达数据查询与导出
- ✅ 数据预测 (光流法 + Prophet)
- ✅ 系统监控与日志

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制配置文件
cp .env.example .env

# 编辑配置文件，修改数据库连接等信息
nano .env
```

### 3. 初始化数据库

```bash
# 方式1: 使用SQL脚本（推荐）
mysql -u admin -p gfs_weather < ../docs/database.sql

# 方式2: 使用Python脚本
python scripts/init_db.py
```

### 4. 启动服务

```bash
# 开发模式（支持热重载）
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📂 项目结构

```
backend/
├── app/
│   ├── api/                # API路由
│   │   └── v1/
│   │       ├── endpoints/  # API端点
│   │       └── __init__.py
│   ├── core/              # 核心配置
│   │   ├── config.py      # 应用配置
│   │   ├── database.py    # 数据库配置
│   │   └── security.py    # 安全认证
│   ├── models/            # 数据库模型
│   │   ├── site.py
│   │   ├── radar_image.py
│   │   ├── radar_data.py
│   │   ├── prediction.py
│   │   └── user.py
│   ├── schemas/           # Pydantic Schema
│   │   ├── site.py
│   │   ├── token.py
│   │   ├── user.py
│   │   └── common.py
│   ├── services/          # 业务逻辑
│   ├── tasks/             # Celery任务
│   └── main.py           # 应用入口
├── scripts/              # 脚本工具
│   ├── init_db.py       # 初始化数据库
│   └── check_db.py      # 检查数据库
├── requirements.txt      # 依赖包
├── .env.example         # 环境变量示例
└── README.md            # 项目说明
```

## 🔧 开发指南

### 添加新的API端点

1. 在 `app/api/v1/endpoints/` 创建新的路由文件
2. 在 `app/api/v1/__init__.py` 注册路由
3. 在 `app/schemas/` 定义请求/响应Schema
4. 在 `app/models/` 定义数据库模型（如需要）

### 数据库迁移

```bash
# 生成迁移文件
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行指定测试文件
pytest tests/test_api.py

# 生成覆盖率报告
pytest --cov=app tests/
```

## 🔐 默认账户

- **用户名**: admin
- **密码**: admin123
- **邮箱**: admin@example.com

## 📝 API示例

### 登录获取Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 获取站点列表

```bash
curl -X GET "http://localhost:8000/api/v1/sites?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 创建站点

```bash
curl -X POST "http://localhost:8000/api/v1/sites" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "北京站",
    "code": "BJ001",
    "longitude": 116.4074,
    "latitude": 39.9042,
    "region": "华北"
  }'
```

## 🐛 常见问题

### 数据库连接失败

```bash
# 检查MySQL服务状态
sudo systemctl status mysql

# 检查端口占用
netstat -an | grep 3308

# 测试连接
mysql -h localhost -P 3308 -u admin -p
```

### 依赖安装失败

```bash
# 升级pip
pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 📞 技术支持

- API文档: http://localhost:8000/docs
- 技术方案: `../方案.md`
- 部署文档: `../docs/DEPLOYMENT.md`

## 📄 许可证

MIT License
