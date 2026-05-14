#!/bin/bash

# 快速启动脚本

echo "======================================"
echo "实习学习记录 Agent - 快速启动"
echo "======================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Python
echo "检查 Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} $PYTHON_VERSION"
else
    echo -e "${RED}✗ Python3 未安装${NC}"
    exit 1
fi

# 检查 Node.js
echo "检查 Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓${NC} Node.js $NODE_VERSION"
else
    echo -e "${RED}✗ Node.js 未安装${NC}"
    exit 1
fi

# 检查 MySQL
echo "检查 MySQL..."
if command -v mysql &> /dev/null; then
    echo -e "${GREEN}✓${NC} MySQL 客户端已安装"
else
    echo -e "${YELLOW}⚠${NC} MySQL 客户端未找到，请确保 MySQL 服务正在运行"
fi

echo ""
echo "======================================"
echo "配置验证"
echo "======================================"

# 验证后端配置
echo "验证后端配置..."
cd backend
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} 找到 .env 配置文件"
    python3 verify_config.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ 配置验证失败${NC}"
        echo ""
        echo "请检查以下项目："
        echo "1. MySQL 服务是否正在运行"
        echo "2. 数据库 'intern_agent' 是否已创建"
        echo "3. .env 文件中的配置是否正确"
        exit 1
    fi
else
    echo -e "${RED}✗ 未找到 .env 配置文件${NC}"
    echo "请复制 .env.example 并配置："
    echo "  cp .env.example .env"
    exit 1
fi

cd ..

echo ""
echo "======================================"
echo "启动服务"
echo "======================================"
echo ""

# 询问是否启动服务
read -p "是否启动服务？(y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消启动"
    exit 0
fi

# 启动后端
echo "启动后端服务..."
cd backend
python3 main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✓${NC} 后端服务已启动 (PID: $BACKEND_PID)"
echo "  日志文件: logs/backend.log"
echo "  API 地址: http://localhost:8000"
echo "  API 文档: http://localhost:8000/docs"

cd ..

# 等待后端启动
echo "等待后端服务启动..."
sleep 3

# 检查后端是否启动成功
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓${NC} 后端服务启动成功"
else
    echo -e "${YELLOW}⚠${NC} 后端服务可能未启动成功，请检查日志"
fi

# 启动前端
echo ""
echo "启动前端服务..."
cd frontend

# 检查是否需要安装依赖
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✓${NC} 前端服务已启动 (PID: $FRONTEND_PID)"
echo "  日志文件: logs/frontend.log"
echo "  应用地址: http://localhost:3000"

cd ..

# 保存 PID 到文件
mkdir -p logs
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

echo ""
echo "======================================"
echo "启动完成！"
echo "======================================"
echo ""
echo "访问地址："
echo "  前端应用: http://localhost:3000"
echo "  API 文档: http://localhost:8000/docs"
echo "  健康检查: http://localhost:8000/health"
echo ""
echo "API Key: UC_ylPdFJMGwIKi5IVCzQ-CF_LQ9bUGFhmUwqZ5WEhY"
echo ""
echo "停止服务："
echo "  ./stop.sh"
echo ""
echo "查看日志："
echo "  tail -f logs/backend.log"
echo "  tail -f logs/frontend.log"
echo ""
