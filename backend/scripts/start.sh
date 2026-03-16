#!/bin/bash

# 气象雷达数据管理与预测平台 - 启动脚本
# 用于启动所有服务（后端、前端、Celery、Redis）

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

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

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 未安装，请先安装 Python 3.9+"
        exit 1
    fi

    # 检查Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装，请先安装 Node.js 16+"
        exit 1
    fi

    # 检查MySQL
    if ! command -v mysql &> /dev/null; then
        log_warn "MySQL 未安装，请确保 MySQL 8.0 已启动并配置"
    fi

    # 检查Redis
    if ! command -v redis-server &> /dev/null; then
        log_warn "Redis 未安装，请先安装 Redis"
    fi

    log_info "依赖检查完成"
}

# 安装后端依赖
install_backend_deps() {
    log_info "安装后端依赖..."

    cd "$BACKEND_DIR"

    if [ ! -d "venv" ]; then
        log_info "创建Python虚拟环境..."
        python3 -m venv venv
    fi

    log_info "激活虚拟环境并安装依赖..."
    source venv/bin/activate
    pip install -r requirements.txt

    log_info "后端依赖安装完成"
}

# 安装前端依赖
install_frontend_deps() {
    log_info "安装前端依赖..."

    cd "$FRONTEND_DIR"

    if [ ! -d "node_modules" ]; then
        log_info "安装npm依赖..."
        npm install
    fi

    log_info "前端依赖安装完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."

    cd "$BACKEND_DIR"
    source venv/bin/activate

    python scripts/init_db.py

    log_info "数据库初始化完成"
}

# 启动Redis
start_redis() {
    log_info "启动Redis..."

    if pgrep -x "redis-server" > /dev/null; then
        log_info "Redis 已在运行"
    else
        redis-server --daemonize yes
        log_info "Redis 启动成功"
    fi
}

# 启动Celery Worker
start_celery_worker() {
    log_info "启动Celery Worker..."

    cd "$BACKEND_DIR"
    source venv/bin/activate

    # 停止已存在的Worker
    pkill -f "celery worker" || true
    sleep 2

    # 启动Worker
    nohup celery -A app.tasks worker \
        --loglevel=info \
        --concurrency=4 \
        -n worker1@%h \
        > logs/celery_worker.log 2>&1 &

    log_info "Celery Worker 启动成功"
}

# 启动Celery Beat
start_celery_beat() {
    log_info "启动Celery Beat..."

    cd "$BACKEND_DIR"
    source venv/bin/activate

    # 停止已存在的Beat
    pkill -f "celery beat" || true
    sleep 2

    # 启动Beat
    nohup celery -A app.tasks beat \
        --loglevel=info \
        > logs/celery_beat.log 2>&1 &

    log_info "Celery Beat 启动成功"
}

# 启动后端API
start_backend() {
    log_info "启动后端API..."

    cd "$BACKEND_DIR"
    source venv/bin/activate

    # 停止已存在的API
    pkill -f "uvicorn" || true
    sleep 2

    # 启动API
    nohup uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        > logs/backend.log 2>&1 &

    log_info "后端API 启动成功 (http://localhost:8000)"
}

# 启动前端
start_frontend() {
    log_info "启动前端开发服务器..."

    cd "$FRONTEND_DIR"

    # 停止已存在的Vite
    pkill -f "vite" || true
    sleep 2

    # 启动Vite
    nohup npm run dev > logs/frontend.log 2>&1 &

    log_info "前端启动成功 (http://localhost:5173)"
}

# 显示状态
show_status() {
    log_info "服务状态："

    echo ""
    echo "后端API (FastAPI):"
    if pgrep -f "uvicorn" > /dev/null; then
        echo -e "  ${GREEN}✓${NC} 运行中 (http://localhost:8000)"
    else
        echo -e "  ${RED}✗${NC} 未运行"
    fi

    echo ""
    echo "前端 (Vite):"
    if pgrep -f "vite" > /dev/null; then
        echo -e "  ${GREEN}✓${NC} 运行中 (http://localhost:5173)"
    else
        echo -e "  ${RED}✗${NC} 未运行"
    fi

    echo ""
    echo "Celery Worker:"
    if pgrep -f "celery worker" > /dev/null; then
        echo -e "  ${GREEN}✓${NC} 运行中"
    else
        echo -e "  ${RED}✗${NC} 未运行"
    fi

    echo ""
    echo "Celery Beat:"
    if pgrep -f "celery beat" > /dev/null; then
        echo -e "  ${GREEN}✓${NC} 运行中"
    else
        echo -e "  ${RED}✗${NC} 未运行"
    fi

    echo ""
    echo "Redis:"
    if pgrep -x "redis-server" > /dev/null; then
        echo -e "  ${GREEN}✓${NC} 运行中"
    else
        echo -e "  ${RED}✗${NC} 未运行"
    fi

    echo ""
    echo "查看日志:"
    echo "  后端: tail -f $BACKEND_DIR/logs/backend.log"
    echo "  前端: tail -f $FRONTEND_DIR/logs/frontend.log"
    echo "  Celery Worker: tail -f $BACKEND_DIR/logs/celery_worker.log"
    echo "  Celery Beat: tail -f $BACKEND_DIR/logs/celery_beat.log"
}

# 主函数
main() {
    echo ""
    echo "======================================"
    echo "气象雷达数据管理与预测平台 - 启动"
    echo "======================================"
    echo ""

    # 创建日志目录
    mkdir -p "$BACKEND_DIR/logs"
    mkdir -p "$FRONTEND_DIR/logs"

    # 解析命令行参数
    case "${1:-all}" in
        all)
            check_dependencies
            install_backend_deps
            install_frontend_deps
            init_database
            start_redis
            start_celery_worker
            start_celery_beat
            start_backend
            start_frontend
            sleep 3
            show_status
            ;;
        backend)
            start_backend
            ;;
        frontend)
            start_frontend
            ;;
        celery)
            start_celery_worker
            start_celery_beat
            ;;
        redis)
            start_redis
            ;;
        status)
            show_status
            ;;
        stop)
            log_info "停止所有服务..."
            pkill -f "uvicorn" || true
            pkill -f "vite" || true
            pkill -f "celery worker" || true
            pkill -f "celery beat" || true
            log_info "所有服务已停止"
            ;;
        *)
            echo "用法: $0 {all|backend|frontend|celery|redis|status|stop}"
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
