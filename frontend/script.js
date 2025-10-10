// API 基础配置
const API_BASE_URL = 'http://localhost:8000';

// DOM 元素
const textTab = document.querySelector('[data-tab="text"]');
const documentTab = document.querySelector('[data-tab="document"]');
const textPanel = document.getElementById('text-panel');
const documentPanel = document.getElementById('document-panel');
const textInput = document.getElementById('text-input');
const detectTextBtn = document.getElementById('detect-text-btn');
const fileInput = document.getElementById('file-input');
const uploadArea = document.getElementById('upload-area');
const fileInfo = document.getElementById('file-info');
const detectDocumentBtn = document.getElementById('detect-document-btn');
const selectFileBtn = document.getElementById('select-file-btn');
const loadingOverlay = document.getElementById('loading-overlay');

// 标签页切换
function switchTab(tabName) {
    // 移除所有活动状态
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(panel => panel.classList.remove('active'));
    
    // 添加活动状态
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`${tabName}-panel`).classList.add('active');
}

// 文本检测功能
async function detectText() {
    const text = textInput.value.trim();
    
    if (!text) {
        showNotification('请输入需要检测的文本内容', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/detect/text`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        displayTextResult(result.data);
        
    } catch (error) {
        console.error('文本检测失败:', error);
        showNotification('检测失败，请检查网络连接或稍后重试', 'error');
    } finally {
        showLoading(false);
    }
}

// 显示文本检测结果
function displayTextResult(data) {
    const resultSection = document.getElementById('text-result');
    
    document.getElementById('original-text').textContent = data.original_text;
    document.getElementById('rule-detected').innerHTML = formatDetectionResult(data.rule_detected);
    document.getElementById('llm-detected').innerHTML = formatDetectionResult(data.llm_detected);
    document.getElementById('final-result').innerHTML = formatFinalResult(data.final_result);
    
    resultSection.style.display = 'block';
    resultSection.scrollIntoView({ behavior: 'smooth' });
}

// 格式化检测结果
function formatDetectionResult(result) {
    if (Array.isArray(result) && result.length > 0) {
        return `<span class="status-tag status-sensitive">检测到 ${result.length} 个敏感词: ${result.join(', ')}</span>`;
    } else if (result === '敏感') {
        return '<span class="status-tag status-sensitive">敏感</span>';
    } else {
        return '<span class="status-tag status-normal">正常</span>';
    }
}

// 格式化最终结果
function formatFinalResult(result) {
    if (result === '敏感') {
        return '<span class="status-tag status-sensitive">敏感</span>';
    } else {
        return '<span class="status-tag status-normal">正常</span>';
    }
}

// 文档检测功能
async function detectDocument(file) {
    if (!file) {
        showNotification('请选择要检测的文档', 'error');
        return;
    }
    
    // 检查文件类型
    const allowedTypes = ['text/plain', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!allowedTypes.includes(file.type)) {
        showNotification('不支持的文件类型！仅支持 TXT、PDF、DOCX 格式', 'error');
        return;
    }
    
    // 检查文件大小 (10MB)
    if (file.size > 10 * 1024 * 1024) {
        showNotification('文件大小不能超过 10MB', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE_URL}/detect/document`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        displayDocumentResult(result.data);
        
    } catch (error) {
        console.error('文档检测失败:', error);
        showNotification('检测失败，请检查网络连接或稍后重试', 'error');
    } finally {
        showLoading(false);
    }
}

// 显示文档检测结果
function displayDocumentResult(data) {
    const resultSection = document.getElementById('document-result');
    
    document.getElementById('doc-filename').textContent = data.filename;
    document.getElementById('doc-file-type').textContent = data.file_type.toUpperCase();
    document.getElementById('doc-text-length').textContent = `${data.text_length} 字符`;
    document.getElementById('doc-rule-detected').innerHTML = formatDetectionResult(data.rule_detected);
    document.getElementById('doc-llm-detected').innerHTML = formatDetectionResult(data.llm_detected);
    document.getElementById('doc-final-result').innerHTML = formatFinalResult(data.final_result);
    
    resultSection.style.display = 'block';
    resultSection.scrollIntoView({ behavior: 'smooth' });
}

// 文件上传处理
function handleFileSelect(file) {
    if (!file) return;
    
    // 更新文件输入框（用于检测功能）
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    fileInput.files = dataTransfer.files;
    
    document.getElementById('file-name').textContent = file.name;
    document.getElementById('file-size').textContent = formatFileSize(file.size);
    
    uploadArea.style.display = 'none';
    fileInfo.style.display = 'flex';
}

// 重置文档检测
function resetDocumentDetection() {
    // 清空文件输入
    fileInput.value = '';
    
    // 隐藏结果区域
    document.getElementById('document-result').style.display = 'none';
    
    // 隐藏文件信息，显示上传区域
    fileInfo.style.display = 'none';
    uploadArea.style.display = 'block';
    
    // 清空文件信息显示
    document.getElementById('file-name').textContent = '';
    document.getElementById('file-size').textContent = '';
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 拖拽上传处理
function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
}

// 显示/隐藏加载状态
function showLoading(show) {
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

// 显示通知
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // 添加样式
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#f8d7da' : '#d1ecf1'};
        color: ${type === 'error' ? '#721c24' : '#0c5460'};
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1001;
        animation: slideIn 0.3s ease;
        max-width: 400px;
    `;
    
    document.body.appendChild(notification);
    
    // 3秒后自动移除
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// 字符计数
function updateCharCount() {
    const count = textInput.value.length;
    document.querySelector('.char-count').textContent = `${count} 字符`;
}

// 事件监听器
document.addEventListener('DOMContentLoaded', function() {
    // 标签页切换
    textTab.addEventListener('click', () => switchTab('text'));
    documentTab.addEventListener('click', () => switchTab('document'));
    
    // 文本检测
    detectTextBtn.addEventListener('click', detectText);
    textInput.addEventListener('input', updateCharCount);
    
    // 文档检测
    detectDocumentBtn.addEventListener('click', () => {
        const file = fileInput.files[0];
        detectDocument(file);
    });
    
    // 文件选择
    fileInput.addEventListener('change', (e) => {
        handleFileSelect(e.target.files[0]);
    });
    
    // 拖拽上传
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    
    // 点击上传区域选择文件
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });
    
    // 点击选择文件按钮
    selectFileBtn.addEventListener('click', (e) => {
        e.stopPropagation(); // 阻止事件冒泡
        fileInput.click();
    });
    
    // 重置文档检测 - 使用事件委托
    document.addEventListener('click', (e) => {
        if (e.target && e.target.id === 'reset-document-btn') {
            resetDocumentDetection();
        }
    });
    
    // 键盘快捷键
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            if (textPanel.classList.contains('active')) {
                detectText();
            } else if (documentPanel.classList.contains('active')) {
                const file = fileInput.files[0];
                if (file) {
                    detectDocument(file);
                }
            }
        }
    });
    
    // 初始化字符计数
    updateCharCount();
});
