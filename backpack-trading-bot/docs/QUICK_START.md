# 快速开始指南

## 5分钟快速部署

### 1. 克隆项目
```bash
git clone https://github.com/your-username/backpack-trading-bot.git
cd backpack-trading-bot
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置API密钥
```bash
# 复制配置文件
cp config.env.example config.env

# 编辑配置文件，填入您的API密钥
# Windows: notepad config.env
# Linux/Mac: nano config.env
```

在 `config.env` 中填入：
```env
BACKPACK_API_KEY=您的API密钥
BACKPACK_PRIVATE_KEY=您的私钥
```

### 4. 测试连接
```bash
python simple_api_test.py
```

### 5. 开始交易
```bash
# 单账户智能挖掘
python intelligent_points_farming.py

# 或者运行网格策略
python backpack_grid_strategy.py
```

## 多账户配置（可选）

### 1. JSON配置方式
```bash
cp multi_account_config.json.example multi_account_config.json
# 编辑 multi_account_config.json 添加多个账户
python multi_account_farming.py
```

### 2. Excel配置方式
```bash
# 创建 accounts.xlsx 文件，包含账户信息
python run_excel_accounts.py
```

## 重要提醒

⚠️ **安全提醒**
- 妥善保管API密钥，不要泄露
- 建议先用小额资金测试
- 设置合理的风险控制参数

📚 **更多信息**
- 详细说明：[README.md](README.md)
- 安装指南：[INSTALLATION.md](INSTALLATION.md)
- 安全政策：[SECURITY.md](SECURITY.md)

🚀 **开始交易，祝您收益丰厚！**
