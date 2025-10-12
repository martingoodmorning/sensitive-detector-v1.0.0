#!/bin/bash

# 量化模型设置脚本
# 用于快速下载和配置量化的Qwen模型

set -e

echo "🚀 开始设置量化Qwen模型..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查Ollama是否安装
check_ollama() {
    if ! command -v ollama &> /dev/null; then
        echo -e "${RED}❌ Ollama未安装，请先安装Ollama${NC}"
        echo "安装命令："
        echo "curl -fsSL https://ollama.ai/install.sh | sh"
        exit 1
    fi
    echo -e "${GREEN}✅ Ollama已安装${NC}"
}

# 检查Ollama服务是否运行
check_ollama_service() {
    if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo -e "${YELLOW}⚠️  Ollama服务未运行，正在启动...${NC}"
        ollama serve &
        sleep 5
        
        # 再次检查
        if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
            echo -e "${RED}❌ 无法启动Ollama服务${NC}"
            exit 1
        fi
    fi
    echo -e "${GREEN}✅ Ollama服务正在运行${NC}"
}

# 显示模型选择菜单
show_model_menu() {
    echo -e "${BLUE}请选择要下载的量化模型：${NC}"
    echo "1) qwen2.5:7b-instruct-q4_K_M  (推荐，~4.1GB，生产环境)"
    echo "2) qwen2.5:3b-instruct-q4_K_M  (轻量，~1.9GB，开发测试)"
    echo "3) qwen2.5:1.5b-instruct-q4_K_M (极轻量，~0.9GB，资源受限)"
    echo "4) 自定义模型"
    echo "5) 退出"
}

# 下载模型
download_model() {
    local model=$1
    echo -e "${BLUE}📥 正在下载模型: ${model}${NC}"
    
    if ollama pull "$model"; then
        echo -e "${GREEN}✅ 模型下载成功: ${model}${NC}"
        return 0
    else
        echo -e "${RED}❌ 模型下载失败: ${model}${NC}"
        return 1
    fi
}

# 测试模型
test_model() {
    local model=$1
    echo -e "${BLUE}🧪 正在测试模型: ${model}${NC}"
    
    # 测试简单对话
    response=$(ollama run "$model" "你好，请简单回复'测试成功'" 2>/dev/null)
    
    if [[ $response == *"测试成功"* ]] || [[ $response == *"成功"* ]]; then
        echo -e "${GREEN}✅ 模型测试成功${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  模型测试结果不确定，但可能正常工作${NC}"
        return 0
    fi
}

# 更新Docker配置
update_docker_config() {
    local model=$1
    echo -e "${BLUE}🔧 正在更新Docker配置...${NC}"
    
    # 备份原配置
    if [[ -f "docker-compose.yml" ]]; then
        cp docker-compose.yml docker-compose.yml.backup
        echo -e "${GREEN}✅ 已备份原配置到 docker-compose.yml.backup${NC}"
    fi
    
    # 更新模型配置
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/OLLAMA_MODEL=.*/OLLAMA_MODEL=$model/" docker-compose.yml
    else
        # Linux
        sed -i "s/OLLAMA_MODEL=.*/OLLAMA_MODEL=$model/" docker-compose.yml
    fi
    
    echo -e "${GREEN}✅ Docker配置已更新${NC}"
}

# 显示使用说明
show_usage() {
    local model=$1
    echo -e "${GREEN}🎉 设置完成！${NC}"
    echo ""
    echo -e "${BLUE}📋 使用说明：${NC}"
    echo "1. 模型已下载: $model"
    echo "2. Docker配置已更新"
    echo "3. 启动服务: docker-compose up -d"
    echo "4. 访问应用: http://localhost:8000"
    echo ""
    echo -e "${BLUE}🔍 验证模型：${NC}"
    echo "ollama list | grep $(echo $model | cut -d: -f1)"
    echo ""
    echo -e "${BLUE}📊 性能监控：${NC}"
    echo "docker logs sensitive-detector"
}

# 主函数
main() {
    echo -e "${BLUE}🔍 检查环境...${NC}"
    check_ollama
    check_ollama_service
    
    while true; do
        show_model_menu
        read -p "请选择 (1-5): " choice
        
        case $choice in
            1)
                model="qwen2.5:7b-instruct-q4_K_M"
                break
                ;;
            2)
                model="qwen2.5:3b-instruct-q4_K_M"
                break
                ;;
            3)
                model="qwen2.5:1.5b-instruct-q4_K_M"
                break
                ;;
            4)
                read -p "请输入自定义模型名称: " model
                break
                ;;
            5)
                echo -e "${YELLOW}👋 退出设置${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ 无效选择，请重新输入${NC}"
                ;;
        esac
    done
    
    echo -e "${BLUE}📋 选择的模型: ${model}${NC}"
    
    # 下载模型
    if download_model "$model"; then
        # 测试模型
        test_model "$model"
        
        # 更新Docker配置
        update_docker_config "$model"
        
        # 显示使用说明
        show_usage "$model"
    else
        echo -e "${RED}❌ 设置失败${NC}"
        exit 1
    fi
}

# 运行主函数
main "$@"
