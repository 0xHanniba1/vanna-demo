"""
Vanna 训练脚本：导入 DDL schema、业务文档、Question→SQL 示例对
用法：
    python train.py                       # 首次全量训练（使用内置演示数据）
    python train.py --auto                # 自动从数据库提取表结构并训练
    python train.py --reset               # 清空训练数据后重新训练
    python train.py --add-pair            # 交互式追加 question→SQL 对
    python train.py --add-doc             # 交互式追加业务文档
"""
import argparse
import sys

from vanna_config import create_vanna, load_config


# ── 表结构 DDL ──

DDL_STATEMENTS = [
    """CREATE TABLE departments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,         -- 部门名称（如：销售部、技术部、市场部、财务部、人事部）
    manager TEXT                -- 部门经理姓名
)""",
    """CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,         -- 员工姓名
    department_id INTEGER,      -- 所属部门ID，关联 departments.id
    position TEXT,              -- 职位（经理/高级工程师/工程师/助理/实习生/主管/专员）
    salary DECIMAL(10,2),       -- 月薪（人民币）
    hire_date DATE,             -- 入职日期
    FOREIGN KEY (department_id) REFERENCES departments(id)
)""",
    """CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,         -- 客户名称（企业客户，如：腾讯科技、阿里巴巴等）
    city TEXT,                  -- 所在城市（北京/上海/广州/深圳/杭州/成都/武汉/南京/西安/重庆）
    level TEXT,                 -- 客户等级：VIP / 金牌 / 银牌 / 普通
    register_date DATE          -- 注册日期
)""",
    """CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,         -- 产品名称
    category TEXT,              -- 产品类别（云服务/软件/安全/AI/工具/运维）
    price DECIMAL(10,2),        -- 单价（人民币）
    stock INTEGER               -- 库存数量
)""",
    """CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER,        -- 客户ID，关联 customers.id
    employee_id INTEGER,        -- 负责员工ID，关联 employees.id
    product_id INTEGER,         -- 产品ID，关联 products.id
    quantity INTEGER,           -- 购买数量
    total_amount DECIMAL(10,2), -- 订单总金额（人民币，含折扣）
    order_date DATE,            -- 下单日期
    status TEXT,                -- 订单状态：已完成 / 处理中 / 已取消 / 待付款
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
)""",
]


# ── 业务文档 ──

DOCUMENTATION = [
    "这是一个 B2B 电商业务系统，公司销售云服务、软件、AI 产品等给企业客户。",
    "客户分为 VIP、金牌、银牌、普通四个等级，VIP 客户享受优先服务和更高折扣。",
    "订单状态包括：已完成、处理中、已取消、待付款。统计销售额时通常只计算「已完成」的订单。",
    "部门包括：销售部、技术部、市场部、财务部、人事部。每个部门有一个经理。",
    "数据库使用 SQLite，日期函数使用 strftime，例如 strftime('%Y-%m', order_date) 提取年月。",
]


# ── Question → SQL 示例对 ──

QUESTION_SQL_PAIRS = [
    (
        "一共有多少条订单？",
        "SELECT COUNT(*) AS 订单总数 FROM orders",
    ),
    (
        "统计已完成的订单总数",
        "SELECT COUNT(*) AS 订单总数 FROM orders WHERE status = '已完成'",
    ),
    (
        "每个部门的平均薪资是多少？",
        "SELECT d.name AS 部门, ROUND(AVG(e.salary), 2) AS 平均薪资 FROM employees e JOIN departments d ON e.department_id = d.id GROUP BY d.name ORDER BY 平均薪资 DESC",
    ),
    (
        "各城市客户的订单总金额",
        "SELECT c.city AS 城市, ROUND(SUM(o.total_amount), 2) AS 总金额 FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.status = '已完成' GROUP BY c.city ORDER BY 总金额 DESC",
    ),
    (
        "销售额最高的产品",
        "SELECT p.name AS 产品名称, ROUND(SUM(o.total_amount), 2) AS 销售总额 FROM orders o JOIN products p ON o.product_id = p.id WHERE o.status = '已完成' GROUP BY p.name ORDER BY 销售总额 DESC LIMIT 1",
    ),
    (
        "每月订单数量趋势",
        "SELECT strftime('%Y-%m', order_date) AS 月份, COUNT(*) AS 订单数 FROM orders GROUP BY 月份 ORDER BY 月份",
    ),
    (
        "VIP 客户有哪些？",
        "SELECT name AS 客户名称, city AS 城市 FROM customers WHERE level = 'VIP'",
    ),
    (
        "薪资最高的 5 个员工是谁？",
        "SELECT e.name AS 姓名, d.name AS 部门, e.position AS 职位, e.salary AS 月薪 FROM employees e JOIN departments d ON e.department_id = d.id ORDER BY e.salary DESC LIMIT 5",
    ),
    (
        "哪个员工的订单数量最多？",
        "SELECT e.name AS 员工姓名, COUNT(o.id) AS 订单数量 FROM orders o JOIN employees e ON o.employee_id = e.id GROUP BY e.name ORDER BY 订单数量 DESC LIMIT 1",
    ),
    (
        "各产品类别的销售额占比",
        "SELECT p.category AS 产品类别, ROUND(SUM(o.total_amount), 2) AS 销售额 FROM orders o JOIN products p ON o.product_id = p.id WHERE o.status = '已完成' GROUP BY p.category ORDER BY 销售额 DESC",
    ),
    (
        "已取消的订单有多少？",
        "SELECT COUNT(*) AS 已取消订单数 FROM orders WHERE status = '已取消'",
    ),
    (
        "销售额 Top 5 的产品",
        "SELECT p.name AS 产品名称, ROUND(SUM(o.total_amount), 2) AS 销售总额 FROM orders o JOIN products p ON o.product_id = p.id WHERE o.status = '已完成' GROUP BY p.name ORDER BY 销售总额 DESC LIMIT 5",
    ),
]


def train_all(vn, reset=False):
    """执行全量训练。"""
    if reset:
        print("清空已有训练数据...")
        vn.remove_collection("ddl")
        vn.remove_collection("sql")
        vn.remove_collection("documentation")
        print("已清空。\n")

    # 1. 训练 DDL
    print("=== 训练 DDL（表结构）===")
    for ddl in DDL_STATEMENTS:
        table_name = ddl.split("(")[0].strip().split()[-1]
        vn.train(ddl=ddl)
        print(f"  + {table_name}")

    # 2. 训练业务文档
    print("\n=== 训练业务文档 ===")
    for doc in DOCUMENTATION:
        vn.train(documentation=doc)
        print(f"  + {doc[:40]}...")

    # 3. 训练 Question → SQL 对
    print("\n=== 训练 Question → SQL 对 ===")
    for question, sql in QUESTION_SQL_PAIRS:
        vn.train(question=question, sql=sql)
        print(f"  + {question}")

    print(f"\n训练完成！共 {len(DDL_STATEMENTS)} 个 DDL, {len(DOCUMENTATION)} 条文档, {len(QUESTION_SQL_PAIRS)} 个 Q&A 对。")


def train_auto(vn, cfg, reset=False):
    """自动从数据库提取表结构并训练。"""
    db_type = cfg.get("db_type", "sqlite")

    if reset:
        print("清空已有训练数据...")
        vn.remove_collection("ddl")
        vn.remove_collection("sql")
        vn.remove_collection("documentation")
        print("已清空。\n")

    # 1. 自动提取 DDL
    print("=== 从数据库自动提取表结构 ===")
    ddl_list = []

    if db_type == "sqlite":
        import sqlite3
        db_path = cfg.get("db_path", "demo.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        for table_name, create_sql in cursor.fetchall():
            if create_sql:
                ddl_list.append((table_name, create_sql))
        conn.close()

    elif db_type == "mysql":
        import pymysql
        conn = pymysql.connect(
            host=cfg.get("db_host", "localhost"),
            user=cfg.get("db_user", "root"),
            password=cfg.get("db_password", ""),
            database=cfg.get("db_name", ""),
            port=cfg.get("db_port", 3306),
            charset="utf8mb4",
        )
        cursor = conn.cursor()

        # 获取所有表名
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]

        for table_name in tables:
            # 获取建表语句（包含字段注释）
            cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
            create_sql = cursor.fetchone()[1]
            ddl_list.append((table_name, create_sql))

        conn.close()

    if not ddl_list:
        print("  未找到任何表，请检查数据库配置。")
        return

    for table_name, ddl in ddl_list:
        vn.train(ddl=ddl)
        print(f"  + {table_name}")

    # 2. 训练基础文档
    print(f"\n=== 训练基础文档 ===")
    if db_type == "mysql":
        db_doc = f"数据库类型是 MySQL，日期函数使用 DATE_FORMAT，当前日期用 CURDATE()，数据库名称是 {cfg.get('db_name', '')}。"
    else:
        db_doc = "数据库类型是 SQLite，日期函数使用 strftime，例如 strftime('%Y-%m', date_col) 提取年月。"
    vn.train(documentation=db_doc)
    print(f"  + {db_doc[:50]}...")

    print(f"\n自动训练完成！共提取 {len(ddl_list)} 张表。")
    print("提示：建议运行 python train.py --add-doc 补充业务文档，帮助 AI 理解业务含义。")


def add_pair_interactive(vn):
    """交互式追加 question→SQL 对。"""
    print("输入 question→SQL 对（输入空行结束）：\n")
    while True:
        question = input("Question: ").strip()
        if not question:
            break
        sql = input("SQL: ").strip()
        if not sql:
            break
        vn.train(question=question, sql=sql)
        print(f"  + 已添加: {question}\n")


def add_doc_interactive(vn):
    """交互式追加业务文档。"""
    print("输入业务文档（每行一条，输入空行结束）：")
    print("例如：订单状态包括已完成、处理中、已取消，统计收入时只算已完成的。\n")
    while True:
        doc = input("文档: ").strip()
        if not doc:
            break
        vn.train(documentation=doc)
        print(f"  + 已添加\n")


def show_training_data(vn):
    """展示当前训练数据统计。"""
    df = vn.get_training_data()
    if df.empty:
        print("暂无训练数据。")
        return
    print("\n=== 训练数据统计 ===")
    counts = df["training_data_type"].value_counts()
    for dtype, count in counts.items():
        print(f"  {dtype}: {count} 条")
    print(f"  总计: {len(df)} 条")


def main():
    parser = argparse.ArgumentParser(description="Vanna 训练脚本")
    parser.add_argument("--auto", action="store_true", help="自动从数据库提取表结构并训练")
    parser.add_argument("--reset", action="store_true", help="清空已有训练数据后重新训练")
    parser.add_argument("--add-pair", action="store_true", help="交互式追加 question→SQL 对")
    parser.add_argument("--add-doc", action="store_true", help="交互式追加业务文档")
    parser.add_argument("--show", action="store_true", help="展示当前训练数据统计")
    args = parser.parse_args()

    cfg = load_config()
    if not cfg:
        print("请先创建 config.json，或通过 Streamlit 界面配置。")
        sys.exit(1)

    # 训练只需 ChromaDB 本地 embedding，不需要 LLM API Key
    # 设置占位 key 避免 OpenAI 客户端初始化报错
    if not cfg.get("api_key") and cfg.get("llm_type", "openai") != "ollama":
        cfg["api_key"] = "sk-placeholder-for-training"

    vn = create_vanna(cfg)

    if args.show:
        show_training_data(vn)
    elif args.add_pair:
        add_pair_interactive(vn)
    elif args.add_doc:
        add_doc_interactive(vn)
    elif args.auto:
        train_auto(vn, cfg, reset=args.reset)
        show_training_data(vn)
    else:
        train_all(vn, reset=args.reset)
        show_training_data(vn)


if __name__ == "__main__":
    main()
