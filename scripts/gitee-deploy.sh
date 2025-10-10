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

# 配置变量
GITEE_USERNAME="saisai5203"
REPO_NAME="sensitive-detector-v1.0.0"
VERSION="1.0.0"
PACKAGE_NAME="sensitive-detector-v${VERSION}"
GITEE_URL="https://gitee.com/${GITEE_USERNAME}/${REPO_NAME}"

# 显示欢迎信息
show_welcome() {
    echo "=========================================="
    echo "    敏感词检测系统 Gitee 部署脚本"
    echo "    Sensitive Word Detection System"
    echo "=========================================="
    echo ""
    echo "本脚本将帮助您从 Gitee 快速部署敏感词检测系统"
    echo ""
}

# 检查网络连接
check_network() {
    log_step "检查网络连接..."
    
    # 检查基本网络连接
    if ping -c 3 8.8.8.8 > /dev/null 2>&1; then
        log_info "基本网络连接正常"
    else
        log_error "基本网络连接失败"
        exit 1
    fi
    
    # 检查 Gitee 连接
    if curl -s https://gitee.com > /dev/null 2>&1; then
        log_info "Gitee 连接正常"
    else
        log_warn "Gitee 连接异常，尝试使用备用方案"
    fi
}

# 配置国内镜像源
setup_mirrors() {
    log_step "配置国内镜像源..."
    
    # 配置 Docker 镜像加速器
    if [ ! -f /etc/docker/daemon.json ]; then
        log_info "配置 Docker 镜像加速器..."
        sudo mkdir -p /etc/docker
        sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
EOF
        sudo systemctl daemon-reload
        sudo systemctl restart docker
        log_info "Docker 镜像加速器配置完成"
    else
        log_info "Docker 镜像加速器已配置"
    fi
    
    # 配置 DNS
    if command -v systemctl &> /dev/null; then
        log_info "配置 DNS 解析..."
        sudo tee /etc/systemd/resolved.conf <<-'EOF'
[Resolve]
DNS=223.5.5.5 223.6.6.6
FallbackDNS=8.8.8.8 8.8.4.4
EOF
        sudo systemctl restart systemd-resolved
        log_info "DNS 配置完成"
    fi
}

# 下载部署包
download_package() {
    log_step "下载部署包..."
    
    PACKAGE_URL="${GITEE_URL}/raw/master/releases/${PACKAGE_NAME}.tar.gz"
    
    log_info "下载地址: ${PACKAGE_URL}"
    
    # 尝试下载
    if wget -O "${PACKAGE_NAME}.tar.gz" "${PACKAGE_URL}"; then
        log_info "部署包下载成功"
    elif curl -L -o "${PACKAGE_NAME}.tar.gz" "${PACKAGE_URL}"; then
        log_info "部署包下载成功"
    else
        log_error "部署包下载失败"
        log_info "请手动下载: ${PACKAGE_URL}"
        exit 1
    fi
    
    # 验证文件
    if [ -f "${PACKAGE_NAME}.tar.gz" ]; then
        FILE_SIZE=$(du -h "${PACKAGE_NAME}.tar.gz" | cut -f1)
        log_info "文件大小: ${FILE_SIZE}"
    else
        log_error "文件下载失败"
        exit 1
    fi
}

# 解压部署包
extract_package() {
    log_step "解压部署包..."
    
    if [ -f "${PACKAGE_NAME}.tar.gz" ]; then
        tar -zxvf "${PACKAGE_NAME}.tar.gz"
        log_info "解压完成"
    else
        log_error "部署包文件不存在"
        exit 1
    fi
    
    # 检查解压结果
    if [ -d "${PACKAGE_NAME}" ]; then
        log_info "进入部署目录: ${PACKAGE_NAME}"
        cd "${PACKAGE_NAME}"
    else
        log_error "解压失败"
        exit 1
    fi
}

# 执行安装
run_installation() {
    log_step "执行安装..."
    
    if [ -f "install.sh" ]; then
        chmod +x install.sh
        log_info "开始安装..."
        ./install.sh
    else
        log_error "安装脚本不存在"
        exit 1
    fi
}

# 显示访问信息
show_access_info() {
    log_step "部署完成!"
    echo ""
    echo "=========================================="
    echo "           部署成功!"
    echo "=========================================="
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
    echo "技术支持:"
    echo "  Gitee 仓库: ${GITEE_URL}"
    echo "  Issues: ${GITEE_URL}/issues"
    echo ""
}

# 清理函数
cleanup() {
    log_info "清理临时文件..."
    
    # 返回上级目录
    cd ..
    
    # 清理下载的压缩包
    if [ -f "${PACKAGE_NAME}.tar.gz" ]; then
        rm -f "${PACKAGE_NAME}.tar.gz"
        log_info "临时文件已清理"
    fi
}

# 错误处理
handle_error() {
    log_error "部署过程中发生错误"
    cleanup
    exit 1
}

# 设置错误处理
trap handle_error ERR

# 主函数
main() {
    show_welcome
    check_network
    setup_mirrors
    download_package
    extract_package
    run_installation
    show_access_info
    cleanup
    
    log_info "Gitee 部署完成!"
}

# 显示帮助信息
show_help() {
    echo "敏感词检测系统 Gitee 部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo "  -v, --version  显示版本信息"
    echo "  -u, --user     指定 Gitee 用户名"
    echo "  -r, --repo     指定仓库名称"
    echo "  -t, --tag      指定版本标签"
    echo ""
    echo "示例:"
    echo "  $0                          # 使用默认配置"
    echo "  $0 -u myusername            # 指定用户名"
    echo "  $0 -r my-repo               # 指定仓库名"
    echo "  $0 -t v1.1.0                # 指定版本"
    echo ""
    echo "环境变量:"
    echo "  GITEE_USERNAME              # Gitee 用户名"
    echo "  REPO_NAME                   # 仓库名称"
    echo "  VERSION                     # 版本号"
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--version)
            echo "版本: ${VERSION}"
            exit 0
            ;;
        -u|--user)
            GITEE_USERNAME="$2"
            shift 2
            ;;
        -r|--repo)
            REPO_NAME="$2"
            shift 2
            ;;
        -t|--tag)
            VERSION="$2"
            shift 2
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 更新配置
PACKAGE_NAME="sensitive-detector-v${VERSION}"
GITEE_URL="https://gitee.com/${GITEE_USERNAME}/${REPO_NAME}"

# 执行主函数
main "$@"
