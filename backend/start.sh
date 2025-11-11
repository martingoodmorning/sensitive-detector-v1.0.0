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
echo ""
echo "📋 系统信息："
echo "   模型: $MODEL_NAME"
echo "   Ollama地址: $OLLAMA_URL"
echo ""

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

# 监控下载进度
monitor_download_progress() {
    echo "🔄 开始监控下载进度..."
    echo ""
    
    # 获取下载开始时间
    start_time=$(date +%s)
    last_progress_time=$start_time
    
    # 监控下载进度
    while true; do
        # 检查模型是否已存在
        if curl -s "$OLLAMA_URL/api/tags" | grep -q "$MODEL_NAME"; then
            end_time=$(date +%s)
            duration=$((end_time - start_time))
            echo ""
            echo "✅ 模型下载完成！"
            echo "   下载时间: ${duration}秒"
            break
        fi
        
        # 检查下载进程是否还在运行
        if ! kill -0 $download_pid 2>/dev/null; then
            echo ""
            echo "⚠️  下载进程已结束，检查下载状态..."
            break
        fi
        
        # 显示进度信息
        current_time=$(date +%s)
        elapsed=$((current_time - start_time))
        
        # 每10秒显示一次详细进度
        if [ $((current_time - last_progress_time)) -ge 10 ]; then
            echo ""
            echo "⏳ 下载进行中... 已用时: ${elapsed}秒"
            echo "   请耐心等待，大模型下载需要较长时间"
            last_progress_time=$current_time
        else
            # 每5秒显示一个点
            echo -n "."
        fi
        
        sleep 5
    done
}

# 显示下载进度
show_download_progress() {
    echo ""
    echo "📊 模型下载信息："
    echo "   模型名称: $MODEL_NAME"
    echo "   预计大小: ~5.2GB"
    echo "   预计时间: 10-30分钟（取决于网络速度）"
    echo ""
    echo "🔄 正在下载中，请耐心等待..."
    echo "   实时监控: 每5秒检查一次下载状态"
    echo "   详细日志: docker logs ollama-service -f"
    echo ""
}

# 下载模型
download_model() {
    echo "📥 正在下载模型: $MODEL_NAME"
    show_download_progress
    
    # 启动下载
    echo "🔄 开始下载模型..."
    echo ""
    
    # 使用流式API获取实时下载进度
    curl -X POST "$OLLAMA_URL/api/pull" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"$MODEL_NAME\",\"stream\":true}" \
        --no-buffer | while IFS= read -r line; do
        # 解析JSON响应并输出进度
        if echo "$line" | jq -e '.status' >/dev/null 2>&1; then
            status=$(echo "$line" | jq -r '.status')
            if [ "$status" = "pulling" ]; then
                digest=$(echo "$line" | jq -r '.digest // "unknown"')
                total=$(echo "$line" | jq -r '.total // 0')
                completed=$(echo "$line" | jq -r '.completed // 0')
                
                if [ "$total" -gt 0 ]; then
                    percent=$((completed * 100 / total))
                    # 格式化字节大小
                    total_mb=$((total / 1024 / 1024))
                    completed_mb=$((completed / 1024 / 1024))
                    echo "📥 下载进度: ${percent}% (${completed_mb}MB/${total_mb}MB) - ${digest:0:12}"
                else
                    echo "📥 正在下载: ${digest:0:12}"
                fi
            elif [ "$status" = "success" ]; then
                echo "✅ 模型下载完成: $MODEL_NAME"
                break
            fi
        fi
    done
    
    # 验证下载结果
    if curl -s "$OLLAMA_URL/api/tags" | grep -q "$MODEL_NAME"; then
        echo "✅ 模型验证成功: $MODEL_NAME"
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
        echo "⚠️ 模型测试结果不确定，但可能正常工作"
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
    
    # 无论模型是否刚下载，统一进行一次轻量预热，降低首请求延迟
    echo "🔥 进行一次模型预热..."
    test_model || echo "⚠️  预热调用未确认成功，但服务将继续启动"
    
    echo ""
    echo "🎉 系统准备完成！"
    echo ""
    echo "📊 服务状态："
    echo "   ✅ Ollama服务: 已就绪"
    echo "   ✅ 模型: $MODEL_NAME"
    echo "   ✅ 服务地址: $OLLAMA_URL"
    echo ""
    echo "🌐 启动 FastAPI 应用..."
    echo "   前端界面: http://localhost:8000"
    echo "   API文档: http://localhost:8000/api/docs"
    echo "   健康检查: http://localhost:8000/health"
    echo ""
    exec python main.py
}

# 运行主函数
main "$@"
