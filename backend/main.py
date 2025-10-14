from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # 解决前端跨域问题
from fastapi.staticfiles import StaticFiles  # 静态文件服务
from fastapi.responses import FileResponse  # 文件响应
from pydantic import BaseModel  # 校验请求参数格式
from typing import List, Optional, Dict, Any
import docx  # 解析docx文档
import PyPDF2  # 解析pdf文档
import docx2txt  # 解析doc文档
import pytesseract  # OCR文字识别
from PIL import Image  # 图像处理
import os
import json
import requests
from io import BytesIO
import glob
from datetime import datetime
import time
import subprocess  # 用于调用antiword工具
import tempfile  # 用于创建临时文件

# 1. 初始化FastAPI应用
app = FastAPI(title="敏感词检测", version="1.0", docs_url="/api/docs", redoc_url="/api/redoc")

# 根路径重定向到前端页面
@app.get("/", include_in_schema=False)
async def read_root():
    return FileResponse("/app/frontend/index.html")

# API文档路径
@app.get("/docs", include_in_schema=False)
async def read_docs():
    return FileResponse("/app/frontend/index.html")

# 挂载静态文件目录（容器内路径）- 必须在路由之后
app.mount("/static", StaticFiles(directory="/app/frontend"), name="static")

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

# ---------------------- 敏感词库管理 ----------------------
class WordLibraryManager:
    """敏感词库管理器"""
    
    def __init__(self, base_path="/app/word_libraries"):
        self.base_path = base_path
        self.ensure_base_directory()
    
    def ensure_base_directory(self):
        """确保基础目录存在"""
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path, exist_ok=True)
    
    def get_library_list(self) -> List[Dict[str, Any]]:
        """获取所有敏感词库列表"""
        libraries = []
        
        # 扫描所有.txt文件
        pattern = os.path.join(self.base_path, "*.txt")
        for file_path in glob.glob(pattern):
            filename = os.path.basename(file_path)
            name = os.path.splitext(filename)[0]
            
            # 获取文件信息
            stat = os.stat(file_path)
            word_count = self._count_words_in_file(file_path)
            
            libraries.append({
                "id": name,
                "name": name,
                "filename": filename,
                "path": file_path,
                "word_count": word_count,
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "size": stat.st_size
            })
        
        return sorted(libraries, key=lambda x: x["name"])
    
    def _count_words_in_file(self, file_path: str) -> int:
        """统计文件中的敏感词数量"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return len([line.strip() for line in f if line.strip()])
        except:
            return 0
    
    def create_library(self, name: str, words: List[str]) -> Dict[str, Any]:
        """创建新的敏感词库"""
        filename = f"{name}.txt"
        file_path = os.path.join(self.base_path, filename)
        
        # 检查是否已存在
        if os.path.exists(file_path):
            raise HTTPException(status_code=400, detail=f"敏感词库 '{name}' 已存在")
        
        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            for word in words:
                f.write(word.strip() + "\n")
        
        return {
            "id": name,
            "name": name,
            "filename": filename,
            "path": file_path,
            "word_count": len(words),
            "created_time": datetime.now().isoformat(),
            "modified_time": datetime.now().isoformat(),
            "size": os.path.getsize(file_path)
        }
    
    def delete_library(self, name: str) -> bool:
        """删除敏感词库"""
        filename = f"{name}.txt"
        file_path = os.path.join(self.base_path, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"敏感词库 '{name}' 不存在")
        
        os.remove(file_path)
        return True
    
    def get_library_content(self, name: str) -> List[str]:
        """获取敏感词库内容"""
        filename = f"{name}.txt"
        file_path = os.path.join(self.base_path, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"敏感词库 '{name}' 不存在")
        
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    
    def update_library(self, name: str, words: List[str]) -> Dict[str, Any]:
        """更新敏感词库"""
        filename = f"{name}.txt"
        file_path = os.path.join(self.base_path, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"敏感词库 '{name}' 不存在")
        
        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            for word in words:
                f.write(word.strip() + "\n")
        
        return {
            "id": name,
            "name": name,
            "filename": filename,
            "path": file_path,
            "word_count": len(words),
            "modified_time": datetime.now().isoformat(),
            "size": os.path.getsize(file_path)
        }

# OCR配置和预处理函数
def preprocess_image_for_ocr(image):
    """预处理图片以提高OCR识别率"""
    # 转换为RGB模式
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # 可以添加更多预处理步骤，如：
    # - 调整对比度
    # - 去噪
    # - 二值化
    # - 倾斜校正等
    
    return image

def get_ocr_config():
    """获取OCR配置参数"""
    return {
        'lang': 'chi_sim+eng',  # 支持中文简体和英文
        'config': '--psm 6 --oem 3',  # PSM 6: 统一文本块, OEM 3: 默认引擎
        'char_whitelist': None  # 移除字符白名单限制，允许识别所有字符
    }

# 初始化敏感词库管理器
word_lib_manager = WordLibraryManager()

# 检测词库持久化管理
class DetectionLibraryManager:
    """检测词库持久化管理器"""
    
    def __init__(self, config_path="/app/detection_config.json"):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self):
        """加载检测配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载检测配置失败: {e}")
        
        # 默认配置
        return {
            "used_libraries": [],
            "last_updated": None,
            "word_count": 0
        }
    
    def save_config(self, used_libraries, word_count):
        """保存检测配置"""
        try:
            config = {
                "used_libraries": used_libraries,
                "last_updated": datetime.now().isoformat(),
                "word_count": word_count
            }
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            # 更新内存中的配置
            self.config = config
            print(f"检测配置已保存: 使用 {len(used_libraries)} 个词库，共 {word_count} 个敏感词")
        except Exception as e:
            print(f"保存检测配置失败: {e}")
    
    def reload_config(self):
        """重新加载配置文件"""
        print(f"开始重新加载配置文件: {self.config_path}")
        old_config = self.config.copy() if self.config else {}
        self.config = self.load_config()
        print(f"重新加载检测配置完成:")
        print(f"  旧配置: {old_config}")
        print(f"  新配置: {self.config}")
        print(f"  配置文件是否存在: {os.path.exists(self.config_path)}")
    
    def get_used_libraries(self):
        """获取当前使用的词库列表"""
        return self.config.get("used_libraries", [])
    
    def get_word_count(self):
        """获取当前词库的敏感词数量"""
        return self.config.get("word_count", 0)

# 初始化检测词库管理器
detection_lib_manager = DetectionLibraryManager()

# 模型状态跟踪
model_warm_up_status = {
    "is_warmed_up": False,
    "warm_up_time": None,
    "last_call_time": None
}


# ---------------------- 三步匹配规则引擎 ----------------------

# 第一步：AC自动机初筛 - 快速过滤无风险文本，标记可疑文本
class ACNode:
    def __init__(self):
        self.children = {}
        self.fail = None
        self.is_end = False
        self.word = None
        self.output = []

class ACAutomaton:
    def __init__(self, words):
        self.root = ACNode()
        self.words = words
        # 添加敏感词到AC自动机
        for word in words:
                        self.add_word(word)
        self.build_fail_links()

    def add_word(self, word):
        """添加敏感词到AC自动机"""
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = ACNode()
            node = node.children[char]
        node.is_end = True
        node.word = word
        node.output.append(word)

    def build_fail_links(self):
        """构建失败链接"""
        from collections import deque
        queue = deque()
        
        # 第一层节点的fail指针指向root
        for child in self.root.children.values():
            child.fail = self.root
            queue.append(child)
        
        # 构建其他层的fail指针
        while queue:
            current = queue.popleft()
            for char, child in current.children.items():
                queue.append(child)
                fail_node = current.fail
                while fail_node and char not in fail_node.children:
                    fail_node = fail_node.fail
                if fail_node:
                    child.fail = fail_node.children.get(char, self.root)
                else:
                    child.fail = self.root
                # 合并输出
                child.output.extend(child.fail.output)

    def search(self, text):
        """AC自动机搜索，返回可疑文本片段和匹配的敏感词"""
        results = []
        suspicious_segments = []
        current = self.root
        
        for i, char in enumerate(text):
            # 沿着fail链找到匹配的节点
            while current and char not in current.children:
                current = current.fail
            if current:
                current = current.children.get(char, self.root)
            else:
                current = self.root
            
            # 检查当前节点及其fail链上的输出
            temp = current
            while temp:
                for word in temp.output:
                    results.append(word)
                    # 标记可疑文本片段（向前扩展一些字符以捕获上下文）
                    start = max(0, i - len(word) - 5)
                    end = min(len(text), i + 5)
                    suspicious_segments.append(text[start:end])
                temp = temp.fail
        
        return list(set(results)), list(set(suspicious_segments))

# 第二步：DFA检测 - 对可疑文本进行精准验证
class DFAFilter:
    def __init__(self, words):
        self.words = words
        self.dfa = self.build_dfa()

    def build_dfa(self):
        """构建DFA状态机"""
        dfa = {}
        state = 0
        
        for word in self.words:
            current_state = 0
            for char in word:
                if (current_state, char) not in dfa:
                    state += 1
                    dfa[(current_state, char)] = state
                current_state = dfa[(current_state, char)]
            # 标记终态
            dfa[(current_state, '')] = -1  # -1表示终态
        
        return dfa

    def precise_match(self, text, suspicious_segments):
        """对可疑文本片段进行DFA精准匹配"""
        precise_results = []
        
        for segment in suspicious_segments:
            for i in range(len(segment)):
                current_state = 0
                for j in range(i, len(segment)):
                    char = segment[j]
                    if (current_state, char) in self.dfa:
                        current_state = self.dfa[(current_state, char)]
                        if (current_state, '') in self.dfa:  # 到达终态
                            precise_results.append(segment[i:j+1])
                    else:
                        break
        
        return list(set(precise_results))

# 文本预处理 - 统一字符格式，消除"无意义变体"
class TextPreprocessor:
    def __init__(self):
        """文本预处理器，用于统一字符格式，消除无意义变体"""
        self.setup_normalization_rules()
    
    def setup_normalization_rules(self):
        """设置字符归一化规则"""
        # 全角转半角映射
        self.full_to_half = {
            'Ａ': 'A', 'Ｂ': 'B', 'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E', 'Ｆ': 'F', 'Ｇ': 'G', 'Ｈ': 'H',
            'Ｉ': 'I', 'Ｊ': 'J', 'Ｋ': 'K', 'Ｌ': 'L', 'Ｍ': 'M', 'Ｎ': 'N', 'Ｏ': 'O', 'Ｐ': 'P',
            'Ｑ': 'Q', 'Ｒ': 'R', 'Ｓ': 'S', 'Ｔ': 'T', 'Ｕ': 'U', 'Ｖ': 'V', 'Ｗ': 'W', 'Ｘ': 'X',
            'Ｙ': 'Y', 'Ｚ': 'Z',
            'ａ': 'a', 'ｂ': 'b', 'ｃ': 'c', 'ｄ': 'd', 'ｅ': 'e', 'ｆ': 'f', 'ｇ': 'g', 'ｈ': 'h',
            'ｉ': 'i', 'ｊ': 'j', 'ｋ': 'k', 'ｌ': 'l', 'ｍ': 'm', 'ｎ': 'n', 'ｏ': 'o', 'ｐ': 'p',
            'ｑ': 'q', 'ｒ': 'r', 'ｓ': 's', 'ｔ': 't', 'ｕ': 'u', 'ｖ': 'v', 'ｗ': 'w', 'ｘ': 'x',
            'ｙ': 'y', 'ｚ': 'z',
            '０': '0', '１': '1', '２': '2', '３': '3', '４': '4', '５': '5', '６': '6', '７': '7',
            '８': '8', '９': '9',
            '（': '(', '）': ')', '［': '[', '］': ']', '｛': '{', '｝': '}', '＜': '<', '＞': '>',
            '，': ',', '。': '.', '；': ';', '：': ':', '？': '?', '！': '!', '～': '~', '＠': '@',
            '＃': '#', '＄': '$', '％': '%', '＾': '^', '＆': '&', '＊': '*', '－': '-', '＿': '_',
            '＋': '+', '＝': '=', '｜': '|', '＼': '\\', '／': '/', '　': ' '
        }
        
        # 繁体转简体映射（常用字）
        self.traditional_to_simplified = {
            '學': '学', '習': '习', '經': '经', '濟': '济', '發': '发', '現': '现', '實': '实',
            '際': '际', '電': '电', '腦': '脑', '網': '网', '絡': '络', '資': '资', '訊': '讯',
            '話': '话', '視': '视', '影': '影', '軟': '软', '體': '体', '硬': '硬', '系': '系',
            '統': '统', '件': '件', '程': '程', '式': '式', '設': '设', '計': '计', '開': '开',
            '測': '测', '試': '试', '維': '维', '護': '护', '管': '管', '理': '理', '服': '服',
            '務': '务', '產': '产', '品': '品', '質': '质', '量': '量', '標': '标', '準': '准',
            '規': '规', '範': '范', '誌': '志', '識': '识', '別': '别', '區': '区', '分': '分',
            '類': '类', '型': '型', '種': '种', '級': '级', '層': '层', '次': '次', '順': '顺',
            '序': '序', '排': '排', '列': '列', '組': '组', '合': '合', '配': '配', '置': '置',
            '定': '定', '選': '选', '擇': '择', '決': '决', '確': '确', '認': '认', '證': '证',
            '驗': '验', '明': '明', '據': '据', '書': '书', '照': '照', '券': '券', '票': '票'
        }
    
    def normalize_text(self, text):
        """文本归一化处理"""
        if not text:
            return text
        
        # 1. 全角转半角
        normalized = text
        for full_char, half_char in self.full_to_half.items():
            normalized = normalized.replace(full_char, half_char)
        
        # 2. 繁体转简体
        for trad_char, simp_char in self.traditional_to_simplified.items():
            normalized = normalized.replace(trad_char, simp_char)
        
        # 3. 移除特殊符号（保留中文字符、英文字母、数字）
        cleaned = ""
        for char in normalized:
            if (char.isalnum() or  # 字母或数字
                '\u4e00' <= char <= '\u9fff'):  # 中文字符
                cleaned += char
        
        return cleaned
    
    def preprocess_text(self, text):
        """预处理文本，返回归一化文本"""
        return self.normalize_text(text)

# 规则匹配引擎整合（预处理+AC+DFA）
class ThreeStepFilter:
    def __init__(self, word_paths=None):
        if word_paths is None:
            # 默认使用word_libraries目录中的所有词库
            word_paths = []
            base_path = "/app/word_libraries"
            if os.path.exists(base_path):
                for filename in os.listdir(base_path):
                    if filename.endswith('.txt'):
                        word_paths.append(os.path.join(base_path, filename))
        self.word_paths = word_paths
        self.words = []
        self._load_words()
        # 文本预处理器
        self.text_preprocessor = TextPreprocessor()
        # 第一步：AC自动机
        self.ac_automaton = ACAutomaton(self.words)
        # 第二步：DFA检测
        self.dfa_filter = DFAFilter(self.words)

    def _load_words(self):
        """加载敏感词并自动去重"""
        all_words = []
        word_sources = {}  # 记录每个词来自哪些词库
        
        for word_path in self.word_paths:
            if os.path.exists(word_path):
                library_name = os.path.splitext(os.path.basename(word_path))[0]
                with open(word_path, "r", encoding="utf-8") as f:
                    for word in f:
                        word = word.strip()
                        if word:
                            all_words.append(word)
                            # 记录词库来源
                            if word not in word_sources:
                                word_sources[word] = []
                            word_sources[word].append(library_name)
            else:
                print(f"警告：敏感词库文件 {word_path} 不存在")
        
        # 去重并统计
        original_count = len(all_words)
        self.words = list(set(all_words))  # 自动去重
        deduplicated_count = len(self.words)
        removed_count = original_count - deduplicated_count
        
        # 打印去重统计信息
        if removed_count > 0:
            print(f"词库去重完成：原始 {original_count} 个词，去重后 {deduplicated_count} 个词，删除重复词 {removed_count} 个")
            
            # 显示重复词及其来源（仅显示前10个）
            duplicates = [word for word, sources in word_sources.items() if len(sources) > 1]
            if duplicates:
                print("重复词示例（前10个）:")
                for i, word in enumerate(duplicates[:10]):
                    sources = word_sources[word]
                    print(f"  '{word}' 出现在: {', '.join(sources)}")
                if len(duplicates) > 10:
                    print(f"  ... 还有 {len(duplicates) - 10} 个重复词")
        else:
            print(f"词库加载完成：共 {deduplicated_count} 个词，无重复词")

    def reload_with_libraries(self, library_names: List[str]):
        """重新加载指定的敏感词库"""
        word_paths = []
        for name in library_names:
            file_path = os.path.join(word_lib_manager.base_path, f"{name}.txt")
            if os.path.exists(file_path):
                word_paths.append(file_path)
        
        if word_paths:
            self.word_paths = word_paths
            self._load_words()
            # 重新初始化各个组件
            self.text_preprocessor = TextPreprocessor()
            self.ac_automaton = ACAutomaton(self.words)
            self.dfa_filter = DFAFilter(self.words)

    def detect(self, text, fast_mode=False):
        """规则匹配检测（预处理+AC+DFA）"""
        start_time = time.time()
        
        # 文本预处理：归一化字符格式
        preprocess_start = time.time()
        normalized_text = self.text_preprocessor.preprocess_text(text)
        preprocess_time = time.time() - preprocess_start
        
        # 第一步：AC自动机初筛（对归一化文本）
        ac_start = time.time()
        ac_results, suspicious_segments = self.ac_automaton.search(normalized_text)
        ac_time = time.time() - ac_start
        
        # 第二步：DFA检测（对原始文本的可疑片段）
        dfa_start = time.time()
        dfa_results = self.dfa_filter.precise_match(text, suspicious_segments)
        dfa_time = time.time() - dfa_start
        
        # 合并所有结果
        all_results = list(set(ac_results + dfa_results))
        
        total_time = time.time() - start_time
        
        return {
            'ac_results': ac_results,
            'dfa_results': dfa_results,
            'preprocess_results': [],  # 预处理结果（用于兼容性）
            'all_results': all_results,
            'suspicious_segments': suspicious_segments,
            'word_count': len(self.words),  # 添加词库统计信息
            'fast_mode': fast_mode,  # 是否使用快速模式
            'normalized_text': normalized_text,  # 归一化后的文本
            'timing': {
                'preprocess_time': round(preprocess_time * 1000, 2),  # 预处理用时
                'ac_time': round(ac_time * 1000, 2),      # 毫秒
                'dfa_time': round(dfa_time * 1000, 2),    # 毫秒
                'total_time': round(total_time * 1000, 2)  # 毫秒
            }
        }

# 初始化三步匹配规则引擎（加载敏感词库）
# 默认使用word_libraries中的词库

# 模型预热函数

def call_ollama_api(text: str) -> str:
    """
    调用 Ollama 本地 API，检测文本是否含敏感内容
    返回："敏感" 或 "正常"（容错处理后）
    """
    
    # 记录调用时间
    call_start_time = time.time()
    model_warm_up_status["last_call_time"] = call_start_time
    
    # 检查是否是冷启动
    if not model_warm_up_status["is_warmed_up"]:
        print("⚠️  检测到模型冷启动，可能需要较长时间...")
    elif model_warm_up_status["warm_up_time"]:
        time_since_warmup = call_start_time - model_warm_up_status["warm_up_time"]
        if time_since_warmup > 300:  # 5分钟后认为可能冷启动
            print(f"⚠️  距离预热已过{time_since_warmup:.0f}秒，可能触发冷启动...")
    
    # Ollama API 地址与模型名通过环境变量配置
    # 在WSL环境中，使用host.docker.internal可能无法解析，尝试多种方式
    base_url = os.getenv("OLLAMA_BASE_URL", "http://172.17.0.1:11434").rstrip("/")
    model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct-q4_K_M")
    ollama_url = f"{base_url}/api/generate"
    
    print(f"尝试调用Ollama API: {ollama_url}")
    print(f"使用模型: {model_name}")
    
    # 提示词工程：严格约束输出，确保一致性
    prompt = f"""
你是专业的内容安全检测系统。请严格按照以下规则进行判断：

【敏感内容标准】
包含以下任何一类内容即判定为敏感：
1. 辱骂词汇（如：白痴、傻逼、去死等）
2. 暴力威胁（如：杀了你、打你、伤害等）
3. 违法内容（如：毒品、犯罪、诈骗等）
4. 色情内容（如：性暗示、色情描述等）
5. 歧视内容（如：种族歧视、性别歧视等）
6. 政治敏感内容（如：法西斯、纳粹、极端主义、恐怖主义、分裂主义等）
7. 仇恨言论（如：煽动仇恨、暴力、极端的言论）
8. 虚假信息（如：虚假新闻、虚假宣传、虚假广告、谣言等）
9. 欺凌言论（如：霸凌、冷暴力、孤立的言论）
10. 隐蔽的敏感内容（如：反动内容、色情内容、暴力内容、违法内容等，但需要通过上下文才能判断）
【检测文本】
{text[:10000]}

【判断规则】
- 如果文本包含上述任何一类敏感内容，回答：敏感
- 如果文本是正常的日常对话、学术讨论、新闻描述等，回答：正常
- 对于涉及敏感词汇但属于学术研究、历史讨论、新闻报道等正当用途，回答：正常
- 对于明确表达支持、宣扬、美化敏感内容的，回答：敏感

【输出要求】
请严格按照以下格式输出，不要添加任何其他内容：
敏感
或
正常
    """
    
    try:
        # 发送 POST 请求到 Ollama API
        print(f"发送请求到: {ollama_url}")
        response = requests.post(
            ollama_url,
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "temperature": 0
            },
            timeout=30
        )
        print(f"API响应状态码: {response.status_code}")
        response.raise_for_status()  # 若 HTTP 状态码异常，抛出错误
        result = response.json()
        print(f"API响应内容: {result}")
        
        # 提取模型响应，清理空格和换行
        llm_output = result.get("response", "").strip()
        print(f"模型输出: '{llm_output}'")
        # 容错处理：若模型输出异常，默认返回"正常"
        final_result = llm_output if llm_output in ["敏感", "正常"] else "正常"
        print(f"最终结果: {final_result}")
        return final_result
    
    except Exception as e:
        # 捕获网络错误、API 错误等，打印日志并返回"正常"（避免服务崩溃）
        print(f"Ollama API 调用失败：{str(e)}")
        print(f"异常类型: {type(e).__name__}")
        return "正常"

def warm_up_model():
    """预热Ollama模型，避免第一次调用时的冷启动延迟"""
    try:
        print("正在预热Ollama模型...")
        
        # 多次预热，确保模型完全加载
        warm_up_texts = [
            "这是一个测试文本，用于预热模型。",
            "今天天气很好，适合出门散步。",
            "请帮我分析一下这个文本的内容。"
        ]
        
        for i, text in enumerate(warm_up_texts, 1):
            print(f"预热第{i}次...")
            result = call_ollama_api(text)
            print(f"第{i}次预热完成，结果: {result}")
            
            # 短暂延迟，让模型稳定
            time.sleep(0.5)
        
        print("模型预热全部完成！")
        
        # 更新预热状态
        model_warm_up_status["is_warmed_up"] = True
        model_warm_up_status["warm_up_time"] = time.time()
        
        return True
    except Exception as e:
        print(f"模型预热失败: {e}")
        return False


# 启动时加载保存的检测词库配置
def initialize_detection_filter():
    """初始化检测过滤器"""
    used_libraries = detection_lib_manager.get_used_libraries()
    
    # 预热Ollama模型
    warm_up_model()
    
    if used_libraries:
        print(f"加载保存的检测词库配置: {', '.join(used_libraries)}")
        # 使用保存的词库配置
        word_paths = []
        for name in used_libraries:
            file_path = os.path.join(word_lib_manager.base_path, f"{name}.txt")
            if os.path.exists(file_path):
                word_paths.append(file_path)
            else:
                print(f"警告：保存的词库 '{name}' 文件不存在，跳过")
        
        if word_paths:
            return ThreeStepFilter(word_paths)
        else:
            print("所有保存的词库文件都不存在，使用默认词库")
    
    # 使用word_libraries中的词库作为默认词库
    print("使用word_libraries中的词库作为默认词库")
    word_lib_paths = []
    
    # 扫描word_libraries目录中的所有词库
    if os.path.exists(word_lib_manager.base_path):
        for filename in os.listdir(word_lib_manager.base_path):
            if filename.endswith('.txt'):
                file_path = os.path.join(word_lib_manager.base_path, filename)
                word_lib_paths.append(file_path)
                print(f"找到词库: {filename}")
    
    if word_lib_paths:
        print(f"使用 {len(word_lib_paths)} 个词库作为默认词库")
        return ThreeStepFilter(word_lib_paths)
    else:
        print("word_libraries目录为空，创建默认词库")
        # 创建默认词库
        default_library_path = os.path.join(word_lib_manager.base_path, "默认词库.txt")
        with open(default_library_path, "w", encoding="utf-8") as f:
            f.write("暴力\n辱骂\n违法\n色情\n赌博\n毒品\n法西斯\n纳粹\n极端主义\n恐怖主义\n")
        print(f"已创建默认词库: {default_library_path}")
        return ThreeStepFilter([default_library_path])

three_step_filter = initialize_detection_filter()

# ---------------------- 新增：Ollama API 调用逻辑 ----------------------


# ---------------------- 定义请求参数格式 ----------------------
class TextRequest(BaseModel):
    """文本检测的请求体格式：必须包含text字段"""
    text: str
    fast_mode: Optional[bool] = False  # 快速模式：已废弃，建议使用默认模式
    strict_mode: Optional[bool] = False  # 严格模式：跳过规则匹配，直接使用大模型

class LibraryCreateRequest(BaseModel):
    """创建敏感词库的请求体格式"""
    name: str
    words: List[str]

class LibraryUpdateRequest(BaseModel):
    """更新敏感词库的请求体格式"""
    words: List[str]

# ---------------------- 敏感词库管理API ----------------------
@app.get("/word-libraries", summary="获取敏感词库列表")
async def get_word_libraries():
    """获取所有敏感词库列表"""
    libraries = word_lib_manager.get_library_list()
    return {
        "status": "success",
        "data": libraries
    }

@app.post("/word-libraries", summary="创建敏感词库")
async def create_word_library(req: LibraryCreateRequest):
    """创建新的敏感词库"""
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="词库名称不能为空")
    
    if not req.words:
        raise HTTPException(status_code=400, detail="敏感词列表不能为空")
    
    library = word_lib_manager.create_library(req.name.strip(), req.words)
    return {
        "status": "success",
        "data": library
    }

@app.get("/word-libraries/{name}", summary="获取敏感词库内容")
async def get_word_library_content(name: str):
    """获取指定敏感词库的内容"""
    words = word_lib_manager.get_library_content(name)
    return {
        "status": "success",
        "data": {
            "name": name,
            "words": words,
            "word_count": len(words)
        }
    }

@app.put("/word-libraries/{name}", summary="更新敏感词库")
async def update_word_library(name: str, req: LibraryUpdateRequest):
    """更新指定敏感词库的内容"""
    if not req.words:
        raise HTTPException(status_code=400, detail="敏感词列表不能为空")
    
    library = word_lib_manager.update_library(name, req.words)
    return {
        "status": "success",
        "data": library
    }

@app.delete("/word-libraries/{name}", summary="删除敏感词库")
async def delete_word_library(name: str):
    """删除指定的敏感词库"""
    word_lib_manager.delete_library(name)
    return {
        "status": "success",
        "message": f"敏感词库 '{name}' 已删除"
    }

@app.post("/detection-libraries/update", summary="更新检测词库配置")
async def update_detection_libraries(req: dict):
    """更新检测词库配置"""
    library_names = req.get("library_names", [])
    
    if not library_names:
        # 清空检测词库配置，使用默认词库
        detection_lib_manager.save_config([], 0)
        three_step_filter.reload_with_libraries([])
        return {
            "status": "success",
            "message": "已清空检测词库配置，使用默认词库",
            "data": {
                "used_libraries": [],
                "word_count": len(three_step_filter.words)
            }
        }
    
    # 验证词库是否存在
    valid_libraries = []
    for name in library_names:
        file_path = os.path.join(word_lib_manager.base_path, f"{name}.txt")
        if os.path.exists(file_path):
            valid_libraries.append(name)
        else:
            print(f"警告：词库 '{name}' 不存在，跳过")
    
    if not valid_libraries:
        return {
            "status": "error",
            "message": "没有找到有效的词库"
        }
    
    # 更新检测词库
    three_step_filter.reload_with_libraries(valid_libraries)
    
    # 保存配置
    detection_lib_manager.save_config(valid_libraries, len(three_step_filter.words))
    
    return {
        "status": "success",
        "message": f"检测词库已更新，使用 {len(valid_libraries)} 个词库",
        "data": {
            "used_libraries": valid_libraries,
            "word_count": len(three_step_filter.words)
        }
    }

@app.get("/detection-libraries/status", summary="获取检测词库状态")
async def get_detection_libraries_status():
    """获取当前检测词库状态"""
    print("=== API调用: 获取检测词库状态 ===")
    
    # 强制重新加载配置文件
    try:
        with open("/app/detection_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        print(f"直接从文件读取配置: {config}")
        
        used_libraries = config.get("used_libraries", [])
        word_count = config.get("word_count", 0)
        last_updated = config.get("last_updated")
        
        print(f"返回的词库: {used_libraries}")
        print(f"返回的词库数量: {len(used_libraries)}")
        print("=== API调用结束 ===")
        
        return {
            "status": "success",
            "data": {
                "used_libraries": used_libraries,
                "word_count": word_count,
                "last_updated": last_updated
            }
        }
    except Exception as e:
        print(f"读取配置文件失败: {e}")
        return {
            "status": "error",
            "message": f"读取配置文件失败: {str(e)}"
        }

# ---------------------- 核心API：文本检测 ----------------------
@app.post("/detect/text", summary="文本敏感词检测")
async def detect_text(req: TextRequest):
    # 1. 校验请求参数（文本不能为空）
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="检测文本不能为空")
    
    # 调试日志
    print(f"🔍 调试信息: strict_mode={req.strict_mode}, fast_mode={req.fast_mode}")
    
    # 2. 检查是否为严格模式
    if req.strict_mode:
        # 严格模式：跳过规则匹配，直接使用大模型检测
        llm_start = time.time()
        llm_result = call_ollama_api(req.text)
        llm_time = time.time() - llm_start
        # 容错：若模型输出异常，默认按"正常"处理
        llm_result = llm_result if llm_result in ["敏感", "正常"] else "正常"
        final_result = llm_result
        
        # 返回严格模式结果
        return {
            "status": "success",
            "data": {
                "original_text": req.text[:100] + "..." if len(req.text) > 100 else req.text,
                "rule_detection": {
                    "ac_results": [],
                    "dfa_results": [],
                    "preprocess_results": [],
                    "all_results": [],
                    "suspicious_segments": [],
                    "word_count": 0,
                    "normalized_text": "",
                    "timing": {"preprocess_time": 0, "ac_time": 0, "dfa_time": 0, "total_time": 0}
                },
                "llm_detected": llm_result,
                "llm_time": round(llm_time * 1000, 2),
                "final_result": final_result,
                "detection_flow": "strict_mode"
            }
        }
    
    # 3. 普通模式：使用规则匹配快速筛选 + 存疑内容大模型检测
    rule_result = three_step_filter.detect(req.text, fast_mode=req.fast_mode)
    
    # 4. 判断是否需要大模型检测（规则匹配快速筛选 + 存疑内容大模型检测）
    rule_has_sensitive = bool(rule_result['all_results'])  # 规则匹配是否发现敏感词
    
    if rule_has_sensitive:
        # 仅对规则匹配出敏感词的文本进行大模型检测
        llm_start = time.time()
        llm_result = call_ollama_api(req.text)
        llm_time = time.time() - llm_start
        # 容错：若模型输出异常，默认按"正常"处理
        llm_result = llm_result if llm_result in ["敏感", "正常"] else "正常"
        final_result = llm_result  # 大模型检测结果即为最终结果
    else:
        # 规则匹配无敏感词，直接判定为正常
        llm_result = "正常"
        llm_time = 0
        final_result = "正常"

    # 4. 返回响应
    return {
        "status": "success",
        "data": {
            "original_text": req.text[:100] + "..." if len(req.text) > 100 else req.text,
            "rule_detection": {
                "ac_results": rule_result['ac_results'],           # AC自动机初筛结果
                "dfa_results": rule_result['dfa_results'],         # DFA检测结果
                "preprocess_results": rule_result['preprocess_results'],  # 预处理结果
                "all_results": rule_result['all_results'],         # 合并后的所有敏感词
                "suspicious_segments": rule_result['suspicious_segments'],  # 可疑文本片段
                "word_count": rule_result['word_count'],           # 词库统计信息
                "normalized_text": rule_result['normalized_text'], # 归一化后的文本
                "timing": rule_result['timing']                    # 规则匹配用时
            },
            "llm_detected": llm_result,    # 大模型检测结果
            "llm_time": round(llm_time * 1000, 2),  # 大模型检测用时（毫秒）
            "final_result": final_result,  # 最终结果
            "detection_flow": "rule_only" if not rule_has_sensitive else "rule_then_llm"  # 检测流程：规则匹配快速筛选 + 存疑内容大模型检测
        }
    }

# ---------------------- 模型管理API ----------------------
@app.get("/model-status", summary="获取模型状态")
async def get_model_status():
    """获取大模型预热状态"""
    current_time = time.time()
    
    status_info = {
        "is_warmed_up": model_warm_up_status["is_warmed_up"],
        "warm_up_time": model_warm_up_status["warm_up_time"],
        "last_call_time": model_warm_up_status["last_call_time"],
        "current_time": current_time
    }
    
    if model_warm_up_status["warm_up_time"]:
        time_since_warmup = current_time - model_warm_up_status["warm_up_time"]
        status_info["time_since_warmup"] = round(time_since_warmup, 2)
        status_info["warmup_status"] = "active" if time_since_warmup < 300 else "stale"
    else:
        status_info["time_since_warmup"] = None
        status_info["warmup_status"] = "not_warmed"
    
    return {
        "status": "success",
        "data": status_info
    }

@app.post("/warm-up-model", summary="预热Ollama模型")
async def warm_up_model_endpoint():
    """预热Ollama模型，减少第一次调用的延迟"""
    try:
        success = warm_up_model()
        if success:
            return {
                "status": "success",
                "message": "模型预热成功"
            }
        else:
            return {
                "status": "error", 
                "message": "模型预热失败"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"模型预热异常: {str(e)}"
    }

# ---------------------- 核心API：文档检测 ----------------------
@app.post("/detect/document", summary="文档敏感词检测（支持txt/pdf/docx/doc/图片OCR，严格模式）")
async def detect_document(file: UploadFile = File(...)):
    # 1. 校验文件类型（支持多种格式）
    allowed_types = {
        "text/plain": "txt",
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/msword": "doc",  # DOC格式
        "image/jpeg": "jpg", "image/jpg": "jpg", "image/png": "png", 
        "image/bmp": "bmp", "image/gif": "gif", "image/tiff": "tiff"  # 图片格式（OCR）
    }
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型！支持：TXT、PDF、DOCX、DOC、图片格式（OCR）"
        )

    # 1.1 校验文件大小（限制10MB）
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大！文件大小不能超过10MB，当前文件大小：{file.size / (1024 * 1024):.2f}MB"
        )

    # 2. 读取文件内容（根据文件类型解析）
    content = await file.read()
    text = ""
    file_type = allowed_types[file.content_type]
    
    try:
        if file_type == "txt":
            # 解析txt（默认UTF-8编码，若乱码可尝试gbk）
            text = content.decode("utf-8", errors="ignore")
        elif file_type == "docx":
            # 解析docx
            doc = docx.Document(BytesIO(content))
            text = "\n".join([para.text for para in doc.paragraphs])
        elif file_type == "pdf":
            # 解析pdf（忽略无法提取的文本）
            reader = PyPDF2.PdfReader(BytesIO(content))
            text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif file_type == "doc":
            # 解析doc - 使用antiword工具
            try:
                # 创建临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix='.doc') as temp_file:
                    temp_file.write(content)
                    temp_file_path = temp_file.name
                
                try:
                    # 使用antiword工具解析DOC文件
                    result = subprocess.run(
                        ['antiword', temp_file_path],
                        capture_output=True,
                        text=True,
                        timeout=30  # 30秒超时
                    )
                    
                    if result.returncode == 0:
                        text = result.stdout
                        if not text.strip():
                            raise Exception("antiword无法从DOC文件中提取文本内容")
                    else:
                        raise Exception(f"antiword执行失败：{result.stderr}")
                        
                finally:
                    # 清理临时文件
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass
                        
            except FileNotFoundError:
                raise HTTPException(
                    status_code=500,
                    detail="antiword工具未安装。请重新构建Docker镜像以确保antiword工具已正确安装。"
                )
            except subprocess.TimeoutExpired:
                raise HTTPException(
                    status_code=500,
                    detail="DOC文件解析超时，文件可能过大或格式异常。"
                )
            except Exception as doc_error:
                raise HTTPException(
                    status_code=400,
                    detail=f"DOC文件解析失败：{str(doc_error)}。建议将DOC文件转换为DOCX格式后重新上传。"
                )
        elif file_type in ["jpg", "png", "bmp", "gif", "tiff"]:
            # OCR文字识别 - 使用pytesseract + Tesseract OCR引擎
            try:
                # 打开图片
                image = Image.open(BytesIO(content))
                
                # 图片预处理以提高OCR识别率
                processed_image = preprocess_image_for_ocr(image)
                
                # 获取OCR配置
                ocr_config = get_ocr_config()
                
                # 构建OCR配置字符串
                if ocr_config['char_whitelist']:
                    full_config = f"{ocr_config['config']} -c tessedit_char_whitelist={ocr_config['char_whitelist']}"
                else:
                    full_config = ocr_config['config']
                
                # 执行OCR识别
                text = pytesseract.image_to_string(
                    processed_image, 
                    lang=ocr_config['lang'], 
                    config=full_config
                )
                
                # 清理识别结果
                text = text.strip()
                
                # 添加OCR识别结果调试信息
                print(f"OCR识别结果: '{text}'")
                print(f"OCR识别结果长度: {len(text)}")
                
                # 如果识别结果为空，尝试使用更宽松的配置
                if not text.strip():
                    print("使用宽松配置重新尝试OCR识别...")
                    text = pytesseract.image_to_string(
                        processed_image, 
                        lang=ocr_config['lang'], 
                        config='--psm 3 --oem 3'  # 更宽松的配置
                    ).strip()
                    print(f"宽松配置OCR识别结果: '{text}'")
                
            except Exception as ocr_error:
                raise HTTPException(
                    status_code=500, 
                    detail=f"OCR识别失败：{str(ocr_error)}。请确保图片清晰且包含可识别的文字内容。"
                )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档解析失败：{str(e)}")

    # 3. 校验解析结果（文档内容不能为空）
    if not text.strip():
        raise HTTPException(status_code=400, detail="文档内容为空或无法提取文本")

    # 4. 文档检测：文本预处理 + 严格模式（直接使用大模型检测）
    # 4.1 文本预处理（归一化字符格式）
    preprocessor = TextPreprocessor()
    normalized_text = preprocessor.preprocess_text(text)
    
    # 4.2 使用预处理后的文本进行LLM检测
    llm_start = time.time()
    llm_result = call_ollama_api(normalized_text)
    llm_time = time.time() - llm_start
    # 容错：若模型输出异常，默认按"正常"处理
    llm_result = llm_result if llm_result in ["敏感", "正常"] else "正常"
    final_result = llm_result

    # 5. 返回响应
    return {
        "status": "success",
        "data": {
            "filename": file.filename,
            "file_type": file_type,
            "text_length": len(text),  # 提取的文本长度
            "rule_detection": {
                "ac_results": [],
                "dfa_results": [],
                "preprocess_results": [],
                "all_results": [],
                "suspicious_segments": [],
                "word_count": 0,
                "normalized_text": normalized_text,  # 归一化后的文本
                "timing": {"preprocess_time": 0, "ac_time": 0, "dfa_time": 0, "total_time": 0}
            },
            "llm_detected": llm_result,
            "llm_time": round(llm_time * 1000, 2),  # 大模型检测用时（毫秒）
            "final_result": final_result,
            "detection_flow": "strict_mode"  # 文档检测使用严格模式（预处理+LLM）
        }
    }

# ---------------------- 健康检查端点 ----------------------
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
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
