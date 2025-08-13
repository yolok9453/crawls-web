"""
商品比較快取服務
負責商品比較結果的快取管理和候選商品獲取
"""

import json
from datetime import datetime
from core.database import get_db_connection


class ProductComparisonCacheService:
    def __init__(self, crawler_manager, product_comparison_service):
        self.crawler_manager = crawler_manager
        self.product_comparison_service = product_comparison_service
    
    def get_candidate_products_from_database(self, target_product):
        """從已爬取的資料庫中獲取候選商品，不重新爬取"""
        try:
            target_title = target_product.get('title', '')
            target_platform = target_product.get('platform', '')
            
            # 提取關鍵詞用於資料庫搜尋
            keywords_to_remove = ['【', '】', '★', '☆', '▶', '▷', '※', '◆', '◇', '■', '□', 
                                 '限時', '特價', '促銷', '優惠', '折扣', '免運', '現貨', '熱銷',
                                 '新款', '2024', '2025', '正品', '官方', '代理', '公司貨']
            
            search_keyword = target_title
            for remove_word in keywords_to_remove:
                search_keyword = search_keyword.replace(remove_word, '')
            
            # 進一步簡化關鍵詞
            if '(' in search_keyword:
                search_keyword = search_keyword.split('(')[0].strip()
            elif '（' in search_keyword:
                search_keyword = search_keyword.split('（')[0].strip()
            
            # 提取品牌或主要關鍵詞
            words = search_keyword.strip().split()
            if len(words) > 1:
                # 取前2-3個關鍵詞
                key_words = words[:3]
            else:
                key_words = words
            
            print(f"🔍 從資料庫搜尋關鍵詞: {key_words}")
            
            candidate_products = []
            conn = get_db_connection()
            
            # 從 daily_deals 表搜尋（排除自己）
            for keyword in key_words:
                if len(keyword) >= 2:  # 只搜尋長度>=2的關鍵詞
                    cursor = conn.execute("""
                        SELECT title, platform, price, url, image_url, 'daily_deals' as source_table
                        FROM daily_deals 
                        WHERE title LIKE ? AND platform != ?
                        ORDER BY crawl_time DESC
                        LIMIT 50
                    """, (f'%{keyword}%', target_platform))
                    
                    results = cursor.fetchall()
                    for row in results:
                        candidate_product = {
                            'title': row['title'],
                            'platform': row['platform'],
                            'price': row['price'],
                            'url': row['url'],
                            'image_url': row['image_url'],
                            'source_table': row['source_table']
                        }
                        # 避免重複
                        if not any(p['url'] == candidate_product['url'] for p in candidate_products):
                            candidate_products.append(candidate_product)
            
            # 從 products 表搜尋（如果 daily_deals 結果不足）
            if len(candidate_products) < 20:
                for keyword in key_words:
                    if len(keyword) >= 2:
                        cursor = conn.execute("""
                            SELECT title, platform, price, url, image_url, 'products' as source_table
                            FROM products 
                            WHERE title LIKE ? AND platform != ?
                            ORDER BY id DESC
                            LIMIT 30
                        """, (f'%{keyword}%', target_platform))
                        
                        results = cursor.fetchall()
                        for row in results:
                            candidate_product = {
                                'title': row['title'],
                                'platform': row['platform'],
                                'price': row['price'],
                                'url': row['url'],
                                'image_url': row['image_url'],
                                'source_table': row['source_table']
                            }
                            # 避免重複
                            if not any(p['url'] == candidate_product['url'] for p in candidate_products):
                                candidate_products.append(candidate_product)
            
            conn.close()
            
            print(f"📊 從資料庫找到 {len(candidate_products)} 個候選商品")
            return candidate_products[:50]  # 限制數量
            
        except Exception as e:
            print(f"從資料庫獲取候選商品時發生錯誤: {e}")
            return []
    
    def get_candidate_products_for_comparison(self, target_product):
        """獲取用於比較的候選商品 - 優先使用資料庫搜尋"""
        try:
            # 首先從資料庫搜尋
            candidate_products = self.get_candidate_products_from_database(target_product)
            
            if len(candidate_products) >= 5:  # 如果資料庫有足夠的候選商品
                print(f"✅ 使用資料庫搜尋結果: {len(candidate_products)} 個候選商品")
                return candidate_products
            
            # 如果資料庫結果不足，才進行即時爬取（作為備用）
            print(f"⚠️ 資料庫候選商品不足({len(candidate_products)}個)，使用即時爬取作為補充...")
            return self.get_candidate_products_from_crawling(target_product)
            
        except Exception as e:
            print(f"獲取候選商品時發生錯誤: {e}")
            return []
    
    def get_candidate_products_from_crawling(self, target_product):
        """從即時爬取獲取候選商品（備用方法）"""
        try:
            target_title = target_product.get('title', '')
            
            # 提取關鍵詞用於爬取
            keywords_to_remove = ['【', '】', '★', '☆', '▶', '▷', '※', '◆', '◇', '■', '□', 
                                 '限時', '特價', '促銷', '優惠', '折扣', '免運', '現貨', '熱銷',
                                 '新款', '2024', '2025', '正品', '官方', '代理', '公司貨']
            
            search_keyword = target_title
            for remove_word in keywords_to_remove:
                search_keyword = search_keyword.replace(remove_word, '')
            
            # 進一步簡化關鍵詞
            if '(' in search_keyword:
                search_keyword = search_keyword.split('(')[0].strip()
            elif '（' in search_keyword:
                search_keyword = search_keyword.split('（')[0].strip()
            
            words = search_keyword.strip().split()
            if len(words) > 3:
                search_keyword = ' '.join(words[:3])
            else:
                search_keyword = search_keyword.strip()
            
            # 即時爬取各平台的候選商品
            candidate_products = []
            crawl_platforms = ['carrefour', 'pchome', 'yahoo', 'routn']
            
            for platform in crawl_platforms:
                try:
                    crawl_result = self.crawler_manager.run_single_crawler(
                        platform=platform,
                        keyword=search_keyword,
                        max_products=30,  # 減少數量以加快處理速度
                        min_price=0,
                        max_price=999999
                    )
                    
                    if crawl_result['status'] == 'success' and crawl_result['products']:
                        for product in crawl_result['products']:
                            candidate_product = {
                                'title': product.get('title') or product.get('name', ''),
                                'platform': platform,
                                'price': product.get('price', 0),
                                'url': product.get('url', ''),
                                'image_url': product.get('image_url', ''),
                                'source_table': 'live_crawl'
                            }
                            candidate_products.append(candidate_product)
                            
                except Exception as e:
                    print(f"爬取 {platform} 時發生錯誤: {e}")
                    continue
            
            return candidate_products
            
        except Exception as e:
            print(f"獲取候選商品時發生錯誤: {e}")
            return []
    
    def precompute_comparison_results(self):
        """預先計算所有每日促銷商品的比較結果並存入快取"""
        try:
            print("開始預先計算商品比較結果...")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 清除舊的比較結果快取
            cursor.execute("DELETE FROM product_comparison_cache")
            conn.commit()
            print("已清除舊的比較結果快取")
            
            # 獲取所有每日促銷商品
            daily_deals = conn.execute("SELECT * FROM daily_deals ORDER BY crawl_time DESC").fetchall()
            print(f"找到 {len(daily_deals)} 個每日促銷商品需要計算比較結果")
            
            processed_count = 0
            
            for deal in daily_deals:
                try:
                    target_product = {
                        'title': deal['title'],
                        'platform': deal['platform'],
                        'price': deal['price']
                    }
                    
                    print(f"計算商品 {deal['title'][:30]}... 的比較結果")
                    
                    # 使用相同的邏輯獲取候選商品
                    candidate_products = self.get_candidate_products_for_comparison(target_product)
                    
                    if candidate_products:
                        # 使用 AI 或備用方法進行比較
                        matches = self.product_comparison_service.compare_products(target_product, candidate_products)
                        
                        # 將比較結果存入快取
                        cache_entries = []
                        for match in matches:
                            similarity = match.get('similarity', 0)
                            if similarity >= 0.70:  # 只快取高相似度的結果
                                try:
                                    product_index = match['index']
                                    if 0 <= product_index < len(candidate_products):
                                        candidate = candidate_products[product_index]
                                        
                                        # 將候選商品存入 products 表（如果不存在）
                                        cursor.execute("""
                                            INSERT OR IGNORE INTO products 
                                            (session_id, platform, title, price, url, image_url) 
                                            VALUES (?, ?, ?, ?, ?, ?)
                                        """, (
                                            -1,  # 特殊 session_id 表示這是比較用的商品
                                            candidate['platform'],
                                            candidate['title'],
                                            candidate['price'],
                                            candidate['url'],
                                            candidate.get('image_url', '')
                                        ))
                                        
                                        # 獲取剛插入或已存在的商品ID
                                        product_id = cursor.execute(
                                            "SELECT id FROM products WHERE url = ?", 
                                            (candidate['url'],)
                                        ).fetchone()['id']
                                        
                                        cache_entries.append((
                                            deal['id'],
                                            product_id,
                                            similarity,
                                            match.get('reason', ''),
                                            match.get('confidence', ''),
                                            match.get('category', ''),
                                            datetime.now().isoformat()
                                        ))
                                        
                                except Exception as e:
                                    print(f"處理匹配結果時發生錯誤: {e}")
                                    continue
                        
                        # 批量插入快取結果
                        if cache_entries:
                            cursor.executemany("""
                                INSERT INTO product_comparison_cache 
                                (target_product_id, similar_product_id, similarity, reason, confidence, category, cache_time)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, cache_entries)
                            conn.commit()
                            print(f"為商品 {deal['title'][:30]}... 快取了 {len(cache_entries)} 個比較結果")
                        
                        processed_count += 1
                        
                        # 每處理10個商品就顯示進度
                        if processed_count % 10 == 0:
                            print(f"已處理 {processed_count}/{len(daily_deals)} 個商品")
                    
                except Exception as e:
                    print(f"計算商品 {deal['title'][:30]}... 的比較結果時發生錯誤: {e}")
                    continue
            
            conn.close()
            print(f"預先計算完成，共處理 {processed_count} 個商品")
            
        except Exception as e:
            print(f"預先計算比較結果時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def get_cached_comparison(self, target_product_name, target_platform, target_price):
        """從快取中獲取商品比較結果"""
        try:
            conn = get_db_connection()
            
            # 查找對應的每日促銷商品
            daily_deal = conn.execute("""
                SELECT * FROM daily_deals 
                WHERE title = ? AND platform = ? AND price = ?
                ORDER BY crawl_time DESC 
                LIMIT 1
            """, (target_product_name, target_platform, target_price)).fetchone()
            
            if daily_deal:
                print(f"找到對應的每日促銷商品，ID: {daily_deal['id']}")
                
                # 從快取中獲取比較結果
                cached_results = conn.execute("""
                    SELECT pcc.*, p.title, p.platform, p.price, p.url, p.image_url
                    FROM product_comparison_cache pcc
                    JOIN products p ON pcc.similar_product_id = p.id
                    WHERE pcc.target_product_id = ?
                    ORDER BY pcc.similarity DESC
                """, (daily_deal['id'],)).fetchall()
                
                conn.close()
                
                if cached_results:
                    print(f"從快取中找到 {len(cached_results)} 個比較結果")
                    
                    # 轉換為前端需要的格式
                    similar_products = []
                    for result in cached_results:
                        similar_products.append({
                            'title': result['title'],
                            'platform': result['platform'],
                            'price': result['price'],
                            'url': result['url'],
                            'image_url': result['image_url'],
                            'similarity': result['similarity'],
                            'reason': result['reason'],
                            'confidence': result['confidence'],
                            'category': result['category'],
                            'source_table': 'cache'
                        })
                    
                    return {
                        'similarProducts': similar_products,
                        'totalCandidates': len(similar_products),
                        'totalMatches': len(similar_products),
                        'targetProduct': {
                            'title': target_product_name,
                            'platform': target_platform,
                            'price': target_price
                        },
                        'source': 'cache'
                    }
            
            conn.close()
            return None
            
        except Exception as e:
            print(f"從快取獲取比較結果時發生錯誤: {e}")
            return None
    
    def compare_products_realtime(self, target_product):
        """即時商品比較（當快取中沒有結果時使用）"""
        try:
            print("快取中沒有找到結果，回退到即時計算...")
            
            # 獲取候選商品
            candidate_products = self.get_candidate_products_for_comparison(target_product)
            
            if not candidate_products:
                print("警告: 沒有候選商品可供比較")
                return {
                    'similarProducts': [], 
                    'totalCandidates': 0,
                    'message': '沒有候選商品可供比較'
                }

            print("開始調用 AI 進行商品比較...")
            matches = self.product_comparison_service.compare_products(target_product, candidate_products)
            print(f"AI 回傳 {len(matches)} 個匹配結果")
            
            similar_products = []
            for i, match in enumerate(matches):            
                similarity = match.get('similarity', 0)
                if similarity >= 0.70:
                    try:
                        product_index = match['index']
                        if 0 <= product_index < len(candidate_products):
                            product = candidate_products[product_index]
                            product['similarity'] = similarity
                            product['reason'] = match.get('reason', '')
                            product['confidence'] = match.get('confidence', '')
                            product['category'] = match.get('category', '')
                            similar_products.append(product)
                    except (IndexError, KeyError) as e:
                        print(f"解析比較結果時發生錯誤: {e}")
                        continue

            similar_products.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            
            return {
                'similarProducts': similar_products,
                'totalCandidates': len(candidate_products),
                'totalMatches': len(matches),
                'targetProduct': target_product,
                'source': 'realtime'
            }
            
        except Exception as e:
            print(f"即時商品比較時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            raise e
