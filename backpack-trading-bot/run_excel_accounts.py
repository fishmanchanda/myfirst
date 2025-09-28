#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel账户一键运行脚本
最简单的Excel多账户启动方式
"""

import os
import sys
from excel_account_loader import ExcelAccountLoader
from multi_account_farming import MultiAccountPointsFarmer

def main():
    """主函数"""
    print("🎯 Excel多账户智能刷分系统 - 一键启动")
    print("=" * 60)
    
    # 检查Excel文件
    excel_file = "backpack.xlsx"
    if not os.path.exists(excel_file):
        print(f"❌ Excel文件不存在: {excel_file}")
        print("请确保Excel文件在当前目录下")
        return
    
    print(f"📊 发现Excel文件: {excel_file}")
    
    try:
        # 每次运行都重新创建Excel加载器，确保读取最新数据
        print("📥 重新加载Excel账户数据...")
        loader = ExcelAccountLoader(excel_file)
        
        # 加载Excel数据
        if not loader.load_excel_data():
            print("❌ Excel数据加载失败")
            return
        
        print(f"✅ 成功加载 {len(loader.accounts_data)} 个账户")
        
        # 显示账户信息
        print("\n📋 账户列表:")
        for i, account in enumerate(loader.accounts_data, 1):
            print(f"   {i}. {account.account_name}")
            print(f"      API Key: {account.api_key[:20]}...")
            print(f"      API Secret: {'已设置' if account.api_secret else '未设置'}")
        
        # 询问是否使用代理
        print("\n🔧 创建多账户配置...")
        use_proxy = input("是否使用代理？(y/n，默认n): ").lower().strip() == 'y'
        
        if use_proxy:
            print("✅ 将使用代理配置")
            config = loader.create_multi_account_config(use_proxy=True)
        else:
            print("✅ 不使用代理，直接连接")
            config = loader.create_multi_account_config(use_proxy=False)
        
        # 显示配置信息
        print(f"✅ 配置创建完成")
        print(f"   总账户数: {len(config.accounts)}")
        print(f"   启用账户数: {len([acc for acc in config.accounts if acc.enabled])}")
        print(f"   最大并发数: {config.max_concurrent_accounts}")
        
        # 确认启动
        print(f"\n🚀 准备启动多账户刷分服务")
        print(f"   运行模式: 前台运行 - 无限循环")
        print(f"   运行方式: 每天24个周期，自动循环运行")
        print(f"   停止方式: 按 Ctrl+C 停止服务")
        
        input("\n按回车键开始启动...")
        
        # 创建多账户刷分系统
        print("\n🎯 启动多账户刷分系统...")
        multi_farmer = MultiAccountPointsFarmer(config)
        
        # 运行多账户刷分
        multi_farmer.run_multi_account_farming()
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断，服务已停止")
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
