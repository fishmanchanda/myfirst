#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的API连接测试
"""

import requests
import time
import base64
import json
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

def test_api_connection():
    """测试API连接"""
    try:
        api_key = os.getenv('BACKPACK_API_KEY', '')
        private_key = os.getenv('BACKPACK_PRIVATE_KEY', '')
        
        if not api_key or not private_key:
            print("❌ 请在config.env文件中设置API密钥")
            return
        
        print(f"✅ API Key: {api_key[:20]}...")
        print(f"✅ Private Key: {'已设置' if private_key else '未设置'}")
        
        # 测试简单的GET请求（不需要签名）
        print("\n🔍 测试市场信息获取...")
        response = requests.get('https://api.backpack.exchange/api/v1/markets', timeout=10)
        
        if response.status_code == 200:
            markets = response.json()
            print(f"✅ 市场信息获取成功，共 {len(markets)} 个交易对")
            return True
        else:
            print(f"❌ 市场信息获取失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_signed_request():
    """测试带签名的请求"""
    try:
        api_key = os.getenv('BACKPACK_API_KEY', '')
        private_key = os.getenv('BACKPACK_PRIVATE_KEY', '')
        
        if not api_key or not private_key:
            print("❌ 请在config.env文件中设置API密钥")
            return
        
        print("\n🔍 测试带签名的请求...")
        
        # 生成签名 - 使用Backpack标准格式
        timestamp = int(time.time() * 1000)
        window = 5000
        instruction = 'balanceQuery'
        signing_string = f"instruction={instruction}&timestamp={timestamp}&window={window}"
        
        print(f"🔍 时间戳: {timestamp}")
        print(f"🔍 窗口: {window}")
        print(f"🔍 指令: {instruction}")
        print(f"🔍 签名字符串: {signing_string}")
        
        # 使用ED25519私钥签名
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        
        # 解码私钥
        private_key_bytes = base64.b64decode(private_key)
        ed25519_private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        
        # 生成签名
        signature = ed25519_private_key.sign(signing_string.encode())
        signature_b64 = base64.b64encode(signature).decode()
        
        # 设置请求头
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key,
            'X-Timestamp': str(timestamp),
            'X-Window': str(window),
            'X-Signature': signature_b64,
            'User-Agent': 'SimpleAPITest/1.0'
        }
        
        # 发送请求
        url = 'https://api.backpack.exchange/api/v1/capital'
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 带签名的请求成功")
            if 'balances' in data:
                print(f"✅ 获取到 {len(data['balances'])} 个代币余额")
                for balance in data['balances'][:3]:  # 显示前3个
                    symbol = balance.get('symbol', '')
                    total = balance.get('totalQuantity', 0)
                    if float(total) > 0:
                        print(f"   {symbol}: {total}")
            return True
        else:
            print(f"❌ 带签名的请求失败: {response.status_code} - {response.text}")
            return False
            
    except ImportError:
        print("❌ 缺少cryptography库，请安装: pip install cryptography")
        return False
    except Exception as e:
        print(f"❌ 签名请求失败: {e}")
        return False

def main():
    """主函数"""
    print("🧪 Backpack API连接测试")
    print("=" * 50)
    
    # 测试1: 基本连接
    print("测试1: 基本API连接")
    basic_ok = test_api_connection()
    
    if basic_ok:
        # 测试2: 带签名的请求
        print("\n测试2: 带签名的请求")
        signed_ok = test_signed_request()
        
        if signed_ok:
            print("\n✅ 所有测试通过！API连接正常")
        else:
            print("\n❌ 签名请求失败，请检查API密钥配置")
    else:
        print("\n❌ 基本连接失败，请检查网络连接")

if __name__ == "__main__":
    main()
