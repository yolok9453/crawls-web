#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
系統狀態檢查腳本
檢查所有關鍵組件的狀態
"""

import json
import os
import sys
from datetime import datetime

def check_data_files():
    """檢查資料檔案"""
    print("=== 資料檔案狀態 ===")
    
    files_to_check = [
        ("crawl_data/crawler_results_pchome_onsale.json", "PChome 促銷"),
        ("crawl_data/crawler_results_yahoo_rushbuy.json", "Yahoo 秒殺")
    ]
    
    total_products = 0
    
    for file_path, name in files_to_check:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                products = data.get('products', [])
                timestamp = data.get('timestamp', 'N/A')
                
                print(f"✓ {name}: {len(products)} 個商品")
                print(f"  時間戳記: {timestamp}")
                print(f"  檔案大小: {os.path.getsize(file_path):,} bytes")
                
                if products:
                    sample_product = products[0]
                    print(f"  範例商品: {sample_product.get('title', 'N/A')[:40]}...")
                    print(f"  價格: {sample_product.get('price', 'N/A')}")
                    print(f"  圖片: {sample_product.get('image_url', 'N/A')[:50]}...")
                
                total_products += len(products)
                print()
                
            except Exception as e:
                print(f"✗ {name}: 讀取錯誤 - {e}")
        else:
            print(f"✗ {name}: 檔案不存在")
    
    print(f"總商品數: {total_products}")
    print()

def check_web_components():
    """檢查網頁組件"""
    print("=== 網頁組件狀態 ===")
    
    components = [
        ("web_app.py", "Flask 主應用"),
        ("static/daily_deals.js", "每日促銷 JS"),
        ("static/main.js", "主要 JS"),
        ("static/style.css", "樣式表"),
        ("templates/daily_deals.html", "每日促銷頁面"),
        ("templates/index.html", "首頁"),
        ("templates/api_test.html", "API 測試頁"),
        ("templates/image_test.html", "圖片測試頁"),
    ]
    
    for file_path, name in components:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✓ {name}: {size:,} bytes")
        else:
            print(f"✗ {name}: 檔案不存在")
    
    print()

def check_test_tools():
    """檢查測試工具"""
    print("=== 測試工具狀態 ===")
    
    tools = [
        ("api_test.py", "API 自動測試"),
        ("check_images.py", "圖片檢查工具"),
        ("test_image_urls.py", "圖片 URL 測試"),
        ("diagnose.py", "診斷工具"),
        ("auto_crawler_service.py", "自動更新服務"),
    ]
    
    for file_path, name in tools:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✓ {name}: {size:,} bytes")
        else:
            print(f"✗ {name}: 檔案不存在")
    
    print()

def main():
    print("==========================================")
    print("         每日促銷系統狀態檢查")
    print("==========================================")
    print()
    
    check_data_files()
    check_web_components()
    check_test_tools()
    
    print("=== 建議的啟動步驟 ===")
    print("1. 啟動 Flask 應用: python web_app.py")
    print("2. 開啟瀏覽器訪問: http://localhost:5000")
    print("3. 測試每日促銷頁面: http://localhost:5000/daily-deals")
    print("4. 測試 API: http://localhost:5000/api/daily-deals")
    print()
    print("=== 可用的測試頁面 ===")
    print("- API 測試: http://localhost:5000/api_test.html")
    print("- 圖片測試: http://localhost:5000/image_test.html")
    print("- 圖片除錯: http://localhost:5000/image_debug.html")
    print("- 簡單圖片測試: http://localhost:5000/simple_image_test.html")
    print("- CORS 測試: http://localhost:5000/cors_test.html")
    print()
    print("狀態檢查完成！")

if __name__ == "__main__":
    main()
