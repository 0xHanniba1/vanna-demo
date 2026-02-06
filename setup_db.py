"""
创建示例 SQLite 数据库 - 模拟一个电商业务场景
包含：部门、员工、客户、产品、订单等表
"""
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "demo.db"


def create_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 部门表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            manager TEXT
        )
    """)

    # 员工表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department_id INTEGER,
            position TEXT,
            salary DECIMAL(10,2),
            hire_date DATE,
            FOREIGN KEY (department_id) REFERENCES departments(id)
        )
    """)

    # 客户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT,
            level TEXT,
            register_date DATE
        )
    """)

    # 产品表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            price DECIMAL(10,2),
            stock INTEGER
        )
    """)

    # 订单表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            employee_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            total_amount DECIMAL(10,2),
            order_date DATE,
            status TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # 插入部门数据
    departments = [
        (1, "销售部", "张伟"),
        (2, "技术部", "李娜"),
        (3, "市场部", "王芳"),
        (4, "财务部", "赵敏"),
        (5, "人事部", "陈静"),
    ]
    cursor.executemany("INSERT OR IGNORE INTO departments VALUES (?,?,?)", departments)

    # 插入员工数据
    names = [
        "张伟", "李娜", "王芳", "赵敏", "陈静",
        "刘洋", "杨磊", "黄丽", "周杰", "吴敏",
        "徐强", "孙颖", "马超", "朱婷", "胡明",
        "郭靖", "林峰", "何雪", "高远", "罗琳",
    ]
    positions = ["经理", "高级工程师", "工程师", "助理", "实习生", "主管", "专员"]
    employees = []
    for i, name in enumerate(names, 1):
        dept_id = random.randint(1, 5)
        pos = random.choice(positions)
        salary = round(random.uniform(5000, 35000), 2)
        hire_date = (datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1800))).strftime("%Y-%m-%d")
        employees.append((i, name, dept_id, pos, salary, hire_date))
    cursor.executemany("INSERT OR IGNORE INTO employees VALUES (?,?,?,?,?,?)", employees)

    # 插入客户数据
    cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "南京", "西安", "重庆"]
    levels = ["VIP", "金牌", "银牌", "普通"]
    customer_names = [
        "腾讯科技", "阿里巴巴", "字节跳动", "华为技术", "小米科技",
        "京东集团", "美团点评", "百度在线", "网易公司", "拼多多",
        "滴滴出行", "快手科技", "蚂蚁金服", "携程旅行", "哔哩哔哩",
        "新浪微博", "搜狐公司", "唯品会", "贝壳找房", "猿辅导",
    ]
    customers = []
    for i, name in enumerate(customer_names, 1):
        city = random.choice(cities)
        level = random.choice(levels)
        reg_date = (datetime(2021, 1, 1) + timedelta(days=random.randint(0, 1400))).strftime("%Y-%m-%d")
        customers.append((i, name, city, level, reg_date))
    cursor.executemany("INSERT OR IGNORE INTO customers VALUES (?,?,?,?,?)", customers)

    # 插入产品数据
    product_list = [
        (1, "企业云服务器", "云服务", 9999.00, 500),
        (2, "数据分析平台", "软件", 29999.00, 200),
        (3, "智能客服系统", "软件", 15999.00, 300),
        (4, "网络安全套件", "安全", 19999.00, 150),
        (5, "办公协作工具", "软件", 4999.00, 800),
        (6, "AI 训练平台", "AI", 49999.00, 100),
        (7, "大数据存储", "云服务", 12999.00, 400),
        (8, "移动开发框架", "工具", 7999.00, 600),
        (9, "API 网关服务", "云服务", 5999.00, 700),
        (10, "监控告警系统", "运维", 8999.00, 350),
    ]
    cursor.executemany("INSERT OR IGNORE INTO products VALUES (?,?,?,?,?)", product_list)

    # 插入订单数据 (200条)
    statuses = ["已完成", "处理中", "已取消", "待付款"]
    orders = []
    for i in range(1, 201):
        cust_id = random.randint(1, 20)
        emp_id = random.randint(1, 20)
        prod_id = random.randint(1, 10)
        qty = random.randint(1, 20)
        # 查找产品价格
        price = product_list[prod_id - 1][3]
        total = round(price * qty * random.uniform(0.8, 1.0), 2)  # 带折扣
        order_date = (datetime(2024, 1, 1) + timedelta(days=random.randint(0, 400))).strftime("%Y-%m-%d")
        status = random.choices(statuses, weights=[60, 20, 10, 10])[0]
        orders.append((i, cust_id, emp_id, prod_id, qty, total, order_date, status))
    cursor.executemany("INSERT OR IGNORE INTO orders VALUES (?,?,?,?,?,?,?,?)", orders)

    conn.commit()
    conn.close()
    print(f"数据库 {DB_PATH} 创建成功！")
    print(f"  - 5 个部门")
    print(f"  - {len(employees)} 个员工")
    print(f"  - {len(customers)} 个客户")
    print(f"  - {len(product_list)} 个产品")
    print(f"  - {len(orders)} 条订单")


if __name__ == "__main__":
    create_database()
