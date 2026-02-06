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

训练不是每天都要做的事，而是**建库时做一次，答错时补一次**。就像带新员工：入职时给他看文档，犯错时纠正一下，纠正几次后就越来越熟了。

> 注意：日常查询**不会自动**加入知识库。知识库只在你主动运行 `train.py` 时才会变化。

### 什么时候需要训练

| 时机 | 做什么 | 命令 |
|------|--------|------|
| **初始化** — 刚接入一个新数据库 | 自动提取表结构并训练 | `python train.py --auto` |
| **数据库变了** — 加了新表、改了字段 | 清空后重新自动提取 | `python train.py --auto --reset` |
| **AI 答错了** — 生成的 SQL 不正确 | 把正确的 question→SQL 喂给它 | `python train.py --add-pair` |
| **补充业务知识** — AI 不理解业务含义 | 追加业务文档 | `python train.py --add-doc` |

### 命令参考

```bash
# 自动从数据库提取表结构并训练（推荐，适合实际项目）
python train.py --auto

# 清空后重新自动提取（数据库结构变了时用）
python train.py --auto --reset

# 使用内置演示数据训练（仅用于 demo）
python train.py

# 查看训练数据统计
python train.py --show

# 交互式追加 Question→SQL 对（AI 答错了时用）
python train.py --add-pair

# 交互式追加业务文档（补充业务知识）
python train.py --add-doc
```

### 示例：自动提取 + 补充业务知识 + 纠正错误

```bash
# 第一步：自动提取表结构（不用手写 DDL）
$ python train.py --auto
=== 从数据库自动提取表结构 ===
  + departments
  + employees
  + customers
  + products
  + orders
自动训练完成！共提取 5 张表。

# 第二步：补充业务文档（帮 AI 理解业务含义）
$ python train.py --add-doc
文档: 订单状态包括已完成、处理中、已取消、待付款，统计销售额时只算已完成的
  + 已添加
文档: 客户分为VIP、金牌、银牌、普通四个等级
  + 已添加
文档:
（输入空行结束）

# 第三步：日常使用中 AI 答错了，纠正它
$ python train.py --add-pair
Question: 上季度 VIP 客户的订单总额
SQL: SELECT SUM(o.total_amount) AS 总额 FROM orders o JOIN customers c ON o.customer_id = c.id WHERE c.level = 'VIP' AND o.status = '已完成' AND o.order_date >= date('now', '-3 months')
  + 已添加: 上季度 VIP 客户的订单总额
```

## 切换到 MySQL

1. 侧边栏数据库类型选 `mysql`，填写连接信息并保存
2. 运行 `python train.py --auto --reset` 自动提取表结构
3. 运行 `python train.py --add-doc` 补充业务文档

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
