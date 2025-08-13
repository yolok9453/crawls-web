#!/usr/bin/env python3
"""
爬蟲結果展示網站 - 主要入口點
"""

import os
import sys

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'app'))
sys.path.insert(0, os.path.join(project_root, 'core'))

# 設定環境變數路徑
from dotenv import load_dotenv
config_path = os.path.join(project_root, 'config', '.env')
if os.path.exists(config_path):
    load_dotenv(config_path)

# 啟動Flask應用
if __name__ == '__main__':
    try:
        # 自動同步 GitHub 資料庫
        print("🔄 檢查資料庫更新...")
        try:
            from core.github_sync import auto_sync_if_needed
            auto_sync_if_needed(max_age_hours=2)  # 如果超過2小時沒更新就同步
        except Exception as e:
            print(f"⚠️ 資料庫同步檢查失敗，將使用本地資料庫: {e}")
        
        # 導入並啟動web應用
        from app.web_app import app, init_db
        
        # 初始化資料庫
        init_db()
        
        print("🚀 爬蟲結果展示網站啟動中...")
        print("📁 請訪問: http://localhost:5000")
        print("💡 提示: 網站會自動從 GitHub 同步最新的促銷資料")
        print("⏹️  按 Ctrl+C 停止伺服器")
        
        # 解決 UWSGI 連接問題
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        # 使用簡單的開發伺服器
        app.run(debug=True, host='127.0.0.1', port=5000, threaded=True, use_reloader=False)
        
    except Exception as e:
        print(f"❌ 啟動Web應用時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
