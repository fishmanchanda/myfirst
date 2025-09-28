#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backpack多账户智能刷分系统 - 支持代理轮换
每个账户使用不同的代理IP，实现多账户同时刷分
"""

import asyncio
import json
import logging
import random
import time
import threading
import multiprocessing
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import requests
from dataclasses import dataclass
from dotenv import load_dotenv
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# 加载环境变量
load_dotenv()

@dataclass
class ProxyConfig:
    """代理配置"""
    enabled: bool = False
    gateway: str = ""
    port: int = 0
    username: str = ""
    password: str = ""
    
    def get_proxy_url(self) -> str:
        """获取代理URL"""
        if not self.enabled:
            return None
        return f"http://{self.username}:{self.password}@{self.gateway}:{self.port}"

@dataclass
class AccountConfig:
    """账户配置"""
    account_id: str
    name: str
    api_key: str
    private_key: str
    proxy: ProxyConfig
    enabled: bool = True
    description: str = ""

@dataclass
class MultiAccountConfig:
    """多账户配置"""
    accounts: List[AccountConfig]
    max_concurrent_accounts: int = 3
    account_start_delay: int = 30
    cycle_interval: int = 3600
    daily_cycles: int = 24
    operation_delay: Tuple[int, int] = (10, 30)
    max_daily_loss: float = 5.0
    proxy_rotation_enabled: bool = True
    proxy_rotation_interval: int = 300

class ProxyRotator:
    """代理轮换器"""
    
    def __init__(self, proxy_configs: List[ProxyConfig]):
        self.proxy_configs = [p for p in proxy_configs if p.enabled]
        self.current_index = 0
        self.last_rotation = time.time()
        self.rotation_interval = 300  # 5分钟轮换一次
        
    def get_next_proxy(self) -> Optional[str]:
        """获取下一个代理"""
        if not self.proxy_configs:
            return None
            
        # 检查是否需要轮换
        if time.time() - self.last_rotation > self.rotation_interval:
            self.current_index = (self.current_index + 1) % len(self.proxy_configs)
            self.last_rotation = time.time()
            
        return self.proxy_configs[self.current_index].get_proxy_url()
    
    def get_current_proxy(self) -> Optional[str]:
        """获取当前代理"""
        if not self.proxy_configs:
            return None
        return self.proxy_configs[self.current_index].get_proxy_url()

class MultiAccountPointsFarmer:
    """多账户积分刷取系统"""
    
    def __init__(self, config: MultiAccountConfig):
        self.config = config
        self.active_accounts = []
        self.account_farmers = {}
        self.proxy_rotator = ProxyRotator([acc.proxy for acc in config.accounts])
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('multi_account_farming.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 统计信息
        self.stats = {
            'total_accounts': len([acc for acc in config.accounts if acc.enabled]),
            'active_accounts': 0,
            'total_operations': 0,
            'start_time': datetime.now(),
            'account_stats': {}
        }
        
    def create_account_farmer(self, account_config: AccountConfig):
        """为单个账户创建刷分器"""
        from intelligent_points_farming import PointsFarmingConfig, IntelligentPointsFarmer
        
        # 创建账户特定的配置
        farming_config = PointsFarmingConfig()
        farming_config.api_key = account_config.api_key
        farming_config.private_key = account_config.private_key
        farming_config.trading_pairs = ["SOL_USDC", "BTC_USDC", "ETH_USDC"]  # 设置完整交易对列表
        farming_config.daily_cycles = self.config.daily_cycles
        farming_config.cycle_interval = self.config.cycle_interval
        farming_config.operation_delay = self.config.operation_delay
        farming_config.max_daily_loss = self.config.max_daily_loss
        
        # 创建刷分器实例
        farmer = IntelligentPointsFarmer(farming_config)
        
        # 设置代理
        if account_config.proxy.enabled:
            farmer.set_proxy(account_config.proxy.get_proxy_url())
            self.logger.info(f"🔗 账户 {account_config.name} 使用代理: {account_config.proxy.gateway}:{account_config.proxy.port}")
        
        # 检查并补足资产（与单账户模式保持一致）
        try:
            from asset_manager import AssetManager, AssetConfig
            
            # 为当前账户创建资产管理器
            asset_config = AssetConfig()
            asset_config.api_key = account_config.api_key
            asset_config.private_key = account_config.private_key
            
            asset_manager = AssetManager(asset_config)
            
            # 设置代理（如果启用）
            if account_config.proxy.enabled:
                proxy_url = account_config.proxy.get_proxy_url()
                asset_manager.session.proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }
                self.logger.info(f"🔗 资产管理器使用代理: {proxy_url}")
            
            # 获取资产建议
            recommendations = asset_manager.get_asset_recommendations()
            self.logger.info(f"📊 账户 {account_config.name} 资产状态:")
            for asset, recommendation in recommendations.items():
                self.logger.info(f"   {asset}: {recommendation}")
            
            # 检查是否需要补足资产
            needs_replenishment = any("需要" in rec for rec in recommendations.values())
            
            if needs_replenishment:
                self.logger.info(f"⚠️ 账户 {account_config.name} 检测到资产不足，自动补足资产...")
                success = asset_manager.check_and_replenish_assets()
                
                if success:
                    self.logger.info(f"✅ 账户 {account_config.name} 资产补足完成！")
                else:
                    self.logger.info(f"ℹ️ 账户 {account_config.name} 资产补足失败，继续运行策略（偶尔交易失败属正常现象）")
            
        except ImportError:
            self.logger.warning(f"⚠️ 账户 {account_config.name} 资产管理器未找到，跳过资产检查")
        except Exception as e:
            self.logger.error(f"⚠️ 账户 {account_config.name} 资产检查异常: {e}")
        
        return farmer
    
    def run_single_account(self, account_config: AccountConfig) -> Dict:
        """运行单个账户的刷分"""
        account_stats = {
            'account_id': account_config.account_id,
            'name': account_config.name,
            'start_time': datetime.now(),
            'operations': 0,
            'errors': 0,
            'status': 'running'
        }
        
        try:
            self.logger.info(f"🚀 启动账户: {account_config.name} ({account_config.account_id})")
            
            # 创建账户刷分器
            farmer = self.create_account_farmer(account_config)
            self.account_farmers[account_config.account_id] = farmer
            
            # 记录初始余额
            farmer.record_initial_balance()
            
            # 运行刷分循环
            for cycle in range(1, self.config.daily_cycles + 1):
                self.logger.info(f"🔄 账户 {account_config.name} 开始第 {cycle}/{self.config.daily_cycles} 个周期")
                
                # 执行操作周期
                cycle_stats = farmer.execute_operation_cycle()
                
                # 更新统计
                account_stats['operations'] += sum(cycle_stats.values())
                
                self.logger.info(f"✅ 账户 {account_config.name} 第 {cycle} 个周期完成:")
                for op_type, count in cycle_stats.items():
                    if count > 0:
                        self.logger.info(f"   {op_type}: {count} 次操作")
                
                # 更新盈亏状态
                farmer.update_pnl_status()
                
                # 如果不是最后一个周期，等待下一个周期
                if cycle < self.config.daily_cycles:
                    wait_time = self.config.cycle_interval
                    self.logger.info(f"⏳ 账户 {account_config.name} 等待 {wait_time//60} 分钟后开始下一个周期...")
                    time.sleep(wait_time)
            
            account_stats['status'] = 'completed'
            self.logger.info(f"✅ 账户 {account_config.name} 刷分完成")
            
        except Exception as e:
            account_stats['status'] = 'error'
            account_stats['errors'] += 1
            self.logger.error(f"❌ 账户 {account_config.name} 运行错误: {e}")
        
        finally:
            account_stats['end_time'] = datetime.now()
            account_stats['duration'] = account_stats['end_time'] - account_stats['start_time']
        
        return account_stats
    
    def run_single_account_concurrent(self, account_config: AccountConfig) -> Dict:
        """运行单个账户的刷分 - 并发网格策略版"""
        account_stats = {
            'account_id': account_config.account_id,
            'name': account_config.name,
            'start_time': datetime.now(),
            'operations': 0,
            'errors': 0,
            'status': 'running'
        }
        
        try:
            self.logger.info(f"🚀 启动账户: {account_config.name} ({account_config.account_id}) - 并发网格策略")
            
            # 创建账户刷分器
            farmer = self.create_account_farmer(account_config)
            self.account_farmers[account_config.account_id] = farmer
            
            # 记录初始余额
            farmer.record_initial_balance()
            
            # 初始化网格策略
            self.logger.info(f"🎯 账户 {account_config.name} 初始化网格策略...")
            grid_result = farmer.grid_strategy.execute_grid_strategy()
            if grid_result['success']:
                self.logger.info(f"✅ 账户 {account_config.name} 网格策略初始化成功")
            else:
                self.logger.warning(f"⚠️ 账户 {account_config.name} 网格策略初始化失败: {grid_result['message']}")
            
            # 运行24小时网格策略循环 - 支持无限循环
            cycle_count = 0
            start_time = datetime.now()
            day_count = 1
            
            # 无限循环运行，每天24个周期
            while True:
                try:
                    self.logger.info(f"🔄 账户 {account_config.name} 第 {day_count} 天 - 开始第 {cycle_count + 1}/{self.config.daily_cycles} 个周期")
                    
                    # 执行网格策略更新
                    grid_result = farmer.grid_strategy.execute_grid_strategy()
                    
                    if grid_result['success']:
                        self.logger.info(f"✅ 账户 {account_config.name} 网格策略更新成功 - {grid_result['action']}")
                        account_stats['operations'] += 1
                    else:
                        self.logger.info(f"ℹ️ 账户 {account_config.name} 网格策略更新失败（属正常现象）")
                    
                    # 执行其他操作（数据查询、账户活动等）
                    other_operations = farmer.execute_other_operations()
                    account_stats['operations'] += other_operations
                    
                    # 更新盈亏状态
                    farmer.update_pnl_status()
                    
                    cycle_count += 1
                    
                    # 检查是否完成一天的周期
                    if cycle_count >= self.config.daily_cycles:
                        # 完成一天的周期，开始新的一天
                        day_count += 1
                        cycle_count = 0
                        self.logger.info(f"🎉 账户 {account_config.name} 完成第 {day_count-1} 天，开始第 {day_count} 天")
                        self.logger.info(f"📊 账户 {account_config.name} 第 {day_count-1} 天统计: 总操作 {account_stats['operations']} 次")
                        
                        # 重置每日统计
                        account_stats['operations'] = 0
                        account_stats['errors'] = 0
                        
                        # 重新初始化网格策略
                        self.logger.info(f"🔄 账户 {account_config.name} 重新初始化网格策略...")
                        grid_result = farmer.grid_strategy.execute_grid_strategy()
                        if grid_result['success']:
                            self.logger.info(f"✅ 账户 {account_config.name} 网格策略重新初始化成功")
                        else:
                            self.logger.warning(f"⚠️ 账户 {account_config.name} 网格策略重新初始化失败")
                    
                    # 等待下一个周期
                    wait_time = self.config.cycle_interval
                    self.logger.info(f"⏳ 账户 {account_config.name} 等待 {wait_time//60} 分钟后开始下一个周期...")
                    time.sleep(wait_time)
                
                except KeyboardInterrupt:
                    self.logger.info(f"⏹️ 账户 {account_config.name} 用户中断，停止刷分")
                    break
                except Exception as e:
                    self.logger.error(f"❌ 账户 {account_config.name} 周期执行异常: {e}")
                    account_stats['errors'] += 1
                    time.sleep(10)  # 异常后等待10秒
                    continue
            
            # 停止网格策略
            farmer.grid_strategy.stop_strategy()
            self.logger.info(f"🛑 账户 {account_config.name} 网格策略已停止")
            
            account_stats['status'] = 'completed'
            self.logger.info(f"✅ 账户 {account_config.name} 刷分完成")
            
        except Exception as e:
            account_stats['status'] = 'error'
            account_stats['errors'] += 1
            self.logger.error(f"❌ 账户 {account_config.name} 运行错误: {e}")
        
        finally:
            account_stats['end_time'] = datetime.now()
            account_stats['duration'] = account_stats['end_time'] - account_stats['start_time']
        
        return account_stats
    
    def run_multi_account_farming(self):
        """运行多账户刷分 - 真正的并发网格策略"""
        self.logger.info("🚀 启动Backpack多账户智能刷分系统 - 并发网格策略版")
        
        # 获取启用的账户
        enabled_accounts = [acc for acc in self.config.accounts if acc.enabled]
        self.logger.info(f"📊 启用账户数量: {len(enabled_accounts)}")
        
        if not enabled_accounts:
            self.logger.error("❌ 没有启用的账户")
            return
        
        # 设置最大并发账户数量 - 支持全并发
        max_accounts = len(enabled_accounts)  # 所有账户同时运行
        self.logger.info(f"🔄 全并发账户数: {max_accounts}")
        self.logger.info(f"🚀 所有账户将同时启动，独立运行24小时")
        
        # 使用线程池运行所有账户 - 真正的全并发执行
        with ThreadPoolExecutor(max_workers=max_accounts) as executor:
            # 提交所有账户任务
            future_to_account = {}
            
            for i, account in enumerate(enabled_accounts):
                # 添加短暂启动延迟，避免API请求冲突
                if i > 0:
                    time.sleep(2)  # 2秒延迟，避免同时启动造成API冲突
                
                future = executor.submit(self.run_single_account_concurrent, account)
                future_to_account[future] = account
                self.logger.info(f"📝 提交账户任务: {account.name} (第{i+1}/{len(enabled_accounts)}个)")
            
            # 等待所有任务完成
            for future in as_completed(future_to_account):
                account = future_to_account[future]
                try:
                    account_stats = future.result()
                    self.stats['account_stats'][account.account_id] = account_stats
                    self.logger.info(f"✅ 账户 {account.name} 任务完成: {account_stats['status']}")
                except Exception as e:
                    self.logger.error(f"❌ 账户 {account.name} 任务异常: {e}")
        
        # 打印总结
        self.print_multi_account_summary()
    
    def print_multi_account_summary(self):
        """打印多账户总结"""
        runtime = datetime.now() - self.stats['start_time']
        
        print("\n" + "="*80)
        print("🎯 Backpack多账户智能刷分系统 - 总结报告")
        print("="*80)
        print(f"⏰ 总运行时间: {runtime}")
        print(f"📊 账户统计:")
        print(f"   总账户数: {self.stats['total_accounts']}")
        print(f"   活跃账户数: {len(self.stats['account_stats'])}")
        
        print(f"\n📋 各账户详情:")
        for account_id, stats in self.stats['account_stats'].items():
            status_emoji = "✅" if stats['status'] == 'completed' else "❌" if stats['status'] == 'error' else "🔄"
            print(f"   {status_emoji} {stats['name']}: {stats['operations']} 次操作, {stats['errors']} 次错误")
            print(f"      运行时间: {stats.get('duration', 'N/A')}")
            print(f"      状态: {stats['status']}")
        
        print("="*80)

def load_multi_account_config(config_file: str = "multi_account_config.json", excel_file: str = None) -> MultiAccountConfig:
    """加载多账户配置"""
    try:
        # 如果指定了Excel文件，优先从Excel加载
        if excel_file and os.path.exists(excel_file):
            print(f"📊 从Excel文件加载配置: {excel_file}")
            from excel_account_loader import ExcelAccountLoader
            
            loader = ExcelAccountLoader(excel_file)
            if loader.load_excel_data():
                # 创建配置
                config = loader.create_multi_account_config()
                print(f"✅ 从Excel成功加载 {len(config.accounts)} 个账户")
                return config
            else:
                print("❌ Excel数据加载失败，尝试使用JSON配置")
        
        # 从JSON文件加载
        if not os.path.exists(config_file):
            print(f"❌ 配置文件不存在: {config_file}")
            return None
            
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 解析账户配置
        accounts = []
        for acc_data in data['accounts']:
            proxy_config = ProxyConfig(
                enabled=acc_data['proxy']['enabled'],
                gateway=acc_data['proxy']['gateway'],
                port=acc_data['proxy']['port'],
                username=acc_data['proxy']['username'],
                password=acc_data['proxy']['password']
            )
            
            account_config = AccountConfig(
                account_id=acc_data['account_id'],
                name=acc_data['name'],
                api_key=acc_data['api_key'],
                private_key=acc_data['private_key'],
                proxy=proxy_config,
                enabled=acc_data['enabled'],
                description=acc_data['description']
            )
            accounts.append(account_config)
        
        # 创建多账户配置
        multi_config = MultiAccountConfig(
            accounts=accounts,
            max_concurrent_accounts=data['global_settings']['max_concurrent_accounts'],
            account_start_delay=data['global_settings']['account_start_delay'],
            cycle_interval=data['global_settings']['cycle_interval'],
            daily_cycles=data['global_settings']['daily_cycles'],
            operation_delay=tuple(data['global_settings']['operation_delay']),
            max_daily_loss=data['global_settings']['max_daily_loss'],
            proxy_rotation_enabled=data['proxy_rotation']['enabled'],
            proxy_rotation_interval=data['proxy_rotation']['rotation_interval']
        )
        
        return multi_config
        
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        return None

def main():
    """主函数"""
    print("🎯 Backpack多账户智能刷分系统")
    print("=" * 60)
    
    # 加载配置
    config = load_multi_account_config()
    if not config:
        print("❌ 配置加载失败")
        return
    
    # 检查启用的账户
    enabled_accounts = [acc for acc in config.accounts if acc.enabled]
    if not enabled_accounts:
        print("❌ 没有启用的账户，请检查配置文件")
        return
    
    print(f"📊 找到 {len(enabled_accounts)} 个启用的账户:")
    for account in enabled_accounts:
        proxy_info = f" (代理: {account.proxy.gateway}:{account.proxy.port})" if account.proxy.enabled else " (无代理)"
        print(f"   ✅ {account.name}{proxy_info}")
    
    # 创建多账户刷分系统
    multi_farmer = MultiAccountPointsFarmer(config)
    
    # 开始多账户刷分
    multi_farmer.run_multi_account_farming()

if __name__ == "__main__":
    main()
