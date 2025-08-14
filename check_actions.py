#!/usr/bin/env python3
"""
檢查GitHub Actions狀態
"""

import requests
import json
from datetime import datetime, timezone, timedelta

def check_github_actions():
    """檢查GitHub Actions執行狀態"""
    repo = "yolok9453/crawls-web"
    
    try:
        # 獲取工作流程列表
        workflows_url = f"https://api.github.com/repos/{repo}/actions/workflows"
        workflows_response = requests.get(workflows_url)
        workflows_data = workflows_response.json()
        
        print("=== GitHub Actions 工作流程 ===")
        for workflow in workflows_data.get('workflows', []):
            print(f"📋 工作流程: {workflow['name']}")
            print(f"   ID: {workflow['id']}")
            print(f"   狀態: {workflow['state']}")
            print(f"   檔案: {workflow['path']}")
            print(f"   建立時間: {workflow['created_at']}")
            print()
        
        # 獲取最近的執行記錄
        runs_url = f"https://api.github.com/repos/{repo}/actions/runs?per_page=10"
        runs_response = requests.get(runs_url)
        runs_data = runs_response.json()
        
        print("=== 最近的執行記錄 ===")
        for run in runs_data.get('workflow_runs', []):
            created_time = datetime.fromisoformat(run['created_at'].replace('Z', '+00:00'))
            updated_time = datetime.fromisoformat(run['updated_at'].replace('Z', '+00:00'))
            
            # 轉換為台灣時間
            taiwan_tz = timezone(timedelta(hours=8))
            created_local = created_time.astimezone(taiwan_tz)
            updated_local = updated_time.astimezone(taiwan_tz)
            
            status_emoji = {
                'success': '✅',
                'failure': '❌', 
                'cancelled': '⏹️',
                'in_progress': '🔄'
            }.get(run['conclusion'], '❓')
            
            print(f"{status_emoji} 執行 #{run['run_number']}")
            print(f"   狀態: {run['status']} / {run['conclusion']}")
            print(f"   開始: {created_local.strftime('%Y-%m-%d %H:%M:%S')} (台灣時間)")
            print(f"   完成: {updated_local.strftime('%Y-%m-%d %H:%M:%S')} (台灣時間)")
            print(f"   觸發: {run['event']}")
            if run.get('head_commit'):
                print(f"   提交: {run['head_commit']['message'][:50]}...")
            print()
    
    except Exception as e:
        print(f"❌ 檢查GitHub Actions失敗: {e}")

def calculate_next_run():
    """計算下次執行時間"""
    print("=== 下次執行時間計算 ===")
    
    # GitHub Actions cron: '0 */6 * * *' (每6小時執行一次)
    schedule_hours = [0, 6, 12, 18]  # UTC 時間
    
    now_utc = datetime.now(timezone.utc)
    now_taiwan = now_utc.astimezone(timezone(timedelta(hours=8)))
    
    print(f"當前UTC時間: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"當前台灣時間: {now_taiwan.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 找出下次執行時間
    current_hour = now_utc.hour
    next_hours = [h for h in schedule_hours if h > current_hour]
    
    if next_hours:
        next_hour = next_hours[0]
        next_run_utc = now_utc.replace(hour=next_hour, minute=0, second=0, microsecond=0)
    else:
        # 下一天的第一個時段
        next_hour = schedule_hours[0]
        next_run_utc = (now_utc + timedelta(days=1)).replace(hour=next_hour, minute=0, second=0, microsecond=0)
    
    next_run_taiwan = next_run_utc.astimezone(timezone(timedelta(hours=8)))
    time_until = next_run_utc - now_utc
    
    print("⏰ 執行排程 (每6小時):")
    for hour in schedule_hours:
        taiwan_hour = (hour + 8) % 24
        taiwan_day = " (+1天)" if hour + 8 >= 24 else ""
        print(f"   UTC {hour:02d}:00 → 台灣時間 {taiwan_hour:02d}:00{taiwan_day}")
    
    print()
    print(f"🕒 下次執行時間:")
    print(f"   UTC: {next_run_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   台灣時間: {next_run_taiwan.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   剩餘時間: {str(time_until).split('.')[0]}")

def check_workflow_file():
    """檢查工作流程文件"""
    print("\n=== 工作流程文件檢查 ===")
    
    import os
    workflow_file = ".github/workflows/update-daily-deals.yml"
    
    if os.path.exists(workflow_file):
        print(f"✅ 工作流程文件存在: {workflow_file}")
        
        with open(workflow_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 檢查關鍵設定
        if 'cron:' in content:
            print("✅ 包含排程設定 (cron)")
        if 'workflow_dispatch:' in content:
            print("✅ 支援手動觸發")
        if 'ubuntu-latest' in content:
            print("✅ 使用Ubuntu運行環境")
        if 'python' in content.lower():
            print("✅ 包含Python設定")
        if 'selenium' in content.lower() or 'chrome' in content.lower():
            print("✅ 包含瀏覽器設定")
            
        print(f"📄 文件大小: {len(content)} 字節")
    else:
        print(f"❌ 工作流程文件不存在: {workflow_file}")

def main():
    print("🔍 GitHub Actions 狀態檢查")
    print("=" * 50)
    
    check_workflow_file()
    check_github_actions()
    calculate_next_run()
    
    print("\n💡 提示:")
    print("- 可以在GitHub倉庫的 Actions 頁面查看詳細執行記錄")
    print("- 手動觸發: 在GitHub上進入 Actions → 選擇工作流程 → Run workflow")
    print("- 執行歷史: https://github.com/yolok9453/crawls-web/actions")

if __name__ == "__main__":
    main()
