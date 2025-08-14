#!/usr/bin/env python3
"""
清理不需要的檔案
"""

import os
import sys

project_root = os.path.dirname(os.path.abspath(__file__))

def analyze_files():
    """分析哪些檔案可以安全刪除"""
    print("=== 分析可清理的檔案 ===")
    
    # 可能不需要的檔案/目錄
    candidates_for_removal = [
        # 測試和調試檔案
        'test.py',
        'test.txt', 
        'debug_ai_response.txt',
        'check_db.py',
        'check_db2.py',
        'check_system.py',
        
        # 舊的JSON資料檔案 (現在使用SQLite)
        'crawl_data/crawler_results_pchome_onsale.json',
        'crawl_data/crawler_results_yahoo_rushbuy.json',
        
        # 空的測試目錄
        'crawl_testdata/',
        
        # 本檢查腳本自身
        'cleanup_files.py'
    ]
    
    # 分類檔案
    can_remove = []
    keep_files = []
    
    for file_path in candidates_for_removal:
        full_path = os.path.join(project_root, file_path)
        
        if os.path.exists(full_path):
            # 檢查檔案大小和類型
            if os.path.isfile(full_path):
                size = os.path.getsize(full_path)
                print(f"📄 {file_path} - {size:,} bytes")
                
                # JSON檔案通常是舊的爬蟲結果，現在用SQLite
                if file_path.endswith('.json') and 'crawler_results' in file_path:
                    can_remove.append((file_path, f"舊的JSON結果檔案，現已使用SQLite資料庫"))
                # 測試和調試檔案
                elif any(keyword in file_path for keyword in ['test', 'debug', 'check']):
                    can_remove.append((file_path, f"測試/調試檔案"))
                else:
                    keep_files.append((file_path, "可能仍有用途"))
                    
            elif os.path.isdir(full_path):
                # 檢查目錄是否為空
                try:
                    items = os.listdir(full_path)
                    if not items:
                        can_remove.append((file_path, "空目錄"))
                    elif items == ['.gitkeep']:
                        print(f"📁 {file_path} - 空目錄 (只有.gitkeep)")
                        keep_files.append((file_path, "空目錄但有.gitkeep，建議保留"))
                    else:
                        print(f"📁 {file_path} - {len(items)} 項目")
                        keep_files.append((file_path, f"目錄包含 {len(items)} 個項目"))
                except PermissionError:
                    keep_files.append((file_path, "無權限檢查"))
        else:
            print(f"❌ {file_path} - 不存在")
    
    return can_remove, keep_files

def show_recommendations(can_remove, keep_files):
    """顯示清理建議"""
    print(f"\n=== 清理建議 ===")
    
    print(f"\n🗑️ 建議刪除的檔案 ({len(can_remove)} 個):")
    total_size = 0
    for file_path, reason in can_remove:
        full_path = os.path.join(project_root, file_path)
        if os.path.isfile(full_path):
            size = os.path.getsize(full_path)
            total_size += size
            print(f"  ❌ {file_path} - {reason} ({size:,} bytes)")
        else:
            print(f"  ❌ {file_path} - {reason}")
    
    print(f"\n💾 建議保留的檔案 ({len(keep_files)} 個):")
    for file_path, reason in keep_files:
        print(f"  ✅ {file_path} - {reason}")
    
    if total_size > 0:
        print(f"\n💾 總共可節省空間: {total_size:,} bytes ({total_size/1024:.1f} KB)")
    
    return can_remove

def confirm_and_remove(can_remove):
    """確認並刪除檔案"""
    if not can_remove:
        print("\n沒有找到需要清理的檔案。")
        return
    
    print(f"\n確定要刪除這 {len(can_remove)} 個檔案嗎？")
    print("輸入 'yes' 確認刪除，或按 Enter 取消:")
    
    confirm = input().strip().lower()
    
    if confirm == 'yes':
        print("\n開始清理...")
        
        removed_count = 0
        for file_path, reason in can_remove:
            full_path = os.path.join(project_root, file_path)
            
            try:
                if os.path.isfile(full_path):
                    os.remove(full_path)
                    print(f"✅ 已刪除檔案: {file_path}")
                    removed_count += 1
                elif os.path.isdir(full_path):
                    os.rmdir(full_path)
                    print(f"✅ 已刪除目錄: {file_path}")
                    removed_count += 1
                else:
                    print(f"⚠️ 檔案不存在: {file_path}")
                    
            except Exception as e:
                print(f"❌ 刪除失敗 {file_path}: {e}")
        
        print(f"\n🎉 清理完成！成功刪除 {removed_count} 個檔案/目錄。")
    else:
        print("\n❌ 取消清理操作。")

def main():
    print("🧹 檔案清理工具")
    print(f"📁 專案目錄: {project_root}")
    
    can_remove, keep_files = analyze_files()
    can_remove = show_recommendations(can_remove, keep_files)
    confirm_and_remove(can_remove)

if __name__ == "__main__":
    main()
