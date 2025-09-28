# 安装和部署指南

## 系统要求

- Python 3.8 或更高版本
- pip 包管理器
- 稳定的网络连接
- 4GB以上可用内存（多账户模式）

## 安装步骤

### 1. 下载项目
```bash
git clone https://github.com/your-username/backpack-trading-bot.git
cd backpack-trading-bot
```

### 2. 创建虚拟环境（推荐）
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置设置

#### 单账户配置
```bash
# 复制配置模板
cp config.env.example config.env

# 编辑配置文件
# Windows: notepad config.env
# Linux/Mac: nano config.env
```

在 `config.env` 文件中填入：
```env
BACKPACK_API_KEY=您的API密钥
BACKPACK_PRIVATE_KEY=您的私钥
```

#### 多账户配置
```bash
# 复制多账户配置模板
cp multi_account_config.json.example multi_account_config.json

# 编辑配置文件
# Windows: notepad multi_account_config.json
# Linux/Mac: nano multi_account_config.json
```

### 5. 测试连接
```bash
# 测试API连接
python simple_api_test.py

# 测试公开API
python test_public_api.py
```

## 运行程序

### 单账户模式
```bash
# 智能积分挖掘
python intelligent_points_farming.py

# 网格交易策略
python backpack_grid_strategy.py

# 代币管理
python backpack_token_manager.py
```

### 多账户模式
```bash
# JSON配置方式
python multi_account_farming.py

# Excel配置方式（需要创建accounts.xlsx文件）
python run_excel_accounts.py
```

## 常见问题

### 1. 安装依赖失败
```bash
# 更新pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 2. API连接失败
- 检查网络连接
- 确认API密钥格式正确（Base64编码的ED25519）
- 检查API权限设置

### 3. 交易失败
- 检查账户余额
- 确认交易对状态
- 检查最小交易数量限制

### 4. 多账户冲突
- 使用不同的代理
- 调整启动延迟时间
- 检查并发账户数量限制

## 服务器部署

### 使用screen（Linux）
```bash
# 安装screen
sudo apt-get install screen

# 创建新会话
screen -S backpack_bot

# 运行程序
python multi_account_farming.py

# 分离会话：Ctrl+A, 然后按D
# 重新连接：screen -r backpack_bot
```

### 使用systemd服务（Linux）
创建服务文件：
```bash
sudo nano /etc/systemd/system/backpack-bot.service
```

服务文件内容：
```ini
[Unit]
Description=Backpack Trading Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/backpack-trading-bot
ExecStart=/path/to/venv/bin/python multi_account_farming.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl enable backpack-bot
sudo systemctl start backpack-bot
sudo systemctl status backpack-bot
```

### 使用Docker
创建 Dockerfile：
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "multi_account_farming.py"]
```

构建和运行：
```bash
docker build -t backpack-bot .
docker run -d --name backpack-bot -v $(pwd)/config.env:/app/config.env backpack-bot
```

## 监控和维护

### 日志文件
- `multi_account_farming.log`: 多账户运行日志
- `points_farming.log`: 积分挖掘日志
- `token_manager.log`: 代币管理日志

### 监控命令
```bash
# 实时查看日志
tail -f multi_account_farming.log

# 查看进程状态
ps aux | grep python

# 查看系统资源使用
top
htop
```

### 定期维护
- 定期检查日志文件大小
- 更新依赖包版本
- 备份重要配置文件
- 监控账户余额变化

## 安全建议

1. **定期更换API密钥**
2. **使用强密码保护服务器**
3. **定期备份配置和日志**
4. **监控异常交易活动**
5. **遵守交易所使用条款**

如有问题，请查看 [README.md](README.md) 或提交 Issue。
