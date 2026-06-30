#!/bin/bash
# AI 智能测试平台 — 一键启动脚本
# 按顺序启动所有服务

echo "=========================================="
echo "  AI 智能测试平台 — 启动中..."
echo "=========================================="

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 1. 检查 MySQL
echo "[1/5] 检查 MySQL..."
netstat -ano 2>/dev/null | grep -q ":3306.*LISTENING" && echo "  ✓ MySQL 已运行" || echo "  ⚠ MySQL 未运行，请手动启动"

# 2. Redis
echo "[2/5] 启动 Redis..."
if netstat -ano 2>/dev/null | grep -q ":6379.*LISTENING"; then
    echo "  ✓ Redis 已运行"
else
    /c/ZenTao/bin/redis/redis-server.exe --daemonize yes 2>/dev/null &
    sleep 1
    echo "  ✓ Redis 已启动"
fi

# 3. 后端
echo "[3/5] 启动后端 API (port 8000)..."
cd "$PROJECT_DIR/backend"
python -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0 &
BACKEND_PID=$!
sleep 2
echo "  ✓ 后端 PID: $BACKEND_PID"

# 4. Celery Worker
echo "[4/5] 启动 Celery Worker..."
cd "$PROJECT_DIR/backend"
celery -A app.celery_app worker --loglevel=info --concurrency=2 &
CELERY_PID=$!
sleep 1
echo "  ✓ Celery PID: $CELERY_PID"

# 5. 前端
echo "[5/5] 启动前端 (port 5174)..."
cd "$PROJECT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
sleep 2
echo "  ✓ 前端 PID: $FRONTEND_PID"

echo ""
echo "=========================================="
echo "  所有服务已启动！"
echo "  Swagger:  http://localhost:8000/docs"
echo "  前端:     http://localhost:5174"
echo "  登录:     admin / 123456"
echo "=========================================="
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待信号
trap "kill $BACKEND_PID $CELERY_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
