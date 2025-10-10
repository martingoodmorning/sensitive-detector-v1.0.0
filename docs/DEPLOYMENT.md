# 部署指南

## 概述

本文档详细说明敏感词检测系统的部署流程，包括开发环境、测试环境和生产环境的部署配置。

## 环境要求

### 硬件要求

| 环境 | CPU | 内存 | 存储 | 网络 |
|------|-----|------|------|------|
| 开发环境 | 2核 | 4GB | 20GB | 100Mbps |
| 测试环境 | 4核 | 8GB | 50GB | 100Mbps |
| 生产环境 | 8核 | 16GB | 100GB | 1Gbps |

### 软件要求

- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Windows 10+ (WSL)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.10+ (本地开发)
- **Node.js**: 16+ (前端构建)

## 开发环境部署

### 1. 环境准备

**Ubuntu/WSL 环境**:
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 安装 Python 3.10
sudo apt install python3.10 python3.10-venv python3.10-dev

# 安装 Git
sudo apt install git
```

**Windows 环境**:
```powershell
# 安装 WSL2
wsl --install

# 安装 Docker Desktop
# 下载并安装 Docker Desktop for Windows

# 安装 Python
# 下载并安装 Python 3.10 from python.org
```

### 2. 项目克隆

```bash
# 克隆项目
git clone <repository-url>
cd sensitive-detector

# 检查项目结构
ls -la
```

### 3. Ollama 服务部署

```bash
# 安装 Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 启动 Ollama 服务
export OLLAMA_HOST=0.0.0.0:11434
ollama serve &

# 下载 qwen:7b 模型
ollama pull qwen:7b

# 验证安装
ollama list
curl http://localhost:11434/api/tags
```

### 4. 应用部署

```bash
# 构建并启动服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f sensitive-detector-backend
```

### 5. 访问验证

```bash
# 健康检查
curl http://localhost:8000/health

# 文本检测测试
curl -X POST "http://localhost:8000/detect/text" \
     -H "Content-Type: application/json" \
     -d '{"text":"测试文本"}'

# 访问前端界面
# 浏览器打开: http://localhost:8000
```

## 测试环境部署

### 1. 服务器准备

```bash
# 创建部署用户
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG docker deploy
sudo usermod -aG sudo deploy

# 切换到部署用户
su - deploy
```

### 2. 环境配置

```bash
# 创建应用目录
sudo mkdir -p /opt/sensitive-detector
sudo chown deploy:deploy /opt/sensitive-detector
cd /opt/sensitive-detector

# 克隆代码
git clone <repository-url> .

# 创建配置文件
cp docker-compose.yml docker-compose.prod.yml
```

### 3. 生产配置

**docker-compose.prod.yml**:
```yaml
services:
  sensitive-detector-backend:
    build: ./backend
    container_name: sensitive-detector-prod
    ports:
      - "8000:8000"
    volumes:
      - ./backend/sensitive_words.txt:/app/sensitive_words.txt
      - ./frontend:/app/frontend
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
      - OLLAMA_BASE_URL=http://172.20.0.1:11434
      - OLLAMA_MODEL=qwen:7b
      - CORS_ALLOW_ORIGINS=https://your-domain.com
      - LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 本章节将详细介绍敏感词检测系统的部署流程，包括开发环境、测试环境和生产环境的部署配置。我们将从环境要求开始，逐步介绍各种部署方式，并提供详细的配置示例和故障排除指南。

## 概述

敏感词检测系统采用容器化部署方式，支持 Docker 和 Docker Compose 一键部署。系统包含前端界面、后端 API 服务和 Ollama LLM 服务三个主要组件。

## 环境要求

### 硬件要求

| 环境 | CPU | 内存 | 存储 | 网络 |
|------|-----|------|------|------|
| 开发环境 | 2核 | 4GB | 20GB | 100Mbps |
| 测试环境 | 4核 | 8GB | 50GB | 100Mbps |
| 生产环境 | 8核 | 16GB | 100GB | 1Gbps |

### 软件要求

- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Windows 10+ (WSL)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.10+ (本地开发)
- **Node.js**: 16+ (前端构建)

## 开发环境部署

### 1. 环境准备

**Ubuntu/WSL 环境**:
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 安装 Python 3.10
sudo apt install python3.10 python3.10-venv python3.10-dev

# 安装 Git
sudo apt install git
```

**Windows 环境**:
```powershell
# 安装 WSL2
wsl --install

# 安装 Docker Desktop
# 下载并安装 Docker Desktop for Windows

# 安装 Python
# 下载并安装 Python 3.10 from python.org
```

### 2. 项目克隆

```bash
# 克隆项目
git clone <repository-url>
cd sensitive-detector

# 检查项目结构
ls -la
```

### 3. Ollama 服务部署

```bash
# 安装 Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 启动 Ollama 服务
export OLLAMA_HOST=0.0.0.0:11434
ollama serve &

# 下载 qwen:7b 模型
ollama pull qwen:7b

# 验证安装
ollama list
curl http://localhost:11434/api/tags
```

### 4. 应用部署

```bash
# 构建并启动服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f sensitive-detector-backend
```

### 5. 访问验证

```bash
# 健康检查
curl http://localhost:8000/health

# 文本检测测试
curl -X POST "http://localhost:8000/detect/text" \
     -H "Content-Type: application/json" \
     -d '{"text":"测试文本"}'

# 访问前端界面
# 浏览器打开: http://localhost:8000
```

## 测试环境部署

### 1. 服务器准备

```bash
# 创建部署用户
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG docker deploy
sudo usermod -aG sudo deploy

# 切换到部署用户
su - deploy
```

### 2. 环境配置

```bash
# 创建应用目录
sudo mkdir -p /opt/sensitive-detector
sudo chown deploy:deploy /opt/sensitive-detector
cd /opt/sensitive-detector

# 克隆代码
git clone <repository-url> .

# 创建配置文件
cp docker-compose.yml docker-compose.prod.yml
```

### 3. 生产配置

**docker-compose.prod.yml**:
```yaml
services:
  sensitive-detector-backend:
    build: ./backend
    container_name: sensitive-detector-prod
    ports:
      - "8000:8000"
    volumes:
      - ./backend/sensitive_words.txt:/app/sensitive_words.txt
      - ./frontend:/app/frontend
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
      - OLLAMA_BASE_URL=http://172.20.0.1:11434
      - OLLAMA_MODEL=qwen:7b
      - CORS_ALLOW_ORIGINS=https://your-domain.com
      - LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 4. 部署脚本

**deploy.sh**:
```bash
#!/bin/bash

set -e

echo "开始部署敏感词检测系统..."

# 检查 Docker 服务
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker 服务未运行"
    exit 1
fi

# 检查 Ollama 服务
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "错误: Ollama 服务未运行"
    exit 1
fi

# 停止现有服务
echo "停止现有服务..."
docker compose -f docker-compose.prod.yml down

# 构建新镜像
echo "构建新镜像..."
docker compose -f docker-compose.prod.yml build --no-cache

# 启动服务
echo "启动服务..."
docker compose -f docker-compose.prod.yml up -d

# 等待服务启动
echo "等待服务启动..."
sleep 30

# 健康检查
echo "执行健康检查..."
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "部署成功!"
else
    echo "部署失败: 健康检查未通过"
    exit 1
fi

echo "部署完成!"
```

### 5. 部署执行

```bash
# 赋予执行权限
chmod +x deploy.sh

# 执行部署
./deploy.sh
```

## 生产环境部署

### 1. 服务器配置

```bash
# 系统优化
echo 'vm.max_map_count=262144' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# 防火墙配置
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8000
sudo ufw enable
```

### 2. Nginx 反向代理

**安装 Nginx**:
```bash
sudo apt update
sudo apt install nginx
```

**Nginx 配置**:
```nginx
# /etc/nginx/sites-available/sensitive-detector
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL 证书配置
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    
    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # 反向代理配置
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # 缓冲配置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # 静态文件缓存
    location /static/ {
        proxy_pass http://localhost:8000;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 健康检查
    location /health {
        proxy_pass http://localhost:8000;
        access_log off;
    }
}
```

**启用配置**:
```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/sensitive-detector /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 3. SSL 证书配置

**使用 Let's Encrypt**:
```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 4. 监控配置

**安装 Prometheus**:
```bash
# 下载 Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xzf prometheus-2.45.0.linux-amd64.tar.gz
sudo mv prometheus-2.45.0.linux-amd64 /opt/prometheus

# 创建配置文件
sudo tee /opt/prometheus/prometheus.yml > /dev/null <<EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'sensitive-detector'
    static_configs:
      - targets: ['localhost:8000']
EOF

# 创建 systemd 服务
sudo tee /etc/systemd/system/prometheus.service > /dev/null <<EOF
[Unit]
Description=Prometheus
After=network.target

[Service]
Type=simple
User=prometheus
ExecStart=/opt/prometheus/prometheus --config.file=/opt/prometheus/prometheus.yml
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo useradd --no-create-home --shell /bin/false prometheus
sudo chown -R prometheus:prometheus /opt/prometheus
sudo systemctl daemon-reload
sudo systemctl start prometheus
sudo systemctl enable prometheus
```

**安装 Grafana**:
```bash
# 添加 Grafana 仓库
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list

# 安装 Grafana
sudo apt update
sudo apt install grafana

# 启动服务
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

### 5. 日志管理

**配置日志轮转**:
```bash
# 创建日志目录
sudo mkdir -p /var/log/sensitive-detector
sudo chown deploy:deploy /var/log/sensitive-detector

# 配置 logrotate
sudo tee /etc/logrotate.d/sensitive-detector > /dev/null <<EOF
/var/log/sensitive-detector/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 deploy deploy
    postrotate
        docker compose -f /opt/sensitive-detector/docker-compose.prod.yml restart sensitive-detector-backend
    endscript
}
EOF
```

### 6. 备份策略

**创建备份脚本**:
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/opt/backups/sensitive-detector"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份应用代码
tar -czf $BACKUP_DIR/code_$DATE.tar.gz -C /opt sensitive-detector

# 备份敏感词库
cp /opt/sensitive-detector/backend/sensitive_words.txt $BACKUP_DIR/sensitive_words_$DATE.txt

# 备份配置文件
cp /opt/sensitive-detector/docker-compose.prod.yml $BACKUP_DIR/config_$DATE.yml

# 清理旧备份 (保留30天)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.txt" -mtime +30 -delete
find $BACKUP_DIR -name "*.yml" -mtime +30 -delete

echo "备份完成: $BACKUP_DIR"
```

**设置定时备份**:
```bash
# 添加到 crontab
crontab -e
# 添加: 0 2 * * * /opt/sensitive-detector/backup.sh
```

## 容器化部署

### 1. Docker 镜像构建

**后端 Dockerfile**:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 多阶段构建

**优化 Dockerfile**:
```dockerfile
# 构建阶段
FROM python:3.10-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 运行阶段
FROM python:3.10-slim

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制 Python 包
COPY --from=builder /root/.local /root/.local

# 复制应用代码
COPY . .

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 设置环境变量
ENV PATH=/root/.local/bin:$PATH

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Docker Compose 配置

**docker-compose.prod.yml**:
```yaml
version: '3.8'

services:
  sensitive-detector-backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: sensitive-detector-prod
    ports:
      - "8000:8000"
    volumes:
      - ./backend/sensitive_words.txt:/app/sensitive_words.txt:ro
      - ./frontend:/app/frontend:ro
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
      - OLLAMA_BASE_URL=http://172.20.0.1:11434
      - OLLAMA_MODEL=qwen:7b
      - CORS_ALLOW_ORIGINS=https://your-domain.com
      - LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - app-network
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'

networks:
  app-network:
    driver: bridge
```

## 性能优化

### 1. 系统优化

```bash
# 内核参数优化
echo 'net.core.somaxconn = 65535' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_max_syn_backlog = 65535' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_fin_timeout = 30' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# 文件描述符限制
echo '* soft nofile 65535' | sudo tee -a /etc/security/limits.conf
echo '* hard nofile 65535' | sudo tee -a /etc/security/limits.conf
```

### 2. Docker 优化

```yaml
# docker-compose.prod.yml
services:
  sensitive-detector-backend:
    # ... 其他配置
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
    ulimits:
      nofile:
        soft: 65535
        hard: 65535
```

### 3. 应用优化

```python
# main.py
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,  # 多进程
        loop="uvloop",  # 高性能事件循环
        http="httptools",  # 高性能 HTTP 解析器
        log_level="info"
    )
```

## 安全配置

### 1. 网络安全

```bash
# 防火墙配置
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 禁用不必要的服务
sudo systemctl disable bluetooth
sudo systemctl disable cups
sudo systemctl disable avahi-daemon
```

### 2. 容器安全

```dockerfile
# 使用非 root 用户
RUN useradd -m -u 1000 appuser
USER appuser

# 只读文件系统
docker run --read-only --tmpfs /tmp sensitive-detector

# 资源限制
docker run --memory=2g --cpus=1.0 sensitive-detector
```

### 3. 应用安全

```python
# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # 限制域名
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # 限制方法
    allow_headers=["*"],
)

# 请求限流
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/detect/text")
@limiter.limit("10/minute")
async def detect_text(request: Request, ...):
    pass
```

## 监控和告警

### 1. 系统监控

```bash
# 安装监控工具
sudo apt install htop iotop nethogs

# 创建监控脚本
cat > monitor.sh << 'EOF'
#!/bin/bash

echo "=== 系统资源使用情况 ==="
echo "CPU 使用率: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "内存使用率: $(free | grep Mem | awk '{printf("%.2f%%", $3/$2 * 100.0)}')"
echo "磁盘使用率: $(df -h / | awk 'NR==2{printf "%s", $5}')"

echo -e "\n=== Docker 容器状态 ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo -e "\n=== 服务健康检查 ==="
curl -s http://localhost:8000/health | jq '.status'
EOF

chmod +x monitor.sh
```

### 2. 日志监控

```bash
# 安装日志监控工具
sudo apt install logwatch

# 配置日志监控
sudo tee /etc/logwatch/conf/logwatch.conf > /dev/null <<EOF
LogDir = /var/log
TmpDir = /var/cache/logwatch
MailTo = admin@your-domain.com
MailFrom = logwatch@your-domain.com
Print = No
Save = /var/log/logwatch
Range = yesterday
Detail = High
Service = All
EOF
```

### 3. 告警配置

```bash
# 创建告警脚本
cat > alert.sh << 'EOF'
#!/bin/bash

# 检查服务状态
if ! curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "警告: 敏感词检测服务异常" | mail -s "服务告警" admin@your-domain.com
fi

# 检查磁盘空间
DISK_USAGE=$(df / | awk 'NR==2{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "警告: 磁盘使用率超过80%" | mail -s "磁盘告警" admin@your-domain.com
fi

# 检查内存使用
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
if [ $MEMORY_USAGE -gt 90 ]; then
    echo "警告: 内存使用率超过90%" | mail -s "内存告警" admin@your-domain.com
fi
EOF

chmod +x alert.sh

# 添加到 crontab
crontab -e
# 添加: */5 * * * * /opt/sensitive-detector/alert.sh
```

## 故障排除

### 1. 常见问题

**问题 1: 容器无法启动**
```bash
# 检查日志
docker compose logs sensitive-detector-backend

# 检查端口占用
netstat -tlnp | grep 8000

# 检查 Docker 服务
sudo systemctl status docker
```

**问题 2: Ollama 连接失败**
```bash
# 检查 Ollama 服务
ps aux | grep ollama
curl http://localhost:11434/api/tags

# 重启 Ollama
pkill ollama
ollama serve &
```

**问题 3: 内存不足**
```bash
# 检查内存使用
free -h
docker stats

# 清理内存
sync && echo 3 > /proc/sys/vm/drop_caches
```

### 2. 调试工具

```bash
# 安装调试工具
sudo apt install strace tcpdump

# 进程跟踪
strace -p $(pgrep -f "uvicorn")

# 网络抓包
tcpdump -i any port 8000

# 容器调试
docker exec -it sensitive-detector-prod /bin/bash
```

### 3. 性能分析

```bash
# 安装性能分析工具
sudo apt install perf-tools-unstable

# CPU 性能分析
perf top -p $(pgrep -f "uvicorn")

# 内存分析
perf mem record -p $(pgrep -f "uvicorn")
perf mem report
```

## 维护指南

### 1. 日常维护

```bash
# 创建维护脚本
cat > maintenance.sh << 'EOF'
#!/bin/bash

echo "开始日常维护..."

# 更新系统
sudo apt update && sudo apt upgrade -y

# 清理 Docker
docker system prune -f

# 清理日志
sudo journalctl --vacuum-time=7d

# 重启服务
docker compose -f docker-compose.prod.yml restart

echo "日常维护完成"
EOF

chmod +x maintenance.sh
```

### 2. 版本更新

```bash
# 创建更新脚本
cat > update.sh << 'EOF'
#!/bin/bash

set -e

echo "开始版本更新..."

# 备份当前版本
./backup.sh

# 拉取最新代码
git pull origin main

# 重新构建镜像
docker compose -f docker-compose.prod.yml build --no-cache

# 滚动更新
docker compose -f docker-compose.prod.yml up -d

# 等待服务启动
sleep 30

# 健康检查
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "版本更新成功!"
else
    echo "版本更新失败，回滚..."
    git reset --hard HEAD~1
    docker compose -f docker-compose.prod.yml up -d
fi
EOF

chmod +x update.sh
```

### 3. 数据备份

```bash
# 创建数据备份脚本
cat > data_backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/backups/data"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份敏感词库
cp /opt/sensitive-detector/backend/sensitive_words.txt $BACKUP_DIR/sensitive_words_$DATE.txt

# 备份日志
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz -C /opt/sensitive-detector logs/

# 清理旧备份
find $BACKUP_DIR -name "*.txt" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "数据备份完成: $BACKUP_DIR"
EOF

chmod +x data_backup.sh
```

---

**文档版本**: v1.0.0  
**最后更新**: 2024年1月1日
