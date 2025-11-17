#!/bin/bash

# Let's Talk 项目环境配置脚本

echo "🎁 Let's Talk - 环境配置脚本"
echo "================================"

# 检查Python版本
python_version=$(python3 --version 2>&1)
if [[ $? -eq 0 ]]; then
    echo "✅ Python: $python_version"
else
    echo "❌ 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "⬆️  升级pip..."
python3 -m pip install --upgrade pip

# 安装依赖
echo "📥 安装项目依赖..."
python3 -m pip install -r requirements.txt

# 检查环境配置文件
if [ ! -f ".env" ]; then
    echo "📄 复制环境配置文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件配置你的API密钥"
else
    echo "✅ 环境配置文件已存在"
fi

echo ""
echo "🎉 环境配置完成！"
echo ""
echo "下一步操作："
echo "1. 编辑 .env 文件，配置你的LLM API密钥"
echo "2. 激活虚拟环境: source venv/bin/activate"
echo "3. 启动应用: python main.py"
echo ""
echo "访问地址: http://localhost:5002"