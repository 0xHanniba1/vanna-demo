# Vanna AI Text-to-SQL Demo

基于 [Vanna](https://github.com/vanna-ai/vanna) 的 Text-to-SQL 演示项目。用自然语言查询数据库，AI 自动检索相关 Schema 并生成 SQL。

## 特性

- **RAG 增强**：Schema、业务文档、示例 SQL 存入 ChromaDB 向量库，提问时自动检索相关上下文（而非全部塞入 prompt），适合大型数据库
- **多 LLM 后端**：支持 OpenAI 兼容 API（DeepSeek / MiniMax / 通义千问等）、Anthropic Claude、Ollama 本地模型，配置文件一行切换
- **多数据库支持**：SQLite（演示）+ MySQL（生产），可扩展 PostgreSQL 等
- **双 UI**：Streamlit 自定义界面（正式使用）+ Vanna Flask 内置界面（快速体验）
- **持续学习**：通过追加 Question→SQL 对不断提升准确率

## 项目结构

```
├── vanna_config.py    # 核心配置：LLM/数据库/向量库初始化 + 工厂函数
├── train.py           # 训练脚本：导入 DDL、业务文档、Q&A 对到 ChromaDB
├── app.py             # Streamlit UI（推荐，可在界面配置 LLM 和数据库）
├── app_flask.py       # Vanna 自带 Flask UI（极简一键启动）
├── setup_db.py        # 创建 SQLite 演示数据库（5 表 200+ 条数据）
├── requirements.txt   # Python 依赖
├── config.json        # 运行时配置（API Key 等，不提交到 Git）
├── demo.db            # SQLite 演示数据库
└── chromadb_data/     # ChromaDB 训练数据持久化目录（不提交到 Git）
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 创建演示数据库

```bash
python setup_db.py
```

### 3. 训练

```bash
python train.py
```

训练完成后会在本地 `chromadb_data/` 目录生成向量数据，包含 5 个 DDL、5 条业务文档、12 个 Q&A 对。

### 4. 启动

```bash
# Streamlit 界面（推荐）
streamlit run app.py

# 或 Vanna Flask 界面
python app_flask.py
```

### 5. 配置 API

在 Streamlit 左侧边栏填写：

| 字段 | 说明 | 示例 |
|------|------|------|
| LLM 后端 | openai / ollama / claude | openai |
| API Key | 你的 API 密钥 | sk-xxx |
| Base URL | 中转/兼容 API 地址（可选） | https://api.minimaxi.com/v1 |
| 模型名称 | 模型标识 | MiniMax-M2.1-lightning |

点击「保存配置」后即可在底部输入框提问。

## 训练管理

```bash
# 全量训练（首次）
python train.py

# 清空后重新训练
python train.py --reset

# 查看训练数据统计
python train.py --show

# 交互式追加 Question→SQL 对
python train.py --add-pair
```

## 切换到 MySQL

1. 侧边栏数据库类型选 `mysql`，填写连接信息并保存
2. 修改 `train.py` 中的 `DDL_STATEMENTS` 和 `DOCUMENTATION` 为实际表结构和业务说明
3. 运行 `python train.py --reset` 重新训练

## 配置文件示例

`config.json`（不提交到 Git）：

```json
{
  "llm_type": "openai",
  "api_key": "sk-xxx",
  "base_url": "https://api.minimaxi.com/v1",
  "model": "MiniMax-M2.1-lightning",
  "db_type": "sqlite",
  "db_path": "demo.db"
}
```

## 工作原理

```
用户提问 → Vanna 从 ChromaDB 检索相关 Schema/文档/示例
         → 组装 Prompt 发送到 LLM
         → LLM 返回 SQL
         → 执行 SQL 并展示结果 + 图表
```

相比直接将全部 Schema 塞入 Prompt，Vanna 的 RAG 方式在大型数据库（几十上百张表）中优势明显：只检索与问题相关的表结构和示例，避免 token 浪费和上下文溢出。
