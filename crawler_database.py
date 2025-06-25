#!/usr/bin/env python3
"""
SQLite 資料庫管理模組
用於儲存和管理爬蟲資料
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class CrawlerDatabase:
    def __init__(self, db_path: str = "crawler_data.db"):
        """初始化資料庫連接"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """建立資料庫表格"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 建立爬蟲執行記錄表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS crawl_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    keyword TEXT,
                    total_products INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'success',
                    execution_time REAL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 建立商品資料表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    title TEXT NOT NULL,
                    price TEXT,
                    price_numeric REAL,
                    image_url TEXT,
                    product_url TEXT,
                    platform TEXT NOT NULL,
                    crawl_time TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES crawl_sessions (id)
                )
            ''')
            
            # 建立每日促銷快取表（用於快速查詢）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_deals_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 建立索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_platform ON products(platform)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_crawl_time ON products(crawl_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_platform ON crawl_sessions(platform)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_timestamp ON crawl_sessions(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_deals_platform ON daily_deals_cache(platform)')
            
            conn.commit()
            print("✅ 資料庫初始化完成")
    
    def parse_price(self, price_str) -> float:
        """解析價格字串或數字轉為數字"""
        if not price_str:
            return 0.0
        
        # 如果已經是數字型別，直接返回
        if isinstance(price_str, (int, float)):
            return float(price_str)
        
        # 如果是字串，移除貨幣符號和逗號
        if isinstance(price_str, str):
            cleaned = price_str.replace('$', '').replace(',', '').replace('NT', '').strip()
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
        
        return 0.0
    
    def save_crawl_session(self, platform: str, keyword: str, total_products: int, 
                          timestamp: str, status: str = 'success', execution_time: float = 0) -> int:
        """儲存爬蟲執行記錄"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO crawl_sessions (timestamp, platform, keyword, total_products, status, execution_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (timestamp, platform, keyword, total_products, status, execution_time))
            
            session_id = cursor.lastrowid
            conn.commit()
            return session_id
    
    def save_products(self, session_id: int, products: List[Dict], platform: str, crawl_time: str):
        """儲存商品資料"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for product in products:
                price_numeric = self.parse_price(product.get('price', ''))
                
                cursor.execute('''
                    INSERT INTO products (session_id, title, price, price_numeric, image_url, 
                                        product_url, platform, crawl_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id,
                    product.get('title', ''),
                    product.get('price', ''),
                    price_numeric,
                    product.get('image_url', ''),
                    product.get('url', ''),
                    platform,
                    crawl_time
                ))
            
            conn.commit()
            print(f"✅ 已儲存 {len(products)} 個 {platform} 商品")
    
    def import_json_data(self, json_file_path: str) -> bool:
        """從 JSON 檔案匯入資料到資料庫"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            platform = data.get('platform', 'unknown')
            keyword = data.get('keyword', platform)
            total_products = data.get('total_products', 0)
            timestamp = data.get('timestamp', data.get('crawl_time', datetime.now().isoformat()))
            products = data.get('products', [])
            
            # 儲存爬蟲記錄
            session_id = self.save_crawl_session(platform, keyword, total_products, timestamp)
            
            # 儲存商品
            self.save_products(session_id, products, platform, timestamp)
            
            print(f"✅ 成功匯入 {json_file_path}")
            return True
            
        except Exception as e:
            print(f"❌ 匯入 {json_file_path} 失敗: {e}")
            return False
    
    def get_latest_deals(self, platform: str = None, limit: int = 100) -> List[Dict]:
        """獲取最新促銷商品"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if platform:
                cursor.execute('''
                    SELECT p.*, s.timestamp as session_timestamp
                    FROM products p
                    JOIN crawl_sessions s ON p.session_id = s.id
                    WHERE p.platform = ?
                    ORDER BY p.crawl_time DESC
                    LIMIT ?
                ''', (platform, limit))
            else:
                cursor.execute('''
                    SELECT p.*, s.timestamp as session_timestamp
                    FROM products p
                    JOIN crawl_sessions s ON p.session_id = s.id
                    ORDER BY p.crawl_time DESC
                    LIMIT ?                ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]

    def get_platform_stats(self, platform: str = None) -> Dict:
        """獲取平台統計資訊"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if platform:
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_products,
                        AVG(price_numeric) as avg_price,
                        MIN(price_numeric) as min_price,
                        MAX(price_numeric) as max_price,
                        MAX(crawl_time) as last_update
                    FROM products 
                    WHERE platform = ? AND price_numeric > 0
                ''', (platform,))
            else:
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_products,
                        AVG(price_numeric) as avg_price,
                        MIN(price_numeric) as min_price,
                        MAX(price_numeric) as max_price,
                        MAX(crawl_time) as last_update
                    FROM products 
                    WHERE price_numeric > 0
                ''')
            
            row = cursor.fetchone()
            return {
                'total_products': row[0] if row[0] else 0,
                'avg_price': round(row[1], 2) if row[1] else 0,
                'min_price': row[2] if row[2] else 0,
                'max_price': row[3] if row[3] else 0,
                'last_update': row[4] if row[4] else None
            }

    def get_crawl_sessions(self, platform: str = None, keyword: str = None, 
                          session_id: int = None, limit: int = 50) -> List[Dict]:
        """獲取爬蟲會話記錄"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM crawl_sessions WHERE 1=1"
            params = []
            
            if session_id:
                query += " AND id = ?"
                params.append(session_id)
            elif platform:
                query += " AND platform = ?"
                params.append(platform)
            
            if keyword:
                query += " AND keyword LIKE ?"
                params.append(f"%{keyword}%")
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_products_by_session(self, session_id: int) -> List[Dict]:
        """根據會話 ID 獲取商品列表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, price, price_numeric, image_url, 
                       product_url as url, platform, crawl_time
                FROM products 
                WHERE session_id = ?
                ORDER BY id
            ''', (session_id,))
            
            return [dict(row) for row in cursor.fetchall()]

    def get_database_stats(self) -> Dict:
        """獲取整個資料庫的統計資訊"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 總會話數
            cursor.execute("SELECT COUNT(*) FROM crawl_sessions")
            total_sessions = cursor.fetchone()[0]
            
            # 總商品數
            cursor.execute("SELECT COUNT(*) FROM products")
            total_products = cursor.fetchone()[0]
            
            # 平台數
            cursor.execute("SELECT COUNT(DISTINCT platform) FROM crawl_sessions")
            platform_count = cursor.fetchone()[0]
            
            # 各平台資訊
            cursor.execute('''
                SELECT platform, COUNT(*) as session_count, 
                       MAX(timestamp) as last_update
                FROM crawl_sessions 
                GROUP BY platform
                ORDER BY session_count DESC
            ''')
            platforms = [{'platform': row[0], 'sessions': row[1], 'last_update': row[2]} 
                        for row in cursor.fetchall()]
            
            return {
                'total_sessions': total_sessions,
                'total_products': total_products,
                'platform_count': platform_count,
                'platforms': platforms
            }
    
    def export_to_json(self, platform: str, output_file: str) -> bool:
        """將資料庫資料匯出為 JSON 格式（用於 GitHub Pages）"""
        try:
            products = self.get_latest_deals(platform=platform)
            
            if not products:
                print(f"❌ 沒有找到 {platform} 的資料")
                return False
            
            # 獲取最新的 session 資訊
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT timestamp, keyword, total_products
                    FROM crawl_sessions
                    WHERE platform = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                ''', (platform,))
                
                session_row = cursor.fetchone()
            
            # 轉換為原始 JSON 格式
            json_data = {
                'timestamp': session_row[0] if session_row else datetime.now().isoformat(),
                'platform': platform,
                'keyword': session_row[1] if session_row else platform,
                'total_products': len(products),
                'products': [
                    {
                        'title': product['title'],
                        'price': product['price'],
                        'image_url': product['image_url'],
                        'url': product['product_url'],
                        'platform': product['platform']
                    }
                    for product in products
                ]
            }
            
            # 儲存到檔案
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 已匯出 {len(products)} 個商品到 {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ 匯出失敗: {e}")
            return False

if __name__ == "__main__":
    # 測試資料庫功能
    db = CrawlerDatabase()
    
    # 測試匯入現有 JSON 資料
    json_files = [
        "crawl_data/crawler_results_pchome_onsale.json",
        "crawl_data/crawler_results_yahoo_rushbuy.json"
    ]
    
    for json_file in json_files:
        if os.path.exists(json_file):
            db.import_json_data(json_file)
    
    # 顯示統計資訊
    stats = db.get_platform_stats()
    print(f"\n📊 總體統計: {stats}")
    
    pchome_stats = db.get_platform_stats('pchome_onsale')
    print(f"📊 PChome 統計: {pchome_stats}")
    
    yahoo_stats = db.get_platform_stats('yahoo_rushbuy')
    print(f"📊 Yahoo 統計: {yahoo_stats}")
