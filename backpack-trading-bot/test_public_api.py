#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试公共API端点
"""

import requests
import json

def test_public_apis():
    """测试公共API端点"""
    base_url = 'https://api.backpack.exchange'
    
    # 测试公共端点
    public_endpoints = [
        '/api/v1/markets',
        '/api/v1/ticker',
        '/api/v1/depth',
        '/api/v1/trades'
    ]
    
    print("🧪 测试Backpack公共API端点")
    print("=" * 50)
    
    for endpoint in public_endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"\n🔍 测试: {endpoint}")
            
            if endpoint == '/api/v1/ticker':
                # 需要参数
                response = requests.get(url, params={'symbol': 'SOL_USDC'}, timeout=10)
            elif endpoint == '/api/v1/depth':
                # 需要参数
                response = requests.get(url, params={'symbol': 'SOL_USDC'}, timeout=10)
            elif endpoint == '/api/v1/trades':
                # 需要参数
                response = requests.get(url, params={'symbol': 'SOL_USDC'}, timeout=10)
            else:
                response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功: {len(data) if isinstance(data, list) else 'OK'}")
            else:
                print(f"❌ 失败: {response.status_code} - {response.text[:100]}")
                
        except Exception as e:
            print(f"❌ 异常: {e}")

if __name__ == "__main__":
    test_public_apis()
