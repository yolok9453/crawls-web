#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 GitHub Actions 自動化流程的本地測試腳本
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def test_automation_flow():
    """測試整個自動化流程"""
    print("=== 測試 GitHub Actions 自動化流程 ===")
    print(f"測試時間: {datetime.now().isoformat()}")
    
    # 1. 測試執行爬蟲腳本
    print("\n1. 測試執行 PChome OnSale 爬蟲...")
    try:
        result = subprocess.run([
            sys.executable, "run_pchome_onsale.py"
        ], capture_output=True, text=True, encoding='utf-8')
        
        print(f"返回碼: {result.returncode}")
        if result.stdout:
            print("標準輸出:")
            print(result.stdout)
        if result.stderr:
            print("錯誤輸出:")
            print(result.stderr)
            
        if result.returncode == 0:
            print("✅ 爬蟲執行成功")
        else:
            print("❌ 爬蟲執行失敗")
            return False
            
    except Exception as e:
        print(f"❌ 執行爬蟲腳本時發生錯誤: {e}")
        return False
    
    # 2. 檢查生成的檔案
    print("\n2. 檢查生成的檔案...")
    crawl_data_dir = "crawl_data"
    
    if not os.path.exists(crawl_data_dir):
        print("❌ crawl_data 目錄不存在")
        return False
    
    # 檢查是否有 pchome_onsale 檔案
    import glob
    onsale_files = glob.glob(os.path.join(crawl_data_dir, "*pchome_onsale*.json"))
    
    if not onsale_files:
        print("❌ 沒有找到 PChome OnSale 結果檔案")
        return False
    
    print(f"✅ 找到 {len(onsale_files)} 個 PChome OnSale 檔案")
    
    # 檢查最新檔案
    latest_file = max(onsale_files, key=os.path.getmtime)
    print(f"最新檔案: {latest_file}")
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"檔案大小: {os.path.getsize(latest_file)} bytes")
        print(f"關鍵字: {data.get('keyword', 'N/A')}")
        print(f"總商品數: {data.get('total_products', 0)}")
        print(f"爬取時間: {data.get('crawl_time', 'N/A')}")
        
        if 'results' in data and 'pchome_onsale' in data['results']:
            pchome_result = data['results']['pchome_onsale']
            print(f"PChome 狀態: {pchome_result.get('status', 'N/A')}")
            print(f"PChome 商品數: {pchome_result.get('total_products', 0)}")
        
        print("✅ 檔案格式正確")
        
    except Exception as e:
        print(f"❌ 讀取檔案失敗: {e}")
        return False
    
    # 3. 測試 Web API
    print("\n3. 測試 Web API...")
    try:
        import requests
        
        # 假設 Web 應用在本地運行
        # 這部分在 GitHub Actions 中不會執行
        print("📝 注意: Web API 測試需要啟動 Flask 應用")
        print("   可以執行: python web_app.py")
        print("   然後訪問: http://localhost:5000/api/daily-deals")
        
    except ImportError:
        print("📝 未安裝 requests，跳過 API 測試")
    
    # 4. 檢查 GitHub Actions 檔案
    print("\n4. 檢查 GitHub Actions 設置...")
    
    workflow_file = ".github/workflows/update-daily-deals.yml"
    if os.path.exists(workflow_file):
        print("✅ GitHub Actions 工作流程檔案存在")
        
        with open(workflow_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'run_pchome_onsale.py' in content:
            print("✅ 工作流程包含正確的執行腳本")
        else:
            print("❌ 工作流程缺少執行腳本")
            
        if 'cron:' in content:
            print("✅ 工作流程包含定時觸發設置")
        else:
            print("❌ 工作流程缺少定時設置")
            
    else:
        print("❌ GitHub Actions 工作流程檔案不存在")
        return False
    
    print("\n=== 測試完成 ===")
    print("✅ 自動化流程準備就緒")
    print("\n下一步:")
    print("1. 將代碼推送到 GitHub 倉庫")
    print("2. 檢查 GitHub Actions 頁面確認工作流程已啟用")
    print("3. 可以手動觸發一次測試")
    
    return True

if __name__ == "__main__":
    success = test_automation_flow()
    if not success:
        sys.exit(1)
