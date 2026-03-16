# 🔑 CMA认证配置快速指南

**您的发现**: 需要在 https://data.cma.cn/ 登录后才能下载图片
**解决方案**: ✅ 已实现Cookie和Token认证支持

---

## ⚡ 3分钟快速配置

### 步骤1: 获取Cookie（1分钟）

1. 浏览器打开 https://data.cma.cn/ 并登录
2. 按 `F12` 打开开发者工具
3. 点击 `Application` → `Cookies` → `https://data.cma.cn`
4. 找到 `JSESSIONID` 或其他关键Cookie
5. 复制Cookie值（右键 → Copy）

### 步骤2: 配置Cookie（1分钟）

编辑 `backend/.env` 文件（或创建它）：

```bash
CMA_COOKIE=JSESSIONID=你的Cookie值
```

或多个Cookie：
```bash
CMA_COOKIE=JSESSIONID=xxx; auth_token=yyy; user_id=zzz
```

### 步骤3: 测试下载（1分钟）

重启后端服务并测试：

```bash
# 重启后端
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 测试下载
curl -X POST "http://localhost:8000/api/v1/downloads/trigger?count=1"
```

**期望结果**: `"成功下载 1 张图片"` ✅

---

## 🎯 已实现的功能

### 1. Cookie认证 ✅
```python
# download_service_real.py
def _get_cookies(self):
    """自动解析Cookie字符串为字典"""
    cookies = {}
    for item in self.cookie.split(';'):
        key, value = item.split('=', 1)
        cookies[key.strip()] = value.strip()
    return cookies
```

### 2. Token认证 ✅
```python
def _get_auth_headers(self):
    """构建带Token的请求头"""
    if self.auth_token:
        headers['Authorization'] = f'Bearer {self.auth_token}'
    return headers
```

### 3. 自动携带认证信息 ✅
```python
response = requests.get(
    download_url,
    headers=headers,    # ✅ 包含Token
    cookies=cookies     # ✅ 包含Cookie
)
```

### 4. 认证状态显示 ✅
```bash
🔐 认证状态: ✅ 已配置  # 服务启动时显示
```

---

## 📁 相关文件

| 文件 | 说明 |
|------|------|
| [backend/app/core/config.py:70-76](../backend/app/core/config.py) | 认证配置参数 |
| [backend/app/services/download_service_real.py:42-84](../backend/app/services/download_service_real.py) | Cookie/Token处理逻辑 |
| [docs/CMA_AUTHENTICATION_GUIDE.md](CMA_AUTHENTICATION_GUIDE.md) | 详细配置指南 |
| [backend/scripts/test_cookie_auth.py](../backend/scripts/test_cookie_auth.py) | Cookie测试工具 |

---

## 🧪 使用测试工具

运行交互式测试工具：

```bash
cd backend
python3 scripts/test_cookie_auth.py
```

按提示粘贴Cookie，自动测试是否能成功下载。

---

## ❓ 常见问题

### Q: Cookie从哪里获取？
**A**: 浏览器登录 https://data.cma.cn/ → F12 → Application → Cookies

### Q: 需要哪些Cookie？
**A**: 通常是 `JSESSIONID`，也可以尝试所有Cookie

### Q: Cookie多久过期？
**A**: 几小时到几天，过期后重新登录获取

### Q: 仍然下载失败怎么办？
**A**:
1. 检查Cookie格式是否正确
2. 尝试使用不同的Cookie
3. 确认网络连接正常
4. 运行测试工具验证

---

## 📚 详细文档

完整配置指南请查看:
**[docs/CMA_AUTHENTICATION_GUIDE.md](CMA_AUTHENTICATION_GUIDE.md)**

包含:
- Cookie获取详细步骤（附截图说明）
- 多种配置方式
- 故障排除指南
- 安全注意事项

---

## ✅ 验证成功标志

配置正确后，您应该看到：

```bash
# 服务启动
🔐 认证状态: ✅ 已配置

# 下载时
🍪 使用Cookie认证，包含 2 个Cookie
📥 正在下载: Z_RADA_C_BABJ_20260310...
✅ 下载成功: radar_20260311000000.png (524288 bytes)

# API返回
{
  "code": 200,
  "message": "成功下载 1 张图片"  ✅
}
```

---

**状态**: ✅ 功能已实现，等待配置Cookie测试
**优先级**: 🔥 高 - 这是解决下载问题的关键
**预计时间**: 3分钟完成配置
