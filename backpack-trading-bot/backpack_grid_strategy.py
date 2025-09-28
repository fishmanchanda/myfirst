#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backpack交易所网格量化策略
专门用于SOL代币的网格交易
"""

import time
import logging
import random
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
import math

class BackpackGridStrategy:
    """Backpack交易所网格交易策略"""
    
    def __init__(self, api_client, config):
        """
        初始化网格策略
        
        Args:
            api_client: Backpack API客户端
            config: 配置对象
        """
        self.api_client = api_client
        self.config = config
        
        # 网格参数
        self.grid_spacing = 0.004  # 网格间距 (0.4%)
        self.initial_quantity = 0.05  # 初始交易数量 (SOL) - 降低到0.05SOL
        self.max_grid_levels = 5  # 最大网格层数
        
        # 价格跟踪
        self.current_price = 0.0
        self.grid_prices = []  # 网格价格列表
        self.grid_orders = {}  # 网格订单字典 {price: order_id}
        
        # 状态跟踪
        self.is_running = False
        self.last_update_time = 0
        
        # 日志
        self.logger = logging.getLogger(__name__)
        
    def calculate_grid_prices(self, base_price: float) -> List[float]:
        """
        计算网格价格
        
        Args:
            base_price: 基础价格
            
        Returns:
            网格价格列表
        """
        grid_prices = []
        
        # 计算买入网格价格（低于当前价格）
        for i in range(1, self.max_grid_levels + 1):
            buy_price = base_price * (1 - self.grid_spacing * i)
            grid_prices.append(buy_price)
            
        # 计算卖出网格价格（高于当前价格）
        for i in range(1, self.max_grid_levels + 1):
            sell_price = base_price * (1 + self.grid_spacing * i)
            grid_prices.append(sell_price)
            
        return sorted(grid_prices)
    
    def get_current_price(self) -> float:
        """获取当前SOL价格"""
        try:
            # 获取SOL/USDC价格
            ticker = self.api_client._make_request('GET', '/api/v1/ticker', 'getTicker', {'symbol': 'SOL_USDC'})
            if ticker and 'lastPrice' in ticker:
                return float(ticker['lastPrice'])
        except Exception as e:
            self.logger.error(f"获取价格失败: {e}")
            
        return 0.0
    
    def place_grid_order(self, side: str, price: float, quantity: float) -> Optional[str]:
        """
        下网格订单
        
        Args:
            side: 买卖方向 ('Bid' 或 'Ask')
            price: 价格
            quantity: 数量
            
        Returns:
            订单ID或None
        """
        try:
            # 确保价格精度
            price = round(price, 2)
            quantity = round(quantity, 4)
            
            # 下订单
            order_params = {
                'symbol': 'SOL_USDC',
                'side': side,
                'orderType': 'Limit',
                'quantity': f"{quantity:.4f}",
                'price': f"{price:.2f}"
            }
            
            result = self.api_client._make_request('POST', '/api/v1/order', 'orderExecute', order_params)
            
            if result and ('orderId' in result or 'id' in result):
                order_id = result.get('orderId') or result.get('id')
                self.logger.info(f"网格订单成功: {side} {quantity} SOL @ {price}")
                return order_id
            else:
                self.logger.error(f"网格订单失败: {side} {quantity} SOL @ {price}")
                return None
                
        except Exception as e:
            self.logger.error(f"下网格订单异常: {e}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """
        取消订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否成功
        """
        try:
            result = self.api_client._make_request('DELETE', f'/api/v1/order/{order_id}', 'cancelOrder')
            if result:
                self.logger.info(f"取消订单成功: {order_id}")
                return True
            else:
                self.logger.error(f"取消订单失败: {order_id}")
                return False
        except Exception as e:
            self.logger.error(f"取消订单异常: {e}")
            return False
    
    def get_open_orders(self) -> List[Dict]:
        """获取未成交订单"""
        try:
            orders = self.api_client._make_request('GET', '/api/v1/orders', 'getOpenOrders', {'symbol': 'SOL_USDC'})
            return orders if orders else []
        except Exception as e:
            self.logger.error(f"获取未成交订单失败: {e}")
            return []
    
    def get_account_balance(self) -> Dict[str, float]:
        """获取账户余额"""
        try:
            balance = self.api_client._make_request('GET', '/api/v1/capital', 'getBalance')
            if balance and 'balances' in balance:
                result = {'SOL': 0, 'USDC': 0}
                for asset in balance['balances']:
                    symbol = asset.get('symbol', '')
                    if symbol == 'SOL':
                        result['SOL'] = float(asset.get('totalQuantity', 0))
                    elif symbol == 'USDC':
                        result['USDC'] = float(asset.get('totalQuantity', 0))
                return result
        except Exception as e:
            self.logger.error(f"获取账户余额失败: {e}")
            
        return {'SOL': 0, 'USDC': 0}
    
    def initialize_grid(self) -> bool:
        """
        初始化网格
        
        Returns:
            是否成功
        """
        try:
            # 获取当前价格
            self.current_price = self.get_current_price()
            if self.current_price <= 0:
                self.logger.error("无法获取当前价格，初始化网格失败")
                return False
            
            # 计算网格价格
            self.grid_prices = self.calculate_grid_prices(self.current_price)
            
            # 获取账户余额
            balance = self.get_account_balance()
            sol_balance = balance['SOL']
            usdc_balance = balance['USDC']
            
            self.logger.info(f"初始化网格 - 当前价格: {self.current_price}, SOL余额: {sol_balance}, USDC余额: {usdc_balance}")
            
            # 清除现有订单
            self.clear_all_orders()
            
            # 下网格订单
            orders_placed = 0
            
            for price in self.grid_prices:
                if price < self.current_price:
                    # 买入订单
                    if usdc_balance >= price * self.initial_quantity:
                        order_id = self.place_grid_order('buy', price, self.initial_quantity)
                        if order_id:
                            self.grid_orders[price] = order_id
                            orders_placed += 1
                            usdc_balance -= price * self.initial_quantity
                else:
                    # 卖出订单
                    if sol_balance >= self.initial_quantity:
                        order_id = self.place_grid_order('sell', price, self.initial_quantity)
                        if order_id:
                            self.grid_orders[price] = order_id
                            orders_placed += 1
                            sol_balance -= self.initial_quantity
                
                # 避免过于频繁的请求
                time.sleep(0.1)
            
            self.logger.info(f"网格初始化完成，共下订单: {orders_placed}")
            return orders_placed > 0
            
        except Exception as e:
            self.logger.error(f"初始化网格失败: {e}")
            return False
    
    def clear_all_orders(self):
        """清除所有未成交订单"""
        try:
            open_orders = self.get_open_orders()
            for order in open_orders:
                if 'id' in order:
                    self.cancel_order(order['id'])
                    time.sleep(0.1)
            
            self.grid_orders.clear()
            self.logger.info("已清除所有未成交订单")
            
        except Exception as e:
            self.logger.error(f"清除订单失败: {e}")
    
    def update_grid(self) -> bool:
        """
        更新网格
        
        Returns:
            是否成功
        """
        try:
            # 获取当前价格
            new_price = self.get_current_price()
            if new_price <= 0:
                return False
            
            # 检查价格变化是否足够大
            price_change = abs(new_price - self.current_price) / self.current_price
            if price_change < self.grid_spacing * 0.5:  # 价格变化小于网格间距的一半
                return True
            
            self.logger.info(f"价格变化: {self.current_price} -> {new_price}, 变化率: {price_change:.4f}")
            
            # 重新初始化网格
            self.current_price = new_price
            return self.initialize_grid()
            
        except Exception as e:
            self.logger.error(f"更新网格失败: {e}")
            return False
    
    def execute_grid_strategy(self) -> Dict:
        """
        执行网格策略
        
        Returns:
            执行结果
        """
        try:
            if not self.is_running:
                # 首次运行，初始化网格
                self.is_running = True
                success = self.initialize_grid()
                if success:
                    return {
                        'success': True,
                        'action': 'grid_initialized',
                        'message': '网格策略初始化成功',
                        'grid_levels': len(self.grid_prices),
                        'orders_placed': len(self.grid_orders)
                    }
                else:
                    return {
                        'success': False,
                        'action': 'grid_init_failed',
                        'message': '网格策略初始化失败'
                    }
            else:
                # 更新网格
                success = self.update_grid()
                if success:
                    return {
                        'success': True,
                        'action': 'grid_updated',
                        'message': '网格策略更新成功',
                        'grid_levels': len(self.grid_prices),
                        'orders_placed': len(self.grid_orders)
                    }
                else:
                    return {
                        'success': False,
                        'action': 'grid_update_failed',
                        'message': '网格策略更新失败'
                    }
                    
        except Exception as e:
            self.logger.error(f"执行网格策略失败: {e}")
            return {
                'success': False,
                'action': 'grid_error',
                'message': f'网格策略执行异常: {e}'
            }
    
    def get_strategy_status(self) -> Dict:
        """
        获取策略状态
        
        Returns:
            策略状态信息
        """
        try:
            balance = self.get_account_balance()
            open_orders = self.get_open_orders()
            
            return {
                'is_running': self.is_running,
                'current_price': self.current_price,
                'grid_levels': len(self.grid_prices),
                'active_orders': len(self.grid_orders),
                'open_orders': len(open_orders),
                'balance': balance,
                'last_update': self.last_update_time
            }
            
        except Exception as e:
            self.logger.error(f"获取策略状态失败: {e}")
            return {
                'is_running': False,
                'error': str(e)
            }
    
    def stop_strategy(self):
        """停止策略"""
        try:
            self.is_running = False
            self.clear_all_orders()
            self.logger.info("网格策略已停止")
        except Exception as e:
            self.logger.error(f"停止策略失败: {e}")
