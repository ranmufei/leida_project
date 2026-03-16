# 雷达图片下载使用说明

## ✅ 好消息：下载功能已修复！

之前的下载问题已经解决，现在可以正常下载图片了。

## 📋 两种下载方式

### 方式1：Web界面下载

1. 启动后端服务：
```bash
cd /Users/ranmufei/2026/leida_project/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

2. 启动前端服务（另一个终端）：
```bash
cd /Users/ranmufei/2026/leida_project/frontend/frontend
npm run dev
```

3. 打开浏览器访问：`http://localhost:5173`

4. 点击"图片管理"菜单

5. 点击"立即下载"按钮，系统会：
   - 下载全部168张图片
   - 自动跳过已下载的图片
   - 每张图片间隔1秒（避免频率过快）
   - 显示下载进度和统计

### 方式2：命令行脚本下载

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

## 🔧 环境要求

### 系统Python环境（推荐）
使用系统Python 3，无需虚拟环境：
```bash
python3 --version  # 确认是Python 3.10+
```

### 如果使用虚拟环境
如果需要在虚拟环境中使用，请先安装依赖：
```bash
cd /Users/ranmufei/2026/leida_project/backend
source venv/bin/activate  # 激活虚拟环境
pip install requests sqlalchemy pymysql  # 安装必需的依赖
```

## 🍪 Cookie配置

### 为什么需要Cookie？
中国气象局API需要登录认证才能下载图片。

### 如何获取Cookie？

1. 访问 https://data.cma.cn/ 并登录
2. 打开浏览器开发者工具 (F12)
3. 切换到 "Network" (网络) 标签
4. 刷新页面
5. 点击任意请求
6. 查看 "Request Headers" (请求头)
7. 找到 "Cookie" 字段，复制其值

### 更新Cookie配置
编辑 `backend/.env` 文件：
```bash
CMA_COOKIE=你的Cookie值
```

**重要提示**：
- Cookie会过期，如果下载失败请重新获取
- 不要分享Cookie，它包含你的登录信息
- Cookie格式：`key1=value1; key2=value2; key3=value3`

## 📊 下载统计

下载完成后会显示：
- 总计：尝试下载的图片数量
- 成功：成功下载的图片数量
- 跳过：已存在未重复下载的图片数量
- 失败：下载失败的图片数量

## ⚙️ 功能特性

✅ 自动去重：已下载的图片不会重复保存
✅ 断点续传：支持中断后续传
✅ 原始文件名：使用API原始文件名（包含时间信息）
✅ 速率限制：每张图片间隔1秒，避免API限流
✅ 错误重试：失败自动重试3次
✅ 进度显示：实时显示下载进度
✅ 数据库记录：自动记录下载状态和元信息

## 📁 下载位置

图片保存在：`backend/data/raw/`

文件名格式：`Z_RADA_C_BABJ_20260310160658_P_DOR_ACHN_CREF_20260310_160000.png`

## ❓ 常见问题

### Q1: 下载失败怎么办？
A:
1. 检查Cookie是否过期，重新登录获取
2. 检查网络连接
3. 查看错误日志了解详细原因

### Q2: 如何查看已下载的图片？
A:
1. Web界面：访问"图片管理"页面
2. 文件系统：查看 `backend/data/raw/` 目录
3. 数据库：查看 `radar_images` 表

### Q3: 可以重新下载失败的图片吗？
A: 可以，使用 `force=True` 参数：
```python
downloader.download_latest_from_api(count=None, force=True)
```

### Q4: 下载速度慢怎么办？
A: 目前设置为1秒间隔以避免API限流。如果需要调整，修改：
```python
# app/services/download_service_real.py 第418行
time.sleep(1)  # 改为更小的值，如 time.sleep(0.5)
```

## 🎉 测试结果

最新测试（2026-03-11）：
- ✅ 单张图片下载：成功
- ✅ Cookie认证：正常工作
- ✅ 数据库保存：正常工作
- ✅ 文件保存：917916 bytes
- ✅ 原始文件名：正确保留

开始下载吧！🚀
