#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backpack代币管理工具
功能：
1. 查询账户所有代币余额
2. 将除SOL外的其他代币卖出成USDC
"""

import requests
import json
import time
import logging
import base64
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

@dataclass
class TokenBalance:
    """代币余额信息"""
    symbol: str
    total_quantity: float
    available_quantity: float
    locked_quantity: float
    usd_value: float = 0.0

@dataclass
class TokenManagerConfig:
    """代币管理器配置"""
    api_key: str = os.getenv('BACKPACK_API_KEY', '')
    private_key: str = os.getenv('BACKPACK_PRIVATE_KEY', '')
    base_url: str = 'https://api.backpack.exchange'
    min_sell_amount: float = 0.001  # 最小卖出数量
    max_retries: int = 3  # 最大重试次数

class BackpackTokenManager:
    """Backpack代币管理器"""
    
    def __init__(self, config: TokenManagerConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-API-Key': config.api_key
        })
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('token_manager.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 代币价格缓存
        self.price_cache = {}
        
    def _make_request(self, method: str, endpoint: str, operation: str, data: dict = None, max_retries: int = 3) -> Optional[dict]:
        """发送API请求 - 使用与主脚本相同的方式"""
        url = f"{self.config.base_url}{endpoint}"
        
        for attempt in range(max_retries):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, params=data)
                else:
                    response = self.session.post(url, json=data)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 400:
                    error_text = response.text
                    if "Request has expired" in error_text:
                        self.logger.warning(f"请求过期，重试 {attempt + 1}/{max_retries}")
                        time.sleep(1)
                        continue
                    else:
                        self.logger.error(f"请求失败 {endpoint}: {response.status_code} - {error_text}")
                        return None
                else:
                    self.logger.error(f"请求失败 {endpoint}: {response.status_code} - {response.text}")
                    return None
                    
            except Exception as e:
                self.logger.error(f"请求异常 {endpoint}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return None
        
        return None
    
    def get_all_token_balances(self) -> List[TokenBalance]:
        """获取所有代币余额"""
        try:
            self.logger.info("🔍 查询账户所有代币余额...")
            
            # 获取账户余额
            balance_data = self._make_request('GET', '/api/v1/capital', 'getBalance')
            if not balance_data or 'balances' not in balance_data:
                self.logger.error("❌ 获取账户余额失败")
                return []
            
            balances = []
            total_usd_value = 0.0
            
            for asset in balance_data['balances']:
                symbol = asset.get('symbol', '')
                total_quantity = float(asset.get('totalQuantity', 0))
                available_quantity = float(asset.get('availableQuantity', 0))
                locked_quantity = float(asset.get('lockedQuantity', 0))
                
                # 获取代币价格
                usd_value = self._get_token_price(symbol, total_quantity)
                
                balance = TokenBalance(
                    symbol=symbol,
                    total_quantity=total_quantity,
                    available_quantity=available_quantity,
                    locked_quantity=locked_quantity,
                    usd_value=usd_value
                )
                
                balances.append(balance)
                total_usd_value += usd_value
                
                if total_quantity > 0:
                    self.logger.info(f"💰 {symbol}: {total_quantity:.6f} (可用: {available_quantity:.6f}, 锁定: {locked_quantity:.6f}) - ${usd_value:.2f}")
            
            self.logger.info(f"📊 总资产价值: ${total_usd_value:.2f}")
            return balances
            
        except Exception as e:
            self.logger.error(f"获取代币余额失败: {e}")
            return []
    
    def _get_token_price(self, symbol: str, quantity: float) -> float:
        """获取代币价格"""
        try:
            if symbol in self.price_cache:
                return self.price_cache[symbol] * quantity
            
            # 获取代币价格
            ticker_data = self._make_request('GET', '/api/v1/ticker', 'getTicker', {'symbol': f'{symbol}_USDC'})
            if ticker_data and 'lastPrice' in ticker_data:
                price = float(ticker_data['lastPrice'])
                self.price_cache[symbol] = price
                return price * quantity
            
            # 如果直接获取失败，尝试其他交易对
            if symbol != 'USDC':
                # 尝试通过BTC或ETH获取价格
                for base in ['BTC', 'ETH']:
                    if symbol != base:
                        ticker_data = self._make_request('GET', '/api/v1/ticker', 'getTicker', {'symbol': f'{symbol}_{base}'})
                        if ticker_data and 'lastPrice' in ticker_data:
                            symbol_price = float(ticker_data['lastPrice'])
                            # 获取基础代币对USDC的价格
                            base_ticker = self._make_request('GET', '/api/v1/ticker', 'getTicker', {'symbol': f'{base}_USDC'})
                            if base_ticker and 'lastPrice' in base_ticker:
                                base_price = float(base_ticker['lastPrice'])
                                price = symbol_price * base_price
                                self.price_cache[symbol] = price
                                return price * quantity
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"获取代币价格失败 {symbol}: {e}")
            return 0.0
    
    def sell_all_tokens_except_sol(self) -> Dict[str, bool]:
        """卖出除SOL外的所有代币"""
        try:
            self.logger.info("🔄 开始卖出除SOL外的所有代币...")
            
            # 获取所有代币余额
            balances = self.get_all_token_balances()
            if not balances:
                self.logger.error("❌ 无法获取代币余额")
                return {}
            
            # 过滤出需要卖出的代币
            tokens_to_sell = []
            for balance in balances:
                if (balance.symbol != 'SOL' and 
                    balance.symbol != 'USDC' and 
                    balance.available_quantity >= self.config.min_sell_amount):
                    tokens_to_sell.append(balance)
            
            if not tokens_to_sell:
                self.logger.info("✅ 没有需要卖出的代币")
                return {}
            
            self.logger.info(f"📋 需要卖出的代币: {[token.symbol for token in tokens_to_sell]}")
            
            # 执行卖出操作
            sell_results = {}
            for token in tokens_to_sell:
                success = self._sell_token(token)
                sell_results[token.symbol] = success
                
                # 避免过于频繁的请求
                time.sleep(1)
            
            return sell_results
            
        except Exception as e:
            self.logger.error(f"卖出代币失败: {e}")
            return {}
    
    def _sell_token(self, token: TokenBalance) -> bool:
        """卖出单个代币"""
        try:
            symbol = token.symbol
            quantity = token.available_quantity
            
            self.logger.info(f"🔄 卖出 {symbol}: {quantity:.6f}")
            
            # 检查交易对是否存在
            trading_pair = f"{symbol}_USDC"
            markets = self._make_request('GET', '/api/v1/markets', 'getMarkets')
            if not markets:
                self.logger.error(f"❌ 无法获取市场信息")
                return False
            
            # 检查交易对是否支持
            market_exists = False
            for market in markets:
                if market.get('symbol') == trading_pair:
                    market_exists = True
                    break
            
            if not market_exists:
                self.logger.warning(f"⚠️ 交易对 {trading_pair} 不存在，跳过 {symbol}")
                return False
            
            # 获取当前价格
            ticker = self._make_request('GET', '/api/v1/ticker', 'getTicker', {'symbol': trading_pair})
            if not ticker or 'lastPrice' not in ticker:
                self.logger.error(f"❌ 无法获取 {symbol} 价格")
                return False
            
            current_price = float(ticker['lastPrice'])
            
            # 使用市价单卖出
            order_params = {
                'symbol': trading_pair,
                'side': 'Ask',  # 卖出
                'orderType': 'Market',  # 市价单
                'quantity': f"{quantity:.6f}"
            }
            
            result = self._make_request('POST', '/api/v1/order', 'sellOrder', order_params)
            
            if result and ('orderId' in result or 'id' in result):
                order_id = result.get('orderId') or result.get('id')
                self.logger.info(f"✅ {symbol} 卖出成功: {quantity:.6f} @ {current_price:.4f} USDC (订单ID: {order_id})")
                return True
            else:
                self.logger.error(f"❌ {symbol} 卖出失败: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"卖出 {token.symbol} 失败: {e}")
            return False
    
    def get_markets_info(self) -> List[Dict]:
        """获取市场信息"""
        try:
            markets = self._make_request('GET', '/api/v1/markets', 'getMarkets')
            if markets:
                self.logger.info(f"📊 获取到 {len(markets)} 个交易对")
                return markets
            return []
        except Exception as e:
            self.logger.error(f"获取市场信息失败: {e}")
            return []

def show_menu():
    """显示菜单"""
    print("\n" + "="*60)
    print("🎯 Backpack代币管理工具")
    print("="*60)
    print("1. 查询账户所有代币余额")
    print("2. 卖出除SOL外的所有代币")
    print("3. 获取市场信息")
    print("4. 退出")
    print("="*60)

def main():
    """主函数"""
    try:
        # 创建配置
        config = TokenManagerConfig()
        
        if not config.api_key or not config.private_key:
            print("❌ 请在config.env文件中设置BACKPACK_API_KEY和BACKPACK_PRIVATE_KEY")
            return
        
        # 创建代币管理器
        manager = BackpackTokenManager(config)
        
        while True:
            show_menu()
            choice = input("请选择操作 (1-4): ").strip()
            
            if choice == '1':
                print("\n🔍 查询账户所有代币余额...")
                balances = manager.get_all_token_balances()
                if balances:
                    print(f"\n✅ 查询完成，共 {len(balances)} 种代币")
                else:
                    print("\n❌ 查询失败")
            
            elif choice == '2':
                print("\n🔄 卖出除SOL外的所有代币...")
                confirm = input("确认要卖出除SOL外的所有代币吗？(y/n): ").lower().strip()
                if confirm == 'y':
                    results = manager.sell_all_tokens_except_sol()
                    if results:
                        success_count = sum(1 for success in results.values() if success)
                        print(f"\n✅ 卖出完成: {success_count}/{len(results)} 个代币成功")
                        for symbol, success in results.items():
                            status = "✅ 成功" if success else "❌ 失败"
                            print(f"   {symbol}: {status}")
                    else:
                        print("\n❌ 卖出失败")
                else:
                    print("❌ 操作已取消")
            
            elif choice == '3':
                print("\n📊 获取市场信息...")
                markets = manager.get_markets_info()
                if markets:
                    print(f"\n✅ 获取到 {len(markets)} 个交易对")
                    # 显示前10个交易对
                    for i, market in enumerate(markets[:10]):
                        symbol = market.get('symbol', '')
                        status = market.get('status', '')
                        print(f"   {i+1}. {symbol} - {status}")
                    if len(markets) > 10:
                        print(f"   ... 还有 {len(markets) - 10} 个交易对")
                else:
                    print("\n❌ 获取市场信息失败")
            
            elif choice == '4':
                print("\n👋 退出程序")
                break
            
            else:
                print("\n❌ 无效选择，请重新输入")
            
            input("\n按回车键继续...")
    
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，退出程序")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")

if __name__ == "__main__":
    main()
