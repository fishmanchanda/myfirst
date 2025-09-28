#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试代币管理工具
"""

from backpack_token_manager import BackpackTokenManager, TokenManagerConfig

def test_token_manager():
    """测试代币管理工具"""
    try:
        print("🧪 测试代币管理工具...")
        
        # 创建配置
        config = TokenManagerConfig()
        
        if not config.api_key or not config.private_key:
            print("❌ 请在config.env文件中设置BACKPACK_API_KEY和BACKPACK_PRIVATE_KEY")
            return
        
        print(f"✅ API Key: {config.api_key[:20]}...")
        print(f"✅ Private Key: {'已设置' if config.private_key else '未设置'}")
        
        # 创建代币管理器
        manager = BackpackTokenManager(config)
        
        # 测试查询余额
        print("\n🔍 测试查询账户余额...")
        balances = manager.get_all_token_balances()
        
        if balances:
            print(f"✅ 查询成功，共 {len(balances)} 种代币")
            for balance in balances[:5]:  # 只显示前5个
                if balance.total_quantity > 0:
                    print(f"   {balance.symbol}: {balance.total_quantity:.6f} - ${balance.usd_value:.2f}")
        else:
            print("❌ 查询失败")
        
        print("\n✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_token_manager()
