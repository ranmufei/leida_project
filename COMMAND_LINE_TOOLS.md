# 命令行工具完整索引

## 📑 目录

- [数据下载工具](#数据下载工具)
- [站点管理工具](#站点管理工具)
- [数据处理工具](#数据处理工具)
- [统计分析工具](#统计分析工具)
- [数据库管理工具](#数据库管理工具)
- [系统管理工具](#系统管理工具)

---

## 数据下载工具

### test_single_download.py

测试单张图片下载功能，用于诊断下载问题。

**位置**: `backend/scripts/test_single_download.py`

**用法**:
```bash
python3 scripts/test_single_download.py
```

**功能**:
- 测试Cookie认证是否正常
- 下载最新的一张雷达图片
- 显示详细的下载过程
- 验证文件保存是否成功

**输出示例**:
```
🧪 测试单张图片下载功能
📋 当前配置:
  API地址: https://data.cma.cn/...
  Cookie配置: ✅ 已配置

📸 第一张图片信息:
  文件名: Z_RADA_C_BABJ_20260311084854_P_DOR_ACHN_CREF_20260311_084200.png
  时间: 20260311084854
  URL: https://image.data.cma.cn/...

✅ 下载成功 (917916 bytes)
```

---

### download_all_fixed.py

下载全部雷达图片。

**位置**: `backend/scripts/download_all_fixed.py`

**用法**:
```bash
python3 scripts/download_all_fixed.py
```

**功能**:
- 下载API中的全部168张图片
- 每张图片间隔1秒（避免限流）
- 自动去重，不重复下载
- 使用原始文件名
- 显示下载进度和统计

**特性**:
- ✅ 断点续传
- ✅ 错误重试（最多3次）
- ✅ MD5校验
- ✅ 原始文件名保留

---

## 站点管理工具

### init_sites.py

站点数据初始化和管理。

**位置**: `backend/scripts/init_sites.py`

**用法**:
```bash
# 初始化站点
python3 scripts/init_sites.py init --yes

# 查看站点列表
python3 scripts/init_sites.py list

# 清空站点
python3 scripts/init_sites.py cleanup --yes
```

**子命令**:

#### init
初始化默认站点数据。

```bash
python3 scripts/init_sites.py init [--yes]
```

参数:
- `--yes, -y`: 自动确认所有提示

**默认站点**: 北京、上海、广州、深圳、成都、武汉、西安、杭州、南京、重庆

#### list
显示所有站点信息。

```bash
python3 scripts/init_sites.py list
```

#### cleanup
清空所有站点数据。

```bash
python3 scripts/init_sites.py cleanup [--yes]
```

---

## 数据处理工具

### process_all_images.py

批量处理雷达图片，生成站点数据。

**位置**: `backend/scripts/process_all_images.py`

**用法**:
```bash
# 处理全部图片
python3 scripts/process_all_images.py

# 处理指定数量图片
python3 scripts/process_all_images.py --limit 10

# 强制重新处理
python3 scripts/process_all_images.py --force

# 静默模式
python3 scripts/process_all_images.py --quiet
```

**参数**:

| 参数 | 简写 | 说明 |
|------|------|------|
| --limit | -l | 限制处理数量，None=处理全部 |
| --force | -f | 强制重新处理，覆盖已存在的数据 |
| --quiet | -q | 静默模式，不显示详细信息 |

**功能**:
- 读取已下载的雷达图片
- 对每个站点提取RGB值
- 转换为dBZ反射率
- 计算云影响因子
- 保存到数据库

**处理速度**: 约40条/秒

**输出示例**:
```
🚀 开始批量处理雷达图片
📍 找到 10 个启用站点
📸 找到 168 张雷达图片
📊 预计生成 1680 条站点数据

✅ 成功处理: 1680 条
⏭️  跳过（已存在）: 0 条
⚠️  超出范围: 0 条
❌ 错误: 0 条

⏱️  总耗时: 40.1 秒
⚡ 平均速度: 41.9 条/秒
```

---

### process_single_image.py

处理单张雷达图片（测试用）。

**位置**: `backend/scripts/process_single_image.py`

**用法**:
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

**参数**:

| 参数 | 说明 |
|------|------|
| --id | 雷达图片ID |
| --filename | 雷达图片文件名 |
| --force, -f | 强制重新处理，覆盖已存在的数据 |

**功能**:
- 显示图片详细信息
- 显示坐标映射信息
- 处理每个站点的数据
- 显示详细的处理结果
- 生成结果表格

**输出示例**:
```
📸 图片信息:
  ID: 173
  文件名: Z_RADA_C_BABJ_20260311084854_P_DOR_ACHN_CREF_20260311_084200.png
  观测时间: 2026-03-11 16:42:00

🗺️  坐标映射信息:
  经度范围: 82.67° ~ 127.33°
  纬度范围: 15.00° ~ 55.00°
  分辨率: 0.0331° × 0.0331°

[1/10] 处理站点: 北京 (BJ001)
  经纬度: (116.407400, 39.904200)
  像素坐标: (1019, 455)
  RGB值: (250, 250, 250)
  dBZ值: 65.00
  强度等级: extreme
  云影响因子: 0.000
  ✅ 已保存到数据库
```

---

## 统计分析工具

### show_processing_stats.py

显示站点雷达数据统计信息。

**位置**: `backend/scripts/show_processing_stats.py`

**用法**:
```bash
# 显示总体统计
python3 scripts/show_processing_stats.py

# 显示特定站点详情
python3 scripts/show_processing_stats.py --site BJ001

# 列出所有站点
python3 scripts/show_processing_stats.py --list-sites
```

**参数**:

| 参数 | 简写 | 说明 |
|------|------|------|
| --site | -s | 显示特定站点的详细信息（站点编码） |
| --list-sites | -l | 列出所有站点及其编码 |

**统计内容**:
- 基础统计（站点数、图片数、数据记录数）
- 数据来源分布
- 数据质量分布
- dBZ强度分布（带可视化条形图）
- 各站点数据统计
- 时间范围
- 最近24小时统计
- 数据完整性检查

**输出示例**:
```
📊 站点雷达数据统计

📈 基础统计
  总站点数: 10
  启用站点: 10
  雷达图片: 168
  数据记录: 1680
  完成度: 100.0%

🌩️  dBZ强度分布
  极端回波: █████████████████████████████████████████████████ 1668 条 (99.3%)
  中等回波: █ 7 条 (0.4%)
  弱回波:   3 条 (0.2%)

📍 各站点数据统计
  站点名称    编码    数据量    平均dBZ    最新时间
  北京        BJ001   168       65.00     2026-03-11 16:42
  上海        SH001   168       65.00     2026-03-11 16:42
```

---

## 数据库管理工具

### init_db.py

初始化数据库结构。

**位置**: `backend/scripts/init_db.py`

**用法**:
```bash
python3 scripts/init_db.py
```

**功能**:
- 创建所有数据表
- 创建索引
- 初始化基础数据

**注意**: 此操作会删除现有数据！

---

### check_db.py

检查数据库连接和结构。

**位置**: `backend/scripts/check_db.py`

**用法**:
```bash
python3 scripts/check_db.py
```

**功能**:
- 测试数据库连接
- 检查表结构
- 统计记录数
- 验证索引

---

## 系统管理工具

### start.sh

启动所有服务。

**位置**: `backend/scripts/start.sh`

**用法**:
```bash
# 启动所有服务
./scripts/start.sh all

# 启动特定服务
./scripts/start.sh backend
./scripts/start.sh frontend
./scripts/start.sh redis

# 查看服务状态
./scripts/start.sh status
```

**服务列表**:
- backend: FastAPI后端服务
- frontend: Vue.js前端服务
- redis: Redis服务
- celery: Celery Worker
- beat: Celery Beat

---

### stop.sh

停止所有服务。

**位置**: `backend/scripts/stop.sh`

**用法**:
```bash
./scripts/stop.sh
```

**功能**:
- 优雅地停止所有服务
- 清理临时文件
- 保存日志

---

## 常用命令组合

### 完整数据更新流程

```bash
# 1. 下载最新图片
python3 scripts/download_all_fixed.py

# 2. 处理数据
python3 scripts/process_all_images.py

# 3. 查看统计
python3 scripts/show_processing_stats.py
```

### 测试新站点

```bash
# 1. 添加站点（SQL方式）
mysql -u root -p gfs_weather
INSERT INTO sites (name, code, longitude, latitude, region, is_active)
VALUES ('测试站点', 'TEST001', 120.0, 30.0, '华东', 1);

# 2. 处理单张图片测试
python3 scripts/process_single_image.py

# 3. 查看站点统计
python3 scripts/show_processing_stats.py --site TEST001
```

### 系统重置

```bash
# 1. 清空雷达数据
mysql -u root -p gfs_weather -e "TRUNCATE TABLE site_radar_data;"

# 2. 删除图片文件
rm backend/data/raw/*.png

# 3. 重新下载
python3 scripts/download_all_fixed.py

# 4. 重新处理
python3 scripts/process_all_images.py
```

---

## 工具开发指南

### 创建新工具

1. 在 `backend/scripts/` 创建Python文件
2. 添加shebang: `#!/usr/bin/env python3`
3. 导入必要模块:
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   ```
4. 添加执行权限:
   ```bash
   chmod +x scripts/your_tool.py
   ```

### 工具模板

```python
#!/usr/bin/env python3
"""
工具描述
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """主函数"""
    print("工具功能")

if __name__ == "__main__":
    main()
```

---

## 附录

### 退出码

| 退出码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1 | 一般错误 |
| 2 | 误用参数 |
| 127 | 命令未找到 |

### 日志级别

| 级别 | 说明 |
|------|------|
| DEBUG | 调试信息 |
| INFO | 一般信息 |
| WARNING | 警告信息 |
| ERROR | 错误信息 |
| CRITICAL | 严重错误 |

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| DB_HOST | 数据库主机 | localhost |
| DB_PORT | 数据库端口 | 3308 |
| DB_USER | 数据库用户 | root |
| DB_NAME | 数据库名 | gfs_weather |
| CMA_COOKIE | CMA认证Cookie | - |

---

<div align="center">

**命令行工具索引 v1.0.0**

完整文档请查看 [USER_GUIDE.md](USER_GUIDE.md)

Made with ❤️ by AI Assistant

</div>
