#!/bin/bash

# 开发环境启动脚本

set -e

echo "🚀 启动淘宝智能搜索助手开发环境..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python版本需要 >= $required_version，当前版本: $python_version"
    exit 1
fi

echo "✅ Python版本检查通过: $python_version"

# 检查虚拟环境
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  建议在虚拟环境中运行"
    read -p "是否继续? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 安装依赖
echo "📦 安装依赖包..."
pip install -r requirements.txt

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "📝 创建环境变量文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件配置必要的环境变量"
fi

# 初始化数据库
echo "🗄️  初始化数据库..."
python3 init_db.py

# 创建必要的目录
echo "📁 创建必要目录..."
mkdir -p logs
mkdir -p uploads

# 启动开发服务器
echo "🌟 启动开发服务器..."
echo "访问地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo "按 Ctrl+C 停止服务器"

python3 run.py