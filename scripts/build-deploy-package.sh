#!/bin/bash

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 获取版本号
get_version() {
    if [ -f "VERSION" ]; then
        cat VERSION
    else
        echo "1.0.0"
    fi
}

# 创建部署包
create_deploy_package() {
    VERSION=$(get_version)
    PACKAGE_NAME="sensitive-detector-v${VERSION}"
    PACKAGE_DIR="./${PACKAGE_NAME}"
    
    log_step "创建部署包: ${PACKAGE_NAME}"
    
    # 清理旧包
    if [ -d "$PACKAGE_DIR" ]; then
        log_info "清理旧部署包..."
        rm -rf "$PACKAGE_DIR"
    fi
    
    # 创建目录结构
    log_info "创建目录结构..."
    mkdir -p ${PACKAGE_DIR}/{config,scripts,docs,examples}
    
    # 复制必要文件
    log_info "复制必要文件..."
    
    # 核心文件
    cp docker-compose.prod.yml ${PACKAGE_DIR}/docker-compose.yml
    cp install.sh ${PACKAGE_DIR}/
    chmod +x ${PACKAGE_DIR}/install.sh
    
    # 配置文件
    cp -r config.example ${PACKAGE_DIR}/examples/
    
    # 脚本文件
    cp scripts/*.sh ${PACKAGE_DIR}/scripts/
    chmod +x ${PACKAGE_DIR}/scripts/*.sh
    
    # 文档文件
    cp README.md ${PACKAGE_DIR}/docs/
    cp docs/*.md ${PACKAGE_DIR}/docs/ 2>/dev/null || true
    
    # 创建快速开始指南
    cat > ${PACKAGE_DIR}/QUICKSTART.md << 'EOF'
# 快速开始指南

## 一键安装

```bash
# 1. 解压部署包
tar -xzf sensitive-detector-v*.tar.gz
cd sensitive-detector-v*

# 2. 执行安装
chmod +x install.sh
./install.sh

# 3. 访问系统
# 浏览器打开: http://localhost:8000
```

## 手动安装

```bash
# 1. 启动 Ollama 服务
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
ollama pull qwen:7b

# 2. 启动应用
docker compose up -d

# 3. 访问系统
# 浏览器打开: http://localhost:8000
```

## 管理命令

```bash
# 查看日志
docker compose logs -f

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看状态
docker compose ps
```

## 故障排除

如果遇到问题，请查看：
- [故障排除文档](docs/TROUBLESHOOTING.md)
- [API 文档](docs/API.md)
- [部署指南](docs/DEPLOYMENT.md)
EOF

    # 创建版本信息文件
    cat > ${PACKAGE_DIR}/VERSION << EOF
${VERSION}
EOF

    # 创建变更日志
    cat > ${PACKAGE_DIR}/CHANGELOG.md << 'EOF'
# 变更日志

## v1.0.0 (2024-01-01)

### 新增功能
- 文本敏感词检测
- 文档敏感词检测 (TXT, PDF, DOCX)
- 规则匹配 + LLM 双重检测
- Web 界面
- Docker 容器化部署

### 技术特性
- FastAPI 后端
- Ollama LLM 集成
- 响应式前端界面
- 健康检查
- 日志记录

### 支持格式
- 文本输入
- TXT 文件
- PDF 文件
- DOCX 文件

### 系统要求
- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ 内存
- 20GB+ 磁盘空间
EOF

    # 创建许可证文件
    cat > ${PACKAGE_DIR}/LICENSE << 'EOF'
MIT License

Copyright (c) 2024 Sensitive Word Detection System

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

    # 创建压缩包
    log_info "创建压缩包..."
    tar -czf ${PACKAGE_NAME}.tar.gz ${PACKAGE_DIR}
    
    # 计算文件大小
    PACKAGE_SIZE=$(du -h ${PACKAGE_NAME}.tar.gz | cut -f1)
    
    log_info "部署包创建完成!"
    echo ""
    echo "=========================================="
    echo "           部署包信息"
    echo "=========================================="
    echo "包名: ${PACKAGE_NAME}.tar.gz"
    echo "大小: ${PACKAGE_SIZE}"
    echo "版本: ${VERSION}"
    echo ""
    echo "包含内容:"
    echo "  - 一键安装脚本"
    echo "  - Docker 配置文件"
    echo "  - 敏感词库示例"
    echo "  - 管理脚本"
    echo "  - 完整文档"
    echo ""
    echo "使用方法:"
    echo "  1. tar -xzf ${PACKAGE_NAME}.tar.gz"
    echo "  2. cd ${PACKAGE_NAME}"
    echo "  3. ./install.sh"
    echo ""
}

# 验证部署包
verify_package() {
    PACKAGE_NAME="sensitive-detector-v$(get_version)"
    
    log_step "验证部署包..."
    
    if [ ! -f "${PACKAGE_NAME}.tar.gz" ]; then
        log_error "部署包不存在: ${PACKAGE_NAME}.tar.gz"
        exit 1
    fi
    
    # 解压验证
    log_info "解压验证..."
    tar -tzf ${PACKAGE_NAME}.tar.gz > /dev/null
    
    if [ $? -eq 0 ]; then
        log_info "部署包验证通过"
    else
        log_error "部署包验证失败"
        exit 1
    fi
    
    # 检查关键文件
    log_info "检查关键文件..."
    tar -tzf ${PACKAGE_NAME}.tar.gz | grep -q "install.sh"
    tar -tzf ${PACKAGE_NAME}.tar.gz | grep -q "docker-compose.yml"
    tar -tzf ${PACKAGE_NAME}.tar.gz | grep -q "scripts/"
    tar -tzf ${PACKAGE_NAME}.tar.gz | grep -q "docs/"
    
    log_info "关键文件检查通过"
}

# 清理临时文件
cleanup() {
    VERSION=$(get_version)
    PACKAGE_NAME="sensitive-detector-v${VERSION}"
    PACKAGE_DIR="./${PACKAGE_NAME}"
    
    log_info "清理临时文件..."
    
    if [ -d "$PACKAGE_DIR" ]; then
        rm -rf "$PACKAGE_DIR"
        log_info "临时目录已清理"
    fi
}

# 显示帮助信息
show_help() {
    echo "敏感词检测系统部署包构建脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo "  -v, --version  显示版本信息"
    echo "  -c, --clean    清理临时文件"
    echo ""
    echo "示例:"
    echo "  $0             构建部署包"
    echo "  $0 --clean     清理临时文件"
    echo "  $0 --help      显示帮助信息"
}

# 主函数
main() {
    case "${1:-}" in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--version)
            echo "版本: $(get_version)"
            exit 0
            ;;
        -c|--clean)
            cleanup
            exit 0
            ;;
        "")
            create_deploy_package
            verify_package
            cleanup
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
