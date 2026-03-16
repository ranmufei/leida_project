# 气象雷达数据管理平台 - 快速参考指南

<div align="center">

**版本：v1.0.0** | **更新日期：2026-03-11**

</div>

---

## 🚀 快速启动

### 启动服务

```bash
# 后端服务
cd /Users/ranmufei/2026/leida_project/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 前端服务（新终端）
cd /Users/ranmufei/2026/leida_project/frontend/frontend
npm run dev
```

### 访问系统

- **前端**: http://localhost:5173
- **API文档**: http://localhost:8000/docs

---

## 📥 常用命令

### 数据下载

```bash
# 测试下载
python3 scripts/test_single_download.py

# 下载全部图片
python3 scripts/download_all_fixed.py

# 查看图片管理
python3 scripts/show_processing_stats.py --list-sites
```

### 站点管理

```bash
# 初始化站点
python3 scripts/init_sites.py init --yes

# 查看站点列表
python3 scripts/init_sites.py list

# 查看站点详情
python3 scripts/show_processing_stats.py --site BJ001
```

### 数据处理

```bash
# 处理全部图片
python3 scripts/process_all_images.py

# 处理前10张图片
python3 scripts/process_all_images.py --limit 10

# 处理单张图片
python3 scripts/process_single_image.py

# 强制重新处理
python3 scripts/process_all_images.py --force
```

### 数据统计

```bash
# 查看总体统计
python3 scripts/show_processing_stats.py

# 查看特定站点
python3 scripts/show_processing_stats.py --site BJ001

# 列出所有站点
python3 scripts/show_processing_stats.py --list-sites
```

---

## 🔧 配置文件

### 后端配置 (.env)

```bash
# 数据库
DB_HOST=localhost
DB_PORT=3308
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=gfs_weather

# CMA API
CMA_API_URL=https://data.cma.cn/...
CMA_COOKIE=your_cookie_here

# 存储
RAW_DATA_DIR=../data/raw
```

### 前端配置 (.env.local)

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=气象雷达数据管理平台
```

---

## 📊 核心API接口

### 站点管理

```bash
# 获取站点列表
GET /api/v1/sites/?page=1&page_size=20

# 获取站点详情
GET /api/v1/sites/{site_id}

# 创建站点
POST /api/v1/sites/
```

### 数据查询

```bash
# 查询雷达数据
GET /api/v1/data/query?site_id=8&page=1&page_size=20

# 获取数据统计
GET /api/v1/data/statistics
```

### 下载管理

```bash
# 触发下载
POST /api/v1/downloads/trigger?count=None

# 获取下载状态
GET /api/v1/downloads/status
```

### 图片管理

```bash
# 获取图片列表
GET /api/v1/images/list?page=1&page_size=20

# 预览图片
GET /api/v1/images/{image_id}/preview

# 删除图片
DELETE /api/v1/images/{image_id}
```

---

## 🎯 常见操作

### 添加新站点

```bash
# 方式1：使用SQL
mysql -u root -p gfs_weather
INSERT INTO sites (name, code, longitude, latitude, altitude, region, is_active)
VALUES ('站点名', 'CODE001', 120.0, 30.0, 10.0, '华东', 1);

# 方式2：使用Python脚本
python3 -c "
from app.core.database import SessionLocal
from app.models.site import Site
db = SessionLocal()
site = Site(name='站点名', code='CODE001', longitude=120.0, latitude=30.0, is_active=True)
db.add(site)
db.commit()
"
```

### 重新处理数据

```bash
# 重新处理所有数据
python3 scripts/process_all_images.py --force

# 重新处理特定图片
python3 scripts/process_single_image.py --id 1 --force
```

### 备份数据

```bash
# 备份数据库
mysqldump -u root -p gfs_weather > backup_$(date +%Y%m%d).sql

# 备份图片
tar -czf images_backup_$(date +%Y%m%d).tar.gz backend/data/raw/
```

### 恢复数据

```bash
# 恢复数据库
mysql -u root -p gfs_weather < backup_20260311.sql

# 恢复图片
tar -xzf images_backup_20260311.tar.gz
```

---

## 🐛 故障排查

### 服务无法启动

```bash
# 检查端口占用
lsof -i :8000
lsof -i :5173

# 杀死占用进程
kill -9 <PID>

# 重新启动
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 数据库连接失败

```bash
# 测试连接
mysql -h localhost -P 3308 -u root -p

# 检查MySQL状态
systemctl status mysql

# 启动MySQL
systemctl start mysql
```

### 下载失败

```bash
# 1. 测试Cookie
python3 scripts/test_single_download.py

# 2. 更新Cookie（.env文件）
CMA_COOKIE=新的Cookie值

cookie 获取， 登陆国家气象局 https://data.cma.cn/data/online.html?t=6 ，在处于登陆状态的前提下 在浏览器下 F12 随便找到一个接口的 的cookie 复制到env文件中。 
# 3. 重启服务


backend/.env  

```

### 清理数据

```bash
# 清空雷达数据表
mysql -u root -p gfs_weather -e "TRUNCATE TABLE site_radar_data;"

# 删除旧图片
rm backend/data/raw/Z_RADA_C_*.png

# 重置自增ID
mysql -u root -p gfs_weather -e "ALTER TABLE site_radar_data AUTO_INCREMENT=1;"
```

---

## 📈 性能优化

### 数据库优化

```sql
-- 添加索引
CREATE INDEX idx_site_observation ON site_radar_data(site_id, observation_time);
CREATE INDEX idx_observation_time ON site_radar_data(observation_time);

-- 优化表
OPTIMIZE TABLE site_radar_data;

-- 分析查询
EXPLAIN SELECT * FROM site_radar_data WHERE site_id = 8;
```

### 应用优化

```python
# 批量插入（大于1000条时使用）
Session.bulk_save_objects(objects)

# 使用连接池
SQLALCHEMY_POOL_SIZE = 20
```

---

## 🔍 系统监控

### 查看系统状态

```bash
# CPU使用率
top

# 内存使用
free -h

# 磁盘空间
df -h

# 进程状态
ps aux | grep uvicorn
```

### 查看日志

```bash
# 后端日志
tail -f backend/logs/app.log

# 错误日志
grep ERROR backend/logs/app.log

# 最近100行
tail -n 100 backend/logs/app.log
```

---

## 📞 获取帮助

### 查看文档

- **完整文档**: [USER_GUIDE.md](USER_GUIDE.md)
- **API文档**: http://localhost:8000/docs
- **项目README**: [README.md](README.md)

### 常见问题

详见 [USER_GUIDE.md](USER_GUIDE.md) 第10节

### 技术支持

- **Issues**: GitHub Issues
- **Email**: support@example.com

---

## 📝 快速参考卡片

### 数据处理流程

```
下载图片 → 初始化站点 → 处理数据 → 查询分析
```

### 核心命令

| 操作 | 命令 |
|------|------|
| 初始化站点 | `python3 scripts/init_sites.py init --yes` |
| 下载图片 | `python3 scripts/download_all_fixed.py` |
| 处理数据 | `python3 scripts/process_all_images.py` |
| 查看统计 | `python3 scripts/show_processing_stats.py` |

### 重要文件

| 文件 | 说明 |
|------|------|
| `backend/.env` | 后端配置文件 |
| `frontend/frontend/.env.local` | 前端配置文件 |
| `backend/data/raw/` | 雷达图片存储目录 |
| `backend/logs/` | 后端日志目录 |

### 默认端口

| 服务 | 端口 |
|------|------|
| 后端API | 8000 |
| 前端Web | 5173 |
| MySQL | 3308 |
| Redis | 6379 |

---

<div align="center">

**快速参考指南 v1.0.0**

完整文档请查看 [USER_GUIDE.md](USER_GUIDE.md)

Made with ❤️ by AI Assistant

</div>
