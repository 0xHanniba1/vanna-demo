"""
Vanna AI Text-to-SQL —— Streamlit 自定义 UI
底层使用 Vanna 库（ChromaDB 向量检索 + 可切换 LLM）
"""
import os
import streamlit as st
import pandas as pd

from vanna_config import create_vanna, load_config, save_config


# ──────────────────────────────────────────────
# Streamlit 界面
# ──────────────────────────────────────────────
def main():
    st.set_page_config(page_title="Vanna AI Text-to-SQL", page_icon="🤖", layout="wide")

    st.title("🤖 Text-to-SQL Demo")
    st.caption("用自然语言查询数据库，Vanna AI 自动检索相关 schema 并生成 SQL")

    # ── 侧边栏：配置 ──
    with st.sidebar:
        st.header("⚙️ 配置")

        cfg = load_config()

        llm_type = st.selectbox(
            "LLM 后端",
            ["openai", "ollama", "claude"],
            index=["openai", "ollama", "claude"].index(cfg.get("llm_type", "openai")),
            help="openai: 兼容 OpenAI/DeepSeek/MiniMax 等; ollama: 本地模型; claude: Anthropic",
        )

        if llm_type in ("openai", "claude"):
            api_key = st.text_input(
                "API Key",
                type="password",
                value=cfg.get("api_key", ""),
                help="输入你的 API Key",
            )
        else:
            api_key = ""

        if llm_type == "openai":
            base_url = st.text_input(
                "Base URL（可选）",
                value=cfg.get("base_url", ""),
                help="中转/代理 API 地址，留空则用 OpenAI 官方",
                placeholder="https://api.openai.com/v1",
            )
        else:
            base_url = ""

        if llm_type == "ollama":
            ollama_host = st.text_input(
                "Ollama Host",
                value=cfg.get("ollama_host", "http://localhost:11434"),
            )
        else:
            ollama_host = ""

        model = st.text_input(
            "模型名称",
            value=cfg.get("model", "MiniMax-Text-01"),
            help="如 MiniMax-Text-01、gpt-4o-mini、deepseek-chat、llama3、claude-sonnet-4-5",
        )

        st.divider()
        st.header("🗄️ 数据库")

        db_type = st.selectbox(
            "数据库类型",
            ["sqlite", "mysql"],
            index=["sqlite", "mysql"].index(cfg.get("db_type", "sqlite")),
        )

        if db_type == "sqlite":
            db_path = st.text_input(
                "SQLite 文件路径",
                value=cfg.get("db_path", "demo.db"),
            )
        else:
            db_host = st.text_input("MySQL Host", value=cfg.get("db_host", "localhost"))
            db_port = st.number_input("MySQL Port", value=cfg.get("db_port", 3306), step=1)
            db_user = st.text_input("MySQL User", value=cfg.get("db_user", "root"))
            db_password = st.text_input("MySQL Password", type="password", value=cfg.get("db_password", ""))
            db_name = st.text_input("MySQL Database", value=cfg.get("db_name", ""))

        # 保存配置按钮
        if st.button("💾 保存配置"):
            new_cfg = {
                "llm_type": llm_type,
                "api_key": api_key,
                "base_url": base_url,
                "ollama_host": ollama_host,
                "model": model,
                "db_type": db_type,
            }
            if db_type == "sqlite":
                new_cfg["db_path"] = db_path
            else:
                new_cfg.update({
                    "db_host": db_host,
                    "db_port": int(db_port),
                    "db_user": db_user,
                    "db_password": db_password,
                    "db_name": db_name,
                })
            save_config(new_cfg)
            st.success("配置已保存！")
            st.rerun()

        st.divider()
        st.header("💡 试试这些问题")
        example_questions = [
            "一共有多少条订单？",
            "每个部门的平均薪资是多少？",
            "哪个城市的订单金额最高？",
            "销售额 Top 5 的产品",
            "每月订单数量趋势",
            "VIP 客户有哪些？",
            "薪资最高的 5 个员工是谁？",
            "哪个员工的订单数量最多？",
            "各产品类别的销售额占比",
            "已取消的订单有多少？",
        ]
        for q in example_questions:
            st.code(q, language=None)

    # ── 主区域 ──
    cfg = load_config()

    if not cfg.get("api_key") and cfg.get("llm_type", "openai") != "ollama":
        st.warning("👈 请在左侧边栏配置 API Key 并保存")
        st.stop()

    # 初始化 Vanna（缓存避免重复创建）
    @st.cache_resource
    def get_vanna(_cfg_hash):
        return create_vanna(load_config())

    cfg_hash = str(sorted(cfg.items()))
    try:
        vn = get_vanna(cfg_hash)
    except Exception as e:
        st.error(f"初始化失败：{e}")
        st.stop()

    # 训练数据统计
    try:
        training_data = vn.get_training_data()
        if training_data.empty:
            st.warning("⚠️ 暂无训练数据，请先运行 `python train.py` 导入 schema 和示例。")
        else:
            counts = training_data["training_data_type"].value_counts().to_dict()
            cols = st.columns(3)
            cols[0].metric("DDL", counts.get("ddl", 0))
            cols[1].metric("文档", counts.get("documentation", 0))
            cols[2].metric("Q&A 对", counts.get("sql", 0))
    except Exception:
        pass

    st.success("✅ Vanna 已就绪！输入自然语言问题，AI 会检索相关 schema 并生成 SQL。")

    # 聊天历史
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 显示历史消息
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "sql" in msg:
                st.code(msg["sql"], language="sql")
            if "df" in msg and msg["df"] is not None:
                st.dataframe(msg["df"], use_container_width=True)

    # 用户输入
    if question := st.chat_input("输入你的问题，例如：每个部门的平均薪资是多少？"):
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("🧠 Vanna 正在检索相关 schema 并生成 SQL..."):
                try:
                    sql = vn.generate_sql(question=question)

                    if sql and sql.strip():
                        st.markdown("**生成的 SQL：**")
                        st.code(sql, language="sql")

                        df = vn.run_sql(sql)

                        if df is not None and not df.empty:
                            st.markdown(f"**查询结果（{len(df)} 行）：**")
                            st.dataframe(df, use_container_width=True)

                            if len(df.columns) >= 2 and len(df) > 1:
                                try:
                                    numeric_cols = df.select_dtypes(include=["number"]).columns
                                    if len(numeric_cols) >= 1:
                                        st.bar_chart(df.set_index(df.columns[0])[numeric_cols[0]])
                                except Exception:
                                    pass

                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": f"查询结果（{len(df)} 行）：",
                                "sql": sql,
                                "df": df,
                            })
                        else:
                            st.info("查询执行成功，但没有返回数据。")
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": "查询执行成功，但没有返回数据。",
                                "sql": sql,
                            })
                    else:
                        st.warning("无法生成 SQL，请尝试换一种方式描述你的问题。")
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": "无法生成 SQL，请尝试换一种方式描述你的问题。",
                        })

                except Exception as e:
                    error_msg = f"出错了：{str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                    })


if __name__ == "__main__":
    main()
