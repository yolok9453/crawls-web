"""
GitHub 資料庫同步模組
從 GitHub 倉庫下載最新的資料庫檔案
"""

import os
import requests
import shutil
from datetime import datetime

def download_latest_database(github_username="yolok9453", repo_name="crawls-web", branch="master"):
    """
    從 GitHub 下載最新的資料庫檔案
    """
    try:
        # GitHub raw file URL
        db_url = f"https://raw.githubusercontent.com/{github_username}/{repo_name}/{branch}/data/crawler_data.db"
        
        # 本地資料庫路徑
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        local_db_path = os.path.join(project_root, 'data', 'crawler_data.db')
        backup_db_path = os.path.join(project_root, 'data', f'crawler_data_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
        
        # 確保目錄存在
        os.makedirs(os.path.dirname(local_db_path), exist_ok=True)
        
        print(f"🔄 正在從 GitHub 下載最新資料庫...")
        print(f"📥 下載網址: {db_url}")
        
        # 下載檔案
        response = requests.get(db_url, timeout=30)
        response.raise_for_status()
        
        # 備份現有資料庫（如果存在）
        if os.path.exists(local_db_path):
            shutil.copy2(local_db_path, backup_db_path)
            print(f"💾 已備份現有資料庫到: {backup_db_path}")
        
        # 儲存新資料庫
        with open(local_db_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ 成功下載資料庫到: {local_db_path}")
        print(f"📊 檔案大小: {len(response.content)} bytes")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 下載失敗 - 網路錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 下載失敗 - 其他錯誤: {e}")
        return False

def check_database_update_time():
    """
    檢查本地資料庫的最後更新時間
    """
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        local_db_path = os.path.join(project_root, 'data', 'crawler_data.db')
        
        if os.path.exists(local_db_path):
            mtime = os.path.getmtime(local_db_path)
            update_time = datetime.fromtimestamp(mtime)
            print(f"📅 本地資料庫最後更新時間: {update_time.strftime('%Y-%m-%d %H:%M:%S')}")
            return update_time
        else:
            print("❌ 本地資料庫不存在")
            return None
    except Exception as e:
        print(f"❌ 檢查資料庫更新時間失敗: {e}")
        return None

def auto_sync_if_needed(max_age_hours=1):
    """
    如果本地資料庫太舊，自動同步
    """
    try:
        update_time = check_database_update_time()
        
        if update_time is None:
            print("🔄 本地資料庫不存在，開始下載...")
            return download_latest_database()
        
        # 檢查是否需要更新
        now = datetime.now()
        age_hours = (now - update_time).total_seconds() / 3600
        
        if age_hours > max_age_hours:
            print(f"🔄 本地資料庫已 {age_hours:.1f} 小時未更新，開始同步...")
            return download_latest_database()
        else:
            print(f"✅ 本地資料庫夠新（{age_hours:.1f} 小時前），無需同步")
            return True
            
    except Exception as e:
        print(f"❌ 自動同步檢查失敗: {e}")
        return False

if __name__ == "__main__":
    # 測試功能
    print("🧪 測試 GitHub 資料庫同步功能...")
    check_database_update_time()
    download_latest_database()
