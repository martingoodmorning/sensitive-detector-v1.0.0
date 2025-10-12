# 后端技术文档

## 概述

敏感词检测系统后端基于 FastAPI 框架构建，提供高性能的 RESTful API 服务。系统集成了传统的敏感词匹配算法和大语言模型，实现双重检测机制，确保检测结果的准确性和可靠性。

## 技术架构

### 框架选择

- **FastAPI**: 现代化的 Python Web 框架
- **Uvicorn**: ASGI 服务器，支持异步处理
- **Pydantic**: 数据验证和序列化
- **Python 3.10+**: 编程语言

### 核心组件

```
后端系统
├── Web 服务层 (FastAPI)
│   ├── 路由处理
│   ├── 中间件
│   └── 异常处理
├── 业务逻辑层
│   ├── 文本检测服务
│   ├── 文档解析服务
│   └── 结果整合服务
├── 算法层
│   ├── 文本预处理（字符归一化）
│   ├── AC自动机多模式匹配
│   ├── DFA精确验证
│   └── LLM 智能检测
└── 外部服务
    └── Ollama LLM 服务
```

## 项目结构

```
backend/
├── main.py                 # 主应用文件
├── requirements.txt        # Python 依赖
├── Dockerfile             # Docker 构建文件
└── word_libraries/         # 敏感词库目录
```

## 核心文件详解

### main.py

主应用文件，包含所有 API 端点和业务逻辑。

#### 导入模块

```python
import os
import re
import time
from typing import List, Union
from collections import defaultdict

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import requests
import PyPDF2
from docx import Document
```

#### 应用初始化

```python
# FastAPI 应用实例
app = FastAPI(
    title="敏感词检测",
    version="1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件挂载
app.mount("/static", StaticFiles(directory="/app/frontend"), name="static")
```

#### 数据模型

```python
class TextDetectionRequest(BaseModel):
    text: str

class DetectionResponse(BaseModel):
    success: bool
    data: Union[dict, None] = None
    error: Union[dict, None] = None
```

#### 敏感词检测算法

**AC自动机实现**:
```python
class ACAutomaton:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.word = ""

class SensitiveWordDetector:
    def __init__(self, words_file: str):
        self.root = TrieNode()
        self.load_words(words_file)
    
    def load_words(self, words_file: str):
        """加载敏感词库"""
        try:
            with open(words_file, 'r', encoding='utf-8') as f:
                for word in f:
                    word = word.strip()
                    if word:
                        self.insert_word(word)
        except FileNotFoundError:
            print(f"敏感词文件 {words_file} 不存在")
    
    def insert_word(self, word: str):
        """插入敏感词到 Trie 树"""
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True
        node.word = word
    
    def detect(self, text: str) -> List[str]:
        """检测文本中的敏感词"""
        sensitive_words = []
        text_lower = text.lower()
        
        for i in range(len(text_lower)):
            node = self.root
            j = i
            while j < len(text_lower) and text_lower[j] in node.children:
                node = node.children[text_lower[j]]
                if node.is_end:
                    sensitive_words.append(node.word)
                j += 1
        
        return list(set(sensitive_words))
```

#### LLM 检测服务

```python
def call_ollama_api(text: str) -> str:
    """调用 Ollama API 进行 LLM 检测"""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://172.20.0.1:11434").rstrip("/")
    model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct-q4_K_M")
    ollama_url = f"{base_url}/api/generate"
    
    # 优化的提示词
    prompt = f"""
    你是专业的内容安全检测系统。请严格按照以下规则进行判断：

    【敏感内容标准】
    必须同时满足以下条件才判定为敏感：
    1. 包含明确的辱骂词汇（如：白痴、傻逼、去死等）
    2. 包含暴力威胁（如：杀了你、打你、伤害等）
    3. 包含违法内容（如：毒品、犯罪、违法等）
    4. 包含色情内容（如：性暗示、色情描述等）
    5. 包含歧视内容（如：种族歧视、性别歧视等）

    【检测文本】
    {text[:500]}

    【判断规则】
    - 如果文本明显包含上述任何一类敏感内容，回答：敏感
    - 如果文本是正常的日常对话、描述、询问等，回答：正常
    - 对于模糊边界的内容，倾向于判定为正常

    【输出要求】
    请严格按照以下格式输出，不要添加任何其他内容：
    敏感
    或
    正常
    """
    
    try:
        response = requests.post(
            ollama_url,
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "temperature": 0  # 设置为0确保一致性
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "正常").strip()
        else:
            print(f"Ollama API 调用失败：{response.text}")
            return "正常"
            
    except Exception as e:
        print(f"Ollama API 调用异常：{e}")
        return "正常"
```

#### 文档解析服务

```python
def extract_text_from_file(file: UploadFile) -> str:
    """从上传的文件中提取文本内容"""
    content = file.file.read()
    
    if file.content_type == "text/plain":
        return content.decode("utf-8")
    
    elif file.content_type == "application/pdf":
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PDF 解析失败: {str(e)}")
    
    elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        try:
            doc = Document(io.BytesIO(content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"DOCX 解析失败: {str(e)}")
    
    else:
        raise HTTPException(status_code=400, detail="不支持的文件类型")
```

#### API 端点

**1. 文本检测端点**:
```python
@app.post("/detect/text", response_model=DetectionResponse)
async def detect_text(request: TextDetectionRequest):
    """文本敏感词检测"""
    try:
        text = request.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="文本内容不能为空")
        
        # 规则匹配检测
        rule_detected = detector.detect(text)
        
        # LLM 检测
        llm_detected = call_ollama_api(text)
        
        # 结果整合
        final_result = "敏感" if rule_detected or llm_detected == "敏感" else "正常"
        
        return DetectionResponse(
            success=True,
            data={
                "original_text": text,
                "rule_detected": rule_detected if rule_detected else "正常",
                "llm_detected": llm_detected,
                "final_result": final_result
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")
```

**2. 文档检测端点**:
```python
@app.post("/detect/document", response_model=DetectionResponse)
async def detect_document(file: UploadFile = File(...)):
    """文档敏感词检测"""
    try:
        # 文件类型检查
        allowed_types = [
            "text/plain",
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail="不支持的文件类型，仅支持 TXT、PDF、DOCX、DOC 格式和图片格式（OCR）"
            )
        
        # 文件大小检查 (10MB)
        if file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")
        
        # 提取文本内容
        text = extract_text_from_file(file)
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="文档内容为空")
        
        # 规则匹配检测
        rule_detected = detector.detect(text)
        
        # LLM 检测
        llm_detected = call_ollama_api(text)
        
        # 结果整合
        final_result = "敏感" if rule_detected or llm_detected == "敏感" else "正常"
        
        return DetectionResponse(
            success=True,
            data={
                "filename": file.filename,
                "file_type": file.content_type.split("/")[-1],
                "text_length": len(text),
                "rule_detected": rule_detected if rule_detected else "正常",
                "llm_detected": llm_detected,
                "final_result": final_result
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")
```

**3. 健康检查端点**:
```python
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }
```

**4. 静态文件服务**:
```python
@app.get("/", include_in_schema=False)
async def read_root():
    """根路径重定向到前端页面"""
    return FileResponse("/app/frontend/index.html")

@app.get("/docs", include_in_schema=False)
async def read_docs():
    """文档路径重定向到前端页面"""
    return FileResponse("/app/frontend/index.html")
```

## 算法详解

### 规则匹配引擎（预处理+AC+DFA）

**算法原理**:
1. 文本预处理：字符归一化（全角转半角、繁体转简体、特殊符号移除）
2. AC自动机匹配：多模式字符串匹配，快速识别可能的敏感词
3. DFA精确验证：对AC标记的可疑文本片段进行精确匹配验证
4. 结果收集：收集所有匹配的敏感词

**时间复杂度**:
- 文本预处理: O(k)，k 为文本长度
- AC自动机构建: O(n*m)，n 为敏感词数量，m 为平均长度
- AC匹配: O(k+z)，k 为文本长度，z 为匹配数量
- DFA验证: O(z*m)，z 为可疑片段数量，m 为平均长度

**空间复杂度**:
- AC自动机存储: O(n*m)
- DFA状态机: O(n*m)
- 检测过程: O(1)

**优势**:
- 高效的字符串匹配（AC自动机）
- 支持多模式匹配
- 精确的二次验证（DFA）
- 统一的变体处理（文本预处理）
- 内存使用合理

### LLM 智能检测

**模型选择**:
- **Qwen2.5:7b**: 通义千问 2.5 版本 7B 参数模型（量化版本）
- **本地部署**: 使用 Ollama 框架
- **一致性优化**: temperature=0 确保输出一致

**提示词工程**:
```python
prompt = f"""
你是专业的内容安全检测系统。请严格按照以下规则进行判断：

【敏感内容标准】
必须同时满足以下条件才判定为敏感：
1. 包含明确的辱骂词汇（如：白痴、傻逼、去死等）
2. 包含暴力威胁（如：杀了你、打你、伤害等）
3. 包含违法内容（如：毒品、犯罪、违法等）
4. 包含色情内容（如：性暗示、色情描述等）
5. 包含歧视内容（如：种族歧视、性别歧视等）

【检测文本】
{text[:500]}

【判断规则】
- 如果文本明显包含上述任何一类敏感内容，回答：敏感
- 如果文本是正常的日常对话、描述、询问等，回答：正常
- 对于模糊边界的内容，倾向于判定为正常

【输出要求】
请严格按照以下格式输出，不要添加任何其他内容：
敏感
或
正常
"""
```

**检测流程**:
1. 文本预处理：截取前500字符
2. 提示词构建：包含检测规则和文本
3. API 调用：发送到 Ollama 服务
4. 结果解析：提取检测结果
5. 异常处理：网络错误时返回默认值

## 性能优化

### 算法优化

1. **Trie 树优化**:
   ```python
   # 使用字典而非列表存储子节点
   self.children = {}
   
   # 预分配内存
   self.word = ""
   ```

2. **文本处理优化**:
   ```python
   # 使用生成器而非列表
   def detect_generator(self, text: str):
       for i in range(len(text)):
           # 生成匹配结果
           yield self._match_at_position(text, i)
   ```

3. **LLM 调用优化**:
   ```python
   # 设置超时时间
   response = requests.post(url, json=data, timeout=30)
   
   # 使用连接池
   session = requests.Session()
   ```

### 内存优化

1. **对象复用**:
   ```python
   # 复用 Trie 树实例
   detector = SensitiveWordDetector(["word_libraries/政治敏感词.txt", "word_libraries/暴力词汇.txt"])
   ```

2. **垃圾回收**:
   ```python
   import gc
   gc.collect()  # 手动触发垃圾回收
   ```

3. **内存监控**:
   ```python
   import psutil
   memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
   ```

### 并发优化

1. **异步处理**:
   ```python
   async def detect_text_async(request: TextDetectionRequest):
       # 异步处理检测逻辑
       pass
   ```

2. **连接池**:
   ```python
   import aiohttp
   async with aiohttp.ClientSession() as session:
       async with session.post(url, json=data) as response:
           result = await response.json()
   ```

3. **任务队列**:
   ```python
   import asyncio
   tasks = [detect_text_async(req) for req in requests]
   results = await asyncio.gather(*tasks)
   ```

## 错误处理

### 异常分类

1. **输入验证异常**:
   ```python
   if not text.strip():
       raise HTTPException(status_code=400, detail="文本内容不能为空")
   ```

2. **文件处理异常**:
   ```python
   try:
       text = extract_text_from_file(file)
   except Exception as e:
       raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")
   ```

3. **外部服务异常**:
   ```python
   try:
       response = requests.post(ollama_url, json=data, timeout=30)
   except requests.exceptions.Timeout:
       return "正常"  # 超时返回默认值
   except requests.exceptions.ConnectionError:
       return "正常"  # 连接错误返回默认值
   ```

### 错误响应格式

```python
class ErrorResponse(BaseModel):
    success: bool = False
    error: dict

# 错误响应示例
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "文本内容不能为空",
        "details": "请求参数验证失败"
    }
}
```

### 日志记录

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 记录错误
try:
    result = risky_operation()
except Exception as e:
    logger.error(f"操作失败: {str(e)}", exc_info=True)
    raise HTTPException(status_code=500, detail="操作失败")
```

## 安全考虑

### 输入验证

1. **文本长度限制**:
   ```python
   if len(text) > 10000:
       raise HTTPException(status_code=400, detail="文本长度不能超过10000字符")
   ```

2. **文件类型检查**:
   ```python
   allowed_types = ["text/plain", "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
   if file.content_type not in allowed_types:
       raise HTTPException(status_code=400, detail="不支持的文件类型")
   ```

3. **文件大小限制**:
   ```python
   if file.size > 10 * 1024 * 1024:  # 10MB
       raise HTTPException(status_code=400, detail="文件大小不能超过10MB")
   ```

### 数据安全

1. **敏感信息过滤**:
   ```python
   # 不记录敏感内容到日志
   logger.info(f"检测请求: 文本长度={len(text)}")
   ```

2. **错误信息脱敏**:
   ```python
   # 不暴露内部错误详情
   except Exception as e:
       logger.error(f"内部错误: {str(e)}")
       raise HTTPException(status_code=500, detail="检测失败")
   ```

### 访问控制

1. **CORS 配置**:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # 生产环境应限制具体域名
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **请求限流**:
   ```python
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   from slowapi.errors import RateLimitExceeded
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
   
   @app.post("/detect/text")
   @limiter.limit("10/minute")
   async def detect_text(request: Request, ...):
       pass
   ```

## 监控和日志

### 性能监控

1. **响应时间监控**:
   ```python
   import time
   
   @app.middleware("http")
   async def add_process_time_header(request: Request, call_next):
       start_time = time.time()
       response = await call_next(request)
       process_time = time.time() - start_time
       response.headers["X-Process-Time"] = str(process_time)
       return response
   ```

2. **内存使用监控**:
   ```python
   import psutil
   
   def get_memory_usage():
       process = psutil.Process()
       return process.memory_info().rss / 1024 / 1024  # MB
   ```

3. **API 调用统计**:
   ```python
   from collections import defaultdict
   
   api_stats = defaultdict(int)
   
   @app.middleware("http")
   async def track_api_calls(request: Request, call_next):
       api_stats[request.url.path] += 1
       response = await call_next(request)
       return response
   ```

### 日志配置

1. **结构化日志**:
   ```python
   import structlog
   
   logger = structlog.get_logger()
   
   # 使用结构化日志
   logger.info("API调用", 
               endpoint=request.url.path,
               method=request.method,
               response_time=process_time)
   ```

2. **日志级别**:
   ```python
   # 开发环境
   logging.basicConfig(level=logging.DEBUG)
   
   # 生产环境
   logging.basicConfig(level=logging.INFO)
   ```

3. **日志轮转**:
   ```python
   from logging.handlers import RotatingFileHandler
   
   handler = RotatingFileHandler(
       'app.log', 
       maxBytes=10*1024*1024,  # 10MB
       backupCount=5
   )
   logger.addHandler(handler)
   ```

## 部署配置

### Docker 配置

**Dockerfile**:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**requirements.txt**:
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
requests==2.31.0
PyPDF2==3.0.1
python-docx==1.1.0
python-multipart==0.0.6
```

### 环境变量

```bash
# Ollama 配置
OLLAMA_BASE_URL=http://172.20.0.1:11434
OLLAMA_MODEL=qwen2.5:7b-instruct-q4_K_M

# 应用配置
PYTHONUNBUFFERED=1
CORS_ALLOW_ORIGINS=*

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 健康检查

```python
@app.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        # 检查 Ollama 连接
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://172.20.0.1:11434")
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        ollama_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        ollama_status = "unhealthy"
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "services": {
            "ollama": ollama_status
        }
    }
```

## 测试指南

### 单元测试

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_detect_text():
    response = client.post("/detect/text", json={"text": "测试文本"})
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_detect_text_empty():
    response = client.post("/detect/text", json={"text": ""})
    assert response.status_code == 400

def test_detect_document():
    with open("test.txt", "rb") as f:
        response = client.post("/detect/document", files={"file": f})
    assert response.status_code == 200
```

### 集成测试

```python
def test_full_detection_flow():
    # 测试完整检测流程
    text = "这是一个测试文本"
    response = client.post("/detect/text", json={"text": text})
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert "original_text" in data
    assert "rule_detected" in data
    assert "llm_detected" in data
    assert "final_result" in data
```

### 性能测试

```python
import time

def test_performance():
    start_time = time.time()
    
    for i in range(100):
        response = client.post("/detect/text", json={"text": f"测试文本{i}"})
        assert response.status_code == 200
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 100
    
    assert avg_time < 1.0  # 平均响应时间小于1秒
```

## 故障排除

### 常见问题

1. **Ollama 连接失败**:
   ```bash
   # 检查 Ollama 服务状态
   curl http://localhost:11434/api/tags
   
   # 重启 Ollama 服务
   pkill ollama
   ollama serve &
   ```

2. **内存不足**:
   ```bash
   # 检查内存使用
   free -h
   
   # 清理内存
   sync && echo 3 > /proc/sys/vm/drop_caches
   ```

3. **端口冲突**:
   ```bash
   # 检查端口占用
   netstat -tlnp | grep 8000
   
   # 杀死占用进程
   kill -9 <PID>
   ```

### 调试技巧

1. **启用调试模式**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **添加调试信息**:
   ```python
   print(f"调试信息: {variable}")
   logger.debug(f"调试信息: {variable}")
   ```

3. **使用调试器**:
   ```python
   import pdb
   pdb.set_trace()  # 设置断点
   ```

---

**文档版本**: v1.0.0  
**最后更新**: 2025年10月
