#!/bin/bash

# FalkorDB 快速启动脚本（用于测试）

echo "=========================================="
echo "启动 FalkorDB 测试服务"
echo "=========================================="

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 停止并删除已存在的容器
if docker ps -a | grep -q falkordb-test; then
    echo "停止已存在的 falkordb-test 容器..."
    docker stop falkordb-test > /dev/null 2>&1
    docker rm falkordb-test > /dev/null 2>&1
fi

# 启动FalkorDB
echo "启动 FalkorDB 容器..."
docker run -d \
    --name falkordb-test \
    -p 6379:6379 \
    -p 3000:3000 \
    falkordb/falkordb:latest

# 等待服务就绪
echo "等待 FalkorDB 就绪..."
sleep 3

# 验证连接
if docker exec falkordb-test redis-cli ping > /dev/null 2>&1; then
    echo ""
    echo "=========================================="
    echo "✅ FalkorDB 启动成功！"
    echo "=========================================="
    echo "连接信息:"
    echo "  Host: localhost"
    echo "  Port: 6379"
    echo ""
    echo "停止服务:"
    echo "  docker stop falkordb-test"
    echo ""
    echo "删除容器:"
    echo "  docker rm falkordb-test"
    echo "=========================================="
else
    echo "❌ FalkorDB 启动失败"
    exit 1
fi
