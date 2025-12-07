# 快速开始指南 (Quick Start Guide)

## 最小化配置步骤

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置服务器连接

复制示例配置：
```bash
cp config.example.json config.json
```

编辑 `config.json`，修改服务器信息。

**重要：选择以下两种认证方式之一**

#### 选项A：SSH密钥认证（推荐）
```json
{
  "servers": [
    {
      "name": "server1",
      "host": "YOUR_SERVER_IP",
      "port": 22,
      "username": "YOUR_USERNAME",
      "password": ""
    }
  ]
}
```

#### 选项B：密码认证
```json
{
  "servers": [
    {
      "name": "server1",
      "host": "YOUR_SERVER_IP",
      "port": 22,
      "username": "YOUR_USERNAME",
      "password": "YOUR_PASSWORD"
    }
  ]
}
```

### 3. 配置SSH密钥（如果选择选项A）

```bash
# 生成SSH密钥（如果还没有）
ssh-keygen -t rsa -b 4096

# 复制公钥到目标服务器
ssh-copy-id username@server_ip
```

### 4. 启动监控系统

```bash
python3 main.py
```

### 5. 访问Web界面

打开浏览器访问：
```
http://localhost:8080
```

## 验证安装

### 测试系统
```bash
python3 test_system.py
```

### 测试API端点
```bash
# 健康检查
curl http://localhost:8080/api/health

# 获取最新数据
curl http://localhost:8080/api/latest

# 获取摘要
curl http://localhost:8080/api/summary
```

## 常见问题

### 无法连接到服务器
1. 检查SSH连接：`ssh username@server_ip`
2. 确认防火墙设置
3. 验证SSH密钥或密码

### GPU信息为空
- 正常现象，如果服务器没有NVIDIA GPU

### Web界面无法访问
1. 检查端口占用：`netstat -tuln | grep 8080`
2. 确认服务器正在运行：`ps aux | grep main.py`

## 生产环境建议

1. **使用systemd服务**
   - 创建服务文件管理监控系统
   - 自动启动和重启

2. **配置反向代理**
   - 使用Nginx或Apache
   - 添加HTTPS支持

3. **启用认证**
   - 添加基础认证
   - 或使用OAuth2

4. **日志管理**
   - 配置日志轮转
   - 监控日志文件大小

## 下一步

- 阅读完整 [README.md](README.md) 了解所有功能
- 查看安全建议章节
- 根据需求调整监控间隔
