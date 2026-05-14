#!/bin/bash

# 停止服务脚本

echo "======================================"
echo "停止服务"
echo "======================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# 停止后端
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        echo -e "${GREEN}✓${NC} 后端服务已停止 (PID: $BACKEND_PID)"
    else
        echo -e "${RED}✗${NC} 后端服务未运行"
    fi
    rm logs/backend.pid
else
    echo -e "${RED}✗${NC} 未找到后端 PID 文件"
fi

# 停止前端
if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        echo -e "${GREEN}✓${NC} 前端服务已停止 (PID: $FRONTEND_PID)"
    else
        echo -e "${RED}✗${NC} 前端服务未运行"
    fi
    rm logs/frontend.pid
else
    echo -e "${RED}✗${NC} 未找到前端 PID 文件"
fi

echo ""
echo "服务已停止"
