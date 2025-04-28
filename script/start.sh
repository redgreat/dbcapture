#!/bin/bash

# 设置环境变量
export SECRET_KEY="7H3<jOU[}=GzwB^/dc)J|"6)>A-:hO}I,Ze~>6kU["<@OFK\{C"
export PYTHONPATH=$PYTHONPATH:$(pwd)

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "警告：未检测到虚拟环境，建议在虚拟环境中运行"
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 检查依赖是否安装
if [ ! -f "requirements.txt" ]; then
    echo "错误：未找到requirements.txt文件"
    exit 1
fi

# 安装依赖
echo "正在安装依赖..."
pip install -r requirements.txt

# 创建必要的目录
mkdir -p reports
mkdir -p log

# 启动应用
echo "正在启动应用..."
uvicorn app.main:app --reload
