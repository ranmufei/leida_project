# NMC雷达图片下载服务 - 使用文档

## 📋 目录
- [概述](#概述)
- [快速开始](#快速开始)
- [详细说明](#详细说明)
- [API参考](#api参考)
- [常见问题](#常见问题)

---

## 概述

### 特点
- ✅ **无需认证**：直接构造URL，不需要Cookie或Token
- ✅ **自动时间对齐**：自动对齐到6分钟边界
- ✅ **自动时区转换**：URL使用UTC时间，存储使用北京时间
- ✅ **完全兼容**：与旧下载方式图片格式完全一致

### URL格式
```
https://image.nmc.cn/product/YYYY/MM/DD/RDCP/SEVP_AOC_RDCP_SLDAS3_ECREF_ACHN_L88_PI_YYYYMMDDHHmmssSSS.PNG
```

**示例**：
```
https://image.nmc.cn/product/2026/03/15/RDCP/SEVP_AOC_RDCP_SLDAS3_ECREF_ACHN_L88_PI_20260315104200000.PNG
```

### 时间规则
- **时间戳格式**：17位数字 `YYYYMMDDHHmmssSSS`
- **UTC时间**：URL中时间是UTC（比北京时间晚8小时）
- **6分钟间隔**：分钟必须是6的倍数：`00, 06, 12, 18, 24, 30, 36, 42, 48, 54`
- **最新图片延迟**：通常与当前时间有 **30分钟左右延迟**

---

## 快速开始

### 1. 测试单张下载

```bash
cd /data/weather3.0/leida_project/backend
python3 scripts/test_single_download.py
```

**输出示例**：
```
🧪 测试单张图片下载功能（NMC直接URL）
📅 测试时间（北京时间）: 2026-03-15 18:42:00
🌐 生成的URL: https://image.nmc.cn/product/2026/03/15/RDCP/SEVP_AOC_RDCP_SLDAS3_ECREF_ACHN_L88_PI_20260315104200000.PNG
✅ 下载成功: radar_20260315_184200.png
```

### 2. 下载最近24小时数据

```bash
python3 scripts/download_all_simple.py
```

### 3. 下载指定数量

```bash
# 下载最近50张图片
python3 scripts/batch_download_radar.py --count 50

# 下载最近24小时
python3 scripts/batch_download_radar.py --hours 24
```

### 4. 下载指定时间范围

```bash
python3 scripts/batch_download_radar.py \
  --start "2026-03-15 00:00:00" \
  --end "2026-03-16 00:00:00"
```

### 5. 处理图片生成雷达数据

```bash
# 处理所有已下载的图片
python3 scripts/process_all_images.py

# 只处理最新的10张图片
python3 scripts/process_all_images.py --limit 10

# 强制重新处理
python3 scripts/process_all_images.py --force
```

---

## 详细说明

### 时间转换示例

| 北京时间 | UTC时间 | URL时间戳 |
|----------|---------|-----------|
| 2026-03-15 16:42:00 | 2026-03-15 08:42:00 | 20260315104200000 |
| 2026-03-15 18:42:00 | 2026-03-15 10:42:00 | 20260315104200000 |
| 2026-03-16 06:30:00 | 2026-03-15 22:30:00 | 20260315223000000 |

**注意**：
- 北京时间 = UTC时间 + 8小时
- 分钟自动对齐到6的倍数
- 秒和毫秒固定为000

### 下载时间范围建议

由于最新图片通常有30分钟左右的延迟，建议：

```python
from datetime import datetime, timedelta

# 推荐方式：结束时间设为30分钟前
end_time = datetime.now() - timedelta(minutes=30)
start_time = end_time - timedelta(hours=24)

# 下载最近24小时（不含最近30分钟）
stats = downloader.download_range(start_time, end_time)
```

### 可用脚本列表

| 脚本 | 功能 | 使用场景 |
|------|------|----------|
| `test_single_download.py` | 测试单张下载 | 调试、验证URL生成 |
| `test_url_generation.py` | 测试URL生成 | 验证时间转换逻辑 |
| `download_all_simple.py` | 简单批量下载 | 日常下载任务 |
| `download_all_fixed.py` | 自定义范围下载 | 指定时间范围 |
| `batch_download_radar.py` | 高级批量下载 | 灵活的下载选项 |
| `process_all_images.py` | 处理图片生成数据 | 提取站点雷达数据 |
| `process_single_image.py` | 处理单张图片 | 测试处理流程 |
| `show_processing_stats.py` | 显示处理统计 | 查看数据库状态 |

---

## API参考

### NMCRadarImageDownloader 类

#### 初始化
```python
from app.services.download_service_nmc import NMCRadarImageDownloader

downloader = NMCRadarImageDownloader()
```

#### 主要方法

##### download_image()
下载指定时间的图片

```python
success, message, file_path = downloader.download_image(
    beijing_time=datetime(2026, 3, 15, 18, 42, 0),  # 北京时间
    force=False  # 是否强制重新下载
)
```

##### download_range()
下载指定时间范围的图片

```python
stats = downloader.download_range(
    start_time=datetime(2026, 3, 15, 0, 0, 0),
    end_time=datetime(2026, 3, 16, 0, 0, 0),
    force=False,
    use_beijing_time=True  # 输入时间是否为北京时间
)

# 返回值示例：
# {
#     'total': 240,      # 总计处理
#     'success': 100,    # 成功下载
#     'skipped': 138,    # 已存在跳过
#     'failed': 2        # 下载失败
# }
```

##### download_latest()
下载最新的N张图片

```python
stats = downloader.download_latest(
    count=50,  # 下载数量
    force=False
)
```

##### 辅助方法

```python
# UTC时间转北京时间
beijing_time = downloader.utc_to_beijing(utc_time)

# 北京时间转UTC时间
utc_time = downloader.beijing_to_utc(beijing_time)

# 对齐到6分钟边界
aligned_time = downloader.align_to_6_minutes(datetime.now())

# 构建URL
url = downloader.build_url(utc_time)

# 获取下载统计
stats = downloader.get_download_statistics()
```

---

## 常见问题

### Q1: 为什么下载失败？
**A**: 可能原因：
1. 该时间点暂无图片数据（30分钟延迟）
2. 网络连接问题
3. 图片URL格式已变更

**解决方法**：
```bash
# 1. 测试单张下载
python3 scripts/test_single_download.py

# 2. 检查时间范围，避免下载最近的30分钟
end_time = datetime.now() - timedelta(minutes=30)
```

### Q2: 时间如何选择？
**A**:
1. **分钟必须是6的倍数**：00, 06, 12, 18, 24, 30, 36, 42, 48, 54
2. **考虑30分钟延迟**：避免下载最近30分钟的图片
3. **自动对齐**：输入任意时间，系统自动对齐到最近的6分钟边界

```python
# 错误：指定非6分钟倍数的时间
# ✅ 正确：系统会自动对齐
downloader.download_image(datetime(2026, 3, 15, 18, 45, 0))
# 实际下载：18:42:00（向下对齐）
```

### Q3: 如何确保下载完整数据？
**A**:
```python
# 1. 检查数据库中的下载记录
stats = downloader.get_download_statistics()
print(f"总记录: {stats['total']}")
print(f"成功: {stats['success']}")

# 2. 查看处理统计
python3 scripts/show_processing_stats.py

# 3. 重新下载失败的图片
python3 scripts/batch_download_radar.py --hours 24 --force
```

### Q4: 新下载方式与旧方式的区别？
| 特性 | 旧方式（CMA API） | 新方式（NMC直接URL） |
|------|------------------|---------------------|
| 认证 | 需要Cookie/Token | 无需认证 ✅ |
| 图片来源 | API动态获取 | 直接URL构造 |
| 时间格式 | 原始时间 | UTC时间 |
| 图片质量 | 完全相同 | 完全相同 |
| 图例/色标 | 完全相同 | 完全相同 |

### Q5: 如何定时自动下载？
**A**: 使用 cron 定时任务
```bash
# 编辑 crontab
crontab -e

# 每6分钟下载一次（考虑延迟，从7分钟前开始）
*/6 * * * * cd /data/weather3.0/leida_project/backend && python3 -c "
from datetime import datetime, timedelta
from app.services.download_service_nmc import NMCRadarImageDownloader
d = NMCRadarImageDownloader()
end = datetime.now() - timedelta(minutes=7)
start = datetime.now() - timedelta(minutes=13)
d.download_range(start, end)
" >> /var/log/radar_download.log 2>&1
```

---

## 完整工作流程示例

```bash
#!/bin/bash
# radar_pipeline.sh - 完整的雷达数据获取流程

# 1. 下载最近24小时的图片（不含最近30分钟）
echo "📥 开始下载雷达图片..."
python3 scripts/batch_download_radar.py --hours 24

# 2. 处理图片生成站点数据
echo "🔄 开始处理图片生成站点数据..."
python3 scripts/process_all_images.py --limit 1000

# 3. 查看统计信息
echo "📊 处理统计："
python3 scripts/show_processing_stats.py

echo "✅ 流程完成！"
```

---

## 配置文件位置

- **数据库配置**: `backend/app/core/config.py`
- **下载服务**: `backend/app/services/download_service_nmc.py`
- **处理服务**: `backend/app/services/processing_service.py`
- **环境变量**: `backend/.env`

---

## 版本历史

- **v2.0** (2026-03-15)
  - 新增NMC直接URL下载方式
  - 移除Cookie认证依赖
  - 自动UTC/北京时间转换
  - 自动时间对齐

- **v1.0** (早期版本)
  - CMA API + Cookie认证方式
  - 需要手动获取Cookie

---

## 技术支持

如遇问题，请检查：
1. Python依赖是否完整：`pip install -r requirements.txt`
2. 数据库连接是否正常
3. 网络连接是否稳定
4. 时间选择是否正确（考虑30分钟延迟）
