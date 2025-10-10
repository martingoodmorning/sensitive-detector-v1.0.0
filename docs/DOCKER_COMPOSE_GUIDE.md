# Docker Compose 配置指南

## 概述

本项目提供了两个 Docker Compose 配置文件，分别用于不同的部署场景。

## 配置文件说明

### 1. docker-compose.yml (开发环境)

**用途**: 开发环境快速启动
**特点**:
- 简单的单服务配置
- 依赖外部 Ollama 服务
- 适合本地开发和测试
- 配置相对简单，启动快速

**适用场景**:
- 本地开发
- 快速测试
- 已有 Ollama 服务运行

**启动命令**:
```bash
docker compose up -d
```

### 2. docker-compose.prod.yml (生产环境)

**用途**: 生产环境完整部署
**特点**:
- 包含 Ollama 服务
- 完整的生产级配置
- 健康检查、资源限制、安全配置
- 网络隔离、只读文件系统
- 日志管理

**适用场景**:
- 生产环境部署
- 完整系统部署
- 需要 Ollama 服务

**启动命令**:
```bash
docker compose -f docker-compose.prod.yml up -d
```

## 配置对比

| 特性 | docker-compose.yml | docker-compose.prod.yml |
|------|-------------------|------------------------|
| Ollama 服务 | 外部依赖 | 内置服务 |
| 健康检查 | 无 | 有 |
| 资源限制 | 无 | 有 |
| 安全配置 | 基础 | 完整 |
| 网络隔离 | 无 | 有 |
| 日志管理 | 基础 | 完整 |
| 适用场景 | 开发/测试 | 生产环境 |

## 使用建议

### 开发环境
```bash
# 1. 启动外部 Ollama 服务
ollama serve

# 2. 下载模型
ollama pull qwen:7b

# 3. 启动应用
docker compose up -d
```

### 生产环境
```bash
# 1. 使用生产配置启动
docker compose -f docker-compose.prod.yml up -d

# 2. 等待模型下载完成
docker compose -f docker-compose.prod.yml logs -f ollama
```

## 环境变量配置

### 开发环境变量
```bash
# .env.dev
OLLAMA_BASE_URL=http://172.20.0.1:11434
OLLAMA_MODEL=qwen:7b
CORS_ALLOW_ORIGINS=*
PYTHONUNBUFFERED=1
```

### 生产环境变量
```bash
# .env.prod
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen:7b
CORS_ALLOW_ORIGINS=https://your-domain.com
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
```

## 故障排除

### 开发环境问题

**问题**: Ollama 连接失败
```bash
# 检查 Ollama 服务状态
ps aux | grep ollama

# 重启 Ollama 服务
pkill ollama
export OLLAMA_HOST=0.0.0.0:11434
ollama serve &
```

### 生产环境问题

**问题**: 容器启动失败
```bash
# 查看详细日志
docker compose -f docker-compose.prod.yml logs

# 检查资源使用
docker stats

# 重启服务
docker compose -f docker-compose.prod.yml restart
```

## 迁移指南

### 从开发环境迁移到生产环境

1. **备份数据**
   ```bash
   cp -r config backup/
   ```

2. **停止开发环境**
   ```bash
   docker compose down
   ```

3. **启动生产环境**
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

4. **验证服务**
   ```bash
   curl http://localhost:8000/health
   ```

---

**文档版本**: v1.0.0  
**最后更新**: 2025年10月
