"""
爬蟲結果展示網頁應用
使用Flask和SQLite建立Web介面來顯示和管理爬蟲結果
"""

from flask import Flask, render_template, request, jsonify
import os
import json
import sys
import importlib.util
import re
from datetime import datetime
from threading import Thread

# 添加路徑到sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.crawler_manager import CrawlerManager
from core.product_filter import ProductFilter
from core.database import get_db_connection, init_db
from core.github_sync import auto_sync_if_needed, download_latest_database
from core.services.product_comparison_service import ProductComparisonService
from core.services.daily_deals_service import DailyDealsService
from core.services.product_comparison_cache_service import ProductComparisonCacheService
from core.services.database_service import DatabaseService

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not installed. Product comparison feature will be disabled.")

app = Flask(__name__)
app.static_folder = 'static'
app.template_folder = 'templates'

# 配置
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# 初始化爬蟲管理器
crawler_manager = CrawlerManager()

# 初始化商品過濾器
try:
    # 注意：ProductFilter 現在需要傳入資料庫連線函式
    product_filter = ProductFilter(db_connection_func=get_db_connection)
    PRODUCT_FILTER_AVAILABLE = True
    print("ProductFilter 初始化成功")
except Exception as e:
    product_filter = None
    PRODUCT_FILTER_AVAILABLE = False
    print(f"Warning: ProductFilter 初始化失敗: {e}. 商品過濾功能將被禁用。")

# 配置 Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash-exp') # 使用 Gemini 2.0 Flash
    print("✅ AI 模型初始化成功 (使用 Gemini 2.0 Flash)")
else:
    model = None
    print("Warning: Gemini API key not found. Product comparison feature will be disabled.")

# 爬蟲狀態追蹤
crawler_status = {
    'is_updating': False,
    'start_time': None,
    'completion_time': None
}

# --- Helper Functions ---
def dict_from_row(row):
    """將 sqlite3.Row 物件轉換為字典"""
    return dict(row) if row else None

def dict_from_rows(rows):
    """將 sqlite3.Row 物件列表轉換為字典列表"""
    return [dict(row) for row in rows]

# --- 初始化服務 ---
product_comparison_service = ProductComparisonService(model)
daily_deals_service = DailyDealsService(crawler_manager)
comparison_cache_service = ProductComparisonCacheService(crawler_manager, product_comparison_service)
database_service = DatabaseService()

# 爬蟲狀態追蹤（兼容舊代碼）
crawler_status = daily_deals_service.get_status()

# --- Web Routes ---
@app.route('/')
def index():
    # 直接在服務器端獲取數據並傳給模板
    try:
        sessions = database_service.get_crawl_sessions()
        print(f"🔍 首頁載入: 找到 {len(sessions)} 個會話")
        if sessions:
            print(f"最新會話: {sessions[0]['keyword']} - {sessions[0]['total_products']} 個商品")
        return render_template('index.html', sessions=sessions)
    except Exception as e:
        print(f"獲取會話數據錯誤: {e}")
        return render_template('index.html', sessions=[])

@app.route('/crawler')
def crawler_page():
    return render_template('crawler.html')

@app.route('/daily-deals')
def daily_deals_page():
    return render_template('daily_deals.html')

@app.route('/test')
def test_api_page():
    return render_template('test_api.html')

@app.route('/test-api-detail')
def test_api_detail():
    return render_template('test_api_detail.html')

@app.route('/view/<int:session_id>')
def view_result(session_id):
    """詳情頁面"""
    print(f"🔍 詳情頁請求: session_id={session_id}")
    return render_template('result_detail_simple.html', session_id=session_id)



# --- API Routes ---
@app.route('/api/crawlers')
def get_crawlers():
    return jsonify({
        'crawlers': crawler_manager.list_crawlers(),
        'status': 'success'
    })

@app.route('/api/crawl', methods=['POST'])
def start_crawl():
    """執行爬蟲任務"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '無效的請求資料'}), 400
        
        keyword = data.get('keyword', '').strip()
        if not keyword:
            return jsonify({'error': '請輸入關鍵字'}), 400
        
        platforms = data.get('platforms', [])
        if not platforms:
            return jsonify({'error': '請選擇至少一個平台'}), 400
        
        max_products = data.get('max_products', 100)
        min_price = data.get('min_price', 0)
        max_price = data.get('max_price', 999999)
        
        # 執行爬蟲
        session_id = crawler_manager.run_all_crawlers(
            keyword=keyword,
            max_products=max_products,
            min_price=min_price,
            max_price=max_price,
            platforms=platforms
        )
        
        # 獲取商品詳情
        conn = get_db_connection()
        products = conn.execute('SELECT * FROM products WHERE session_id = ? ORDER BY price', (session_id,)).fetchall()
        session = conn.execute('SELECT * FROM crawl_sessions WHERE id = ?', (session_id,)).fetchone()
        
        # 按平台組織結果，匹配前端期望的格式
        results = {}
        for platform in platforms:
            platform_products = [dict(p) for p in products if p['platform'] == platform]
            
            results[platform] = {
                'status': 'success' if platform_products else 'failed',
                'total_products': len(platform_products),
                'products': platform_products,
                'execution_time': 0  # 這裡可以從其他地方獲取，暫時設為0
            }
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'results': results,
            'filename': f'crawler_results_{keyword}_{session_id}.json',
            'message': f'成功爬取了 {len(platforms)} 個平台的商品'
        })
        
    except Exception as e:
        print(f"爬蟲API錯誤: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'爬蟲執行失敗: {str(e)}'}), 500

@app.route('/api/results')
def get_results():
    """從資料庫獲取所有爬蟲任務結果"""
    try:
        sessions = database_service.get_crawl_sessions()
        return jsonify({
            'files': sessions, # 'files' for frontend compatibility
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/result/<int:session_id>')
def get_result_detail(session_id):
    """從資料庫獲取特定任務的詳細內容，包含商品列表"""
    try:
        print(f"🔍 API 詳情請求: session_id={session_id}")
        
        # 獲取統計信息
        stats = database_service.get_session_detail(session_id)
        print(f"📊 統計信息: {stats}")
        
        # 獲取商品列表
        conn = get_db_connection()
        products = conn.execute('SELECT * FROM products WHERE session_id = ? ORDER BY price', (session_id,)).fetchall()
        print(f"🛍️ 找到 {len(products)} 個商品")
        
        # 組織成前端期望的格式
        results = {}
        all_platforms = set()
        all_products_list = []  # 收集所有商品到一個列表
        
        for product in products:
            platform = product['platform']
            all_platforms.add(platform)
            all_products_list.append(dict(product))  # 添加到統一商品列表
            
            if platform not in results:
                results[platform] = {
                    'status': 'success',
                    'total_products': 0,
                    'products': [],
                    'execution_time': 0
                }
            
            results[platform]['products'].append(dict(product))
            results[platform]['total_products'] += 1
        
        conn.close()
        
        # 返回前端期望的格式
        return jsonify({
            'status': 'success',
            'data': {
                'session': {
                    'id': session_id,
                    'keyword': stats.get('keyword', ''),
                    'total_products': len(all_products_list),
                    'platforms': list(all_platforms)
                },
                'products': all_products_list
            },
            'results': results,  # 保留原有格式以防其他地方需要
            'statistics': stats,
            'filename': f'crawler_results_session_{session_id}.json',
            'message': f'載入會話 {session_id} 的結果，共 {len(products)} 個商品'
        })
    except Exception as e:
        print(f"獲取會話詳情錯誤: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/daily-deals')
def get_daily_deals():
    """從資料庫獲取每日促銷結果，自動檢查GitHub更新"""
    platform_filter = request.args.get('platform', 'all')
    auto_sync = request.args.get('auto_sync', 'true').lower() == 'true'
    
    try:
        # 如果啟用自動同步，先檢查是否需要從GitHub更新資料
        sync_performed = False
        if auto_sync:
            try:
                # 檢查資料是否需要更新（超過1小時就同步）
                updated = auto_sync_if_needed(max_age_hours=1)
                if updated:
                    sync_performed = True
                    print("✅ 每日促銷API：已從GitHub同步最新資料")
            except Exception as sync_error:
                print(f"⚠️ 每日促銷API：GitHub同步失敗，使用本地資料: {sync_error}")
        
        result = database_service.get_daily_deals(platform_filter)
        result['status'] = 'success'
        result['sync_performed'] = sync_performed
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-daily-deals', methods=['POST'])
def update_daily_deals():
    """更新每日促銷商品數據並存入資料庫"""
    result = daily_deals_service.start_update()
    return jsonify(result)

@app.route('/api/products/compare', methods=['POST'])
def compare_products_api():
    """商品比較 API，優先使用快取結果"""
    print("=== 商品比較 API 開始 ===")
    
    try:
        data = request.get_json()
        print(f"收到的請求資料: {data}")
        
        target_product_name = data.get('productName', '')
        target_platform = data.get('platform', '')
        target_price = data.get('price', 0)
        
        print(f"目標商品: {target_product_name} | {target_platform} | ${target_price}")
        
        # 首先嘗試從快取中獲取結果
        cached_result = comparison_cache_service.get_cached_comparison(
            target_product_name, target_platform, target_price
        )
        
        if cached_result:
            print(f"=== 商品比較 API 完成 (使用快取) ===")
            return jsonify(cached_result)
        
        # 如果快取中沒有結果，則回退到即時計算
        if not GEMINI_AVAILABLE:
            print("錯誤: Gemini 不可用")
            return jsonify({'error': 'Gemini 套件未安裝'}), 503
            
        if not model:
            print("錯誤: Gemini 模型未配置")
            return jsonify({'error': 'Gemini API 未配置或 API 金鑰無效'}), 503
        
        # 即時計算
        target_product = {
            'title': target_product_name,
            'platform': target_platform,
            'price': target_price
        }
        
        result = comparison_cache_service.compare_products_realtime(target_product)
        
        print("=== 商品比較 API 完成 (即時計算) ===")
        return jsonify(result)
        
    except Exception as e:
        print(f"商品比較 API 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'商品比較失敗: {str(e)}'}), 500

@app.route('/api/products/filter', methods=['POST'])
def filter_products_api():
    """商品過濾 API - 使用 ProductFilter 過濾指定 session 的商品"""
    if not PRODUCT_FILTER_AVAILABLE or not product_filter:
        return jsonify({'error': 'ProductFilter 未配置，無法使用商品過濾功能'}), 503
    
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({'error': '請提供要過濾的 session_id'}), 400
        
        stats = product_filter.filter_session_products(session_id)
        
        return jsonify({
            'status': 'success',
            'message': '商品過濾完成',
            'statistics': stats
        })
        
    except Exception as e:
        print(f"商品過濾錯誤: {e}")
        return jsonify({'error': f'商品過濾失敗: {str(e)}'}), 500

@app.route('/api/products/filter-all', methods=['POST'])
def filter_all_products_api():
    """批量過濾所有尚未過濾過的爬蟲任務"""
    if not PRODUCT_FILTER_AVAILABLE or not product_filter:
        return jsonify({'error': 'ProductFilter 未配置，無法使用商品過濾功能'}), 503

    try:
        sessions_to_filter = database_service.get_sessions_to_filter()

        if not sessions_to_filter:
            return jsonify({'status': 'info', 'message': '沒有找到需要過濾的任務'})

        filtered_results = []
        for session in sessions_to_filter:
            session_id = session['id']
            try:
                stats = product_filter.filter_session_products(session_id)
                filtered_results.append({'status': 'success', **stats})
            except Exception as e:
                print(f"過濾 Session {session_id} 失敗: {e}")
                filtered_results.append({'status': 'error', 'session_id': session_id, 'error': str(e)})
        
        return jsonify({
            'status': 'success',
            'message': f'批量過濾完成，處理了 {len(sessions_to_filter)} 個任務',
            'filtered_sessions': filtered_results
        })

    except Exception as e:
        print(f"批量過濾錯誤: {e}")
        return jsonify({'error': f'批量過濾失敗: {str(e)}'}), 500

@app.route('/api/crawler-status')
def get_crawler_status():
    """獲取爬蟲執行狀態"""
    return jsonify(daily_deals_service.get_status())

@app.route('/api/daily-deals/status')
def get_daily_deals_status():
    """獲取每日促銷狀態"""
    try:
        status = database_service.get_daily_deals_status(daily_deals_service.get_status())
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 錯誤處理
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '頁面未找到'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': '伺服器內部錯誤'}), 500

@app.after_request
def add_cors_headers(response):
    """添加CORS頭部，允許本地請求"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    """全局異常處理器"""
    print(f"全局異常捕獲: {e}")
    return jsonify({
        'error': str(e),
        'status': 'error'
    }), 500

# 添加調試路由
@app.route('/api/debug')
def debug_info():
    return jsonify({
        'status': 'success',
        'message': '伺服器運行正常',
        'available_crawlers': crawler_manager.list_crawlers(),
        'product_filter_available': PRODUCT_FILTER_AVAILABLE,
        'gemini_available': GEMINI_AVAILABLE
    })

@app.route('/api/debug/daily-deals')
def debug_daily_deals():
    """調試用：檢查每日促銷狀態"""
    result = database_service.debug_daily_deals(daily_deals_service.get_status())
    return jsonify(result)

@app.route('/api/debug/reset-status', methods=['POST'])
def debug_reset_status():
    """調試用：強制重置爬蟲狀態"""
    result = daily_deals_service.reset_status()
    return jsonify(result)

@app.route('/api/enrich-product-database', methods=['POST'])
def enrich_product_database():
    """手動豐富商品資料庫 - 爬取熱門關鍵字商品"""
    result = daily_deals_service.enrich_product_database()
    return jsonify(result)

@app.route('/api/sync-github-data', methods=['POST'])
def sync_github_data():
    """手動同步GitHub最新資料"""
    try:
        print("🔄 開始從GitHub同步最新資料...")
        
        # 強制下載最新資料庫
        success = download_latest_database()
        
        if success:
            # 重新初始化資料庫服務以使用新資料
            global database_service
            database_service = DatabaseService()
            
            return jsonify({
                'status': 'success',
                'message': '✅ 成功從GitHub同步最新資料',
                'sync_time': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '❌ GitHub資料同步失敗，請稍後再試'
            }), 500
            
    except Exception as e:
        print(f"GitHub同步錯誤: {e}")
        return jsonify({
            'status': 'error', 
            'message': f'同步過程發生錯誤: {str(e)}'
        }), 500

@app.route('/api/check-github-sync', methods=['GET'])
def check_github_sync():
    """檢查是否需要從GitHub同步資料"""
    try:
        from core.github_sync import check_database_update_time
        
        update_time = check_database_update_time()
        
        if update_time:
            # 計算資料庫年齡
            now = datetime.now()
            age_hours = (now - update_time).total_seconds() / 3600
            
            needs_sync = age_hours > 1  # 如果超過1小時就建議同步
            
            return jsonify({
                'status': 'success',
                'last_update': update_time.isoformat(),
                'age_hours': round(age_hours, 2),
                'needs_sync': needs_sync,
                'message': f'資料庫最後更新於 {age_hours:.1f} 小時前'
            })
        else:
            return jsonify({
                'status': 'error',
                'needs_sync': True,
                'message': '本地資料庫不存在，需要同步'
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'檢查同步狀態失敗: {str(e)}'
        }), 500

# ===== 新增的資料庫管理 API =====

@app.route('/api/session/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    """刪除指定的搜尋會話及其所有商品"""
    try:
        conn = get_db_connection()
        
        # 獲取會話信息（用於返回訊息）
        session = conn.execute('SELECT keyword FROM crawl_sessions WHERE id = ?', (session_id,)).fetchone()
        if not session:
            conn.close()
            return jsonify({'status': 'error', 'error': '找不到指定的會話'}), 404
        
        keyword = session['keyword']
        
        # 計算要刪除的商品數量
        product_count = conn.execute('SELECT COUNT(*) as count FROM products WHERE session_id = ?', (session_id,)).fetchone()['count']
        
        # 刪除商品
        conn.execute('DELETE FROM products WHERE session_id = ?', (session_id,))
        
        # 刪除會話
        conn.execute('DELETE FROM crawl_sessions WHERE id = ?', (session_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': f'已刪除關鍵字「{keyword}」的搜尋結果，共清理了 {product_count} 個商品'
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/database/clean/<int:days>', methods=['POST'])
def clean_old_sessions(days):
    """清理指定天數前的舊資料"""
    try:
        conn = get_db_connection()
        
        # 計算日期 (DATETIME 格式)
        cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # 獲取要刪除的會話
        old_sessions = conn.execute('SELECT id FROM crawl_sessions WHERE crawl_time < ?', (cutoff_str,)).fetchall()
        session_ids = [s['id'] for s in old_sessions]
        
        if not session_ids:
            conn.close()
            return jsonify({
                'status': 'success',
                'deleted_sessions': 0,
                'deleted_products': 0,
                'message': f'沒有找到 {days} 天前的資料'
            })
        
        # 計算要刪除的商品數量
        placeholders = ','.join('?' * len(session_ids))
        product_count = conn.execute(f'SELECT COUNT(*) as count FROM products WHERE session_id IN ({placeholders})', session_ids).fetchone()['count']
        
        # 刪除商品
        conn.execute(f'DELETE FROM products WHERE session_id IN ({placeholders})', session_ids)
        
        # 刪除會話
        conn.execute(f'DELETE FROM crawl_sessions WHERE id IN ({placeholders})', session_ids)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'deleted_sessions': len(session_ids),
            'deleted_products': product_count,
            'message': f'成功清理了 {days} 天前的資料'
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/database/clean-empty', methods=['POST'])
def clean_empty_sessions():
    """清理沒有商品的空會話"""
    try:
        conn = get_db_connection()
        
        # 找到沒有商品的會話
        empty_sessions = conn.execute('''
            SELECT cs.id, cs.keyword 
            FROM crawl_sessions cs 
            LEFT JOIN products p ON cs.id = p.session_id 
            WHERE p.session_id IS NULL
        ''').fetchall()
        
        if not empty_sessions:
            conn.close()
            return jsonify({
                'status': 'success',
                'deleted_sessions': 0,
                'message': '沒有找到空的搜尋會話'
            })
        
        # 刪除空會話
        session_ids = [s['id'] for s in empty_sessions]
        placeholders = ','.join('?' * len(session_ids))
        conn.execute(f'DELETE FROM crawl_sessions WHERE id IN ({placeholders})', session_ids)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'deleted_sessions': len(session_ids),
            'message': f'成功清理了 {len(session_ids)} 個空的搜尋會話'
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/database/optimize', methods=['POST'])
def optimize_database():
    """優化資料庫，重建索引和壓縮檔案"""
    try:
        conn = get_db_connection()
        
        # 執行 VACUUM 來壓縮資料庫
        conn.execute('VACUUM')
        
        # 重建索引（如果有的話）
        conn.execute('REINDEX')
        
        # 分析表格以優化查詢計劃
        conn.execute('ANALYZE')
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': '資料庫優化完成，已壓縮檔案並重建索引'
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/database/backup', methods=['POST'])
def backup_database():
    """建立資料庫備份"""
    try:
        import shutil
        from core.database import DB_PATH
        
        # 產生備份檔名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'crawler_data_backup_{timestamp}.db'
        backup_dir = os.path.join(project_root, 'data')
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # 確保備份目錄存在
        os.makedirs(backup_dir, exist_ok=True)
        
        # 複製資料庫檔案
        shutil.copy2(DB_PATH, backup_path)
        
        return jsonify({
            'status': 'success',
            'backup_file': backup_path,
            'message': f'資料庫備份已建立: {backup_filename}'
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/database/stats')
def get_database_stats():
    """獲取資料庫統計資訊"""
    try:
        conn = get_db_connection()
        
        # 基本統計
        total_sessions = conn.execute('SELECT COUNT(*) as count FROM crawl_sessions').fetchone()['count']
        total_products = conn.execute('SELECT COUNT(*) as count FROM products').fetchone()['count']
        empty_sessions = conn.execute('''
            SELECT COUNT(*) as count 
            FROM crawl_sessions cs 
            LEFT JOIN products p ON cs.id = p.session_id 
            WHERE p.session_id IS NULL
        ''').fetchone()['count']
        
        # 日期範圍
        date_range = conn.execute('''
            SELECT 
                MIN(crawl_time) as oldest,
                MAX(crawl_time) as newest
            FROM crawl_sessions
            WHERE crawl_time IS NOT NULL
        ''').fetchone()
        
        # 資料庫檔案大小
        from core.database import DB_PATH
        db_size = 0
        size_str = "未知"
        
        if os.path.exists(DB_PATH):
            db_size = os.path.getsize(DB_PATH)
            if db_size > 1024 * 1024:
                size_str = f"{db_size / (1024 * 1024):.1f} MB"
            elif db_size > 1024:
                size_str = f"{db_size / 1024:.1f} KB"
            else:
                size_str = f"{db_size} Bytes"
        
        # 格式化日期
        def format_datetime(dt_str):
            if dt_str:
                try:
                    # 如果是 datetime 字符串格式，直接返回
                    if isinstance(dt_str, str):
                        return dt_str
                    # 如果是時間戳，轉換格式
                    return datetime.fromtimestamp(dt_str).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    return "未知"
            return "無資料"
        
        oldest_date = format_datetime(date_range['oldest']) if date_range['oldest'] else "無資料"
        newest_date = format_datetime(date_range['newest']) if date_range['newest'] else "無資料"
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'stats': {
                'total_sessions': total_sessions,
                'total_products': total_products,
                'empty_sessions': empty_sessions,
                'db_size': size_str,
                'oldest_session_date': oldest_date,
                'latest_session_date': newest_date
            }
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

if __name__ == '__main__':
    try:
        # 更新資料庫路徑
        import core.database as db
        db.DB_PATH = os.path.join(project_root, 'data', 'crawler_data.db')
        
        init_db() # 確保資料庫和資料表已建立
        print("爬蟲結果展示網站啟動中...")
        print("請訪問: http://localhost:5000")
        print("按 Ctrl+C 停止伺服器")
        
        # 解決 UWSGI 連接問題
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        # 使用簡單的開發伺服器
        app.run(debug=True, host='127.0.0.1', port=5000, threaded=True, use_reloader=False)
    except Exception as e:
        print(f"啟動Web應用時發生錯誤: {e}")
        import traceback
        traceback.print_exc()