# 部署指南 - Resource Monitor

## 自动化部署工具

本项目提供了完整的自动化部署脚本，支持：
- ✅ 使用 uv 管理虚拟环境
- ✅ 自动检测和安装依赖
- ✅ systemd 服务自动启动
- ✅ 本地持久化环境（.venv）

## 快速开始

### 1. 安装 uv（如果尚未安装）

```bash
# 方式一：使用安装脚本（推荐）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 方式二：使用 pip
pip install uv
```

### 2. 设置虚拟环境

运行环境设置脚本会自动：
- 检测 uv 是否安装
- 创建 `.venv` 虚拟环境（如果不存在）
- 安装/更新所有依赖包
- 验证安装完整性

```bash
./setup_env.sh
```

### 3. 配置服务器

编辑配置文件：

```bash
cp config.example.json config.json
nano config.json  # 或使用你喜欢的编辑器
```

### 4. 测试运行

使用 start.sh 脚本测试运行（前台运行）：

```bash
./start.sh
```

访问 http://localhost:8080 检查是否正常工作。按 Ctrl+C 停止。

### 5. 安装为系统服务（开机自启）

**重要：** 安装服务前必须先运行 `./setup_env.sh` 创建虚拟环境！

```bash
sudo ./install_service.sh
```

安装脚本会：
- 检查 .venv 虚拟环境是否存在
- 自动检测当前用户
- 创建 systemd 服务文件
- 启用开机自动启动
- 提示是否立即启动服务

**注意：** 如果看到 "Virtual environment not found" 错误，请先运行 `./setup_env.sh`

## 服务管理

### 启动服务

```bash
sudo systemctl start resource-monitor
```

### 停止服务

```bash
sudo systemctl stop resource-monitor
```

### 重启服务

```bash
sudo systemctl restart resource-monitor
```

### 查看服务状态

```bash
sudo systemctl status resource-monitor
```

### 查看实时日志

```bash
sudo journalctl -u resource-monitor -f
```

### 查看历史日志

```bash
# 查看最近 100 行
sudo journalctl -u resource-monitor -n 100

# 查看今天的日志
sudo journalctl -u resource-monitor --since today

# 查看特定时间范围
sudo journalctl -u resource-monitor --since "2025-12-01" --until "2025-12-07"
```

### 禁用开机自启

```bash
sudo systemctl disable resource-monitor
```

### 卸载服务

```bash
sudo ./uninstall_service.sh
```

## 文件说明

### 脚本文件

| 文件 | 说明 |
|------|------|
| `setup_env.sh` | 环境设置脚本，检查并安装虚拟环境和依赖 |
| `start.sh` | 前台启动脚本，用于测试和调试 |
| `install_service.sh` | 服务安装脚本，配置 systemd 自动启动 |
| `uninstall_service.sh` | 服务卸载脚本 |
| `resource-monitor.service` | Systemd 服务配置模板 |

### 虚拟环境

- 位置：`/path/to/project/.venv/`
- Python 可执行文件：`.venv/bin/python`
- Pip 可执行文件：`.venv/bin/pip`

虚拟环境是**本地持久化**的，不会随系统重启而丢失。

## 工作原理

### 1. 环境检测流程

```
setup_env.sh 执行
  ↓
检查 uv 是否安装
  ↓
检查 .venv 是否存在
  ↓
[不存在] → 使用 uv venv .venv 创建
  ↓
[存在] → 验证 Python 可执行文件
  ↓
使用 uv pip install -r requirements.txt 安装依赖
  ↓
验证关键包（flask, paramiko, apscheduler, psutil）
  ↓
完成
```

### 2. 服务启动流程

```
系统启动
  ↓
Systemd 启动 resource-monitor.service
  ↓
执行 ExecStartPre: setup_env.sh（确保环境就绪）
  ↓
执行 ExecStart: .venv/bin/python main.py
  ↓
监控服务运行，出错自动重启
```

### 3. uv 的优势

- **快速**：比 pip 快 10-100 倍
- **可靠**：完整的依赖解析
- **简单**：与 pip 兼容的命令
- **本地化**：虚拟环境存储在项目目录

## 故障排除

### 问题：uv 未安装

```bash
ERROR: uv is not installed!
```

**解决方案**：安装 uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 问题：权限不足

```bash
ERROR: This script must be run as root (use sudo)
```

**解决方案**：使用 sudo 运行安装脚本

```bash
sudo ./install_service.sh
```

### 问题：服务启动失败

**检查日志**：

```bash
sudo journalctl -u resource-monitor -n 50
```

**常见原因**：
1. 配置文件错误 → 检查 config.json
2. 端口被占用 → 检查 8080 端口
3. SSH 连接失败 → 检查服务器配置和网络

### 问题：依赖包安装失败

**手动重新安装**：

```bash
source .venv/bin/activate
uv pip install -r requirements.txt --force-reinstall
```

### 问题：服务重启过于频繁

服务配置了自动重启（RestartSec=10），如果持续失败可能导致频繁重启。

**检查原因**：

```bash
sudo journalctl -u resource-monitor --since "10 minutes ago"
```

**临时停止**：

```bash
sudo systemctl stop resource-monitor
```

## 更新应用

### 方法一：Git 拉取更新

```bash
# 停止服务
sudo systemctl stop resource-monitor

# 拉取最新代码
git pull

# 更新依赖（如果 requirements.txt 有变化）
./setup_env.sh

# 重启服务
sudo systemctl start resource-monitor
```

### 方法二：重新安装

```bash
# 卸载服务
sudo ./uninstall_service.sh

# 更新代码
git pull

# 重新设置环境
./setup_env.sh

# 重新安装服务
sudo ./install_service.sh
```

## 安全建议

### 1. 服务运行用户

- ✅ 服务以非 root 用户运行
- ✅ 使用 User= 和 Group= 指定用户
- ⚠️ 确保该用户有权限读取配置文件

### 2. 配置文件权限

```bash
# 限制配置文件权限（包含敏感信息）
chmod 600 config.json
chown $USER:$USER config.json
```

### 3. SSH 密钥认证

推荐使用 SSH 密钥而非密码：

```bash
# 生成密钥对
ssh-keygen -t ed25519 -C "resource-monitor"

# 复制公钥到远程服务器
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@server

# 在 config.json 中设置 password 为空字符串
```

### 4. 防火墙配置

如果需要远程访问 Web 界面：

```bash
# 开放 8080 端口（示例）
sudo ufw allow 8080/tcp

# 或限制特定 IP 访问
sudo ufw allow from 192.168.1.0/24 to any port 8080
```

## 性能优化

### 1. 调整采集间隔

编辑 `config.json`：

```json
{
  "monitoring": {
    "resource_check_interval": 300,  // 5分钟，根据需要调整
    "disk_check_interval": 28800     // 8小时，根据需要调整
  }
}
```

### 2. 限制数据历史

默认保留 24 小时数据。如需调整，修改 `data_aggregator.py` 中的 `max_age` 参数。

### 3. 资源限制

服务文件中已设置 `LimitNOFILE=65536`，如需其他限制可添加：

```ini
[Service]
# 内存限制（示例：512MB）
MemoryLimit=512M

# CPU 权重
CPUWeight=100
```

## 备份和恢复

### 备份

备份以下文件即可：

```bash
# 配置文件
cp config.json config.json.backup

# （可选）服务配置
sudo cp /etc/systemd/system/resource-monitor.service resource-monitor.service.backup
```

### 恢复

```bash
# 恢复配置
cp config.json.backup config.json

# 如果需要恢复服务配置
sudo ./install_service.sh
```

## 技术支持

- 查看 README.md 了解功能详情
- 查看 QUICKSTART.md 快速入门
- 查看日志排查问题：`sudo journalctl -u resource-monitor`

## 完整部署示例

```bash
# 1. 克隆项目
git clone <repository-url>
cd resource_monitor

# 2. 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. 设置环境
./setup_env.sh

# 4. 配置服务器
cp config.example.json config.json
nano config.json

# 5. 测试运行
./start.sh
# 按 Ctrl+C 停止

# 6. 安装服务
sudo ./install_service.sh

# 7. 查看状态
sudo systemctl status resource-monitor

# 8. 访问 Web 界面
# 浏览器打开 http://localhost:8080
```

部署完成！🎉
