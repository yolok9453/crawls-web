#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自動化每日促銷更新系統
定時執行促銷爬蟲並自動更新資料
"""

import schedule
import time
import threading
from datetime import datetime, timedelta
from crawler_manager import CrawlerManager
from crawler_database import CrawlerDatabase
import logging
import os

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_crawler.log'),
        logging.StreamHandler()
    ]
)

class AutoCrawlerService:
    def __init__(self):
        """初始化自動化爬蟲服務"""
        self.manager = CrawlerManager()
        self.db = CrawlerDatabase()
        self.is_running = False
        
    def run_daily_deals_crawler(self, platform, max_products=50):
        """執行每日促銷爬蟲"""
        try:
            logging.info(f"🚀 開始執行 {platform} 自動爬蟲")
            
            result = self.manager.run_single_crawler(
                platform=platform,
                keyword=platform,
                max_products=max_products,
                use_sqlite=True,
                save_json=True
            )
            
            if result.get('status') == 'success':
                products_count = result.get('total_products', 0)
                exec_time = result.get('execution_time', 0)
                
                logging.info(f"✅ {platform} 爬蟲成功: {products_count} 個商品, {exec_time:.2f}s")
                
                # 匯出 JSON 備援
                json_file = f"crawl_data/crawler_results_{platform}.json"
                if self.db.export_to_json(platform, json_file):
                    logging.info(f"✅ {platform} JSON 備援已更新")
                
                return True
            else:
                error_msg = result.get('error', 'unknown')
                logging.error(f"❌ {platform} 爬蟲失敗: {error_msg}")
                return False
                
        except Exception as e:
            logging.error(f"❌ {platform} 爬蟲執行異常: {e}")
            return False
    
    def pchome_daily_update(self):
        """PChome 每日促銷更新"""
        logging.info("🛒 執行 PChome 每日促銷自動更新")
        return self.run_daily_deals_crawler('pchome_onsale', max_products=60)
    
    def yahoo_daily_update(self):
        """Yahoo 秒殺每日更新"""
        logging.info("⚡ 執行 Yahoo 秒殺自動更新")
        return self.run_daily_deals_crawler('yahoo_rushbuy', max_products=40)
    
    def check_data_freshness(self, platform, max_hours=4):
        """檢查資料是否需要更新（超過指定小時數）"""
        try:
            sessions = self.db.get_crawl_sessions(platform=platform, limit=1)
            if not sessions:
                logging.info(f"⚠️ {platform} 沒有歷史資料，需要更新")
                return True
            
            last_session = sessions[0]
            last_update = datetime.fromisoformat(
                last_session['timestamp'].replace('Z', '+00:00') if 'Z' in last_session['timestamp'] 
                else last_session['timestamp']
            )
            
            now = datetime.now()
            if last_update.tzinfo is None:
                last_update = last_update.replace(tzinfo=now.tzinfo)
            
            hours_ago = (now - last_update.replace(tzinfo=None)).total_seconds() / 3600
            
            if hours_ago > max_hours:
                logging.info(f"📅 {platform} 資料已過時 ({hours_ago:.1f}h)，需要更新")
                return True
            else:
                logging.info(f"✅ {platform} 資料仍新鮮 ({hours_ago:.1f}h)，跳過更新")
                return False
                
        except Exception as e:
            logging.error(f"❌ 檢查 {platform} 資料新鮮度失敗: {e}")
            return True  # 出錯時強制更新
    
    def smart_update_check(self):
        """智慧更新檢查 - 只在需要時更新"""
        logging.info("🔍 執行智慧更新檢查")
        
        updates_needed = []
        
        # 檢查 PChome 是否需要更新
        if self.check_data_freshness('pchome_onsale', max_hours=3):
            updates_needed.append('pchome')
        
        # 檢查 Yahoo 是否需要更新
        if self.check_data_freshness('yahoo_rushbuy', max_hours=4):
            updates_needed.append('yahoo')
        
        # 執行需要的更新
        if 'pchome' in updates_needed:
            self.pchome_daily_update()
        
        if 'yahoo' in updates_needed:
            self.yahoo_daily_update()
        
        if not updates_needed:
            logging.info("✅ 所有資料都是最新的，無需更新")
    
    def setup_schedules(self):
        """設定自動化排程"""
        logging.info("⏰ 設定自動化排程")
        
        # PChome 促銷 - 每天多次更新（商品變化較快）
        schedule.every().day.at("08:00").do(self.pchome_daily_update)
        schedule.every().day.at("12:00").do(self.pchome_daily_update)
        schedule.every().day.at("16:00").do(self.pchome_daily_update)
        schedule.every().day.at("20:00").do(self.pchome_daily_update)
        
        # Yahoo 秒殺 - 每天兩次更新
        schedule.every().day.at("09:00").do(self.yahoo_daily_update)
        schedule.every().day.at("18:00").do(self.yahoo_daily_update)
        
        # 智慧檢查 - 每2小時檢查一次是否需要更新
        schedule.every(2).hours.do(self.smart_update_check)
        
        # 夜間完整更新 - 確保隔天有新資料
        schedule.every().day.at("02:00").do(lambda: [
            self.pchome_daily_update(),
            self.yahoo_daily_update()
        ])
        
        logging.info("✅ 排程設定完成:")
        logging.info("   • PChome 促銷: 08:00, 12:00, 16:00, 20:00")
        logging.info("   • Yahoo 秒殺: 09:00, 18:00")
        logging.info("   • 智慧檢查: 每2小時")
        logging.info("   • 夜間更新: 02:00")
    
    def run_scheduler(self):
        """執行排程器"""
        self.is_running = True
        logging.info("🚀 自動化排程服務啟動")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(30)  # 每30秒檢查一次
            except KeyboardInterrupt:
                logging.info("👋 接收到停止信號")
                break
            except Exception as e:
                logging.error(f"❌ 排程執行錯誤: {e}")
                time.sleep(60)  # 出錯時等待1分鐘再繼續
        
        self.is_running = False
        logging.info("🛑 自動化排程服務已停止")
    
    def start_service(self):
        """啟動服務"""
        self.setup_schedules()
        
        # 啟動時執行一次智慧檢查
        logging.info("🔄 啟動時執行初始檢查")
        self.smart_update_check()
        
        # 在背景執行排程
        scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        scheduler_thread.start()
        
        return scheduler_thread
    
    def stop_service(self):
        """停止服務"""
        self.is_running = False
        logging.info("🛑 正在停止自動化服務...")

def main():
    """主函數 - 可以作為獨立服務運行"""
    print("🤖 自動化每日促銷更新服務")
    print("=" * 50)
    
    service = AutoCrawlerService()
    
    try:
        # 啟動服務
        thread = service.start_service()
        
        print("✅ 自動化服務已啟動")
        print("📋 排程:")
        print("   • PChome 促銷: 08:00, 12:00, 16:00, 20:00")
        print("   • Yahoo 秒殺: 09:00, 18:00")
        print("   • 智慧檢查: 每2小時")
        print("   • 夜間更新: 02:00")
        print("\n按 Ctrl+C 停止服務...")
        
        # 保持主程序運行
        while service.is_running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 正在關閉服務...")
        service.stop_service()
        print("✅ 服務已停止")

if __name__ == "__main__":
    main()
