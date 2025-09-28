#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用公共API获取代币信息（无法获取账户余额）
"""

import requests
import json
from typing import Dict, List, Optional

class PublicTokenInfo:
    """公共代币信息查询器"""
    
    def __init__(self):
        self.base_url = 'https://api.backpack.exchange'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PublicTokenInfo/1.0'
        })
    
    def get_all_markets(self) -> List[Dict]:
        """获取所有交易对信息"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/markets", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ 获取市场信息失败: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ 获取市场信息异常: {e}")
            return []
    
    def get_token_price(self, symbol: str) -> Optional[float]:
        """获取代币价格"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/ticker",
                params={'symbol': symbol},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return float(data.get('lastPrice', 0))
            else:
                print(f"❌ 获取价格失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 获取价格异常: {e}")
            return None
    
    def get_token_info(self, symbol: str) -> Optional[Dict]:
        """获取代币详细信息"""
        try:
            # 获取价格信息
            price_response = self.session.get(
                f"{self.base_url}/api/v1/ticker",
                params={'symbol': symbol},
                timeout=10
            )
            
            # 获取深度信息
            depth_response = self.session.get(
                f"{self.base_url}/api/v1/depth",
                params={'symbol': symbol},
                timeout=10
            )
            
            if price_response.status_code == 200 and depth_response.status_code == 200:
                price_data = price_response.json()
                depth_data = depth_response.json()
                
                return {
                    'symbol': symbol,
                    'price': float(price_data.get('lastPrice', 0)),
                    'volume': float(price_data.get('volume', 0)),
                    'change': float(price_data.get('priceChangePercent', 0)),
                    'high': float(price_data.get('highPrice', 0)),
                    'low': float(price_data.get('lowPrice', 0)),
                    'bid': float(depth_data.get('bids', [[0]])[0][0]) if depth_data.get('bids') else 0,
                    'ask': float(depth_data.get('asks', [[0]])[0][0]) if depth_data.get('asks') else 0,
                }
            else:
                print(f"❌ 获取代币信息失败")
                return None
                
        except Exception as e:
            print(f"❌ 获取代币信息异常: {e}")
            return None
    
    def get_sol_tokens(self) -> List[Dict]:
        """获取所有SOL相关的代币信息"""
        try:
            markets = self.get_all_markets()
            sol_tokens = []
            
            for market in markets:
                symbol = market.get('symbol', '')
                if 'SOL' in symbol and symbol.endswith('_USDC'):
                    token_info = self.get_token_info(symbol)
                    if token_info:
                        sol_tokens.append(token_info)
            
            return sol_tokens
            
        except Exception as e:
            print(f"❌ 获取SOL代币信息异常: {e}")
            return []
    
    def display_token_info(self, tokens: List[Dict]):
        """显示代币信息"""
        if not tokens:
            print("❌ 没有找到代币信息")
            return
        
        print(f"\n📊 找到 {len(tokens)} 个SOL相关代币:")
        print("=" * 80)
        print(f"{'代币':<15} {'价格':<12} {'24h涨跌':<10} {'24h最高':<12} {'24h最低':<12} {'成交量':<15}")
        print("-" * 80)
        
        for token in tokens:
            symbol = token['symbol']
            price = token['price']
            change = token['change']
            high = token['high']
            low = token['low']
            volume = token['volume']
            
            change_str = f"{change:+.2f}%"
            if change > 0:
                change_str = f"📈 {change_str}"
            elif change < 0:
                change_str = f"📉 {change_str}"
            
            print(f"{symbol:<15} {price:<12.4f} {change_str:<10} {high:<12.4f} {low:<12.4f} {volume:<15.2f}")

def main():
    """主函数"""
    print("🔍 Backpack公共代币信息查询器")
    print("=" * 50)
    print("⚠️  注意：此工具只能获取公共市场信息，无法获取账户余额")
    print("⚠️  如需获取账户余额和进行交易，需要解决API签名问题")
    print()
    
    info = PublicTokenInfo()
    
    while True:
        print("\n📋 请选择操作:")
        print("1. 查看所有SOL相关代币")
        print("2. 查询特定代币价格")
        print("3. 查看所有交易对")
        print("4. 退出")
        
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == '1':
            print("\n🔍 正在获取SOL相关代币信息...")
            sol_tokens = info.get_sol_tokens()
            info.display_token_info(sol_tokens)
            
        elif choice == '2':
            symbol = input("请输入代币符号 (如: SOL_USDC): ").strip().upper()
            if symbol:
                print(f"\n🔍 正在查询 {symbol} 信息...")
                token_info = info.get_token_info(symbol)
                if token_info:
                    print(f"\n📊 {symbol} 详细信息:")
                    print(f"价格: {token_info['price']:.4f}")
                    print(f"24h涨跌: {token_info['change']:+.2f}%")
                    print(f"24h最高: {token_info['high']:.4f}")
                    print(f"24h最低: {token_info['low']:.4f}")
                    print(f"24h成交量: {token_info['volume']:.2f}")
                    print(f"买一价: {token_info['bid']:.4f}")
                    print(f"卖一价: {token_info['ask']:.4f}")
                else:
                    print(f"❌ 无法获取 {symbol} 信息")
            
        elif choice == '3':
            print("\n🔍 正在获取所有交易对...")
            markets = info.get_all_markets()
            if markets:
                print(f"\n📊 共找到 {len(markets)} 个交易对:")
                for i, market in enumerate(markets[:20]):  # 只显示前20个
                    symbol = market.get('symbol', '')
                    print(f"{i+1:2d}. {symbol}")
                if len(markets) > 20:
                    print(f"... 还有 {len(markets) - 20} 个交易对")
            
        elif choice == '4':
            print("👋 再见！")
            break
            
        else:
            print("❌ 无效选择，请重新输入")

if __name__ == "__main__":
    main()
