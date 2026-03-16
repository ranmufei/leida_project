#!/bin/bash
# 启动后端API服务

cd /Users/ranmufei/2026/leida_project/backend

# 清理旧进程
pkill -f uvicorn 2>/dev/null

# 等待清理完成
sleep 2

# 启动服务
echo "Starting backend API service..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
