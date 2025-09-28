# Backpack 24小时量化交易系统

## 概述

这是专门为24小时运行优化的Backpack量化交易系统，具有以下特点：

- **24小时不间断运行**：支持全天候自动化交易
- **智能时间调度**：根据时间段自动调整交易频率和策略权重
- **增强风险控制**：每日/每小时损失限制和自动冷却机制
- **自动监控重启**：健康检查和自动恢复功能
- **资源优化**：降低内存占用和API调用频率

## 主要改进

### 1. 交易频率优化
- 交易间隔从30秒增加到120秒
- 根据时间段动态调整间隔：
  - 高峰期（9-17点）：96秒间隔，权重1.2
  - 非高峰期（18-8点）：180秒间隔，权重0.6
  - 维护期（2-4点）：240秒间隔，权重0.3

### 2. 风险控制增强
- 每日损失限制：3%
- 每小时损失限制：1%
- 自动冷却期：5分钟
- 恢复阈值：2%

### 3. 策略优化
- 交易金额：10U（符合Backpack最低交易要求）
- 调整止损止盈：止损0.4%，止盈1.0%
- 新增网格交易和做市商策略
- 优化RSI参数：超卖35，超买65

## 文件结构

```
backpack/
├── config.json                    # 24小时优化配置
├── start_24h_trading.py           # 24小时交易启动脚本
├── start_24h_farming.py           # 24小时积分刷取启动脚本
├── start_background_stable.py     # 稳定后台运行脚本 (推荐)
├── backpack_trader.py             # 优化的交易引擎
├── intelligent_points_farming.py  # 优化的积分刷取
├── start_trading.py               # 更新的启动脚本
├── start_backpack.py              # 统一启动器
├── monitor.py                     # 基础监控工具
├── monitor_enhanced.py            # 增强版监控工具 (推荐)
├── background_farming.log         # 后台运行日志
├── points_farming.log             # 积分刷取日志
├── backpack_farming.pid           # 进程ID文件
└── README_24H.md                  # 本文档
```

## 使用方法

### 1. 启动24小时交易系统

```bash
python start_24h_trading.py
```

### 2. 启动24小时积分刷取系统

```bash
python start_24h_farming.py
```

### 3. 启动后台积分刷取系统 (推荐)

```bash
# 通过主菜单启动
python start_backpack.py
# 选择 "3. 🔄 24小时积分刷取 (后台运行)"

# 或直接启动后台服务
python start_background_stable.py start
```

### 4. 监控系统状态

```bash
# 基础监控 (每15分钟自动更新)
python monitor.py

# 增强版监控 (支持手动刷新)
python monitor_enhanced.py
```

## 🔧 后台程序管理命令

### 服务状态管理

#### 查看服务状态
```bash
# 使用稳定的后台管理脚本
python start_background_stable.py status
```

#### 停止后台服务
```bash
# 方法1: 使用稳定的后台管理脚本 (推荐)
python start_background_stable.py stop

# 方法2: 使用统一启动器
python start_backpack.py
# 然后选择相应的停止选项

# 方法3: 强制终止 (如果上述方法无效)
# 查看Python进程
tasklist | findstr python

# 强制终止特定进程
taskkill /F /PID [进程ID]

# 或强制终止所有Python进程
taskkill /F /IM python.exe
```

#### 重启后台服务
```bash
# 手动操作 (停止后启动)
python start_background_stable.py stop
python start_background_stable.py start
```

### 日志管理

#### 查看运行日志
```bash
# 查看后台运行日志
Get-Content background_farming.log -Tail 20

# 查看积分刷取日志
Get-Content points_farming.log -Tail 20

# 查看最近50行日志
Get-Content background_farming.log -Tail 50
```

#### 日志文件位置
- **后台运行日志**: `background_farming.log`
- **积分刷取日志**: `points_farming.log`
- **PID文件**: `backpack_farming.pid`

### 故障排除

#### 强制停止服务
```bash
# 如果正常停止失败，强制停止
python start_background_simple.py stop

# 手动删除PID文件
del backpack_farming.pid

# 重新启动
python start_background_stable.py start
```

#### 清理和重启
```bash
# 1. 检查服务状态
python start_background_stable.py status

# 2. 停止服务
python start_background_stable.py stop

# 3. 清理PID文件
del backpack_farming.pid

# 4. 重新启动
python start_background_stable.py start

# 5. 验证启动
python start_background_stable.py status
```

#### Windows任务管理器管理
```bash
# 查看Python进程
tasklist | findstr python

# 根据PID结束进程 (替换XXXX为实际PID)
taskkill /F /PID XXXX
```

### 日常管理流程

#### 每日检查流程
```bash
# 1. 检查服务状态
python start_background_stable.py status

# 2. 查看最近日志
Get-Content background_farming.log -Tail 20

# 3. 如有需要，重启服务
python start_background_stable.py stop
python start_background_stable.py start

# 4. 确认重启成功
python start_background_stable.py status
```

#### 日志备份和清理
```bash
# 备份当前日志
copy background_farming.log background_farming.log.bak

# 清空日志文件
echo. > background_farming.log

# 重启服务
python start_background_stable.py stop
python start_background_stable.py start
```

## 配置说明

### 24小时调度配置

```json
{
  "24h_schedule": {
    "enabled": true,
    "peak_hours": {
      "start": 9,
      "end": 17,
      "trading_weight": 1.2,
      "interval_multiplier": 0.8
    },
    "off_hours": {
      "start": 18,
      "end": 8,
      "trading_weight": 0.6,
      "interval_multiplier": 1.5
    },
    "maintenance_window": {
      "start": 2,
      "end": 4,
      "trading_weight": 0.3,
      "interval_multiplier": 2.0
    }
  }
}
```

### 风险控制配置

```json
{
  "risk_management": {
    "max_daily_loss": 0.03,
    "max_hourly_loss": 0.01,
    "max_drawdown": 0.08,
    "cooldown_period": 300,
    "recovery_threshold": 0.02
  }
}
```

### 监控配置

```json
{
  "monitoring": {
    "health_check_interval": 300,
    "auto_restart": true,
    "max_restart_attempts": 3,
    "restart_delay": 60,
    "performance_logging": true
  }
}
```

## 时间段说明

### 高峰期（9:00-17:00）
- 交易频率：较高
- 策略权重：1.2
- 间隔倍数：0.8
- 适合：活跃交易

### 非高峰期（18:00-8:00）
- 交易频率：中等
- 策略权重：0.6
- 间隔倍数：1.5
- 适合：保守交易

### 维护期（2:00-4:00）
- 交易频率：最低
- 策略权重：0.3
- 间隔倍数：2.0
- 适合：系统维护

## 风险控制机制

### 1. 损失限制
- **每日限制**：总损失不超过3%
- **每小时限制**：单小时损失不超过1%
- **自动触发**：达到限制时自动进入冷却期

### 2. 冷却机制
- **冷却期**：5分钟无交易
- **恢复条件**：盈利达到2%时自动恢复
- **手动恢复**：重启系统

### 3. 自动重启
- **健康检查**：每5分钟检查系统状态
- **最大重启**：最多3次自动重启
- **重启延迟**：每次重启间隔60秒

## 监控功能

### 1. 基础监控 (`monitor.py`)
- **更新频率**: 每15分钟自动更新
- **实时数据**: 账户余额、盈亏状态
- **运行统计**: 成功/失败操作次数
- **进程状态**: 脚本运行状态检查

### 2. 增强版监控 (`monitor_enhanced.py`)
- **更新频率**: 每15分钟自动更新 + 手动刷新
- **实时数据**: 实时获取账户余额和盈亏
- **详细统计**: 交易、借贷、数据查询操作统计
- **后台服务**: 后台服务状态监控
- **手动刷新**: 按Enter键立即刷新数据

### 3. 监控数据
- **账户余额**: 实时抵押品净资产
- **盈亏状态**: 初始资金、当前资金、总盈亏
- **操作统计**: 各类操作的成功/失败次数
- **运行状态**: 脚本和服务运行状态
- **最后活动**: 最近一次操作时间

### 4. 健康检查
- API连接状态
- 内存使用情况
- 系统响应时间
- 错误日志监控

### 5. 自动恢复
- 连接断开自动重连
- 异常情况自动重启
- 资源清理和优化

## 性能优化

### 1. 资源使用
- 降低内存占用
- 优化API调用频率
- 减少不必要的计算

### 2. 网络优化
- 请求重试机制
- 连接池管理
- 超时控制

### 3. 日志管理
- 日志轮转
- 大小限制
- 自动清理

## 注意事项

1. **系统要求**：
   - Python 3.8+
   - 稳定的网络连接
   - 足够的内存（建议4GB+）

2. **安全建议**：
   - 定期备份配置文件
   - 监控API密钥使用
   - 设置合理的损失限制

3. **维护建议**：
   - 定期检查日志文件
   - 监控系统资源使用
   - 及时更新配置参数

## 故障排除

### 常见问题

1. **连接失败**
   - 检查网络连接
   - 验证API密钥
   - 查看错误日志

2. **内存不足**
   - 重启系统
   - 清理日志文件
   - 调整配置参数

3. **交易异常**
   - 检查账户余额
   - 验证交易对设置
   - 查看风险控制状态

4. **后台服务问题**
   - 检查服务状态：`python start_background_stable.py status`
   - 查看服务日志：`Get-Content background_farming.log -Tail 20`
   - 正常停止：`python start_background_stable.py stop`
   - 强制停止：`taskkill /F /IM python.exe`
   - 重启服务：`python start_background_stable.py stop && python start_background_stable.py start`

### 日志文件

- `trading.log`：交易日志
- `points_farming.log`：积分刷取日志
- `background_farming.log`：后台运行日志
- `backpack_farming.pid`：进程ID文件
- `pnl_data.json`：盈亏数据

### 后台服务故障排除

#### 服务无法启动
```bash
# 1. 检查PID文件是否存在
dir backpack_farming.pid

# 2. 删除旧的PID文件
del backpack_farming.pid

# 3. 重新启动
python start_background_stable.py start
```

#### 如何停止后台服务
```bash
# 方法1: 正常停止 (推荐)
python start_background_stable.py stop

# 方法2: 查看进程并强制停止
# 查看Python进程
tasklist | findstr python

# 强制终止特定进程 (替换[进程ID]为实际ID)
taskkill /F /PID [进程ID]

# 方法3: 强制终止所有Python进程
taskkill /F /IM python.exe

# 验证停止状态
python start_background_stable.py status
```

#### 服务无法停止
```bash
# 1. 强制停止
taskkill /F /IM python.exe

# 2. 手动删除PID文件
del backpack_farming.pid

# 3. 通过任务管理器结束进程
tasklist | findstr python
taskkill /F /PID [进程ID]
```

#### 日志文件过大
```bash
# 1. 备份日志
copy background_farming.log background_farming.log.bak

# 2. 清空日志
echo. > background_farming.log

# 3. 重启服务
python start_background_stable.py stop
python start_background_stable.py start
```

## 🎯 多账户24小时刷分策略完整工作流程

### 📋 **1. 系统启动阶段**

#### **Excel文件读取**
- 📊 自动读取 `backpack.xlsx` 文件
- 🔑 提取所有账户的API Key和API Secret
- ⚙️ 为每个账户创建独立配置
- 🔄 **每次运行都重新读取Excel**，支持动态添加账户

#### **多账户配置生成**
- 🏗️ 为每个账户创建独立的 `PointsFarmingConfig`
- 🔗 设置代理配置（可选）
- 📊 配置交易对：`["SOL_USDC", "BTC_USDC", "ETH_USDC"]`
- ⚖️ 设置止盈止损：**止盈1.0%，止损0.4%**

### 💰 **2. 资产检查与补足阶段**

#### **真实资产检查**
- 🔍 调用抵押品API获取真实资产数据
- 📊 检查SOL、ETH、BTC、USDC余额
- 💵 计算资产价值（按当前市场价格）
- ✅ 显示准确的资产状态

#### **自动资产补足**
- 🛒 检测到ETH/BTC不足时自动买入（各50U）
- 💰 优先使用现货USDC余额
- 🔄 失败时尝试使用借贷池资产
- ⚠️ 补足失败不影响策略继续运行

### 🔄 **3. 24小时循环运行**

#### **每日24个周期**
- ⏰ 每小时执行一个周期
- 🎲 每个周期随机选择操作类型
- 📊 操作权重分配：
  - **交易**: 40% (每日约20次交易)
  - **数据查询**: 25%
  - **账户活动**: 20%
  - **借贷操作**: 10%
  - **功能使用**: 5%

### 💹 **4. 交易策略执行**

#### **多样化交易策略**
- 🎯 **传统交易** (权重50%) - 成功率最高
- 📊 **网格交易** (权重20%)
- 🏪 **做市商策略** (权重20%)
- 📈 **双均线策略** (权重10%)

#### **止盈止损监控**
- 🛑 **止损**: 0.4% - 自动平仓
- 🎯 **止盈**: 1.0% - 自动平仓
- 📊 **持仓跟踪**: 实时监控价格变化
- 🔄 **智能平仓**: 自动执行止盈止损

#### **交易参数**
- 💰 交易金额：10-50U随机
- 📊 交易对：SOL/USDC、ETH/USDC、BTC/USDC
- ⏰ 订单类型：市价单和限价单随机
- 🔄 支持借贷池资产交易

### 📊 **5. 数据查询操作**

#### **市场数据查询**
- 📈 查询111个市场信息
- 💹 获取价格数据
- 📊 查询订单簿深度
- 📋 查询最近交易记录

#### **账户数据查询**
- 💰 查询账户余额
- 🏦 查询抵押品信息
- 📊 查询现货余额
- 🔍 查询账户信息

### 🏦 **6. 借贷操作**

#### **借贷池交互**
- 🔍 查询抵押品信息
- 💰 获取净资产数据
- 🎯 模拟借贷决策
- 📈 提升平台活跃度

### 🎯 **7. 账户活动提升**

#### **平台交互**
- 🔍 查询账户信息
- 💰 查询余额信息
- 🏦 查询抵押品信息
- 📊 查询系统状态

### 🔧 **8. 功能使用**

#### **平台功能体验**
- 📊 查询系统状态
- 🔍 测试各种API端点
- 📈 提升功能使用率

### 📊 **9. 风险控制**

#### **多层风险控制**
- 🛑 **单笔止损**: 0.4%
- 📊 **每日损失限制**: 10U
- ⏰ **操作间隔**: 10-30秒随机延迟
- 🔄 **API重试机制**: 自动重试失败的请求

#### **盈亏监控**
- 💰 实时监控抵押品净资产
- 📊 计算盈亏百分比
- 📋 记录每日统计
- 📈 生成盈亏报告

### 🚀 **10. 并发运行**

#### **多账户同时运行**
- 🔄 每个账户独立运行
- 🔗 支持不同代理配置
- 📊 独立的资产管理和交易
- 💰 独立的盈亏监控

### 📝 **11. 日志记录**

#### **详细日志系统**
- 📊 操作日志记录
- 💹 交易记录
- ⚠️ 错误日志
- 📈 统计信息

### 🎯 **12. 积分最大化策略**

#### **全方位平台交互**
- 💹 **交易活跃度**: 通过多样化交易策略
- 📊 **数据查询**: 频繁的市场数据查询
- 🏦 **借贷参与**: 借贷池交互
- 🎯 **账户活跃**: 账户信息查询
- 🔧 **功能使用**: 平台功能体验

## 🎉 **系统特点总结**

您的多账户24小时刷分系统现在是一个**完整的、智能的、自动化的积分获取系统**，具备：

- ✅ **真实资产检查** - 准确显示账户余额
- ✅ **自动资产补足** - 智能买入不足资产
- ✅ **多样化交易策略** - 4种交易策略随机执行
- ✅ **完整止盈止损** - 1.0%止盈，0.4%止损
- ✅ **24小时循环运行** - 每小时一个周期
- ✅ **多账户并发** - 支持无限账户同时运行
- ✅ **风险控制** - 多层风险保护
- ✅ **实时监控** - 盈亏状态实时跟踪
- ✅ **Excel集成** - 一键启动，动态配置

这个系统现在完全按照单账户模式的标准运行，但支持多账户并发，是一个真正的**企业级多账户积分刷取系统**！🚀

## 更新日志

### v2.3.0 (多账户Excel集成版)
- ✅ 新增Excel多账户支持
- ✅ 真实资产检查功能
- ✅ 完整止盈止损系统
- ✅ API重试机制优化
- ✅ 多账户并发运行
- ✅ 动态Excel配置读取

### v2.2.0 (监控功能增强版)
- 新增增强版监控脚本 `monitor_enhanced.py`
- 优化监控数据更新频率 (15分钟)
- 实时获取账户余额和盈亏数据
- 支持手动刷新监控数据
- 增强后台服务状态监控
- 详细的操作统计和分类

### v2.1.0 (后台管理优化版)
- 新增后台程序管理功能
- 优化交易频率 (每日约20次交易)
- 新增 `start_background_stable.py` 稳定后台管理脚本
- 完善后台服务启动/停止/重启功能
- 增强日志管理和故障排除功能

### v2.3.0 (文件结构优化版)
- 删除冗余的启动文件，简化文件结构
- 统一使用 `start_background_stable.py` 作为后台管理脚本
- 更新文档和命令，提高易用性
- 优化监控脚本的后台服务状态检测
- 完善停止后台服务的多种方法和故障排除指南

### v2.0.0 (24小时优化版)
- 新增24小时运行支持
- 优化时间调度系统
- 增强风险控制机制
- 改进监控和日志系统
- 优化资源使用

## 技术支持

如有问题，请检查：
1. 配置文件是否正确
2. API密钥是否有效
3. 网络连接是否稳定
4. 系统资源是否充足

---

**免责声明**：本系统仅供学习和研究使用，实际交易存在风险，请谨慎使用并做好风险控制。
