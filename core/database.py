import sqlite3
import os
from datetime import datetime

# 設定資料庫路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(project_root, 'data', 'crawler_data.db')

def get_db_connection():
    """建立並返回資料庫連線"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化資料庫，建立資料表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 檢查資料表是否存在，如果不存在則建立
    cursor.execute("""
        SELECT name FROM sqlite_master WHERE type='table' AND name='crawl_sessions'
    """)
    
    if cursor.fetchone() is None:
        print("建立資料表...")
        
        # 爬取任務資料表
        cursor.execute("""
        CREATE TABLE crawl_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            crawl_time DATETIME NOT NULL,
            total_products INTEGER DEFAULT 0,
            status TEXT NOT NULL,
            platforms TEXT
        );
        """)

        # 商品資訊資料表
        cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            platform TEXT NOT NULL,
            title TEXT NOT NULL,
            price INTEGER,
            url TEXT UNIQUE,
            image_url TEXT,
            is_filtered_out BOOLEAN DEFAULT 0,
            FOREIGN KEY (session_id) REFERENCES crawl_sessions (id)
        );
        """)
        # 為 url 欄位建立索引以加速查詢
        cursor.execute("CREATE INDEX idx_product_url ON products (url);")
        cursor.execute("CREATE INDEX idx_product_session_id ON products (session_id);")

        # 每日特價商品資料表
        cursor.execute("""
        CREATE TABLE daily_deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            title TEXT NOT NULL,
            price INTEGER,
            url TEXT UNIQUE,
            image_url TEXT,
            crawl_time DATETIME NOT NULL
        );
        """)
        cursor.execute("CREATE INDEX idx_daily_deals_platform ON daily_deals (platform);")

        # 商品比較結果快取表
        cursor.execute("""
        CREATE TABLE product_comparison_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_product_id INTEGER NOT NULL,
            similar_product_id INTEGER NOT NULL,
            similarity REAL NOT NULL,
            reason TEXT,
            confidence TEXT,
            category TEXT,
            cache_time DATETIME NOT NULL,
            FOREIGN KEY (target_product_id) REFERENCES daily_deals (id),
            FOREIGN KEY (similar_product_id) REFERENCES products (id)
        );
        """)
        cursor.execute("CREATE INDEX idx_comparison_cache_target ON product_comparison_cache (target_product_id);")
        cursor.execute("CREATE INDEX idx_comparison_cache_similarity ON product_comparison_cache (similarity);")

        conn.commit()
        print("資料庫初始化完成。")
    else:
        print("資料庫表已存在，跳過初始化。")
    
    conn.close()

if __name__ == '__main__':
    init_db()
