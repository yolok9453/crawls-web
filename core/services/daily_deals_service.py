"""
每日促銷爬蟲服務
負責管理每日促銷商品的爬取、更新和狀態追蹤
"""

import os
import sys
import importlib.util
from datetime import datetime
from threading import Thread

# 添加項目根目錄到路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from core.database import get_db_connection


class DailyDealsService:
    def __init__(self, crawler_manager):
        self.crawler_manager = crawler_manager
        self.crawler_status = {
            'is_updating': False,
            'start_time': None,
            'completion_time': None
        }
    
    def get_status(self):
        """獲取爬蟲執行狀態"""
        return self.crawler_status.copy()
    
    def is_updating(self):
        """檢查是否正在更新中"""
        return self.crawler_status['is_updating']
    
    def start_update(self):
        """開始更新每日促銷商品"""
        if self.crawler_status['is_updating']:
            return {'status': 'warning', 'message': '爬蟲正在執行中'}

        self.crawler_status.update({
            'is_updating': True, 
            'start_time': datetime.now().isoformat()
        })

        # 在背景執行
        thread = Thread(target=self._update_daily_deals)
        thread.start()
        
        return {'status': 'success', 'message': '每日促銷商品更新已開始'}
    
    def _update_daily_deals(self):
        """更新每日促銷商品的主要邏輯"""
        try:
            # 1. 先更新每日促銷商品
            self._run_and_save('pchome_onsale')
            self._run_and_save('yahoo_rushbuy')
            print("每日促銷爬蟲執行完成")
            
            # 2. 然後爬取一般商品來豐富比較資料庫
            self._run_general_crawlers_for_comparison()
            print("一般商品爬取完成")
            
            print("所有爬蟲任務執行完成")
        except Exception as e:
            print(f"爬蟲執行過程中發生錯誤: {e}")
        finally:
            # 確保狀態被重置
            self.crawler_status.update({
                'is_updating': False, 
                'completion_time': datetime.now().isoformat()
            })
            print("爬蟲狀態已重置為非更新中")
    
    def _run_and_save(self, crawler_name):
        """執行並儲存爬蟲結果"""
        try:
            print(f"開始執行 {crawler_name} 爬蟲...")
            # 修正路徑：從 core/services 到 crawlers 需要回到專案根目錄
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            crawler_path = os.path.join(project_root, "crawlers", f"crawler_{crawler_name}.py")
            print(f"載入爬蟲路徑: {crawler_path}")
            
            spec = importlib.util.spec_from_file_location(
                f"crawler_{crawler_name}", 
                crawler_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 修改為不儲存JSON，直接返回產品
            products = module.run(max_products=100, save_json=False) 
            print(f"{crawler_name} 爬蟲獲取到 {len(products) if products else 0} 個商品")
            
            if products:
                conn = get_db_connection()
                cursor = conn.cursor()
                # 先刪除該平台舊資料
                cursor.execute("DELETE FROM daily_deals WHERE platform = ?", (crawler_name,))
                print(f"已清除 {crawler_name} 平台的舊資料")
                
                products_to_insert = [
                    (crawler_name, p.get('title') or p.get('name'), p.get('price'), p.get('url'), p.get('image_url'), datetime.now().isoformat())
                    for p in products
                ]
                cursor.executemany(
                    "INSERT INTO daily_deals (platform, title, price, url, image_url, crawl_time) VALUES (?, ?, ?, ?, ?, ?)",
                    products_to_insert
                )
                conn.commit()
                conn.close()
                print(f"{crawler_name} 爬蟲完成，{len(products)} 個商品已存入資料庫")
            else:
                print(f"{crawler_name} 爬蟲沒有獲取到任何商品")
        except Exception as e:
            print(f"執行 {crawler_name} 爬蟲時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def _run_general_crawlers_for_comparison(self):
        """爬取一般商品來豐富比較資料庫"""
        try:
            print("開始爬取一般商品來豐富比較資料庫...")
            
            # 從每日促銷商品中提取關鍵字作為搜尋條件
            conn = get_db_connection()
            recent_deals = conn.execute("SELECT DISTINCT title FROM daily_deals ORDER BY crawl_time DESC LIMIT 10").fetchall()
            conn.close()
            
            # 提取關鍵字（簡化版）
            search_keywords = []
            for deal in recent_deals:
                title = deal['title']
                # 提取商品的主要關鍵字
                if 'iPhone' in title or 'iphone' in title:
                    search_keywords.append('iPhone')
                elif 'iPad' in title:
                    search_keywords.append('iPad')
                elif 'AirPods' in title or 'airpods' in title:
                    search_keywords.append('AirPods')
                elif 'Switch' in title or 'SWITCH' in title:
                    search_keywords.append('Switch')
                elif '筆電' in title or '電腦' in title:
                    search_keywords.append('筆電')
                elif '耳機' in title:
                    search_keywords.append('耳機')
                elif '手機' in title:
                    search_keywords.append('手機')
                elif '家電' in title:
                    search_keywords.append('家電')
            
            # 如果沒有提取到關鍵字，使用預設的熱門商品關鍵字
            if not search_keywords:
                search_keywords = ['iPhone', 'iPad', 'AirPods', '筆電', '耳機', '手機殼']
            
            # 去重
            search_keywords = list(set(search_keywords))[:3]  # 限制最多3個關鍵字
            print(f"將使用關鍵字進行爬取: {search_keywords}")
            
            for keyword in search_keywords:
                try:
                    print(f"開始爬取關鍵字: {keyword}")
                    session_id = self.crawler_manager.run_all_crawlers(
                        keyword=keyword,
                        max_products=50,  # 每個關鍵字爬取50個商品
                        min_price=0,
                        max_price=999999,
                        platforms=None  # 使用所有可用平台：carrefour, pchome, routn, yahoo
                    )
                    print(f"關鍵字 '{keyword}' 爬取完成，session_id: {session_id}")
                except Exception as e:
                    print(f"爬取關鍵字 '{keyword}' 時發生錯誤: {e}")
                    
        except Exception as e:
            print(f"執行一般商品爬取時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def enrich_product_database(self):
        """手動豐富商品資料庫 - 爬取熱門關鍵字商品"""
        if self.crawler_status['is_updating']:
            return {'status': 'warning', 'message': '爬蟲正在執行中，請稍後再試'}

        self.crawler_status.update({
            'is_updating': True, 
            'start_time': datetime.now().isoformat()
        })

        def enrich_database():
            try:
                print("開始豐富商品資料庫...")
                
                # 熱門商品關鍵字列表
                popular_keywords = [
                    'iPhone 16', 'iPad', 'AirPods', 'MacBook', 
                    'Switch', 'PS5', '筆電', '耳機', 
                    '手機殼', '充電器', '滑鼠', '鍵盤',
                    '攝影機', '相機', '電視', '冰箱',
                    '洗衣機', '冷氣', '除濕機', '空氣清淨機'
                ]
                
                successful_crawls = 0
                total_products = 0
                
                for i, keyword in enumerate(popular_keywords[:8]):  # 限制8個關鍵字避免過長時間
                    try:
                        print(f"[{i+1}/8] 正在爬取關鍵字: {keyword}")
                        session_id = self.crawler_manager.run_all_crawlers(
                            keyword=keyword,
                            max_products=30,  # 每個關鍵字30個商品
                            min_price=0,
                            max_price=999999,
                            platforms=['pchome', 'yahoo', 'carrefour']  # 使用多個平台
                        )
                        
                        if session_id:
                            # 統計爬取到的商品數量
                            conn = get_db_connection()
                            count = conn.execute("SELECT COUNT(*) FROM products WHERE session_id = ?", (session_id,)).fetchone()[0]
                            conn.close()
                            
                            successful_crawls += 1
                            total_products += count
                            print(f"關鍵字 '{keyword}' 爬取完成，獲得 {count} 個商品")
                        
                    except Exception as e:
                        print(f"爬取關鍵字 '{keyword}' 時發生錯誤: {e}")
                
                print(f"商品資料庫豐富化完成: 成功爬取 {successful_crawls} 個關鍵字，總計 {total_products} 個商品")
                return successful_crawls, total_products
                
            except Exception as e:
                print(f"豐富商品資料庫時發生錯誤: {e}")
                import traceback
                traceback.print_exc()
                return 0, 0
            finally:
                self.crawler_status.update({
                    'is_updating': False, 
                    'completion_time': datetime.now().isoformat()
                })

        # 在背景執行
        def run_enrichment():
            successful, total = enrich_database()
            print(f"資料庫豐富化任務完成: {successful} 個成功, {total} 個商品")

        thread = Thread(target=run_enrichment)
        thread.start()
        
        return {
            'status': 'success', 
            'message': '商品資料庫豐富化已開始，這可能需要幾分鐘時間'
        }
    
    def reset_status(self):
        """強制重置爬蟲狀態（調試用）"""
        self.crawler_status.update({
            'is_updating': False,
            'start_time': None,
            'completion_time': datetime.now().isoformat()
        })
        return {
            'status': 'success',
            'message': '爬蟲狀態已重置',
            'crawler_status': self.crawler_status
        }
