"""
Vanna 配置层：支持多种 LLM 后端 + ChromaDB + SQLite/MySQL
"""
import json
import os
import re

from openai import OpenAI
from vanna.legacy.chromadb.chromadb_vector import ChromaDB_VectorStore
from vanna.legacy.openai.openai_chat import OpenAI_Chat
from vanna.legacy.ollama.ollama import Ollama
from vanna.legacy.anthropic.anthropic_chat import Anthropic_Chat


def _clean_llm_response(raw_sql: str) -> str:
    """清理 LLM 返回中的思考过程和 markdown 标记。"""
    # 去掉 <think>...</think> 思考过程（DeepSeek / MiniMax 等模型）
    sql = re.sub(r"<think>[\s\S]*?</think>", "", raw_sql)
    # 去掉 markdown 代码块标记
    sql = re.sub(r"^```(?:sql)?\s*", "", sql)
    sql = re.sub(r"\s*```$", "", sql)
    return sql.strip()


# ── 三种 LLM 后端 ──

class OpenAI_Vanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

    def submit_prompt(self, prompt, **kwargs) -> str:
        raw = super().submit_prompt(prompt, **kwargs)
        return _clean_llm_response(raw)


class Ollama_Vanna(ChromaDB_VectorStore, Ollama):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        Ollama.__init__(self, config=config)

    def submit_prompt(self, prompt, **kwargs) -> str:
        raw = super().submit_prompt(prompt, **kwargs)
        return _clean_llm_response(raw)


class Claude_Vanna(ChromaDB_VectorStore, Anthropic_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        Anthropic_Chat.__init__(self, config=config)

    def submit_prompt(self, prompt, **kwargs) -> str:
        raw = super().submit_prompt(prompt, **kwargs)
        return _clean_llm_response(raw)


# ── 配置文件读写 ──

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}


def save_config(cfg: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ── 工厂函数 ──

def create_vanna(cfg: dict):
    """根据配置创建 Vanna 实例，返回已连接数据库的 vn 对象。"""
    llm_type = cfg.get("llm_type", "openai")
    chromadb_path = cfg.get("chromadb_path", os.path.join(os.path.dirname(__file__), "chromadb_data"))

    vanna_config = {
        "path": chromadb_path,
        "n_results_sql": cfg.get("n_results_sql", 10),
        "n_results_ddl": cfg.get("n_results_ddl", 10),
        "n_results_documentation": cfg.get("n_results_documentation", 10),
        "temperature": cfg.get("temperature", 0),
    }

    if llm_type == "openai":
        # 支持 OpenAI 兼容 API（DeepSeek / MiniMax / 通义千问等）
        client_kwargs = {"api_key": cfg.get("api_key", os.getenv("OPENAI_API_KEY", ""))}
        base_url = cfg.get("base_url", "")
        if base_url and base_url.strip():
            client_kwargs["base_url"] = base_url.strip()
        client = OpenAI(**client_kwargs)

        vanna_config["model"] = cfg.get("model", "gpt-4o-mini")
        vn = OpenAI_Vanna(config=vanna_config)
        vn.client = client  # 覆盖默认 client 以支持 base_url

    elif llm_type == "ollama":
        vanna_config["model"] = cfg.get("model", "llama3")
        vanna_config["ollama_host"] = cfg.get("ollama_host", "http://localhost:11434")
        vn = Ollama_Vanna(config=vanna_config)

    elif llm_type == "claude":
        vanna_config["api_key"] = cfg.get("api_key", os.getenv("ANTHROPIC_API_KEY", ""))
        vanna_config["model"] = cfg.get("model", "claude-sonnet-4-5")
        vanna_config["max_tokens"] = cfg.get("max_tokens", 2000)
        vn = Claude_Vanna(config=vanna_config)

    else:
        raise ValueError(f"不支持的 LLM 类型: {llm_type}")

    # 连接数据库
    _connect_db(vn, cfg)

    return vn


def _connect_db(vn, cfg: dict):
    """根据配置连接数据库。"""
    db_type = cfg.get("db_type", "sqlite")

    if db_type == "sqlite":
        db_path = cfg.get("db_path", os.path.join(os.path.dirname(__file__), "demo.db"))
        vn.connect_to_sqlite(db_path)

    elif db_type == "mysql":
        vn.connect_to_mysql(
            host=cfg.get("db_host", "localhost"),
            dbname=cfg.get("db_name", ""),
            user=cfg.get("db_user", "root"),
            password=cfg.get("db_password", ""),
            port=cfg.get("db_port", 3306),
        )

    else:
        raise ValueError(f"不支持的数据库类型: {db_type}")
