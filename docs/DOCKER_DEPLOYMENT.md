# Docker 打包移植与快速部署指南

## 概述

本文档详细说明如何使用 Docker 进行敏感词检测系统的打包移植，以及如何让其他用户快速部署该系统。

## 🐳 Docker 打包策略

### 1. 多阶段构建优化

**后端 Dockerfile 优化**:
```dockerfile
# 构建阶段
FROM python:3.10-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
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
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 镜像优化技巧

**减小镜像大小**:
```dockerfile
# 使用 Alpine 基础镜像
FROM python:3.10-alpine as builder

# 安装构建依赖
RUN apk add --no-cache gcc musl-dev

# 清理缓存
RUN pip install --no-cache-dir -r requirements.txt && \
    pip cache purge

# 运行阶段使用更小的基础镜像
FROM python:3.10-alpine

# 只安装运行时依赖
RUN apk add --no-cache curl

# 复制必要的文件
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

# 设置用户
RUN adduser -D -s /bin/sh appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. 构建脚本

**build.sh**:
```bash
#!/bin/bash

set -e

echo "开始构建敏感词检测系统镜像..."

# 设置变量
IMAGE_NAME="sensitive-detector"
TAG="latest"
REGISTRY="your-registry.com"

# 构建后端镜像
echo "构建后端镜像..."
docker build -t ${IMAGE_NAME}-backend:${TAG} ./backend

# 构建前端镜像（如果需要）
echo "构建前端镜像..."
docker build -t ${IMAGE_NAME}-frontend:${TAG} ./frontend

# 标记镜像
docker tag ${IMAGE_NAME}-backend:${TAG} ${REGISTRY}/${IMAGE_NAME}-backend:${TAG}
docker tag ${IMAGE_NAME}-frontend:${TAG} ${REGISTRY}/${IMAGE_NAME}-frontend:${TAG}

# 推送到镜像仓库
echo "推送镜像到仓库..."
docker push ${REGISTRY}/${IMAGE_NAME}-backend:${TAG}
docker push ${REGISTRY}/${IMAGE_NAME}-frontend:${TAG}

echo "镜像构建和推送完成!"
echo "后端镜像: ${REGISTRY}/${IMAGE_NAME}-backend:${TAG}"
echo "前端镜像: ${REGISTRY}/${IMAGE_NAME}-frontend:${TAG}"
```

## 📦 打包移植方案

### 1. 完整系统打包

**docker-compose.prod.yml**:
```yaml
version: '3.8'

services:
  sensitive-detector-backend:
    image: your-registry.com/sensitive-detector-backend:latest
    container_name: sensitive-detector-prod
    ports:
      - "8000:8000"
    volumes:
      - ./config/sensitive_words.txt:/app/sensitive_words.txt:ro
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_MODEL=qwen:7b
      - CORS_ALLOW_ORIGINS=*
      - LOG_LEVEL=INFO
    depends_on:
      - ollama
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - app-network

  ollama:
    image: ollama/ollama:latest
    container_name: ollama-service
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    restart: unless-stopped
    networks:
      - app-network

volumes:
  ollama_data:

networks:
  app-network:
    driver: bridge
```

### 2. 部署包结构

**部署包目录结构**:
```
sensitive-detector-deploy/
├── docker-compose.yml          # 生产环境配置
├── docker-compose.dev.yml      # 开发环境配置
├── config/
│   ├── sensitive_words.txt     # 敏感词库
│   └── nginx.conf             # Nginx 配置
├── scripts/
│   ├── deploy.sh              # 部署脚本
│   ├── backup.sh              # 备份脚本
│   └── update.sh              # 更新脚本
├── docs/
│   ├── README.md              # 部署说明
│   ├── INSTALL.md             # 安装指南
│   └── TROUBLESHOOTING.md     # 故障排除
└── examples/
    ├── docker-compose.example.yml
    └── config.example/
```

### 3. 一键部署脚本

**deploy.sh**:
```bash
#!/bin/bash

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    # 检查 Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    # 检查内存
    MEMORY_GB=$(free -g | awk 'NR==2{print $2}')
    if [ $MEMORY_GB -lt 8 ]; then
        log_warn "系统内存不足 8GB，可能影响 LLM 性能"
    fi
    
    log_info "系统要求检查通过"
}

# 下载模型
download_model() {
    log_info "下载 qwen:7b 模型..."
    
    # 启动 Ollama 服务
    docker compose up -d ollama
    
    # 等待服务启动
    sleep 10
    
    # 下载模型
    docker compose exec ollama ollama pull qwen:7b
    
    log_info "模型下载完成"
}

# 部署应用
deploy_app() {
    log_info "部署敏感词检测系统..."
    
    # 创建必要的目录
    mkdir -p logs config
    
    # 复制配置文件
    if [ ! -f config/sensitive_words.txt ]; then
        cp config.example/sensitive_words.txt config/
        log_info "已创建默认敏感词库"
    fi
    
    # 启动服务
    docker compose up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 健康检查
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_info "服务启动成功!"
    else
        log_error "服务启动失败，请检查日志"
        docker compose logs
        exit 1
    fi
}

# 显示访问信息
show_access_info() {
    log_info "部署完成!"
    echo ""
    echo "访问信息:"
    echo "  前端界面: http://localhost:8000"
    echo "  API 文档: http://localhost:8000/api/docs"
    echo "  健康检查: http://localhost:8000/health"
    echo ""
    echo "管理命令:"
    echo "  查看日志: docker compose logs -f"
    echo "  停止服务: docker compose down"
    echo "  重启服务: docker compose restart"
    echo ""
}

# 主函数
main() {
    log_info "开始部署敏感词检测系统..."
    
    check_requirements
    download_model
    deploy_app
    show_access_info
    
    log_info "部署完成!"
}

# 执行主函数
main "$@"
```

## 🚀 快速部署指南

### 1. 部署包准备

**创建部署包**:
```bash
#!/bin/bash
# create-deploy-package.sh

PACKAGE_NAME="sensitive-detector-v1.0.0"
PACKAGE_DIR="./${PACKAGE_NAME}"

echo "创建部署包: ${PACKAGE_NAME}"

# 创建目录结构
mkdir -p ${PACKAGE_DIR}/{config,scripts,docs,examples}

# 复制必要文件
cp docker-compose.yml ${PACKAGE_DIR}/
cp docker-compose.prod.yml ${PACKAGE_DIR}/
cp -r config.example ${PACKAGE_DIR}/examples/
cp scripts/*.sh ${PACKAGE_DIR}/scripts/
cp docs/*.md ${PACKAGE_DIR}/docs/

# 创建安装脚本
cat > ${PACKAGE_DIR}/install.sh << 'EOF'
#!/bin/bash
set -e

echo "敏感词检测系统安装程序"
echo "=========================="

# 检查系统要求
if ! command -v docker &> /dev/null; then
    echo "错误: 请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "错误: 请先安装 Docker Compose"
    exit 1
fi

# 执行部署
chmod +x scripts/*.sh
./scripts/deploy.sh

echo "安装完成!"
EOF

chmod +x ${PACKAGE_DIR}/install.sh

# 创建压缩包
tar -czf ${PACKAGE_NAME}.tar.gz ${PACKAGE_DIR}

echo "部署包创建完成: ${PACKAGE_NAME}.tar.gz"
```

### 2. 用户部署步骤

**用户部署流程**:
```bash
# 1. 下载部署包
wget https://gitee.com/saisai5203/sensitive-detector/releases/download/v1.0.0/sensitive-detector-v1.0.0.tar.gz

# 2. 解压部署包
tar -xzf sensitive-detector-v1.0.0.tar.gz
cd sensitive-detector-v1.0.0

# 3. 一键安装
chmod +x install.sh
./install.sh

# 4. 访问系统
# 浏览器打开: http://localhost:8000
```

### 3. 配置说明

**环境变量配置**:
```bash
# .env 文件
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen:7b
CORS_ALLOW_ORIGINS=*
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1

# 生产环境配置
# OLLAMA_BASE_URL=http://your-ollama-server:11434
# CORS_ALLOW_ORIGINS=https://your-domain.com
```

**敏感词库配置**:
```bash
# 编辑敏感词库
vim config/sensitive_words.txt

# 重启服务使配置生效
docker compose restart sensitive-detector-backend
```

## ⚠️ 部署注意事项

### 1. 系统要求

**硬件要求**:
- **CPU**: 4核以上 (推荐 8核)
- **内存**: 8GB 以上 (推荐 16GB)
- **存储**: 20GB 以上可用空间
- **网络**: 稳定的网络连接

**软件要求**:
- **操作系统**: Linux (Ubuntu 20.04+, CentOS 8+)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.10+ (本地开发)

### 2. 网络配置

**端口要求**:
```bash
# 必需端口
8000/tcp  # 应用服务端口
11434/tcp # Ollama 服务端口

# 可选端口
80/tcp    # HTTP (Nginx)
443/tcp   # HTTPS (Nginx)
```

**防火墙配置**:
```bash
# Ubuntu/Debian
sudo ufw allow 8000/tcp
sudo ufw allow 11434/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=11434/tcp
sudo firewall-cmd --reload
```

### 3. 安全考虑

**生产环境安全**:
```yaml
# docker-compose.prod.yml
services:
  sensitive-detector-backend:
    # ... 其他配置
    environment:
      - CORS_ALLOW_ORIGINS=https://your-domain.com
      - LOG_LEVEL=WARNING
    # 资源限制
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
    # 安全配置
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
```

**数据安全**:
```bash
# 备份敏感词库
cp config/sensitive_words.txt backup/sensitive_words_$(date +%Y%m%d).txt

# 设置文件权限
chmod 600 config/sensitive_words.txt
chown root:root config/sensitive_words.txt
```

### 4. 性能优化

**Docker 优化**:
```yaml
# docker-compose.yml
services:
  sensitive-detector-backend:
    # ... 其他配置
    # 性能优化
    ulimits:
      nofile:
        soft: 65535
        hard: 65535
    # 内存优化
    mem_limit: 2g
    memswap_limit: 2g
    # CPU 优化
    cpus: '1.0'
```

**系统优化**:
```bash
# 内核参数优化
echo 'vm.max_map_count=262144' | sudo tee -a /etc/sysctl.conf
echo 'net.core.somaxconn=65535' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# 文件描述符限制
echo '* soft nofile 65535' | sudo tee -a /etc/security/limits.conf
echo '* hard nofile 65535' | sudo tee -a /etc/security/limits.conf
```

### 5. 监控和维护

**健康检查**:
```bash
# 服务状态检查
docker compose ps

# 健康检查
curl http://localhost:8000/health

# 日志查看
docker compose logs -f sensitive-detector-backend
```

**性能监控**:
```bash
# 资源使用情况
docker stats

# 磁盘使用情况
df -h

# 内存使用情况
free -h
```

**备份策略**:
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/opt/backups/sensitive-detector"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份配置文件
tar -czf $BACKUP_DIR/config_$DATE.tar.gz config/

# 备份日志
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs/

# 备份敏感词库
cp config/sensitive_words.txt $BACKUP_DIR/sensitive_words_$DATE.txt

# 清理旧备份 (保留30天)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.txt" -mtime +30 -delete

echo "备份完成: $BACKUP_DIR"
```

## 🔧 故障排除

### 1. 常见问题

**问题 1: 容器启动失败**
```bash
# 检查日志
docker compose logs sensitive-detector-backend

# 检查端口占用
netstat -tlnp | grep 8000

# 重新构建
docker compose down
docker compose build --no-cache
docker compose up -d
```

**问题 2: Ollama 连接失败**
```bash
# 检查 Ollama 服务
docker compose logs ollama

# 重启 Ollama
docker compose restart ollama

# 检查网络连接
docker compose exec sensitive-detector-backend curl http://ollama:11434/api/tags
```

**问题 3: 内存不足**
```bash
# 检查内存使用
free -h
docker stats

# 清理内存
sync && echo 3 > /proc/sys/vm/drop_caches

# 重启服务
docker compose restart
```

### 2. 调试工具

**调试脚本**:
```bash
#!/bin/bash
# debug.sh

echo "敏感词检测系统调试信息"
echo "========================"

echo "1. 系统信息:"
uname -a
free -h
df -h

echo "2. Docker 信息:"
docker version
docker compose version

echo "3. 容器状态:"
docker compose ps

echo "4. 服务健康检查:"
curl -s http://localhost:8000/health | jq .

echo "5. 网络连接测试:"
docker compose exec sensitive-detector-backend curl -s http://ollama:11434/api/tags

echo "6. 日志信息:"
docker compose logs --tail=20 sensitive-detector-backend
```

## 📋 部署检查清单

### 部署前检查
- [ ] 系统要求满足 (CPU、内存、存储)
- [ ] Docker 和 Docker Compose 已安装
- [ ] 网络端口已开放
- [ ] 防火墙配置正确
- [ ] 部署包已下载并解压

### 部署过程检查
- [ ] 环境变量配置正确
- [ ] 敏感词库文件存在
- [ ] Ollama 服务启动成功
- [ ] 模型下载完成
- [ ] 应用服务启动成功
- [ ] 健康检查通过

### 部署后检查
- [ ] 前端界面可访问
- [ ] API 接口正常
- [ ] 文本检测功能正常
- [ ] 文档检测功能正常
- [ ] 日志输出正常
- [ ] 性能指标正常

## 📞 技术支持

### 联系方式
- **文档**: [项目文档地址]
- **Issues**: [Gitee Issues]
- **邮箱**: support@example.com

### 常见问题
- 查看 [故障排除文档](TROUBLESHOOTING.md)
- 查看 [FAQ 文档](FAQ.md)
- 提交 [Gitee Issue](https://gitee.com/saisai5203/sensitive-detector/issues)

---

**文档版本**: v1.0.0  
**最后更新**: 2025年10月
