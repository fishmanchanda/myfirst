# Backpack交易所量化交易系统

这是一个专为Backpack交易所设计的量化交易和积分挖掘系统，支持多种策略和多账户并发运行。

## 主要功能

### 🎯 核心功能
- **网格交易策略**: 专门针对SOL等主流代币的网格量化交易
- **智能积分挖掘**: 自动化积分获取和账户活跃度提升
- **多账户管理**: 支持多账户并发运行，提高效率
- **资产管理**: 自动检查和补足交易所需资产
- **代理支持**: 支持代理轮换，保护账户安全

### 📊 交易策略
- **网格交易**: 在设定价格区间内自动买入卖出
- **移动平均线交叉**: 基于技术指标的趋势跟踪
- **RSI均值回归**: 基于超买超卖信号的反向操作
- **做市策略**: 在买卖盘提供流动性

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/your-username/backpack-trading-bot.git
cd backpack-trading-bot

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置设置

#### 单账户配置
```bash
# 复制配置文件模板
cp config.env.example config.env

# 编辑配置文件，填入您的API密钥
# BACKPACK_API_KEY=您的API密钥
# BACKPACK_PRIVATE_KEY=您的私钥
```

#### 多账户配置
```bash
# 复制多账户配置模板
cp multi_account_config.json.example multi_account_config.json

# 编辑配置文件，添加多个账户信息
```

### 3. 获取API密钥

1. 登录Backpack交易所
2. 进入API管理页面
3. 创建新的API密钥对
4. 确保API权限包含交易权限
5. 将密钥信息填入配置文件

**注意**: API密钥需要是Base64编码的ED25519格式

### 4. 运行程序

#### 单账户模式
```bash
# 运行智能积分挖掘
python intelligent_points_farming.py

# 运行网格交易策略
python backpack_grid_strategy.py
```

#### 多账户模式
```bash
# 使用JSON配置运行多账户
python multi_account_farming.py

# 使用Excel配置运行多账户
python run_excel_accounts.py
```

## 文件说明

### 核心模块
- `backpack_grid_strategy.py`: 网格交易策略核心实现
- `intelligent_points_farming.py`: 智能积分挖掘系统
- `multi_account_farming.py`: 多账户管理系统
- `asset_manager.py`: 资产管理器
- `backpack_token_manager.py`: 代币管理工具

### 配置文件
- `config.env.example`: 单账户配置模板
- `config.json`: 策略参数配置
- `multi_account_config.json.example`: 多账户配置模板

### 工具脚本
- `run_excel_accounts.py`: Excel账户一键启动
- `excel_account_loader.py`: Excel账户数据加载器
- `simple_api_test.py`: API连接测试
- `test_public_api.py`: 公开API测试

### 文档
- `TOKEN_MANAGER_GUIDE.md`: 代币管理器使用指南
- `GRID_STRATEGY_DETAILS.md`: 网格策略详细说明
- `CONCURRENT_GRID_STRATEGY.md`: 并发网格策略说明

## 策略配置

### 网格交易参数
```json
{
  "grid_spacing": 0.004,      // 网格间距 (0.4%)
  "initial_quantity": 0.05,   // 初始交易数量
  "max_grid_levels": 5        // 最大网格层数
}
```

### 风险控制参数
```json
{
  "max_daily_loss": 10.0,     // 每日最大亏损限制
  "stop_loss_pct": 0.004,     // 止损百分比
  "take_profit_pct": 0.01     // 止盈百分比
}
```

## 注意事项

### ⚠️ 风险提示
- 本程序仅供学习和研究使用
- 量化交易存在风险，请谨慎使用
- 建议先在测试环境中验证策略
- 合理设置风险控制参数

### 🔒 安全须知
- 妥善保管API密钥，不要泄露给他人
- 定期更换API密钥
- 使用代理保护网络安全
- 定期备份重要数据

### 📝 合规说明
- 请遵守当地法律法规
- 遵守交易所使用条款
- 合理使用API，避免频繁请求
- 尊重交易所的风控措施

## 技术支持

### 常见问题
1. **API连接失败**: 检查API密钥格式和权限
2. **交易失败**: 检查账户余额和交易对状态
3. **网格策略不生效**: 检查价格变动和网格参数设置
4. **多账户冲突**: 使用代理分离网络环境

### 系统要求
- Python 3.8+
- 稳定的网络连接
- 足够的系统资源（多账户模式）

## 免责声明

本软件仅供教育和研究目的使用。使用本软件进行实际交易的任何损失，开发者概不负责。请在充分了解风险的情况下谨慎使用。

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

---

**祝您交易愉快！** 🚀