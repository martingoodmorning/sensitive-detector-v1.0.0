# Gitee 部署指南

## 概述

由于网络访问限制，本项目提供基于 Gitee 的部署方案，确保国内用户能够顺利下载和部署敏感词检测系统。

## 🚀 快速部署

### 方法一：下载部署包（推荐）

```bash
# 1. 下载部署包
wget https://gitee.com/saisai5203/sensitive-detector/releases/download/v1.0.0/sensitive-detector-v1.0.0.tar.gz

# 2. 解压并安装
tar -xzf sensitive-detector-v1.0.0.tar.gz
cd sensitive-detector-v1.0.0
chmod +x install.sh
./install.sh

# 3. 访问系统
# 浏览器打开: http://localhost:8000
```

### 方法二：克隆源码

```bash
# 1. 克隆项目
git clone https://gitee.com/saisai5203/sensitive-detector.git
cd sensitive-detector

# 2. 构建部署包
chmod +x scripts/build-deploy-package.sh
./scripts/build-deploy-package.sh

# 3. 解压部署包
tar -xzf sensitive-detector-v1.0.0.tar.gz
cd sensitive-detector-v1.0.0

# 4. 一键安装
chmod +x install.sh
./install.sh
```

## 📦 Gitee 仓库配置

### 1. 创建 Gitee 仓库

1. 访问 [Gitee](https://gitee.com)
2. 点击 "新建仓库"
3. 填写仓库信息：
   - 仓库名称：`sensitive-detector`
   - 仓库描述：`敏感词检测系统`
   - 开源许可证：MIT
   - 初始化仓库：勾选 "使用 README 文件初始化这个仓库"

### 2. 上传项目文件

```bash
# 1. 添加远程仓库
git remote add gitee https://gitee.com/your-username/sensitive-detector.git

# 2. 推送代码
git push -u gitee main

# 3. 创建标签
git tag v1.0.0
git push gitee v1.0.0
```

### 3. 创建 Release

1. 在 Gitee 仓库页面点击 "发布"
2. 填写发布信息：
   - 版本号：`v1.0.0`
   - 发布标题：`敏感词检测系统 v1.0.0`
   - 发布说明：填写更新内容
3. 上传部署包：`sensitive-detector-v1.0.0.tar.gz`

## 🔧 国内网络优化

### 1. Docker 镜像加速

**配置 Docker 镜像加速器**:
```bash
# 创建或编辑 Docker 配置文件
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
EOF

# 重启 Docker 服务
sudo systemctl daemon-reload
sudo systemctl restart docker
```

### 2. Ollama 模型下载加速

**使用国内镜像源**:
```bash
# 设置 Ollama 镜像源
export OLLAMA_HOST=0.0.0.0:11434
export OLLAMA_MODELS=/root/.ollama/models

# 从国内镜像下载模型
ollama pull qwen:7b
```

### 3. 系统包管理器加速

**Ubuntu/Debian**:
```bash
# 备份原始源
sudo cp /etc/apt/sources.list /etc/apt/sources.list.backup

# 使用国内镜像源
sudo tee /etc/apt/sources.list <<-'EOF'
deb https://mirrors.ustc.edu.cn/ubuntu/ focal main restricted universe multiverse
deb https://mirrors.ustc.edu.cn/ubuntu/ focal-security main restricted universe multiverse
deb https://mirrors.ustc.edu.cn/ubuntu/ focal-updates main restricted universe multiverse
deb https://mirrors.ustc.edu.cn/ubuntu/ focal-backports main restricted universe multiverse
EOF

# 更新包列表
sudo apt update
```

**CentOS/RHEL**:
```bash
# 使用阿里云镜像
sudo sed -e 's|^mirrorlist=|#mirrorlist=|g' \
         -e 's|^#baseurl=http://mirror.centos.org|baseurl=https://mirrors.aliyun.com|g' \
         -i.bak \
         /etc/yum.repos.d/CentOS-*.repo

# 更新包列表
sudo yum update
```

## 🌐 网络配置优化

### 1. DNS 配置

**配置国内 DNS**:
```bash
# 编辑 DNS 配置
sudo tee /etc/systemd/resolved.conf <<-'EOF'
[Resolve]
DNS=223.5.5.5 223.6.6.6
FallbackDNS=8.8.8.8 8.8.4.4
EOF

# 重启 DNS 服务
sudo systemctl restart systemd-resolved
```

### 2. 代理配置（可选）

**HTTP 代理设置**:
```bash
# 设置环境变量
export http_proxy=http://proxy.example.com:8080
export https_proxy=http://proxy.example.com:8080
export no_proxy=localhost,127.0.0.1

# 配置 Git 代理
git config --global http.proxy http://proxy.example.com:8080
git config --global https.proxy http://proxy.example.com:8080
```

## 📋 部署检查清单

### 部署前检查
- [ ] Gitee 仓库已创建
- [ ] 项目代码已上传
- [ ] Release 已发布
- [ ] 部署包已上传
- [ ] 网络连接正常
- [ ] Docker 已安装
- [ ] Docker Compose 已安装

### 部署过程检查
- [ ] 部署包下载成功
- [ ] 解压无错误
- [ ] 安装脚本执行成功
- [ ] Docker 镜像拉取成功
- [ ] Ollama 服务启动成功
- [ ] 模型下载完成
- [ ] 应用服务启动成功
- [ ] 健康检查通过

### 部署后检查
- [ ] 前端界面可访问
- [ ] API 接口正常
- [ ] 文本检测功能正常
- [ ] 文档检测功能正常
- [ ] 日志输出正常
- [ ] 性能指标正常

## 🔍 故障排除

### 常见问题

**问题 1: 无法访问 Gitee**
```bash
# 检查网络连接
ping gitee.com

# 检查 DNS 解析
nslookup gitee.com

# 使用备用下载方式
curl -L -o sensitive-detector-v1.0.0.tar.gz https://gitee.com/your-username/sensitive-detector/releases/download/v1.0.0/sensitive-detector-v1.0.0.tar.gz
```

**问题 2: Docker 镜像拉取失败**
```bash
# 检查 Docker 镜像加速器配置
docker info | grep -A 10 "Registry Mirrors"

# 手动拉取镜像
docker pull registry.cn-hangzhou.aliyuncs.com/library/python:3.10-slim
docker tag registry.cn-hangzhou.aliyuncs.com/library/python:3.10-slim python:3.10-slim
```

**问题 3: Ollama 模型下载慢**
```bash
# 检查 Ollama 服务状态
ollama list

# 手动下载模型
ollama pull qwen:7b

# 检查模型文件
ls -la ~/.ollama/models/
```

### 网络诊断工具

**网络连接测试**:
```bash
#!/bin/bash
# network-test.sh

echo "网络连接测试"
echo "=============="

# 测试基本网络连接
echo "1. 测试基本网络连接:"
ping -c 3 8.8.8.8

# 测试 DNS 解析
echo "2. 测试 DNS 解析:"
nslookup gitee.com

# 测试 HTTPS 连接
echo "3. 测试 HTTPS 连接:"
curl -I https://gitee.com

# 测试 Docker Hub 连接
echo "4. 测试 Docker Hub 连接:"
curl -I https://registry-1.docker.io

# 测试 Ollama 连接
echo "5. 测试 Ollama 连接:"
curl -I https://ollama.ai
```

## 📞 技术支持

### 联系方式
- **Gitee 仓库**: https://gitee.com/saisai5203/sensitive-detector
- **Issues**: https://gitee.com/saisai5203/sensitive-detector/issues
- **邮箱**: support@example.com

### 获取帮助
1. 查看 [故障排除文档](TROUBLESHOOTING.md)
2. 查看 [FAQ 文档](FAQ.md)
3. 提交 [Gitee Issue](https://gitee.com/saisai5203/sensitive-detector/issues)
4. 发送邮件到技术支持邮箱

## 🔄 更新和维护

### 版本更新
```bash
# 1. 下载新版本
wget https://gitee.com/saisai5203/sensitive-detector/releases/download/v1.1.0/sensitive-detector-v1.1.0.tar.gz

# 2. 备份当前版本
cp -r sensitive-detector-v1.0.0 sensitive-detector-v1.0.0.backup

# 3. 解压新版本
tar -xzf sensitive-detector-v1.1.0.tar.gz
cd sensitive-detector-v1.1.0

# 4. 执行更新
chmod +x install.sh
./install.sh
```

### 数据备份
```bash
# 备份敏感词库
cp config/sensitive_words.txt backup/sensitive_words_$(date +%Y%m%d).txt

# 备份日志
tar -czf backup/logs_$(date +%Y%m%d).tar.gz logs/

# 备份配置
tar -czf backup/config_$(date +%Y%m%d).tar.gz config/
```

---

**文档版本**: v1.0.0  
**最后更新**: 2024年1月1日
