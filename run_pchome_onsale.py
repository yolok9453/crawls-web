#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動執行 PChome OnSale 爬蟲的腳本
專門用於 GitHub Actions 定時執行
"""

import os
import sys
import json
import logging
from datetime import datetime

# 設置路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 導入爬蟲管理器
from crawler_manager import CrawlerManager

def setup_logging():
    """設置日誌記錄"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('pchome_onsale_auto.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def cleanup_old_files(output_dir):
    """清理舊的 PCHOME ONSALE 檔案"""
    import glob
    
    try:
        pattern = os.path.join(output_dir, "crawler_results_pchome_onsale_*.json")
        old_files = glob.glob(pattern)
        
        for file_path in old_files:
            try:
                os.remove(file_path)
                logging.info(f"已刪除舊檔案: {file_path}")
            except Exception as e:
                logging.warning(f"無法刪除檔案 {file_path}: {e}")
                
    except Exception as e:
        logging.error(f"清理舊檔案時發生錯誤: {e}")

def run_pchome_onsale_crawler():
    """執行 PChome OnSale 爬蟲"""
    setup_logging()
    
    logging.info("=== 開始執行 PChome OnSale 自動爬蟲 ===")
    logging.info(f"執行時間: {datetime.now().isoformat()}")
    
    try:
        # 初始化爬蟲管理器
        manager = CrawlerManager()
        
        # 清理舊檔案
        cleanup_old_files(manager.output_dir)
        
        # 執行 PCHOME ONSALE 爬蟲
        logging.info("正在執行 PChome OnSale 爬蟲...")
        results = manager.run_all_crawlers(
            keyword="pchome_onsale",
            max_products=300,  # 增加數量以獲取更多促銷商品
            min_price=0,
            max_price=999999,
            platforms=['pchome_onsale']
        )
        
        if not results or 'pchome_onsale' not in results:
            logging.error("爬蟲執行失敗：沒有獲取到結果")
            return False
            
        result = results['pchome_onsale']
        
        # 檢查結果狀態
        if result.get('status') == 'error':
            logging.error(f"爬蟲執行失敗: {result.get('error', '未知錯誤')}")
            return False
            
        # 保存結果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crawler_results_pchome_onsale_{timestamp}.json"
        filepath = manager.save_results("pchome_onsale", results, filename)
        
        # 記錄成功資訊
        total_products = result.get('total_products', 0)
        crawl_time = result.get('crawl_time', '')
        
        logging.info(f"爬蟲執行成功！")
        logging.info(f"  - 獲取商品數量: {total_products}")
        logging.info(f"  - 爬取時間: {crawl_time}")
        logging.info(f"  - 結果檔案: {filepath}")
        
        # 創建或更新最新結果的符號連結檔案
        latest_file = os.path.join(manager.output_dir, "crawler_results_pchome_onsale.json")
        try:
            if os.path.exists(latest_file):
                os.remove(latest_file)
            
            # 創建符號連結或複製檔案
            import shutil
            shutil.copy2(filepath, latest_file)
            logging.info(f"已更新最新結果檔案: {latest_file}")
            
        except Exception as e:
            logging.warning(f"無法創建最新結果檔案: {e}")
        
        return True
        
    except Exception as e:
        logging.error(f"執行過程中發生錯誤: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return False

def main():
    """主函數"""
    success = run_pchome_onsale_crawler()
    
    if success:
        print("✅ PChome OnSale 爬蟲執行成功")
        sys.exit(0)
    else:
        print("❌ PChome OnSale 爬蟲執行失敗")
        sys.exit(1)

if __name__ == "__main__":
    main()
