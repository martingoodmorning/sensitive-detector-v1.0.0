# 前端技术文档

## 概述

敏感词检测系统前端采用原生 HTML、CSS、JavaScript 技术栈，提供现代化的用户界面和交互体验。前端通过 RESTful API 与后端通信，实现文本和文档的敏感词检测功能。

## 技术栈

- **HTML5**: 语义化标记语言
- **CSS3**: 样式设计和动画效果
- **JavaScript ES6+**: 交互逻辑和 API 调用
- **Fetch API**: HTTP 请求处理
- **Drag & Drop API**: 文件拖拽上传
- **Font Awesome**: 图标库

## 项目结构

```
frontend/
├── index.html          # 主页面文件
├── style.css           # 样式文件
└── script.js           # 交互逻辑文件
```

## 文件详解

### index.html

主页面文件，定义页面结构和内容。

#### 页面结构

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <!-- 元数据定义 -->
</head>
<body>
    <div class="container">
        <!-- 顶部导航 -->
        <header class="header">
            <!-- 系统标题和标签页 -->
        </header>
        
        <!-- 主要内容区域 -->
        <main class="main-content">
            <!-- 文本检测面板 -->
            <div class="panel active" id="text-panel">
                <!-- 文本输入和检测功能 -->
            </div>
            
            <!-- 文档检测面板 -->
            <div class="panel" id="document-panel">
                <!-- 文件上传和检测功能 -->
            </div>
        </main>
        
        <!-- 加载遮罩 -->
        <div class="loading-overlay" id="loading-overlay">
            <!-- 加载动画 -->
        </div>
    </div>
</body>
</html>
```

#### 关键元素

| 元素ID | 类型 | 说明 |
|--------|------|------|
| `text-panel` | div | 文本检测面板 |
| `document-panel` | div | 文档检测面板 |
| `text-input` | textarea | 文本输入框 |
| `file-input` | input | 文件选择输入 |
| `upload-area` | div | 文件拖拽区域 |
| `loading-overlay` | div | 加载遮罩层 |

### style.css

样式文件，定义页面外观和动画效果。

#### 设计系统

**色彩方案**:
```css
:root {
    --primary-color: #3498db;      /* 主色调 */
    --secondary-color: #2c3e50;    /* 次要色调 */
    --success-color: #27ae60;      /* 成功状态 */
    --error-color: #e74c3c;        /* 错误状态 */
    --warning-color: #f39c12;      /* 警告状态 */
    --background-color: #f8f9fa;   /* 背景色 */
    --text-color: #2c3e50;         /* 文本色 */
    --border-color: #dee2e6;       /* 边框色 */
}
```

**字体系统**:
```css
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 
                 'Helvetica Neue', Arial, sans-serif;
    font-size: 16px;
    line-height: 1.6;
}
```

**间距系统**:
```css
:root {
    --spacing-xs: 4px;
    --spacing-sm: 8px;
    --spacing-md: 16px;
    --spacing-lg: 24px;
    --spacing-xl: 32px;
}
```

#### 响应式设计

**断点定义**:
```css
/* 移动设备 */
@media (max-width: 768px) {
    .container {
        padding: var(--spacing-md);
    }
    
    .header h1 {
        font-size: 1.5rem;
    }
}

/* 平板设备 */
@media (min-width: 769px) and (max-width: 1024px) {
    .container {
        max-width: 800px;
    }
}

/* 桌面设备 */
@media (min-width: 1025px) {
    .container {
        max-width: 1200px;
    }
}
```

#### 动画效果

**加载动画**:
```css
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.loading-spinner {
    animation: spin 1s linear infinite;
}
```

**通知动画**:
```css
@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes slideOut {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(100%);
        opacity: 0;
    }
}
```

### script.js

交互逻辑文件，实现页面功能和 API 调用。

#### 模块结构

```javascript
// 1. 配置和常量定义
const API_BASE_URL = 'http://localhost:8000';

// 2. DOM 元素获取
const textTab = document.querySelector('[data-tab="text"]');
// ... 其他元素

// 3. 核心功能函数
function switchTab(tabName) { /* ... */ }
function detectText() { /* ... */ }
function detectDocument(file) { /* ... */ }

// 4. 工具函数
function showNotification(message, type) { /* ... */ }
function formatFileSize(bytes) { /* ... */ }

// 5. 事件监听器
document.addEventListener('DOMContentLoaded', function() {
    // 事件绑定
});
```

#### 核心功能

**1. 标签页切换**
```javascript
function switchTab(tabName) {
    // 移除所有活动状态
    document.querySelectorAll('.tab-btn').forEach(btn => 
        btn.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(panel => 
        panel.classList.remove('active'));
    
    // 添加活动状态
    document.querySelector(`[data-tab="${tabName}"]`)
        .classList.add('active');
    document.getElementById(`${tabName}-panel`)
        .classList.add('active');
}
```

**2. 文本检测**
```javascript
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
```

**3. 文档检测**
```javascript
async function detectDocument(file) {
    if (!file) {
        showNotification('请选择要检测的文档', 'error');
        return;
    }
    
    // 文件类型检查
    const allowedTypes = [
        'text/plain', 
        'application/pdf', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];
    
    if (!allowedTypes.includes(file.type)) {
        showNotification('不支持的文件类型！仅支持 TXT、PDF、DOCX 格式', 'error');
        return;
    }
    
    // 文件大小检查 (10MB)
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
```

**4. 文件拖拽处理**
```javascript
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
```

**5. 通知系统**
```javascript
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // 动态样式
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
    
    // 自动移除
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}
```

#### 事件处理

**事件监听器绑定**:
```javascript
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
    
    // 点击上传区域
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });
    
    // 选择文件按钮
    selectFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });
    
    // 重置按钮 (事件委托)
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
    
    // 初始化
    updateCharCount();
});
```

## 用户体验设计

### 交互流程

1. **文本检测流程**
   ```
   用户输入文本 → 点击检测按钮 → 显示加载状态 → 调用API → 显示结果
   ```

2. **文档检测流程**
   ```
   选择/拖拽文件 → 显示文件信息 → 点击检测按钮 → 显示加载状态 → 调用API → 显示结果
   ```

### 反馈机制

1. **视觉反馈**
   - 加载动画
   - 状态指示器
   - 进度条

2. **通知反馈**
   - 成功通知
   - 错误通知
   - 警告通知

3. **交互反馈**
   - 按钮状态变化
   - 悬停效果
   - 点击反馈

### 可访问性

1. **键盘导航**
   - Tab 键切换焦点
   - Enter 键激活按钮
   - Ctrl+Enter 快捷键检测

2. **屏幕阅读器支持**
   - 语义化 HTML 标签
   - ARIA 属性
   - 描述性文本

3. **视觉辅助**
   - 高对比度色彩
   - 清晰的字体大小
   - 适当的间距

## 性能优化

### 代码优化

1. **DOM 操作优化**
   ```javascript
   // 缓存 DOM 元素
   const textInput = document.getElementById('text-input');
   
   // 批量 DOM 更新
   const fragment = document.createDocumentFragment();
   // ... 添加元素到 fragment
   container.appendChild(fragment);
   ```

2. **事件处理优化**
   ```javascript
   // 事件委托
   document.addEventListener('click', (e) => {
       if (e.target.matches('.reset-btn')) {
           resetFunction();
       }
   });
   ```

3. **异步处理**
   ```javascript
   // 使用 async/await
   async function detectText() {
       try {
           const response = await fetch(url, options);
           const result = await response.json();
           return result;
       } catch (error) {
           console.error(error);
       }
   }
   ```

### 资源优化

1. **CSS 优化**
   - 使用 CSS 变量
   - 避免重复样式
   - 使用 transform 替代位置变化

2. **JavaScript 优化**
   - 模块化代码
   - 避免全局变量
   - 使用 const/let 替代 var

3. **网络优化**
   - 压缩资源文件
   - 使用 CDN 加速
   - 实现缓存策略

## 浏览器兼容性

### 支持的浏览器

| 浏览器 | 最低版本 | 说明 |
|--------|----------|------|
| Chrome | 60+ | 完全支持 |
| Firefox | 55+ | 完全支持 |
| Safari | 12+ | 完全支持 |
| Edge | 79+ | 完全支持 |

### 兼容性处理

1. **ES6+ 语法兼容**
   ```javascript
   // 使用 Babel 转译
   // 或使用 polyfill
   ```

2. **API 兼容性**
   ```javascript
   // Fetch API polyfill
   if (!window.fetch) {
       // 加载 polyfill
   }
   ```

3. **CSS 兼容性**
   ```css
   /* 使用 autoprefixer */
   .example {
       -webkit-transform: translateX(0);
       -moz-transform: translateX(0);
       -ms-transform: translateX(0);
       transform: translateX(0);
   }
   ```

## 测试指南

### 功能测试

1. **文本检测测试**
   - 正常文本检测
   - 敏感文本检测
   - 空文本处理
   - 超长文本处理

2. **文档检测测试**
   - 支持格式测试
   - 不支持格式测试
   - 文件大小限制测试
   - 拖拽上传测试

3. **界面交互测试**
   - 标签页切换
   - 按钮点击
   - 键盘快捷键
   - 响应式布局

### 性能测试

1. **加载性能**
   - 页面加载时间
   - 资源加载时间
   - 首屏渲染时间

2. **交互性能**
   - 点击响应时间
   - 动画流畅度
   - 内存使用情况

### 兼容性测试

1. **浏览器测试**
   - 主流浏览器测试
   - 移动浏览器测试
   - 不同分辨率测试

2. **设备测试**
   - 桌面设备
   - 平板设备
   - 移动设备

## 部署说明

### 静态文件部署

1. **Nginx 配置**
   ```nginx
   server {
       listen 80;
       server_name example.com;
       root /var/www/sensitive-detector/frontend;
       index index.html;
       
       location / {
           try_files $uri $uri/ /index.html;
       }
       
       location /static/ {
           expires 1y;
           add_header Cache-Control "public, immutable";
       }
   }
   ```

2. **Apache 配置**
   ```apache
   <VirtualHost *:80>
       ServerName example.com
       DocumentRoot /var/www/sensitive-detector/frontend
       
       <Directory /var/www/sensitive-detector/frontend>
           AllowOverride All
           Require all granted
       </Directory>
   </VirtualHost>
   ```

### CDN 部署

1. **资源上传**
   - 上传静态文件到 CDN
   - 配置缓存策略
   - 设置 CORS 头

2. **域名配置**
   - 配置 CDN 域名
   - 设置 SSL 证书
   - 配置回源规则

## 维护指南

### 日常维护

1. **监控检查**
   - 页面加载速度
   - 错误日志检查
   - 用户反馈收集

2. **性能优化**
   - 代码审查
   - 性能分析
   - 优化建议实施

### 版本更新

1. **更新流程**
   - 代码审查
   - 测试验证
   - 部署发布
   - 监控验证

2. **回滚策略**
   - 版本备份
   - 快速回滚
   - 问题修复

---

**文档版本**: v1.0.0  
**最后更新**: 2025年10月
