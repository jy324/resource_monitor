# 资源监控系统 (Resource Monitor)

一个分布式服务器资源监控系统，用于实时监控服务器池中多台服务器的CPU、GPU、内存和磁盘使用情况。

## 功能特性

- 📊 **实时资源监控**: 每5分钟自动收集CPU、GPU和内存使用率
- 💾 **磁盘监控**: 每8小时检查 `/home` 和 `/data` 磁盘使用情况
- 🌐 **Web界面**: 提供直观的Web仪表板展示所有指标
- 🔄 **自动刷新**: 前端每10秒自动更新数据
- 🖥️ **多服务器支持**: 可同时监控服务器池中的多台服务器
- 📈 **历史数据**: 保存24小时的历史监控数据
- 🏠 **本地监控**: 自动检测并直接监控本地服务器（无需SSH）

## 系统架构

```
┌─────────────────────────────────────────────────┐
│           监控服务器 (Monitor Server)           │
│                                                 │
│  ┌──────────────┐      ┌──────────────────┐   │
│  │ HTTP Server  │◄─────┤ Data Aggregator  │   │
│  │  (Flask)     │      │                  │   │
│  └──────────────┘      └────────▲─────────┘   │
│         │                        │             │
│         │              ┌─────────┴─────────┐   │
│    ┌────▼────┐        │  Monitoring       │   │
│    │ Frontend │        │  Service          │   │
│    │ (HTML/JS)│        │  (Scheduler)      │   │
│    └─────────┘        └─────────┬─────────┘   │
│                                  │             │
│                       ┌──────────┴──────────┐  │
│                       │ Resource Collectors │  │
│                       └──────────┬──────────┘  │
└───────────────────────────────────┼─────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌──────────┐    ┌──────────┐    ┌──────────┐
            │ Server 1 │    │ Server 2 │    │ Server 3 │
            │ (SSH)    │    │ (SSH)    │    │ (SSH)    │
            └──────────┘    └──────────┘    └──────────┘
```

## 快速开始

### 自动化部署（推荐）

使用自动化脚本快速部署，支持开机自启和虚拟环境管理：

```bash
# 1. 安装 uv（如果尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 设置虚拟环境和依赖
./setup_env.sh

# 3. 配置服务器
cp config.example.json config.json
nano config.json

# 4. 测试运行
./start.sh

# 5. 安装为系统服务（开机自启）
sudo ./install_service.sh
```

**完整部署文档**: 查看 [DEPLOYMENT.md](DEPLOYMENT.md) 了解详细部署步骤、服务管理和故障排除。

### 手动安装

## 安装配置

### 1. 系统要求

- Python 3.7+
- uv（推荐）或 pip
- 对目标服务器的SSH访问权限
- 目标服务器需要安装：
  - Linux操作系统
  - 基础命令工具（top, free, df等）
  - nvidia-smi（如需GPU监控）

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置服务器

编辑 `config.json` 文件，配置需要监控的服务器：

```json
{
  "servers": [
    {
      "name": "server1",
      "host": "192.168.1.101",
      "port": 22,
      "username": "monitor",
      "password": ""
    },
    {
      "name": "server2",
      "host": "192.168.1.102",
      "port": 22,
      "username": "monitor",
      "password": ""
    },
    {
      "name": "server3",
      "host": "192.168.1.103",
      "port": 22,
      "username": "monitor",
      "password": ""
    }
  ],
  "monitoring": {
    "resource_check_interval": 300,
    "disk_check_interval": 28800
  },
  "http_server": {
    "host": "0.0.0.0",
    "port": 8080
  }
}
```

**配置说明**：
- `servers`: 服务器列表
  - `name`: 服务器名称（显示在仪表板上）
  - `host`: 服务器IP地址或主机名
  - `port`: SSH端口（默认22）
  - `username`: SSH用户名
  - `password`: SSH密码（**可选**）
    - 如果提供密码（非空字符串），使用密码认证
    - 如果为空字符串 `""`，使用SSH密钥认证（推荐）
    - **不需要同时配置密码和SSH密钥**，选择其中一种即可
- `monitoring`: 监控配置
  - `resource_check_interval`: 资源检查间隔（秒），默认300秒（5分钟）
  - `disk_check_interval`: 磁盘检查间隔（秒），默认28800秒（8小时）
- `http_server`: HTTP服务器配置
  - `host`: 监听地址（0.0.0.0表示所有接口）
  - `port`: 监听端口

### 4. SSH认证配置

系统支持两种认证方式，**选择其中一种即可**：

#### 方式一：SSH密钥认证（推荐）

在 `config.json` 中将 `password` 设为空字符串 `""`，系统将自动使用SSH密钥：

```bash
# 生成SSH密钥（如果还没有）
ssh-keygen -t rsa -b 4096

# 将公钥复制到目标服务器
ssh-copy-id -i ~/.ssh/id_rsa.pub monitor@192.168.1.101

# 测试连接
ssh monitor@192.168.1.101
```

配置示例：
```json
{
  "servers": [
    {
      "name": "server1",
      "host": "192.168.1.101",
      "port": 22,
      "username": "monitor",
      "password": ""
    }
  ]
}
```

#### 方式二：密码认证

在 `config.json` 中直接设置 `password` 字段：

```json
{
  "servers": [
    {
      "name": "server1",
      "host": "192.168.1.101",
      "port": 22,
      "username": "monitor",
      "password": "your_password_here"
    }
  ]
}
```

**注意**：密码认证安全性较低，不建议在生产环境使用。

### 监控本地服务器

系统会自动检测配置中的本地服务器（localhost、127.0.0.1或本机主机名），并使用 `psutil` 库直接监控，无需SSH连接。

**示例配置（监控本地服务器）**：
```json
{
  "servers": [
    {
      "name": "a100",
      "host": "localhost",
      "port": 22,
      "username": "monitor",
      "password": ""
    }
  ]
}
```

当 `host` 为以下任一值时，将自动启用本地监控：
- `localhost`
- `127.0.0.1`
- `::1`
- 本机主机名
- 解析为本机IP的主机名

**优势**：
- 无需SSH配置
- 更快的数据采集速度
- 更准确的实时数据
- 避免SSH认证问题

## 使用方法

### 启动监控系统

```bash
python main.py [config.json]
```

或者：

```bash
python3 main.py
```

系统启动后会：
1. 加载配置文件
2. 初始化监控服务
3. 启动定时任务（资源监控和磁盘监控）
4. 启动HTTP服务器

### 访问Web界面

在浏览器中访问：

```
http://localhost:8080
```

或者使用服务器IP地址：

```
http://<监控服务器IP>:8080
```

## API接口

系统提供以下REST API接口：

### 1. 获取最新数据
```
GET /api/latest
```

返回所有服务器的最新监控数据。

### 2. 获取历史数据
```
GET /api/history?server=<server_name>&hours=<hours>
```

参数：
- `server`: 服务器名称（可选，默认为所有服务器）
- `hours`: 历史数据时长（小时，默认为1）

### 3. 获取统计摘要
```
GET /api/summary
```

返回所有服务器的统计摘要信息。

### 4. 健康检查
```
GET /api/health
```

检查服务状态。

## 监控指标

### CPU监控
- 实时CPU使用率百分比
- 每5分钟更新

### 内存监控
- 总内存容量
- 已使用内存
- 内存使用率百分比
- 每5分钟更新

### GPU监控（需要nvidia-smi）
- GPU索引和名称
- GPU利用率
- 显存使用情况
- 每5分钟更新

### 磁盘监控
- `/home` 目录磁盘使用情况
- `/data` 目录磁盘使用情况
- 总容量、已使用、可用空间
- 每8小时更新

## 安全建议

### SSH连接安全

1. **使用SSH密钥认证** (推荐):
   - 比密码认证更安全
   - 在 `config.json` 中将 `password` 留空
   - 确保私钥权限正确 (chmod 600)

2. **Host Key验证**:
   - 首次连接时，系统会自动接受未知主机密钥
   - 生产环境建议预先配置 `~/.ssh/known_hosts`
   - 或修改代码使用 `RejectPolicy()` 进行严格验证

3. **最小权限原则**:
   - 为监控创建专用用户账户
   - 仅授予必要的命令执行权限
   - 考虑使用 sudo 配置限制命令

4. **网络安全**:
   - 使用防火墙限制SSH访问
   - 考虑使用VPN或堡垒机
   - 启用SSH日志审计

### HTTP服务器安全

1. **使用反向代理**:
   ```nginx
   location / {
       proxy_pass http://localhost:8080;
   }
   ```

2. **添加认证**:
   - 考虑在反向代理层添加基础认证
   - 或在Flask应用中添加登录功能

3. **HTTPS**:
   - 生产环境建议使用HTTPS
   - 使用Let's Encrypt等免费证书

## 故障排除

### 无法连接到服务器

1. 检查SSH连接：
```bash
ssh username@hostname
```

2. 验证SSH密钥或密码配置
3. 检查防火墙设置
4. 确认目标服务器SSH服务正常运行

### GPU信息无法获取

1. 确认目标服务器安装了NVIDIA驱动和nvidia-smi：
```bash
nvidia-smi
```

2. 如果没有GPU，系统会正常显示其他指标

### Web界面无法访问

1. 检查HTTP服务是否正常运行
2. 验证端口是否被占用：
```bash
netstat -tuln | grep 8080
```

3. 检查防火墙设置

## 文件结构

```
resource_monitor/
├── main.py                 # 主程序入口
├── config.json             # 配置文件
├── requirements.txt        # Python依赖
├── resource_collector.py   # 资源收集模块
├── data_aggregator.py      # 数据聚合模块
├── monitoring_service.py   # 监控服务模块
├── http_server.py          # HTTP服务器
├── static/                 # 前端静态文件
│   ├── index.html         # 主页面
│   ├── style.css          # 样式表
│   └── script.js          # JavaScript代码
└── README.md              # 本文档
```

## 技术栈

- **后端**: Python 3, Flask
- **前端**: HTML5, CSS3, JavaScript (原生)
- **SSH通信**: Paramiko
- **任务调度**: APScheduler
- **数据存储**: 内存存储（可扩展为数据库）

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！