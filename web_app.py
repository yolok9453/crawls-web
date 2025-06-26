"""
爬蟲結果展示網頁應用
使用Flask建立Web介面來顯示和管理爬蟲結果
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
import glob
from datetime import datetime
from crawler_manager import CrawlerManager


app = Flask(__name__)

# 設定靜態檔案路徑
app.static_folder = 'static'
app.template_folder = 'templates'

# 初始化爬蟲管理器
crawler_manager = CrawlerManager()

# 配置應用程式



@app.route('/')
def index():
    """主頁面"""
    return render_template('index.html')

@app.route('/api/crawlers')
def get_crawlers():
    """獲取可用的爬蟲列表（排除每日促銷爬蟲）"""
    all_crawlers = crawler_manager.list_crawlers()
    # 排除 pchome_onsale，因為這是每日促銷專用的，不讓用戶手動執行
    available_crawlers = [crawler for crawler in all_crawlers if crawler != 'pchome_onsale']
    
    return jsonify({
        'crawlers': available_crawlers,
        'status': 'success'
    })

@app.route('/api/results')
def get_results():
    """獲取所有爬蟲結果檔案（排除每日促銷專用檔案）"""
    results_dir = crawler_manager.output_dir
    files = []
    
    # 搜尋所有JSON檔案
    json_files = glob.glob(os.path.join(results_dir, "*.json"))
    
    for file_path in json_files:
        filename = os.path.basename(file_path)
        
        # 排除每日促銷專用檔案
        if 'pchome_onsale' in filename or 'yahoo_rushbuy' in filename:
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            file_info = {
                'filename': os.path.basename(file_path),
                'filepath': file_path,
                'keyword': data.get('keyword', 'unknown'),
                'total_products': data.get('total_products', 0),
                'crawl_time': data.get('crawl_time', ''),
                'file_size': os.path.getsize(file_path),
                'platforms': list(data.get('results', {}).keys()) if 'results' in data else [data.get('platform', 'unknown')]
            }
            files.append(file_info)
        except Exception as e:
            print(f"讀取檔案 {file_path} 失敗: {e}")
    
    # 按時間排序（最新的在前面）
    files.sort(key=lambda x: x['crawl_time'], reverse=True)
    
    return jsonify({
        'files': files,
        'status': 'success'
    })

@app.route('/api/result/<filename>')
def get_result_detail(filename):
    """獲取特定結果檔案的詳細內容"""
    file_path = os.path.join(crawler_manager.output_dir, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': '檔案不存在'}), 404
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify({
            'data': data,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': f'讀取檔案失敗: {str(e)}'}), 500

@app.route('/api/crawl', methods=['POST'])
def start_crawl():
    """啟動新的爬蟲任務"""
    try:
        data = request.get_json()
        keyword = data.get('keyword', '')
        platforms = data.get('platforms', [])
        max_products = int(data.get('max_products', 100))
        min_price = int(data.get('min_price', 0))
        max_price = int(data.get('max_price', 999999))
        
        if not keyword:
            return jsonify({'error': '請輸入搜索關鍵字'}), 400
        
        if not platforms:
            platforms = crawler_manager.list_crawlers()
        
        # 執行爬蟲
        results = crawler_manager.run_all_crawlers(
            keyword=keyword,
            max_products=max_products,
            min_price=min_price,
            max_price=max_price,
            platforms=platforms
        )
        
        # 保存結果
        filename = crawler_manager.save_results(keyword, results)
        
        return jsonify({
            'status': 'success',
            'message': '爬蟲執行完成',
            'filename': os.path.basename(filename),
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': f'爬蟲執行失敗: {str(e)}'}), 500

@app.route('/api/statistics/<filename>')
def get_statistics(filename):
    """獲取特定結果的統計資訊"""
    file_path = os.path.join(crawler_manager.output_dir, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': '檔案不存在'}), 404
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 計算統計資訊
        stats = {
            'keyword': data.get('keyword', ''),
            'total_products': 0,
            'platforms': {},
            'price_stats': {
                'min': float('inf'),
                'max': 0,
                'average': 0,
                'total': 0
            }
        }
        
        all_prices = []
        
        # 處理新格式（包含多個平台）
        if 'results' in data:
            results = data['results']
            for platform, result in results.items():
                platform_stats = {
                    'product_count': result.get('total_products', 0),
                    'status': result.get('status', 'unknown'),
                    'execution_time': result.get('execution_time', 0)
                }
                stats['platforms'][platform] = platform_stats
                stats['total_products'] += platform_stats['product_count']
                
                # 收集價格
                for product in result.get('products', []):
                    price = product.get('price', 0)
                    if price > 0:
                        all_prices.append(price)
        
        # 處理舊格式（單一平台）
        elif 'products' in data:
            platform = data.get('platform', 'unknown')
            stats['platforms'][platform] = {
                'product_count': len(data['products']),
                'status': 'success',
                'execution_time': 0
            }
            stats['total_products'] = len(data['products'])
            
            for product in data['products']:
                price = product.get('price', 0)
                if price > 0:
                    all_prices.append(price)
        
        # 計算價格統計
        if all_prices:
            stats['price_stats']['min'] = min(all_prices)
            stats['price_stats']['max'] = max(all_prices)
            stats['price_stats']['average'] = sum(all_prices) / len(all_prices)
            stats['price_stats']['total'] = len(all_prices)
        else:
            stats['price_stats']['min'] = 0
        
        return jsonify({
            'statistics': stats,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': f'統計計算失敗: {str(e)}'}), 500

@app.route('/view/<filename>')
def view_result(filename):
    """查看特定結果的詳細頁面"""
    return render_template('result_detail.html', filename=filename)

@app.route('/crawler')
def crawler_page():
    """爬蟲執行頁面"""
    return render_template('crawler.html')

@app.route('/api/daily-deals')
def get_daily_deals():
    """獲取每日促銷（PCHOME ONSALE + YAHOO RUSHBUY）結果"""
    results_dir = crawler_manager.output_dir
    daily_deals = []
    
    # 處理 PCHOME ONSALE 商品
    pchome_file = os.path.join(results_dir, "crawler_results_pchome_onsale.json")
    if os.path.exists(pchome_file):
        try:
            with open(pchome_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 處理新格式（有 results 結構）或舊格式
            if 'results' in data and 'pchome_onsale' in data['results']:
                # 新格式：有 results 結構
                pchome_result = data['results']['pchome_onsale']
                file_info = {
                    'filename': os.path.basename(pchome_file),
                    'filepath': pchome_file,
                    'keyword': data.get('keyword', 'pchome_onsale'),
                    'total_products': pchome_result.get('total_products', 0),
                    'crawl_time': data.get('crawl_time', pchome_result.get('crawl_time', '')),
                    'file_size': os.path.getsize(pchome_file),
                    'platform': 'pchome_onsale',
                    'products': pchome_result.get('products', [])
                }
                daily_deals.append(file_info)
            elif data.get('platform') == 'pchome_onsale' or 'pchome_onsale' in data.get('keyword', ''):
                # 舊格式：直接包含產品資料
                file_info = {
                    'filename': os.path.basename(pchome_file),
                    'filepath': pchome_file,
                    'keyword': data.get('keyword', 'pchome_onsale'),
                    'total_products': data.get('total_products', 0),
                    'crawl_time': data.get('crawl_time', data.get('timestamp', '')),
                    'file_size': os.path.getsize(pchome_file),
                    'platform': 'pchome_onsale',
                    'products': data.get('products', [])
                }
                daily_deals.append(file_info)
        except Exception as e:
            print(f"讀取 PChome 每日促銷檔案失敗: {e}")
    
    # 處理 YAHOO RUSHBUY 商品
    yahoo_file = os.path.join(results_dir, "crawler_results_yahoo_rushbuy.json")
    if os.path.exists(yahoo_file):
        try:
            with open(yahoo_file, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
                
            if data.get('platform') == 'yahoo_rushbuy':
                file_info = {
                    'filename': os.path.basename(yahoo_file),
                    'filepath': yahoo_file,
                    'keyword': data.get('keyword', 'yahoo_rushbuy'),
                    'total_products': data.get('total_products', 0),
                    'crawl_time': data.get('crawl_time', data.get('timestamp', '')),
                    'file_size': os.path.getsize(yahoo_file),
                    'platform': 'yahoo_rushbuy',
                    'products': data.get('products', [])
                }
                daily_deals.append(file_info)
        except Exception as e:
            print(f"讀取 Yahoo 秒殺檔案失敗: {e}")    # 按時間排序（最新的在前面）
    daily_deals.sort(key=lambda x: x.get('crawl_time', ''), reverse=True)
    
    # 支援平台過濾
    platform_filter = request.args.get('platform', 'all')
    if platform_filter != 'all':
        daily_deals = [deal for deal in daily_deals if deal['platform'] == platform_filter]
    
    # 取得各平台最後更新時間
    platform_update_times = {}
    for deal in daily_deals:
        platform = deal['platform']
        if platform not in platform_update_times:
            platform_update_times[platform] = deal.get('crawl_time', '')
    
    return jsonify({
        'daily_deals': daily_deals,
        'total_deals': sum(deal['total_products'] for deal in daily_deals),
        'latest_update': daily_deals[0]['crawl_time'] if daily_deals else '',
        'platform_updates': platform_update_times,
        'next_update_times': {
            'morning': '08:00',
            'afternoon': '14:00',
            'evening': '20:00',
            'night': '02:00'
        },
        'status': 'success'
    })

@app.route('/daily-deals')
def daily_deals_page():
    """每日促銷專頁"""
    return render_template('daily_deals.html')

@app.route('/api/products/compare', methods=['POST'])
def compare_products():
    """商品比較 API"""
    print("=" * 50)
    print("進入商品比較 API")
    print("=" * 50)
    
    if not GEMINI_AVAILABLE or not model:
        print("Gemini API 不可用")
        return jsonify({
            'error': 'Gemini API 未配置，無法使用商品比較功能',
            'similarProducts': []
        }), 503
    
    try:
        data = request.get_json()
        target_product = {
            'title': data.get('productName', ''),
            'platform': data.get('platform', ''),
            'price': data.get('price', 0)
        }
        
        # 從所有爬蟲結果中尋找候選商品
        candidate_products = []
        results_dir = crawler_manager.output_dir
        json_files = glob.glob(os.path.join(results_dir, "*.json"))
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                
                # 從不同格式的檔案中提取商品
                products = extract_products_from_file(file_data)
                
                # 第一層過濾：使用改進的關鍵字過濾減少候選商品數量
                keywords = extract_keywords(target_product['title'])
                if keywords['core'] or keywords['important']:
                    filtered_products = []
                    for product in products:
                        product_title = product.get('title', product.get('name', ''))
                        product_lower = product_title.lower()
                        
                        # 更嚴格的匹配條件
                        match_score = 0
                        total_core = len(keywords['core'])
                        total_important = len(keywords['important'])
                        
                        # 核心關鍵字匹配（品牌、型號）
                        core_matches = sum(1 for kw in keywords['core'] if kw.lower() in product_lower)
                        # 重要關鍵字匹配（規格）
                        important_matches = sum(1 for kw in keywords['important'] if kw.lower() in product_lower)
                        
                        # 計算匹配分數
                        if total_core > 0:
                            match_score += (core_matches / total_core) * 0.6  # 核心關鍵字權重60%
                        if total_important > 0:
                            match_score += (important_matches / total_important) * 0.4  # 重要關鍵字權重40%
                        
                        # 只保留匹配分數 >= 0.5 的商品（至少一半關鍵字匹配）
                        if match_score >= 0.5:
                            filtered_products.append(product)
                    
                    print(f"檔案 {os.path.basename(file_path)}: 關鍵字過濾")
                    print(f"  核心關鍵字: {keywords['core']}")
                    print(f"  重要關鍵字: {keywords['important']}")
                    print(f"  過濾前: {len(products)} 個商品")
                    print(f"  過濾後: {len(filtered_products)} 個商品")
                    
                    candidate_products.extend(filtered_products)
                else:
                    print(f"檔案 {os.path.basename(file_path)}: 無有效關鍵字，加入所有 {len(products)} 個商品")
                    candidate_products.extend(products)
                    
            except Exception as e:
                print(f"讀取檔案 {file_path} 失敗: {e}")
                continue
        
        # 移除與目標商品相同的商品
        candidate_products = [p for p in candidate_products 
                            if p.get('title', '') != target_product['title'] or 
                               p.get('platform', '') != target_product['platform']]
        
        if not candidate_products:
            return jsonify({
                'similarProducts': [],
                'totalCandidates': 0,
                'totalMatches': 0
            })
        
        print(f"找到 {len(candidate_products)} 個候選商品進行比較")
        
        # 顯示過濾後的候選商品JSON
        print("=" * 60)
        print("過濾後的候選商品列表 (JSON格式):")
        print("=" * 60)
        candidate_products_json = json.dumps(candidate_products, ensure_ascii=False, indent=2)
        print(candidate_products_json)
        print("=" * 60)
        print(f"候選商品總數: {len(candidate_products)}")
        
        # 保存過濾後的候選商品到檔案
        # 清理檔案名稱中的特殊字符
        clean_title = target_product['title'].replace(' ', '_').replace('/', '_').replace('\\', '_').replace(':', '_').replace('?', '_').replace('*', '_').replace('<', '_').replace('>', '_').replace('|', '_').replace('"', '_')
        filtered_filename = f"filtered_candidates_{clean_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filtered_filepath = os.path.join(crawler_manager.output_dir, filtered_filename)
        
        print(f"🔍 準備保存過濾結果...")
        print(f"📁 目標目錄: {crawler_manager.output_dir}")
        print(f"📄 檔案名稱: {filtered_filename}")
        print(f"📍 完整路徑: {filtered_filepath}")
        
        try:
            # 確保目錄存在
            os.makedirs(crawler_manager.output_dir, exist_ok=True)
            print(f"✅ 目錄確認存在: {os.path.exists(crawler_manager.output_dir)}")
            
            filtered_data = {
                'target_product': target_product,
                'filter_keywords': extract_keywords(target_product['title']),
                'total_candidates': len(candidate_products),
                'filtered_time': datetime.now().isoformat(),
                'note': '第一層改進關鍵字過濾後的候選商品，採用加權匹配分數≥0.5，將交由Gemini AI進行第二層智慧比對',
                'candidates': candidate_products
            }
            
            print(f"💾 開始寫入檔案...")
            with open(filtered_filepath, 'w', encoding='utf-8') as f:
                json.dump(filtered_data, f, ensure_ascii=False, indent=2)
            
            # 驗證檔案是否成功創建
            if os.path.exists(filtered_filepath):
                file_size = os.path.getsize(filtered_filepath)
                print(f"✅ 過濾結果已成功保存!")
                print(f"📁 檔案位置: {filtered_filepath}")
                print(f"� 檔案大小: {file_size} bytes")
            else:
                print(f"❌ 檔案創建失敗，檔案不存在")
            
        except PermissionError as e:
            print(f"❌ 權限錯誤: {e}")
            print(f"💡 請確認對 {crawler_manager.output_dir} 目錄有寫入權限")
        except Exception as e:
            print(f"❌ 保存過濾結果失敗: {e}")
            print(f"❌ 錯誤類型: {type(e).__name__}")
            import traceback
            print(f"❌ 詳細錯誤: {traceback.format_exc()}")
        
        # 顯示前3個商品的詳細信息
        for i, product in enumerate(candidate_products[:3]):
            print(f"\n候選商品 {i+1}:")
            print(f"  - 標題: {product.get('title', product.get('name', ''))}")
            print(f"  - 平台: {product.get('platform', '')}")
            print(f"  - 價格: ${product.get('price', 0)}")
            print(f"  - URL: {product.get('url', '')}")
        
        if len(candidate_products) > 3:
            print(f"\n... 還有 {len(candidate_products) - 3} 個商品")
        print("=" * 60)
        
        # 使用 Gemini 進行單次比較
        try:
            matches = product_comparison_service.compare_products(target_product, candidate_products)
            print(f"單次API呼叫完成，找到 {len(matches)} 個匹配結果")
        except Exception as e:
            print(f"商品比較API呼叫失敗: {e}")
            matches = []
        
        # 過濾並組織結果
        similar_products = []
        for match in matches:
            if match.get('similarity', 0) >= 0.75:  # 降低門檻到0.75
                product = candidate_products[match['index']]
                similar_product = {
                    'title': product.get('title', product.get('name', '')),
                    'price': product.get('price', 0),
                    'platform': product.get('platform', ''),
                    'url': product.get('url', ''),
                    'image_url': product.get('image_url', ''),
                    'similarity': match.get('similarity', 0),
                    'reason': match.get('reason', ''),
                    'confidence': match.get('confidence', '中'),
                    'category': match.get('category', '相似商品')
                }
                similar_products.append(similar_product)
        
        # 按相似度排序
        similar_products.sort(key=lambda x: x['similarity'], reverse=True)
        
        print(f"找到 {len(similar_products)} 個相似商品 (≥75%)")
        
        return jsonify({
            'similarProducts': similar_products,
            'totalCandidates': len(candidate_products),
            'totalMatches': len(matches),
            'highQualityMatches': len(similar_products),
            'similarityThreshold': 0.75
        })
        
    except Exception as e:
        print(f"商品比較錯誤: {e}")
        return jsonify({
            'error': f'商品比較失敗: {str(e)}',
            'similarProducts': []
        }), 500

def extract_products_from_file(file_data):
    """從檔案資料中提取商品列表"""
    products = []
    
    # 處理新格式（有 results 結構）
    if 'results' in file_data:
        for platform, platform_data in file_data['results'].items():
            if 'products' in platform_data:
                for product in platform_data['products']:
                    product['platform'] = platform
                    products.append(product)
    
    # 處理舊格式（直接包含產品資料）
    elif 'products' in file_data:
        for product in file_data['products']:
            if 'platform' not in product:
                product['platform'] = file_data.get('platform', 'unknown')
            products.append(product)
    
    return products

def extract_keywords(text):
    """提取關鍵字並按重要性分類 - 通用版本適用於各種商品類型"""
    if not text:
        return {'core': [], 'important': [], 'optional': []}
    
    # 移除常見的無意義詞彙
    stop_words = ['的', '和', '與', '或', '及', '個', '組', '入', '盒', '包', '裝', '版', '型', '款', '件', '條', '支', '片', '顆', '台', '部', '隻', '雙', '對']
    
    # 通用品牌關鍵詞（核心）- 覆蓋多種商品類型
    core_brands = [
        # 3C電子品牌
        'Apple', 'iPhone', 'iPad', 'MacBook', 'Samsung', 'LG', 'Sony', 'ASUS', 'MSI', 'GIGABYTE', '技嘉', '微星', '華碩',
        'Dell', 'HP', 'Lenovo', 'Acer', 'NVIDIA', 'AMD', 'Intel', 'GeForce', 'RTX', 'GTX', 'Radeon', 'Arc',
        # 運動品牌
        'Nike', 'Adidas', 'PUMA', 'New Balance', 'Converse', 'Vans', 'ASICS', 'Mizuno', 'Under Armour',
        # 汽車品牌
        'Toyota', 'Honda', 'BMW', 'Mercedes', 'Audi', 'Volkswagen', 'Ford', 'Nissan', 'Mazda', 'Hyundai',
        # 家電品牌
        'Panasonic', 'Sharp', 'Toshiba', 'Philips', 'Bosch', 'Siemens', 'Whirlpool', 'Electrolux',
        # 食品品牌
        'Coca-Cola', 'Pepsi', 'Nestle', 'Unilever', 'P&G', 'Johnson', 'Kraft', 'Kellogg',
        # 時尚品牌
        'Gucci', 'Louis Vuitton', 'Chanel', 'Hermès', 'Prada', 'Burberry', 'Coach', 'Michael Kors'
    ]
    
    # 重要規格/型號關鍵詞 - 使用正則表達式匹配模式
    important_patterns = [
        # 數字+單位組合 (如: 32G, 24GB, 1TB, 500GB, 16吋, 14inch等)
        r'\d+[GT]B?',  # 記憶體/儲存容量
        r'\d+吋',      # 螢幕尺寸
        r'\d+inch',    # 英寸尺寸
        # 型號數字 (如: 5090, 4080, iPhone 15, Galaxy S24等)
        r'\d{3,4}',    # 3-4位數字型號
        # 常見規格詞
        r'Pro|Max|Mini|Plus|Ultra|Super|Ti|Air|Lite'
    ]
    
    # 商品類型關鍵詞（重要）
    product_types = [
        '顯示卡', '顯卡', '主機板', '主板', '處理器', 'CPU', 'GPU', '記憶體', '硬碟', 'SSD', 'HDD',
        '手機', '平板', '筆電', '筆記型電腦', '桌機', '螢幕', '鍵盤', '滑鼠', '耳機', '喇叭',
        '球鞋', '運動鞋', '籃球鞋', '跑鞋', '休閒鞋', '涼鞋', '靴子', '服飾', '上衣', '褲子',
        '冰箱', '洗衣機', '冷氣', '電視', '烤箱', '微波爐', '吸塵器', '除濕機', '空氣清淨機',
        '汽車', '機車', '自行車', '輪胎', '機油', '零件', '配件'
    ]
    
    # 分割文字並分類
    keywords = {'core': [], 'important': [], 'optional': []}
    words = re.split(r'[\s,，。()（）\[\]【】\-_/\\]+', text)
    
    for word in words:
        word = word.strip()
        if len(word) <= 1 or word in stop_words:
            continue
        
        # 檢查是否為核心品牌
        if any(brand.lower() == word.lower() for brand in core_brands):
            keywords['core'].append(word)
        # 檢查是否符合重要規格模式
        elif any(re.match(pattern, word, re.IGNORECASE) for pattern in important_patterns):
            keywords['important'].append(word)
        # 檢查是否為商品類型
        elif any(ptype.lower() in word.lower() for ptype in product_types):
            keywords['important'].append(word)
        # 檢查是否為純數字（可能是重要型號）
        elif word.isdigit() and len(word) >= 2:
            keywords['important'].append(word)
        # 其他有意義的詞彙
        elif len(word) >= 2 and not word.isdigit():
            keywords['optional'].append(word)
    
    # 去重並限制每類關鍵字數量
    keywords['core'] = list(dict.fromkeys(keywords['core']))[:3]  # 最多3個核心關鍵字
    keywords['important'] = list(dict.fromkeys(keywords['important']))[:4]  # 最多4個重要關鍵字
    keywords['optional'] = list(dict.fromkeys(keywords['optional']))[:2]  # 最多2個可選關鍵字
    
    return keywords

# 手動更新 API 已移除，使用 GitHub Actions 自動更新

if __name__ == '__main__':
    # 確保templates和static目錄存在
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("爬蟲結果展示網站啟動中...")
    print("請訪問: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
