#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Let's Talk 系统监控脚本
用于监控应用状态、性能指标等
"""

import requests
import time
import json
import sys
import os
from datetime import datetime, timedelta

class LetsTalkMonitor:
    def __init__(self, base_url="http://localhost:5002"):
        self.base_url = base_url.rstrip('/')
        self.health_url = f"{self.base_url}/health"
        self.status_url = f"{self.base_url}/erra-api/status"
        
    def check_health(self):
        """检查服务健康状态"""
        try:
            response = requests.get(self.health_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'status': data.get('status'),
                    'services': data.get('services', {}),
                    'timestamp': data.get('timestamp'),
                    'response_time': response.elapsed.total_seconds()
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'response_time': response.elapsed.total_seconds()
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'response_time': None
            }
    
    def check_api_status(self):
        """检查API状态"""
        try:
            response = requests.get(self.status_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'data': data,
                    'response_time': response.elapsed.total_seconds()
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'response_time': response.elapsed.total_seconds()
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'response_time': None
            }
    
    def test_ask_api(self):
        """测试问答API"""
        test_question = "什么是人工智能？"
        try:
            response = requests.post(
                f"{self.base_url}/erra-api/ask",
                json={"question": test_question, "subject_count": 2},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'subjects_count': len(data.get('subjects', [])),
                    'demo_mode': data.get('demo_mode', False),
                    'response_time': response.elapsed.total_seconds()
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'response_time': response.elapsed.total_seconds()
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'response_time': None
            }
    
    def run_full_check(self):
        """运行完整检查"""
        print(f"🔍 Let's Talk 系统监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 健康检查
        print("🏥 健康检查...")
        health = self.check_health()
        if health['success']:
            status_icon = "✅" if health['status'] == 'healthy' else "⚠️"
            print(f"{status_icon} 服务状态: {health['status']}")
            print(f"⏱️  响应时间: {health['response_time']:.3f}s")
            
            services = health.get('services', {})
            for service, status in services.items():
                service_icon = "✅" if status == 'ok' else ("⚠️" if 'demo' in status else "❌")
                print(f"   {service_icon} {service}: {status}")
        else:
            print(f"❌ 健康检查失败: {health['error']}")
            return False
        
        print()
        
        # API状态检查
        print("📊 API状态检查...")
        api_status = self.check_api_status()
        if api_status['success']:
            data = api_status['data']
            print(f"✅ API响应正常")
            print(f"⏱️  响应时间: {api_status['response_time']:.3f}s")
            print(f"🤖 运行模式: {data.get('current_mode', 'unknown')}")
            print(f"📚 学科数量: {data.get('subject_count', 0)}")
            print(f"🔒 LLM专用: {'是' if data.get('llm_only') else '否'}")
        else:
            print(f"❌ API状态检查失败: {api_status['error']}")
        
        print()
        
        # 问答API测试
        print("💬 问答API测试...")
        ask_test = self.test_ask_api()
        if ask_test['success']:
            print(f"✅ 问答API正常")
            print(f"⏱️  响应时间: {ask_test['response_time']:.3f}s")
            print(f"📖 返回学科: {ask_test['subjects_count']}个")
            print(f"🎭 演示模式: {'是' if ask_test['demo_mode'] else '否'}")
        else:
            print(f"❌ 问答API测试失败: {ask_test['error']}")
        
        print("\n" + "=" * 60)
        return health['success'] and api_status['success']
    
    def run_continuous_monitor(self, interval=60):
        """持续监控模式"""
        print(f"🔄 开始持续监控 (间隔: {interval}秒)")
        print("按 Ctrl+C 停止监控\n")
        
        try:
            while True:
                success = self.run_full_check()
                if not success:
                    print("⚠️  检测到问题，建议查看应用日志")
                
                print(f"😴 等待 {interval} 秒...")
                time.sleep(interval)
                print("\n" + "🔄" * 20 + "\n")
                
        except KeyboardInterrupt:
            print("\n👋 监控已停止")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Let\'s Talk 系统监控')
    parser.add_argument('--url', default='http://localhost:5002', help='应用地址')
    parser.add_argument('--continuous', '-c', action='store_true', help='持续监控模式')
    parser.add_argument('--interval', '-i', type=int, default=60, help='监控间隔(秒)')
    
    args = parser.parse_args()
    
    monitor = LetsTalkMonitor(args.url)
    
    if args.continuous:
        monitor.run_continuous_monitor(args.interval)
    else:
        success = monitor.run_full_check()
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()