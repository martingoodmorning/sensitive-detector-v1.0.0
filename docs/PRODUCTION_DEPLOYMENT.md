# 生产环境部署指南

## 🎯 概述

本文档详细说明敏感词检测系统在生产环境中的部署流程，包括容器化部署、服务配置、监控维护等内容。

## 🏗️ 架构设计

### 服务架构

```
┌─────────────────┐    ┌─────────────────┐
│   Ollama 容器    │    │   应用容器       │
│   ollama-service│────│sensitive-detector│
│   ~1GB 镜像     │    │   ~500MB 镜像   │
│   8GB 内存限制   │    │   2GB 内存限制   │
│   4 核心 CPU    │    │   1 核心 CPU    │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────────────────┼─────────────────┐
                                 │                 │
                    ┌─────────────────┐    ┌─────────────────┐
                    │   模型数据       │    │   配置文件       │
                    │   Volumes       │    │   Volumes       │
                    │   ~4GB          │    │   ~几MB         │
                    └─────────────────┘    └─────────────────┘
```

### 技术栈

- **容器化**: Docker + Docker Compose
- **AI 服务**: Ollama + Qwen2.5:7b-instruct-q4_K_M
- **应用服务**: FastAPI + Uvicorn
- **数据存储**: Docker Volumes
- **网络**: Bridge 网络模式

## 🚀 部署流程

### 1. 环境准备

#### 系统要求

- **操作系统**: Linux (Ubuntu 20.04+ 推荐)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **内存**: 8GB+ (推荐 16GB)
- **磁盘**: 20GB+ 可用空间
- **CPU**: 4 核心+ (推荐 8 核心)

#### 依赖安装

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose-plugin

# CentOS/RHEL
sudo yum install docker docker-compose-plugin

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 添加用户到 docker 组
sudo usermod -aG docker $USER
```

### 2. 项目部署

#### 克隆项目

```bash
git clone https://github.com/martingoodmorning/sensitive-detector-v1.0.0.git
cd sensitive-detector
```

#### 启动服务

```bash
# 一键启动所有服务
docker-compose up -d

# 查看启动状态
docker-compose ps
```

### 3. 服务验证

#### 健康检查

```bash
# 检查应用服务
curl http://localhost:8000/health

# 检查 Ollama 服务
curl http://localhost:11434/api/tags

# 检查 Web 界面
curl http://localhost:8000
```

#### 模型验证

```bash
# 查看已下载的模型
docker-compose exec ollama ollama list

# 测试模型响应
docker-compose exec ollama ollama run qwen2.5:7b-instruct-q4_K_M "你好"
```

## ⚙️ 配置管理

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama 服务地址 |
| `OLLAMA_MODEL` | `qwen2.5:7b-instruct-q4_K_M` | 使用的模型 |
| `CORS_ALLOW_ORIGINS` | `*` | CORS 配置 |
| `HEALTH_CHECK_ENABLED` | `true` | 健康检查开关 |

### 资源配置

#### Ollama 服务资源

```yaml
deploy:
  resources:
    limits:
      memory: 8G      # 最大内存
      cpus: '4.0'     # 最大CPU
    reservations:
      memory: 4G      # 预留内存
      cpus: '2.0'     # 预留CPU
```

#### 应用服务资源

```yaml
deploy:
  resources:
    limits:
      memory: 2G      # 最大内存
      cpus: '1.0'     # 最大CPU
    reservations:
      memory: 1G      # 预留内存
      cpus: '0.5'     # 预留CPU
```

### 网络配置

```yaml
ports:
  - "8000:8000"   # 应用服务端口
  - "11434:11434" # Ollama 服务端口（可选）
```

## 📊 监控运维

### 服务监控

#### 状态检查

```bash
# 查看服务状态
docker-compose ps

# 查看资源使用
docker stats

# 查看健康状态
docker inspect ollama-service | grep Health
docker inspect sensitive-detector | grep Health
```

#### 日志管理

```bash
# 查看实时日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f ollama
docker-compose logs -f sensitive-detector

# 查看错误日志
docker-compose logs | grep ERROR
```

### 性能监控

#### 关键指标

- **API 响应时间**: 正常 < 100ms，LLM 检测 < 500ms
- **内存使用**: Ollama < 6GB，应用 < 1GB
- **CPU 使用**: Ollama < 80%，应用 < 50%
- **磁盘使用**: 模型数据 < 5GB

#### 监控命令

```bash
# 内存使用
free -h

# 磁盘使用
df -h

# 网络连接
netstat -tlnp | grep -E "(8000|11434)"

# 进程监控
ps aux | grep -E "(ollama|uvicorn)"
```

### 数据备份

#### 模型数据备份

```bash
# 备份模型数据
tar -czf ollama-backup-$(date +%Y%m%d).tar.gz ./data/ollama/

# 恢复模型数据
tar -xzf ollama-backup-20250101.tar.gz
```

#### 配置文件备份

```bash
# 备份配置文件
cp detection_config.json detection_config.json.backup
cp docker-compose.yml docker-compose.yml.backup
```

## 🔧 故障排除

### 常见问题

#### 1. 容器启动失败

**症状**: 容器状态为 `Exited` 或 `Restarting`

**排查步骤**:
```bash
# 检查容器状态
docker-compose ps

# 查看错误日志
docker-compose logs ollama
docker-compose logs sensitive-detector

# 检查资源使用
docker stats
```

**解决方案**:
- 检查内存是否充足
- 检查端口是否被占用
- 检查 Docker 服务状态

#### 2. 模型下载失败

**症状**: 日志显示模型下载错误

**排查步骤**:
```bash
# 检查网络连接
docker-compose exec ollama curl -I https://ollama.ai

# 检查磁盘空间
df -h

# 手动下载模型
docker-compose exec ollama ollama pull qwen2.5:7b-instruct-q4_K_M
```

**解决方案**:
- 检查网络连接
- 确保磁盘空间充足
- 重启 Ollama 服务

#### 3. 健康检查失败

**症状**: 服务状态显示 `unhealthy`

**排查步骤**:
```bash
# 检查服务端口
curl http://localhost:8000/health
curl http://localhost:11434/api/tags

# 检查容器内部
docker-compose exec ollama ollama list
docker-compose exec sensitive-detector curl http://ollama:11434/api/tags
```

**解决方案**:
- 重启相关服务
- 检查服务依赖关系
- 验证网络连接

#### 4. 性能问题

**症状**: API 响应缓慢或超时

**排查步骤**:
```bash
# 检查资源使用
docker stats

# 检查日志中的响应时间
docker-compose logs sensitive-detector | grep "响应时间"

# 检查模型状态
docker-compose exec ollama ollama list
```

**解决方案**:
- 调整资源限制
- 优化模型配置
- 检查系统负载

### 应急处理

#### 服务重启

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart ollama
docker-compose restart sensitive-detector
```

#### 服务停止

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据
docker-compose down -v
```

#### 数据恢复

```bash
# 恢复模型数据
tar -xzf ollama-backup-20250101.tar.gz

# 重启服务
docker-compose up -d
```

## 🔄 更新升级

### 应用更新

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose build

# 重启服务
docker-compose up -d
```

### 模型更新

```bash
# 下载新模型
docker-compose exec ollama ollama pull qwen2.5:3b-instruct-q4_K_M

# 更新环境变量
# 编辑 docker-compose.yml 中的 OLLAMA_MODEL

# 重启服务
docker-compose restart sensitive-detector
```

## 📈 性能优化

### 模型优化

1. **模型选择**
   - 生产环境：`qwen2.5:7b-instruct-q4_K_M` (4.1GB)
   - 开发测试：`qwen2.5:3b-instruct-q4_K_M` (1.9GB)
   - 资源受限：`qwen2.5:1.5b-instruct-q4_K_M` (0.9GB)

2. **预热策略**
   - 启动时自动预热
   - 定期保持模型活跃
   - 优化预热参数

### 系统优化

1. **资源调优**
   - 根据服务器配置调整资源限制
   - 监控资源使用情况
   - 优化内存分配

2. **网络优化**
   - 使用内部网络通信
   - 优化端口配置
   - 启用连接池

## 🔒 安全配置

### 网络安全

```yaml
# 限制外部访问
ports:
  - "127.0.0.1:8000:8000"  # 仅本地访问
  # - "11434:11434"        # 不暴露 Ollama 端口
```

### 数据安全

```bash
# 设置数据目录权限
chmod 700 ./data/ollama

# 定期备份数据
crontab -e
# 添加: 0 2 * * * tar -czf /backup/ollama-$(date +\%Y\%m\%d).tar.gz /path/to/data/ollama
```

## 📋 检查清单

### 部署前检查

- [ ] 系统资源充足（内存 8GB+，磁盘 20GB+）
- [ ] Docker 和 Docker Compose 已安装
- [ ] 网络端口 8000 和 11434 可用
- [ ] 项目代码已克隆
- [ ] 数据目录已创建

### 部署后检查

- [ ] 所有容器状态为 `Up` 和 `healthy`
- [ ] 应用服务可访问 (http://localhost:8000)
- [ ] 健康检查通过 (http://localhost:8000/health)
- [ ] 模型已下载并可用
- [ ] 日志无错误信息

### 运行中检查

- [ ] 服务响应时间正常
- [ ] 资源使用在合理范围内
- [ ] 日志文件正常轮转
- [ ] 备份任务正常执行
- [ ] 监控告警正常

## 📞 技术支持

如遇到问题，请提供以下信息：

1. **系统信息**: 操作系统版本、Docker 版本
2. **错误日志**: `docker-compose logs` 输出
3. **服务状态**: `docker-compose ps` 输出
4. **资源使用**: `docker stats` 输出
5. **网络状态**: `netstat -tlnp` 输出

---

**最后更新**: 2025年10月
**版本**: v1.0.0
