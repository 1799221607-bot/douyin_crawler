import sqlite3
import os

def migrate():
    db_path = 'douyin_crawler.db'
    if not os.path.exists(db_path):
        print(f"❌ 找不到数据库文件: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("开始检查数据库变更...")

    # 1. 为 creators 表增加字段
    columns_to_add = [
        ('priority', 'INTEGER DEFAULT 1'),
        ('is_fast_mode', 'BOOLEAN DEFAULT 0')
    ]

    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE creators ADD COLUMN {col_name} {col_type}")
            print(f"✅ 已成功添加字段: creators.{col_name}")
        except sqlite3.OperationalError:
            print(f"ℹ️ 字段 creators.{col_name} 已存在，跳过")

    # 2. 检查并创建新表 platform_accounts (如果 SQLAlchemy 还没创建的话)
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS platform_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform VARCHAR(50) NOT NULL,
            username VARCHAR(100) NOT NULL,
            cookie TEXT NOT NULL,
            proxy_url VARCHAR(500),
            ua VARCHAR(500),
            status VARCHAR(50) DEFAULT 'active',
            fail_count INTEGER DEFAULT 0,
            last_used_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("✅ 检查/创建 platform_accounts 表完成")
    except Exception as e:
        print(f"❌ 创建新表失败: {e}")

    conn.commit()
    conn.close()
    print("\n🎉 数据库迁移完成！现在可以运行 python main.py 了。")

if __name__ == "__main__":
    migrate()
