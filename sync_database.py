#!/usr/bin/env python3
"""
手動同步 GitHub 資料庫工具
"""

import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'core'))

def main():
    """主函數"""
    print("🔄 GitHub 資料庫同步工具")
    print("=" * 40)
    
    try:
        from core.github_sync import download_latest_database, check_database_update_time
        
        # 檢查當前資料庫狀態
        print("📊 檢查當前資料庫狀態...")
        check_database_update_time()
        print()
        
        # 詢問是否要同步
        choice = input("🤔 是否要從 GitHub 下載最新資料庫？(y/N): ").lower().strip()
        
        if choice in ['y', 'yes']:
            print()
            success = download_latest_database()
            
            if success:
                print("\n✅ 同步完成！現在可以啟動網站查看最新資料。")
                print("💡 執行 'python main.py' 啟動網站")
            else:
                print("\n❌ 同步失敗，請檢查網路連線或稍後再試。")
                sys.exit(1)
        else:
            print("\n⏹️ 已取消同步")
            
    except ImportError as e:
        print(f"❌ 模組匯入失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
