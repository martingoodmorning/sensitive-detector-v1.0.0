FROM python:3.10-slim

# 设置工作目录（容器内的目录，后续操作都在这个目录下）
WORKDIR /app

# 1. 安装系统依赖（仅必要的构建工具与运行依赖）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    antiword \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-eng \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. 配置Python国内源（加速依赖安装）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 安装Python依赖（先复制requirements.txt，利用Docker缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 复制后端代码到容器
COPY main.py .

# 5. 暴露端口（FastAPI运行在8000端口，需与docker-compose.yml一致）
EXPOSE 8000

# 6. 容器启动命令（执行main.py，启动UVicorn服务）
CMD ["python", "main.py"]
