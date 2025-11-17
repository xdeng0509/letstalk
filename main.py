#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Let's Talk - 多学科视角Agent
主程序入口

使用方法：
    python main.py                  # 启动Web服务（默认演示模式）
    python main.py --llm-only      # 强制LLM模式，禁止演示
    python main.py --port 8080     # 指定端口
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Let\'s Talk - 多学科视角Agent')
    parser.add_argument('--port', type=int, default=5002, help='服务端口 (默认: 5002)')
    parser.add_argument('--host', default='0.0.0.0', help='服务地址 (默认: 0.0.0.0)')
    parser.add_argument('--llm-only', action='store_true', help='强制LLM模式，禁止演示模式')
    parser.add_argument('--debug', action='store_true', help='开启调试模式')
    return parser.parse_args()

def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")
    
    # 检查必要的文件
    required_files = [
        'config/subjects.json',
        'agents/subject_library.py',
        'agents/subject_agent.py',
        'utils/llm_client.py',
        'templates/index.html',
        'templates/landing.html'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 缺少必要文件: {', '.join(missing_files)}")
        return False
    
    # 检查LLM配置
    llm_provider = os.getenv('LLM_PROVIDER', 'openai').lower()
    has_llm_config = False
    
    if llm_provider == 'openai' and os.getenv('OPENAI_API_KEY'):
        has_llm_config = True
        print(f"✅ OpenAI 配置检测到")
    elif llm_provider == 'gemini' and os.getenv('GEMINI_API_KEY'):
        has_llm_config = True
        print(f"✅ Gemini 配置检测到")
    elif llm_provider == 'huiyuan' and os.getenv('HUIYUAN_API_KEY') and os.getenv('HUIYUAN_BASE_URL'):
        has_llm_config = True
        print(f"✅ 慧言 配置检测到")
    
    if not has_llm_config:
        print(f"⚠️  未检测到有效的LLM配置 (当前提供方: {llm_provider})")
        print("   可以在演示模式下运行，或配置 .env 文件启用LLM")
    
    print("✅ 环境检查完成")
    return True

def main():
    """主函数"""
    args = parse_args()
    
    # 设置LLM_ONLY环境变量
    if args.llm_only:
        os.environ['LLM_ONLY'] = 'true'
    
    # 检查环境
    if not check_environment():
        sys.exit(1)
    
    # 导入并启动Flask应用
    try:
        from app import app
        
        print("🎁 Let's Talk - 多学科视角Agent")
        print("=" * 50)
        
        # 显示运行模式
        llm_only = os.getenv('LLM_ONLY', 'false').lower() in ('1', 'true', 'yes') or args.llm_only
        if llm_only:
            print("🔒 LLM专用模式：仅使用真实API，禁止演示")
        else:
            print("🎭 混合模式：支持LLM和演示模式切换")
        
        # 显示LLM配置
        llm_provider = os.getenv('LLM_PROVIDER', 'openai')
        print(f"🤖 LLM提供方: {llm_provider}")
        
        print("=" * 50)
        print(f"🌐 访问地址: http://localhost:{args.port}")
        print(f"📱 产品介绍: http://localhost:{args.port}/")
        print(f"💬 对话入口: http://localhost:{args.port}/chat")
        print("\\n按 Ctrl+C 停止服务\\n")
        
        # 启动Flask应用
        app.run(
            debug=args.debug or os.getenv('FLASK_DEBUG', '').lower() in ('1', 'true'),
            host=args.host,
            port=args.port
        )
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保所有依赖已安装: pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()