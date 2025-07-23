"""
資料庫服務
負責各種資料庫操作的封裝和管理
"""

from core.database import get_db_connection


class DatabaseService:
    def __init__(self):
        pass
    
    def get_crawl_sessions(self):
        """獲取所有爬蟲任務結果"""
        try:
            conn = get_db_connection()
            sessions = conn.execute('SELECT * FROM crawl_sessions ORDER BY crawl_time DESC').fetchall()
            conn.close()
            return [dict(row) for row in sessions]
        except Exception as e:
            raise Exception(f'讀取爬取紀錄失敗: {str(e)}')
    
    def get_session_detail(self, session_id):
        """獲取特定任務的詳細內容"""
        try:
            print(f"獲取任務 {session_id} 的詳情")
            conn = get_db_connection()
            session = conn.execute('SELECT * FROM crawl_sessions WHERE id = ?', (session_id,)).fetchone()
            
            if not session:
                conn.close()
                print(f"錯誤: 找不到ID為 {session_id} 的任務")
                raise Exception('任務不存在')
            
            products = conn.execute('SELECT * FROM products WHERE session_id = ? ORDER BY price', (session_id,)).fetchall()
            products_count = len(products)
            print(f"找到 {products_count} 個商品")
            
            # 獲取各平台統計資料
            platform_stats_rows = conn.execute("""
                SELECT platform, COUNT(*) as 'COUNT(*)', AVG(price) as 'AVG(price)', 
                       MIN(price) as 'MIN(price)', MAX(price) as 'MAX(price)'
                FROM products WHERE session_id = ? GROUP BY platform
            """, (session_id,)).fetchall()
            
            # 獲取整體價格統計
            price_stats_row = conn.execute("""
                SELECT COUNT(*) as 'COUNT(*)', AVG(price) as 'AVG(price)', 
                       MIN(price) as 'MIN(price)', MAX(price) as 'MAX(price)'
                FROM products WHERE session_id = ?
            """, (session_id,)).fetchone()
            
            platform_stats = {
                row['platform']: {
                    'product_count': row['COUNT(*)'],
                    'average_price': row['AVG(price)'],
                    'min_price': row['MIN(price)'],
                    'max_price': row['MAX(price)'],
                } for row in platform_stats_rows
            }

            stats = {
                'keyword': session['keyword'],
                'total_products': session['total_products'],
                'platforms': platform_stats,
                'price_stats': {
                    'min': price_stats_row['MIN(price)'] if price_stats_row and price_stats_row['COUNT(*)'] > 0 else 0,
                    'max': price_stats_row['MAX(price)'] if price_stats_row and price_stats_row['COUNT(*)'] > 0 else 0,
                    'average': price_stats_row['AVG(price)'] if price_stats_row and price_stats_row['COUNT(*)'] > 0 else 0,
                    'total': price_stats_row['COUNT(*)'] if price_stats_row and price_stats_row['COUNT(*)'] > 0 else 0
                }
            }
            
            conn.close()
            return stats
        except Exception as e:
            print(f"獲取統計資料時出錯: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f'獲取統計資料失敗: {str(e)}')
    
    def get_daily_deals(self, platform_filter='all'):
        """獲取每日促銷結果"""
        try:
            conn = get_db_connection()
            query = "SELECT * FROM daily_deals"
            params = []
            if platform_filter != 'all':
                query += " WHERE platform = ?"
                params.append(platform_filter)
            query += " ORDER BY crawl_time DESC"
            
            deals = conn.execute(query, params).fetchall()
            
            # 取得各平台最後更新時間
            update_times_rows = conn.execute("SELECT platform, MAX(crawl_time) as last_update FROM daily_deals GROUP BY platform").fetchall()
            conn.close()

            platform_updates = {row['platform']: row['last_update'] for row in update_times_rows}

            return {
                'daily_deals': [dict(row) for row in deals],
                'total_deals': len(deals),
                'last_update': deals[0]['crawl_time'] if deals else '',
                'platform_updates': platform_updates
            }
        except Exception as e:
            raise Exception(f'讀取每日促銷失敗: {str(e)}')
    
    def get_daily_deals_status(self, crawler_status):
        """獲取每日促銷狀態"""
        try:
            conn = get_db_connection()
            count = conn.execute("SELECT COUNT(*) FROM daily_deals").fetchone()[0]
            latest_update = conn.execute("SELECT MAX(crawl_time) FROM daily_deals").fetchone()[0]
            conn.close()
            
            return {
                'status': 'updating' if crawler_status['is_updating'] else 'idle',
                'is_updating': crawler_status['is_updating'],
                'total_deals': count,
                'last_update': latest_update,
                'start_time': crawler_status.get('start_time'),
                'completion_time': crawler_status.get('completion_time')
            }
        except Exception as e:
            raise Exception(f'獲取狀態失敗: {str(e)}')
    
    def debug_daily_deals(self, crawler_status):
        """調試用：檢查每日促銷狀態"""
        try:
            conn = get_db_connection()
            
            # 獲取每日促銷資料
            deals = conn.execute("SELECT * FROM daily_deals ORDER BY crawl_time DESC").fetchall()
            
            # 統計各平台數量
            platform_counts = {}
            latest_updates = {}
            
            for deal in deals:
                platform = deal['platform']
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
                
                # 記錄最新更新時間
                if platform not in latest_updates or deal['crawl_time'] > latest_updates[platform]:
                    latest_updates[platform] = deal['crawl_time']
            
            conn.close()
            
            return {
                'crawler_status': crawler_status,
                'total_deals': len(deals),
                'platform_counts': platform_counts,
                'latest_updates': latest_updates,
                'recent_deals': [dict(deal) for deal in deals[:10]]  # 最近10個商品
            }
            
        except Exception as e:
            return {
                'error': f'調試檢查失敗: {str(e)}',
                'crawler_status': crawler_status
            }
    
    def get_sessions_to_filter(self):
        """獲取需要過濾的爬蟲任務"""
        try:
            conn = get_db_connection()
            # 找出從未被過濾的 session (假設只要執行過一次就不再執行)
            # 這裡的邏輯是：如果一個 session 的所有商品都沒有 is_filtered_out=1 的，就當作是未過濾
            query = """
            SELECT s.id FROM crawl_sessions s
            WHERE NOT EXISTS (
                SELECT 1 FROM products p WHERE p.session_id = s.id AND p.is_filtered_out = 1
            )
            ORDER BY s.id DESC
            """
            sessions_to_filter = conn.execute(query).fetchall()
            conn.close()
            return [dict(row) for row in sessions_to_filter]
        except Exception as e:
            raise Exception(f'獲取需要過濾的任務失敗: {str(e)}')
