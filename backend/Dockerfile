FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 配置国内源加速
RUN apt-get update && apt-get install -y --no-install-recommends gnupg2 dirmngr && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security/ bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 6ED0E7B82643E131 && \
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 78DBA3BC47EF2265 && \
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys F8D2585B8783D481

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    antiword \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-eng \
    libtesseract-dev \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# 配置 Python 国内源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码和启动脚本
COPY main.py .
COPY start.sh .
RUN chmod +x /app/start.sh

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV OLLAMA_BASE_URL=http://ollama:11434
ENV OLLAMA_MODEL=qwen2.5:7b-instruct-q4_K_M
ENV HEALTH_CHECK_ENABLED=true

# 健康检查（仅检查应用服务）
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令（自动检查并下载模型）
CMD ["/app/start.sh"]