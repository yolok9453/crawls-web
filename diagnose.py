#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速診斷腳本
檢查每日促銷 API 的問題
"""

import json
import os
from datetime import datetime

def check_data_files():
    """檢查資料檔案"""
    print("=== 檢查資料檔案 ===")
    
    pchome_file = "crawl_data/crawler_results_pchome_onsale.json"
    yahoo_file = "crawl_data/crawler_results_yahoo_rushbuy.json"
    
    for file_path, name in [(pchome_file, "PChome"), (yahoo_file, "Yahoo")]:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                products = data.get('products', [])
                print(f"{name}: ✓ 存在, {len(products)} 個商品")
                
                if products:
                    print(f"  - 第一個商品: {products[0].get('title', 'N/A')[:50]}")
                    print(f"  - 檔案大小: {os.path.getsize(file_path)} bytes")
                    print(f"  - 修改時間: {datetime.fromtimestamp(os.path.getmtime(file_path))}")
                
            except Exception as e:
                print(f"{name}: ✗ 錯誤 - {e}")
        else:
            print(f"{name}: ✗ 檔案不存在")
    print()

def test_api_endpoint():
    """測試 API 端點"""
    print("=== 測試 API 端點 ===")
    
    try:
        from web_app import app
        print("✓ Flask 應用程式載入成功")
        
        with app.test_client() as client:
            # 測試每日促銷 API
            response = client.get('/api/daily-deals')
            print(f"API 回應狀態: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"✓ API 回應成功")
                print(f"  - 狀態: {data.get('status', 'N/A')}")
                print(f"  - 總促銷數: {data.get('total_deals', 'N/A')}")
                print(f"  - 促銷平台數: {len(data.get('daily_deals', []))}")
                
                if data.get('daily_deals'):
                    for deal in data['daily_deals']:
                        platform = deal.get('platform', 'unknown')
                        products = len(deal.get('products', []))
                        print(f"    * {platform}: {products} 個商品")
            else:
                print(f"✗ API 回應失敗: {response.status_code}")
                print(f"錯誤內容: {response.get_data(as_text=True)}")
        
    except Exception as e:
        print(f"✗ Flask 測試失敗: {e}")
        import traceback
        traceback.print_exc()
    print()

def test_dependencies():
    """檢查依賴套件"""
    print("=== 檢查依賴套件 ===")
    
    required_modules = ['flask', 'json', 'os', 'datetime']
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module} - {e}")
    print()

if __name__ == "__main__":
    print("🔍 每日促銷系統診斷開始...\n")
    
    test_dependencies()
    check_data_files()
    test_api_endpoint()
    
    print("✨ 診斷完成！")
