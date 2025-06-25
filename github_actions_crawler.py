#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub Actions 專用爬蟲執行器
針對雲端環境優化，支援無頭模式和自動化執行
"""

import os
import sys
import argparse
import json
from datetime import datetime
from crawler_manager import CrawlerManager
from crawler_database import CrawlerDatabase

def setup_github_actions_environment():
    """設置 GitHub Actions 環境"""
    print("🔧 設置 GitHub Actions 環境")
    
    # 設置環境變數
    os.environ['HEADLESS'] = 'true'
    os.environ['GITHUB_ACTIONS'] = 'true'
    os.environ['DISPLAY'] = ':99'  # 虛擬顯示器
    
    # 確保目錄存在
    os.makedirs('crawl_data', exist_ok=True)
    os.makedirs('docs', exist_ok=True)
    
    print("✅ 環境設置完成")

def run_daily_deals_crawlers(max_products=50):
    """執行每日促銷爬蟲"""
    print("🛒 執行每日促銷爬蟲")
    print("=" * 50)
    
    results = {}
    
    try:
        manager = CrawlerManager()
        
        # PChome 促銷
        print("1. 執行 PChome 促銷爬蟲...")
        pchome_result = manager.run_single_crawler(
            platform='pchome_onsale',
            keyword='pchome_onsale',
            max_products=max_products,
            use_sqlite=True,
            save_json=True
        )
        results['pchome_onsale'] = pchome_result
        print(f"   ✅ PChome: {pchome_result.get('total_products', 0)} 個商品")
        
        # Yahoo 秒殺
        print("2. 執行 Yahoo 秒殺爬蟲...")
        yahoo_result = manager.run_single_crawler(
            platform='yahoo_rushbuy',
            keyword='yahoo_rushbuy',
            max_products=max_products,
            use_sqlite=True,
            save_json=True
        )
        results['yahoo_rushbuy'] = yahoo_result
        print(f"   ✅ Yahoo: {yahoo_result.get('total_products', 0)} 個商品")
        
        return results
        
    except Exception as e:
        print(f"❌ 每日促銷爬蟲失敗: {e}")
        return {}

def run_general_crawlers(max_products=30):
    """執行一般爬蟲 (較少商品數量，避免超時)"""
    print("🕷️ 執行一般爬蟲")
    print("=" * 50)
    
    # 熱門關鍵字列表
    popular_keywords = [
        'iPhone',
        'Switch',
        '蛋白粉',
        '空氣清淨機',
        '咖啡'
    ]
    
    results = {}
    
    try:
        manager = CrawlerManager()
        general_platforms = ['yahoo', 'pchome', 'routn']  # 排除促銷平台
        
        # 隨機選擇一個關鍵字和一個平台，避免執行時間過長
        import random
        keyword = random.choice(popular_keywords)
        platform = random.choice(general_platforms)
        
        print(f"🎯 執行 {platform} 平台，關鍵字: {keyword}")
        
        result = manager.run_single_crawler(
            platform=platform,
            keyword=keyword,
            max_products=max_products,
            use_sqlite=True,
            save_json=True
        )
        
        results[f'{platform}_{keyword}'] = result
        print(f"   ✅ {platform}: {result.get('total_products', 0)} 個商品")
        
        return results
        
    except Exception as e:
        print(f"❌ 一般爬蟲失敗: {e}")
        return {}

def export_json_files():
    """從 SQLite 匯出 JSON 檔案供 GitHub Pages 使用"""
    print("📄 匯出 JSON 檔案")
    print("=" * 30)
    
    try:
        db = CrawlerDatabase()
        
        # 匯出每日促銷 JSON
        daily_deals_platforms = ['pchome_onsale', 'yahoo_rushbuy']
        
        for platform in daily_deals_platforms:
            filename = f"crawl_data/crawler_results_{platform}.json"
            if db.export_to_json(platform, filename):
                print(f"✅ 匯出 {platform}: {filename}")
            else:
                print(f"⚠️ {platform} 沒有資料可匯出")
        
        # 匯出統計資料
        stats = db.get_database_stats()
        stats_file = "crawl_data/database_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'stats': stats
            }, f, ensure_ascii=False, indent=2)
        print(f"✅ 匯出統計: {stats_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON 匯出失敗: {e}")
        return False

def generate_execution_report(daily_results, general_results):
    """生成執行報告"""
    print("📊 生成執行報告")
    print("=" * 30)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'execution_summary': {
            'daily_deals': {
                'total_platforms': len(daily_results),
                'total_products': sum(r.get('total_products', 0) for r in daily_results.values()),
                'results': daily_results
            },
            'general_crawlers': {
                'total_executions': len(general_results),
                'total_products': sum(r.get('total_products', 0) for r in general_results.values()),
                'results': general_results
            }
        },
        'github_actions': {
            'run_id': os.environ.get('GITHUB_RUN_ID', 'local'),
            'workflow': os.environ.get('GITHUB_WORKFLOW', 'manual'),
            'actor': os.environ.get('GITHUB_ACTOR', 'system')
        }
    }
    
    # 儲存報告
    report_file = "crawl_data/execution_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 報告已儲存: {report_file}")
    
    # 顯示摘要
    total_products = report['execution_summary']['daily_deals']['total_products'] + \
                    report['execution_summary']['general_crawlers']['total_products']
    
    print(f"📈 執行摘要:")
    print(f"   每日促銷: {report['execution_summary']['daily_deals']['total_products']} 個商品")
    print(f"   一般爬蟲: {report['execution_summary']['general_crawlers']['total_products']} 個商品")
    print(f"   總計: {total_products} 個商品")
    
    return report

def main():
    """主要執行函數"""
    parser = argparse.ArgumentParser(description='GitHub Actions 爬蟲執行器')
    parser.add_argument('--mode', choices=['daily-deals', 'general', 'all'], 
                       default='all', help='執行模式')
    parser.add_argument('--max-products', type=int, default=50, 
                       help='每個平台最大商品數量')
    
    args = parser.parse_args()
    
    print("🤖 GitHub Actions 爬蟲自動化執行")
    print("=" * 60)
    print(f"⏰ 執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 執行模式: {args.mode}")
    print(f"📊 最大商品數: {args.max_products}")
    
    # 設置環境
    setup_github_actions_environment()
    
    daily_results = {}
    general_results = {}
    
    try:
        # 執行每日促銷爬蟲
        if args.mode in ['daily-deals', 'all']:
            daily_results = run_daily_deals_crawlers(args.max_products)
        
        # 執行一般爬蟲
        if args.mode in ['general', 'all']:
            general_results = run_general_crawlers(args.max_products // 2)  # 一般爬蟲用較少商品數
        
        # 匯出 JSON 檔案
        export_json_files()
        
        # 生成執行報告
        report = generate_execution_report(daily_results, general_results)
        
        print("\n🎉 自動化執行完成！")
        
        # 設置 GitHub Actions 輸出
        if os.environ.get('GITHUB_ACTIONS'):
            total_products = sum(r.get('total_products', 0) for r in daily_results.values()) + \
                           sum(r.get('total_products', 0) for r in general_results.values())
            print(f"::set-output name=total_products::{total_products}")
            print(f"::set-output name=timestamp::{datetime.now().isoformat()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 執行失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
