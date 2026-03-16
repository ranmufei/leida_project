# 气象雷达数据管理与预测平台 - 部署文档

## 📋 部署环境要求

### 硬件要求
- **CPU**: 4核心以上
- **内存**: 8GB以上
- **磁盘**: 100GB以上（用于存储雷达图片和数据库）
- **网络**: 稳定的互联网连接（用于下载雷达数据）

### 软件要求
- **操作系统**: Linux (推荐Ubuntu 20.04+) 或 Windows 10+
- **Python**: 3.9+
- **Node.js**: 16+
- **MySQL**: 8.0+
- **Redis**: 6.0+ (可选，用于缓存和任务队列)

---

## 🚀 快速部署指南

### 方式一：直接部署（推荐用于开发/测试）

#### 1. 克隆项目
```bash
git clone https://github.com/your-org/radar-platform.git
cd radar-platform
```

#### 2. 安装后端依赖
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 3. 配置环境变量
```bash
cp ../config/.env.example .env
# 编辑 .env 文件，修改数据库连接等配置
nano .env
```

#### 4. 初始化数据库
```bash
python scripts/init_db.py
```

#### 5. 启动后端服务
```bash
# 启动FastAPI服务器
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 启动Celery Worker（新终端）
celery -A app.tasks.celery_app worker --loglevel=info

# 启动Celery Beat（新终端）
celery -A app.tasks.celery_app beat --loglevel=info
```

#### 6. 安装前端依赖
```bash
cd ../frontend
npm install
```

#### 7. 配置前端环境变量
```bash
cp ../config/frontend_config.js src/config.js
# 根据需要修改配置
```

#### 8. 启动前端服务
```bash
npm run dev
```

#### 9. 访问系统
- 前端地址: http://localhost:5173
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

---

### 方式二：Docker部署（推荐用于生产）

#### 1. 使用Docker Compose
```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 2. 单独服务管理
```bash
# 启动MySQL和Redis
docker-compose up -d mysql redis

# 启动后端
docker-compose up -d backend celery_worker celery_beat

# 启动前端
docker-compose up -d frontend nginx
```

---

## 🔧 详细配置说明

### 数据库配置

#### 1. 创建数据库
```sql
CREATE DATABASE gfs_weather CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER 'admin'@'localhost' IDENTIFIED BY 'cqsyyxydxsyc6z';
GRANT ALL PRIVILEGES ON gfs_weather.* TO 'admin'@'localhost';
FLUSH PRIVILEGES;
```

#### 2. 导入表结构
```bash
mysql -u admin -p gfs_weather < docs/database.sql
```

#### 3. 验证安装
```sql
USE gfs_weather;
SHOW TABLES;
SELECT COUNT(*) FROM sites;
```

### 后端配置

#### 1. 编辑 `.env` 文件
```bash
# 数据库配置
DATABASE_HOST=localhost
DATABASE_PORT=3308
DATABASE_USER=admin
DATABASE_PASSWORD=cqsyyxydxsyc6z
DATABASE_NAME=gfs_weather

# JWT配置
JWT_SECRET_KEY=your-secret-key-change-in-production

# 下载配置
DOWNLOAD_BASE_URL=https://image.data.cma.cn/vis/RAD__B0_CR
DOWNLOAD_INTERVAL_MINUTES=6
```

#### 2. 安装Python依赖
```bash
pip install -r requirements.txt

# 核心依赖
# fastapi==0.100.0
# uvicorn[standard]==0.23.0
# sqlalchemy==2.0.0
# pymysql==1.1.0
# celery==5.3.0
# redis==4.6.0
# pandas==2.0.0
# numpy==1.24.0
# opencv-python==4.8.0
# prophet==1.1.4
# pillow==10.0.0
# requests==2.31.0
# python-multipart==0.0.6
# python-jose[cryptography]==3.3.0
# passlib[bcrypt]==1.7.4
# python-dotenv==1.0.0
# pydantic==2.0.0
# pydantic-settings==2.0.0
```

### 前端配置

#### 1. 编辑 `src/config.js`
```javascript
export default {
  apiBaseUrl: 'http://localhost:8000/api/v1',
  // 其他配置...
}
```

#### 2. 安装Node.js依赖
```bash
npm install

# 核心依赖
# "vue": "^3.3.0"
# "vue-router": "^4.2.0"
# "pinia": "^2.1.0"
# "element-plus": "^2.3.0"
# "axios": "^1.4.0"
# "echarts": "^5.4.0"
# "dayjs": "^1.11.0"
```

---

## 📊 初始化数据

### 1. 创建默认管理员用户
```bash
cd backend
python scripts/create_admin.py
```

### 2. 导入示例站点数据
```bash
python scripts/import_sites.py
```

### 3. 手动下载历史数据（可选）
```bash
python scripts/download_historical.py --days 30
```

---

## 🔍 服务验证

### 1. 检查后端API
```bash
curl http://localhost:8000/api/v1/system/status
```

### 2. 检查数据库连接
```bash
python scripts/check_database.py
```

### 3. 检查Celery任务
```bash
celery -A app.tasks.celery_app inspect active
```

### 4. 检查前端访问
浏览器访问: http://localhost:5173

---

## 🛠️ 常见问题排查

### 问题1: 数据库连接失败
```bash
# 检查MySQL服务状态
sudo systemctl status mysql

# 检查端口占用
netstat -an | grep 3308

# 测试连接
mysql -h localhost -P 3308 -u admin -p
```

### 问题2: Celery任务不执行
```bash
# 检查Redis连接
redis-cli ping

# 查看Celery日志
tail -f logs/celery.log

# 重启Celery服务
pkill -f celery
celery -A app.tasks.celery_app worker --loglevel=info
```

### 问题3: 雷达图片下载失败
```bash
# 测试网络连接
ping image.data.cma.cn

# 检查存储权限
ls -la data/raw/

# 手动测试下载
python scripts/test_download.py
```

### 问题4: 前端页面空白
```bash
# 清除缓存
npm run clean
npm install

# 检查API连接
curl http://localhost:8000/api/v1/sites

# 查看浏览器控制台错误
```

---

## 📈 性能优化建议

### 1. 数据库优化
```sql
-- 创建索引
CREATE INDEX idx_site_time ON site_radar_data(site_id, observation_time);

-- 分区表（按月）
ALTER TABLE site_radar_data PARTITION BY RANGE (TO_DAYS(observation_time))(...);

-- 定期清理旧日志
CALL sp_cleanup_old_logs(90);
```

### 2. Redis缓存配置
```bash
# 修改redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
```

### 3. Nginx反向代理配置
```nginx
upstream backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

---

## 🔒 安全配置

### 1. 修改默认密码
```bash
# 修改数据库密码
ALTER USER 'admin'@'localhost' IDENTIFIED BY 'new-strong-password';

# 修改JWT密钥
# 编辑 .env 文件
JWT_SECRET_KEY=your-new-secret-key
```

### 2. 配置HTTPS
```bash
# 使用Let's Encrypt免费证书
sudo certbot --nginx -d your-domain.com
```

### 3. 防火墙配置
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 📝 维护指南

### 日常维护
```bash
# 1. 查看系统状态
curl http://localhost:8000/api/v1/system/status

# 2. 检查日志
tail -f logs/app.log

# 3. 数据库备份
mysqldump -u admin -p gfs_weather > backup_$(date +%Y%m%d).sql

# 4. 清理旧日志
python scripts/cleanup_logs.py --days 30
```

### 定期任务
```bash
# 添加到crontab
crontab -e

# 每天凌晨2点备份数据库
0 2 * * * /path/to/backup_script.sh

# 每周日凌晨3点清理旧日志
0 3 * * 0 /path/to/cleanup_logs.py --days 30
```

---

## 📞 技术支持

### 日志文件位置
- 应用日志: `logs/app.log`
- Celery日志: `logs/celery.log`
- 下载日志: `logs/download.log`
- 错误日志: `logs/error.log`

### 配置文件位置
- 环境配置: `config/.env`
- 后端配置: `config/backend_config.yaml`
- 前端配置: `config/frontend_config.js`

### 获取帮助
- 查看API文档: http://localhost:8000/docs
- 查看部署文档: `docs/DEPLOYMENT.md`
- 提交问题: GitHub Issues

---

**文档版本**: v1.0.0
**最后更新**: 2024-03-10
**作者**: 气象雷达数据平台团队
