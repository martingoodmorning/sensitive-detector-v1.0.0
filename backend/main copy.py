from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # 解决前端跨域问题
from pydantic import BaseModel  # 校验请求参数格式
import docx  # 解析docx文档
import PyPDF2  # 解析pdf文档
import os
import json
import requests
from io import BytesIO
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse


# 1. 初始化FastAPI应用
app = FastAPI(title="敏感词检测", version="1.0") 

# 自定义Swagger UI，隐藏指定区域
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    # 先获取默认的Swagger UI HTML
    swagger_html = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"
    )
    # 在HTML末尾添加自定义CSS（通过字符串拼接）
    custom_css = """
    <style>
        .responses-wrapper { display: none !important; }
        .schemas-wrapper { display: none !important; }
    </style>
    """
    combined_html = swagger_html.body.decode() + custom_css# 拼接HTML和CSS并返回
    return HTMLResponse(content=combined_html)  # 使用HTMLResponse返回

# 2. 解决跨域（前端在Windows浏览器，后端在WSL容器，必须允许跨域）
allow_origins_env = os.getenv("CORS_ALLOW_ORIGINS", "*")
allow_origins = [o.strip() for o in allow_origins_env.split(",")] if allow_origins_env else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------- 规则引擎：基础敏感词匹配（Trie树，高效） ----------------------
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class TrieFilter:
    def __init__(self, word_path="/app/sensitive_words.txt"):
        self.root = TrieNode()
        # 加载敏感词库（容器内路径，后续会挂载本地文件）
        if os.path.exists(word_path):
            with open(word_path, "r", encoding="utf-8") as f:
                for word in f:
                    word = word.strip()
                    if word:
                        self.add_word(word)
        else:
            print(f"警告：敏感词库文件 {word_path} 不存在，仅启用大模型检测")

    def add_word(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True

    def detect(self, text):
        """检测文本中的敏感词，返回去重后的列表"""
        results = []
        text_len = len(text)
        for i in range(text_len):
            node = self.root
            for j in range(i, text_len):
                char = text[j]
                if char not in node.children:
                    break
                node = node.children[char]
                if node.is_end:
                    results.append(text[i:j+1])
        return list(set(results))  # 去重

# 初始化规则引擎（加载敏感词库）
# 支持通过环境变量 SENSITIVE_WORDS_PATH 配置路径
_sensitive_words_path = os.getenv("SENSITIVE_WORDS_PATH", "/app/sensitive_words.txt")
trie_filter = TrieFilter(_sensitive_words_path)

# ---------------------- 新增：Ollama API 调用逻辑 ----------------------
def call_ollama_api(text: str) -> str:
    """
    调用 Ollama 本地 API，检测文本是否含敏感内容
    返回："敏感" 或 "正常"（容错处理后）
    """
    # Ollama API 地址与模型名通过环境变量配置
    base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434").rstrip("/")
    model_name = os.getenv("OLLAMA_MODEL", "qwen:1.8b")
    ollama_url = f"{base_url}/api/generate"
    
    # 提示词工程：严格限制输出格式，避免模型返回冗余内容
    prompt = f"""
    任务：判断以下文本是否包含敏感内容（如辱骂、暴力、违法、色情、歧视等），仅输出"敏感"或"正常"两个词，不添加任何解释、标点或额外字符。
    文本内容：{text[:500]}  # 限制文本长度，避免 API 调用超时
    检测结果：
    """
    
    try:
        # 发送 POST 请求到 Ollama API
        response = requests.post(
            ollama_url,
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.1
            },
            timeout=30
        )
        response.raise_for_status()  # 若 HTTP 状态码异常，抛出错误
        result = response.json()
        
        # 提取模型响应，清理空格和换行
        llm_output = result.get("response", "").strip()
        # 容错处理：若模型输出异常，默认返回"正常"
        return llm_output if llm_output in ["敏感", "正常"] else "正常"
    
    except Exception as e:
        # 捕获网络错误、API 错误等，打印日志并返回"正常"（避免服务崩溃）
        print(f"Ollama API 调用失败：{str(e)}")
        return "正常"


# ---------------------- 定义请求参数格式 ----------------------
class TextRequest(BaseModel):
    """文本检测的请求体格式：必须包含text字段"""
    text: str

# ---------------------- 核心API：文本检测 ----------------------
@app.post("/detect/text", summary="文本敏感词检测")
async def detect_text(req: TextRequest):
    # 1. 校验请求参数（文本不能为空）
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="检测文本不能为空")
    
    # 2. 规则引擎检测（快速匹配显式敏感词）
    rule_result = trie_filter.detect(req.text)
    
    # 3. 大模型检测（通过 Ollama 调用本地模型）
    llm_result = call_ollama_api(req.text)
    # 容错：若模型输出异常，默认按"正常"处理
    llm_result = llm_result if llm_result in ["敏感", "正常"] else "正常"

    # 4. 综合结果（规则引擎或大模型任一检测为敏感，最终结果即为敏感）
    final_result = "敏感" if (rule_result or llm_result == "敏感") else "正常"

    # 5. 返回响应
    return {
        "status": "success",
        "data": {
            "original_text": req.text[:100] + "..." if len(req.text) > 100 else req.text,
            "rule_detected": rule_result,  # 规则引擎检测到的敏感词
            "llm_detected": llm_result,    # 大模型检测结果
            "final_result": final_result   # 最终结果
        }
    }

# ---------------------- 核心API：文档检测 ----------------------
@app.post("/detect/document", summary="文档敏感词检测（支持txt/pdf/docx）")
async def detect_document(file: UploadFile = File(...)):
    # 1. 校验文件类型（只允许txt、pdf、docx）
    allowed_types = {
        "text/plain": "txt",
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx"
    }
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型！仅支持：{', '.join(allowed_types.values())}"
        )

    # 2. 读取文件内容（根据文件类型解析）
    content = await file.read()
    text = ""
    try:
        if allowed_types[file.content_type] == "txt":
            # 解析txt（默认UTF-8编码，若乱码可尝试gbk）
            text = content.decode("utf-8", errors="ignore")
        elif allowed_types[file.content_type] == "docx":
            # 解析docx
            doc = docx.Document(BytesIO(content))
            text = "\n".join([para.text for para in doc.paragraphs])
        elif allowed_types[file.content_type] == "pdf":
            # 解析pdf（忽略无法提取的文本）
            reader = PyPDF2.PdfReader(BytesIO(content))
            text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档解析失败：{str(e)}")

    # 3. 校验解析结果（文档内容不能为空）
    if not text.strip():
        raise HTTPException(status_code=400, detail="文档内容为空或无法提取文本")

    # 4. 复用文本检测逻辑（规则引擎 + 大模型）
    rule_result = trie_filter.detect(text)
    # 大模型检测（通过 Ollama 调用本地模型）
    llm_result = call_ollama_api(text)
    llm_result = llm_result if llm_result in ["敏感", "正常"] else "正常"
    final_result = "敏感" if (rule_result or llm_result == "敏感") else "正常"

    # 5. 返回响应
    return {
        "status": "success",
        "data": {
            "filename": file.filename,
            "file_type": allowed_types[file.content_type],
            "text_length": len(text),  # 提取的文本长度
            "rule_detected": rule_result,
            "llm_detected": llm_result,
            "final_result": final_result
        }
    }

# ---------------------- 启动入口（供容器内执行） ----------------------
if __name__ == "__main__":
    import uvicorn
    # 启动UVicorn服务（host=0.0.0.0：允许容器外部访问）
    uvicorn.run(
        app="main:app",
        host="0.0.0.0",
        port=8000,
        workers=1  # 单进程（大模型占用内存高，多进程易OOM）
    )
