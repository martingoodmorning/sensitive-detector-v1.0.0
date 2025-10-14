# API 文档

## 📋 概述

敏感词检测系统提供 RESTful API 接口，支持文本检测、文档检测、健康检查等功能。

- **Base URL**: `http://localhost:8000`
- **Content-Type**: `application/json`
- **字符编码**: UTF-8
- **认证方式**: 无需认证

## 🔗 接口列表

### 1. 健康检查

**接口地址**: `GET /health`

**描述**: 检查服务健康状态

**请求参数**: 无

**响应格式**:
```json
{
  "status": "healthy",
  "timestamp": 1760443927.4495397,
  "version": "1.0.0"
}
```

**状态码**:
- `200`: 服务正常
- `500`: 服务异常

**示例**:
```bash
curl http://localhost:8000/health
```

### 2. 文本检测

**接口地址**: `POST /detect/text`

**描述**: 检测文本内容是否包含敏感词

**请求参数**:
```json
{
  "text": "需要检测的文本内容"
}
```

**参数说明**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| text | string | 是 | 待检测的文本内容 |

**响应格式**:
```json
{
  "success": true,
  "data": {
    "original_text": "原始文本",
    "rule_detected": ["敏感词1", "敏感词2"],
    "llm_detected": "敏感",
    "final_result": "敏感",
    "detection_time": 0.045,
    "rule_time": 0.005,
    "llm_time": 0.040
  }
}
```

**响应字段说明**:
| 字段名 | 类型 | 说明 |
|--------|------|------|
| success | boolean | 请求是否成功 |
| data.original_text | string | 原始输入文本 |
| data.rule_detected | array | 规则匹配检测到的敏感词列表 |
| data.llm_detected | string | LLM 检测结果（"正常"/"敏感"） |
| data.final_result | string | 最终检测结果（"正常"/"敏感"） |
| data.detection_time | number | 总检测时间（秒） |
| data.rule_time | number | 规则匹配时间（秒） |
| data.llm_time | number | LLM 检测时间（秒） |

**状态码**:
- `200`: 检测成功
- `400`: 请求参数错误
- `500`: 服务器内部错误

**示例**:
```bash
curl -X POST http://localhost:8000/detect/text \
  -H "Content-Type: application/json" \
  -d '{"text": "这是一段测试文本"}'
```

### 3. 文档检测

**接口地址**: `POST /detect/document`

**描述**: 检测上传的文档是否包含敏感内容

**请求参数**: `multipart/form-data`
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | file | 是 | 上传的文档文件 |

**支持的文件格式**:
- **文本文件**: `.txt`
- **PDF 文档**: `.pdf`
- **Word 文档**: `.docx`, `.doc`
- **图片文件**: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`, `.tiff`

**文件限制**:
- **文件大小**: 最大 10MB
- **文本长度**: 最大 10000 个字符

**响应格式**:
```json
{
  "success": true,
  "data": {
    "filename": "document.pdf",
    "file_type": "pdf",
    "text_length": 10000,
    "rule_detected": [],
    "llm_detected": "正常",
    "final_result": "正常",
    "detection_time": 0.450,
    "rule_time": 0.005,
    "llm_time": 0.445
  }
}
```

**响应字段说明**:
| 字段名 | 类型 | 说明 |
|--------|------|------|
| success | boolean | 请求是否成功 |
| data.filename | string | 文件名 |
| data.file_type | string | 文件类型 |
| data.text_length | number | 提取的文本长度 |
| data.rule_detected | array | 规则匹配检测到的敏感词列表 |
| data.llm_detected | string | LLM 检测结果（"正常"/"敏感"） |
| data.final_result | string | 最终检测结果（"正常"/"敏感"） |
| data.detection_time | number | 总检测时间（秒） |
| data.rule_time | number | 规则匹配时间（秒） |
| data.llm_time | number | LLM 检测时间（秒） |

**状态码**:
- `200`: 检测成功
- `400`: 请求参数错误或文件格式不支持
- `413`: 文件过大
- `500`: 服务器内部错误

**示例**:
```bash
curl -X POST http://localhost:8000/detect/document \
  -F "file=@document.pdf"
```

### 4. 词库管理

#### 4.1 获取词库列表

**接口地址**: `GET /word-libraries`

**描述**: 获取所有可用的词库列表

**请求参数**: 无

**响应格式**:
```json
{
  "success": true,
  "data": {
    "libraries": [
      {
        "name": "政治敏感词",
        "filename": "政治敏感词.txt",
        "word_count": 150,
        "last_modified": "2025-01-01T00:00:00Z"
      },
      {
        "name": "暴力词汇",
        "filename": "暴力词汇.txt",
        "word_count": 200,
        "last_modified": "2025-01-01T00:00:00Z"
      }
    ]
  }
}
```

#### 4.2 获取词库内容

**接口地址**: `GET /word-libraries/{library_name}`

**描述**: 获取指定词库的内容

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| library_name | string | 是 | 词库名称（路径参数） |

**响应格式**:
```json
{
  "success": true,
  "data": {
    "name": "政治敏感词",
    "filename": "政治敏感词.txt",
    "words": ["法西斯", "纳粹", "极端主义"],
    "word_count": 3
  }
}
```

#### 4.3 创建词库

**接口地址**: `POST /word-libraries`

**描述**: 创建新的词库

**请求参数**:
```json
{
  "name": "新词库名称",
  "words": ["敏感词1", "敏感词2", "敏感词3"]
}
```

**响应格式**:
```json
{
  "success": true,
  "data": {
    "name": "新词库名称",
    "filename": "新词库名称.txt",
    "word_count": 3,
    "message": "词库创建成功"
  }
}
```

#### 4.4 更新词库

**接口地址**: `PUT /word-libraries/{library_name}`

**描述**: 更新指定词库的内容

**请求参数**:
```json
{
  "words": ["更新后的敏感词1", "更新后的敏感词2"]
}
```

**响应格式**:
```json
{
  "success": true,
  "data": {
    "name": "词库名称",
    "filename": "词库名称.txt",
    "word_count": 2,
    "message": "词库更新成功"
  }
}
```

#### 4.5 删除词库

**接口地址**: `DELETE /word-libraries/{library_name}`

**描述**: 删除指定的词库

**请求参数**: 无

**响应格式**:
```json
{
  "success": true,
  "data": {
    "message": "词库删除成功"
  }
}
```

## ❌ 错误处理

### 错误响应格式

所有接口遵循统一的错误响应格式：

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": "详细错误信息"
  }
}
```

### 错误码说明

| 错误码 | HTTP状态码 | 说明 |
|--------|------------|------|
| `INVALID_PARAMETER` | 400 | 请求参数无效 |
| `FILE_TOO_LARGE` | 413 | 文件过大 |
| `UNSUPPORTED_FILE_TYPE` | 400 | 不支持的文件类型 |
| `TEXT_TOO_LONG` | 400 | 文本长度超限 |
| `LIBRARY_NOT_FOUND` | 404 | 词库不存在 |
| `LIBRARY_ALREADY_EXISTS` | 409 | 词库已存在 |
| `OLLAMA_SERVICE_ERROR` | 500 | Ollama 服务错误 |
| `INTERNAL_SERVER_ERROR` | 500 | 服务器内部错误 |

### 错误示例

#### 参数错误
```json
{
  "success": false,
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "请求参数无效",
    "details": "text 字段不能为空"
  }
}
```

#### 文件过大
```json
{
  "success": false,
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "文件过大",
    "details": "文件大小超过 10MB 限制"
  }
}
```

#### 服务错误
```json
{
  "success": false,
  "error": {
    "code": "OLLAMA_SERVICE_ERROR",
    "message": "Ollama 服务错误",
    "details": "无法连接到 Ollama 服务"
  }
}
```

## 🔧 使用示例

### JavaScript 示例

```javascript
// 文本检测
async function detectText(text) {
  const response = await fetch('http://localhost:8000/detect/text', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text: text })
  });
  
  const result = await response.json();
  return result;
}

// 文档检测
async function detectDocument(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:8000/detect/document', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  return result;
}

// 使用示例
detectText("这是一段测试文本").then(result => {
  console.log('检测结果:', result.data.final_result);
});
```

### Python 示例

```python
import requests
import json

# 文本检测
def detect_text(text):
    url = 'http://localhost:8000/detect/text'
    data = {'text': text}
    
    response = requests.post(url, json=data)
    return response.json()

# 文档检测
def detect_document(file_path):
    url = 'http://localhost:8000/detect/document'
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files)
    
    return response.json()

# 使用示例
result = detect_text("这是一段测试文本")
print(f"检测结果: {result['data']['final_result']}")
```

### cURL 示例

```bash
# 文本检测
curl -X POST http://localhost:8000/detect/text \
  -H "Content-Type: application/json" \
  -d '{"text": "这是一段测试文本"}'

# 文档检测
curl -X POST http://localhost:8000/detect/document \
  -F "file=@document.pdf"

# 健康检查
curl http://localhost:8000/health

# 获取词库列表
curl http://localhost:8000/word-libraries
```

## 📊 性能指标

### 响应时间

| 操作类型 | 平均响应时间 | 最大响应时间 |
|----------|--------------|--------------|
| 规则匹配 | 5ms | 10ms |
| LLM 检测 | 450ms | 1000ms |
| 文档解析 | 100ms | 500ms |
| OCR 识别 | 200ms | 1000ms |

### 吞吐量

| 并发数 | 文本检测 QPS | 文档检测 QPS |
|--------|--------------|--------------|
| 1 | 2 | 1 |
| 5 | 8 | 3 |
| 10 | 15 | 5 |

### 资源使用

| 服务 | 内存使用 | CPU 使用 |
|------|----------|----------|
| Ollama | 6GB | 60% |
| 应用服务 | 1GB | 30% |

## 🔒 安全考虑

### 输入验证

- 文本长度限制：最大 10000 字符
- 文件大小限制：最大 10MB
- 文件类型验证：仅允许指定格式
- 特殊字符过滤：防止注入攻击

### 错误处理

- 不暴露内部错误信息
- 统一错误响应格式
- 记录错误日志用于调试

### 访问控制

- 无认证要求（可根据需要添加）
- CORS 配置支持跨域访问
- 端口访问控制

## 📝 更新日志

### v1.0.0 (2025-01-01)

- 初始版本发布
- 支持文本和文档检测
- 支持词库管理
- 提供健康检查接口

---

**最后更新**: 2025年1月
**版本**: v1.0.0