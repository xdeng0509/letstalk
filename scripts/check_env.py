# -*- coding: utf-8 -*-
"""
简单的环境检查脚本
"""

import os
import sys

def check_environment():
    print("=== Let's Talk 环境检查 ===")
    
    # 检查Python版本
    print("Python版本:", sys.version)
    
    # 检查关键文件
    files_to_check = [
        'app.py',
        'main.py', 
        '.env',
        '.env.example',
        'requirements.txt',
        'config/subjects.json'
    ]
    
    print("\n文件检查:")
    for filename in files_to_check:
        if os.path.exists(filename):
            print("✅", filename)
        else:
            print("❌", filename, "(缺失)")
    
    # 检查环境变量
    print("\n环境变量检查:")
    if os.path.exists('.env'):
        print("✅ .env 文件存在")
    else:
        print("⚠️  .env 文件不存在")
        
    # 检查依赖
    print("\n依赖检查:")
    try:
        import flask
        print("✅ Flask")
    except ImportError:
        print("❌ Flask 未安装")
        
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv")
    except ImportError:
        print("❌ python-dotenv 未安装")
    
    print("\n=== 检查完成 ===")
    print("如需安装依赖: pip install -r requirements.txt")
    print("启动应用: python main.py")

if __name__ == '__main__':
    check_environment()