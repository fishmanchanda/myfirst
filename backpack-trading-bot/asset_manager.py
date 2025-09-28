#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资产管理器 - 自动检查和补足交易资产
确保量化策略能够正常执行
"""

import os
import time
import logging
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

@dataclass
class AssetConfig:
    """资产配置"""
    # API配置
    api_key: str = os.getenv('BACKPACK_API_KEY', '')
    private_key: str = os.getenv('BACKPACK_PRIVATE_KEY', '')
    base_url: str = 'https://api.backpack.exchange'
    
    # 目标资产配置
    target_assets: Dict[str, float] = None  # 目标资产数量
    min_asset_amount: float = 0.0001  # 最小资产数量
    max_buy_amount: float = 50.0  # 单次最大买入金额
    
    def __post_init__(self):
        if self.target_assets is None:
            # 根据策略需求设置目标资产（按金额计算）
            self.target_assets = {
                'SOL': 0.5,    # 至少0.5个SOL (约100U)
                'ETH': 50.0,   # 至少50U的ETH
                'BTC': 50.0,   # 至少50U的BTC
                'USDC': 100.0  # 至少100个USDC
            }

class AssetManager:
    """资产管理器"""
    
    def __init__(self, config: AssetConfig):
        self.config = config
        self.session = requests.Session()
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _make_request(self, method: str, endpoint: str, instruction: str, params: Dict = None, max_retries: int = 3) -> Optional[Dict]:
        """发送认证请求（带重试机制）"""
        for attempt in range(max_retries):
            try:
                from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
                import base64
                
                # 解码私钥
                private_key_bytes = base64.b64decode(self.config.private_key)
                private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
                
                # 创建签名
                timestamp = int(time.time() * 1000)
                window = 5000
                
                # 构建签名字符串
                if params:
                    param_str = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
                    signing_string = f"instruction={instruction}&{param_str}&timestamp={timestamp}&window={window}"
                else:
                    signing_string = f"instruction={instruction}&timestamp={timestamp}&window={window}"
                
                # 签名
                signature = private_key.sign(signing_string.encode())
                signature_b64 = base64.b64encode(signature).decode()
                
                # 设置请求头
                headers = {
                    'Content-Type': 'application/json',
                    'X-API-Key': self.config.api_key,
                    'X-Timestamp': str(timestamp),
                    'X-Window': str(window),
                    'X-Signature': signature_b64
                }
                
                # 发送请求
                url = f"{self.config.base_url}{endpoint}"
                
                if method.upper() == 'GET':
                    response = self.session.get(url, headers=headers, params=params, timeout=30)
                else:
                    response = self.session.post(url, headers=headers, json=params, timeout=30)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 400 and "Request has expired" in response.text:
                    # API请求过期，等待后重试
                    if attempt < max_retries - 1:
                        self.logger.warning(f"API请求过期，等待1秒后重试 (尝试 {attempt + 1}/{max_retries})")
                        time.sleep(1)
                        continue
                    else:
                        self.logger.error(f"请求过期重试失败 {endpoint}: {response.status_code} - {response.text}")
                        return None
                else:
                    self.logger.error(f"请求失败 {endpoint}: {response.status_code} - {response.text}")
                    return None
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"请求异常，等待1秒后重试 (尝试 {attempt + 1}/{max_retries}): {e}")
                    time.sleep(1)
                    continue
                else:
                    self.logger.error(f"请求异常: {e}")
                    return None
        
        return None
    
    def get_current_assets(self) -> Dict[str, float]:
        """获取当前资产（包括现货和借贷池）"""
        try:
            # 使用认证请求获取现货余额
            balances = self._make_request('GET', '/api/v1/capital', 'balanceQuery')
            if not balances:
                self.logger.error("获取现货余额失败")
                return {}
            
            current_assets = {}
            
            if isinstance(balances, list):
                for balance in balances:
                    token = balance.get('token', '')
                    total = float(balance.get('total', 0))
                    if total > 0:
                        current_assets[token] = total
            
            # 获取抵押品信息（借贷池资产）
            collateral_info = self._make_request('GET', '/api/v1/capital/collateral', 'collateralQuery')
            if collateral_info and 'collateral' in collateral_info:
                collateral = collateral_info['collateral']
                if isinstance(collateral, list):
                    for asset in collateral:
                        token = asset.get('symbol', '')  # 抵押品API使用'symbol'字段
                        total = float(asset.get('totalQuantity', 0))  # 抵押品API使用'totalQuantity'字段
                        if total > 0:
                            # 累加到现有资产
                            if token in current_assets:
                                current_assets[token] += total
                            else:
                                current_assets[token] = total
            
            # 如果API获取失败，记录警告但不使用假数据
            if not current_assets:
                self.logger.warning("⚠️ 所有API获取资产失败，无法获取真实资产数据")
                return {}
            
            return current_assets
            
        except Exception as e:
            self.logger.error(f"获取资产失败: {e}")
            return {}
    
    def get_asset_price(self, symbol: str) -> float:
        """获取资产价格"""
        try:
            ticker = self.session.get(f"{self.config.base_url}/api/v1/ticker", 
                                    params={'symbol': symbol}).json()
            if ticker and 'lastPrice' in ticker:
                return float(ticker['lastPrice'])
            return 0
        except Exception as e:
            self.logger.error(f"获取价格失败 {symbol}: {e}")
            return 0
    
    def buy_asset(self, symbol: str, amount_usd: float) -> bool:
        """买入资产（支持借贷池资产）"""
        try:
            # 获取当前价格
            price = self.get_asset_price(symbol)
            if price <= 0:
                self.logger.error(f"无法获取 {symbol} 价格")
                return False
            
            # 计算买入数量
            quantity = amount_usd / price
            # 根据资产类型调整小数位数
            if 'BTC' in symbol:
                quantity = round(quantity, 8)  # BTC保留8位小数
            elif 'ETH' in symbol:
                quantity = round(quantity, 6)  # ETH保留6位小数
            else:
                quantity = round(quantity, 4)  # 其他资产保留4位小数
            
            if quantity < self.config.min_asset_amount:
                self.logger.warning(f"买入数量 {quantity} 小于最小数量 {self.config.min_asset_amount}")
                return False
            
            # 尝试两种下单方式
            # 方式1：使用quoteQuantity（需要现货USDC余额）
            order_params = {
                'symbol': symbol,
                'side': 'Bid',
                'orderType': 'Market',
                'quoteQuantity': f"{amount_usd:.2f}"  # 使用quoteQuantity指定USDC金额
            }
            
            self.logger.info(f"📝 订单参数: {order_params}")
            result = self._make_request('POST', '/api/v1/order', 'orderExecute', order_params)
            
            if result and ('orderId' in result or 'id' in result):
                order_id = result.get('orderId') or result.get('id')
                executed_qty = result.get('executedQuantity', '0')
                executed_quote = result.get('executedQuoteQuantity', '0')
                status = result.get('status', 'Unknown')
                self.logger.info(f"✅ 成功买入 {symbol}: {executed_qty} @ {executed_quote}USDC (订单ID: {order_id}, 状态: {status})")
                return True
            elif result and 'INSUFFICIENT_FUNDS' in str(result):
                # 方式2：使用quantity（可以使用借贷池资产）
                self.logger.info(f"🔄 quoteQuantity方式失败，尝试quantity方式...")
                order_params = {
                    'symbol': symbol,
                    'side': 'Bid',
                    'orderType': 'Market',
                    'quantity': f"{quantity:.8f}"  # 使用quantity指定买入数量
                }
                
                self.logger.info(f"📝 订单参数: {order_params}")
                result = self._make_request('POST', '/api/v1/order', 'orderExecute', order_params)
                
                if result and ('orderId' in result or 'id' in result):
                    order_id = result.get('orderId') or result.get('id')
                    executed_qty = result.get('executedQuantity', '0')
                    executed_quote = result.get('executedQuoteQuantity', '0')
                    status = result.get('status', 'Unknown')
                    self.logger.info(f"✅ 成功买入 {symbol}: {executed_qty} @ {executed_quote}USDC (订单ID: {order_id}, 状态: {status})")
                    return True
                else:
                    self.logger.error(f"❌ 买入失败 {symbol}: {result}")
                    return False
            else:
                self.logger.error(f"❌ 买入失败 {symbol}: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"买入资产异常 {symbol}: {e}")
            return False
    
    def check_and_replenish_assets(self) -> bool:
        """检查并补足资产（全自动）"""
        try:
            self.logger.info("🔍 开始检查资产状态...")
            
            # 获取当前资产
            current_assets = self.get_current_assets()
            self.logger.info(f"📊 当前资产: {current_assets}")
            
            # 检查需要补足的资产
            assets_to_buy = []
            
            for asset, target_value in self.config.target_assets.items():
                current_amount = current_assets.get(asset, 0)
                
                # 计算当前资产的价值
                if asset == 'USDC':
                    current_value = current_amount
                else:
                    symbol = f"{asset}_USDC"
                    price = self.get_asset_price(symbol)
                    if price > 0:
                        current_value = current_amount * price
                    else:
                        self.logger.error(f"无法获取 {symbol} 价格")
                        continue
                
                # 检查是否充足
                if current_value < target_value:
                    shortage_value = target_value - current_value
                    assets_to_buy.append((asset, shortage_value))
                    self.logger.warning(f"⚠️ {asset} 不足: 当前价值 {current_value:.2f}U, 需要 {target_value:.2f}U, 缺少 {shortage_value:.2f}U")
                else:
                    self.logger.info(f"✅ {asset} 充足: 当前价值 {current_value:.2f}U >= 需要 {target_value:.2f}U")
            
            if not assets_to_buy:
                self.logger.info("🎉 所有资产都充足，无需补足！")
                return True
            
            # 自动补足资产
            self.logger.info(f"🛒 自动补足 {len(assets_to_buy)} 种资产...")
            
            success_count = 0
            for asset, shortage_value in assets_to_buy:
                if asset == 'USDC':
                    self.logger.info(f"💰 USDC 需要补足 {shortage_value:.2f}U，但无法直接买入USDC")
                    continue
                
                # 使用固定的买入金额，确保满足最小订单要求
                if asset == 'ETH' or asset == 'BTC':
                    buy_amount = 50.0  # ETH和BTC买入50U
                else:
                    buy_amount = 100.0  # 其他资产买入100U
                
                symbol = f"{asset}_USDC"
                self.logger.info(f"🛒 自动买入 {asset}: 金额 {buy_amount:.2f}U")
                
                if self.buy_asset(symbol, buy_amount):
                    success_count += 1
                    self.logger.info(f"✅ {asset} 买入成功")
                    time.sleep(3)  # 等待订单完成
                else:
                    self.logger.error(f"❌ 买入 {asset} 失败")
            
            self.logger.info(f"📊 自动补足完成: 成功 {success_count}/{len(assets_to_buy)}")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"检查补足资产异常: {e}")
            return False
    
    def get_asset_recommendations(self) -> Dict[str, str]:
        """获取资产建议"""
        try:
            current_assets = self.get_current_assets()
            recommendations = {}
            
            for asset, target_value in self.config.target_assets.items():
                current_amount = current_assets.get(asset, 0)
                
                # 计算当前资产的价值
                if asset == 'USDC':
                    current_value = current_amount
                else:
                    symbol = f"{asset}_USDC"
                    price = self.get_asset_price(symbol)
                    if price > 0:
                        current_value = current_amount * price
                    else:
                        recommendations[asset] = f"价格获取失败"
                        continue
                
                if current_value < target_value:
                    shortage_value = target_value - current_value
                    if asset == 'USDC':
                        recommendations[asset] = f"需要补足 {shortage_value:.2f} USDC (建议通过其他方式获得)"
                    else:
                        recommendations[asset] = f"需要买入 {shortage_value:.2f}U 的 {asset} (当前价值 {current_value:.2f}U)"
                else:
                    recommendations[asset] = f"充足 (当前价值 {current_value:.2f}U)"
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"获取建议异常: {e}")
            return {}

def main():
    """主函数"""
    print("🏦 Backpack资产管理器")
    print("=" * 50)
    
    # 检查配置
    if not os.getenv('BACKPACK_API_KEY') or not os.getenv('BACKPACK_PRIVATE_KEY'):
        print("❌ 错误: 请先配置API密钥")
        return
    
    # 创建配置
    config = AssetConfig()
    
    # 创建资产管理器
    manager = AssetManager(config)
    
    # 显示当前状态
    print("\n📊 当前资产状态:")
    recommendations = manager.get_asset_recommendations()
    for asset, recommendation in recommendations.items():
        print(f"  {asset}: {recommendation}")
    
    # 询问是否补足
    print("\n" + "=" * 50)
    choice = input("是否自动补足不足的资产？(y/n): ").strip().lower()
    
    if choice == 'y':
        print("\n🛒 开始自动补足资产...")
        success = manager.check_and_replenish_assets()
        
        if success:
            print("\n✅ 资产补足完成！现在可以运行量化策略了。")
        else:
            print("\n❌ 资产补足失败，请检查网络和余额。")
    else:
        print("\n📋 资产检查完成，请手动补足不足的资产。")

if __name__ == "__main__":
    main()
