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
from crawler_database import CrawlerDatabase

app = Flask(__name__)

# 設定靜態檔案路徑
app.static_folder = 'static'
app.template_folder = 'templates'

# 初始化爬蟲管理器和資料庫
crawler_manager = CrawlerManager()
db = CrawlerDatabase()

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

@app.route('/api/search')
def search_products():
    """搜尋商品（支援 SQLite 和 JSON 雙重來源）"""
    keyword = request.args.get('keyword', '').strip()
    platform = request.args.get('platform', 'all')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    limit = request.args.get('limit', 50, type=int)
    use_sqlite = request.args.get('use_sqlite', 'true').lower() == 'true'
    
    if not keyword:
        return jsonify({'error': '請輸入搜尋關鍵字'}), 400
    
    try:
        if use_sqlite:
            # 優先使用 SQLite 搜尋
            products = db.search_products(
                keyword=keyword,
                platform=platform if platform != 'all' else None,
                min_price=min_price,
                max_price=max_price,
                limit=limit
            )
            
            return jsonify({
                'products': products,
                'total': len(products),
                'keyword': keyword,
                'source': 'sqlite',
                'status': 'success'
            })
        else:
            # 使用 JSON 檔案搜尋（備援方案）
            return search_products_from_json(keyword, platform, min_price, max_price, limit)
            
    except Exception as e:
        print(f"SQLite 搜尋失敗，改用 JSON 搜尋: {e}")
        return search_products_from_json(keyword, platform, min_price, max_price, limit)

def search_products_from_json(keyword, platform, min_price, max_price, limit):
    """從 JSON 檔案搜尋商品（備援方案）"""
    results_dir = crawler_manager.output_dir
    all_products = []
    
    # 搜尋所有 JSON 檔案
    json_files = glob.glob(os.path.join(results_dir, "*.json"))
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 處理不同格式的 JSON 檔案
            products = []
            if 'results' in data:
                # 新格式：多平台結果
                for plat, result in data['results'].items():
                    if platform != 'all' and plat != platform:
                        continue
                    products.extend(result.get('products', []))
            elif 'products' in data:
                # 舊格式：單平台結果
                file_platform = data.get('platform', 'unknown')
                if platform == 'all' or file_platform == platform:
                    products = data['products']
            
            # 過濾產品
            for product in products:
                title = product.get('title', '').lower()
                if keyword.lower() in title:
                    # 價格過濾
                    price = product.get('price_numeric', product.get('price', 0))
                    if isinstance(price, str):
                        price = float(price.replace('$', '').replace(',', '').replace('NT', '') or 0)
                    
                    if min_price is not None and price < min_price:
                        continue
                    if max_price is not None and price > max_price:
                        continue
                    
                    all_products.append(product)
                    
                    if len(all_products) >= limit:
                        break
            
            if len(all_products) >= limit:
                break
                
        except Exception as e:
            print(f"讀取檔案 {file_path} 失敗: {e}")
    
    return jsonify({
        'products': all_products[:limit],
        'total': len(all_products),
        'keyword': keyword,
        'source': 'json',
        'status': 'success'
    })

@app.route('/api/sqlite/sessions')
def get_sqlite_sessions():
    """獲取 SQLite 中的爬蟲執行記錄"""
    try:
        limit = request.args.get('limit', 20, type=int)
        platform = request.args.get('platform')
        
        sessions = db.get_crawl_sessions(platform=platform, limit=limit)
        
        return jsonify({
            'sessions': sessions,
            'total': len(sessions),
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': f'獲取執行記錄失敗: {str(e)}'}), 500

@app.route('/api/sqlite/products/<int:session_id>')
def get_sqlite_products_by_session(session_id):
    """獲取特定執行記錄的商品"""
    try:
        products = db.get_products_by_session(session_id)
        
        return jsonify({
            'products': products,
            'session_id': session_id,
            'total': len(products),
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': f'獲取商品失敗: {str(e)}'}), 500

@app.route('/api/sqlite/stats')
def get_sqlite_stats():
    """獲取 SQLite 資料庫統計"""
    try:
        stats = db.get_database_stats()
        
        return jsonify({
            'stats': stats,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': f'獲取統計失敗: {str(e)}'}), 500

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
    """獲取每日促銷（直接讀取 PChome 和 Yahoo 檔案）"""
    daily_deals = []
    
    # 直接讀取 PChome 促銷檔案
    pchome_file = os.path.join(crawler_manager.output_dir, "crawler_results_pchome_onsale.json")
    if os.path.exists(pchome_file):
        try:
            print(f"讀取 PChome 檔案: {pchome_file}")
            with open(pchome_file, 'r', encoding='utf-8') as f:
                pchome_data = json.load(f)
            
            # 使用檔案的時間戳記或修改時間
            crawl_time = pchome_data.get('timestamp') or pchome_data.get('crawl_time')
            if not crawl_time:
                file_mtime = os.path.getmtime(pchome_file)
                crawl_time = datetime.fromtimestamp(file_mtime).isoformat()
            
            file_info = {
                'filename': 'crawler_results_pchome_onsale.json',
                'filepath': pchome_file,
                'keyword': 'PChome 促銷',
                'total_products': pchome_data.get('total_products', len(pchome_data.get('products', []))),
                'crawl_time': crawl_time,
                'file_size': os.path.getsize(pchome_file),
                'platform': 'pchome_onsale',
                'products': pchome_data.get('products', [])
            }
            daily_deals.append(file_info)
            print(f"PChome 資料: {file_info['total_products']} 個商品, 時間: {crawl_time}")
            
        except Exception as e:
            print(f"讀取 PChome 檔案失敗: {e}")
    
    # 直接讀取 Yahoo 秒殺檔案
    yahoo_file = os.path.join(crawler_manager.output_dir, "crawler_results_yahoo_rushbuy.json")
    if os.path.exists(yahoo_file):
        try:
            print(f"讀取 Yahoo 檔案: {yahoo_file}")
            with open(yahoo_file, 'r', encoding='utf-8-sig') as f:
                yahoo_data = json.load(f)
            
            # 使用檔案的時間戳記或修改時間
            crawl_time = yahoo_data.get('timestamp') or yahoo_data.get('crawl_time')
            if not crawl_time:
                file_mtime = os.path.getmtime(yahoo_file)
                crawl_time = datetime.fromtimestamp(file_mtime).isoformat()
            
            file_info = {
                'filename': 'crawler_results_yahoo_rushbuy.json',
                'filepath': yahoo_file,
                'keyword': 'Yahoo 秒殺',
                'total_products': yahoo_data.get('total_products', len(yahoo_data.get('products', []))),
                'crawl_time': crawl_time,
                'file_size': os.path.getsize(yahoo_file),
                'platform': 'yahoo_rushbuy',
                'products': yahoo_data.get('products', [])
            }
            daily_deals.append(file_info)
            print(f"Yahoo 資料: {file_info['total_products']} 個商品, 時間: {crawl_time}")
            
        except Exception as e:
            print(f"讀取 Yahoo 檔案失敗: {e}")
    
    # 按時間排序（最新的在前面）
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
    
    # 獲取最新更新時間
    latest_update = daily_deals[0]['crawl_time'] if daily_deals else ''
    
    print(f"回傳 {len(daily_deals)} 個平台資料, 總商品: {sum(deal['total_products'] for deal in daily_deals)}")
    print(f"最新更新時間: {latest_update}")
    
    return jsonify({
        'daily_deals': daily_deals,
        'total_deals': sum(deal['total_products'] for deal in daily_deals),
        'latest_update': latest_update,
        'platform_updates': platform_update_times,
        'next_update_times': {
            'morning': '10:00',
            'afternoon': '15:00', 
            'evening': '21:00'
        },
        'status': 'success'
    })

@app.route('/daily-deals')
def daily_deals_page():
    """每日促銷專頁"""
    return render_template('daily_deals.html')

@app.route('/dashboard')
def dashboard_page():
    """系統儀表板"""
    return render_template('dashboard.html')

# 測試頁面路由
@app.route('/api_test.html')
def api_test_page():
    """API 測試頁面"""
    return render_template('api_test.html')

@app.route('/image_test.html')
def image_test_page():
    """圖片測試頁面"""
    return render_template('image_test.html')

if __name__ == '__main__':
    # 確保templates和static目錄存在
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("爬蟲結果展示網站啟動中...")
    print("請訪問: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
