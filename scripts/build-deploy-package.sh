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
