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

# 显示欢迎信息
show_welcome() {
    echo "=========================================="
    echo "    敏感词检测系统部署脚本"
    echo "    Sensitive Word Detection System"
    echo "=========================================="
    echo ""
}

# 检查系统要求
check_requirements() {
    log_step "检查系统要求..."
    
    # 检查操作系统
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log_info "操作系统: Linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        log_info "操作系统: macOS"
    else
        log_warn "未识别的操作系统: $OSTYPE"
    fi
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        echo "安装命令: curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
        exit 1
    fi
    
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    log_info "Docker 版本: $DOCKER_VERSION"
    
    # 检查 Docker Compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
        log_info "Docker Compose 版本: $COMPOSE_VERSION"
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version --short)
        log_info "Docker Compose 版本: $COMPOSE_VERSION"
        COMPOSE_CMD="docker compose"
    else
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        echo "安装命令: sudo curl -L \"https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
        exit 1
    fi
    
    # 检查内存
    if command -v free &> /dev/null; then
        MEMORY_GB=$(free -g | awk 'NR==2{print $2}')
        if [ $MEMORY_GB -lt 8 ]; then
            log_warn "系统内存不足 8GB (当前: ${MEMORY_GB}GB)，可能影响 LLM 性能"
        else
            log_info "系统内存: ${MEMORY_GB}GB"
        fi
    fi
    
    # 检查磁盘空间
    if command -v df &> /dev/null; then
        DISK_FREE=$(df -BG . | awk 'NR==2{print $4}' | sed 's/G//')
        if [ $DISK_FREE -lt 20 ]; then
            log_warn "磁盘空间不足 20GB (当前: ${DISK_FREE}GB)"
        else
            log_info "可用磁盘空间: ${DISK_FREE}GB"
        fi
    fi
    
    log_info "系统要求检查通过"
}

# 创建必要目录
create_directories() {
    log_step "创建必要目录..."
    
    mkdir -p logs config backup
    
    # 设置目录权限
    chmod 755 logs config backup
    
    log_info "目录创建完成"
}

# 配置敏感词库
setup_sensitive_words() {
    log_step "配置敏感词库..."
    
    if [ ! -f config/sensitive_words.txt ]; then
        log_info "创建默认敏感词库..."
        cat > config/sensitive_words.txt << 'EOF'
# 敏感词库文件
# 每行一个敏感词，支持中文和英文
# 以 # 开头的行为注释

# 辱骂词汇
白痴
傻逼
去死
混蛋
王八蛋

# 暴力威胁
杀了你
打你
伤害
暴力

# 违法内容
毒品
犯罪
违法
赌博

# 色情内容
色情
性暗示
黄色

# 歧视内容
种族歧视
性别歧视
地域歧视
EOF
        log_info "默认敏感词库创建完成"
    else
        log_info "使用现有敏感词库"
    fi
    
    # 设置文件权限
    chmod 644 config/sensitive_words.txt
}

# 下载并启动 Ollama
setup_ollama() {
    log_step "设置 Ollama 服务..."
    
    # 检查 Ollama 是否已安装
    if ! command -v ollama &> /dev/null; then
        log_info "安装 Ollama..."
        curl -fsSL https://ollama.ai/install.sh | sh
    else
        log_info "Ollama 已安装"
    fi
    
    # 启动 Ollama 服务
    log_info "启动 Ollama 服务..."
    export OLLAMA_HOST=0.0.0.0:11434
    ollama serve &
    OLLAMA_PID=$!
    
    # 等待服务启动
    sleep 10
    
    # 检查服务状态
    if curl -s http://localhost:11434/api/tags > /dev/null; then
        log_info "Ollama 服务启动成功"
    else
        log_error "Ollama 服务启动失败"
        exit 1
    fi
    
    # 下载 qwen:7b 模型
    log_info "下载 qwen:7b 模型 (这可能需要几分钟)..."
    ollama pull qwen:7b
    
    if [ $? -eq 0 ]; then
        log_info "模型下载完成"
    else
        log_error "模型下载失败"
        exit 1
    fi
}

# 部署应用
deploy_app() {
    log_step "部署敏感词检测系统..."
    
    # 检查 docker-compose.yml 文件
    if [ ! -f docker-compose.yml ]; then
        log_error "docker-compose.yml 文件不存在"
        exit 1
    fi
    
    # 停止现有服务
    log_info "停止现有服务..."
    $COMPOSE_CMD down 2>/dev/null || true
    
    # 构建并启动服务
    log_info "构建并启动服务..."
    $COMPOSE_CMD up -d --build
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 健康检查
    log_info "执行健康检查..."
    for i in {1..10}; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            log_info "服务启动成功!"
            break
        else
            log_warn "健康检查失败，重试中... ($i/10)"
            sleep 10
        fi
        
        if [ $i -eq 10 ]; then
            log_error "服务启动失败，请检查日志"
            $COMPOSE_CMD logs
            exit 1
        fi
    done
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
    echo "  查看日志: $COMPOSE_CMD logs -f"
    echo "  停止服务: $COMPOSE_CMD down"
    echo "  重启服务: $COMPOSE_CMD restart"
    echo "  查看状态: $COMPOSE_CMD ps"
    echo ""
    echo "配置文件:"
    echo "  敏感词库: config/sensitive_words.txt"
    echo "  日志目录: logs/"
    echo "  备份目录: backup/"
    echo ""
    echo "注意事项:"
    echo "  - 首次启动可能需要几分钟下载模型"
    echo "  - 建议定期备份敏感词库"
    echo "  - 生产环境请配置 HTTPS 和防火墙"
    echo ""
}

# 清理函数
cleanup() {
    log_info "清理临时文件..."
    # 这里可以添加清理逻辑
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
    check_requirements
    create_directories
    setup_sensitive_words
    setup_ollama
    deploy_app
    show_access_info
    
    log_info "部署完成!"
}

# 执行主函数
main "$@"
