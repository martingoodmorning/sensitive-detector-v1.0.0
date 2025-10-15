# 故障排除指南 v1.0.0

**版本**: v1.0.0  
**更新时间**: 2025年10月

## 🔍 常见问题

### 1. 容器启动失败

#### 症状
- 容器状态显示 `Exited` 或 `Restarting`
- 服务无法访问

#### 排查步骤
```bash
# 检查容器状态
docker-compose ps

# 查看错误日志
docker-compose logs ollama
docker-compose logs sensitive-detector

# 检查资源使用
docker stats
```

#### 解决方案
- **内存不足**: 确保系统有 8GB+ 可用内存
- **端口冲突**: 检查端口 8000 和 11434 是否被占用
- **Docker 服务**: 确保 Docker 服务正在运行

### 2. 模型下载失败

#### 症状
- 日志显示模型下载错误
- 应用无法进行 LLM 检测

#### 排查步骤
```bash
# 检查网络连接
docker-compose exec ollama curl -I https://ollama.ai

# 检查磁盘空间
df -h

# 手动下载模型
docker-compose exec ollama ollama pull qwen3:8b-q4_K_M
```

#### 解决方案
- **网络问题**: 检查网络连接，确保可以访问 ollama.ai
- **磁盘空间**: 确保有 20GB+ 可用磁盘空间
- **权限问题**: 检查 Docker 权限设置

### 3. 健康检查失败

#### 症状
- 服务状态显示 `unhealthy`
- API 响应异常

#### 排查步骤
```bash
# 检查服务端口
curl http://localhost:8000/health
curl http://localhost:11434/api/tags

# 检查容器内部
docker-compose exec ollama ollama list
docker-compose exec sensitive-detector curl http://ollama:11434/api/tags
```

#### 解决方案
- **服务依赖**: 确保 Ollama 服务先启动
- **网络连接**: 检查容器间网络连接
- **配置错误**: 检查环境变量配置

### 4. 性能问题

#### 症状
- API 响应缓慢
- 检测超时

#### 排查步骤
```bash
# 检查资源使用
docker stats

# 检查日志中的响应时间
docker-compose logs sensitive-detector | grep "响应时间"

# 检查模型状态
docker-compose exec ollama ollama list
```

#### 解决方案
- **资源不足**: 增加内存和 CPU 资源
- **模型问题**: 检查模型是否正确加载
- **系统负载**: 检查系统整体负载

## 🛠️ 应急处理

### 服务重启
```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart ollama
docker-compose restart sensitive-detector
```

### 服务停止
```bash
# 停止所有服务
docker-compose down

# 停止并删除数据
docker-compose down -v
```

### 数据恢复
```bash
# 恢复模型数据
tar -xzf ollama-backup-20250101.tar.gz

# 重启服务
docker-compose up -d
```

## 📞 技术支持

如遇到问题，请提供以下信息：

1. **系统信息**: 操作系统版本、Docker 版本
2. **错误日志**: `docker-compose logs` 输出
3. **服务状态**: `docker-compose ps` 输出
4. **资源使用**: `docker stats` 输出
5. **网络状态**: `netstat -tlnp` 输出

---

**最后更新**: 2025年10月
**版本**: v1.0.0
