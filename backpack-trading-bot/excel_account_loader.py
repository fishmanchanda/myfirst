#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel账户加载器
从xlsx文件中读取账户信息和API密钥，自动生成多账户配置
"""

import pandas as pd
import json
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from multi_account_farming import AccountConfig, ProxyConfig, MultiAccountConfig

@dataclass
class ExcelAccountData:
    """Excel账户数据结构"""
    account_name: str
    api_key: str
    api_secret: str
    email: str = ""
    enabled: bool = True

class ExcelAccountLoader:
    """Excel账户加载器"""
    
    def __init__(self, excel_file: str = "backpack.xlsx"):
        self.excel_file = excel_file
        self.accounts_data: List[ExcelAccountData] = []
        
    def load_excel_data(self) -> bool:
        """从Excel文件加载账户数据"""
        try:
            if not os.path.exists(self.excel_file):
                print(f"❌ Excel文件不存在: {self.excel_file}")
                return False
            
            # 读取Excel文件
            df = pd.read_excel(self.excel_file)
            print(f"✅ 成功读取Excel文件: {self.excel_file}")
            print(f"   数据行数: {len(df)}")
            print(f"   列名: {df.columns.tolist()}")
            
            # 解析数据
            self.accounts_data = []
            for index, row in df.iterrows():
                try:
                    # 获取账户信息
                    account_name = str(row.get('account', f'account_{index+1}'))
                    api_key = str(row.get('API Key', ''))
                    api_secret = str(row.get('API Secret', ''))
                    
                    # 清理数据
                    if api_secret == 'nan' or api_secret == 'NaN':
                        api_secret = ''
                    
                    # 验证必要字段
                    if not api_key:
                        print(f"⚠️ 第{index+1}行缺少API Key，跳过")
                        continue
                    
                    # 创建账户数据
                    account_data = ExcelAccountData(
                        account_name=account_name,
                        api_key=api_key,
                        api_secret=api_secret,
                        email=account_name if '@' in account_name else '',
                        enabled=True
                    )
                    
                    self.accounts_data.append(account_data)
                    print(f"✅ 加载账户: {account_name}")
                    
                except Exception as e:
                    print(f"❌ 解析第{index+1}行数据失败: {e}")
                    continue
            
            print(f"✅ 成功加载 {len(self.accounts_data)} 个账户")
            return len(self.accounts_data) > 0
            
        except Exception as e:
            print(f"❌ 读取Excel文件失败: {e}")
            return False
    
    def generate_proxy_configs(self, proxy_list: List[str]) -> List[ProxyConfig]:
        """生成代理配置列表"""
        proxy_configs = []
        
        for i, proxy_str in enumerate(proxy_list):
            try:
                # 解析代理字符串: gateway:port:username:password
                parts = proxy_str.split(':')
                if len(parts) >= 4:
                    gateway = parts[0]
                    port = int(parts[1])
                    username = parts[2]
                    password = parts[3]
                    
                    proxy_config = ProxyConfig(
                        enabled=True,
                        gateway=gateway,
                        port=port,
                        username=username,
                        password=password
                    )
                    proxy_configs.append(proxy_config)
                    print(f"✅ 配置代理 {i+1}: {gateway}:{port}")
                else:
                    print(f"⚠️ 代理格式错误: {proxy_str}")
                    
            except Exception as e:
                print(f"❌ 解析代理失败: {proxy_str}, 错误: {e}")
        
        return proxy_configs
    
    def generate_default_proxy_configs(self, account_count: int) -> List[ProxyConfig]:
        """生成默认代理配置列表 - 为每个账户分配不同的代理"""
        proxy_configs = []
        
        # 基础代理信息
        base_gateway = "proxy.example.com"
        base_port = 1080
        base_username = "YOUR_PROXY_USERNAME"
        base_password = "YOUR_PROXY_PASSWORD"
        
        for i in range(account_count):
            # 为每个账户生成不同的代理配置
            # 使用不同的端口或用户名来区分
            proxy_config = ProxyConfig(
                enabled=True,
                gateway=base_gateway,
                port=base_port,
                username=f"{base_username}-{i+1}",  # 为每个账户添加序号
                password=base_password
            )
            proxy_configs.append(proxy_config)
            print(f"✅ 配置代理 {i+1}: {base_gateway}:{base_port} (用户: {proxy_config.username})")
        
        return proxy_configs
    
    def create_multi_account_config(self, 
                                  proxy_list: List[str] = None,
                                  max_concurrent: int = 3,
                                  start_delay: int = 30,
                                  use_proxy: bool = False) -> MultiAccountConfig:
        """创建多账户配置"""
        
        # 生成代理配置
        if use_proxy and proxy_list:
            proxy_configs = self.generate_proxy_configs(proxy_list)
        elif use_proxy:
            # 使用默认代理配置 - 为20个账户生成20个不同的代理
            proxy_configs = self.generate_default_proxy_configs(len(self.accounts_data))
        else:
            # 不使用代理
            proxy_configs = [
                ProxyConfig(
                    enabled=False,
                    gateway="",
                    port=0,
                    username="",
                    password=""
                )
            ]
        
        # 创建账户配置
        account_configs = []
        for i, account_data in enumerate(self.accounts_data):
            # 选择代理（循环使用）
            proxy_config = proxy_configs[i % len(proxy_configs)]
            
            account_config = AccountConfig(
                account_id=f"account_{i+1}",
                name=account_data.account_name,
                api_key=account_data.api_key,
                private_key=account_data.api_secret,  # 使用Excel中的API Secret作为私钥
                proxy=proxy_config,
                enabled=account_data.enabled,
                description=f"从Excel加载的账户: {account_data.account_name}"
            )
            
            account_configs.append(account_config)
            print(f"✅ 创建账户配置: {account_data.account_name} (代理: {proxy_config.gateway}:{proxy_config.port})")
        
        # 创建多账户配置
        multi_config = MultiAccountConfig(
            accounts=account_configs,
            max_concurrent_accounts=max_concurrent,
            account_start_delay=start_delay,
            cycle_interval=3600,
            daily_cycles=24,
            operation_delay=(10, 30),
            max_daily_loss=5.0,
            proxy_rotation_enabled=True,
            proxy_rotation_interval=300
        )
        
        return multi_config
    
    def save_config_to_file(self, config: MultiAccountConfig, filename: str = "auto_generated_config.json"):
        """保存配置到文件"""
        try:
            config_dict = {
                "accounts": [],
                "global_settings": {
                    "max_concurrent_accounts": config.max_concurrent_accounts,
                    "account_start_delay": config.account_start_delay,
                    "cycle_interval": config.cycle_interval,
                    "daily_cycles": config.daily_cycles,
                    "operation_delay": list(config.operation_delay),
                    "max_daily_loss": config.max_daily_loss
                },
                "proxy_rotation": {
                    "enabled": config.proxy_rotation_enabled,
                    "rotation_interval": config.proxy_rotation_interval
                }
            }
            
            # 转换账户配置
            for account in config.accounts:
                account_dict = {
                    "account_id": account.account_id,
                    "name": account.name,
                    "api_key": account.api_key,
                    "private_key": account.private_key,
                    "proxy": {
                        "enabled": account.proxy.enabled,
                        "gateway": account.proxy.gateway,
                        "port": account.proxy.port,
                        "username": account.proxy.username,
                        "password": account.proxy.password
                    },
                    "enabled": account.enabled,
                    "description": account.description
                }
                config_dict["accounts"].append(account_dict)
            
            # 保存到文件
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 配置已保存到: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
            return False
    
    def print_summary(self):
        """打印加载摘要"""
        print("\n📊 Excel账户加载摘要")
        print("=" * 50)
        print(f"Excel文件: {self.excel_file}")
        print(f"加载账户数: {len(self.accounts_data)}")
        
        for i, account in enumerate(self.accounts_data, 1):
            print(f"\n账户 {i}:")
            print(f"  名称: {account.account_name}")
            print(f"  API Key: {account.api_key[:20]}...")
            print(f"  API Secret: {'已设置' if account.api_secret else '未设置'}")
            print(f"  邮箱: {account.email}")
            print(f"  启用: {'是' if account.enabled else '否'}")

def main():
    """主函数 - 测试Excel加载功能"""
    print("📊 Excel账户加载器测试")
    print("=" * 50)
    
    # 创建加载器
    loader = ExcelAccountLoader("backpack.xlsx")
    
    # 加载Excel数据
    if not loader.load_excel_data():
        print("❌ Excel数据加载失败")
        return
    
    # 打印摘要
    loader.print_summary()
    
    # 创建多账户配置
    print("\n🔧 创建多账户配置...")
    config = loader.create_multi_account_config()
    
    # 保存配置
    print("\n💾 保存配置...")
    loader.save_config_to_file(config, "excel_generated_config.json")
    
    print("\n✅ Excel账户加载器测试完成！")

if __name__ == "__main__":
    main()
