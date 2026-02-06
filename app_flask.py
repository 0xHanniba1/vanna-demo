"""
Vanna Flask UI —— 一键启动，快速体验
用法：python app_flask.py
"""
from vanna.legacy.flask import VannaFlaskApp
from vanna_config import create_vanna, load_config


def main():
    cfg = load_config()
    vn = create_vanna(cfg)

    app = VannaFlaskApp(
        vn,
        title="Vanna Text-to-SQL",
        subtitle="用自然语言查询数据库",
        show_training_data=True,
        allow_llm_to_see_data=True,
    )
    app.run(host="0.0.0.0", port=8084)


if __name__ == "__main__":
    main()
