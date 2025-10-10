# Gitee 快速开始指南

## 概述

本指南专门为国内用户提供基于 Gitee 的快速部署方案，解决网络访问限制问题。

## 🚀 一键部署

### 方法一：使用部署脚本（推荐）

```bash
# 1. 下载部署脚本
wget https://gitee.com/your-username/sensitive-detector/raw/main/scripts/gitee-deploy.sh

# 2. 赋予执行权限
chmod +x gitee-deploy.sh

# 3. 执行部署
./gitee-deploy.sh

# 4. 访问系统
# 浏览器打开: http://localhost:8000
```

### 方法二：手动部署

```bash
# 1. 下载部署包
wget https://gitee.com/your-username/sensitive-detector/releases/download/v1.0.0/sensitive-detector-v1.0.0.tar.gz

# 2. 解压部署包
tar -xzf sensitive-detector-v1.0.0.tar.gz
cd sensitive-detector-v1.0.0

# 3. 一键安装
chmod +x install.sh
./install.sh

# 4. 访问系统
# 浏览器打开: http://localhost:8000
```

## 📋 系统要求

### 硬件要求
- **CPU**: 4核以上 (推荐 8核)
- **内存**: 8GB 以上 (推荐 16GB)
- **存储**: 20GB 以上可用空间
- **网络**: 稳定的网络连接

### 软件要求
- **操作系统**: Linux (Ubuntu 20.04+, CentOS 8+)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

## 🔧 网络优化

### Docker 镜像加速

```bash
# 配置 Docker 镜像加速器
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

### DNS 配置

```bash
# 配置国内 DNS
sudo tee /etc/systemd/resolved.conf <<-'EOF'
[Resolve]
DNS=223.5.5.5 223.6.6.6
FallbackDNS=8.8.8.8 8.8.4.4
EOF

# 重启 DNS 服务
sudo systemctl restart systemd-resolved
```

## 📦 部署包内容

```
sensitive-detector-v1.0.0/
├── install.sh              # 一键安装脚本
├── docker-compose.yml      # Docker 配置
├── config/
│   └── sensitive_words.txt # 敏感词库
├── scripts/
│   ├── deploy.sh          # 部署脚本
│   └── backup.sh          # 备份脚本
├── docs/
│   ├── README.md          # 说明文档
│   └── API.md             # API 文档
└── examples/
    └── config.example/     # 配置示例
```

## 🎯 功能特性

- **文本检测**: 实时文本敏感词检测
- **文档检测**: 支持 TXT、PDF、DOCX 格式
- **双重检测**: 规则匹配 + LLM 智能检测
- **Web 界面**: 现代化响应式设计
- **容器化**: Docker 一键部署

## 🔍 故障排除

### 常见问题

**问题 1: 无法访问 Gitee**
```bash
# 检查网络连接
ping gitee.com

# 使用备用下载方式
curl -L -o package.tar.gz https://gitee.com/your-username/sensitive-detector/releases/download/v1.0.0/sensitive-detector-v1.0.0.tar.gz
```

**问题 2: Docker 镜像拉取失败**
```bash
# 检查镜像加速器配置
docker info | grep -A 10 "Registry Mirrors"

# 手动拉取镜像
docker pull registry.cn-hangzhou.aliyuncs.com/library/python:3.10-slim
```

**问题 3: Ollama 模型下载慢**
```bash
# 检查 Ollama 服务状态
ollama list

# 手动下载模型
ollama pull qwen:7b
```

### 网络诊断

```bash
# 网络连接测试
ping -c 3 8.8.8.8

# DNS 解析测试
nslookup gitee.com

# HTTPS 连接测试
curl -I https://gitee.com
```

## 📞 技术支持

### 联系方式
- **Gitee 仓库**: https://gitee.com/your-username/sensitive-detector
- **Issues**: https://gitee.com/your-username/sensitive-detector/issues
- **邮箱**: support@example.com

### 获取帮助
1. 查看 [故障排除文档](docs/TROUBLESHOOTING.md)
2. 查看 [FAQ 文档](docs/FAQ.md)
3. 提交 [Gitee Issue](https://gitee.com/your-username/sensitive-detector/issues)
4. 发送邮件到技术支持邮箱

## 🔄 更新和维护

### 版本更新
```bash
# 1. 下载新版本
wget https://gitee.com/your-username/sensitive-detector/releases/download/v1.1.0/sensitive-detector-v1.1.0.tar.gz

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

## 📋 部署检查清单

### 部署前检查
- [ ] 系统要求满足
- [ ] 网络连接正常
- [ ] Docker 已安装
- [ ] Docker Compose 已安装
- [ ] 防火墙配置正确

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

---

**文档版本**: v1.0.0  
**最后更新**: 2024年1月1日
