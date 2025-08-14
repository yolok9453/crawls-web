#!/usr/bin/env python3
"""
檢查爬蟲系統的完整流程和問題
"""

import os
import sys
import sqlite3
import requests
import importlib.util
from datetime import datetime

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'app'))
sys.path.insert(0, os.path.join(project_root, 'core'))

def check_file_structure():
    """檢查文件結構"""
    print("=== 檢查文件結構 ===")
    
    required_files = [
        'main.py',
        'app/web_app.py',
        'core/database.py',
        'core/crawler_manager.py',
        'config/requirements.txt',
        'data/crawler_data.db'
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (缺失)")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def check_database():
    """檢查資料庫連接和結構"""
    print("\n=== 檢查資料庫 ===")
    
    try:
        from core.database import get_db_connection, init_db
        
        # 初始化資料庫
        init_db()
        print("✅ 資料庫初始化成功")
        
        # 檢查連接
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 檢查表是否存在
        tables = ['crawl_sessions', 'products', 'daily_deals']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✅ {table} 表: {count} 筆記錄")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 資料庫檢查失敗: {e}")
        return False

def check_crawlers():
    """檢查爬蟲模組"""
    print("\n=== 檢查爬蟲模組 ===")
    
    try:
        from core.crawler_manager import CrawlerManager
        
        manager = CrawlerManager()
        crawlers = manager.list_crawlers()
        
        print(f"✅ 成功載入 {len(crawlers)} 個爬蟲:")
        for crawler in crawlers:
            print(f"  - {crawler}")
        
        return len(crawlers) > 0
        
    except Exception as e:
        print(f"❌ 爬蟲檢查失敗: {e}")
        return False

def check_dependencies():
    """檢查Python依賴套件"""
    print("\n=== 檢查依賴套件 ===")
    
    required_packages = [
        ('flask', 'flask'),
        ('requests', 'requests'),
        ('beautifulsoup4', 'bs4'),
        ('selenium', 'selenium'),
        ('lxml', 'lxml'),
        ('python-dotenv', 'dotenv')
    ]
    
    missing_packages = []
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} (未安裝)")
            missing_packages.append(package_name)
    
    # 檢查可選套件
    try:
        import google.generativeai as genai
        print("✅ google-generativeai (AI功能可用)")
    except ImportError:
        print("⚠️ google-generativeai (AI功能將被禁用)")
    
    return len(missing_packages) == 0

def check_environment():
    """檢查環境配置"""
    print("\n=== 檢查環境配置 ===")
    
    # 檢查.env文件
    env_path = os.path.join(project_root, 'config', '.env')
    if os.path.exists(env_path):
        print("✅ .env 文件存在")
        
        # 檢查API密鑰
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
            
            gemini_key = os.getenv('GEMINI_API_KEY')
            if gemini_key:
                print("✅ GEMINI_API_KEY 已配置")
            else:
                print("⚠️ GEMINI_API_KEY 未配置 (AI功能將被禁用)")
        except Exception as e:
            print(f"⚠️ 無法讀取.env文件: {e}")
    else:
        print("⚠️ .env 文件不存在")
    
    return True

def check_web_service():
    """檢查Web服務"""
    print("\n=== 檢查Web服務 ===")
    
    try:
        # 嘗試匯入web_app
        from app.web_app import app
        print("✅ Flask應用程式載入成功")
        
        # 檢查路由
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(str(rule))
        
        print(f"✅ 註冊了 {len(routes)} 個路由")
        important_routes = ['/', '/api/results', '/api/daily-deals', '/crawler']
        for route in important_routes:
            if any(route in r for r in routes):
                print(f"  ✅ {route}")
            else:
                print(f"  ❌ {route} (缺失)")
        
        return True
        
    except Exception as e:
        print(f"❌ Web服務檢查失敗: {e}")
        return False

def test_simple_crawler():
    """測試簡單的爬蟲功能"""
    print("\n=== 測試爬蟲功能 ===")
    
    try:
        from core.crawler_manager import CrawlerManager
        
        manager = CrawlerManager()
        crawlers = manager.list_crawlers()
        
        if not crawlers:
            print("❌ 沒有可用的爬蟲")
            return False
        
        # 選擇第一個爬蟲進行測試
        test_platform = crawlers[0]
        print(f"🧪 測試 {test_platform} 爬蟲...")
        
        # 執行小規模測試
        result = manager.run_single_crawler(
            platform=test_platform,
            keyword="測試商品",
            max_products=3
        )
        
        if result['status'] == 'success':
            print(f"✅ 爬蟲測試成功，獲得 {result['total_products']} 個商品")
            return True
        else:
            print(f"❌ 爬蟲測試失敗: {result.get('error', '未知錯誤')}")
            return False
            
    except Exception as e:
        print(f"❌ 爬蟲測試失敗: {e}")
        return False

def generate_recommendations():
    """生成修復建議"""
    print("\n=== 修復建議 ===")
    
    recommendations = []
    
    # 檢查.env文件
    env_path = os.path.join(project_root, 'config', '.env')
    if not os.path.exists(env_path):
        recommendations.append("1. 創建 config/.env 文件並配置 GEMINI_API_KEY (用於AI功能)")
    
    # 檢查requirements
    req_path = os.path.join(project_root, 'config', 'requirements.txt')
    if os.path.exists(req_path):
        recommendations.append("2. 執行: pip install -r config/requirements.txt")
    
    # 檢查資料庫
    db_path = os.path.join(project_root, 'data', 'crawler_data.db')
    if not os.path.exists(db_path):
        recommendations.append("3. 初始化資料庫: python core/database.py")
    
    recommendations.extend([
        "4. 啟動Web服務: python main.py",
        "5. 訪問 http://localhost:5000 查看界面",
        "6. 測試爬蟲功能: 訪問 /crawler 頁面"
    ])
    
    for rec in recommendations:
        print(f"💡 {rec}")

def main():
    """主要檢查流程"""
    print("🔍 開始檢查爬蟲系統...")
    print(f"📁 專案路徑: {project_root}")
    
    checks = [
        ("文件結構", check_file_structure),
        ("依賴套件", check_dependencies),
        ("環境配置", check_environment),
        ("資料庫", check_database),
        ("爬蟲模組", check_crawlers),
        ("Web服務", check_web_service),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            if check_func():
                passed += 1
                print(f"✅ {name} 檢查通過")
            else:
                print(f"❌ {name} 檢查失敗")
        except Exception as e:
            print(f"❌ {name} 檢查發生異常: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 檢查結果: {passed}/{total} 項通過")
    
    if passed == total:
        print("🎉 所有檢查都通過！系統應該可以正常運行。")
        
        # 額外進行爬蟲測試
        if input("\n是否要進行爬蟲功能測試？(y/N): ").lower() == 'y':
            test_simple_crawler()
    else:
        print("⚠️ 發現問題，請查看上述檢查結果並修復。")
    
    generate_recommendations()

if __name__ == "__main__":
    main()
