import json
from typing import List, Dict, Any, Callable, TypedDict
import google.generativeai as genai
import os

# 使用 TypedDict 取代 Pydantic
class ProductFilterRequest(TypedDict):
    id: int
    title: str

class FilterResponse(TypedDict):
    products_to_remove: List[int]
    reasoning: str

class ProductFilter:
    def __init__(self, db_connection_func: Callable):
        """
        初始化商品過濾器
        
        Args:
            db_connection_func: 一個返回資料庫連線的函式
        """
        # 配置 Gemini API
        GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            print("Warning: Gemini API key not found. Product filtering will be disabled.")
        
        self.get_db_connection = db_connection_func

    def _get_products_from_db(self, session_id: int) -> List[Dict[str, Any]]:
        """從資料庫獲取指定 session 的商品"""
        conn = self.get_db_connection()
        products = conn.execute(
            "SELECT id, title, price FROM products WHERE session_id = ?",
            (session_id,)
        ).fetchall()
        conn.close()
        return [dict(p) for p in products]

    def _update_filtered_status_in_db(self, product_ids: List[int]):
        """在資料庫中更新商品的 is_filtered_out 狀態"""
        if not product_ids:
            return
        conn = self.get_db_connection()
        cursor = conn.cursor()
        ids_to_update = [(pid,) for pid in product_ids]
        cursor.executemany(
            "UPDATE products SET is_filtered_out = 1 WHERE id = ?",
            ids_to_update
        )
        conn.commit()
        conn.close()
        print(f"已在資料庫中標記 {len(product_ids)} 個商品為已過濾。")

    def filter_products_with_gemini(self, products: List[ProductFilterRequest], keyword: str) -> FilterResponse:
        """
        使用Gemini API過濾商品
        """
        if not products:
            return {"products_to_remove": [], "reasoning": "沒有商品可供過濾。"}

        if not self.model:
            return {"products_to_remove": [], "reasoning": "Gemini API 未配置，無法進行過濾。"}

        products_info = "\n".join([f"ID: {p['id']}, 標題: {p['title']}" for p in products])
        
        prompt = f"""
        你是一個商品過濾專家。給定搜索關鍵字 "{keyword}" 和商品列表，請識別出哪些商品不是 "{keyword}" 的主體商品。

        需要過濾掉的商品類型包括：
        1. 不同型號或不同版本的商品
        2. 與主體商品無關的配件或附加商品 (如保護殼、保護貼、充電器)
        3. 贈品或套裝中的贈品
        4. 維修零件或拆機零件
        5. 與主體商品無直接關係的周邊商品

        商品列表：
        {products_info}

        請分析每個商品標題，找出需要移除的商品ID。只有當商品明確不是 "{keyword}" 主體時才移除。
        請返回 JSON 格式，包含 'products_to_remove' (一個整數ID列表) 和 'reasoning' (字串)。
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # 解析JSON回應
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]  # 移除```json和```
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]  # 移除```
            
            parsed_json: FilterResponse = json.loads(response_text)
            return parsed_json
            
        except Exception as e:
            print(f"Gemini API 調用失敗: {e}")
            return {"products_to_remove": [], "reasoning": "API調用失敗，未進行過濾"}

    def filter_session_products(self, session_id: int) -> Dict[str, Any]:
        """
        過濾指定 session ID 的爬蟲結果
        """
        print(f"開始商品過濾流程，Session ID: {session_id}...")
        
        conn = self.get_db_connection()
        session = conn.execute("SELECT keyword FROM crawl_sessions WHERE id = ?", (session_id,)).fetchone()
        conn.close()

        if not session:
            raise ValueError(f"找不到 Session ID: {session_id}")
        
        keyword = session["keyword"]
        products_from_db = self._get_products_from_db(session_id)
        
        if not products_from_db:
            return {"message": "此任務沒有商品可供過濾。", "original_count": 0, "filtered_count": 0, "removed_count": 0}

        print(f"搜索關鍵字: {keyword}")
        print(f"原始商品總數: {len(products_from_db)}")

        products_for_filtering: List[ProductFilterRequest] = [
            {"id": p["id"], "title": p["title"]} for p in products_from_db
        ]

        print("使用Gemini API進行智能過濾...")
        filter_result = self.filter_products_with_gemini(products_for_filtering, keyword)
        
        print(f"過濾理由: {filter_result['reasoning']}")
        print(f"模型建議移除的商品數量: {len(filter_result['products_to_remove'])}")

        self._update_filtered_status_in_db(filter_result['products_to_remove'])
        
        original_count = len(products_from_db)
        removed_count = len(filter_result['products_to_remove'])
        filtered_count = original_count - removed_count

        print(f"過濾完成！總共移除 {removed_count} 個商品，剩餘 {filtered_count} 個。")

        return {
            "session_id": session_id,
            "keyword": keyword,
            "original_count": original_count,
            "filtered_count": filtered_count,
            "removed_count": removed_count,
            "reasoning": filter_result['reasoning'],
            "removed_product_ids": filter_result['products_to_remove']
        }

def main():
    """主程式範例"""
    from core.database import get_db_connection, init_db

    init_db()
    
    filter_obj = ProductFilter(db_connection_func=get_db_connection)
    
    conn = get_db_connection()
    latest_session = conn.execute("SELECT id FROM crawl_sessions ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()

    if not latest_session:
        print("資料庫中沒有任何爬取紀錄可供過濾。")
        print("請先執行 crawler_manager.py 來產生一些數據。")
        return

    session_id_to_filter = latest_session['id']
    
    try:
        stats = filter_obj.filter_session_products(session_id_to_filter)
        
        print("\n=== 過濾結果摘要 ===")
        print(f"任務 Session ID: {stats['session_id']}")
        print(f"關鍵字: {stats['keyword']}")
        print(f"原始數量: {stats['original_count']}")
        print(f"移除數量: {stats['removed_count']}")
        print(f"剩餘數量: {stats['filtered_count']}")
        print(f"過濾理由: {stats['reasoning']}")
        
    except Exception as e:
        print(f"過濾過程中發生錯誤: {e}")

if __name__ == "__main__":
    main()
