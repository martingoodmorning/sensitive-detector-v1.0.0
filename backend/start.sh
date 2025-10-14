#!/bin/bash

# 自动模型检查和下载脚本
# 在应用启动时自动检查模型是否存在，如果没有就下载

set -e

# 环境变量
OLLAMA_URL=${OLLAMA_BASE_URL:-http://ollama:11434}
MODEL_NAME=${OLLAMA_MODEL:-qwen2.5:7b-instruct-q4_K_M}
MAX_RETRIES=30
RETRY_INTERVAL=2

# 检测地址列表（按优先级）
OLLAMA_URLS=(
    "$OLLAMA_URL"                    # 环境变量指定的地址
    "http://ollama:11434"            # Docker 容器内地址
    "http://host.docker.internal:11434"  # Docker Desktop 宿主机地址
    "http://172.17.0.1:11434"        # Docker 网关地址
    "http://localhost:11434"         # 本地地址
)

echo "🚀 启动敏感词检测服务..."

# 检查 Ollama 服务是否可用
check_ollama_service() {
    echo "🔍 检查 Ollama 服务..."
    
    # 尝试多个地址
    for url in "${OLLAMA_URLS[@]}"; do
        echo "🔍 尝试连接: $url"
        if curl -s "$url/api/tags" > /dev/null 2>&1; then
            echo "✅ Ollama 服务已就绪: $url"
            OLLAMA_URL="$url"  # 更新全局变量
            return 0
        fi
    done
    
    # 如果所有地址都失败，等待容器内服务启动
    echo "⏳ 等待容器内 Ollama 服务启动..."
    for i in $(seq 1 $MAX_RETRIES); do
        if curl -s "http://ollama:11434/api/tags" > /dev/null 2>&1; then
            echo "✅ 容器内 Ollama 服务已就绪"
            OLLAMA_URL="http://ollama:11434"
            return 0
        fi
        echo "⏳ 等待 Ollama 服务启动... ($i/$MAX_RETRIES)"
        sleep $RETRY_INTERVAL
    done
    
    echo "❌ 无法连接到任何 Ollama 服务"
    echo "请确保："
    echo "1. 容器内 Ollama 服务正在启动"
    echo "2. 或者宿主机 Ollama 服务正在运行"
    return 1
}

# 检查模型是否存在
check_model_exists() {
    echo "🔍 检查模型: $MODEL_NAME"
    
    if curl -s "$OLLAMA_URL/api/tags" | grep -q "$MODEL_NAME"; then
        echo "✅ 模型已存在: $MODEL_NAME"
        return 0
    else
        echo "⚠️  模型不存在: $MODEL_NAME"
        return 1
    fi
}

# 下载模型
download_model() {
    echo "📥 正在下载模型: $MODEL_NAME"
    
    # 使用 Ollama API 下载模型
    if curl -X POST "$OLLAMA_URL/api/pull" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"$MODEL_NAME\"}" \
        --progress-bar; then
        echo "✅ 模型下载成功: $MODEL_NAME"
        return 0
    else
        echo "❌ 模型下载失败: $MODEL_NAME"
        return 1
    fi
}

# 测试模型
test_model() {
    echo "🧪 测试模型: $MODEL_NAME"
    
    # 使用 Ollama API 测试模型
    response=$(curl -s -X POST "$OLLAMA_URL/api/generate" \
        -H "Content-Type: application/json" \
        -d "{\"model\":\"$MODEL_NAME\",\"prompt\":\"你好\",\"stream\":false}" | \
        jq -r '.response' 2>/dev/null || echo "")
    
    if [[ $response == *"你好"* ]] || [[ $response == *"Hello"* ]] || [[ -n "$response" ]]; then
        echo "✅ 模型测试成功"
        return 0
    else
        echo "⚠️  模型测试结果不确定，但可能正常工作"
        return 0
    fi
}

# 主函数
main() {
    echo "🔍 检查环境..."
    
    # 检查 Ollama 服务
    if ! check_ollama_service; then
        echo "❌ 无法连接到 Ollama 服务"
        exit 1
    fi
    
    # 检查模型是否存在
    if ! check_model_exists; then
        echo "📥 模型不存在，开始下载..."
        if download_model; then
            test_model
        else
            echo "❌ 模型下载失败，但服务将继续启动"
        fi
    else
        echo "✅ 模型已就绪，直接使用"
    fi
    
    echo "🌐 启动 FastAPI 应用..."
    exec python main.py
}

# 运行主函数
main "$@"
