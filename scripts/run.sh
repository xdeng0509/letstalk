#!/bin/bash

# Let's Talk 快速启动脚本

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 启动应用
echo "🚀 启动 Let's Talk..."
python3 main.py $@