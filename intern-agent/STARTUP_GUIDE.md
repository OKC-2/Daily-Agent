# 启动指南

## 前置要求

在启动服务之前，请确保已安装以下软件：

1. **MySQL 数据库**
   - MySQL 5.7+ 或 MariaDB 10.3+
   - 确保数据库服务正在运行

2. **Python 3.8+**
   - 已安装 pip 包管理器

3. **Node.js 16+**
   - 已安装 npm 或 yarn

## 快速启动

### 1. 启动 MySQL 数据库

**macOS (使用 Homebrew):**
```bash
brew services start mysql
# 或
mysql.server start
```

**Linux (Ubuntu/Debian):**
```bash
sudo systemctl start mysql
# 或
sudo service mysql start
```

**Windows:**
```bash
# 通过服务管理器启动 MySQL 服务
net start mysql
```

### 2. 创建数据库

连接到 MySQL 并创建数据库：

```bash
mysql -u root -p
```

```sql
CREATE DATABASE intern_agent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### 3. 启动后端服务

```bash
cd backend

# 验证配置
python3 verify_config.py

# 启动服务
python3 main.py
```

后端服务将在 http://localhost:8000 启动

### 4. 启动前端服务

打开新的终端窗口：

```bash
cd frontend

# 安装依赖（如果还没安装）
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 http://localhost:3000 启动

## 访问应用

- **前端应用**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## API 认证

所有 API 请求需要在 Header 中携带 API Key：

```
Authorization: Bearer UC_ylPdFJMGwIKi5IVCzQ-CF_LQ9bUGFhmUwqZ5WEhY
```

## 测试 API

### 使用 curl 测试

```bash
# 健康检查
curl http://localhost:8000/health

# 获取学习记录（需要认证）
curl -H "Authorization: Bearer UC_ylPdFJMGwIKi5IVCzQ-CF_LQ9bUGFhmUwqZ5WEhY" \
     http://localhost:8000/logs

# 创建学习记录
curl -X POST \
     -H "Authorization: Bearer UC_ylPdFJMGwIKi5IVCzQ-CF_LQ9bUGFhmUwqZ5WEhY" \
     -H "Content-Type: application/json" \
     -d '{
       "date": "2026-05-14",
       "tasks": [
         {
           "id": "1",
           "title": "学习 FastAPI",
           "description": "完成 FastAPI 基础教程",
           "status": "completed"
         }
       ],
       "learnings": [
         {
           "id": "1",
           "content": "掌握了 FastAPI 的基本用法",
           "category": "tech",
           "keywords": ["FastAPI", "Python", "API"],
           "source": "官方文档"
         }
       ],
       "tags": ["Python", "FastAPI"]
     }' \
     http://localhost:8000/logs
```

### 使用浏览器测试

访问 http://localhost:8000/docs，在页面右上角点击 "Authorize" 按钮，输入 API Key 进行认证。

## 环境变量说明

### 后端环境变量 (backend/.env)

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DATABASE_URL | 数据库连接字符串 | - |
| API_KEY | API 认证密钥 | - |
| GLM_API_KEY | GLM API 密钥 | - |
| GLM_MODEL | GLM 模型名称 | glm-4 |
| GLM_TIMEOUT | API 超时时间（秒） | 30 |
| DB_POOL_SIZE | 数据库连接池大小 | 5 |
| ALLOWED_ORIGINS | CORS 允许的源 | http://localhost:3000 |
| HOST | 服务器地址 | 0.0.0.0 |
| PORT | 服务器端口 | 8000 |

### 前端环境变量 (frontend/.env.local)

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| NEXT_PUBLIC_API_BASE | 后端 API 地址 | http://localhost:8000 |
| NEXT_PUBLIC_API_KEY | API 认证密钥 | - |

## 常见问题

### 1. 数据库连接失败

**错误信息**: `Can't connect to MySQL server on 'localhost'`

**解决方案**:
- 确保 MySQL 服务正在运行
- 检查数据库连接字符串中的用户名和密码
- 确认数据库 `intern_agent` 已创建

### 2. 端口被占用

**错误信息**: `Address already in use`

**解决方案**:
```bash
# 查找占用端口的进程
lsof -i :8000  # 后端
lsof -i :3000  # 前端

# 终止进程
kill -9 <PID>
```

### 3. 认证失败

**错误信息**: `401 Unauthorized`

**解决方案**:
- 检查 API Key 是否正确
- 确保请求 Header 中包含 `Authorization: Bearer YOUR_API_KEY`
- 确认 `.env` 文件中的 `API_KEY` 已设置

### 4. AI 功能不可用

**错误信息**: `GLM_API_KEY 未配置`

**解决方案**:
- 检查 `.env` 文件中的 `GLM_API_KEY` 是否设置
- 确认 GLM API Key 有效且有余额
- 查看 GLM API 文档: https://open.bigmodel.cn/

## 生产环境部署

### 后端部署

1. 使用 Gunicorn + Uvicorn:
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

2. 使用 Docker:
```bash
docker build -t intern-agent-backend .
docker run -p 8000:8000 --env-file .env intern-agent-backend
```

### 前端部署

1. 构建生产版本:
```bash
npm run build
npm start
```

2. 使用 Docker:
```bash
docker build -t intern-agent-frontend .
docker run -p 3000:3000 intern-agent-frontend
```

## 安全建议

1. **生产环境必须**:
   - 使用 HTTPS
   - 设置强密码的 API Key
   - 配置防火墙规则
   - 启用数据库 SSL 连接
   - 定期备份数据库

2. **密钥管理**:
   - 不要将 `.env` 文件提交到版本控制
   - 定期轮换 API Key 和数据库密码
   - 使用环境变量或密钥管理服务

3. **监控**:
   - 设置日志监控
   - 配置告警规则
   - 监控 API 调用频率

## 下一步

1. 启动 MySQL 数据库服务
2. 创建 `intern_agent` 数据库
3. 运行 `python3 backend/verify_config.py` 验证配置
4. 启动后端服务 `python3 backend/main.py`
5. 启动前端服务 `cd frontend && npm run dev`
6. 访问 http://localhost:3000 开始使用

## 支持

如有问题，请查看：
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health
- 日志文件: 后端控制台输出
