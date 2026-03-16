#!/bin/bash

# 气象雷达数据管理与预测平台 - 停止脚本
# 用于停止所有服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 停止服务函数
stop_service() {
    local service_name=$1
    local process_pattern=$2

    if pgrep -f "$process_pattern" > /dev/null; then
        log_info "停止 $service_name..."
        pkill -f "$process_pattern" || true
        sleep 1

        # 强制停止如果还在运行
        if pgrep -f "$process_pattern" > /dev/null; then
            log_warn "强制停止 $service_name..."
            pkill -9 -f "$process_pattern" || true
        fi

        log_info "$service_name 已停止"
    else
        log_warn "$service_name 未运行"
    fi
}

# 主函数
main() {
    echo ""
    echo "======================================"
    echo "气象雷达数据管理与预测平台 - 停止"
    echo "======================================"
    echo ""

    # 停止前端
    stop_service "前端 (Vite)" "vite"

    # 停止后端API
    stop_service "后端API (FastAPI)" "uvicorn"

    # 停止Celery Worker
    stop_service "Celery Worker" "celery worker"

    # 停止Celery Beat
    stop_service "Celery Beat" "celery beat"

    # 停止Redis
    read -p "是否停止Redis? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        stop_service "Redis" "redis-server"
    fi

    echo ""
    log_info "所有服务已停止"
}

# 运行主函数
main
