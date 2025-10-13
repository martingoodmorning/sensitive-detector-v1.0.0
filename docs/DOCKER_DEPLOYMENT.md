# Docker 部署指南

## 📋 概述

本文档介绍如何使用 Docker 部署敏感词检测系统。推荐直接克隆项目进行部署，简单高效。

## 🚀 快速部署

### 1. 克隆项目

```bash
# 克隆项目
git clone https://github.com/martingoodmorning/sensitive-detector-v1.0.0.git
cd sensitive-detector
```

### 2. 启动服务

```bash
# 启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps
```

### 3. 访问系统

- **前端界面**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 🐳 Docker 配置说明

### docker-compose.yml 配置

```yaml
services:
  sensitive-detector-backend:
    build: ./backend
    container_name: sensitive-detector
    network_mode: host  # 使用host网络模式，确保Ollama连接稳定
    volumes:
      - ./frontend:/app/frontend
      - ./word_libraries:/app/word_libraries
      - ./detection_config.json:/app/detection_config.json
    environment:
      - PYTHONUNBUFFERED=1
      - OLLAMA_BASE_URL=http://localhost:11434
      - OLLAMA_MODEL=qwen2.5:7b-instruct-q4_K_M
      - CORS_ALLOW_ORIGINS=*
    restart: unless-stopped
```

### 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OLLAMA_BASE_URL` | Ollama服务地址（Host模式） | `http://localhost:11434` |
| `OLLAMA_MODEL` | 使用的模型 | `qwen2.5:7b-instruct-q4_K_M` |
| `CORS_ALLOW_ORIGINS` | 跨域设置 | `*` |

### 网络配置说明

#### Host模式（默认推荐）

**配置特点**：
- 容器直接使用宿主机网络栈
- Ollama服务地址为 `localhost:11434`
- 前端访问地址仍为 `http://localhost:8000`

**优势**：
- ✅ Ollama连接稳定可靠
- ✅ 网络配置简单
- ✅ 适合本地开发环境

**注意事项**：
- ⚠️ 容器直接使用宿主机网络
- ⚠️ 适合开发环境，生产环境需谨慎

#### Bridge模式（可选）

如需使用Bridge模式，请修改配置：

```yaml
services:
  sensitive-detector-backend:
    build: ./backend
    container_name: sensitive-detector
    ports:
      - "8000:8000"  # 恢复端口映射
    volumes:
      - ./frontend:/app/frontend
      - ./word_libraries:/app/word_libraries
      - ./detection_config.json:/app/detection_config.json
    environment:
      - PYTHONUNBUFFERED=1
      - OLLAMA_BASE_URL=http://172.17.0.1:11434  # 使用Docker网关IP
      - OLLAMA_MODEL=qwen2.5:7b-instruct-q4_K_M
      - CORS_ALLOW_ORIGINS=*
    restart: unless-stopped
```

**优势**：
- ✅ 网络隔离性好
- ✅ 适合生产环境
- ✅ 安全性更高

**注意事项**：
- ⚠️ 需要确保Ollama服务可被Docker网关访问
- ⚠️ 可能需要额外的网络配置

## 🔧 系统依赖

### Dockerfile 依赖

```dockerfile
# 系统依赖 (容器内自动安装)
RUN apt-get update && apt-get install -y \
    antiword \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-eng \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*
```

### 工具说明

- **antiword**: DOC文件解析工具
- **Tesseract OCR**: 图片OCR识别引擎
- **语言包**: 中文简体 + 英文支持

## 📁 目录结构

```
sensitive-detector/
├── backend/                 # 后端代码
│   ├── Dockerfile          # 后端镜像构建文件
│   ├── main.py            # 主程序
│   └── requirements.txt   # Python依赖
├── frontend/               # 前端代码
│   ├── index.html         # 主页面
│   ├── script.js          # 前端逻辑
│   └── style.css          # 样式文件
├── word_libraries/         # 敏感词库目录
│   ├── 01零时-Tencent.txt
│   ├── 02网易前端过滤敏感词库.txt
│   └── ... (17个专业词库)
├── detection_config.json   # 检测配置
└── docker-compose.yml      # Docker编排文件
```

## ⚙️ 配置说明

### 敏感词库配置

```bash
# 查看可用的敏感词库
ls word_libraries/

# 编辑特定敏感词库
vim word_libraries/默认词库.txt

# 重启服务使配置生效
docker compose restart sensitive-detector-backend
```

### 检测配置

编辑 `detection_config.json`:

```json
{
  "default_word_library": "默认词库",
  "available_word_libraries": [
    "默认词库",
    "01零时-Tencent",
    "02网易前端过滤敏感词库",
    "03非法网址",
    "04GFW中国国家防火墙补充词库",
    "COVID-19词库",
    "其他词库",
    "反动词库",
    "广告类型",
    "政治类型",
    "新思想启蒙",
    "暴恐词库",
    "民生词库",
    "涉枪涉爆",
    "色情类型",
    "色情词库",
    "补充词库",
    "贪腐词库"
  ]
}
```

## 🔍 功能验证

### 1. 基础功能测试

```bash
# 检查服务状态
docker compose ps

# 查看日志
docker compose logs sensitive-detector-backend

# 测试API
curl http://localhost:8000/health
```

### 2. 文档格式支持

- **TXT**: 纯文本文件
- **PDF**: PDF文档 (PyPDF2)
- **DOCX**: Word文档 (python-docx)
- **DOC**: Word文档 (antiword)
- **图片**: JPG/PNG/BMP/GIF/TIFF (Tesseract OCR)

### 3. 检测模式

- **默认模式**: 规则匹配快速筛选 + 存疑内容大模型检测
- **严格模式**: 直接使用大模型检测

## 🛠️ 管理命令

### 服务管理

```bash
# 启动服务
docker compose up -d

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看日志
docker compose logs -f sensitive-detector-backend

# 进入容器
docker compose exec sensitive-detector-backend bash
```

### 工具检查

```bash
# 检查antiword
docker compose exec sensitive-detector-backend antiword

# 检查tesseract
docker compose exec sensitive-detector-backend tesseract --version

# 检查语言包
docker compose exec sensitive-detector-backend tesseract --list-langs
```

## 🔧 故障排除

### 常见问题

#### 1. DOC文件解析失败

```bash
# 检查antiword是否安装
docker compose exec sensitive-detector-backend which antiword

# 重新构建镜像
docker compose build --no-cache sensitive-detector-backend
```

#### 2. OCR功能无法使用

```bash
# 检查tesseract
docker compose exec sensitive-detector-backend tesseract --version

# 检查语言包
docker compose exec sensitive-detector-backend tesseract --list-langs
```

#### 3. 大模型检测功能异常

**Host模式（推荐）**：
```bash
# 检查Ollama服务是否运行
curl http://localhost:11434/api/tags

# 检查模型是否加载
curl http://localhost:11434/api/show -d '{"name": "qwen2.5:7b-instruct-q4_K_M"}'

# 检查容器日志
docker compose logs sensitive-detector-backend | grep "Ollama"
```

**Bridge模式**：
```bash
# 检查Docker网关IP
docker network inspect bridge | grep Gateway

# 检查Ollama连接
curl http://172.17.0.1:11434/api/tags

# 如果连接失败，尝试其他网关IP
curl http://172.20.0.1:11434/api/tags
```

**常见解决方案**：
1. **确保Ollama服务运行**：`ollama serve`
2. **检查网络配置**：确认OLLAMA_BASE_URL设置正确
3. **重启服务**：`docker compose restart`

### 日志分析

```bash
# 查看详细日志
docker compose logs -f sensitive-detector-backend

# 查看特定时间日志
docker compose logs --since="2024-01-01T00:00:00" sensitive-detector-backend
```

## 📊 性能优化

### 资源要求

- **内存**: 8GB+ (运行qwen2.5:7b量化模型)
- **CPU**: 4核心+
- **存储**: 10GB+ (包含模型文件)

### 优化建议

1. **模型优化**: 使用量化模型减少内存占用
2. **缓存策略**: 启用检测结果缓存
3. **并发控制**: 限制同时检测的请求数量
4. **资源监控**: 监控CPU和内存使用情况

## 🔒 安全考虑

### 生产环境配置

```yaml
# 生产环境安全配置
services:
  sensitive-detector-backend:
    # ... 其他配置
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
```

### 数据安全

```bash
# 备份敏感词库目录
cp -r word_libraries backup/word_libraries_$(date +%Y%m%d)

# 设置文件权限
chmod -R 600 word_libraries/
chown -R root:root word_libraries/
```

## 📈 监控和维护

### 健康检查

```bash
# API健康检查
curl http://localhost:8000/health

# 服务状态检查
docker compose ps
```

### 备份策略

```bash
# 创建备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backup/${DATE}"

mkdir -p ${BACKUP_DIR}

# 备份敏感词库
tar -czf ${BACKUP_DIR}/word_libraries_${DATE}.tar.gz word_libraries/

# 备份配置文件
cp detection_config.json ${BACKUP_DIR}/detection_config_${DATE}.json

echo "备份完成: ${BACKUP_DIR}"
EOF

chmod +x backup.sh
```

## 🎯 总结

通过Docker部署敏感词检测系统具有以下优势：

- **简单部署**: 一键启动所有服务
- **环境隔离**: 容器化运行，避免环境冲突
- **易于维护**: 统一的配置管理
- **快速扩展**: 支持水平扩展
- **版本管理**: 通过Git管理代码版本

推荐使用 `git clone` + `docker compose up -d` 的方式进行部署