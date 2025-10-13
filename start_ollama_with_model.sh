#!/bin/bash
# 启动 Ollama 服务（后台运行）
ollama serve &
# 等待服务启动(避免服务未就绪导致模型加载失败）
sleep 3
# 启动指定模型（加载到内存）
ollama run qwen2.5:7b-instruct-q4_K_M &
