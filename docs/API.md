# API 技术文档

## 概述

敏感词检测系统提供 RESTful API 接口，支持文本和文档的敏感内容检测。API 基于 FastAPI 框架构建，提供自动生成的交互式文档。

## 基础信息

- **Base URL**: `http://localhost:8000`
- **API 版本**: v1.0.0
- **协议**: HTTP/HTTPS
- **数据格式**: JSON
- **字符编码**: UTF-8

## 认证

当前版本无需认证，所有接口均为公开访问。

## 通用响应格式

### 成功响应

```json
{
  "success": true,
  "data": {
    // 具体数据内容
  }
}
```

### 错误响应

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

## 接口详情

### 1. 文本检测

检测文本内容中的敏感词。

**接口地址**: `POST /detect/text`

**请求头**:
```
Content-Type: application/json
```

**请求参数**:
```json
{
  "text": "需要检测的文本内容"
}
```

**参数说明**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| text | string | 是 | 待检测的文本内容，最大长度 10000 字符 |
| fast_mode | boolean | 否 | 快速模式，默认false（规则匹配+LLM双重检测） |
| strict_mode | boolean | 否 | 严格模式，默认false（跳过规则匹配，直接LLM检测） |

**检测模式说明**:
- **默认模式** (fast_mode=false, strict_mode=false): 规则匹配快速筛选 + 存疑内容大模型检测
- **严格模式** (strict_mode=true): 跳过规则匹配，直接使用大模型检测
- **快速模式** (fast_mode=true): 仅使用规则匹配算法（已废弃，建议使用默认模式）

**响应示例**:
```json
{
  "success": true,
  "data": {
    "original_text": "你是个白痴，我要杀了你",
    "rule_detected": ["白痴"],
    "llm_detected": "敏感",
    "final_result": "敏感"
  }
}
```

**响应字段说明**:
| 字段名 | 类型 | 说明 |
|--------|------|------|
| original_text | string | 原始输入文本 |
| rule_detected | array/string | 规则匹配结果，数组为检测到的敏感词列表，字符串为"正常" |
| llm_detected | string | LLM 检测结果，"敏感"或"正常" |
| final_result | string | 最终检测结果，"敏感"或"正常" |

**状态码**:
- `200`: 检测成功
- `400`: 请求参数错误
- `422`: 数据验证失败
- `500`: 服务器内部错误

### 2. 文档检测

检测上传文档中的敏感内容。

**接口地址**: `POST /detect/document`

**请求头**:
```
Content-Type: multipart/form-data
```

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | file | 是 | 待检测的文档文件 |

**支持的文件格式**:
- TXT (.txt)
- PDF (.pdf)
- DOCX (.docx)
- DOC (.doc) - 使用antiword工具解析
- 图片格式 (.jpg, .jpeg, .png, .bmp, .gif, .tiff) - 使用OCR识别

**文件大小限制**: 10MB

**响应示例**:
```json
{
  "success": true,
  "data": {
    "filename": "test_document.pdf",
    "file_type": "pdf",
    "text_length": 1500,
    "rule_detected": [],
    "llm_detected": "正常",
    "final_result": "正常"
  }
}
```

**响应字段说明**:
| 字段名 | 类型 | 说明 |
|--------|------|------|
| filename | string | 文件名 |
| file_type | string | 文件类型 |
| text_length | integer | 提取的文本长度 |
| rule_detected | array/string | 规则匹配结果 |
| llm_detected | string | LLM 检测结果 |
| final_result | string | 最终检测结果 |

**状态码**:
- `200`: 检测成功
- `400`: 请求参数错误
- `413`: 文件过大
- `415`: 不支持的文件类型
- `500`: 服务器内部错误

### 3. 健康检查

检查服务运行状态。

**接口地址**: `GET /health`

**请求参数**: 无

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0"
}
```

**响应字段说明**:
| 字段名 | 类型 | 说明 |
|--------|------|------|
| status | string | 服务状态，"healthy" 或 "unhealthy" |
| timestamp | string | 检查时间戳 |
| version | string | API 版本号 |

**状态码**:
- `200`: 服务正常
- `503`: 服务异常

## 错误码说明

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| INVALID_REQUEST | 400 | 请求参数无效 |
| VALIDATION_ERROR | 422 | 数据验证失败 |
| FILE_TOO_LARGE | 413 | 文件大小超限 |
| UNSUPPORTED_FILE_TYPE | 415 | 不支持的文件类型 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |
| OLLAMA_CONNECTION_ERROR | 500 | Ollama 服务连接失败 |
| MODEL_LOAD_ERROR | 500 | 模型加载失败 |

## 使用示例

### Python 示例

```python
import requests
import json

# 文本检测
def detect_text(text):
    url = "http://localhost:8000/detect/text"
    data = {"text": text}
    
    response = requests.post(url, json=data)
    return response.json()

# 文档检测
def detect_document(file_path):
    url = "http://localhost:8000/detect/document"
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files)
    
    return response.json()

# 使用示例
result = detect_text("测试文本")
print(json.dumps(result, indent=2, ensure_ascii=False))
```

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
    
    return await response.json();
}

// 文档检测
async function detectDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('http://localhost:8000/detect/document', {
        method: 'POST',
        body: formData
    });
    
    return await response.json();
}

// 使用示例
detectText("测试文本").then(result => {
    console.log(result);
});
```

### cURL 示例

```bash
# 文本检测
curl -X POST "http://localhost:8000/detect/text" \
     -H "Content-Type: application/json" \
     -d '{"text":"测试文本"}'

# 文档检测
curl -X POST "http://localhost:8000/detect/document" \
     -F "file=@document.pdf"

# 健康检查
curl -X GET "http://localhost:8000/health"
```

## 性能指标

### 响应时间

| 接口 | 平均响应时间 | 95% 响应时间 |
|------|-------------|-------------|
| 文本检测 | 200ms | 500ms |
| 文档检测 | 1s | 3s |
| 健康检查 | 50ms | 100ms |

### 并发处理

- 最大并发请求数: 100
- 单次请求超时时间: 30s
- 文件上传超时时间: 60s

## 限流策略

当前版本无限流策略，生产环境建议添加：

- 每分钟最大请求数: 1000
- 单 IP 每分钟最大请求数: 100
- 文件上传频率限制: 每分钟 10 次

## 版本历史

### v1.1.0 (2025-01-XX)
- 新增严格模式：跳过规则匹配，直接使用大模型检测
- 优化默认模式：规则匹配快速筛选 + 存疑内容大模型检测
- 新增DOC文件支持：使用antiword工具解析DOC格式
- 新增OCR功能：支持图片文字识别（JPG、PNG、BMP、GIF、TIFF）
- 优化OCR配置：支持中英文混合识别
- 改进错误处理：提供更详细的错误信息

### v1.0.0 (2024-01-01)

- 初始版本发布
- 支持文本和文档检测
- 集成 Ollama LLM
- 提供 Web 界面

## 更新日志

### 2024-01-01
- 修复 Ollama 连接问题
- 优化 LLM 检测一致性
- 升级到 qwen2.5:7b 量化模型
- 改进错误处理机制

## 技术支持

如有 API 使用问题，请通过以下方式联系：

- 邮箱: support@example.com
- GitHub Issues: [项目地址]/issues
- 文档更新: 请提交 Pull Request

---

**文档版本**: v1.0.0  
**最后更新**: 2025年10月
