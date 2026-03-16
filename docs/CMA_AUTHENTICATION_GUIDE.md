# 🔐 CMA API认证配置指南

**更新日期**: 2026-03-11
**问题发现**: 用户发现需要在 https://data.cma.cn/ 登录后才能下载图片
**解决方案**: 实现Cookie和Token认证支持

---

## 🎯 问题分析

### 用户的发现
> "关于图片下载问题，我发现和是否登陆有关，我只要在 https://data.cma.cn/ 登陆了，再去打开图片地址就可以下载成功。这是否需要携带cookie或者token?"

**您的发现非常准确！** CMA API确实需要身份认证。

### 认证机制
CMA使用 **Session/Cookie** 认证机制：
1. 用户在 https://data.cma.cn/ 登录
2. 服务器返回认证Cookie
3. 后续请求携带此Cookie才能下载图片

---

## ✅ 已实现的认证支持

### 1. 配置参数（config.py）

```python
# CMA API认证配置
CMA_API_URL: str = "https://data.cma.cn/weatherGis/web/bmd/VisDataDef/getVisData?datacode=RAD__B0_CR"
CMA_BASE_URL: str = "https://data.cma.cn"
# CMA认证Cookie（从浏览器获取）
CMA_COOKIE: str = ""  # 格式: "key1=value1; key2=value2"
# 或者使用认证Token
CMA_AUTH_TOKEN: str = ""  # JWT Token或其他认证token
```

### 2. 下载服务更新（download_service_real.py）

#### 新增方法
```python
def _get_auth_headers(self) -> Dict[str, str]:
    """构建带认证信息的请求头"""
    headers = {
        'User-Agent': 'Mozilla/5.0 ...',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://data.cma.cn/',
    }

    if self.auth_token:
        headers['Authorization'] = f'Bearer {self.auth_token}'

    return headers

def _get_cookies(self) -> Dict[str, str]:
    """解析Cookie字符串为字典"""
    if not self.cookie:
        return {}

    cookies = {}
    for item in self.cookie.split(';'):
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key.strip()] = value.strip()

    return cookies
```

#### 下载请求携带认证
```python
def download_from_api(self, image_info: Dict, force: bool = False):
    # 准备认证信息
    headers = self._get_auth_headers()
    cookies = self._get_cookies()

    # 发送HTTP请求（携带认证信息）
    response = requests.get(
        download_url,
        stream=True,
        timeout=self.timeout,
        headers=headers,
        cookies=cookies  # ✅ 关键：携带Cookie
    )
```

---

## 📖 如何获取CMA Cookie

### 方法1: 浏览器开发者工具（推荐）

#### Chrome/Edge浏览器
1. **登录CMA网站**
   - 访问: https://data.cma.cn/
   - 登录您的账号

2. **打开开发者工具**
   - Windows: `F12` 或 `Ctrl + Shift + I`
   - Mac: `Cmd + Option + I`

3. **查看Cookie**
   - 点击 `Application` 标签（或 `Storage`）
   - 左侧菜单 → `Cookies` → `https://data.cma.cn`
   - 找到关键的Cookie（通常包含 `sessionid`, `token`, `JSESSIONID` 等）

4. **复制Cookie值**
   - 右键点击Cookie → `Copy`
   - 或手动记录 `Name` 和 `Value`

#### Firefox浏览器
1. 登录 https://data.cma.cn/
2. 打开开发者工具（`F12`）
3. 点击 `Storage` 标签
4. 左侧 → `Cookies` → `https://data.cma.cn`
5. 查看并复制Cookie值

### 方法2: 浏览器Network面板

1. 登录 https://data.cma.cn/
2. 打开开发者工具（`F12`）
3. 切换到 `Network` 标签
4. 访问任意图片URL
5. 点击请求 → 查看 `Request Headers`
6. 找到 `Cookie:` 字段
7. 复制整个Cookie字符串

### 示例Cookie格式

```
JSESSIONID=abc123xyz; session_id=456def; auth_token=789ghi
```

或单个Cookie：
```
JSESSIONID=A1B2C3D4E5F6G7H8I9J0
```

---

## 🔧 配置步骤

### 方式1: 环境变量配置

创建或编辑 `backend/.env` 文件：

```bash
# CMA认证配置
CMA_COOKIE=JSESSIONID=your_session_id_here; auth_token=your_token_here
# 或者
CMA_AUTH_TOKEN=your_bearer_token_here
```

### 方式2: 直接修改配置文件

编辑 `backend/app/core/config.py`：

```python
class Settings(BaseSettings):
    # ...
    # CMA认证Cookie（从浏览器获取）
    CMA_COOKIE: str = "JSESSIONID=abc123; session_id=xyz789"  # 替换为您的Cookie
    # 或者使用认证Token
    CMA_AUTH_TOKEN: str = ""  # 如果使用Token，填在这里
```

---

## 🧪 测试认证配置

### 1. 查看认证状态

启动后端服务时，会显示认证状态：

```bash
✅ 初始化真实雷达下载服务
📡 API地址: https://data.cma.cn/weatherGis/web/bmd/VisDataDef/getVisData?datacode=RAD__B0_CR
💾 保存目录: ../data/raw
🔐 认证状态: ✅ 已配置    # ← 应该显示"已配置"
```

### 2. 测试下载

```bash
curl -X POST "http://localhost:8000/api/v1/downloads/trigger?count=1"
```

**期望结果**:
```json
{
  "code": 200,
  "message": "成功下载 1 张图片",  // ← 应该成功！
  "data": {
    "statistics": {
      "success": 1,  // ← success应该大于0
      "failed": 0
    }
  }
}
```

### 3. 查看详细日志

后端日志会显示：
```bash
🍪 使用Cookie认证，包含 2 个Cookie
📥 正在下载: Z_RADA_C_BABJ_20260310160658_P_DOR_ACHN_CREF_20260310_160000.png
🌐 URL: https://image.data.cma.cn/vis/RAD__B0_CR/20260310/...
✅ 下载成功: radar_20260311000000.png (524288 bytes)
```

---

## 🎯 Cookie选择指南

### 哪些Cookie是必需的？

通常需要以下类型的Cookie：

1. **Session ID**
   - 名称通常为: `JSESSIONID`, `SESSIONID`, `sessionid`
   - 作用: 标识用户会话

2. **认证Token**
   - 名称通常为: `auth_token`, `access_token`, `token`
   - 作用: 认证凭证

3. **用户标识**
   - 名称通常为: `user_id`, `uid`, `username`
   - 作用: 标识用户身份

### 推荐配置

**最佳实践**: 携带所有CMA域名下的Cookie

```
# 完整Cookie字符串（推荐）
JSESSIONID=xxx; auth_token=yyy; user_id=zzz; language=zh-CN

# 或最小配置（可能不够）
JSESSIONID=xxx
```

---

## ⚠️ 注意事项

### 1. Cookie过期

- **Session Cookie**: 通常几小时到几天过期
- **持久Cookie**: 可能保存数周
- **解决方案**: 重新登录获取新Cookie

### 2. 安全性

- **不要提交Cookie到Git仓库**
- **使用环境变量存储**
- **定期更换Cookie**

### 3. IP限制

CMA可能会：
- 绑定Cookie到特定IP
- 检测异常访问模式
- 限制API调用频率

### 4. Cookie格式

- 多个Cookie用`; `分隔（注意空格）
- 不要包含换行符
- URL编码特殊字符（如果有）

---

## 🔍 故障排除

### 问题1: 下载仍然失败

**检查清单**:
- [ ] Cookie是否正确配置
- [ ] Cookie是否过期（重新登录）
- [ ] 网络连接是否正常
- [ ] 是否被CMA限制访问

### 问题2: 认证状态显示"未配置"

**原因**: `CMA_COOKIE` 和 `CMA_AUTH_TOKEN` 都为空

**解决**: 配置至少一个认证凭证

### 问题3: Cookie无效

**症状**: 日志显示携带Cookie但仍失败

**可能原因**:
1. Cookie格式错误
2. Cookie已过期
3. Cookie不完整（缺少关键字段）

**解决**:
1. 重新获取Cookie
2. 尝试携带所有Cookie
3. 联系CMA获取API密钥

---

## 📋 配置示例

### 完整示例（.env文件）

```bash
# CMA API认证配置
CMA_COOKIE=JSESSIONID=ABCD1234EFGH5678; auth_token=ijkl9012mnop3456; user_id=9999

# 或者使用Token
CMA_AUTH_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 代码中动态设置

```python
from app.core.config import settings

# 运行时设置Cookie
settings.CMA_COOKIE = "JSESSIONID=xxx; auth_token=yyy"

# 创建下载器
downloader = RealRadarImageDownloader()
```

---

## 🚀 下一步

### 自动化登录（高级功能）

未来可以实现：
1. 使用Selenium自动登录获取Cookie
2. Cookie过期自动刷新
3. 多账号轮换使用

### API密钥申请

建议：
1. 联系中国气象局申请官方API访问权限
2. 获取正式的API密钥
3. 使用官方认证方式

---

## 📚 相关文件

### 已更新的文件
- [backend/app/core/config.py](../backend/app/core/config.py) - 添加认证配置
- [backend/app/services/download_service_real.py](../backend/app/services/download_service_real.py) - 实现认证逻辑

### 相关文档
- [docs/REAL_API_STATUS.md](REAL_API_STATUS.md) - API集成状态
- [docs/API.md](API.md) - CMA官方API文档

---

## 📝 总结

### ✅ 已完成
1. ✅ 实现Cookie认证支持
2. ✅ 实现Token认证支持
3. ✅ 自动解析和携带认证信息
4. ✅ 完整的日志输出

### 🎯 您需要做的
1. 登录 https://data.cma.cn/
2. 获取Cookie（使用浏览器开发者工具）
3. 配置到 `.env` 文件或 `config.py`
4. 重启后端服务
5. 测试下载功能

### 💡 关键点
- **您的发现非常重要！** Cookie确实是问题所在
- 配置Cookie后，下载应该能成功
- Cookie会定期过期，需要重新获取

---

**最后更新**: 2026-03-11
**状态**: ✅ 认证功能已实现，等待用户配置Cookie测试
**优先级**: 🔥 高 - 配置Cookie后即可解决下载问题
