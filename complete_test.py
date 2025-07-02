#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
完整功能測試腳本
測試所有 API 端點和功能
"""

import requests
import json
import sys
import time
from datetime import datetime

def test_api_endpoint(url, description):
    """測試單個 API 端點"""
    try:
        print(f"測試 {description}...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ {description} - 成功")
            return True, data
        else:
            print(f"✗ {description} - HTTP {response.status_code}")
            return False, None
            
    except requests.exceptions.ConnectionError:
        print(f"✗ {description} - 連線失敗 (Flask 可能未啟動)")
        return False, None
    except Exception as e:
        print(f"✗ {description} - 錯誤: {e}")
        return False, None

def test_daily_deals_api():
    """測試每日促銷 API"""
    print("=== 測試每日促銷 API ===")
    
    success, data = test_api_endpoint('http://localhost:5000/api/daily-deals', '每日促銷 API')
    
    if success and data:
        print(f"  總促銷數: {data.get('total_deals', 'N/A')}")
        print(f"  最新更新: {data.get('latest_update', 'N/A')}")
        
        daily_deals = data.get('daily_deals', [])
        print(f"  平台數量: {len(daily_deals)}")
        
        for deal in daily_deals:
            platform = deal.get('platform', 'unknown')
            total_products = deal.get('total_products', 0)
            print(f"    - {platform}: {total_products} 個商品")
            
        # 測試平台過濾
        for platform in ['pchome_onsale', 'yahoo_rushbuy']:
            success, filtered_data = test_api_endpoint(
                f'http://localhost:5000/api/daily-deals?platform={platform}', 
                f'{platform} 平台過濾'
            )
            if success and filtered_data:
                filtered_deals = filtered_data.get('daily_deals', [])
                print(f"    {platform} 過濾結果: {len(filtered_deals)} 個平台")
    
    print()

def test_other_apis():
    """測試其他 API"""
    print("=== 測試其他 API ===")
    
    apis = [
        ('http://localhost:5000/api/crawlers', '爬蟲列表 API'),
        ('http://localhost:5000/api/results', '結果檔案 API'),
        ('http://localhost:5000/api/sqlite/sessions', 'SQLite 會話 API'),
    ]
    
    for url, description in apis:
        success, data = test_api_endpoint(url, description)
        if success and data:
            if 'crawlers' in data:
                print(f"  可用爬蟲: {len(data['crawlers'])}")
            elif 'files' in data:
                print(f"  結果檔案: {len(data['files'])}")
            elif 'sessions' in data:
                print(f"  爬蟲會話: {len(data['sessions'])}")
    
    print()

def test_web_pages():
    """測試網頁頁面"""
    print("=== 測試網頁頁面 ===")
    
    pages = [
        ('http://localhost:5000/', '首頁'),
        ('http://localhost:5000/daily-deals', '每日促銷頁面'),
        ('http://localhost:5000/api_test.html', 'API 測試頁'),
        ('http://localhost:5000/image_test.html', '圖片測試頁'),
        ('http://localhost:5000/image_debug.html', '圖片除錯頁'),
        ('http://localhost:5000/simple_image_test.html', '簡單圖片測試頁'),
        ('http://localhost:5000/cors_test.html', 'CORS 測試頁'),
    ]
    
    for url, description in pages:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✓ {description} - 可訪問")
            else:
                print(f"✗ {description} - HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"✗ {description} - 連線失敗")
        except Exception as e:
            print(f"✗ {description} - 錯誤: {e}")
    
    print()

def main():
    print("==========================================")
    print("         完整功能測試")
    print("==========================================")
    print()
    
    print("注意: 請確保 Flask 應用已經啟動 (python web_app.py)")
    print("等待 3 秒後開始測試...")
    time.sleep(3)
    print()
    
    test_daily_deals_api()
    test_other_apis()
    test_web_pages()
    
    print("=== 測試完成 ===")
    print("如果看到連線失敗，請先啟動 Flask 應用:")
    print("python web_app.py")
    print()
    print("然後重新執行測試:")
    print("python complete_test.py")

if __name__ == "__main__":
    main()
