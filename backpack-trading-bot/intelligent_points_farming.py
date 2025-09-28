#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backpack智能刷分系统 - 网格量化策略版
专门用于SOL代币的网格交易，最大化积分获取

主要功能：
1. 网格量化交易策略
2. 借贷操作模拟
3. 账户活跃度提升
4. 智能调度系统
5. 风险控制机制
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import requests
from dataclasses import dataclass
from dotenv import load_dotenv
import os
from backpack_grid_strategy import BackpackGridStrategy

# 加载环境变量
load_dotenv()

@dataclass
class PointsFarmingConfig:
    """积分刷取配置 - 网格量化策略版"""
    # 基础配置
    api_key: str = os.getenv('BACKPACK_API_KEY', '')
    private_key: str = os.getenv('BACKPACK_PRIVATE_KEY', '')
    base_url: str = 'https://api.backpack.exchange'
    
    # 交易配置 - 只交易SOL
    trading_pairs: List[str] = None
    min_trade_amount: float = 10.0  # 最小交易金额
    max_trade_amount: float = 50.0  # 最大交易金额
    
    # 风险控制
    max_daily_loss: float = 10.0  # 每日最大亏损限制(U)
    stop_loss_pct: float = 0.004  # 止损0.4%
    take_profit_pct: float = 0.01  # 止盈1.0%
    
    # 时间配置 - 24小时优化
    daily_cycles: int = 24  # 每日执行轮数 (每小时一次)
    cycle_duration: int = 3600  # 每轮持续时间 (秒)
    operation_interval: Tuple[int, int] = (10, 30)  # 操作间隔 (秒)
    
    # 操作权重配置
    trading_weight: float = 0.4  # 交易操作权重
    data_query_weight: float = 0.25  # 数据查询权重
    account_activity_weight: float = 0.2  # 账户活动权重
    lending_weight: float = 0.1  # 借贷操作权重
    feature_usage_weight: float = 0.05  # 功能使用权重
    
    def __post_init__(self):
        if self.trading_pairs is None:
            self.trading_pairs = ["SOL_USDC"]  # 只交易SOL

class IntelligentPointsFarmer:
    """智能积分刷取系统 - 网格量化策略版"""
    
    def __init__(self, config: PointsFarmingConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-API-Key': config.api_key
        })
        self.proxy_url = None  # 代理URL
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('points_farming.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 统计信息
        self.stats = {
            'total_operations': 0,
            'trading_operations': 0,
            'lending_operations': 0,
            'data_queries': 0,
            'account_activities': 0,
            'feature_usage': 0,
            'start_time': datetime.now(),
            'last_cycle_time': None
        }
        
        # 盈亏监控
        self.pnl_data_file = "pnl_data.json"
        self.initial_balance = None
        
        # 每日统计
        self.daily_stats = {
            'trades_count': 0,
            'total_volume': 0.0,
            'total_fees': 0.0,
            'total_loss': 0.0,
            'points_earned': 0
        }
        
        # 操作历史
        self.operation_history = []
        
        # 持仓跟踪（用于止盈止损）
        self.positions = {}  # {symbol: {'side': 'long'/'short', 'entry_price': float, 'quantity': float, 'entry_time': datetime}}
        
        # 网格策略实例
        self.grid_strategy = BackpackGridStrategy(self, config)
    
    def set_proxy(self, proxy_url: str):
        """设置代理"""
        self.proxy_url = proxy_url
        if proxy_url:
            self.session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            self.logger.info(f"已设置代理: {proxy_url}")
    
    def _make_request(self, method: str, endpoint: str, operation: str, data: dict = None, max_retries: int = 3) -> Optional[dict]:
        """发送API请求"""
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
    
    def check_daily_loss_limit(self) -> bool:
        """检查每日亏损限制"""
        try:
            if self.initial_balance is None:
                self.initial_balance = self.get_account_balance()
                return True
            
            current_balance = self.get_account_balance()
            if not current_balance:
                return True
            
            # 计算盈亏
            pnl = current_balance - self.initial_balance
            if pnl < -self.config.max_daily_loss:
                self.logger.warning(f"达到每日亏损限制: {pnl:.2f}U")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"检查亏损限制失败: {e}")
            return True
    
    def get_account_balance(self) -> Optional[float]:
        """获取账户余额"""
        try:
            balance = self._make_request('GET', '/api/v1/capital', 'getBalance')
            if balance and 'balances' in balance:
                total_balance = 0.0
                for asset in balance['balances']:
                    if asset.get('symbol') in ['SOL', 'USDC', 'BTC', 'ETH']:
                        total_balance += float(asset.get('totalQuantity', 0))
                return total_balance
            return None
        except Exception as e:
            self.logger.error(f"获取账户余额失败: {e}")
            return None
    
    def _log_operation(self, operation_type: str, details: str):
        """记录操作"""
        operation = {
            'timestamp': datetime.now().isoformat(),
            'type': operation_type,
            'details': details
        }
        self.operation_history.append(operation)
        self.stats['total_operations'] += 1
        
        # 限制历史记录长度
        if len(self.operation_history) > 1000:
            self.operation_history = self.operation_history[-500:]
    
    def execute_diversified_trading(self) -> bool:
        """执行网格量化交易策略 - 专门交易SOL代币"""
        try:
            # 检查每日亏损限制
            if not self.check_daily_loss_limit():
                return False
            
            # 执行网格策略
            result = self.grid_strategy.execute_grid_strategy()
            
            if result['success']:
                self._log_operation('网格交易', f"网格策略执行成功 - {result['message']}")
                self.logger.info(f"🎯 网格策略: {result['action']} - 网格层数: {result.get('grid_levels', 0)}, 订单数: {result.get('orders_placed', 0)}")
                return True
            else:
                # 网格策略失败是正常现象，不记录为错误
                self.logger.info(f"ℹ️ 网格策略: {result['message']}（属正常现象，继续下一周期）")
                return False
            
        except Exception as e:
            self.logger.error(f"网格交易异常: {e}")
            return False
    
    def execute_data_queries(self) -> bool:
        """执行数据查询操作"""
        try:
            operations = [
                ('查询市场信息', self._query_markets),
                ('查询价格数据', self._query_ticker),
                ('查询订单簿', self._query_orderbook),
                ('查询交易记录', self._query_trades)
            ]
            
            operation_name, operation_func = random.choice(operations)
            success = operation_func()
            
            if success:
                self._log_operation('数据查询', operation_name)
                self.stats['data_queries'] += 1
            
            return success
            
        except Exception as e:
            self.logger.error(f"数据查询异常: {e}")
            return False
    
    def _query_markets(self) -> bool:
        """查询市场信息"""
        try:
            markets = self._make_request('GET', '/api/v1/markets', 'queryMarkets')
            return markets is not None
        except Exception as e:
            self.logger.error(f"查询市场信息失败: {e}")
            return False
    
    def _query_ticker(self) -> bool:
        """查询价格数据"""
        try:
            symbol = random.choice(self.config.trading_pairs)
            ticker = self._make_request('GET', '/api/v1/ticker', 'queryTicker', {'symbol': symbol})
            return ticker is not None
        except Exception as e:
            self.logger.error(f"查询价格数据失败: {e}")
            return False
    
    def _query_orderbook(self) -> bool:
        """查询订单簿"""
        try:
            symbol = random.choice(self.config.trading_pairs)
            orderbook = self._make_request('GET', '/api/v1/depth', 'queryOrderbook', {'symbol': symbol})
            return orderbook is not None
        except Exception as e:
            self.logger.error(f"查询订单簿失败: {e}")
            return False
    
    def _query_trades(self) -> bool:
        """查询交易记录"""
        try:
            symbol = random.choice(self.config.trading_pairs)
            trades = self._make_request('GET', '/api/v1/trades', 'queryTrades', {'symbol': symbol})
            return trades is not None
        except Exception as e:
            self.logger.error(f"查询交易记录失败: {e}")
            return False
    
    def execute_lending_operations(self) -> bool:
        """执行借贷操作"""
        try:
            operations = [
                ('查询抵押品信息', self._query_collateral),
                ('查询借贷池信息', self._query_lending_pool)
            ]
            
            operation_name, operation_func = random.choice(operations)
            success = operation_func()
            
            if success:
                self._log_operation('借贷操作', operation_name)
                self.stats['lending_operations'] += 1
            
            return success
            
        except Exception as e:
            self.logger.error(f"借贷操作异常: {e}")
            return False
    
    def _query_collateral(self) -> bool:
        """查询抵押品信息"""
        try:
            collateral = self._make_request('GET', '/api/v1/capital', 'queryCollateral')
            return collateral is not None
        except Exception as e:
            self.logger.error(f"查询抵押品信息失败: {e}")
            return False
    
    def _query_lending_pool(self) -> bool:
        """查询借贷池信息"""
        try:
            # 模拟借贷池查询
            balance = self._make_request('GET', '/api/v1/capital', 'queryLendingPool')
            return balance is not None
        except Exception as e:
            self.logger.error(f"查询借贷池信息失败: {e}")
            return False
    
    def execute_account_activities(self) -> bool:
        """执行账户活动"""
        try:
            operations = [
                ('查询账户信息', self._query_account_info),
                ('查询余额信息', self._query_balance),
                ('查询系统状态', self._query_system_status)
            ]
            
            operation_name, operation_func = random.choice(operations)
            success = operation_func()
            
            if success:
                self._log_operation('账户活动', operation_name)
                self.stats['account_activities'] += 1
            
            return success
            
        except Exception as e:
            self.logger.error(f"账户活动异常: {e}")
            return False
    
    def _query_account_info(self) -> bool:
        """查询账户信息"""
        try:
            account = self._make_request('GET', '/api/v1/capital', 'queryAccountInfo')
            return account is not None
        except Exception as e:
            self.logger.error(f"查询账户信息失败: {e}")
            return False
    
    def _query_balance(self) -> bool:
        """查询余额信息"""
        try:
            balance = self._make_request('GET', '/api/v1/capital', 'queryBalance')
            return balance is not None
        except Exception as e:
            self.logger.error(f"查询余额信息失败: {e}")
            return False
    
    def _query_system_status(self) -> bool:
        """查询系统状态"""
        try:
            status = self._make_request('GET', '/api/v1/system/status', 'querySystemStatus')
            return status is not None
        except Exception as e:
            self.logger.error(f"查询系统状态失败: {e}")
            return False
    
    def execute_feature_usage(self) -> bool:
        """执行功能使用"""
        try:
            operations = [
                ('查询系统状态', self._query_system_status),
                ('测试API端点', self._test_api_endpoints)
            ]
            
            operation_name, operation_func = random.choice(operations)
            success = operation_func()
            
            if success:
                self._log_operation('功能使用', operation_name)
                self.stats['feature_usage'] += 1
            
            return success
            
        except Exception as e:
            self.logger.error(f"功能使用异常: {e}")
            return False
    
    def _test_api_endpoints(self) -> bool:
        """测试API端点"""
        try:
            # 测试多个API端点
            endpoints = [
                '/api/v1/markets',
                '/api/v1/ticker',
                '/api/v1/capital'
            ]
            
            for endpoint in endpoints:
                result = self._make_request('GET', endpoint, 'testEndpoint')
                if result is None:
                    return False
            
            return True
        except Exception as e:
            self.logger.error(f"测试API端点失败: {e}")
            return False
    
    def execute_cycle(self) -> bool:
        """执行一个周期"""
        try:
            self.logger.info("🔄 开始执行新周期")
            
            # 随机选择操作类型
            operations = [
                ('网格交易', self.execute_diversified_trading, self.config.trading_weight),
                ('数据查询', self.execute_data_queries, self.config.data_query_weight),
                ('账户活动', self.execute_account_activities, self.config.account_activity_weight),
                ('借贷操作', self.execute_lending_operations, self.config.lending_weight),
                ('功能使用', self.execute_feature_usage, self.config.feature_usage_weight)
            ]
            
            # 根据权重选择操作
            operation_names = [op[0] for op in operations]
            operation_funcs = [op[1] for op in operations]
            weights = [op[2] for op in operations]
            
            operation_name, operation_func = random.choices(
                list(zip(operation_names, operation_funcs)), 
                weights=weights
            )[0]
            
            # 执行选中的操作
            success = operation_func()
            
            if success:
                self.logger.info(f"✅ {operation_name} 执行成功")
            else:
                self.logger.info(f"ℹ️ {operation_name} 执行失败（属正常现象）")
            
            # 记录周期时间
            self.stats['last_cycle_time'] = datetime.now()
            
            return True
            
        except Exception as e:
            self.logger.error(f"执行周期异常: {e}")
            return False
    
    def run_24h_farming(self):
        """运行24小时刷分"""
        try:
            self.logger.info("🚀 启动24小时网格量化刷分系统")
            self.logger.info(f"📊 交易对: {self.config.trading_pairs}")
            self.logger.info(f"⏰ 每日周期数: {self.config.daily_cycles}")
            self.logger.info(f"🎯 网格策略: 专门交易SOL代币")
            
            # 初始化余额
            self.initial_balance = self.get_account_balance()
            if self.initial_balance:
                self.logger.info(f"💰 初始余额: {self.initial_balance:.2f}U")
            
            cycle_count = 0
            start_time = datetime.now()
            
            while cycle_count < self.config.daily_cycles:
                try:
                    # 执行周期
                    self.execute_cycle()
                    cycle_count += 1
                    
                    # 计算剩余时间
                    elapsed = (datetime.now() - start_time).total_seconds()
                    remaining_cycles = self.config.daily_cycles - cycle_count
                    avg_cycle_time = elapsed / cycle_count if cycle_count > 0 else 0
                    estimated_remaining = remaining_cycles * avg_cycle_time
                    
                    self.logger.info(f"📈 进度: {cycle_count}/{self.config.daily_cycles} 周期完成")
                    self.logger.info(f"⏱️ 预计剩余时间: {estimated_remaining/3600:.1f} 小时")
                    
                    # 随机间隔
                    interval = random.randint(*self.config.operation_interval)
                    self.logger.info(f"⏳ 等待 {interval} 秒后执行下一周期")
                    time.sleep(interval)
                    
                except KeyboardInterrupt:
                    self.logger.info("⏹️ 用户中断，停止刷分")
                    break
                except Exception as e:
                    self.logger.error(f"周期执行异常: {e}")
                    time.sleep(10)  # 异常后等待10秒
                    continue
            
            # 停止网格策略
            self.grid_strategy.stop_strategy()
            
            # 输出最终统计
            self._print_final_stats()
            
        except Exception as e:
            self.logger.error(f"24小时刷分异常: {e}")
    
    def execute_other_operations(self) -> int:
        """执行其他操作（数据查询、账户活动等）- 用于并发模式"""
        try:
            operations_count = 0
            
            # 随机选择其他操作类型
            other_operations = [
                ('数据查询', self.execute_data_queries),
                ('账户活动', self.execute_account_activities),
                ('借贷操作', self.execute_lending_operations),
                ('功能使用', self.execute_feature_usage)
            ]
            
            # 随机选择1-2个操作执行
            num_operations = random.randint(1, 2)
            selected_operations = random.sample(other_operations, num_operations)
            
            for operation_name, operation_func in selected_operations:
                try:
                    success = operation_func()
                    if success:
                        operations_count += 1
                        self.logger.info(f"✅ {operation_name} 执行成功")
                    else:
                        self.logger.info(f"ℹ️ {operation_name} 执行失败（属正常现象）")
                except Exception as e:
                    self.logger.error(f"❌ {operation_name} 执行异常: {e}")
            
            return operations_count
            
        except Exception as e:
            self.logger.error(f"执行其他操作异常: {e}")
            return 0
    
    def record_initial_balance(self):
        """记录初始余额"""
        try:
            self.initial_balance = self.get_account_balance()
            if self.initial_balance:
                self.logger.info(f"💰 记录初始余额: {self.initial_balance:.2f}U")
        except Exception as e:
            self.logger.error(f"记录初始余额失败: {e}")
    
    def update_pnl_status(self):
        """更新盈亏状态"""
        try:
            if self.initial_balance:
                current_balance = self.get_account_balance()
                if current_balance:
                    pnl = current_balance - self.initial_balance
                    pnl_pct = (pnl / self.initial_balance) * 100
                    self.logger.info(f"📊 当前盈亏: {pnl:.2f}U ({pnl_pct:.2f}%)")
        except Exception as e:
            self.logger.error(f"更新盈亏状态失败: {e}")
    
    def _print_final_stats(self):
        """输出最终统计信息"""
        try:
            end_time = datetime.now()
            duration = end_time - self.stats['start_time']
            
            self.logger.info("=" * 60)
            self.logger.info("📊 24小时刷分统计报告")
            self.logger.info("=" * 60)
            self.logger.info(f"⏰ 运行时间: {duration}")
            self.logger.info(f"🔄 总操作数: {self.stats['total_operations']}")
            self.logger.info(f"🎯 网格交易: {self.stats['trading_operations']}")
            self.logger.info(f"📊 数据查询: {self.stats['data_queries']}")
            self.logger.info(f"🏦 借贷操作: {self.stats['lending_operations']}")
            self.logger.info(f"👤 账户活动: {self.stats['account_activities']}")
            self.logger.info(f"🔧 功能使用: {self.stats['feature_usage']}")
            
            # 计算盈亏
            if self.initial_balance:
                final_balance = self.get_account_balance()
                if final_balance:
                    pnl = final_balance - self.initial_balance
                    pnl_pct = (pnl / self.initial_balance) * 100
                    self.logger.info(f"💰 初始余额: {self.initial_balance:.2f}U")
                    self.logger.info(f"💰 最终余额: {final_balance:.2f}U")
                    self.logger.info(f"📈 盈亏: {pnl:.2f}U ({pnl_pct:.2f}%)")
            
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"输出统计信息失败: {e}")

def main():
    """主函数"""
    config = PointsFarmingConfig()
    farmer = IntelligentPointsFarmer(config)
    farmer.run_24h_farming()

if __name__ == "__main__":
    main()
