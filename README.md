# DBCapture - 数据库结构对比工具

DBCapture 是一个强大的数据库结构对比工具，用于比较两个MySQL数据库之间的差异，包括数据库配置、表结构、视图、存储过程、函数和触发器等。

## 主要功能

- 数据库配置对比（字符集、排序规则等）
- 表结构对比及变更SQL生成
- 视图对比及变更SQL生成
- 存储过程对比及变更SQL生成
- 自定义函数对比及变更SQL生成
- 触发器对比及变更SQL生成
- 对比结果存储及版本管理
- HTML/PDF报告导出
- 支持手动和定时任务
- 可配置对比规则和忽略项
- 企业微信机器人通知集成

## 安装要求

- Python 3.8+
- MySQL 5.7+
- 相关Python包（见requirements.txt）

## 快速开始

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/dbcapture.git
cd dbcapture
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
复制`.env.example`文件为`.env`并填写相关配置。

5. 初始化数据库：
```bash
alembic upgrade head
```

6. 启动应用：
```bash
uvicorn app.main:app --reload
```

## 配置说明

详细的配置说明请参考 `docs/configuration.md`。

## API文档

启动应用后访问 `http://localhost:8000/docs` 查看API文档。

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

MIT License
