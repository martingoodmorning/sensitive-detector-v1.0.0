// API 基础配置
const API_BASE_URL = 'http://localhost:8000';

// DOM 元素
const textTab = document.querySelector('[data-tab="text"]');
const documentTab = document.querySelector('[data-tab="document"]');
const librariesTab = document.querySelector('[data-tab="libraries"]');
const textPanel = document.getElementById('text-panel');
const documentPanel = document.getElementById('document-panel');
const librariesPanel = document.getElementById('libraries-panel');
const textInput = document.getElementById('text-input');
const detectTextBtn = document.getElementById('detect-text-btn');
const fileInput = document.getElementById('file-input');
const uploadArea = document.getElementById('upload-area');
const fileInfo = document.getElementById('file-info');
const detectDocumentBtn = document.getElementById('detect-document-btn');
const selectFileBtn = document.getElementById('select-file-btn');
const loadingOverlay = document.getElementById('loading-overlay');

// 词库选择相关元素（已移除，保留变量以避免错误）
const librarySelect = null;
const docLibrarySelect = null;
const refreshLibrariesBtn = null;
const refreshDocLibrariesBtn = null;
const selectedLibrariesInfo = null;
const docSelectedLibrariesInfo = null;

// 严格模式相关元素
const strictModeCheckbox = document.getElementById('strict-mode-checkbox');

// 词库管理相关元素
const librariesTable = document.getElementById('libraries-table');
const usedLibrariesList = document.getElementById('used-libraries-list');
const usedLibrariesCount = document.getElementById('used-libraries-count');
const updateDetectionLibrariesBtn = document.getElementById('update-detection-libraries-btn');
const createLibraryBtn = document.getElementById('create-library-btn');
const libraryEditor = document.getElementById('library-editor');
const libraryNameInput = document.getElementById('library-name-input');
const libraryWordsTextarea = document.getElementById('library-words-textarea');
const saveLibraryBtn = document.getElementById('save-library-btn');
const cancelEditBtn = document.getElementById('cancel-edit-btn');
const wordCount = document.getElementById('word-count');

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
        const strictMode = strictModeCheckbox ? strictModeCheckbox.checked : false;
        const requestBody = { text: text, fast_mode: false, strict_mode: strictMode };
        
        const response = await fetch(`${API_BASE_URL}/detect/text`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        displayTextResult(result.data, usedLibraries);
        
    } catch (error) {
        console.error('文本检测失败:', error);
        showNotification('检测失败，请检查网络连接或稍后重试', 'error');
    } finally {
        showLoading(false);
    }
}

// 显示文本检测结果
function displayTextResult(data, selectedLibraries) {
    const resultSection = document.getElementById('text-result');
    
    document.getElementById('original-text').textContent = data.original_text;
    
    // 显示使用的词库
    const usedLibrariesText = selectedLibraries.length > 0 ? selectedLibraries.join(', ') : '默认词库';
    const wordCountText = data.rule_detection && data.rule_detection.word_count 
        ? ` (${data.rule_detection.word_count} 个敏感词)`
        : '';
    document.getElementById('used-libraries').textContent = usedLibrariesText + wordCountText;
    
    // 显示规则匹配结果
    if (data.detection_flow === 'strict_mode') {
        // 严格模式：显示跳过
        document.getElementById('rule-detected').innerHTML = '<span class="status-tag status-skipped">跳过</span>';
    } else if (data.rule_detection) {
        document.getElementById('rule-detected').innerHTML = formatDetectionResult(data.rule_detection.all_results);
    } else {
        // 兼容旧版本API
        document.getElementById('rule-detected').innerHTML = formatDetectionResult(data.rule_detected || []);
    }
    
    // 显示大模型检测结果
    if (data.llm_time && data.llm_time > 0) {
        // 实际执行了大模型检测
    document.getElementById('llm-detected').innerHTML = formatDetectionResult(data.llm_detected);
    } else {
        // 跳过大模型检测
        document.getElementById('llm-detected').innerHTML = '<span class="status-tag status-skipped">跳过</span>';
    }
    
    // 显示检测用时
    const timingText = formatTimingInfo(data);
    document.getElementById('detection-timing').innerHTML = timingText;
    
    // 如果是严格模式，显示特殊提示
    if (data.detection_flow === 'strict_mode') {
        const timingElement = document.getElementById('detection-timing');
        timingElement.innerHTML += '<div class="strict-mode-notice">🔒 严格模式：跳过规则匹配，直接使用大模型检测</div>';
    }
    
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

// 格式化用时信息
function formatTimingInfo(data) {
    let timingHtml = '<div class="timing-info">';
    
    // 规则引擎检测用时
    if (data.detection_flow === 'strict_mode') {
        // 严格模式：显示跳过
        timingHtml += `
            <div class="timing-section">
                <strong>规则引擎检测:</strong>
                <span class="timing-total">跳过 (严格模式)</span>
            </div>
        `;
    } else if (data.rule_detection && data.rule_detection.timing) {
        const timing = data.rule_detection.timing;
        
        timingHtml += `
            <div class="timing-section">
                <strong>规则引擎检测:</strong>
                <span class="timing-item">预处理: ${timing.preprocess_time || 0}ms</span>
                <span class="timing-item">AC: ${timing.ac_time}ms</span>
                <span class="timing-item">DFA: ${timing.dfa_time}ms</span>
                <span class="timing-total">总计: ${timing.total_time}ms</span>
            </div>
        `;
    }
    
    // 大模型用时
    if (data.llm_time && data.llm_time > 0) {
        timingHtml += `
            <div class="timing-section">
                <strong>大模型检测:</strong>
                <span class="timing-total">${data.llm_time}ms</span>
            </div>
        `;
    } else {
        // 跳过大模型检测的情况
        timingHtml += `
            <div class="timing-section">
                <strong>大模型检测:</strong>
                <span class="timing-total">跳过 (规则匹配无敏感词)</span>
            </div>
        `;
    }
    
    // 总用时 - 规则引擎时间 + 大模型时间
    const ruleEngineTime = data.rule_detection?.timing?.total_time || 0;
    const llmTime = data.llm_time || 0;
    const totalTime = ruleEngineTime + llmTime;
    
    timingHtml += `
        <div class="timing-section timing-overall">
            <strong>总用时:</strong>
            <span class="timing-total">${totalTime.toFixed(2)}ms</span>
        </div>
    `;
    
    timingHtml += '</div>';
    return timingHtml;
}

// 文档检测功能
async function detectDocument(file) {
    if (!file) {
        showNotification('请选择要检测的文档', 'error');
        return;
    }
    
    // 检查文件类型（支持多种格式）
    const allowedTypes = [
        'text/plain', 
        'application/pdf', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',  // DOC格式
        'image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/gif', 'image/tiff'  // 图片格式（OCR）
    ];
    if (!allowedTypes.includes(file.type)) {
        showNotification('不支持的文件类型！支持 TXT、PDF、DOCX、DOC、图片格式（OCR）', 'error');
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
        
        // 使用保存的检测词库（无需传递参数）
        
        const response = await fetch(`${API_BASE_URL}/detect/document`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`HTTP error! status: ${response.status}, detail: ${errorData.detail || 'Unknown error'}`);
        }
        
        const result = await response.json();
        displayDocumentResult(result.data, usedLibraries);
        
    } catch (error) {
        console.error('文档检测失败:', error);
        
        // 解析错误信息，提供更友好的提示
        let errorMessage = '检测失败，请检查网络连接或稍后重试';
        
        if (error.message.includes('HTTP error! status: 400')) {
            // 400错误通常是文件格式问题
            const detailMatch = error.message.match(/detail: (.+)/);
            if (detailMatch) {
                errorMessage = `文件格式错误：${detailMatch[1]}`;
            } else {
                errorMessage = '文件格式不支持或文件已损坏，请检查文件格式是否正确';
            }
        } else if (error.message.includes('HTTP error! status: 500')) {
            // 500错误通常是服务器内部错误
            errorMessage = '服务器处理文件时出错，请稍后重试或联系管理员';
        } else if (error.message.includes('Failed to fetch')) {
            // 网络连接问题
            errorMessage = '网络连接失败，请检查网络连接后重试';
        }
        
        showNotification(errorMessage, 'error');
    } finally {
        showLoading(false);
    }
}

// 显示文档检测结果
function displayDocumentResult(data, selectedLibraries) {
    const resultSection = document.getElementById('document-result');
    
    document.getElementById('doc-filename').textContent = data.filename;
    document.getElementById('doc-file-type').textContent = data.file_type.toUpperCase();
    document.getElementById('doc-text-length').textContent = `${data.text_length} 字符`;
    
    // 显示规则匹配结果
    if (data.detection_flow === 'strict_mode') {
        // 严格模式：显示跳过
        document.getElementById('doc-rule-detected').innerHTML = '<span class="status-tag status-skipped">跳过</span>';
    } else if (data.rule_detection) {
        document.getElementById('doc-rule-detected').innerHTML = formatDetectionResult(data.rule_detection.all_results);
    } else {
        // 兼容旧版本API
        document.getElementById('doc-rule-detected').innerHTML = formatDetectionResult(data.rule_detected || []);
    }
    
    document.getElementById('doc-llm-detected').innerHTML = formatDetectionResult(data.llm_detected);
    
    // 显示检测用时
    const timingText = formatTimingInfo(data);
    document.getElementById('doc-detection-timing').innerHTML = timingText;
    
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
    librariesTab.addEventListener('click', () => switchTab('libraries'));
    
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
    
    // 初始化词库管理
    initializeLibraryManagement();
});

// ==================== 词库管理功能 ====================

// 词库管理相关变量
let currentEditingLibrary = null;
let libraries = [];
let usedLibraries = []; // 当前使用的词库列表

// 初始化词库管理
async function initializeLibraryManagement() {
    console.log('初始化词库管理...');
    try {
        await loadLibraries();
        await loadDetectionLibrariesStatus(); // 这个函数内部会调用 renderUsedLibrariesList()
        setupLibraryEventListeners();
        console.log('词库管理初始化完成');
    } catch (error) {
        console.error('词库管理初始化失败:', error);
    }
}

// 加载词库列表
async function loadLibraries() {
    try {
        const response = await fetch(`${API_BASE_URL}/word-libraries`);
        const result = await response.json();
        
        if (result.status === 'success') {
            libraries = result.data;
            renderLibrariesTable();
        }
    } catch (error) {
        console.error('加载词库列表失败:', error);
        showNotification('加载词库列表失败', 'error');
    }
}

// 加载检测词库状态
async function loadDetectionLibrariesStatus() {
    console.log('🚀 开始加载检测词库状态...');
    try {
        const response = await fetch(`${API_BASE_URL}/detection-libraries/status`);
        console.log('📡 API响应状态:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('📦 API响应数据:', result);
        
        if (result.status === 'success') {
            usedLibraries = result.data.used_libraries || [];
            console.log('✅ 成功加载检测词库状态:', usedLibraries);
            console.log('📊 词库数量:', usedLibraries.length);
            console.log('🎨 开始更新UI...');
            renderUsedLibrariesList(); // 更新UI显示
            console.log('✨ UI已更新完成');
        } else {
            console.error('❌ API返回错误状态:', result);
        }
    } catch (error) {
        console.error('💥 加载检测词库状态失败:', error);
    }
}

// 渲染词库列表
function renderLibrariesTable() {
    librariesTable.innerHTML = '';
    
    if (libraries.length === 0) {
        librariesTable.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">暂无词库，点击"创建新词库"开始添加</p>';
        return;
    }
    
    libraries.forEach(library => {
        const libraryItem = document.createElement('div');
        libraryItem.className = 'library-item';
        libraryItem.innerHTML = `
            <div class="library-info-item">
                <div class="library-name">${library.name}</div>
                <div class="library-details">
                    敏感词数量: ${library.word_count} | 
                    创建时间: ${new Date(library.created_time).toLocaleDateString()} |
                    文件大小: ${(library.size / 1024).toFixed(1)} KB
                </div>
            </div>
            <div class="library-actions">
                <button class="btn btn-primary" onclick="addToUsedLibraries('${library.name}')" 
                        ${usedLibraries.includes(library.name) ? 'disabled' : ''}>
                    <i class="fas fa-plus"></i> ${usedLibraries.includes(library.name) ? '已添加' : '添加使用'}
                </button>
                <button class="btn btn-secondary" onclick="editLibrary('${library.name}')">
                    <i class="fas fa-edit"></i> 编辑
                </button>
                <button class="btn btn-secondary" onclick="deleteLibrary('${library.name}')">
                    <i class="fas fa-trash"></i> 删除
                </button>
            </div>
        `;
        librariesTable.appendChild(libraryItem);
    });
}

// 渲染使用词库列表
function renderUsedLibrariesList() {
    console.log('🎯 开始渲染使用词库列表，当前词库:', usedLibraries);
    usedLibrariesList.innerHTML = '';
    
    if (usedLibraries.length === 0) {
        usedLibrariesCount.textContent = '当前使用 0 个词库';
        console.log('无词库，显示默认状态');
    } else {
        usedLibraries.forEach(libraryName => {
            const libraryItem = document.createElement('div');
            libraryItem.className = 'used-library-item';
            libraryItem.innerHTML = `
                <span>${libraryName}</span>
                <button class="remove-btn" onclick="removeFromUsedLibraries('${libraryName}')" title="移除">
                    <i class="fas fa-times"></i>
                </button>
            `;
            usedLibrariesList.appendChild(libraryItem);
        });
        
        usedLibrariesCount.textContent = `已选择 ${usedLibraries.length} 个词库`;
        console.log('已渲染', usedLibraries.length, '个词库');
    }
    
    // 更新状态指示器
    const currentLibraryStatus = document.getElementById('current-library-status');
    if (currentLibraryStatus) {
        if (usedLibraries.length === 0) {
            currentLibraryStatus.textContent = '使用默认词库';
            currentLibraryStatus.className = 'status-value status-default';
            console.log('状态指示器更新为: 使用默认词库');
        } else {
            currentLibraryStatus.textContent = `使用 ${usedLibraries.length} 个自定义词库`;
            currentLibraryStatus.className = 'status-value status-custom';
            console.log('状态指示器更新为: 使用', usedLibraries.length, '个自定义词库');
        }
    } else {
        console.error('找不到状态指示器元素 current-library-status');
    }
    
    // 更新最后更新时间
    const lastUpdateTime = document.getElementById('last-update-time');
    if (lastUpdateTime) {
        lastUpdateTime.textContent = new Date().toLocaleString('zh-CN');
        console.log('更新时间已设置');
    } else {
        console.error('找不到更新时间元素 last-update-time');
    }
}

// 添加到使用词库列表
function addToUsedLibraries(libraryName) {
    if (!usedLibraries.includes(libraryName)) {
        usedLibraries.push(libraryName);
        renderUsedLibrariesList();
        renderLibrariesTable(); // 重新渲染词库列表以更新按钮状态
        showNotification(`已将 "${libraryName}" 添加到使用列表，请点击"更新检测词库"按钮应用更改`, 'success');
    }
}

// 从使用词库列表移除
function removeFromUsedLibraries(libraryName) {
    const index = usedLibraries.indexOf(libraryName);
    if (index > -1) {
        usedLibraries.splice(index, 1);
        renderUsedLibrariesList();
        renderLibrariesTable(); // 重新渲染词库列表以更新按钮状态
        showNotification(`已将 "${libraryName}" 从使用列表移除，请点击"更新检测词库"按钮应用更改`, 'success');
    }
}

// 更新检测词库
async function updateDetectionLibraries() {
    // 显示加载状态
    updateDetectionLibrariesBtn.disabled = true;
    updateDetectionLibrariesBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 更新中...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/detection-libraries/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                library_names: usedLibraries
            })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            console.log('检测词库更新成功:', result.data);
            // 更新词库统计信息
            if (result.data.word_count) {
                usedLibrariesCount.textContent = `当前使用 ${usedLibraries.length} 个词库 (${result.data.word_count} 个敏感词)`;
            }
            showNotification(`检测词库更新成功！使用 ${usedLibraries.length} 个词库，共 ${result.data.word_count} 个敏感词`, 'success');
        } else {
            console.error('检测词库更新失败:', result.message);
            showNotification('检测词库更新失败: ' + result.message, 'error');
        }
    } catch (error) {
        console.error('更新检测词库失败:', error);
        showNotification('更新检测词库失败: ' + error.message, 'error');
    } finally {
        // 恢复按钮状态
        updateDetectionLibrariesBtn.disabled = false;
        updateDetectionLibrariesBtn.innerHTML = '<i class="fas fa-sync-alt"></i> 更新检测词库';
    }
}

// 设置词库管理事件监听器
function setupLibraryEventListeners() {
    console.log('设置词库管理事件监听器...');
    
    // 检查DOM元素是否存在
    if (!createLibraryBtn) {
        console.error('createLibraryBtn 元素不存在');
        return;
    }
    
    // 创建新词库
    createLibraryBtn.addEventListener('click', () => {
        console.log('点击创建新词库按钮');
        showLibraryEditor();
    });
    
    // 保存词库
    saveLibraryBtn.addEventListener('click', saveLibrary);
    
    // 取消编辑
    cancelEditBtn.addEventListener('click', hideLibraryEditor);
    
    // 更新检测词库
    updateDetectionLibrariesBtn.addEventListener('click', async () => {
        console.log('点击更新检测词库按钮');
        await updateDetectionLibraries();
    });
    
    // 刷新词库列表（已移除相关按钮）
    
    // 词库名称输入变化
    libraryNameInput.addEventListener('input', () => {
        if (currentEditingLibrary) {
            libraryNameInput.disabled = true; // 编辑时禁用名称修改
        }
    });
    
    // 敏感词文本变化
    libraryWordsTextarea.addEventListener('input', updateWordCount);
}

// 显示词库编辑器
function showLibraryEditor(libraryName = null) {
    currentEditingLibrary = libraryName;
    
    if (libraryName) {
        // 编辑模式
        document.getElementById('editor-title').textContent = '编辑词库';
        loadLibraryContent(libraryName);
    } else {
        // 创建模式
        document.getElementById('editor-title').textContent = '创建新词库';
        libraryNameInput.value = '';
        libraryWordsTextarea.value = '';
        libraryNameInput.disabled = false;
    }
    
    libraryEditor.style.display = 'block';
    updateWordCount();
}

// 隐藏词库编辑器
function hideLibraryEditor() {
    libraryEditor.style.display = 'none';
    currentEditingLibrary = null;
    libraryNameInput.disabled = false;
}

// 加载词库内容
async function loadLibraryContent(libraryName) {
    try {
        const response = await fetch(`${API_BASE_URL}/word-libraries/${libraryName}`);
        const result = await response.json();
        
        if (result.status === 'success') {
            libraryNameInput.value = result.data.name;
            libraryWordsTextarea.value = result.data.words.join('\n');
            updateWordCount();
        }
    } catch (error) {
        console.error('加载词库内容失败:', error);
        showNotification('加载词库内容失败', 'error');
    }
}

// 保存词库
async function saveLibrary() {
    const name = libraryNameInput.value.trim();
    const wordsText = libraryWordsTextarea.value.trim();
    
    if (!name) {
        showNotification('请输入词库名称', 'error');
        return;
    }
    
    if (!wordsText) {
        showNotification('请输入敏感词', 'error');
        return;
    }
    
    const words = wordsText.split('\n')
        .map(word => word.trim())
        .filter(word => word);
    
    if (words.length === 0) {
        showNotification('请输入有效的敏感词', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const url = currentEditingLibrary 
            ? `${API_BASE_URL}/word-libraries/${currentEditingLibrary}`
            : `${API_BASE_URL}/word-libraries`;
        
        const method = currentEditingLibrary ? 'PUT' : 'POST';
        const body = currentEditingLibrary ? { words } : { name, words };
        
        const response = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body)
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            showNotification(
                currentEditingLibrary ? '词库更新成功' : '词库创建成功', 
                'success'
            );
            await loadLibraries();
            updateLibrarySelects();
            hideLibraryEditor();
        } else {
            throw new Error(result.message || '操作失败');
        }
    } catch (error) {
        console.error('保存词库失败:', error);
        showNotification('保存词库失败: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// 编辑词库
function editLibrary(libraryName) {
    showLibraryEditor(libraryName);
}

// 删除词库
async function deleteLibrary(libraryName) {
    if (!confirm(`确定要删除词库 "${libraryName}" 吗？此操作不可恢复。`)) {
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/word-libraries/${libraryName}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            showNotification('词库删除成功', 'success');
            await loadLibraries();
            updateLibrarySelects();
        } else {
            throw new Error(result.message || '删除失败');
        }
    } catch (error) {
        console.error('删除词库失败:', error);
        showNotification('删除词库失败: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// 更新敏感词计数
function updateWordCount() {
    const wordsText = libraryWordsTextarea.value.trim();
    const wordCount = wordsText ? wordsText.split('\n').filter(line => line.trim()).length : 0;
    document.getElementById('word-count').textContent = `${wordCount} 个敏感词`;
}

