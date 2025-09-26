#!/bin/bash

# 合同差异对比系统启动脚本

echo "🚀 启动合同差异对比系统..."

# 检查 Python 和 Node.js 是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安装，请先安装 Python 3.11+"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装 Node.js 18+"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p backend/uploads/documents/standard
mkdir -p backend/uploads/documents/target
mkdir -p backend/uploads/images
mkdir -p backend/uploads/temp

# 启动后端
echo "🔧 启动后端服务..."
cd backend
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

echo "🌐 后端服务启动在 http://localhost:8000"
python run.py &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端
echo "🎨 启动前端服务..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

echo "🌐 前端服务启动在 http://localhost:3000"
npm run dev &
FRONTEND_PID=$!

echo "✅ 系统启动完成！"
echo "📖 访问 http://localhost:3000 使用系统"
echo "📚 API 文档: http://localhost:8000/docs"

# 等待用户中断
trap "echo '🛑 正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
