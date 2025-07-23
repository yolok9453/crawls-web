import os
import time
import uuid
from typing import List, Dict, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib.util
import sys
from .database import get_db_connection

class CrawlerManager:
    """爬蟲管理器 - 統一管理所有爬蟲的執行並存入資料庫"""
    
    def __init__(self, crawlers_dir: str = None):
        """
        初始化爬蟲管理器
        
        Args:
            crawlers_dir (str): 爬蟲檔案目錄
        """
        if crawlers_dir is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            crawlers_dir = os.path.join(project_root, "crawlers")
        self.crawlers_dir = crawlers_dir
        self.crawlers = {}
        
        # 自動載入爬蟲
        self._load_crawlers()

    def _load_crawlers(self):
        """自動載入crawlers目錄中的所有爬蟲模組"""
        if not os.path.exists(self.crawlers_dir):
            print(f"警告: 爬蟲目錄 {self.crawlers_dir} 不存在")
            return
        
        for filename in os.listdir(self.crawlers_dir):
            if filename.startswith("crawler_") and filename.endswith(".py"):
                platform = filename.replace("crawler_", "").replace(".py", "")
                
                # 跳過 yahoo_rushbuy 和 pchome_onsale，它們只用於每日促銷
                if platform in ['yahoo_rushbuy', 'pchome_onsale']:
                    continue
                    
                module_path = os.path.join(self.crawlers_dir, filename)
                
                try:
                    # 動態載入模組
                    spec = importlib.util.spec_from_file_location(f"crawler_{platform}", module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # 檢查模組是否有run函數
                    if hasattr(module, 'run'):
                        self.crawlers[platform] = module.run
                        print(f"成功載入爬蟲: {platform}")
                    else:
                        print(f"警告: {filename} 沒有run函數")
                        
                except Exception as e:
                    print(f"載入爬蟲 {filename} 失敗: {e}")
    
    def list_crawlers(self) -> List[str]:
        """列出所有可用的爬蟲"""
        return list(self.crawlers.keys())

    def run_single_crawler(self, platform: str, keyword: str, max_products: int = 100, min_price: int = 0, max_price: int = 999999) -> Dict:
        """
        執行單個爬蟲
        
        Args:
            platform (str): 平台名稱
            keyword (str): 搜索關鍵字
            max_products (int): 最大商品數量
            min_price (int): 最低價格範圍
            max_price (int): 最高價格範圍
        Returns:
            Dict: 爬蟲結果
        """
        if platform not in self.crawlers:
            raise ValueError(f"不支援的平台: {platform}")
        
        print(f"開始執行 {platform} 爬蟲，關鍵字: {keyword}")
        start_time = time.time()
        
        try:
            # 呼叫對應平台的爬蟲函數
            products = self.crawlers[platform](keyword, max_products, min_price, max_price)

            result = {
                "platform": platform,
                "keyword": keyword,
                "total_products": len(products),
                "products": products,
                "crawl_time": datetime.now().isoformat(),
                "execution_time": time.time() - start_time,
                "status": "success"
            }
            
            print(f"{platform} 爬蟲完成，獲取 {len(products)} 個商品")
            return result
            
        except Exception as e:
            print(f"{platform} 爬蟲執行失敗: {e}")
            return {
                "platform": platform,
                "keyword": keyword,
                "total_products": 0,
                "products": [],
                "crawl_time": datetime.now().isoformat(),
                "execution_time": time.time() - start_time,
                "status": "error",
                "error": str(e)
            }

    def run_all_crawlers(self, keyword: str, max_products: int = 100, min_price: int = 0, max_price: int = 999999,
                        platforms: Optional[List[str]] = None) -> int:
        """
        同時執行所有爬蟲並將結果存入資料庫
        
        Args:
            keyword (str): 搜索關鍵字
            max_products (int): 每個平台的最大商品數量
            platforms (List[str], optional): 指定要執行的平台，None表示全部
            min_price (int): 最低價格範圍
            max_price (int): 最高價格範圍
            
        Returns:
            int: 本次爬取任務的 session_id
        """
        if platforms is None:
            platforms = list(self.crawlers.keys())
        
        print(f"開始同時執行 {len(platforms)} 個爬蟲，關鍵字: {keyword}")
        start_time = time.time()
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=len(platforms)) as executor:
            future_to_platform = {
                executor.submit(self.run_single_crawler, platform, keyword, max_products, min_price, max_price): platform
                for platform in platforms
            }
            
            for future in as_completed(future_to_platform):
                platform = future_to_platform[future]
                try:
                    result = future.result()
                    results[platform] = result
                except Exception as e:
                    print(f"{platform} 爬蟲執行異常: {e}")
                    results[platform] = {
                        "platform": platform,
                        "keyword": keyword,
                        "total_products": 0,
                        "products": [],
                        "crawl_time": datetime.now().isoformat(),
                        "execution_time": time.time() - start_time,
                        "status": "error",
                        "error": str(e)
                    }
        
        total_time = time.time() - start_time
        total_products = sum(result.get("total_products", 0) for result in results.values())
        
        print(f"所有爬蟲執行完成，總共獲取 {total_products} 個商品，耗時 {total_time:.2f} 秒")
        
        # 將結果存入資料庫
        session_id = self._save_results_to_db(keyword, results, platforms)
        
        return session_id

    def _save_results_to_db(self, keyword: str, results: Dict[str, Dict], platforms: List[str]) -> int:
        """
        將爬蟲結果保存到資料庫
        
        Args:
            keyword (str): 搜索關鍵字
            results (Dict): 爬蟲結果
            platforms (List[str]): 執行的平台列表
            
        Returns:
            int: 新增的 session_id
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        successful_crawlers = [r for r in results.values() if r.get("status") == "success"]
        failed_crawlers = len(results) - len(successful_crawlers)
        
        status = "success"
        if failed_crawlers == len(results):
            status = "failed"
        elif failed_crawlers > 0:
            status = "partial_fail"

        # 1. 創建爬取 session
        cursor.execute(
            "INSERT INTO crawl_sessions (keyword, crawl_time, status, platforms) VALUES (?, ?, ?, ?)",
            (keyword, datetime.now(), status, ",".join(platforms))
        )
        session_id = cursor.lastrowid
        
        # 2. 插入商品數據
        total_products = 0
        products_to_insert = []
        for platform, result in results.items():
            if result.get("status") == "success":
                products = result.get("products", [])
                total_products += len(products)  # 用實際商品數量而不是報告的數量
                print(f"正在處理 {platform} 的 {len(products)} 個商品")
                for p in products:
                    # 檢查必要欄位是否存在
                    title = p.get('title') or p.get('name') or "無標題商品"
                    price = p.get('price')
                    if not price or not isinstance(price, (int, float)):
                        try:
                            price = int(float(price)) if price else 0
                        except:
                            price = 0
                            
                    url = p.get('url')
                    if not url:
                        continue  # 跳過沒有URL的商品
                        
                    products_to_insert.append((
                        session_id,
                        platform,
                        title,
                        price,
                        url,
                        p.get('image_url') or ""
                    ))

        if products_to_insert:
            print(f"插入 {len(products_to_insert)} 個商品到資料庫")
            try:
                cursor.executemany(
                    """
                    INSERT OR IGNORE INTO products (session_id, platform, title, price, url, image_url)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    products_to_insert
                )
                print(f"成功插入 {cursor.rowcount} 個商品")
            except Exception as e:
                print(f"插入商品數據時出錯: {e}")
                # 嘗試一個一個插入以找出問題
                successful = 0
                for product in products_to_insert:
                    try:
                        cursor.execute(
                            "INSERT OR IGNORE INTO products (session_id, platform, title, price, url, image_url) VALUES (?, ?, ?, ?, ?, ?)",
                            product
                        )
                        successful += 1
                    except Exception as e:
                        print(f"插入商品失敗: {e}, 商品: {product}")
                print(f"逐個插入: 成功 {successful}/{len(products_to_insert)} 個商品")

        # 3. 更新 session 的總商品數
        cursor.execute(
            "UPDATE crawl_sessions SET total_products = ? WHERE id = ?",
            (total_products, session_id)
        )
        
        conn.commit()
        conn.close()
        
        print(f"結果已保存至資料庫，Session ID: {session_id}")
        return session_id


def main():
    """主程式範例"""
    # 初始化爬蟲管理器
    manager = CrawlerManager()
    
    print("可用的爬蟲:", manager.list_crawlers())
    
    # 設定搜索關鍵字
    keyword = "iphone 15"
    max_products = 50
    min_price = 20000
    max_price = 40000
    
    # 執行所有爬蟲並獲取 session_id
    session_id = manager.run_all_crawlers(keyword, max_products, min_price, max_price)
    
    print(f"\n爬取任務完成！ Session ID: {session_id}")
    print("您現在可以透過 web_app.py 查看結果。")


if __name__ == "__main__":
    main()
